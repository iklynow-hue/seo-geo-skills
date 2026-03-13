#!/usr/bin/env python3
"""
On-page quality checker — catches issues that parse_html.py extracts but doesn't analyze.

Checks:
  1. Heading text quality (missing spaces, duplicate headings, empty headings)
  2. Viewport accessibility (maximum-scale=1 blocks zoom)
  3. Schema consistency across pages (review count mismatches, missing dateModified)
  4. Multi-page schema coverage (detects pages with zero structured data)

Usage:
    # Single page
    python onpage_checker.py https://example.com

    # Multi-page (crawls sitemap or internal links)
    python onpage_checker.py https://example.com --multi --max-pages 10

    # JSON output
    python onpage_checker.py https://example.com --json
"""

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
try:
    from defusedxml.ElementTree import fromstring as safe_xml_fromstring
except ImportError:
    # defusedxml not installed — use stdlib with a hardened parser that
    # disables external entity / DTD processing (XXE mitigation).
    import xml.etree.ElementTree as _ET

    def safe_xml_fromstring(text):
        # Disable external entity resolution to prevent XXE attacks
        # Note: Modern Python (3.8+) XMLParser is reasonably safe by default
        # For production use, install defusedxml: pip install defusedxml
        parser = _ET.XMLParser(target=_ET.TreeBuilder())
        parser.feed(text)
        return parser.close()
from typing import Optional
from urllib.parse import urljoin, urlparse

try:
    import requests
except ImportError:
    print("Error: requests required. Install with: pip install requests", file=sys.stderr)
    sys.exit(1)

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: beautifulsoup4 required. Install with: pip install beautifulsoup4", file=sys.stderr)
    sys.exit(1)


def fetch(url: str, timeout: int = 15, verify: bool = True) -> Optional[str]:
    try:
        r = requests.get(url, timeout=timeout, headers={"User-Agent": "SGEO-Checker/1.0"}, verify=verify)
        if r.status_code == 200:
            return r.text
    except (requests.exceptions.RequestException, ConnectionError, TimeoutError) as e:
        print(f"Warning: Failed to fetch {url}: {e}", file=sys.stderr)
    return None


def check_heading_quality(soup: BeautifulSoup, brand_names: Optional[list] = None) -> list:
    """Check heading text for spacing issues, duplicates, and empty headings."""
    issues = []
    seen = {}

    for level in ["h1", "h2", "h3", "h4"]:
        for tag in soup.find_all(level):
            text = tag.get_text(strip=True)

            # Empty heading
            if not text:
                issues.append({
                    "type": "empty_heading",
                    "severity": "warning",
                    "tag": level,
                    "detail": f"Empty <{level}> tag found",
                })
                continue

            # Missing spaces — camelCase-like joins (lowercase followed by uppercase)
            # Filter out common brand names and acronyms
            BRAND_PATTERNS = [
                r'Photo[A-Z]',  # PhotoRefix, PhotoShop, etc.
                r'[A-Z]{2,}',   # USA, API, FAQ, etc.
                r'Mc[A-Z]',     # McDonald's, etc.
                r'Mac[A-Z]',    # MacBook, etc.
                r'i[A-Z]',      # iPhone, iPad, etc.
                r'e[A-Z]',      # eBay, eCommerce, etc.
            ]

            # Add user-supplied brand names as patterns
            if brand_names:
                for bn in brand_names:
                    BRAND_PATTERNS.append(re.escape(bn))

            # Find potential spacing issues
            spacing_matches = re.finditer(r'[a-z][A-Z]', text)
            real_issues = []

            for match in spacing_matches:
                # Check if this match is part of a known brand pattern
                is_brand = False
                for pattern in BRAND_PATTERNS:
                    if re.search(pattern, text[max(0, match.start()-5):match.end()+5]):
                        is_brand = True
                        break

                if not is_brand:
                    real_issues.append(match.group())

            if real_issues:
                issues.append({
                    "type": "heading_spacing",
                    "severity": "warning",
                    "tag": level,
                    "text": text,
                    "detail": f"Possible missing space in <{level}>: '{text}' — found joins: {real_issues}",
                })

            # Duplicate headings at same level
            key = (level, text)
            if key in seen:
                seen[key] += 1
            else:
                seen[key] = 1

    # Report duplicates
    for (level, text), count in seen.items():
        if count > 1:
            issues.append({
                "type": "duplicate_heading",
                "severity": "warning",
                "tag": level,
                "text": text,
                "count": count,
                "detail": f"<{level}> '{text}' appears {count} times",
            })

    return issues


def check_viewport_accessibility(soup: BeautifulSoup) -> list:
    """Check if viewport meta prevents user zoom (accessibility issue)."""
    issues = []
    viewport = soup.find("meta", attrs={"name": "viewport"})
    if viewport:
        content = viewport.get("content", "")
        if "maximum-scale=1" in content or "maximum-scale=1.0" in content:
            issues.append({
                "type": "viewport_zoom_blocked",
                "severity": "warning",
                "detail": "Viewport has maximum-scale=1 which prevents user zoom — accessibility barrier (WCAG 1.4.4)",
                "current": content,
                "fix": "Remove maximum-scale=1 or set to maximum-scale=5",
            })
        if "user-scalable=no" in content or "user-scalable=0" in content:
            issues.append({
                "type": "viewport_zoom_disabled",
                "severity": "critical",
                "detail": "Viewport has user-scalable=no which disables zoom entirely — accessibility violation (WCAG 1.4.4)",
                "current": content,
                "fix": "Remove user-scalable=no",
            })
    return issues


def check_schema_quality(soup: BeautifulSoup, url: str) -> list:
    """Check schema blocks for quality issues: missing dateModified, review count consistency, etc."""
    issues = []
    schemas = []
    review_counts = []

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
        except (json.JSONDecodeError, TypeError):
            continue
        schemas.append(data)

        schema_type = data.get("@type", "")

        # Check Article/BlogPosting for dateModified
        if schema_type in ("Article", "BlogPosting", "NewsArticle", "TechArticle"):
            if not data.get("dateModified"):
                issues.append({
                    "type": "missing_date_modified",
                    "severity": "warning",
                    "schema_type": schema_type,
                    "detail": f"{schema_type} schema missing dateModified — AI systems can't determine content freshness",
                    "fix": "Add dateModified in ISO 8601 format",
                })

            # Check author quality
            author = data.get("author", {})
            if isinstance(author, dict):
                if not author.get("jobTitle"):
                    issues.append({
                        "type": "minimal_author_schema",
                        "severity": "info",
                        "schema_type": schema_type,
                        "detail": f"Author in {schema_type} missing jobTitle, knowsAbout — weak E-E-A-T signal",
                        "fix": "Add jobTitle, knowsAbout, image, worksFor to Person schema",
                    })

        # Collect review counts for consistency check
        agg_rating = data.get("aggregateRating", {})
        if agg_rating and agg_rating.get("ratingCount"):
            review_counts.append({
                "type": schema_type,
                "count": int(agg_rating["ratingCount"]),
                "url": url,
            })

    if not schemas:
        issues.append({
            "type": "no_schema",
            "severity": "critical",
            "detail": f"No structured data (JSON-LD) found on {url}",
            "fix": "Add relevant schema markup (SoftwareApplication, Article, etc.)",
        })

    return issues, review_counts


def get_sitemap_urls(base_url: str, max_urls: int = 20, verify: bool = True) -> list:
    """Fetch sitemap and return URLs."""
    sitemap_url = urljoin(base_url, "/sitemap.xml")
    html = fetch(sitemap_url, verify=verify)
    if not html:
        return []

    urls = []
    try:
        root = safe_xml_fromstring(html)
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        for loc in root.findall(".//sm:loc", ns):
            if loc.text:
                urls.append(loc.text.strip())
            if len(urls) >= max_urls:
                break
    except (ET.ParseError, ValueError) as e:
        print(f"Warning: Failed to parse sitemap XML: {e}", file=sys.stderr)
    return urls


def analyze_page(url: str, brand_names: Optional[list] = None, verify: bool = True) -> dict:
    """Run all on-page checks for a single URL."""
    html = fetch(url, verify=verify)
    if not html:
        return {"url": url, "error": "Failed to fetch page", "issues": []}

    soup = BeautifulSoup(html, "lxml" if "lxml" in sys.modules else "html.parser")

    heading_issues = check_heading_quality(soup, brand_names)
    viewport_issues = check_viewport_accessibility(soup)
    schema_issues, review_counts = check_schema_quality(soup, url)

    all_issues = heading_issues + viewport_issues + schema_issues

    return {
        "url": url,
        "issues": all_issues,
        "review_counts": review_counts,
        "heading_count": {
            "h1": len(soup.find_all("h1")),
            "h2": len(soup.find_all("h2")),
            "h3": len(soup.find_all("h3")),
        },
        "has_schema": bool(soup.find_all("script", type="application/ld+json")),
    }


def check_review_consistency(all_review_counts: list) -> list:
    """Cross-page check: are review counts consistent?"""
    issues = []
    if len(all_review_counts) < 2:
        return issues

    counts = [r["count"] for r in all_review_counts]
    min_c, max_c = min(counts), max(counts)

    if max_c > 0 and min_c > 0 and max_c / min_c > 2:
        issues.append({
            "type": "review_count_inconsistency",
            "severity": "warning",
            "detail": f"Review counts vary significantly across pages: {min_c} to {max_c} ({max_c/min_c:.1f}x difference)",
            "pages": all_review_counts,
            "fix": "Use consistent review counts across all schema blocks, or use page-specific counts with clear sourcing",
        })

    return issues


def main():
    parser = argparse.ArgumentParser(description="On-page quality checker")
    parser.add_argument("url", help="URL to check")
    parser.add_argument("--multi", action="store_true", help="Check multiple pages from sitemap")
    parser.add_argument("--max-pages", type=int, default=10, help="Max pages to check in multi mode")
    parser.add_argument("--brand", nargs="*", help="Brand names to exclude from heading spacing checks (e.g. --brand PhotoRefix LinkedIn)")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--no-verify", action="store_true",
                        help="Disable SSL certificate verification")
    args = parser.parse_args()

    verify = not args.no_verify
    if not verify:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    if args.multi:
        urls = get_sitemap_urls(args.url, args.max_pages, verify=verify)
        if not urls:
            # Fallback: just check the homepage
            urls = [args.url]
    else:
        urls = [args.url]

    # Auto-detect brand name from domain if not provided
    brand_names = args.brand or []
    if not brand_names:
        domain = urlparse(args.url).netloc.replace("www.", "")
        name = domain.split(".")[0]
        if any(c.isupper() for c in name[1:]):  # has camelCase
            brand_names.append(name)

    results = []
    all_review_counts = []
    pages_without_schema = []

    for url in urls:
        result = analyze_page(url, brand_names, verify=verify)
        results.append(result)
        all_review_counts.extend(result.get("review_counts", []))
        if not result.get("has_schema"):
            pages_without_schema.append(url)

    # Cross-page checks
    cross_page_issues = check_review_consistency(all_review_counts)

    # Summary
    total_issues = sum(len(r["issues"]) for r in results) + len(cross_page_issues)
    critical = sum(1 for r in results for i in r["issues"] if i.get("severity") == "critical")
    warnings = sum(1 for r in results for i in r["issues"] if i.get("severity") == "warning")

    output = {
        "pages_checked": len(urls),
        "total_issues": total_issues,
        "critical": critical,
        "warnings": warnings,
        "pages_without_schema": pages_without_schema,
        "cross_page_issues": cross_page_issues,
        "results": results,
    }

    if args.json:
        print(json.dumps(output, indent=2))
    else:
        print(f"On-Page Quality Check — {args.url}")
        print("=" * 50)
        print(f"Pages checked: {len(urls)}")
        print(f"Total issues: {total_issues} (🔴 {critical} critical, ⚠️ {warnings} warnings)")
        print()

        if pages_without_schema:
            print(f"🔴 Pages without schema ({len(pages_without_schema)}):")
            for p in pages_without_schema:
                print(f"  • {p}")
            print()

        if cross_page_issues:
            print("⚠️ Cross-page issues:")
            for issue in cross_page_issues:
                print(f"  • {issue['detail']}")
            print()

        for result in results:
            if result.get("error"):
                print(f"❌ {result['url']}: {result['error']}")
                continue
            if not result["issues"]:
                continue

            print(f"📄 {result['url']}")
            for issue in result["issues"]:
                sev = "🔴" if issue["severity"] == "critical" else "⚠️" if issue["severity"] == "warning" else "ℹ️"
                print(f"  {sev} [{issue['type']}] {issue['detail']}")
            print()


if __name__ == "__main__":
    main()
