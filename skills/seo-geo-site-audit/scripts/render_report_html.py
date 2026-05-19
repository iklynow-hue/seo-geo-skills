#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


from _report_styles import PALETTE_CSS as _PALETTE_CSS
from language_packs import REPORT_PACKS as LANGUAGE_PACKS


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_language(value: str | None) -> str:
    raw = (value or "english").strip().lower()
    if raw in {"zh", "zh-cn", "zh-tw", "chinese", "中文", "简体中文", "繁體中文"}:
        return "zh"
    return "en"


def slugify(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", value.strip().lower())
    return value.strip("-") or "section"


def severity_class(value: str) -> str:
    return {
        "P0": "sev-p0",
        "P1": "sev-p1",
        "P2": "sev-p2",
        "P3": "sev-p3",
    }.get((value or "").upper(), "sev-generic")


def render_list(items: list[str], empty_label: str) -> str:
    """Render a list of prose strings.

    The payload is agent-authored, not user input, so inline HTML in items
    (e.g. <strong>, <code>) is treated as content, not escaped. The renderer
    only escapes user-untrusted fields like target_url, headers, and snapshot
    label/value pairs.
    """
    if not items:
        return f"<p class='empty'>{html.escape(empty_label)}</p>"
    return "<ul>" + "".join(f"<li>{item}</li>" for item in items) + "</ul>"


def render_issue_items(items: list[object], empty_label: str) -> str:
    """Render an issue list. Each item is a dict with severity + title + detail
    (canonical schema, see references/report-payload-template.json), or a
    legacy {severity, description, affected} shape kept for backwards
    compatibility. Prose fields pass through as HTML; severity badge is
    escaped because it comes from a small enum.
    """
    if not items:
        return f"<p class='empty'>{html.escape(empty_label)}</p>"
    rendered = []
    for item in items:
        if isinstance(item, dict):
            severity = str(item.get("severity", "")).upper()
            title = str(item.get("title", "")).strip()
            detail = str(item.get("detail", "")).strip()
            # Backwards compat: older payloads used description / affected
            if not title and not detail:
                description = str(item.get("description", "")).strip()
                affected = str(item.get("affected", "")).strip()
                if description:
                    detail = description
                    if affected:
                        detail = f"{detail}<br><small>Affected: {affected}</small>"
            if severity or title or detail:
                badge = f"<span class='severity {severity_class(severity)}'>{html.escape(severity or 'Issue')}</span>"
                # If a title is set, use it as the headline and detail as the body.
                # If only detail is set, render it as the headline alone (no body)
                # so the same prose doesn't appear twice.
                if title:
                    headline = title
                    body = f"<p>{detail}</p>" if detail else ""
                else:
                    headline = detail or severity or "Issue"
                    body = ""
                rendered.append(f"<li class='issue-item'>{badge}<div><strong>{headline}</strong>{body}</div></li>")
            continue
        rendered.append(f"<li>{item}</li>")
    return "<ul class='issues-list'>" + "".join(rendered) + "</ul>"


def render_snapshot(snapshot: list[dict], empty_label: str) -> str:
    if not snapshot:
        return f"<p class='empty'>{html.escape(empty_label)}</p>"
    cards = []
    for item in snapshot:
        label = html.escape(str(item.get("label", "")))
        value = html.escape(str(item.get("value", "")))
        cards.append(
            "<article class='snapshot-card'>"
            f"<div class='snapshot-label'>{label}</div>"
            f"<div class='snapshot-value'>{value}</div>"
            "</article>"
        )
    return "<div class='snapshot-grid'>" + "".join(cards) + "</div>"


def snapshot_label_key(label: str) -> str:
    normalized = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", label.strip().lower())
    mapping = {
        "target": "target",
        "目标": "target",
        "mode": "mode",
        "模式": "mode",
        "pagessampled": "pages_sampled",
        "已采样页面": "pages_sampled",
        "performanceevidence": "performance_evidence",
        "性能证据": "performance_evidence",
        "outputstyle": "output_style",
        "输出风格": "output_style",
        "confidence": "confidence",
        "置信度": "confidence",
    }
    return mapping.get(normalized, normalized)


def prepare_snapshot(snapshot: list[dict]) -> list[dict]:
    by_key: dict[str, dict] = {}
    ordered_unknown: list[dict] = []
    for item in snapshot:
        key = snapshot_label_key(str(item.get("label", "")))
        if key in {"output_style", "confidence"}:
            continue
        if key in {"target", "mode", "pages_sampled", "performance_evidence"}:
            by_key[key] = item
        else:
            ordered_unknown.append(item)
    ordered = []
    for key in ("target", "mode", "pages_sampled", "performance_evidence"):
        if key in by_key:
            ordered.append(by_key[key])
    ordered.extend(ordered_unknown)
    return ordered


def parse_number(value: object) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().rstrip("%").strip()
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def format_weight(value: object) -> str:
    if isinstance(value, str) and value.strip().endswith("%"):
        return value.strip()
    parsed = parse_number(value)
    if parsed is None:
        return str(value or "")
    return f"{parsed:g}%"


def compute_weighted_value(row: dict) -> float | None:
    weighted = parse_number(row.get("weighted_score", row.get("weighted")))
    if weighted is not None:
        return weighted
    score = parse_number(row.get("score"))
    weight = parse_number(row.get("weight"))
    if score is not None and weight is not None:
        return score * weight / 100.0
    return None


def compute_weighted_total(rows: list[dict]) -> float | None:
    total = 0.0
    found = False
    for row in rows:
        weighted = compute_weighted_value(row)
        if weighted is not None:
            total += weighted
            found = True
    return round(total, 2) if found else None


def format_generated_at(value: str, language: str) -> str:
    raw = (value or "").strip()
    if not raw:
        return raw
    try:
        normalized = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return raw
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone()
    if language == "zh":
        return parsed.strftime("%Y-%m-%d %H:%M")
    return parsed.strftime("%b %d, %Y %H:%M")


def render_score_table(rows: list[dict], ui: dict[str, str], empty_label: str) -> str:
    if not rows:
        return f"<p class='empty'>{html.escape(empty_label)}</p>"
    body_rows = []
    for row in rows:
        weighted_value = compute_weighted_value(row)
        body_rows.append(
            "<tr>"
            f"<td>{html.escape(str(row.get('section', '')))}</td>"
            f"<td>{html.escape(str(row.get('score', '')))}</td>"
            f"<td>{html.escape(format_weight(row.get('weight', '')))}</td>"
            f"<td>{html.escape(f'{weighted_value:g}' if weighted_value is not None else '')}</td>"
            f"<td>{html.escape(str(row.get('notes', row.get('note', ''))))}</td>"
            "</tr>"
        )
    weighted_total = compute_weighted_total(rows)
    summary_markup = ""
    if weighted_total is not None:
        summary_markup = (
            "<div class='score-total'>"
            f"<span>{html.escape(ui['weighted_total'])}</span>"
            f"<strong>{html.escape(f'{weighted_total:g} / 100')}</strong>"
            "</div>"
        )
    return (
        "<div class='scorecard-wrap'>"
        "<table class='score-table'>"
        "<thead><tr>"
        f"<th>{html.escape(ui['section'])}</th>"
        f"<th>{html.escape(ui['score'])}</th>"
        f"<th>{html.escape(ui['weight'])}</th>"
        f"<th>{html.escape(ui['weighted'])}</th>"
        f"<th>{html.escape(ui['notes'])}</th>"
        "</tr></thead>"
        f"<tbody>{''.join(body_rows)}</tbody></table>"
        f"{summary_markup}</div>"
    )


def render_performance_column(block: dict, heading: str, ui: dict[str, str], empty_label: str) -> str:
    if not block:
        return (
            "<article class='metric-card panel'>"
            f"<h3>{html.escape(heading)}</h3>"
            f"<p class='empty'>{html.escape(empty_label)}</p>"
            "</article>"
        )
    largest_issues = block.get("largest_issues", [])
    return (
        "<article class='metric-card panel'>"
        f"<h3>{html.escape(heading)}</h3>"
        "<dl class='metric-list'>"
        f"<div><dt>{html.escape(ui['average_performance'])}</dt><dd>{html.escape(str(block.get('average_performance', '')))}</dd></div>"
        f"<div><dt>{html.escape(ui['pattern'])}</dt><dd>{html.escape(str(block.get('pattern', '')))}</dd></div>"
        "</dl>"
        f"<div class='metric-subtitle'>{html.escape(ui['largest_issues'])}</div>"
        f"{render_list([str(item) for item in largest_issues], empty_label)}"
        "</article>"
    )


def build_html(payload: dict) -> str:
    language = normalize_language(payload.get("language"))
    ui = {**LANGUAGE_PACKS[language], **payload.get("ui_text", {})}

    title = str(payload.get("title", "SEO + GEO Audit Report"))
    display_title = str(payload.get("display_title", title))
    target_url = str(payload.get("target_url", ""))
    repo_url = str(payload.get("repo_url", "")).strip()
    repo_label = str(payload.get("repo_label", "SEO GEO Skills")).strip()
    generated_at = str(payload.get("generated_at", datetime.now(timezone.utc).replace(microsecond=0).isoformat()))
    snapshot = prepare_snapshot(payload.get("snapshot", []))
    section_scores = payload.get("section_scores", [])
    top_wins = [str(item) for item in payload.get("top_wins", [])]
    top_issues = [str(item) for item in payload.get("top_issues", [])]
    sections = payload.get("sections", [])
    pagespeed = payload.get("pagespeed_conclusion", {})
    roadmap = payload.get("roadmap", {})
    method_notes = [str(item) for item in payload.get("method_notes", [])]
    report_subject = str(payload.get("report_subject", "")).strip()
    if not report_subject:
        parsed = urlparse(target_url)
        report_subject = parsed.netloc or parsed.path or str(payload.get("target_domain", "")).strip()
    display_generated_at = format_generated_at(generated_at, language)
    report_heading = f"{ui['report_for']} {report_subject}".strip() if report_subject else display_title
    rendered_sections = []
    for section in sections:
        section_title = str(section.get("title", "Section"))
        section_id = slugify(section_title)
        passed = [str(item) for item in section.get("passed_items", [])]
        issues = section.get("issues", [])
        actions = [str(item) for item in section.get("recommended_actions", [])]
        passed_count = f"<span class='count'>{len(passed)}</span>" if passed else ""
        issues_count = f"<span class='count'>{len(issues)}</span>" if issues else ""
        actions_count = f"<span class='count'>{len(actions)}</span>" if actions else ""
        rendered_sections.append(
            f"<section class='finding-section panel' id='{section_id}'>"
            "<div class='section-heading'>"
            "<div>"
            f"<div class='section-kicker'>{html.escape(ui['section_findings'])}</div>"
            f"<h2>{html.escape(section_title)}</h2>"
            "</div>"
            f"<div class='score-pill'>{html.escape(str(section.get('score', '')))}</div>"
            "</div>"
            "<div class='finding-grid'>"
            "<article class='finding-block'>"
            f"<h3>{html.escape(ui['passed_items'])}{passed_count}</h3>"
            f"{render_list(passed, ui['not_provided'])}"
            "</article>"
            "<article class='finding-block issues-block'>"
            f"<h3>{html.escape(ui['issues'])}{issues_count}</h3>"
            f"{render_issue_items(issues, ui['not_provided'])}"
            "</article>"
            "<article class='finding-block'>"
            f"<h3>{html.escape(ui['recommended_actions'])}{actions_count}</h3>"
            f"{render_list(actions, ui['not_provided'])}"
            "</article>"
            "</div>"
            "</section>"
        )

    return f"""<!doctype html>
<html lang="{html.escape(language)}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)} - {html.escape(target_url)}</title>
  <style>
    /* Ollama-inspired minimalist palette. Pure white canvas, grayscale only,
       binary radius (12px containers / 9999px pills), zero shadows, system fonts.
       Palette tokens come from _report_styles.PALETTE_CSS. */
{_PALETTE_CSS}
    html {{ scroll-behavior: smooth; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: var(--font-body);
      font-size: 16px;
      line-height: 1.5;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
    }}
    a {{ color: var(--ink); text-decoration: none; border-bottom: 1px solid transparent; }}
    a:hover {{ border-bottom-color: var(--ink); }}
    main {{ max-width: 1080px; margin: 0 auto; padding: 24px 24px 96px; }}
    code, pre, .mono {{ font-family: var(--font-mono); }}

    /* --- Top navigation ----------------------------------------------- */
    .topbar {{
      position: sticky;
      top: 0;
      z-index: 40;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      padding: 12px 24px;
      background: var(--bg);
      border-bottom: 1px solid var(--line);
    }}
    .toplink {{
      color: var(--ink);
      font-family: var(--font-display);
      font-size: 14px;
      font-weight: 500;
      border-bottom: none;
    }}
    .nav {{ display: flex; gap: 6px; flex-wrap: wrap; justify-content: flex-end; }}
    .nav a {{
      color: var(--muted);
      padding: 8px 14px;
      border-radius: var(--radius-pill);
      background: var(--bg);
      border: 1px solid transparent;
      font-size: 13px;
      transition: background 120ms ease, color 120ms ease, border-color 120ms ease;
    }}
    .nav a:hover {{
      background: var(--line);
      color: var(--ink);
      border-color: var(--line);
    }}

    /* --- Hero --------------------------------------------------------- */
    .hero {{ padding: 80px 0 48px; }}
    h1 {{
      margin: 0 0 20px;
      font-family: var(--font-display);
      font-size: clamp(2.25rem, 5vw, 3rem);
      line-height: 1;
      letter-spacing: -0.02em;
      font-weight: 500;
      max-width: 28ch;
      overflow-wrap: anywhere;
    }}
    .report-prefix, .report-domain {{ color: var(--ink); }}
    .hero-meta {{ display: flex; gap: 8px; flex-wrap: wrap; margin-top: 8px; font-size: 14px; color: var(--muted-soft); }}
    .meta-chip {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 8px 16px;
      border-radius: var(--radius-pill);
      background: var(--bg);
      border: 1px solid var(--line);
      color: var(--muted);
    }}
    .meta-chip a {{ color: var(--ink); font-weight: 500; border-bottom-color: var(--line); }}
    .meta-chip a:hover {{ border-bottom-color: var(--ink); }}

    /* --- Panels ------------------------------------------------------- */
    .panel {{
      background: var(--bg);
      border: 1px solid var(--line);
      border-radius: var(--radius-container);
      padding: 28px;
      min-width: 0;
    }}
    .section-block {{ margin-top: 56px; }}
    .section-block > h2 {{
      font-family: var(--font-display);
      font-size: clamp(1.75rem, 3.5vw, 2.25rem);
      line-height: 1.11;
      letter-spacing: -0.01em;
      font-weight: 500;
      margin: 0 0 24px;
    }}

    /* --- Snapshot ----------------------------------------------------- */
    .snapshot-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(min(220px, 100%), 1fr));
      gap: 12px;
    }}
    .snapshot-card {{
      padding: 20px;
      border-radius: var(--radius-container);
      background: var(--surface);
      border: 1px solid var(--line);
      min-width: 0;
    }}
    .snapshot-label {{
      font-size: 12px;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      color: var(--muted-soft);
      margin-bottom: 8px;
    }}
    .snapshot-value {{
      font-family: var(--font-display);
      font-size: 20px;
      line-height: 1.2;
      font-weight: 500;
      letter-spacing: -0.01em;
      overflow-wrap: anywhere;
      word-break: break-word;
    }}

    /* --- Scorecard ---------------------------------------------------- */
    .scorecard-wrap {{ display: grid; gap: 20px; }}
    .score-table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
    .score-table th, .score-table td {{
      text-align: left;
      padding: 14px 12px;
      border-bottom: 1px solid var(--line);
      vertical-align: top;
      overflow-wrap: anywhere;
      word-break: break-word;
    }}
    .score-table thead th {{
      color: var(--muted-soft);
      font-weight: 500;
      font-size: 12px;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }}
    .score-table tbody tr:last-child td {{ border-bottom: none; }}
    .score-total {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      padding: 20px 24px;
      border-radius: var(--radius-container);
      background: var(--surface);
      border: 1px solid var(--line);
    }}
    .score-total span {{
      color: var(--muted-soft);
      font-size: 12px;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }}
    .score-total strong {{
      font-family: var(--font-display);
      font-size: 32px;
      line-height: 1;
      letter-spacing: -0.02em;
      font-weight: 500;
    }}
    .highlight-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(min(280px, 100%), 1fr));
      gap: 16px;
      margin-top: 24px;
    }}
    .highlight-card h3,
    .metric-card h3,
    .finding-block h3 {{
      margin: 0 0 14px;
      font-family: var(--font-display);
      font-size: 18px;
      letter-spacing: -0.01em;
      font-weight: 500;
      color: var(--ink-near);
    }}

    /* --- Section findings -------------------------------------------- */
    .finding-section {{ margin-top: 24px; }}
    .section-heading {{
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 24px;
    }}
    .section-heading > div:first-child {{ min-width: 0; flex: 1; }}
    .section-kicker {{
      color: var(--muted-soft);
      font-size: 11px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      margin-bottom: 6px;
    }}
    .section-heading h2 {{
      margin: 0;
      font-family: var(--font-display);
      font-size: clamp(1.25rem, 2.5vw, 1.5rem);
      line-height: 1.2;
      letter-spacing: -0.01em;
      font-weight: 500;
      overflow-wrap: anywhere;
      word-break: break-word;
    }}
    .score-pill {{
      flex-shrink: 0;
      padding: 8px 20px;
      border-radius: var(--radius-pill);
      background: var(--line);
      color: var(--ink-near);
      font-family: var(--font-display);
      font-size: 16px;
      font-weight: 500;
      min-width: 56px;
      text-align: center;
    }}
    /* Findings stack vertically — single comfortable reading column for CJK
       and long detail paragraphs. Wide screens get max-width, not extra cols. */
    .finding-grid {{
      display: grid;
      grid-template-columns: minmax(0, 1fr);
      gap: 16px;
    }}
    .finding-block {{
      padding: 24px 28px;
      border-radius: var(--radius-container);
      background: var(--bg);
      border: 1px solid var(--line);
      min-width: 0;
    }}
    .finding-block.issues-block {{ background: var(--surface); }}
    .finding-block h3 {{
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .finding-block .count {{
      font-family: var(--font-body);
      font-size: 13px;
      font-weight: 400;
      color: var(--muted-soft);
      letter-spacing: 0;
    }}

    /* --- Lists -------------------------------------------------------- */
    ul {{ margin: 0; padding-left: 20px; }}
    li {{ overflow-wrap: anywhere; word-break: break-word; }}
    li + li {{ margin-top: 8px; }}
    .issues-list {{ list-style: none; padding: 0; display: grid; gap: 16px; }}
    .issue-item {{
      display: grid;
      grid-template-columns: auto minmax(0, 1fr);
      gap: 10px;
      align-items: start;
    }}
    .issue-item > div {{ min-width: 0; }}
    .issue-item strong {{ overflow-wrap: anywhere; word-break: break-word; }}
    .severity {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 36px;
      padding: 4px 10px;
      border-radius: var(--radius-pill);
      font-family: var(--font-display);
      font-size: 11px;
      font-weight: 500;
      letter-spacing: 0.04em;
      flex-shrink: 0;
    }}
    /* Severity in pure grayscale — saturation conveyed by lightness, not hue */
    .sev-p0 {{ background: var(--ink); color: var(--bg); }}
    .sev-p1 {{ background: var(--ink-button); color: var(--bg); }}
    .sev-p2 {{ background: var(--line); color: var(--ink-near); }}
    .sev-p3 {{ background: var(--bg); color: var(--muted-soft); border: 1px solid var(--line); }}
    .sev-generic {{ background: var(--surface); color: var(--muted); border: 1px solid var(--line); }}
    .issue-item p {{ margin: 6px 0 0; color: var(--muted); font-size: 14px; overflow-wrap: anywhere; word-break: break-word; }}

    /* --- Performance / Roadmap --------------------------------------- */
    .metric-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(min(280px, 100%), 1fr));
      gap: 16px;
    }}
    .metric-card {{ background: var(--bg); }}
    .metric-list {{ display: grid; gap: 12px; margin: 0 0 16px; }}
    .metric-list div {{ display: grid; gap: 4px; }}
    .metric-list dt {{
      color: var(--muted-soft);
      font-size: 12px;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }}
    .metric-list dd {{
      margin: 0;
      font-family: var(--font-display);
      font-size: 18px;
      font-weight: 500;
      letter-spacing: -0.01em;
      overflow-wrap: anywhere;
    }}
    .metric-subtitle {{
      margin-bottom: 8px;
      color: var(--muted-soft);
      font-size: 12px;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }}
    .roadmap-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(min(220px, 100%), 1fr));
      gap: 14px;
    }}
    .roadmap-column {{
      padding: 20px;
      border-radius: var(--radius-container);
      background: var(--surface);
      border: 1px solid var(--line);
      min-width: 0;
    }}
    .roadmap-column h3 {{
      margin: 0 0 14px;
      font-family: var(--font-display);
      font-size: 18px;
      font-weight: 500;
      letter-spacing: -0.01em;
    }}
    /* Roadmap priority shading stays grayscale; rank is conveyed by tint depth */
    .roadmap-p0 {{ background: var(--ink); color: var(--bg); border-color: var(--ink); }}
    .roadmap-p0 h3, .roadmap-p0 li {{ color: var(--bg); }}
    .roadmap-p1 {{ background: var(--ink-button); color: var(--bg); border-color: var(--ink-button); }}
    .roadmap-p1 h3, .roadmap-p1 li {{ color: var(--bg); }}
    .roadmap-p2 {{ background: var(--surface); }}
    .roadmap-p3 {{ background: var(--bg); }}

    .empty {{ color: var(--silver); font-style: normal; margin: 0; }}
    footer {{
      margin-top: 80px;
      padding-top: 24px;
      border-top: 1px solid var(--line);
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      flex-wrap: wrap;
      color: var(--muted-soft);
      font-size: 13px;
    }}
    footer a {{ color: var(--ink); font-weight: 500; }}

    /* --- Responsive: stack cleanly + tighten chrome on small screens -- */
    @media (max-width: 768px) {{
      main {{ padding: 16px 16px 64px; }}
      .topbar {{ padding: 10px 16px; gap: 8px; }}
      .nav {{ gap: 4px; }}
      .nav a {{ padding: 6px 10px; font-size: 12px; }}
      .hero {{ padding: 40px 0 32px; }}
      .section-block {{ margin-top: 40px; }}
      .panel {{ padding: 20px; }}
      .section-heading {{ flex-direction: column; gap: 10px; }}
      .score-pill {{ align-self: flex-start; }}
      .score-total {{ padding: 16px 18px; }}
      .score-total strong {{ font-size: 24px; }}
      .score-table th, .score-table td {{ padding: 10px 8px; }}
    }}
    @media (max-width: 480px) {{
      main {{ padding: 12px 12px 56px; }}
      .topbar {{ flex-direction: column; align-items: flex-start; }}
      .hero {{ padding: 28px 0 24px; }}
      h1 {{ font-size: 1.875rem; }}
    }}
  </style>
</head>
<body>
  <div class="topbar">
    <a class="toplink" href="#top">{html.escape(ui['nav_top'])}</a>
    <nav class="nav">
      <a href="#snapshot">{html.escape(ui['nav_snapshot'])}</a>
      <a href="#scorecard">{html.escape(ui['nav_scorecard'])}</a>
      <a href="#sections">{html.escape(ui['nav_sections'])}</a>
      <a href="#performance">{html.escape(ui['nav_performance'])}</a>
      <a href="#roadmap">{html.escape(ui['nav_roadmap'])}</a>
      <a href="#method">{html.escape(ui['nav_method'])}</a>
    </nav>
  </div>
  <main>
    <section class="hero" id="top">
      <div>
        <h1><span class="report-prefix">{html.escape(ui['report_for'])}</span> <span class="report-domain">{html.escape(report_subject or display_title)}</span></h1>
        <div class="hero-meta">
          <span class="meta-chip">{html.escape(ui['generated_at'])}: {html.escape(display_generated_at)}</span>
          {f"<span class='meta-chip'><a href='{html.escape(repo_url)}'>{html.escape(repo_label)}</a></span>" if repo_url else ""}
        </div>
      </div>
    </section>

    <section class="section-block" id="snapshot">
      <h2>{html.escape(ui['nav_snapshot'])}</h2>
      {render_snapshot(snapshot, ui['not_provided'])}
    </section>

    <section class="section-block" id="scorecard">
      <article class="panel">
        <h2>{html.escape(ui['scorecard'])}</h2>
        {render_score_table(section_scores, ui, ui['not_provided'])}
      </article>
      <div class="highlight-grid">
        <article class="highlight-card wins panel">
          <h3>{html.escape(ui['top_wins'])}</h3>
          {render_list(top_wins, ui['not_provided'])}
        </article>
        <article class="highlight-card issues panel">
          <h3>{html.escape(ui['top_issues'])}</h3>
          {render_list(top_issues, ui['not_provided'])}
        </article>
      </div>
    </section>

    <section class="section-block" id="sections">
      <h2>{html.escape(ui['section_findings'])}</h2>
      {''.join(rendered_sections)}
    </section>

    <section class="section-block" id="performance">
      <h2>{html.escape(ui['pagespeed_conclusion'])}</h2>
      <div class="metric-grid">
        {render_performance_column(pagespeed.get('mobile', {}), ui['mobile'], ui, ui['not_provided'])}
        {render_performance_column(pagespeed.get('desktop', {}), ui['desktop'], ui, ui['not_provided'])}
      </div>
      {f"<div class='panel' style='margin-top:18px'>{render_list([str(pagespeed.get('note'))], ui['not_provided'])}</div>" if pagespeed.get('note') else ""}
    </section>

    <section class="section-block" id="roadmap">
      <h2>{html.escape(ui['prioritized_roadmap'])}</h2>
      <div class="roadmap-grid">
        <article class="roadmap-column roadmap-p0"><h3>P0</h3>{render_list([str(item) for item in roadmap.get('P0', [])], ui['not_provided'])}</article>
        <article class="roadmap-column roadmap-p1"><h3>P1</h3>{render_list([str(item) for item in roadmap.get('P1', [])], ui['not_provided'])}</article>
        <article class="roadmap-column roadmap-p2"><h3>P2</h3>{render_list([str(item) for item in roadmap.get('P2', [])], ui['not_provided'])}</article>
        <article class="roadmap-column roadmap-p3"><h3>P3</h3>{render_list([str(item) for item in roadmap.get('P3', [])], ui['not_provided'])}</article>
      </div>
    </section>

    <section class="section-block" id="method">
      <article class="panel">
        <h2>{html.escape(ui['method_notes'])}</h2>
        {render_list(method_notes, ui['not_provided'])}
      </article>
    </section>

    <footer>
      {f"{html.escape(ui['report_generated_by'])} <a href='{html.escape(repo_url)}'>{html.escape(repo_label)}</a>" if repo_url else ""}
    </footer>
  </main>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a polished HTML report from a structured SEO/GEO report JSON payload.")
    parser.add_argument("--report-json", required=True, help="Path to the structured report JSON payload.")
    parser.add_argument("--out", required=True, help="Output HTML path.")
    args = parser.parse_args()

    payload = load_json(Path(args.report_json))
    html_payload = build_html(payload)
    Path(args.out).write_text(html_payload, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
