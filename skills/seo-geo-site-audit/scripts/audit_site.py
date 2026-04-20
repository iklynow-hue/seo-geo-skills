#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit


SCRIPT_DIR = Path(__file__).resolve().parent
CRAWL_SCRIPT = SCRIPT_DIR / "crawl_sample.py"
PAGESPEED_SCRIPT = SCRIPT_DIR / "pagespeed_batch.py"
DEFAULT_MAX_PAGESPEED_URLS = 5
MODE_DEFAULTS = {
    "fast": 1,
    "template": 25,
    "full": 50,
    "deep": 100,
}


def now_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def safe_host(url: str) -> str:
    host = urlsplit(url).netloc.lower()
    return host.replace(":", "-") or "site"


def build_output_dir(url: str, out_dir: str | None) -> Path:
    if out_dir:
        path = Path(out_dir).expanduser().resolve()
    else:
        path = Path("/tmp") / f"site-audit-{safe_host(url)}-{now_stamp()}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def run_command(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def pick_max_pages(mode: str, override: int | None) -> int:
    if override is not None:
        return max(1, min(100, override))
    return MODE_DEFAULTS[mode]


def write_manifest(
    manifest_path: Path,
    *,
    target_url: str,
    mode: str,
    output_style: str,
    max_pages: int,
    crawl_path: Path,
    pagespeed_path: Path | None,
    html_summary_path: Path | None,
) -> None:
    crawl = read_json(crawl_path)
    pages = crawl.get("pages", [])
    pagespeed = read_json(pagespeed_path) if pagespeed_path and pagespeed_path.exists() else {}
    payload = {
        "target_url": target_url,
        "mode": mode,
        "output_style": output_style,
        "max_pages": max_pages,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "crawl_path": str(crawl_path),
        "pagespeed_path": str(pagespeed_path) if pagespeed_path else None,
        "html_summary_path": str(html_summary_path) if html_summary_path else None,
        "pages_sampled": len(pages),
        "pagespeed_urls_tested": pagespeed.get("tested_urls", []),
        "pagespeed_error_count": len(pagespeed.get("errors", [])) if pagespeed else 0,
    }
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def human_bool(value: bool) -> str:
    return "Yes" if value else "No"


def fmt_score(value: object) -> str:
    if isinstance(value, (int, float)):
        return f"{value:.1f}" if isinstance(value, float) and not float(value).is_integer() else str(int(value))
    return "n/a"


def fmt_dict_table(data: dict[str, object], key_label: str, value_label: str) -> str:
    if not data:
        return "<p>No data available.</p>"
    rows = [
        f"<tr><th>{html.escape(str(key))}</th><td>{html.escape(fmt_score(value))}</td></tr>"
        for key, value in data.items()
    ]
    return (
        "<table>"
        f"<thead><tr><th>{html.escape(key_label)}</th><th>{html.escape(value_label)}</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


def fmt_list(items: list[str]) -> str:
    if not items:
        return "<p>None</p>"
    return "<ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in items) + "</ul>"


def build_html_summary(
    *,
    target_url: str,
    mode: str,
    output_style: str,
    max_pages: int,
    crawl: dict,
    pagespeed: dict | None,
) -> str:
    summary = crawl.get("summary", {})
    pages = crawl.get("pages", [])
    site_signals = crawl.get("site_signals", {})
    security_headers = site_signals.get("security_headers", {})
    llms_txt = site_signals.get("llms_txt", {})
    top_pages = pages[: min(len(pages), 15)]
    issue_counts = summary.get("issue_counts", {})
    top_issues = dict(sorted(issue_counts.items(), key=lambda item: item[1], reverse=True)[:8])
    pagespeed_aggregate = (pagespeed or {}).get("aggregate", {})
    pagespeed_errors = (pagespeed or {}).get("errors", [])
    tested_urls = (pagespeed or {}).get("tested_urls", [])

    page_rows = []
    for page in top_pages:
        page_rows.append(
            "<tr>"
            f"<td><a href=\"{html.escape(page.get('url', ''))}\">{html.escape(page.get('url', ''))}</a></td>"
            f"<td>{html.escape(str(page.get('template', '')))}</td>"
            f"<td>{html.escape(str(page.get('status', '')))}</td>"
            f"<td>{html.escape(page.get('title', '')[:120])}</td>"
            "</tr>"
        )

    pagespeed_blocks = []
    for strategy in ("mobile", "desktop"):
        block = pagespeed_aggregate.get(strategy)
        if not block:
            pagespeed_blocks.append(
                f"<section><h3>{strategy.title()}</h3><p>No {strategy} PageSpeed data collected.</p></section>"
            )
            continue
        pagespeed_blocks.append(
            "<section>"
            f"<h3>{strategy.title()}</h3>"
            f"{fmt_dict_table(block.get('average_category_scores', {}), 'Category', 'Average score')}"
            f"<p><strong>Tested URLs:</strong> {html.escape(', '.join(block.get('tested_urls', [])) or 'None')}</p>"
            "</section>"
        )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SEO/GEO Audit Summary - {html.escape(target_url)}</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f6f1e8;
      --panel: #fffdf9;
      --ink: #1f1a17;
      --muted: #6d635b;
      --line: #d7ccc0;
      --accent: #8d4f2a;
      --accent-soft: #f2dfd0;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", serif;
      background: radial-gradient(circle at top, #fff6ee, var(--bg) 45%);
      color: var(--ink);
      line-height: 1.5;
    }}
    main {{
      max-width: 1120px;
      margin: 0 auto;
      padding: 32px 20px 64px;
    }}
    h1, h2, h3 {{
      font-family: "Avenir Next Condensed", "Arial Narrow", sans-serif;
      letter-spacing: 0.03em;
      text-transform: uppercase;
      margin: 0 0 12px;
    }}
    h1 {{ font-size: 2.6rem; }}
    h2 {{ font-size: 1.35rem; margin-top: 24px; }}
    h3 {{ font-size: 1rem; margin-top: 16px; }}
    p, li, td, th {{ font-size: 0.98rem; }}
    .lede {{
      color: var(--muted);
      max-width: 72ch;
      margin-bottom: 20px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 16px;
    }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 18px;
      box-shadow: 0 10px 30px rgba(67, 36, 16, 0.08);
    }}
    .callout {{
      background: var(--accent-soft);
      border-left: 4px solid var(--accent);
      padding: 14px 16px;
      border-radius: 12px;
      margin-top: 18px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
    }}
    th, td {{
      text-align: left;
      padding: 9px 10px;
      border-bottom: 1px solid var(--line);
      vertical-align: top;
    }}
    th {{
      color: var(--muted);
      font-weight: 600;
    }}
    a {{
      color: var(--accent);
      text-decoration: none;
    }}
    code {{
      background: #f3ece4;
      padding: 0.12rem 0.35rem;
      border-radius: 6px;
    }}
  </style>
</head>
<body>
  <main>
    <h1>SEO/GEO Audit Summary</h1>
    <p class="lede">Artifact summary for <strong>{html.escape(target_url)}</strong>. This page captures crawl coverage, structural signals, and any collected PageSpeed averages. Final scored conclusions should still be written using the scoring rubric and report template.</p>

    <section class="grid">
      <article class="panel">
        <h2>Snapshot</h2>
        <table>
          <tbody>
            <tr><th>Mode</th><td>{html.escape(mode)}</td></tr>
            <tr><th>Output style</th><td>{html.escape(output_style)}</td></tr>
            <tr><th>Crawl cap</th><td>{max_pages}</td></tr>
            <tr><th>Pages sampled</th><td>{crawl.get('page_count', 0)}</td></tr>
            <tr><th>PageSpeed URLs</th><td>{len(tested_urls)}</td></tr>
            <tr><th>PageSpeed errors</th><td>{len(pagespeed_errors)}</td></tr>
          </tbody>
        </table>
      </article>
      <article class="panel">
        <h2>Coverage Rates</h2>
        {fmt_dict_table(summary.get('coverage_rates', {}), 'Signal', 'Coverage %')}
      </article>
      <article class="panel">
        <h2>Template Mix</h2>
        {fmt_dict_table(summary.get('template_counts', {}), 'Template', 'Pages')}
      </article>
      <article class="panel">
        <h2>Key Site Signals</h2>
        <table>
          <tbody>
            <tr><th>llms.txt present</th><td>{human_bool(bool(llms_txt.get('present')))}</td></tr>
            <tr><th>llms.txt URL</th><td>{html.escape(str(llms_txt.get('url', 'n/a')))}</td></tr>
            <tr><th>Robots discovered sitemaps</th><td>{site_signals.get('sitemap', {}).get('urls_discovered', 0)}</td></tr>
            <tr><th>Processed sitemaps</th><td>{site_signals.get('sitemap', {}).get('sitemap_count_processed', 0)}</td></tr>
          </tbody>
        </table>
      </article>
    </section>

    <section class="panel">
      <h2>Security Headers</h2>
      {fmt_dict_table({key: ('present' if value else 'missing') for key, value in security_headers.items()}, 'Header', 'Status')}
    </section>

    <section class="grid">
      <article class="panel">
        <h2>Recurring Crawl Issues</h2>
        {fmt_dict_table(top_issues, 'Issue', 'Occurrences')}
      </article>
      <article class="panel">
        <h2>PageSpeed Coverage</h2>
        <p><strong>API key used:</strong> {human_bool(bool((pagespeed or {}).get('api_key_used')))}</p>
        <p><strong>Representative URLs:</strong> {html.escape(', '.join(tested_urls) or 'None')}</p>
        {fmt_list([f"{item.get('strategy', 'unknown')}: {item.get('url', 'n/a')} — {item.get('error', 'error')}" for item in pagespeed_errors])}
      </article>
    </section>

    <section class="grid">
      {''.join(pagespeed_blocks)}
    </section>

    <section class="panel">
      <h2>Sampled Pages</h2>
      <table>
        <thead>
          <tr><th>URL</th><th>Template</th><th>Status</th><th>Title</th></tr>
        </thead>
        <tbody>
          {''.join(page_rows) or '<tr><td colspan="4">No pages sampled.</td></tr>'}
        </tbody>
      </table>
    </section>

    <div class="callout">
      <strong>Reading this file:</strong> treat it as an audit artifact summary, not the final scorecard. Use the crawl and PageSpeed evidence here together with the scoring rubric to produce the final 0-100 section scores and roadmap.
    </div>
  </main>
</body>
</html>
"""


def write_html_summary(
    html_path: Path,
    *,
    target_url: str,
    mode: str,
    output_style: str,
    max_pages: int,
    crawl_path: Path,
    pagespeed_path: Path | None,
) -> None:
    crawl = read_json(crawl_path)
    pagespeed = read_json(pagespeed_path) if pagespeed_path and pagespeed_path.exists() else None
    html_payload = build_html_summary(
        target_url=target_url,
        mode=mode,
        output_style=output_style,
        max_pages=max_pages,
        crawl=crawl,
        pagespeed=pagespeed,
    )
    html_path.write_text(html_payload, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a one-command SEO/GEO site audit sample with optional PageSpeed prompting."
    )
    parser.add_argument("url", help="Target site URL, usually the homepage.")
    parser.add_argument(
        "--mode",
        choices=sorted(MODE_DEFAULTS),
        default="template",
        help="Audit depth preset. Default: template.",
    )
    parser.add_argument("--max-pages", type=int, help="Override the crawl cap (1-100).")
    parser.add_argument(
        "--output-style",
        choices=("boss", "operator", "specialist"),
        default="operator",
        help="Report style to record alongside the audit artifacts.",
    )
    parser.add_argument("--out-dir", help="Directory for audit artifacts. Defaults to /tmp/site-audit-<host>-<stamp>.")
    parser.add_argument("--skip-pagespeed", action="store_true", help="Skip PageSpeed collection.")
    parser.add_argument(
        "--max-pagespeed-urls",
        type=int,
        default=DEFAULT_MAX_PAGESPEED_URLS,
        help="Maximum representative URLs to test with PageSpeed.",
    )
    parser.add_argument(
        "--html-report",
        action="store_true",
        help="Write a static HTML summary artifact alongside the crawl and PageSpeed JSON files.",
    )
    parser.add_argument("--api-key", help="Google PageSpeed Insights API key.")
    parser.add_argument(
        "--prompt-pagespeed-key",
        action="store_true",
        help="Prompt securely for the PageSpeed API key if one is not already set.",
    )
    args = parser.parse_args()

    max_pages = pick_max_pages(args.mode, args.max_pages)
    out_dir = build_output_dir(args.url, args.out_dir)
    crawl_path = out_dir / "crawl.json"
    pagespeed_path = out_dir / "pagespeed.json"
    manifest_path = out_dir / "audit-run.json"
    html_summary_path = out_dir / "audit-summary.html" if args.html_report else None

    crawl_cmd = [
        sys.executable,
        str(CRAWL_SCRIPT),
        "--url",
        args.url,
        "--max-pages",
        str(max_pages),
        "--out",
        str(crawl_path),
    ]
    run_command(crawl_cmd)

    if args.skip_pagespeed:
        pagespeed_path_out: Path | None = None
    else:
        pagespeed_cmd = [
            sys.executable,
            str(PAGESPEED_SCRIPT),
            "--from-crawl",
            str(crawl_path),
            "--max-urls",
            str(max(1, min(10, args.max_pagespeed_urls))),
            "--out",
            str(pagespeed_path),
        ]
        if args.api_key:
            pagespeed_cmd.extend(["--api-key", args.api_key])
        if args.prompt_pagespeed_key:
            pagespeed_cmd.append("--prompt-api-key")
        run_command(pagespeed_cmd)
        pagespeed_path_out = pagespeed_path

    if html_summary_path:
        write_html_summary(
            html_summary_path,
            target_url=args.url,
            mode=args.mode,
            output_style=args.output_style,
            max_pages=max_pages,
            crawl_path=crawl_path,
            pagespeed_path=pagespeed_path_out,
        )

    write_manifest(
        manifest_path,
        target_url=args.url,
        mode=args.mode,
        output_style=args.output_style,
        max_pages=max_pages,
        crawl_path=crawl_path,
        pagespeed_path=pagespeed_path_out,
        html_summary_path=html_summary_path,
    )

    print(f"Audit artifacts saved to: {out_dir}")
    print(f"- Crawl JSON: {crawl_path}")
    if pagespeed_path_out:
        print(f"- PageSpeed JSON: {pagespeed_path_out}")
    else:
        print("- PageSpeed JSON: skipped")
    if html_summary_path:
        print(f"- HTML summary: {html_summary_path}")
    print(f"- Run manifest: {manifest_path}")
    print(f"Recorded mode: {args.mode} ({max_pages} pages), output style: {args.output_style}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
