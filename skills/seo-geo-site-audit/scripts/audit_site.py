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

# Import prerequisite checker from fetchers
from fetchers import check_prerequisites, print_prereq_summary


SCRIPT_DIR = Path(__file__).resolve().parent
CRAWL_SCRIPT = SCRIPT_DIR / "crawl_sample.py"
PAGESPEED_SCRIPT = SCRIPT_DIR / "pagespeed_batch.py"
DEFAULT_MAX_PAGESPEED_URLS = 5
MAX_CRAWL_PAGES = 25
MODE_DEFAULTS = {
    "fast": 1,
    "light": 10,
    "template": 25,
}

LANGUAGE_PACKS = {
    "en": {
        "html_lang": "en",
        "title_prefix": "SEO/GEO Audit Report",
        "heading": "SEO/GEO Audit Report",
        "lede": "Report view for <strong>{target_url}</strong>. This page captures crawl coverage, structural signals, and any collected performance averages. Final scored conclusions should still be written using the scoring rubric and report template.",
        "snapshot": "Snapshot",
        "mode": "Mode",
        "output_style": "Output style",
        "crawl_cap": "Crawl cap",
        "pages_sampled": "Pages sampled",
        "performance_urls": "Performance URLs",
        "performance_errors": "Performance errors",
        "coverage_rates": "Coverage Rates",
        "signal": "Signal",
        "coverage_percent": "Coverage %",
        "template_mix": "Template Mix",
        "template": "Template",
        "pages": "Pages",
        "key_site_signals": "Key Site Signals",
        "llms_txt_present": "llms.txt present",
        "llms_txt_url": "llms.txt URL",
        "robots_sitemaps": "Robots discovered sitemaps",
        "processed_sitemaps": "Processed sitemaps",
        "security_headers": "Security Headers",
        "header": "Header",
        "status": "Status",
        "present": "present",
        "missing": "missing",
        "recurring_crawl_issues": "Recurring Crawl Issues",
        "issue": "Issue",
        "occurrences": "Occurrences",
        "performance_coverage": "Performance Coverage",
        "provider": "Provider",
        "api_key_used": "API key used",
        "representative_urls": "Representative URLs",
        "tested_urls": "Tested URLs",
        "category": "Category",
        "average_score": "Average score",
        "sampled_pages": "Sampled Pages",
        "url": "URL",
        "title": "Title",
        "no_pages_sampled": "No pages sampled.",
        "no_performance_data": "No {strategy} performance data collected.",
        "reading_this_report": "Reading this report:",
        "reading_this_report_body": "treat it as a structured evidence report, not the final scorecard by itself. Use the crawl and performance evidence here together with the scoring rubric to produce the final 0-100 section scores and roadmap.",
        "yes": "Yes",
        "no": "No",
        "none": "None",
        "no_data": "No data available.",
    },
    "zh": {
        "html_lang": "zh",
        "title_prefix": "SEO/GEO 审核报告",
        "heading": "SEO/GEO 审核报告",
        "lede": "<strong>{target_url}</strong> 的报告视图。本页面汇总抓取覆盖、结构信号以及已收集的性能均值。最终评分结论仍应结合评分规则与报告模板来撰写。",
        "snapshot": "概览",
        "mode": "模式",
        "output_style": "输出风格",
        "crawl_cap": "抓取上限",
        "pages_sampled": "已采样页面",
        "performance_urls": "性能测试 URL 数",
        "performance_errors": "性能错误数",
        "coverage_rates": "覆盖率",
        "signal": "信号",
        "coverage_percent": "覆盖率 %",
        "template_mix": "模板分布",
        "template": "模板",
        "pages": "页面数",
        "key_site_signals": "关键站点信号",
        "llms_txt_present": "是否存在 llms.txt",
        "llms_txt_url": "llms.txt URL",
        "robots_sitemaps": "robots.txt 发现的站点地图",
        "processed_sitemaps": "已处理站点地图",
        "security_headers": "安全响应头",
        "header": "Header",
        "status": "状态",
        "present": "存在",
        "missing": "缺失",
        "recurring_crawl_issues": "重复出现的抓取问题",
        "issue": "问题",
        "occurrences": "出现次数",
        "performance_coverage": "性能覆盖",
        "provider": "来源",
        "api_key_used": "是否使用 API Key",
        "representative_urls": "代表性 URL",
        "tested_urls": "测试 URL",
        "category": "类别",
        "average_score": "平均得分",
        "sampled_pages": "采样页面",
        "url": "URL",
        "title": "标题",
        "no_pages_sampled": "没有采样页面。",
        "no_performance_data": "未收集 {strategy} 性能数据。",
        "reading_this_report": "阅读说明：",
        "reading_this_report_body": "请将其视为结构化证据报告，而不是最终评分卡本身。请结合抓取与性能证据以及评分规则，产出最终 0-100 分分项评分与实施路线图。",
        "yes": "是",
        "no": "否",
        "none": "无",
        "no_data": "暂无数据。",
    },
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


def run_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=check, text=True, capture_output=True)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def pick_max_pages(mode: str, override: int | None) -> int:
    if override is not None:
        return max(1, min(MAX_CRAWL_PAGES, override))
    return MODE_DEFAULTS[mode]


def write_manifest(
    manifest_path: Path,
    *,
    target_url: str,
    mode: str,
    output_style: str,
    max_pages: int,
    report_language: str,
    crawl_path: Path,
    pagespeed_path: Path | None,
    html_report_path: Path | None,
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
        "pagespeed_provider": pagespeed.get("provider"),
        "report_language": report_language,
        "html_report_path": str(html_report_path) if html_report_path else None,
        "pages_sampled": len(pages),
        "pagespeed_urls_tested": pagespeed.get("tested_urls", []),
        "pagespeed_error_count": len(pagespeed.get("errors", [])) if pagespeed else 0,
    }
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_report_language(value: str | None) -> str:
    raw = (value or "english").strip().lower()
    if raw in {"zh", "zh-cn", "zh-tw", "chinese", "中文", "简体中文", "繁體中文", "traditional chinese", "simplified chinese"}:
        return "zh"
    return "en"


def get_language_pack(value: str | None) -> dict[str, str]:
    return LANGUAGE_PACKS[normalize_report_language(value)]


def human_bool(value: bool, yes_label: str, no_label: str) -> str:
    return yes_label if value else no_label


def fmt_score(value: object) -> str:
    if isinstance(value, (int, float)):
        return f"{value:.1f}" if isinstance(value, float) and not float(value).is_integer() else str(int(value))
    return "n/a"


def fmt_dict_table(data: dict[str, object], key_label: str, value_label: str, no_data_label: str) -> str:
    if not data:
        return f"<p>{html.escape(no_data_label)}</p>"
    rows = [
        f"<tr><th>{html.escape(str(key))}</th><td>{html.escape(fmt_score(value))}</td></tr>"
        for key, value in data.items()
    ]
    return (
        "<table>"
        f"<thead><tr><th>{html.escape(key_label)}</th><th>{html.escape(value_label)}</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


def fmt_list(items: list[str], none_label: str) -> str:
    if not items:
        return f"<p>{html.escape(none_label)}</p>"
    return "<ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in items) + "</ul>"


def build_html_report(
    *,
    target_url: str,
    mode: str,
    output_style: str,
    max_pages: int,
    report_language: str,
    crawl: dict,
    pagespeed: dict | None,
) -> str:
    pack = get_language_pack(report_language)
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
                f"<section><h3>{html.escape(strategy.title())}</h3><p>{html.escape(pack['no_performance_data'].format(strategy=strategy))}</p></section>"
            )
            continue
        pagespeed_blocks.append(
            "<section>"
            f"<h3>{html.escape(strategy.title())}</h3>"
            f"{fmt_dict_table(block.get('average_category_scores', {}), pack['category'], pack['average_score'], pack['no_data'])}"
            f"<p><strong>{html.escape(pack['tested_urls'])}:</strong> {html.escape(', '.join(block.get('tested_urls', [])) or pack['none'])}</p>"
            "</section>"
        )

    return f"""<!doctype html>
<html lang="{html.escape(pack['html_lang'])}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(pack['title_prefix'])} - {html.escape(target_url)}</title>
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
    <h1>{html.escape(pack['heading'])}</h1>
    <p class="lede">{pack['lede'].format(target_url=html.escape(target_url))}</p>

    <section class="grid">
      <article class="panel">
        <h2>{html.escape(pack['snapshot'])}</h2>
        <table>
          <tbody>
            <tr><th>{html.escape(pack['mode'])}</th><td>{html.escape(mode)}</td></tr>
            <tr><th>{html.escape(pack['output_style'])}</th><td>{html.escape(output_style)}</td></tr>
            <tr><th>{html.escape(pack['crawl_cap'])}</th><td>{max_pages}</td></tr>
            <tr><th>{html.escape(pack['pages_sampled'])}</th><td>{crawl.get('page_count', 0)}</td></tr>
            <tr><th>{html.escape(pack['performance_urls'])}</th><td>{len(tested_urls)}</td></tr>
            <tr><th>{html.escape(pack['performance_errors'])}</th><td>{len(pagespeed_errors)}</td></tr>
          </tbody>
        </table>
      </article>
      <article class="panel">
        <h2>{html.escape(pack['coverage_rates'])}</h2>
        {fmt_dict_table(summary.get('coverage_rates', {}), pack['signal'], pack['coverage_percent'], pack['no_data'])}
      </article>
      <article class="panel">
        <h2>{html.escape(pack['template_mix'])}</h2>
        {fmt_dict_table(summary.get('template_counts', {}), pack['template'], pack['pages'], pack['no_data'])}
      </article>
      <article class="panel">
        <h2>{html.escape(pack['key_site_signals'])}</h2>
        <table>
          <tbody>
            <tr><th>{html.escape(pack['llms_txt_present'])}</th><td>{human_bool(bool(llms_txt.get('present')), pack['yes'], pack['no'])}</td></tr>
            <tr><th>{html.escape(pack['llms_txt_url'])}</th><td>{html.escape(str(llms_txt.get('url', 'n/a')))}</td></tr>
            <tr><th>{html.escape(pack['robots_sitemaps'])}</th><td>{site_signals.get('sitemap', {}).get('urls_discovered', 0)}</td></tr>
            <tr><th>{html.escape(pack['processed_sitemaps'])}</th><td>{site_signals.get('sitemap', {}).get('sitemap_count_processed', 0)}</td></tr>
          </tbody>
        </table>
      </article>
    </section>

    <section class="panel">
      <h2>{html.escape(pack['security_headers'])}</h2>
      {fmt_dict_table({key: (pack['present'] if value else pack['missing']) for key, value in security_headers.items()}, pack['header'], pack['status'], pack['no_data'])}
    </section>

    <section class="grid">
      <article class="panel">
        <h2>{html.escape(pack['recurring_crawl_issues'])}</h2>
        {fmt_dict_table(top_issues, pack['issue'], pack['occurrences'], pack['no_data'])}
      </article>
      <article class="panel">
        <h2>{html.escape(pack['performance_coverage'])}</h2>
        <p><strong>{html.escape(pack['provider'])}:</strong> {html.escape(str((pagespeed or {}).get('provider', 'n/a')))}</p>
        <p><strong>{html.escape(pack['api_key_used'])}:</strong> {human_bool(bool((pagespeed or {}).get('api_key_used')), pack['yes'], pack['no'])}</p>
        <p><strong>{html.escape(pack['representative_urls'])}:</strong> {html.escape(', '.join(tested_urls) or pack['none'])}</p>
        {fmt_list([f"{item.get('strategy', 'unknown')}: {item.get('url', 'n/a')} — {item.get('error', 'error')}" for item in pagespeed_errors], pack['none'])}
      </article>
    </section>

    <section class="grid">
      {''.join(pagespeed_blocks)}
    </section>

    <section class="panel">
      <h2>{html.escape(pack['sampled_pages'])}</h2>
      <table>
        <thead>
          <tr><th>{html.escape(pack['url'])}</th><th>{html.escape(pack['template'])}</th><th>{html.escape(pack['status'])}</th><th>{html.escape(pack['title'])}</th></tr>
        </thead>
        <tbody>
          {''.join(page_rows) or f'<tr><td colspan="4">{html.escape(pack["no_pages_sampled"])}</td></tr>'}
        </tbody>
      </table>
    </section>

    <div class="callout">
      <strong>{html.escape(pack['reading_this_report'])}</strong> {html.escape(pack['reading_this_report_body'])}
    </div>
  </main>
</body>
</html>
"""


def write_html_report(
    html_path: Path,
    *,
    target_url: str,
    mode: str,
    output_style: str,
    max_pages: int,
    report_language: str,
    crawl_path: Path,
    pagespeed_path: Path | None,
) -> None:
    crawl = read_json(crawl_path)
    pagespeed = read_json(pagespeed_path) if pagespeed_path and pagespeed_path.exists() else None
    html_payload = build_html_report(
        target_url=target_url,
        mode=mode,
        output_style=output_style,
        max_pages=max_pages,
        report_language=report_language,
        crawl=crawl,
        pagespeed=pagespeed,
    )
    html_path.write_text(html_payload, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a one-command SEO/GEO site audit sample with up to 25 pages."
    )
    parser.add_argument("url", help="Target site URL, usually the homepage.")
    parser.add_argument(
        "--mode",
        choices=sorted(MODE_DEFAULTS),
        default="template",
        help="Audit depth preset. Default: template.",
    )
    parser.add_argument("--max-pages", type=int, help="Override the crawl cap (1-25).")
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
        help="Write a static HTML report alongside the crawl and PageSpeed JSON files.",
    )
    parser.add_argument(
        "--report-language",
        default="english",
        help="Language for the HTML report. Built-in localization currently supports English and Chinese.",
    )
    parser.add_argument(
        "--pagespeed-provider",
        choices=("local", "api", "api_with_fallback"),
        default="local",
        help="Performance evidence source. Default: local Lighthouse.",
    )
    parser.add_argument("--api-key", help="Google PageSpeed Insights API key.")
    parser.add_argument(
        "--prompt-pagespeed-key",
        action="store_true",
        help="Prompt securely for the PageSpeed API key if one is not already set.",
    )
    parser.add_argument(
        "--fetcher",
        default="auto",
        choices=["auto", "scrapling", "lightpanda", "agent_browser", "urllib"],
        help="Preferred fetcher for crawl. 'auto' tries Scrapling → Lightpanda → agent-browser → urllib.",
    )
    parser.add_argument(
        "--local-lighthouse-fallback",
        action="store_true",
        help="Compatibility alias for --pagespeed-provider api_with_fallback.",
    )
    parser.add_argument(
        "--skip-prereq-check",
        action="store_true",
        help="Skip prerequisite detection.",
    )
    parser.add_argument(
        "--auto-install-prereqs",
        action="store_true",
        help="Auto-install missing fetcher prerequisites before running the audit.",
    )
    args = parser.parse_args()
    pagespeed_provider = "api_with_fallback" if args.local_lighthouse_fallback else args.pagespeed_provider

    max_pages = pick_max_pages(args.mode, args.max_pages)
    out_dir = build_output_dir(args.url, args.out_dir)
    crawl_path = out_dir / "crawl.json"
    pagespeed_path = out_dir / "pagespeed.json"
    manifest_path = out_dir / "audit-run.json"
    html_report_path = out_dir / "audit-report.html" if args.html_report else None

    # Run prerequisite check. Auto-install is opt-in because it mutates the machine.
    if not args.skip_prereq_check:
        print("Checking prerequisites...")
        prereq_status = check_prerequisites(auto_install=args.auto_install_prereqs)
        print_prereq_summary(prereq_status)
        print()

    crawl_cmd = [
        sys.executable,
        str(CRAWL_SCRIPT),
        "--url",
        args.url,
        "--max-pages",
        str(max_pages),
        "--fetcher",
        args.fetcher,
        "--out",
        str(crawl_path),
    ]
    crawl_result = run_command(crawl_cmd)
    if crawl_result.stdout:
        print(crawl_result.stdout, end="")
    if crawl_result.stderr:
        print(crawl_result.stderr, file=sys.stderr, end="")

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
            "--provider",
            pagespeed_provider,
            "--out",
            str(pagespeed_path),
        ]
        if args.api_key:
            pagespeed_cmd.extend(["--api-key", args.api_key])
        if args.prompt_pagespeed_key:
            pagespeed_cmd.append("--prompt-api-key")
        pagespeed_result = run_command(pagespeed_cmd, check=False)
        if pagespeed_result.stdout:
            print(pagespeed_result.stdout, end="")
        if pagespeed_result.stderr:
            print(pagespeed_result.stderr, file=sys.stderr, end="")
        if pagespeed_result.returncode != 0 and not pagespeed_path.exists():
            raise RuntimeError(
                "Performance collection failed before writing pagespeed.json. "
                "Check stderr output above for details."
            )
        if pagespeed_result.returncode != 0 and pagespeed_path.exists():
            print(
                "PageSpeed completed with partial or failed requests. Continuing with the saved PageSpeed JSON.",
                file=sys.stderr,
            )
        pagespeed_path_out = pagespeed_path

    if html_report_path:
        write_html_report(
            html_report_path,
            target_url=args.url,
            mode=args.mode,
            output_style=args.output_style,
            max_pages=max_pages,
            report_language=args.report_language,
            crawl_path=crawl_path,
            pagespeed_path=pagespeed_path_out,
        )

    write_manifest(
        manifest_path,
        target_url=args.url,
        mode=args.mode,
        output_style=args.output_style,
        max_pages=max_pages,
        report_language=args.report_language,
        crawl_path=crawl_path,
        pagespeed_path=pagespeed_path_out,
        html_report_path=html_report_path,
    )

    print(f"Audit artifacts saved to: {out_dir}")
    print(f"- Crawl JSON: {crawl_path}")
    if pagespeed_path_out:
        print(f"- PageSpeed JSON: {pagespeed_path_out}")
    else:
        print("- PageSpeed JSON: skipped")
    if html_report_path:
        print(f"- HTML report: {html_report_path}")
    print(f"- Run manifest: {manifest_path}")
    print(f"Recorded mode: {args.mode} ({max_pages} pages), output style: {args.output_style}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
