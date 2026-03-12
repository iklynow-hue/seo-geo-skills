#!/usr/bin/env python3
"""
SEO+GEO Master Audit Report Generator

Runs all audit scripts in parallel and generates an interactive HTML dashboard
with dual scoring (SEO + GEO) based on the MECE framework.

Usage:
    python generate_report.py https://example.com
    python generate_report.py https://example.com --output SGEO-REPORT.html
    python generate_report.py https://example.com --api-key YOUR_PAGESPEED_KEY
"""

import argparse
import html as html_lib
import json
import os
import subprocess
import sys
import tempfile
import time
import webbrowser
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from urllib.parse import urlparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FRAMEWORK_PATH = os.path.join(os.path.dirname(SCRIPT_DIR), "MECE-FRAMEWORK.md")

# MECE Framework Weights
MECE_WEIGHTS = {
    "seo": {
        "technical_infrastructure": 0.25,
        "on_page_optimization": 0.20,
        "content_quality": 0.15,
        "structured_data": 0.15,
        "social_signals": 0.05,
        "local_seo": 0.10,  # Optional, redistributed if not applicable
    },
    "geo": {
        "content_citability": 0.25,
        "brand_authority": 0.20,
        "technical_infrastructure": 0.15,
        "content_quality": 0.15,
        "ai_crawler_access": 0.10,
        "structured_data": 0.10,
        "platform_optimization": 0.05,
    }
}

# Script to MECE category mapping
SCRIPT_MAPPING = {
    # Technical Infrastructure (Shared)
    "robots_checker.py": {"category": "technical_infrastructure", "applies_to": ["seo", "geo"]},
    "security_headers.py": {"category": "technical_infrastructure", "applies_to": ["seo", "geo"]},
    "redirect_checker.py": {"category": "technical_infrastructure", "applies_to": ["seo", "geo"]},
    "broken_links.py": {"category": "technical_infrastructure", "applies_to": ["seo", "geo"]},
    "pagespeed.py": {"category": "technical_infrastructure", "applies_to": ["seo", "geo"]},

    # On-Page Optimization (SEO-only)
    "internal_links.py": {"category": "on_page_optimization", "applies_to": ["seo"]},

    # Content Citability (GEO-only)
    "citability_scorer.py": {"category": "content_citability", "applies_to": ["geo"]},

    # Content Quality (Shared)
    "readability.py": {"category": "content_quality", "applies_to": ["seo", "geo"]},
    "duplicate_content.py": {"category": "content_quality", "applies_to": ["seo", "geo"]},

    # Structured Data (Shared)
    "validate_schema.py": {"category": "structured_data", "applies_to": ["seo", "geo"]},

    # Brand Authority (GEO-only)
    "brand_scanner.py": {"category": "brand_authority", "applies_to": ["geo"]},

    # AI Crawler Access (GEO-only)
    "llms_txt_checker.py": {"category": "ai_crawler_access", "applies_to": ["geo"]},

    # Social Signals (SEO-only)
    "social_meta.py": {"category": "social_signals", "applies_to": ["seo"]},

    # Platform Optimization (GEO-only)
    "hreflang_checker.py": {"category": "platform_optimization", "applies_to": ["geo"]},

    # Link Profile (Shared - contributes to both)
    "link_profile.py": {"category": "structured_data", "applies_to": ["seo", "geo"]},
}


def run_script(script_name: str, url: str, api_key: str = None, timeout: int = 120) -> dict:
    """Run an analysis script and capture JSON output with rate limit handling."""
    script_path = os.path.join(SCRIPT_DIR, script_name)
    if not os.path.exists(script_path):
        return {
            "script": script_name,
            "error": f"Script not found: {script_name}",
            "score": 0
        }

    cmd = [sys.executable, script_path, url, "--json"]

    # Add API key for PageSpeed
    if script_name == "pagespeed.py" and api_key:
        cmd.extend(["--api-key", api_key])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
            data["script"] = script_name
            return data

        # Check for rate limiting
        stderr = result.stderr.strip()
        if "rate limit" in stderr.lower() or "429" in stderr:
            return {
                "script": script_name,
                "error": "Rate limited - retry later",
                "score": None,
                "rate_limited": True
            }

        return {
            "script": script_name,
            "error": stderr or f"Exit code {result.returncode}",
            "score": 0
        }

    except subprocess.TimeoutExpired:
        return {
            "script": script_name,
            "error": f"Timeout after {timeout}s",
            "score": 0
        }
    except json.JSONDecodeError as e:
        return {
            "script": script_name,
            "error": f"Invalid JSON: {str(e)}",
            "score": 0
        }
    except Exception as e:
        return {
            "script": script_name,
            "error": str(e),
            "score": 0
        }


def run_all_audits(url: str, api_key: str = None, max_workers: int = 5) -> dict:
    """Run all audit scripts in parallel."""
    results = {}
    scripts = list(SCRIPT_MAPPING.keys())

    print(f"Running {len(scripts)} audit scripts in parallel...")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_script = {
            executor.submit(run_script, script, url, api_key): script
            for script in scripts
        }

        for future in as_completed(future_to_script):
            script = future_to_script[future]
            try:
                result = future.result()
                results[script] = result

                status = "✓" if not result.get("error") else "✗"
                print(f"  {status} {script}")

            except Exception as e:
                results[script] = {
                    "script": script,
                    "error": str(e),
                    "score": 0
                }
                print(f"  ✗ {script} - {str(e)}")

    return results


def calculate_category_scores(results: dict) -> dict:
    """Calculate scores for each MECE category."""
    category_scores = {
        "seo": {},
        "geo": {}
    }

    # Initialize all categories
    for score_type in ["seo", "geo"]:
        for category in MECE_WEIGHTS[score_type].keys():
            category_scores[score_type][category] = {
                "score": 0,
                "count": 0,
                "scripts": []
            }

    # Aggregate script results into categories
    for script_name, result in results.items():
        if script_name not in SCRIPT_MAPPING:
            continue

        mapping = SCRIPT_MAPPING[script_name]
        category = mapping["category"]
        applies_to = mapping["applies_to"]

        # Extract score from result
        score = result.get("score", 0)
        if score is None:  # Rate limited
            score = 0

        # Normalize score to 0-100 if needed
        if isinstance(score, (int, float)):
            score = max(0, min(100, score))

        # Add to applicable score types
        for score_type in applies_to:
            if category in category_scores[score_type]:
                category_scores[score_type][category]["scripts"].append({
                    "name": script_name,
                    "score": score,
                    "result": result
                })
                category_scores[score_type][category]["score"] += score
                category_scores[score_type][category]["count"] += 1

    # Calculate average scores for each category
    for score_type in ["seo", "geo"]:
        for category, data in category_scores[score_type].items():
            if data["count"] > 0:
                data["score"] = data["score"] / data["count"]
            else:
                data["score"] = 0

    return category_scores


def calculate_composite_scores(category_scores: dict) -> dict:
    """Calculate final SEO and GEO composite scores."""
    composite = {
        "seo": 0,
        "geo": 0,
        "breakdown": {
            "seo": {},
            "geo": {}
        }
    }

    for score_type in ["seo", "geo"]:
        total_score = 0

        for category, weight in MECE_WEIGHTS[score_type].items():
            cat_score = category_scores[score_type][category]["score"]
            contribution = cat_score * weight
            total_score += contribution

            composite["breakdown"][score_type][category] = {
                "score": round(cat_score, 1),
                "weight": weight,
                "contribution": round(contribution, 1)
            }

        composite[score_type] = round(total_score, 1)

    return composite


def extract_findings(results: dict) -> list:
    """Extract all findings from audit results, grouped by MECE category."""
    findings = []

    for script_name, result in results.items():
        if script_name not in SCRIPT_MAPPING:
            continue

        mapping = SCRIPT_MAPPING[script_name]
        category = mapping["category"]

        # Extract issues/findings from result
        issues = result.get("issues", [])
        warnings = result.get("warnings", [])
        recommendations = result.get("recommendations", [])

        for issue in issues:
            findings.append({
                "category": category,
                "severity": "critical",
                "script": script_name,
                "message": issue if isinstance(issue, str) else issue.get("message", str(issue))
            })

        for warning in warnings:
            findings.append({
                "category": category,
                "severity": "warning",
                "script": script_name,
                "message": warning if isinstance(warning, str) else warning.get("message", str(warning))
            })

        for rec in recommendations:
            findings.append({
                "category": category,
                "severity": "info",
                "script": script_name,
                "message": rec if isinstance(rec, str) else rec.get("message", str(rec))
            })

    return findings


def generate_html_report(url: str, composite_scores: dict, category_scores: dict,
                        findings: list, results: dict, pdf_filename: str = None) -> str:
    """Generate interactive HTML dashboard."""

    domain = urlparse(url).netloc
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Category display names
    category_names = {
        "technical_infrastructure": "Technical Infrastructure",
        "on_page_optimization": "On-Page Optimization",
        "content_quality": "Content Quality",
        "structured_data": "Structured Data",
        "social_signals": "Social Signals",
        "local_seo": "Local SEO",
        "content_citability": "Content Citability",
        "brand_authority": "Brand Authority",
        "ai_crawler_access": "AI Crawler Access",
        "platform_optimization": "Platform Optimization"
    }

    # Generate findings HTML grouped by category
    findings_by_category = {}
    for finding in findings:
        cat = finding["category"]
        if cat not in findings_by_category:
            findings_by_category[cat] = []
        findings_by_category[cat].append(finding)

    findings_html = ""
    for category in sorted(findings_by_category.keys()):
        cat_findings = findings_by_category[category]
        findings_html += f"""
        <div class="findings-category">
            <h3>{category_names.get(category, category.replace('_', ' ').title())}</h3>
        """

        for finding in cat_findings:
            severity_class = finding["severity"]
            severity_icon = {
                "critical": "🔴",
                "warning": "⚠️",
                "info": "ℹ️",
                "pass": "✅"
            }.get(severity_class, "•")

            findings_html += f"""
            <div class="finding {severity_class}">
                <span class="severity-icon">{severity_icon}</span>
                <span class="finding-message">{html_lib.escape(finding['message'])}</span>
                <span class="finding-source">{finding['script']}</span>
            </div>
            """

        findings_html += "</div>"

    # Generate category breakdown table
    breakdown_html = """
    <table class="breakdown-table">
        <thead>
            <tr>
                <th>Category</th>
                <th>SEO Score</th>
                <th>SEO Weight</th>
                <th>GEO Score</th>
                <th>GEO Weight</th>
            </tr>
        </thead>
        <tbody>
    """

    all_categories = set(list(MECE_WEIGHTS["seo"].keys()) + list(MECE_WEIGHTS["geo"].keys()))

    for category in sorted(all_categories):
        cat_name = category_names.get(category, category.replace('_', ' ').title())

        seo_data = composite_scores["breakdown"]["seo"].get(category, {"score": "N/A", "weight": 0})
        geo_data = composite_scores["breakdown"]["geo"].get(category, {"score": "N/A", "weight": 0})

        seo_score = seo_data["score"] if seo_data["score"] != "N/A" else "—"
        geo_score = geo_data["score"] if geo_data["score"] != "N/A" else "—"

        seo_weight = f"{int(seo_data['weight'] * 100)}%" if seo_data["weight"] > 0 else "—"
        geo_weight = f"{int(geo_data['weight'] * 100)}%" if geo_data["weight"] > 0 else "—"

        seo_class = get_score_class(seo_score) if seo_score != "—" else ""
        geo_class = get_score_class(geo_score) if geo_score != "—" else ""

        breakdown_html += f"""
        <tr>
            <td class="category-name">{cat_name}</td>
            <td class="score {seo_class}">{seo_score}</td>
            <td class="weight">{seo_weight}</td>
            <td class="score {geo_class}">{geo_score}</td>
            <td class="weight">{geo_weight}</td>
        </tr>
        """

    breakdown_html += """
        </tbody>
    </table>
    """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SEO+GEO Audit Report - {html_lib.escape(domain)}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 3rem 2rem;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            font-weight: 700;
        }}

        .header .url {{
            font-size: 1.2rem;
            opacity: 0.9;
            margin-bottom: 0.5rem;
        }}

        .header .timestamp {{
            font-size: 0.9rem;
            opacity: 0.7;
        }}

        .scores-container {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
            padding: 3rem 2rem;
            background: #f8f9fa;
        }}

        .score-card {{
            background: white;
            border-radius: 12px;
            padding: 2rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            text-align: center;
        }}

        .score-card h2 {{
            font-size: 1.5rem;
            margin-bottom: 1.5rem;
            color: #333;
        }}

        .score-gauge {{
            position: relative;
            width: 200px;
            height: 200px;
            margin: 0 auto 1rem;
        }}

        .score-gauge svg {{
            transform: rotate(-90deg);
        }}

        .score-gauge circle {{
            fill: none;
            stroke-width: 20;
        }}

        .score-gauge .bg {{
            stroke: #e9ecef;
        }}

        .score-gauge .progress {{
            stroke-linecap: round;
            transition: stroke-dashoffset 1s ease;
        }}

        .score-value {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 3rem;
            font-weight: 700;
        }}

        .score-label {{
            font-size: 1rem;
            color: #666;
            margin-top: 0.5rem;
        }}

        .content {{
            padding: 2rem;
        }}

        .section {{
            margin-bottom: 3rem;
        }}

        .section h2 {{
            font-size: 1.8rem;
            margin-bottom: 1.5rem;
            color: #333;
            border-bottom: 3px solid #667eea;
            padding-bottom: 0.5rem;
        }}

        .breakdown-table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}

        .breakdown-table thead {{
            background: #667eea;
            color: white;
        }}

        .breakdown-table th {{
            padding: 1rem;
            text-align: left;
            font-weight: 600;
        }}

        .breakdown-table td {{
            padding: 1rem;
            border-bottom: 1px solid #e9ecef;
        }}

        .breakdown-table tbody tr:hover {{
            background: #f8f9fa;
        }}

        .category-name {{
            font-weight: 600;
            color: #333;
        }}

        .score {{
            font-weight: 700;
            font-size: 1.1rem;
        }}

        .score.excellent {{ color: #28a745; }}
        .score.good {{ color: #5cb85c; }}
        .score.fair {{ color: #ffc107; }}
        .score.poor {{ color: #fd7e14; }}
        .score.critical {{ color: #dc3545; }}

        .weight {{
            color: #666;
            font-size: 0.9rem;
        }}

        .findings-category {{
            margin-bottom: 2rem;
            background: white;
            border-radius: 8px;
            padding: 1.5rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}

        .findings-category h3 {{
            font-size: 1.3rem;
            margin-bottom: 1rem;
            color: #333;
        }}

        .finding {{
            padding: 0.75rem 1rem;
            margin-bottom: 0.5rem;
            border-radius: 6px;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}

        .finding.critical {{
            background: #fee;
            border-left: 4px solid #dc3545;
        }}

        .finding.warning {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
        }}

        .finding.info {{
            background: #e7f3ff;
            border-left: 4px solid #0dcaf0;
        }}

        .finding.pass {{
            background: #d4edda;
            border-left: 4px solid #28a745;
        }}

        .severity-icon {{
            font-size: 1.2rem;
            flex-shrink: 0;
        }}

        .finding-message {{
            flex: 1;
            color: #333;
        }}

        .finding-source {{
            font-size: 0.8rem;
            color: #666;
            font-family: monospace;
            flex-shrink: 0;
        }}

        @media (max-width: 768px) {{
            .scores-container {{
                grid-template-columns: 1fr;
            }}

            body {{
                padding: 1rem;
            }}

            .header h1 {{
                font-size: 1.8rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>SEO + GEO Master Audit</h1>
            <div class="url">{html_lib.escape(url)}</div>
            <div class="timestamp">Generated: {timestamp}</div>
            {f'<div style="margin-top: 1rem;"><a href="{pdf_filename}" download style="display: inline-block; background: white; color: #667eea; padding: 0.75rem 1.5rem; border-radius: 6px; text-decoration: none; font-weight: 600; box-shadow: 0 2px 8px rgba(0,0,0,0.2);">📄 Download PDF Report</a></div>' if pdf_filename else ''}
        </div>

        <div class="scores-container">
            <div class="score-card">
                <h2>SEO Score</h2>
                <div class="score-gauge">
                    <svg width="200" height="200">
                        <circle class="bg" cx="100" cy="100" r="90"/>
                        <circle class="progress" cx="100" cy="100" r="90"
                                stroke="{get_score_color(composite_scores['seo'])}"
                                stroke-dasharray="{565.48}"
                                stroke-dashoffset="{565.48 * (1 - composite_scores['seo'] / 100)}"/>
                    </svg>
                    <div class="score-value" style="color: {get_score_color(composite_scores['seo'])}">{composite_scores['seo']}</div>
                </div>
                <div class="score-label">Traditional Search Engine Optimization</div>
            </div>

            <div class="score-card">
                <h2>GEO Score</h2>
                <div class="score-gauge">
                    <svg width="200" height="200">
                        <circle class="bg" cx="100" cy="100" r="90"/>
                        <circle class="progress" cx="100" cy="100" r="90"
                                stroke="{get_score_color(composite_scores['geo'])}"
                                stroke-dasharray="{565.48}"
                                stroke-dashoffset="{565.48 * (1 - composite_scores['geo'] / 100)}"/>
                    </svg>
                    <div class="score-value" style="color: {get_score_color(composite_scores['geo'])}">{composite_scores['geo']}</div>
                </div>
                <div class="score-label">Generative Engine Optimization</div>
            </div>
        </div>

        <div class="content">
            <div class="section">
                <h2>Category Breakdown</h2>
                {breakdown_html}
            </div>

            <div class="section">
                <h2>Findings by Category</h2>
                {findings_html if findings_html else '<p style="color: #666;">No findings to display.</p>'}
            </div>
        </div>
    </div>
</body>
</html>"""

    return html


def get_score_color(score):
    """Get color for score gauge."""
    if score >= 90:
        return "#28a745"
    elif score >= 70:
        return "#5cb85c"
    elif score >= 50:
        return "#ffc107"
    elif score >= 30:
        return "#fd7e14"
    else:
        return "#dc3545"


def get_score_class(score):
    """Get CSS class for score."""
    if isinstance(score, str):
        return ""
    if score >= 90:
        return "excellent"
    elif score >= 70:
        return "good"
    elif score >= 50:
        return "fair"
    elif score >= 30:
        return "poor"
    else:
        return "critical"


def get_output_dir(url: str) -> str:
    """Create and return output directory: outputs/<site-name>/"""
    domain = urlparse(url).netloc.replace("www.", "")
    # Sanitize for filesystem
    safe_name = domain.replace(":", "_").replace("/", "_")
    project_root = os.path.dirname(SCRIPT_DIR)
    output_dir = os.path.join(project_root, "outputs", safe_name)
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def generate_pdf(url, composite_scores, category_scores, findings, results, output_path):
    """Generate PDF report using the bridge + PDF generator."""
    try:
        from sgeo_to_pdf_bridge import transform_sgeo_to_pdf_input
        from generate_pdf_report import generate_report as gen_pdf
    except ImportError:
        # Try with full path
        sys.path.insert(0, SCRIPT_DIR)
        from sgeo_to_pdf_bridge import transform_sgeo_to_pdf_input
        from generate_pdf_report import generate_report as gen_pdf

    pdf_data = transform_sgeo_to_pdf_input(
        url, composite_scores, category_scores, findings, results
    )

    # Also save the intermediate JSON for debugging/reuse
    json_path = output_path.replace(".pdf", ".json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(pdf_data, f, indent=2)

    gen_pdf(pdf_data, output_path)
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Generate SEO+GEO Master Audit Report with dual scoring"
    )
    parser.add_argument("url", help="URL to audit")
    parser.add_argument(
        "--output",
        default=None,
        help="Output HTML file (default: outputs/<site>/SGEO-REPORT.html)"
    )
    parser.add_argument(
        "--no-pdf",
        action="store_true",
        help="Skip PDF generation"
    )
    parser.add_argument(
        "--api-key",
        help="PageSpeed Insights API key (optional, avoids rate limits)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=5,
        help="Number of parallel workers (default: 5)"
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Don't open the HTML report in browser after generation"
    )

    args = parser.parse_args()

    # Determine output directory
    output_dir = get_output_dir(args.url)
    html_output = args.output or os.path.join(output_dir, "SGEO-REPORT.html")
    pdf_output = os.path.join(output_dir, "SGEO-REPORT.pdf")
    pdf_filename = "SGEO-REPORT.pdf"  # Relative name for HTML link

    print(f"\n{'='*60}")
    print(f"SEO+GEO Master Audit Report Generator")
    print(f"{'='*60}\n")
    print(f"Target URL: {args.url}")
    print(f"Output dir: {output_dir}")
    print(f"Framework: MECE (Mutually Exclusive, Collectively Exhaustive)")
    print(f"\n{'='*60}\n")

    # Run all audits in parallel
    start_time = time.time()
    results = run_all_audits(args.url, args.api_key, args.workers)
    elapsed = time.time() - start_time

    print(f"\n{'='*60}")
    print(f"Audit completed in {elapsed:.1f}s")
    print(f"{'='*60}\n")

    # Calculate scores
    print("Calculating MECE category scores...")
    category_scores = calculate_category_scores(results)

    print("Calculating composite SEO and GEO scores...")
    composite_scores = calculate_composite_scores(category_scores)

    print(f"\nFinal Scores:")
    print(f"  SEO Score: {composite_scores['seo']}/100")
    print(f"  GEO Score: {composite_scores['geo']}/100")

    # Extract findings
    print("\nExtracting findings...")
    findings = extract_findings(results)
    print(f"  Found {len(findings)} total findings")

    # Generate PDF first (so HTML can link to it)
    pdf_generated = False
    if not args.no_pdf:
        print(f"\nGenerating PDF report...")
        try:
            generate_pdf(args.url, composite_scores, category_scores,
                        findings, results, pdf_output)
            pdf_generated = True
            print(f"  ✓ PDF saved to: {pdf_output}")
        except Exception as e:
            print(f"  ✗ PDF generation failed: {e}")
            print(f"    (Install reportlab: pip install reportlab)")

    # Generate HTML report
    print(f"\nGenerating HTML report...")
    html = generate_html_report(
        args.url,
        composite_scores,
        category_scores,
        findings,
        results,
        pdf_filename=pdf_filename if pdf_generated else None
    )

    # Write HTML
    with open(html_output, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n{'='*60}")
    print(f"✓ HTML report: {html_output}")
    if pdf_generated:
        print(f"✓ PDF report:  {pdf_output}")
    print(f"{'='*60}\n")

    # Print summary
    print("Score Interpretation:")
    print("  90-100: Excellent - Maintain and monitor")
    print("  70-89:  Good - Minor optimizations")
    print("  50-69:  Fair - Significant improvements needed")
    print("  30-49:  Poor - Major overhaul required")
    print("  0-29:   Critical - Immediate action required")
    print()

    # Auto-open HTML report in default browser
    if not args.no_open:
        report_url = "file://" + os.path.abspath(html_output).replace("\\", "/")
        print(f"Opening report in browser...")
        webbrowser.open(report_url)


if __name__ == "__main__":
    main()
