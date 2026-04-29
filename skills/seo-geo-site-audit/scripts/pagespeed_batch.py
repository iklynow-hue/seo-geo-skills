#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import time
import urllib.parse
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path

API_ENDPOINT = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
REQUEST_TIMEOUT = 45
MAX_ATTEMPTS = 3
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
BACKOFF_BASE = 2  # seconds
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
SKILL_ENV_PATH = SKILL_DIR / ".env"


def load_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"'")
        if key:
            values[key] = value
    return values


def resolve_api_key(args: argparse.Namespace) -> str | None:
    file_env = load_env_file(SKILL_ENV_PATH)
    api_key = (
        args.api_key
        or file_env.get("PAGESPEED_API_KEY")
        or file_env.get("GOOGLE_API_KEY")
        or os.getenv("PAGESPEED_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
    )
    if api_key:
        return api_key
    return None


def call_pagespeed(url: str, strategy: str, api_key: str | None, timeout: int = REQUEST_TIMEOUT) -> dict:
    params = [
        ("url", url),
        ("strategy", strategy),
        ("category", "PERFORMANCE"),
        ("category", "ACCESSIBILITY"),
        ("category", "BEST_PRACTICES"),
        ("category", "SEO"),
    ]
    if api_key:
        params.append(("key", api_key))
    endpoint = f"{API_ENDPOINT}?{urllib.parse.urlencode(params, doseq=True)}"
    req = urllib.request.Request(endpoint, headers={"User-Agent": "seo-geo-site-audit/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        raw = response.read().decode("utf-8", errors="replace")
    return json.loads(raw)


def classify_http_error(exc: urllib.error.HTTPError) -> tuple[RuntimeError, bool]:
    body = exc.read().decode("utf-8", errors="replace")[:300].strip()
    retryable = exc.code in RETRYABLE_STATUS_CODES
    lowered = body.lower()
    if exc.code == 429 and any(
        marker in lowered
        for marker in (
            "quota exceeded",
            "queries per day",
            "daily limit exceeded",
            "quota metric",
        )
    ):
        retryable = False
    message = f"HTTP Error {exc.code}"
    if body:
        message = f"{message}: {body}"
    return RuntimeError(message), retryable


def call_pagespeed_with_retry(url: str, strategy: str, api_key: str | None) -> dict:
    last_error: Exception | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return call_pagespeed(url, strategy, api_key)
        except urllib.error.HTTPError as exc:
            last_error, retryable = classify_http_error(exc)
            if not retryable or attempt == MAX_ATTEMPTS:
                raise last_error
        except (urllib.error.URLError, socket.timeout, TimeoutError) as exc:
            last_error = exc
            if attempt == MAX_ATTEMPTS:
                raise
        except Exception as exc:
            last_error = exc
            if attempt == MAX_ATTEMPTS:
                raise
        time.sleep(min(BACKOFF_BASE ** attempt, 8))
    if last_error:
        raise last_error
    raise RuntimeError("PageSpeed request failed without a captured error.")


def pick_urls_from_crawl(crawl_path: str, max_urls: int) -> list[str]:
    data = json.loads(Path(crawl_path).read_text(encoding="utf-8"))
    pages = data.get("pages", [])
    chosen = []
    seen_templates = set()

    def add(url: str, template: str) -> None:
        if url and url not in chosen and len(chosen) < max_urls:
            chosen.append(url)
            seen_templates.add(template)

    # Performance evidence defaults to the landing page. Most audit value comes
    # from the homepage experience, and API/local Lighthouse runs are expensive
    # on JS-heavy sites. If callers request more URLs, we still add template
    # examples below.
    for page in pages:
        if page.get("status") == 200 and page.get("discovery_source") == "start":
            add(page.get("url", ""), page.get("template", "homepage"))
            break

    for page in pages:
        if page.get("status") == 200 and page.get("template") == "homepage":
            add(page.get("url", ""), "homepage")
            break

    if len(chosen) >= max_urls:
        return chosen[:max_urls]

    for preferred in ("homepage", "pricing", "product", "docs", "blog", "trust", "other"):
        for page in pages:
            if page.get("status") == 200 and page.get("template") == preferred:
                add(page.get("url", ""), preferred)
                break

    for page in pages:
        if page.get("status") == 200:
            add(page.get("url", ""), page.get("template", "other"))
        if len(chosen) >= max_urls:
            break
    return chosen[:max_urls]


def summarize_result(payload: dict, url: str, strategy: str, source: str = "api") -> dict:
    lighthouse = payload.get("lighthouseResult", {})
    categories = lighthouse.get("categories", {})
    audits = lighthouse.get("audits", {})
    loading = payload.get("loadingExperience", {})
    origin_loading = payload.get("originLoadingExperience", {})

    category_scores = {
        key.lower(): round((value.get("score") or 0) * 100)
        for key, value in categories.items()
    }

    metric_map = {
        "first-contentful-paint": "fcp_ms",
        "largest-contentful-paint": "lcp_ms",
        "speed-index": "speed_index_ms",
        "interactive": "tti_ms",
        "total-blocking-time": "tbt_ms",
        "cumulative-layout-shift": "cls",
        "interaction-to-next-paint": "inp_ms",
    }
    lab_metrics = {}
    for audit_id, output_key in metric_map.items():
        item = audits.get(audit_id, {})
        if "numericValue" in item:
            lab_metrics[output_key] = item["numericValue"]

    opportunities = []
    for audit_id, item in audits.items():
        details_type = item.get("details", {}).get("type")
        if details_type == "opportunity" or item.get("scoreDisplayMode") == "metricSavings":
            score = item.get("score")
            if score is None or score >= 0.9:
                continue
            opportunities.append(
                {
                    "id": audit_id,
                    "title": item.get("title", audit_id),
                    "score": score,
                    "display_value": item.get("displayValue", ""),
                }
            )
    opportunities.sort(key=lambda x: x["score"])

    return {
        "url": url,
        "strategy": strategy,
        "source": source,
        "category_scores": category_scores,
        "lab_metrics": lab_metrics,
        "field_data": loading.get("metrics", {}),
        "origin_field_data": origin_loading.get("metrics", {}),
        "top_opportunities": opportunities[:8],
        "final_url": payload.get("id", url),
    }


def aggregate(results: list[dict]) -> dict:
    buckets: dict[str, list[dict]] = defaultdict(list)
    for item in results:
        buckets[item["strategy"]].append(item)

    summary = {}
    for strategy, items in buckets.items():
        count = len(items) or 1
        category_avg = defaultdict(float)
        for item in items:
            for key, value in item.get("category_scores", {}).items():
                category_avg[key] += value
        summary[strategy] = {
            "tested_urls": [item["url"] for item in items],
            "average_category_scores": {k: round(v / count, 1) for k, v in category_avg.items()},
        }
    return summary


def summarize_local_lighthouse(lh_data: dict, url: str, strategy: str) -> dict:
    """Parse local Lighthouse JSON output into the same schema as API results."""
    categories = lh_data.get("categories", {})
    audits = lh_data.get("audits", {})

    category_scores = {
        key.lower(): round((value.get("score") or 0) * 100)
        for key, value in categories.items()
    }

    metric_map = {
        "first-contentful-paint": "fcp_ms",
        "largest-contentful-paint": "lcp_ms",
        "speed-index": "speed_index_ms",
        "interactive": "tti_ms",
        "total-blocking-time": "tbt_ms",
        "cumulative-layout-shift": "cls",
        "interaction-to-next-paint": "inp_ms",
    }
    lab_metrics = {}
    for audit_id, output_key in metric_map.items():
        item = audits.get(audit_id, {})
        if "numericValue" in item:
            lab_metrics[output_key] = item["numericValue"]

    opportunities = []
    for audit_id, item in audits.items():
        details_type = item.get("details", {}).get("type")
        if details_type == "opportunity" or item.get("scoreDisplayMode") == "metricSavings":
            score = item.get("score")
            if score is None or score >= 0.9:
                continue
            opportunities.append(
                {
                    "id": audit_id,
                    "title": item.get("title", audit_id),
                    "score": score,
                    "display_value": item.get("displayValue", ""),
                }
            )
    opportunities.sort(key=lambda x: x["score"])

    return {
        "url": url,
        "strategy": strategy,
        "source": "local_lighthouse",
        "category_scores": category_scores,
        "lab_metrics": lab_metrics,
        "field_data": {},
        "origin_field_data": {},
        "top_opportunities": opportunities[:8],
        "final_url": lh_data.get("finalUrl", url),
    }


def run_local_lighthouse_fallback(url: str, strategy: str, timeout: int = 120) -> dict | None:
    """Try to run Lighthouse locally via CDP as fallback when PageSpeed API fails."""
    try:
        from fetchers import run_local_lighthouse, is_lighthouse_available
    except ImportError:
        return None

    if not is_lighthouse_available():
        print(f"[pagespeed] Local Lighthouse not available for fallback", file=sys.stderr)
        return None

    print(f"[pagespeed] Attempting local Lighthouse for {url} ({strategy})...", file=sys.stderr)
    lh_data = run_local_lighthouse(url, strategy=strategy, timeout=timeout)
    if lh_data is None:
        print(f"[pagespeed] Local Lighthouse failed for {url}", file=sys.stderr)
        return None

    return summarize_local_lighthouse(lh_data, url, strategy)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run PageSpeed Insights for a set of URLs.")
    parser.add_argument("--url", action="append", default=[], help="URL to test. May be supplied multiple times.")
    parser.add_argument("--from-crawl", help="Read homepage-first URLs from crawl_sample.py JSON output.")
    parser.add_argument(
        "--max-urls",
        type=int,
        default=1,
        help="Maximum number of URLs to test. Default is 1 homepage URL; each URL is tested once for mobile and once for desktop.",
    )
    parser.add_argument("--api-key", help=f"PageSpeed API key. Overrides {SKILL_ENV_PATH}.")
    parser.add_argument(
        "--provider",
        choices=("local", "api", "api_with_fallback"),
        default="local",
        help="Performance evidence source. 'local' runs Lighthouse locally, 'api' uses PageSpeed API only, 'api_with_fallback' tries API first then local Lighthouse.",
    )
    parser.add_argument(
        "--local-lighthouse-fallback",
        action="store_true",
        help="Compatibility alias for --provider api_with_fallback.",
    )
    parser.add_argument("--out", help="Optional JSON output file.")
    args = parser.parse_args()

    provider = "api_with_fallback" if args.local_lighthouse_fallback else args.provider

    urls = list(dict.fromkeys(args.url))
    if args.from_crawl:
        urls.extend([u for u in pick_urls_from_crawl(args.from_crawl, args.max_urls) if u not in urls])
    urls = urls[: max(1, min(args.max_urls, 10))]
    if not urls:
        print("No URLs supplied.", file=sys.stderr)
        return 1

    api_key = None
    if provider in {"api", "api_with_fallback"}:
        try:
            api_key = resolve_api_key(args)
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return 1

    results = []
    errors = []
    for url in urls:
        for strategy in ("mobile", "desktop"):
            if provider == "local":
                try:
                    lh_result = run_local_lighthouse_fallback(url, strategy)
                    if lh_result is not None:
                        results.append(lh_result)
                        print(f"[pagespeed] Local Lighthouse succeeded for {url} ({strategy})", file=sys.stderr)
                    else:
                        errors.append({"url": url, "strategy": strategy, "error": "Local Lighthouse unavailable or failed", "source": "local_lighthouse"})
                except Exception as lh_exc:
                    errors.append({"url": url, "strategy": strategy, "error": f"Local Lighthouse: {type(lh_exc).__name__}: {lh_exc}", "source": "local_lighthouse"})
                continue

            api_success = False
            try:
                payload = call_pagespeed_with_retry(url, strategy, api_key)
                results.append(summarize_result(payload, url, strategy, source="api"))
                api_success = True
            except Exception as exc:
                errors.append({"url": url, "strategy": strategy, "error": f"{type(exc).__name__}: {exc}", "source": "api"})

            if not api_success and provider == "api_with_fallback":
                try:
                    lh_result = run_local_lighthouse_fallback(url, strategy)
                    if lh_result is not None:
                        results.append(lh_result)
                        print(f"[pagespeed] Local Lighthouse succeeded for {url} ({strategy})", file=sys.stderr)
                    else:
                        errors.append({"url": url, "strategy": strategy, "error": "Local Lighthouse unavailable or failed", "source": "local_lighthouse"})
                except Exception as lh_exc:
                    errors.append({"url": url, "strategy": strategy, "error": f"Local Lighthouse: {type(lh_exc).__name__}: {lh_exc}", "source": "local_lighthouse"})

    output = {
        "tested_urls": urls,
        "provider": provider,
        "api_key_used": bool(api_key),
        "local_lighthouse_fallback": provider == "api_with_fallback",
        "page_speed_endpoint": API_ENDPOINT,
        "attempts_per_request": MAX_ATTEMPTS,
        "results": results,
        "aggregate": aggregate(results),
        "errors": errors,
    }
    payload_out = json.dumps(output, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(payload_out, encoding="utf-8")
    else:
        print(payload_out)
    return 0 if results else 1


if __name__ == "__main__":
    sys.exit(main())
