#!/usr/bin/env python3
from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

API_ENDPOINT = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"


def resolve_api_key(args: argparse.Namespace) -> str | None:
    api_key = args.api_key or os.getenv("PAGESPEED_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if api_key:
        return api_key
    if args.prompt_api_key:
        if not sys.stdin.isatty():
            raise RuntimeError("Cannot prompt for API key without an interactive terminal.")
        api_key = getpass.getpass("Enter Google PageSpeed Insights API key: ").strip()
        return api_key or None
    return None


def call_pagespeed(url: str, strategy: str, api_key: str | None) -> dict:
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
    with urllib.request.urlopen(req, timeout=60) as response:
        raw = response.read().decode("utf-8", errors="replace")
    return json.loads(raw)


def pick_urls_from_crawl(crawl_path: str, max_urls: int) -> list[str]:
    data = json.loads(Path(crawl_path).read_text(encoding="utf-8"))
    pages = data.get("pages", [])
    chosen = []
    seen_templates = set()

    def add(url: str, template: str) -> None:
        if url and url not in chosen and len(chosen) < max_urls:
            chosen.append(url)
            seen_templates.add(template)

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


def summarize_result(payload: dict, url: str, strategy: str) -> dict:
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Run PageSpeed Insights for a set of URLs.")
    parser.add_argument("--url", action="append", default=[], help="URL to test. May be supplied multiple times.")
    parser.add_argument("--from-crawl", help="Read representative URLs from crawl_sample.py JSON output.")
    parser.add_argument("--max-urls", type=int, default=5, help="Maximum number of URLs to test.")
    parser.add_argument("--api-key", help="PageSpeed API key. Falls back to env vars.")
    parser.add_argument(
        "--prompt-api-key",
        action="store_true",
        help="Prompt securely for a Google PageSpeed Insights API key if one is not already set.",
    )
    parser.add_argument("--out", help="Optional JSON output file.")
    args = parser.parse_args()

    urls = list(dict.fromkeys(args.url))
    if args.from_crawl:
        urls.extend([u for u in pick_urls_from_crawl(args.from_crawl, args.max_urls) if u not in urls])
    urls = urls[: max(1, min(args.max_urls, 10))]
    if not urls:
        print("No URLs supplied.", file=sys.stderr)
        return 1

    try:
        api_key = resolve_api_key(args)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    results = []
    errors = []
    for url in urls:
        for strategy in ("mobile", "desktop"):
            try:
                payload = call_pagespeed(url, strategy, api_key)
                results.append(summarize_result(payload, url, strategy))
            except Exception as exc:
                errors.append({"url": url, "strategy": strategy, "error": f"{type(exc).__name__}: {exc}"})

    output = {
        "tested_urls": urls,
        "api_key_used": bool(api_key),
        "results": results,
        "aggregate": aggregate(results),
        "errors": errors,
    }
    payload = json.dumps(output, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(payload, encoding="utf-8")
    else:
        print(payload)
    return 0 if results else 1


if __name__ == "__main__":
    sys.exit(main())
