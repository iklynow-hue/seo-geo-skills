#!/usr/bin/env python3
"""
SGEO to PDF Bridge
Transforms SGEO audit results into the JSON format expected by generate_pdf_report.py
"""

import json
from datetime import datetime
from urllib.parse import urlparse


def extract_platform_scores(results):
    """Extract platform readiness scores from brand_scanner results."""
    platforms = {
        "Google AI Overviews": 0,
        "ChatGPT": 0,
        "Perplexity": 0,
        "Gemini": 0,
        "Bing Copilot": 0,
    }

    # brand_scanner.py outputs a "platforms" dict with keys like
    # "youtube", "reddit", "wikipedia", "linkedin", "other".
    # Each value is a dict with presence booleans and metadata.
    # We estimate an overall brand-authority score from those and
    # distribute it across AI platforms as a proxy.
    brand_result = results.get("brand_scanner.py", {})
    brand_platforms = brand_result.get("platforms", {})

    if brand_platforms:
        presence_signals = 0
        total_checks = 0
        for _key, platform_data in brand_platforms.items():
            if isinstance(platform_data, dict):
                for v in platform_data.values():
                    if isinstance(v, bool):
                        total_checks += 1
                        if v:
                            presence_signals += 1

        if total_checks > 0:
            brand_score = min(100, int((presence_signals / total_checks) * 100))
        else:
            brand_score = 0

        if brand_score > 0:
            for platform in platforms:
                platforms[platform] = brand_score

    # If no data, use GEO score as baseline
    if all(score == 0 for score in platforms.values()):
        # Use category scores as proxy
        base_score = results.get("_composite_scores", {}).get("geo", 50)
        for platform in platforms:
            platforms[platform] = base_score

    return platforms


def extract_crawler_access(results):
    """Extract AI crawler access status from robots_checker results."""
    crawler_access = {}

    robots_result = results.get("robots_checker.py", {})
    # robots_checker.py outputs "ai_crawler_status" (not "ai_crawlers").
    # Values are status strings like "fully blocked", "not managed (allowed by default)", etc.
    ai_crawler_status = robots_result.get("ai_crawler_status", {})

    crawler_mapping = {
        "GPTBot": "ChatGPT",
        "ClaudeBot": "Claude",
        "PerplexityBot": "Perplexity",
        "Google-Extended": "Gemini",
        "Bingbot": "Bing Copilot",
    }

    for crawler_name, platform in crawler_mapping.items():
        if crawler_name in ai_crawler_status:
            status_str = ai_crawler_status[crawler_name]
            is_blocked = "blocked" in status_str.lower()
            crawler_access[crawler_name] = {
                "platform": platform,
                "status": "Blocked" if is_blocked else "Allowed",
                "recommendation": "Unblock for AI visibility" if is_blocked else "Keep allowed"
            }

    return crawler_access


def categorize_findings_by_priority(findings):
    """Categorize findings into quick wins, medium-term, and strategic."""
    quick_wins = []
    medium_term = []
    strategic = []

    for finding in findings:
        severity = finding.get("severity", "info")
        message = finding.get("message", "")

        # Quick wins: critical/warning issues with simple fixes
        if severity == "critical":
            if "robots" in message.lower() or "crawler" in message.lower():
                quick_wins.append(f"Fix: {message}")
            elif "schema" in message.lower() and "missing" in message.lower():
                medium_term.append(f"Implement: {message}")
            else:
                medium_term.append(f"Address: {message}")

        elif severity == "warning":
            if any(kw in message.lower() for kw in ["meta", "title", "description", "date"]):
                quick_wins.append(f"Update: {message}")
            else:
                medium_term.append(f"Improve: {message}")

        elif severity == "info":
            strategic.append(f"Consider: {message}")

    # Add default recommendations if lists are empty
    if not quick_wins:
        quick_wins = [
            "Allow all Tier 1 AI crawlers in robots.txt (GPTBot, ClaudeBot, PerplexityBot)",
            "Add publication and last-updated dates to all content pages",
            "Add author bylines with credentials to blog posts",
            "Create an llms.txt file to guide AI systems",
        ]

    if not medium_term:
        medium_term = [
            "Implement Organization schema with sameAs linking",
            "Add Article + Person schema to blog posts",
            "Restructure content with question-based headings",
            "Optimize content blocks for AI citability (134-167 words)",
        ]

    if not strategic:
        strategic = [
            "Build Wikipedia/Wikidata entity presence",
            "Develop Reddit community engagement strategy",
            "Create YouTube content aligned with AI queries",
            "Establish original research publication program",
        ]

    return quick_wins[:5], medium_term[:5], strategic[:5]


def generate_executive_summary(url, geo_score, category_scores):
    """Generate executive summary from audit results."""
    domain = urlparse(url).netloc
    score_label = get_score_label(geo_score)

    # Find strongest and weakest areas
    geo_cats = category_scores.get("geo", {})
    cat_scores = {cat: data["score"] for cat, data in geo_cats.items() if data["count"] > 0}

    if cat_scores:
        strongest = max(cat_scores.items(), key=lambda x: x[1])
        weakest = min(cat_scores.items(), key=lambda x: x[1])

        strongest_name = strongest[0].replace("_", " ").title()
        weakest_name = weakest[0].replace("_", " ").title()

        summary = (
            f"This report presents the findings of a comprehensive GEO audit conducted on {domain}. "
            f"The site achieved an overall GEO Readiness Score of {geo_score}/100, placing it in the "
            f"{score_label} tier. The strongest area is {strongest_name} ({strongest[1]:.0f}/100), "
            f"while {weakest_name} ({weakest[1]:.0f}/100) represents the biggest opportunity for improvement. "
            f"Implementing the recommended quick wins could increase the score by 10-15 points within 30 days."
        )
    else:
        summary = (
            f"This report presents the findings of a comprehensive GEO audit conducted on {domain}. "
            f"The site achieved an overall GEO Readiness Score of {geo_score}/100, placing it in the "
            f"{score_label} tier. Implementing the prioritized action plan will improve AI search visibility "
            f"across Google AI Overviews, ChatGPT, Perplexity, Gemini, and Bing Copilot."
        )

    return summary


def get_score_label(score):
    """Return label based on score value."""
    if score >= 85:
        return "Excellent"
    elif score >= 70:
        return "Good"
    elif score >= 55:
        return "Moderate"
    elif score >= 40:
        return "Below Average"
    else:
        return "Needs Attention"


def transform_sgeo_to_pdf_input(url, composite_scores, category_scores, findings, results):
    """
    Transform SGEO audit results to PDF input format.

    Args:
        url: Target URL
        composite_scores: Dict with 'seo' and 'geo' composite scores
        category_scores: Dict with category breakdowns
        findings: List of findings from extract_findings()
        results: Raw script results dict

    Returns:
        Dict in format expected by generate_pdf_report.py
    """
    domain = urlparse(url).netloc
    brand_name = domain.replace("www.", "").split(".")[0].title()

    geo_score = int(composite_scores.get("geo", 0))
    geo_cats = category_scores.get("geo", {})

    # Extract category scores for PDF
    scores = {
        "ai_citability": int(geo_cats.get("content_citability", {}).get("score", 0)),
        "brand_authority": int(geo_cats.get("brand_authority", {}).get("score", 0)),
        "content_eeat": int(geo_cats.get("content_quality", {}).get("score", 0)),
        "technical": int(geo_cats.get("technical_infrastructure", {}).get("score", 0)),
        "schema": int(geo_cats.get("structured_data", {}).get("score", 0)),
        "platform_optimization": int(geo_cats.get("platform_optimization", {}).get("score", 0)),
    }

    # Extract platform scores
    platforms = extract_platform_scores(results)

    # Extract crawler access
    crawler_access = extract_crawler_access(results)

    # Transform findings to PDF format
    pdf_findings = []
    for finding in findings:
        severity = finding.get("severity", "info")
        if severity == "critical":
            sev_label = "critical"
        elif severity == "warning":
            sev_label = "high"
        else:
            sev_label = "medium"

        pdf_findings.append({
            "severity": sev_label,
            "title": finding.get("message", "")[:80],
            "description": finding.get("message", "")
        })

    # Categorize into action plan
    quick_wins, medium_term, strategic = categorize_findings_by_priority(findings)

    # Generate executive summary
    executive_summary = generate_executive_summary(url, geo_score, category_scores)

    return {
        "url": url,
        "brand_name": brand_name,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "geo_score": geo_score,
        "scores": scores,
        "platforms": platforms,
        "findings": pdf_findings[:15],  # Limit to top 15 findings
        "crawler_access": crawler_access,
        "quick_wins": quick_wins,
        "medium_term": medium_term,
        "strategic": strategic,
        "executive_summary": executive_summary
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python sgeo_to_pdf_bridge.py <sgeo_results.json>")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        data = json.load(f)

    pdf_data = transform_sgeo_to_pdf_input(
        data["url"],
        data["composite_scores"],
        data["category_scores"],
        data["findings"],
        data["results"]
    )

    print(json.dumps(pdf_data, indent=2))
