#!/usr/bin/env python3
"""
Check for broken links on a web page.

Crawls all links (internal + external) on a page, checks HTTP status.
Reports broken (4xx/5xx), redirected (3xx), and timeout links.

Usage:
    python broken_links.py https://example.com
    python broken_links.py https://example.com --json
    python broken_links.py https://example.com --internal-only
"""

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse

try:
    import requests
except ImportError:
    print("Error: requests library required. Install with: pip install requests")
    sys.exit(1)

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: beautifulsoup4 library required. Install with: pip install beautifulsoup4")
    sys.exit(1)


HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; SEOSkill/1.0)"}

# Performance optimization: Create a session for connection pooling
# Reuses TCP connections across multiple requests for better performance
SESSION = requests.Session()
SESSION.headers.update(HEADERS)


def extract_links(html: str, base_url: str) -> list:
    """Extract all links from HTML content."""
    soup = BeautifulSoup(html, "html.parser")
    links = []
    seen = set()

    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()

        # Skip anchors, javascript, mailto, tel
        if href.startswith(("#", "javascript:", "mailto:", "tel:", "data:")):
            continue

        absolute = urljoin(base_url, href)
        if absolute in seen:
            continue
        seen.add(absolute)

        anchor_text = tag.get_text(strip=True)[:80] or "[no text]"
        links.append({
            "url": absolute,
            "anchor_text": anchor_text,
            "is_internal": urlparse(absolute).netloc == urlparse(base_url).netloc,
        })

    return links


def check_link(link: dict, session: requests.Session, timeout: int = 10, verify: bool = True) -> dict:
    """Check a single link's HTTP status."""
    url = link["url"]
    result = {**link, "status": None, "error": None, "redirect": None, "response_time_ms": None}

    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Performance optimization: Use session for connection pooling
            resp = session.head(url, timeout=timeout, allow_redirects=True, verify=verify)

            if resp.status_code == 429:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 3
                    time.sleep(wait_time)
                    continue
                else:
                    result["error"] = "rate_limited"
                    return result

            # Some servers reject HEAD, fall back to GET
            if resp.status_code == 405:
                resp = session.get(url, timeout=timeout, allow_redirects=True, verify=verify, stream=True)

            result["status"] = resp.status_code
            result["response_time_ms"] = round(resp.elapsed.total_seconds() * 1000)

            # Check if redirected
            if resp.history:
                result["redirect"] = {
                    "from": url,
                    "to": resp.url,
                    "hops": len(resp.history),
                    "codes": [r.status_code for r in resp.history],
                }
            return result

        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            result["error"] = "timeout"
            return result
        except requests.exceptions.ConnectionError:
            result["error"] = "connection_failed"
            return result
        except requests.exceptions.TooManyRedirects:
            result["error"] = "too_many_redirects"
            return result
        except requests.exceptions.RequestException as e:
            result["error"] = str(e)[:100]
            return result

    return result


def check_broken_links(url: str, internal_only: bool = False,
                       max_workers: int = 10, timeout: int = 10,
                       verify: bool = True) -> dict:
    """
    Check all links on a page for broken links.

    Args:
        url: Page URL to check
        internal_only: Only check internal links
        max_workers: Concurrent request threads
        timeout: Per-request timeout in seconds
        verify: Verify SSL certificates

    Returns:
        Dictionary with all link check results
    """
    result = {
        "page_url": url,
        "total_links": 0,
        "checked": 0,
        "broken": [],
        "redirected": [],
        "timeout": [],
        "healthy": 0,
        "summary": {},
        "issues": [],
        "error": None,
    }

    # Fetch page
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Performance optimization: Use session for connection pooling
            resp = SESSION.get(url, timeout=15, verify=verify)

            if resp.status_code == 429:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 3
                    print(f"  [broken_links] Rate limited. Retrying in {wait_time}s...", file=sys.stderr)
                    time.sleep(wait_time)
                    continue
                else:
                    result["error"] = "Rate limited. Wait a few minutes and try again."
                    return result

            if resp.status_code != 200:
                result["error"] = f"Failed to fetch page: HTTP {resp.status_code}"
                return result
            html = resp.text
            break

        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                print(f"  [broken_links] Timeout. Retrying...", file=sys.stderr)
                time.sleep(2)
                continue
            result["error"] = "Failed to fetch page: Request timed out"
            return result
        except requests.exceptions.RequestException as e:
            result["error"] = f"Failed to fetch page: {e}"
            return result

    # Extract links
    links = extract_links(html, url)
    if internal_only:
        links = [l for l in links if l["is_internal"]]

    result["total_links"] = len(links)

    if not links:
        result["issues"].append("⚠️ No links found on page")
        return result

    # Check all links concurrently
    checked = []
    total_links = len(links)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Performance optimization: Pass session to each worker for connection pooling
        futures = {executor.submit(check_link, link, SESSION, timeout, verify): link for link in links}
        for future in as_completed(futures):
            checked.append(future.result())

            # Progress indicator
            if len(checked) % 10 == 0 or len(checked) == total_links:
                progress_pct = int((len(checked) / total_links) * 100)
                print(f"Checking links: {len(checked)}/{total_links} ({progress_pct}%)...", file=sys.stderr)

    result["checked"] = len(checked)

    for link in checked:
        status = link["status"]

        if link["error"]:
            if link["error"] == "timeout":
                result["timeout"].append(link)
            else:
                result["broken"].append(link)
        elif status and status >= 400:
            result["broken"].append(link)
        elif link["redirect"]:
            result["redirected"].append(link)
        else:
            result["healthy"] += 1

    # Generate summary
    result["summary"] = {
        "total": result["total_links"],
        "healthy": result["healthy"],
        "broken": len(result["broken"]),
        "redirected": len(result["redirected"]),
        "timeout": len(result["timeout"]),
    }

    # Generate issues
    if result["broken"]:
        result["issues"].append(
            f"🔴 {len(result['broken'])} broken link(s) found"
        )
    if result["timeout"]:
        result["issues"].append(
            f"⚠️ {len(result['timeout'])} link(s) timed out"
        )
    if result["redirected"]:
        chains = [l for l in result["redirected"]
                  if l.get("redirect", {}).get("hops", 0) > 1]
        if chains:
            result["issues"].append(
                f"⚠️ {len(chains)} redirect chain(s) detected (>1 hop)"
            )

    return result


def main():
    parser = argparse.ArgumentParser(description="Check for broken links on a page")
    parser.add_argument("url", help="Page URL to check")
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")
    parser.add_argument("--internal-only", "-i", action="store_true",
                        help="Only check internal links")
    parser.add_argument("--workers", "-w", type=int, default=10,
                        help="Concurrent workers (default: 10)")
    parser.add_argument("--timeout", "-t", type=int, default=10,
                        help="Per-link timeout in seconds (default: 10)")
    parser.add_argument("--no-verify", action="store_true",
                        help="Disable SSL certificate verification")

    args = parser.parse_args()

    verify = not args.no_verify
    if not verify:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    result = check_broken_links(args.url, internal_only=args.internal_only,
                                max_workers=args.workers, timeout=args.timeout,
                                verify=verify)

    if args.json:
        print(json.dumps(result, indent=2))
        return

    if result["error"]:
        print(f"Error: {result['error']}")
        sys.exit(1)

    print(f"Broken Link Check — {result['page_url']}")
    print("=" * 50)
    s = result["summary"]
    print(f"Total: {s['total']} | ✅ Healthy: {s['healthy']} | "
          f"🔴 Broken: {s['broken']} | ↪️ Redirected: {s['redirected']} | "
          f"⏱️ Timeout: {s['timeout']}")

    if result["broken"]:
        print(f"\n🔴 Broken Links:")
        for link in result["broken"]:
            status = link["status"] or link["error"]
            loc = "internal" if link["is_internal"] else "external"
            print(f"  [{status}] ({loc}) {link['url']}")
            print(f"         anchor: \"{link['anchor_text']}\"")

    if result["redirected"]:
        chains = [l for l in result["redirected"]
                  if l.get("redirect", {}).get("hops", 0) > 1]
        if chains:
            print(f"\n⚠️ Redirect Chains (>1 hop):")
            for link in chains:
                r = link["redirect"]
                print(f"  {link['url']}")
                print(f"    → {r['to']} ({r['hops']} hops: {r['codes']})")

    if result["timeout"]:
        print(f"\n⏱️ Timed Out:")
        for link in result["timeout"]:
            print(f"  {link['url']}")

    if result["issues"]:
        print(f"\nIssues:")
        for issue in result["issues"]:
            print(f"  {issue}")


if __name__ == "__main__":
    main()
