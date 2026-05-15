#!/usr/bin/env python3
"""Local Lighthouse runner for the SEO/GEO audit skill.

This module collects mobile + desktop performance evidence by invoking
Lighthouse programmatically through `scripts/run_lighthouse.mjs`. The Google
PageSpeed Insights API path has been removed; performance evidence is now
always lab data from a local Chrome managed by chrome-launcher.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
LIGHTHOUSE_RUNNER = SCRIPT_DIR / "run_lighthouse.mjs"
LIGHTHOUSE_TIMEOUT = 180  # seconds per (url, strategy) run


def pick_urls_from_crawl(crawl_path: str, max_urls: int) -> list[str]:
    data = json.loads(Path(crawl_path).read_text(encoding="utf-8"))
    pages = data.get("pages", [])
    chosen: list[str] = []
    seen_templates: set[str] = set()

    def add(url: str, template: str) -> None:
        if url and url not in chosen and len(chosen) < max_urls:
            chosen.append(url)
            seen_templates.add(template)

    # Performance evidence defaults to the landing page. Most audit value comes
    # from the homepage experience, and Lighthouse runs are expensive on
    # JS-heavy sites.
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


def summarize_lighthouse(lh_data: dict, url: str, strategy: str) -> dict:
    """Parse Lighthouse JSON output into a stable schema."""
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
    lab_metrics: dict[str, float] = {}
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
        "top_opportunities": opportunities[:8],
        "final_url": lh_data.get("finalUrl", url),
    }


def aggregate(results: list[dict]) -> dict:
    buckets: dict[str, list[dict]] = defaultdict(list)
    for item in results:
        buckets[item["strategy"]].append(item)

    summary: dict[str, dict] = {}
    for strategy, items in buckets.items():
        count = len(items) or 1
        category_avg: dict[str, float] = defaultdict(float)
        for item in items:
            for key, value in item.get("category_scores", {}).items():
                category_avg[key] += value
        summary[strategy] = {
            "tested_urls": [item["url"] for item in items],
            "average_category_scores": {k: round(v / count, 1) for k, v in category_avg.items()},
        }
    return summary


def run_lighthouse(url: str, strategy: str, timeout: int = LIGHTHOUSE_TIMEOUT) -> dict | None:
    """Invoke run_lighthouse.mjs and return the parsed Lighthouse JSON.

    Returns None on failure (node missing, npm deps missing, Chrome launch failure,
    Lighthouse error). Caller logs the error.
    """
    if not LIGHTHOUSE_RUNNER.exists():
        print(f"[pagespeed] Missing Lighthouse runner: {LIGHTHOUSE_RUNNER}", file=sys.stderr)
        return None

    cmd = ["node", str(LIGHTHOUSE_RUNNER), "--url", url, "--strategy", strategy]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        print("[pagespeed] node not found on PATH. Install Node.js to run Lighthouse.", file=sys.stderr)
        return None
    except subprocess.TimeoutExpired:
        print(f"[pagespeed] Lighthouse timeout after {timeout}s for {url} ({strategy})", file=sys.stderr)
        return None

    if proc.returncode != 0:
        stderr_tail = (proc.stderr or "").strip().splitlines()[-3:]
        print(
            f"[pagespeed] Lighthouse failed for {url} ({strategy}): "
            + " | ".join(stderr_tail),
            file=sys.stderr,
        )
        return None

    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        print(f"[pagespeed] Lighthouse output not JSON for {url} ({strategy}): {exc}", file=sys.stderr)
        return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run local Lighthouse for a set of URLs and emit a normalized JSON summary."
    )
    parser.add_argument("--url", action="append", default=[], help="URL to test. May be supplied multiple times.")
    parser.add_argument("--from-crawl", help="Read homepage-first URLs from crawl_sample.py JSON output.")
    parser.add_argument(
        "--max-urls",
        type=int,
        default=1,
        help="Maximum URLs to test. Default 1 (homepage); each URL is tested once for mobile and once for desktop.",
    )
    parser.add_argument("--out", help="Optional JSON output file.")
    parser.add_argument(
        "--timeout",
        type=int,
        default=LIGHTHOUSE_TIMEOUT,
        help=f"Per-run Lighthouse timeout in seconds. Default: {LIGHTHOUSE_TIMEOUT}.",
    )
    args = parser.parse_args()

    urls = list(dict.fromkeys(args.url))
    if args.from_crawl:
        urls.extend([u for u in pick_urls_from_crawl(args.from_crawl, args.max_urls) if u not in urls])
    urls = urls[: max(1, min(args.max_urls, 10))]
    if not urls:
        print("No URLs supplied.", file=sys.stderr)
        return 1

    results: list[dict] = []
    errors: list[dict] = []
    for url in urls:
        for strategy in ("mobile", "desktop"):
            lh_data = run_lighthouse(url, strategy, timeout=args.timeout)
            if lh_data is None:
                errors.append(
                    {
                        "url": url,
                        "strategy": strategy,
                        "error": "Local Lighthouse run failed (see stderr above).",
                        "source": "local_lighthouse",
                    }
                )
                continue
            results.append(summarize_lighthouse(lh_data, url, strategy))

    output = {
        "tested_urls": urls,
        "provider": "local_lighthouse",
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
