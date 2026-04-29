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
SKILL_DIR = SCRIPT_DIR.parent
RUNS_DIR = SKILL_DIR / "runs"
CRAWL_SCRIPT = SCRIPT_DIR / "crawl_sample.py"
PAGESPEED_SCRIPT = SCRIPT_DIR / "pagespeed_batch.py"
DEFAULT_MAX_PAGESPEED_URLS = 1
MAX_CRAWL_PAGES = 50
MODE_DEFAULTS = {
    "fast": 1,
    "light": 10,
    "template": 50,
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
        "discovery_source": "Discovery source",
        "title": "Title",
        "raw_words": "Raw words",
        "rendered_words": "Rendered words",
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
        "discovery_source": "发现来源",
        "title": "标题",
        "raw_words": "Raw 字数",
        "rendered_words": "渲染后字数",
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
        path = RUNS_DIR / f"site-audit-{safe_host(url)}-{now_stamp()}"
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
    evidence_report_path: Path | None,
    final_report_json_path: Path | None,
    final_report_html_path: Path | None,
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
        "evidence_report_path": str(evidence_report_path) if evidence_report_path else None,
        "final_report_json_path": str(final_report_json_path) if final_report_json_path else None,
        "final_report_html_path": str(final_report_html_path) if final_report_html_path else None,
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


def label_mode(mode: str, max_pages: int, report_language: str) -> str:
    language = normalize_report_language(report_language)
    if language == "zh":
        return {
            "fast": f"快速检查（{max_pages} 页）",
            "light": f"轻量模板审核（{max_pages} 页）",
            "template": f"标准模板审核（{max_pages} 页）",
        }.get(mode, f"自定义样本（{max_pages} 页）")
    return {
        "fast": f"Fast check ({max_pages} page{'s' if max_pages != 1 else ''})",
        "light": f"Light template audit ({max_pages} pages)",
        "template": f"Standard template audit ({max_pages} pages)",
    }.get(mode, f"Custom sample ({max_pages} pages)")


def label_output_style(output_style: str, report_language: str) -> str:
    language = normalize_report_language(report_language)
    if language == "zh":
        return {
            "boss": "Boss",
            "operator": "Operator",
            "specialist": "Specialist",
        }.get(output_style, output_style)
    return output_style.title()


def build_final_report_seed(
    *,
    target_url: str,
    mode: str,
    output_style: str,
    max_pages: int,
    report_language: str,
    crawl_path: Path,
    pagespeed_path: Path | None,
    evidence_report_path: Path | None,
    final_report_html_path: Path | None,
) -> dict:
    crawl = read_json(crawl_path)
    pagespeed = read_json(pagespeed_path) if pagespeed_path and pagespeed_path.exists() else {}
    summary = crawl.get("summary", {})
    page_count = int(crawl.get("page_count", 0) or 0)
    pages_requiring_js_content = int(summary.get("pages_requiring_js_content", 0) or 0)
    pages_requiring_js_navigation = int(summary.get("pages_requiring_js_navigation", 0) or 0)
    pages_with_rendered_recovered_signals = int(summary.get("pages_with_rendered_recovered_signals", 0) or 0)
    pages_missing_signals_after_rendering = int(summary.get("pages_missing_signals_after_rendering", 0) or 0)
    pages_assisted_discovery = int(summary.get("pages_assisted_discovery", 0) or 0)
    pagespeed_provider = pagespeed.get("provider")
    pagespeed_errors = pagespeed.get("errors", [])
    language = normalize_report_language(report_language)
    if language == "zh":
        title = "SEO + GEO 审核报告"
        snapshot = [
            {"label": "目标", "value": urlsplit(target_url).netloc or target_url},
            {"label": "模式", "value": label_mode(mode, max_pages, report_language)},
            {"label": "输出风格", "value": label_output_style(output_style, report_language)},
            {"label": "置信度", "value": "待填写"},
            {"label": "已采样页面", "value": str(page_count)},
            {"label": "性能证据", "value": str(pagespeed_provider or "未收集")},
        ]
        intro = "请用最终输出语言写一句执行摘要，并补全下方各部分。"
        overall = {
            "score": "",
            "band": "待填写",
            "summary": "请在生成最终审核结论后填写总分说明。",
        }
        top_wins = ["请根据最终审核结论填写主要亮点。"]
        top_issues = ["请根据最终审核结论填写主要问题。"]
        method_notes = [
            "这是一次采样式审核，不是全站完整爬取。",
            f"当前包装脚本采样了 {page_count} 个页面。",
        ]
        if pagespeed_provider:
            method_notes.append(f"当前性能证据来源：{pagespeed_provider}。")
        if pagespeed_errors:
            method_notes.append("PageSpeed 存在部分失败，请在最终结论中明确说明。")
        if pages_requiring_js_content or pages_requiring_js_navigation or pages_assisted_discovery:
            method_notes.append(
                "搜索引擎基线提示："
                f"{pages_requiring_js_content} 个页面内容依赖 JS 渲染，"
                f"{pages_requiring_js_navigation} 个页面导航依赖 JS 渲染，"
                f"{pages_assisted_discovery} 个页面来自辅助发现。"
            )
        if pages_with_rendered_recovered_signals or pages_missing_signals_after_rendering:
            method_notes.append(
                "Googlebot 渲染模拟提示："
                f"{pages_with_rendered_recovered_signals} 个页面在渲染后补回了至少一个 raw 缺失信号，"
                f"{pages_missing_signals_after_rendering} 个页面渲染后仍有信号缺失。"
            )
    else:
        title = "SEO + GEO Audit Report"
        snapshot = [
            {"label": "Target", "value": urlsplit(target_url).netloc or target_url},
            {"label": "Mode", "value": label_mode(mode, max_pages, report_language)},
            {"label": "Output style", "value": label_output_style(output_style, report_language)},
            {"label": "Confidence", "value": "Fill after scoring"},
            {"label": "Pages sampled", "value": str(page_count)},
            {"label": "Performance evidence", "value": str(pagespeed_provider or "Not collected")},
        ]
        intro = "Replace this with a one-line executive framing in the final output language and then complete every section below."
        overall = {
            "score": "",
            "band": "Fill after scoring",
            "summary": "Summarize the overall result after you finish the final audit.",
        }
        top_wins = ["Fill these after writing the final audit conclusions."]
        top_issues = ["Fill these after writing the final audit conclusions."]
        method_notes = [
            "This audit is a sampled review, not a full-site crawl.",
            f"The wrapper sampled {page_count} page(s) in this run.",
        ]
        if pagespeed_provider:
            method_notes.append(f"Performance evidence currently comes from {pagespeed_provider}.")
        if pagespeed_errors:
            method_notes.append("PageSpeed recorded partial failures; mention that clearly in the final report.")
        if pages_requiring_js_content or pages_requiring_js_navigation or pages_assisted_discovery:
            method_notes.append(
                "Search baseline note: "
                f"{pages_requiring_js_content} page(s) depend on JS-rendered content, "
                f"{pages_requiring_js_navigation} page(s) depend on JS-rendered navigation, "
                f"and {pages_assisted_discovery} page(s) came from assisted discovery."
            )
        if pages_with_rendered_recovered_signals or pages_missing_signals_after_rendering:
            method_notes.append(
                "Googlebot rendering simulation note: "
                f"{pages_with_rendered_recovered_signals} page(s) recovered at least one raw-missing signal after rendering, "
                f"and {pages_missing_signals_after_rendering} page(s) still had missing signals after rendering."
            )

    section_titles = [
        "1. Technical SEO & Indexability" if language == "en" else "1. 技术 SEO 与可索引性",
        "2. On-Page SEO & Content Packaging" if language == "en" else "2. 页面 SEO 与内容包装",
        "3. Information Architecture & Internal Linking" if language == "en" else "3. 信息架构与内链",
        "4. GEO & AI Extractability" if language == "en" else "4. GEO 与 AI 可提取性",
        "5. EEAT & Trust Signals" if language == "en" else "5. EEAT 与信任信号",
        "6. Entity & Structured Data" if language == "en" else "6. 实体与结构化数据",
        "7. Performance & Page Experience" if language == "en" else "7. 性能与页面体验",
    ]
    section_scores = []
    sections = []
    weights = [20, 15, 10, 20, 15, 10, 10]
    for title_value, weight in zip(section_titles, weights):
        notes_value = (
            "Fill after scoring. Treat section score as 0-100 and weight as a percentage."
            if language == "en"
            else "请在评分后填写。板块得分按 100 分制理解，权重按百分比展示。"
        )
        section_scores.append(
            {
                "section": title_value.split(". ", 1)[-1],
                "score": "",
                "weight": f"{weight}%",
                "weighted_score": "",
                "notes": notes_value,
            }
        )
        sections.append(
            {
                "title": title_value,
                "score": "",
                "passed_items": [],
                "issues": [],
                "evidence": [],
                "recommended_actions": [],
            }
        )

    pagespeed_conclusion = {
        "mobile": {
            "average_performance": "",
            "pattern": "",
            "largest_issues": [],
        },
        "desktop": {
            "average_performance": "",
            "pattern": "",
            "largest_issues": [],
        },
        "note": "",
    }
    artifacts = [
        {"label": "crawl.json", "path": str(crawl_path)},
    ]
    if pagespeed_path:
        artifacts.append({"label": "pagespeed.json", "path": str(pagespeed_path)})
    if evidence_report_path:
        artifacts.append({"label": "evidence-report.html", "path": str(evidence_report_path)})
    if final_report_html_path:
        artifacts.append({"label": "audit-report.html", "path": str(final_report_html_path)})

    payload = {
        "title": title,
        "target_url": target_url,
        "language": report_language,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "intro": intro,
        "overall": overall,
        "snapshot": snapshot,
        "section_scores": section_scores,
        "top_wins": top_wins,
        "top_issues": top_issues,
        "sections": sections,
        "pagespeed_conclusion": pagespeed_conclusion,
        "roadmap": {"P0": [], "P1": [], "P2": [], "P3": []},
        "method_notes": method_notes,
        "artifacts": artifacts,
        "ui_text": {},
    }
    coverage_rates = summary.get("coverage_rates", {})
    if coverage_rates:
        coverage_parts = [f"{name}: {value}" for name, value in coverage_rates.items()]
        payload["method_notes"].append(
            ("Coverage rates: " if language == "en" else "覆盖率：") + ", ".join(coverage_parts)
        )
    return payload


def write_final_report_seed(
    final_report_json_path: Path,
    *,
    target_url: str,
    mode: str,
    output_style: str,
    max_pages: int,
    report_language: str,
    crawl_path: Path,
    pagespeed_path: Path | None,
    evidence_report_path: Path | None,
    final_report_html_path: Path | None,
) -> None:
    payload = build_final_report_seed(
        target_url=target_url,
        mode=mode,
        output_style=output_style,
        max_pages=max_pages,
        report_language=report_language,
        crawl_path=crawl_path,
        pagespeed_path=pagespeed_path,
        evidence_report_path=evidence_report_path,
        final_report_html_path=final_report_html_path,
    )
    final_report_json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


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
    rendering_title = "Raw 与渲染后覆盖率" if pack["html_lang"].startswith("zh") else "Raw vs Rendered Coverage"
    raw_coverage_title = "Raw baseline" if not pack["html_lang"].startswith("zh") else "Raw 基线"
    rendered_coverage_title = "Rendered DOM" if not pack["html_lang"].startswith("zh") else "渲染后 DOM"
    rendered_only_title = "Rendered-only signals" if not pack["html_lang"].startswith("zh") else "仅渲染后出现的信号"
    missing_after_render_title = "Missing after rendering" if not pack["html_lang"].startswith("zh") else "渲染后仍缺失的信号"

    page_rows = []
    for page in top_pages:
        page_rows.append(
            "<tr>"
            f"<td><a href=\"{html.escape(page.get('url', ''))}\">{html.escape(page.get('url', ''))}</a></td>"
            f"<td>{html.escape(str(page.get('template', '')))}</td>"
            f"<td>{html.escape(str(page.get('discovery_source', '')))}</td>"
            f"<td>{html.escape(str(page.get('status', '')))}</td>"
            f"<td>{html.escape(str(page.get('word_count', '')))}</td>"
            f"<td>{html.escape(str(page.get('rendered_word_count', '')))}</td>"
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
        <h2>{html.escape(rendering_title)}</h2>
        <h3>{html.escape(raw_coverage_title)}</h3>
        {fmt_dict_table(summary.get('raw_coverage_rates', {}), pack['signal'], pack['coverage_percent'], pack['no_data'])}
        <h3>{html.escape(rendered_coverage_title)}</h3>
        {fmt_dict_table(summary.get('rendered_coverage_rates', {}), pack['signal'], pack['coverage_percent'], pack['no_data'])}
        <h3>{html.escape(rendered_only_title)}</h3>
        {fmt_dict_table(summary.get('rendered_only_signal_counts', {}), pack['signal'], pack['pages'], pack['no_data'])}
        <h3>{html.escape(missing_after_render_title)}</h3>
        {fmt_dict_table(summary.get('missing_after_rendering_signal_counts', {}), pack['signal'], pack['pages'], pack['no_data'])}
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
          <tr><th>{html.escape(pack['url'])}</th><th>{html.escape(pack['template'])}</th><th>{html.escape(pack['discovery_source'])}</th><th>{html.escape(pack['status'])}</th><th>{html.escape(pack['raw_words'])}</th><th>{html.escape(pack['rendered_words'])}</th><th>{html.escape(pack['title'])}</th></tr>
        </thead>
        <tbody>
          {''.join(page_rows) or f'<tr><td colspan="7">{html.escape(pack["no_pages_sampled"])}</td></tr>'}
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
        description="Run a one-command SEO/GEO site audit sample with up to 50 pages."
    )
    parser.add_argument("url", help="Target site URL, usually the homepage.")
    parser.add_argument(
        "--mode",
        choices=sorted(MODE_DEFAULTS),
        default="light",
        help="Audit depth preset. Default: light.",
    )
    parser.add_argument("--max-pages", type=int, help="Override the crawl cap (1-50).")
    parser.add_argument(
        "--output-style",
        choices=("boss", "operator", "specialist"),
        default="operator",
        help="Report style to record alongside the audit artifacts.",
    )
    parser.add_argument(
        "--out-dir",
        help="Directory for audit artifacts. Defaults to <skill-dir>/runs/site-audit-<host>-<stamp>.",
    )
    parser.add_argument("--skip-pagespeed", action="store_true", help="Skip PageSpeed collection.")
    parser.add_argument(
        "--max-pagespeed-urls",
        type=int,
        default=DEFAULT_MAX_PAGESPEED_URLS,
        help="Maximum URLs to test with PageSpeed. Default is 1 homepage URL; raise this only when you need extra template coverage.",
    )
    parser.add_argument(
        "--html-report",
        action="store_true",
        help="Write an evidence HTML plus a seeded final-report.json alongside the crawl artifacts.",
    )
    parser.add_argument(
        "--report-language",
        default="english",
        help="Language for the wrapper evidence HTML and seeded final-report.json. Built-in localization currently supports English and Chinese.",
    )
    parser.add_argument(
        "--pagespeed-provider",
        choices=("local", "api", "api_with_fallback"),
        default="local",
        help="Performance evidence source. Default: local Lighthouse.",
    )
    parser.add_argument("--api-key", help="Google PageSpeed Insights API key.")
    parser.add_argument(
        "--fetcher",
        default="auto",
        choices=["auto", "scrapling", "lightpanda", "agent_browser", "chrome", "urllib"],
        help="Preferred fetcher for crawl. 'auto' tries Scrapling → Lightpanda → agent-browser → attached Chrome → urllib.",
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
    evidence_report_path = out_dir / "evidence-report.html" if args.html_report else None
    final_report_json_path = out_dir / "final-report.json" if args.html_report else None
    final_report_html_path = out_dir / "audit-report.html" if args.html_report else None

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

    if evidence_report_path:
        write_html_report(
            evidence_report_path,
            target_url=args.url,
            mode=args.mode,
            output_style=args.output_style,
            max_pages=max_pages,
            report_language=args.report_language,
            crawl_path=crawl_path,
            pagespeed_path=pagespeed_path_out,
        )
    if final_report_json_path:
        write_final_report_seed(
            final_report_json_path,
            target_url=args.url,
            mode=args.mode,
            output_style=args.output_style,
            max_pages=max_pages,
            report_language=args.report_language,
            crawl_path=crawl_path,
            pagespeed_path=pagespeed_path_out,
            evidence_report_path=evidence_report_path,
            final_report_html_path=final_report_html_path,
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
        evidence_report_path=evidence_report_path,
        final_report_json_path=final_report_json_path,
        final_report_html_path=final_report_html_path,
    )

    print(f"Audit artifacts saved to: {out_dir}")
    print(f"- Crawl JSON: {crawl_path}")
    if pagespeed_path_out:
        print(f"- PageSpeed JSON: {pagespeed_path_out}")
    else:
        print("- PageSpeed JSON: skipped")
    if evidence_report_path:
        print(f"- Evidence HTML: {evidence_report_path}")
    if final_report_json_path:
        print(f"- Final report JSON seed: {final_report_json_path}")
        print(f"- Final polished HTML target: {final_report_html_path}")
    print(f"- Run manifest: {manifest_path}")
    print(f"Recorded mode: {args.mode} ({max_pages} pages), output style: {args.output_style}")
    if final_report_json_path:
        print(
            "Note: evidence-report.html is the wrapper's evidence view. "
            "Fill final-report.json and run render-report-html to produce the polished audit-report.html."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
