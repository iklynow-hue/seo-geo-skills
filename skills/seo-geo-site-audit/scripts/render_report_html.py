#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path


LANGUAGE_PACKS = {
    "en": {
        "nav_snapshot": "Snapshot",
        "nav_scorecard": "Scorecard",
        "nav_sections": "Findings",
        "nav_performance": "Performance",
        "nav_roadmap": "Roadmap",
        "nav_method": "Method",
        "eyebrow": "SEO + GEO Audit",
        "overall_score": "Overall Score",
        "top_wins": "Top Wins",
        "top_issues": "Top Issues",
        "scorecard": "Scorecard",
        "section_findings": "Section Findings",
        "passed_items": "Passed items",
        "issues": "Issues",
        "evidence": "Evidence",
        "recommended_actions": "Recommended actions",
        "pagespeed_conclusion": "PageSpeed Conclusion",
        "mobile": "Mobile",
        "desktop": "Desktop",
        "average_performance": "Average performance",
        "pattern": "Pattern",
        "largest_issues": "Largest issues",
        "prioritized_roadmap": "Prioritized Roadmap",
        "method_notes": "Method Notes",
        "generated_artifacts": "Artifacts",
        "section": "Section",
        "score": "Score",
        "weight": "Weight",
        "weighted": "Weighted",
        "notes": "Notes",
        "generated_at": "Generated",
        "not_provided": "Not provided",
    },
    "zh": {
        "nav_snapshot": "概览",
        "nav_scorecard": "评分表",
        "nav_sections": "分项发现",
        "nav_performance": "性能",
        "nav_roadmap": "路线图",
        "nav_method": "方法说明",
        "eyebrow": "SEO + GEO 审核",
        "overall_score": "总分",
        "top_wins": "主要亮点",
        "top_issues": "主要问题",
        "scorecard": "评分表",
        "section_findings": "分项发现",
        "passed_items": "通过项",
        "issues": "问题",
        "evidence": "证据",
        "recommended_actions": "建议动作",
        "pagespeed_conclusion": "PageSpeed 结论",
        "mobile": "移动端",
        "desktop": "桌面端",
        "average_performance": "平均性能",
        "pattern": "模式",
        "largest_issues": "最大问题",
        "prioritized_roadmap": "优先路线图",
        "method_notes": "方法说明",
        "generated_artifacts": "产物",
        "section": "分项",
        "score": "得分",
        "weight": "权重",
        "weighted": "加权",
        "notes": "说明",
        "generated_at": "生成时间",
        "not_provided": "未提供",
    },
}


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
    if not items:
        return f"<p class='empty'>{html.escape(empty_label)}</p>"
    return "<ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in items) + "</ul>"


def render_issue_items(items: list[object], empty_label: str) -> str:
    if not items:
        return f"<p class='empty'>{html.escape(empty_label)}</p>"
    rendered = []
    for item in items:
        if isinstance(item, dict):
            severity = str(item.get("severity", "")).upper()
            title = str(item.get("title", "")).strip()
            detail = str(item.get("detail", "")).strip()
            if severity or title or detail:
                badge = f"<span class='severity {severity_class(severity)}'>{html.escape(severity or 'Issue')}</span>"
                headline = html.escape(title or detail or severity or "Issue")
                body = f"<p>{html.escape(detail)}</p>" if detail and detail != title else ""
                rendered.append(f"<li class='issue-item'>{badge}<div><strong>{headline}</strong>{body}</div></li>")
            continue
        rendered.append(f"<li>{html.escape(str(item))}</li>")
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


def render_score_table(rows: list[dict], ui: dict[str, str], empty_label: str) -> str:
    if not rows:
        return f"<p class='empty'>{html.escape(empty_label)}</p>"
    body_rows = []
    for row in rows:
        body_rows.append(
            "<tr>"
            f"<td>{html.escape(str(row.get('section', '')))}</td>"
            f"<td>{html.escape(str(row.get('score', '')))}</td>"
            f"<td>{html.escape(str(row.get('weight', '')))}</td>"
            f"<td>{html.escape(str(row.get('weighted_score', row.get('weighted', ''))))}</td>"
            f"<td>{html.escape(str(row.get('notes', row.get('note', ''))))}</td>"
            "</tr>"
        )
    return (
        "<table class='score-table'>"
        "<thead><tr>"
        f"<th>{html.escape(ui['section'])}</th>"
        f"<th>{html.escape(ui['score'])}</th>"
        f"<th>{html.escape(ui['weight'])}</th>"
        f"<th>{html.escape(ui['weighted'])}</th>"
        f"<th>{html.escape(ui['notes'])}</th>"
        "</tr></thead>"
        f"<tbody>{''.join(body_rows)}</tbody></table>"
    )


def render_performance_column(block: dict, heading: str, ui: dict[str, str], empty_label: str) -> str:
    if not block:
        return (
            "<article class='metric-card'>"
            f"<h3>{html.escape(heading)}</h3>"
            f"<p class='empty'>{html.escape(empty_label)}</p>"
            "</article>"
        )
    largest_issues = block.get("largest_issues", [])
    return (
        "<article class='metric-card'>"
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
    target_url = str(payload.get("target_url", ""))
    intro = str(payload.get("intro", "")).strip()
    generated_at = str(payload.get("generated_at", datetime.now(timezone.utc).replace(microsecond=0).isoformat()))
    snapshot = payload.get("snapshot", [])
    overall = payload.get("overall", {})
    section_scores = payload.get("section_scores", [])
    top_wins = [str(item) for item in payload.get("top_wins", [])]
    top_issues = [str(item) for item in payload.get("top_issues", [])]
    sections = payload.get("sections", [])
    pagespeed = payload.get("pagespeed_conclusion", {})
    roadmap = payload.get("roadmap", {})
    method_notes = [str(item) for item in payload.get("method_notes", [])]
    artifacts = payload.get("artifacts", [])

    section_nav = "".join(
        f"<a href='#{slugify(str(section.get('title', '')))}'>{html.escape(str(section.get('title', 'Section')))}</a>"
        for section in sections
    )

    rendered_sections = []
    for section in sections:
        section_title = str(section.get("title", "Section"))
        section_id = slugify(section_title)
        rendered_sections.append(
            "<section class='finding-section panel' id='{id}'>"
            "<div class='section-heading'>"
            "<div>"
            f"<div class='section-kicker'>{html.escape(ui['section_findings'])}</div>"
            f"<h2>{html.escape(section_title)}</h2>"
            "</div>"
            f"<div class='score-pill'>{html.escape(str(section.get('score', '')))}</div>"
            "</div>"
            "<div class='finding-grid'>"
            "<article class='finding-block'>"
            f"<h3>{html.escape(ui['passed_items'])}</h3>"
            f"{render_list([str(item) for item in section.get('passed_items', [])], ui['not_provided'])}"
            "</article>"
            "<article class='finding-block'>"
            f"<h3>{html.escape(ui['issues'])}</h3>"
            f"{render_issue_items(section.get('issues', []), ui['not_provided'])}"
            "</article>"
            "<article class='finding-block'>"
            f"<h3>{html.escape(ui['evidence'])}</h3>"
            f"{render_list([str(item) for item in section.get('evidence', [])], ui['not_provided'])}"
            "</article>"
            "<article class='finding-block'>"
            f"<h3>{html.escape(ui['recommended_actions'])}</h3>"
            f"{render_list([str(item) for item in section.get('recommended_actions', [])], ui['not_provided'])}"
            "</article>"
            "</div>"
            "</section>"
        .format(id=section_id))

    artifact_markup = ""
    if artifacts:
        rows = []
        for item in artifacts:
            label = html.escape(str(item.get("label", "")))
            value = html.escape(str(item.get("path", "")))
            rows.append(f"<tr><th>{label}</th><td>{value}</td></tr>")
        artifact_markup = (
            "<section class='panel' id='artifacts'>"
            f"<h2>{html.escape(ui['generated_artifacts'])}</h2>"
            f"<table class='artifact-table'><tbody>{''.join(rows)}</tbody></table>"
            "</section>"
        )

    overall_band = html.escape(str(overall.get("band", "")))
    overall_summary = html.escape(str(overall.get("summary", "")))
    overall_score = html.escape(str(overall.get("score", "")))

    return f"""<!doctype html>
<html lang="{html.escape(language)}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)} - {html.escape(target_url)}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Noto+Sans:wght@400;500;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      color-scheme: light;
      --bg: #ffffff;
      --ink: #1c1c1e;
      --muted: #555a6a;
      --line: rgb(224,226,232);
      --blue: #5b76fe;
      --blue-pressed: #2a41b6;
      --panel: #ffffff;
      --coral: #ffc6c6;
      --rose: #ffd8f4;
      --teal: #c3faf5;
      --orange: #ffe6cd;
      --green: #d9f5e8;
      --yellow: #fff1bf;
      --radius-sm: 8px;
      --radius-md: 12px;
      --radius-lg: 24px;
      --shadow: rgb(224,226,232) 0px 0px 0px 1px;
      --font-display: 'Inter', ui-sans-serif, system-ui, sans-serif;
      --font-body: 'Noto Sans', 'Inter', sans-serif;
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      margin: 0;
      background:
        radial-gradient(circle at top left, rgba(255, 216, 244, 0.55), transparent 28%),
        radial-gradient(circle at top right, rgba(195, 250, 245, 0.45), transparent 28%),
        linear-gradient(180deg, #ffffff 0%, #fbfbfd 100%);
      color: var(--ink);
      font-family: var(--font-body);
      line-height: 1.55;
      -webkit-font-smoothing: antialiased;
    }}
    a {{ color: var(--blue); text-decoration: none; }}
    main {{ max-width: 1240px; margin: 0 auto; padding: 0 20px 80px; }}
    .topbar {{
      position: sticky;
      top: 0;
      z-index: 50;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 20px;
      padding: 12px 20px;
      background: rgba(255,255,255,0.86);
      backdrop-filter: blur(10px);
      box-shadow: var(--shadow);
    }}
    .brand {{
      font-family: var(--font-display);
      font-size: 15px;
      font-weight: 700;
      letter-spacing: 0.02em;
    }}
    .nav {{
      display: flex;
      gap: 16px;
      flex-wrap: wrap;
      font-size: 13px;
    }}
    .nav a {{ color: var(--muted); }}
    .hero {{
      padding: 64px 0 36px;
      display: grid;
      grid-template-columns: minmax(0, 1.5fr) minmax(320px, 0.8fr);
      gap: 20px;
      align-items: end;
    }}
    .eyebrow {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      border-radius: 999px;
      background: var(--orange);
      box-shadow: var(--shadow);
      font-family: var(--font-display);
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    h1 {{
      margin: 18px 0 14px;
      font-family: var(--font-display);
      font-size: clamp(2.6rem, 7vw, 4.6rem);
      line-height: 0.96;
      letter-spacing: -0.05em;
      font-weight: 800;
      max-width: 10ch;
    }}
    .hero-target {{
      font-size: 17px;
      color: var(--muted);
      max-width: 62ch;
    }}
    .hero-meta {{
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      margin-top: 18px;
      font-size: 13px;
      color: var(--muted);
    }}
    .panel {{
      background: var(--panel);
      border-radius: var(--radius-lg);
      box-shadow: var(--shadow);
      padding: 24px;
    }}
    .overall-card {{
      display: grid;
      gap: 18px;
      align-self: stretch;
      background: linear-gradient(160deg, rgba(91,118,254,0.08), rgba(255,255,255,0.95));
    }}
    .overall-kicker {{
      font-family: var(--font-display);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
    }}
    .overall-row {{
      display: flex;
      align-items: center;
      gap: 18px;
    }}
    .overall-score {{
      width: 104px;
      height: 104px;
      border-radius: 28px;
      display: grid;
      place-items: center;
      background: var(--blue);
      color: white;
      font-family: var(--font-display);
      font-size: 40px;
      font-weight: 800;
      box-shadow: 0 18px 36px rgba(91,118,254,0.22);
    }}
    .overall-band {{
      font-family: var(--font-display);
      font-size: 26px;
      font-weight: 700;
      line-height: 1.08;
      letter-spacing: -0.03em;
    }}
    .overall-summary {{
      color: var(--muted);
      font-size: 15px;
    }}
    .section-block {{ margin-top: 22px; }}
    .section-block h2 {{
      font-family: var(--font-display);
      font-size: 38px;
      line-height: 1.04;
      letter-spacing: -0.05em;
      margin: 0 0 16px;
    }}
    .snapshot-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 12px;
    }}
    .snapshot-card {{
      padding: 16px;
      border-radius: var(--radius-md);
      background: #fff;
      box-shadow: var(--shadow);
    }}
    .snapshot-label {{
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
      margin-bottom: 8px;
    }}
    .snapshot-value {{
      font-family: var(--font-display);
      font-size: 20px;
      line-height: 1.2;
      font-weight: 700;
      letter-spacing: -0.03em;
    }}
    .dual-grid {{
      display: grid;
      grid-template-columns: 1.1fr 0.9fr;
      gap: 18px;
      align-items: start;
    }}
    .highlight-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 18px;
    }}
    .highlight-card h3,
    .metric-card h3,
    .finding-block h3 {{
      margin: 0 0 12px;
      font-family: var(--font-display);
      font-size: 22px;
      letter-spacing: -0.03em;
    }}
    .highlight-card.wins {{ background: var(--teal); }}
    .highlight-card.issues {{ background: var(--coral); }}
    .score-table,
    .artifact-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }}
    .score-table th,
    .score-table td,
    .artifact-table th,
    .artifact-table td {{
      text-align: left;
      padding: 12px 10px;
      border-bottom: 1px solid var(--line);
      vertical-align: top;
    }}
    .score-table thead th {{ color: var(--muted); font-weight: 600; }}
    .finding-section {{ margin-top: 18px; }}
    .section-heading {{
      display: flex;
      align-items: start;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 18px;
    }}
    .section-kicker {{
      color: var(--muted);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: 6px;
    }}
    .section-heading h2 {{
      margin: 0;
      font-family: var(--font-display);
      font-size: 30px;
      line-height: 1.05;
      letter-spacing: -0.04em;
    }}
    .score-pill {{
      padding: 10px 16px;
      border-radius: 999px;
      background: var(--yellow);
      font-family: var(--font-display);
      font-size: 18px;
      font-weight: 800;
      min-width: 64px;
      text-align: center;
    }}
    .finding-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
    }}
    .finding-block {{
      padding: 18px;
      border-radius: var(--radius-md);
      background: rgba(255,255,255,0.9);
      box-shadow: var(--shadow);
    }}
    ul {{ margin: 0; padding-left: 18px; }}
    li + li {{ margin-top: 8px; }}
    .issues-list {{
      list-style: none;
      padding: 0;
      display: grid;
      gap: 12px;
    }}
    .issue-item {{
      display: grid;
      grid-template-columns: auto 1fr;
      gap: 10px;
      align-items: start;
    }}
    .severity {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 42px;
      padding: 6px 10px;
      border-radius: 999px;
      font-family: var(--font-display);
      font-size: 11px;
      font-weight: 800;
      letter-spacing: 0.06em;
      text-transform: uppercase;
    }}
    .sev-p0 {{ background: #600000; color: #fff; }}
    .sev-p1 {{ background: #ffd8f4; color: #5a2555; }}
    .sev-p2 {{ background: #ffe6cd; color: #7d4d00; }}
    .sev-p3 {{ background: #d9f5e8; color: #0d6540; }}
    .sev-generic {{ background: #eef0f6; color: #3b4252; }}
    .issue-item p {{
      margin: 6px 0 0;
      color: var(--muted);
      font-size: 14px;
    }}
    .metric-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 18px;
    }}
    .metric-card {{
      background: linear-gradient(180deg, rgba(253,224,240,0.42), rgba(255,255,255,0.92));
    }}
    .metric-list {{
      display: grid;
      gap: 10px;
      margin: 0 0 14px;
    }}
    .metric-list div {{
      display: grid;
      gap: 4px;
    }}
    .metric-list dt {{
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    .metric-list dd {{
      margin: 0;
      font-family: var(--font-display);
      font-size: 18px;
      font-weight: 700;
      letter-spacing: -0.03em;
    }}
    .metric-subtitle {{
      margin-bottom: 8px;
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    .roadmap-grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 14px;
    }}
    .roadmap-column {{
      padding: 18px;
      border-radius: var(--radius-md);
      box-shadow: var(--shadow);
      background: rgba(255,255,255,0.95);
    }}
    .roadmap-column h3 {{
      margin: 0 0 12px;
      font-family: var(--font-display);
      font-size: 24px;
    }}
    .roadmap-p0 {{ background: var(--coral); }}
    .roadmap-p1 {{ background: var(--rose); }}
    .roadmap-p2 {{ background: var(--orange); }}
    .roadmap-p3 {{ background: var(--green); }}
    .empty {{
      color: var(--muted);
      font-style: italic;
      margin: 0;
    }}
    footer {{
      margin-top: 28px;
      text-align: center;
      color: var(--muted);
      font-size: 12px;
    }}
    @media (max-width: 960px) {{
      .hero,
      .dual-grid,
      .highlight-grid,
      .metric-grid,
      .roadmap-grid,
      .finding-grid {{
        grid-template-columns: 1fr;
      }}
      .topbar {{
        align-items: start;
        flex-direction: column;
      }}
    }}
  </style>
</head>
<body>
  <div class="topbar">
    <div class="brand">{html.escape(title)}</div>
    <nav class="nav">
      <a href="#snapshot">{html.escape(ui['nav_snapshot'])}</a>
      <a href="#scorecard">{html.escape(ui['nav_scorecard'])}</a>
      <a href="#sections">{html.escape(ui['nav_sections'])}</a>
      <a href="#performance">{html.escape(ui['nav_performance'])}</a>
      <a href="#roadmap">{html.escape(ui['nav_roadmap'])}</a>
      <a href="#method">{html.escape(ui['nav_method'])}</a>
      {section_nav}
    </nav>
  </div>
  <main>
    <section class="hero">
      <div>
        <div class="eyebrow">{html.escape(ui['eyebrow'])}</div>
        <h1>{html.escape(title)}</h1>
        <div class="hero-target">{html.escape(target_url)}</div>
        {f"<p class='hero-target'>{html.escape(intro)}</p>" if intro else ""}
        <div class="hero-meta">
          <span>{html.escape(ui['generated_at'])}: {html.escape(generated_at)}</span>
          {f"<span>{html.escape(overall_band)}</span>" if overall_band else ""}
        </div>
      </div>
      <article class="overall-card panel">
        <div class="overall-kicker">{html.escape(ui['overall_score'])}</div>
        <div class="overall-row">
          <div class="overall-score">{overall_score}</div>
          <div>
            <div class="overall-band">{overall_band}</div>
            {f"<p class='overall-summary'>{overall_summary}</p>" if overall_summary else ""}
          </div>
        </div>
      </article>
    </section>

    <section class="section-block" id="snapshot">
      <h2>{html.escape(ui['nav_snapshot'])}</h2>
      {render_snapshot(snapshot, ui['not_provided'])}
    </section>

    <section class="section-block dual-grid" id="scorecard">
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

    {artifact_markup}

    <footer>{html.escape(title)}</footer>
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
