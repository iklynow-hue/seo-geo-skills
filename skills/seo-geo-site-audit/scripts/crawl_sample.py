#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

# Import unified fetcher
from fetchers import fetch_rendered, detect_spa_shell, DEFAULT_UA as FETCHERS_UA

DEFAULT_UA = FETCHERS_UA
TIMEOUT = 30
MAX_SITEMAPS = 20
MAX_BODY_CHARS = 250000
BINARY_EXTENSIONS = {
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".svg",
    ".webp",
    ".avif",
    ".ico",
    ".zip",
    ".gz",
    ".rar",
    ".7z",
    ".mp4",
    ".webm",
    ".mov",
    ".mp3",
    ".wav",
    ".xml",
    ".json",
    ".rss",
    ".atom",
}
SKIP_SCHEMES = {"mailto", "tel", "javascript", "data"}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def clamp_max_pages(value: int) -> int:
    return max(1, min(50, value))


def canonicalize_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url.strip())
    scheme = parsed.scheme.lower() or "https"
    host = (parsed.netloc or "").lower()
    path = parsed.path or "/"
    if path != "/" and path.endswith("/"):
        path = path[:-1]
    normalized = parsed._replace(
        scheme=scheme,
        netloc=host,
        path=path,
        query=parsed.query,
        fragment="",
    )
    return urllib.parse.urlunsplit(normalized)


def normalize_host(host: str) -> str:
    host = host.lower()
    if host.startswith("www."):
        return host[4:]
    return host


def same_origin(a: str, b: str) -> bool:
    pa = urllib.parse.urlsplit(a)
    pb = urllib.parse.urlsplit(b)
    return (pa.scheme.lower(), normalize_host(pa.netloc)) == (pb.scheme.lower(), normalize_host(pb.netloc))


def looks_like_html_url(url: str) -> bool:
    parsed = urllib.parse.urlsplit(url)
    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"}:
        return False
    lower_path = parsed.path.lower()
    return not any(lower_path.endswith(ext) for ext in BINARY_EXTENSIONS)


def classify_url(url: str, homepage: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    homepage_parsed = urllib.parse.urlsplit(homepage)
    path = parsed.path.lower().strip("/")
    if normalize_host(parsed.netloc) != normalize_host(homepage_parsed.netloc):
        return "external"
    if not path:
        return "homepage"
    tokens = path.split("/")
    joined = "/".join(tokens)
    if any(t in {"blog", "news", "article", "articles", "insights"} for t in tokens):
        return "blog"
    if any(t in {"docs", "doc", "guide", "guides", "help", "kb", "knowledge-base", "academy"} for t in tokens):
        return "docs"
    if any(t in {"product", "products", "feature", "features", "solution", "solutions"} for t in tokens):
        return "product"
    if any(t in {"pricing", "plans", "plan"} for t in tokens):
        return "pricing"
    if any(t in {"about", "company", "team", "careers", "contact", "support"} for t in tokens):
        return "trust"
    if any(t in {"privacy", "terms", "legal", "security", "compliance"} for t in tokens):
        return "legal"
    if any(t in {"category", "categories", "collection", "collections"} for t in tokens):
        return "category"
    if any(re.fullmatch(r"\d{4}", t) for t in tokens) or re.search(r"/\d{4}/\d{2}/", joined):
        return "archive"
    return "other"


def title_priority(url: str, homepage: str) -> tuple:
    template = classify_url(url, homepage)
    order = {
        "homepage": 0,
        "pricing": 1,
        "product": 2,
        "docs": 3,
        "blog": 4,
        "trust": 5,
        "legal": 6,
        "category": 7,
        "archive": 8,
        "other": 9,
    }
    parsed = urllib.parse.urlsplit(url)
    depth = len([p for p in parsed.path.split("/") if p])
    has_query = 1 if parsed.query else 0
    return (order.get(template, 99), depth, has_query, url)


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_chunks: list[str] = []
        self.capture_title = False
        self.skip_text_depth = 0
        self.visible_text_chunks: list[str] = []
        self.links: list[str] = []
        self.link_texts: list[str] = []
        self.link_href_stack: list[str | None] = []
        self.heading_counts = Counter()
        self.in_heading: str | None = None
        self.heading_texts: dict[str, list[str]] = defaultdict(list)
        self.meta = {}
        self.og = {}
        self.twitter = {}
        self.canonical = ""
        self.json_ld_blocks: list[str] = []
        self.capture_json_ld = False
        self.json_ld_chunks: list[str] = []
        self.image_count = 0
        self.images_missing_alt = 0
        self.list_count = 0
        self.table_count = 0
        self.breadcrumb_hint = False
        self.author_hint = False
        self.about_contact_hint = False
        self.faq_hint = False
        self.price_hint = False
        self.lang = ""
        self.script_count = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {k.lower(): (v or "") for k, v in attrs}
        tag = tag.lower()
        if tag == "title":
            self.capture_title = True
        if tag in {"script", "style", "noscript"}:
            self.skip_text_depth += 1
        if tag == "html" and attr_map.get("lang"):
            self.lang = attr_map.get("lang", "")
        if tag == "a":
            href = attr_map.get("href", "")
            self.links.append(href)
            self.link_href_stack.append(href)
            lowered = f"{href} {attr_map.get('aria-label','')}".lower()
            if any(x in lowered for x in ("about", "contact", "support", "help", "company", "team")):
                self.about_contact_hint = True
            if "author" in lowered:
                self.author_hint = True
        if tag == "img":
            self.image_count += 1
            if not attr_map.get("alt", "").strip():
                self.images_missing_alt += 1
        if tag in {"ul", "ol", "dl"}:
            self.list_count += 1
        if tag == "table":
            self.table_count += 1
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.in_heading = tag
            self.heading_counts[tag] += 1
        if tag == "meta":
            name = attr_map.get("name", "").lower()
            prop = attr_map.get("property", "").lower()
            content = attr_map.get("content", "").strip()
            if name:
                self.meta[name] = content
            if prop.startswith("og:"):
                self.og[prop] = content
            if name.startswith("twitter:"):
                self.twitter[name] = content
            if name == "author":
                self.author_hint = True
        if tag == "link":
            rel = " ".join(attr_map.get("rel", "").lower().split())
            href = attr_map.get("href", "").strip()
            if "canonical" in rel and href:
                self.canonical = href
        if tag == "nav":
            label = f"{attr_map.get('aria-label','')} {attr_map.get('id','')} {attr_map.get('class','')}".lower()
            if "breadcrumb" in label:
                self.breadcrumb_hint = True
        if tag == "script":
            self.script_count += 1
            script_type = attr_map.get("type", "").lower()
            if "ld+json" in script_type:
                self.capture_json_ld = True
                self.json_ld_chunks = []

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "title":
            self.capture_title = False
        if tag in {"script", "style", "noscript"} and self.skip_text_depth > 0:
            self.skip_text_depth -= 1
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.in_heading = None
        if tag == "a" and self.link_href_stack:
            self.link_href_stack.pop()
        if tag == "script" and self.capture_json_ld:
            content = "".join(self.json_ld_chunks).strip()
            if content:
                self.json_ld_blocks.append(content)
            self.capture_json_ld = False
            self.json_ld_chunks = []

    def handle_data(self, data: str) -> None:
        stripped = " ".join(data.split())
        if not stripped:
            return
        lowered = stripped.lower()
        if self.capture_title:
            self.title_chunks.append(stripped)
        if self.capture_json_ld:
            self.json_ld_chunks.append(data)
        if self.in_heading:
            self.heading_texts[self.in_heading].append(stripped)
        if self.link_href_stack:
            self.link_texts.append(stripped)
        if self.skip_text_depth == 0:
            self.visible_text_chunks.append(stripped)
        if "frequently asked questions" in lowered or lowered == "faq" or lowered.startswith("faq "):
            self.faq_hint = True
        if any(x in lowered for x in ("author", "written by", "editor", "reviewed by")):
            self.author_hint = True
        if any(x in lowered for x in ("price", "pricing", "plan", "specification", "specs", "$", "usd")):
            self.price_hint = True


def fetch(url: str, user_agent: str, timeout: int = TIMEOUT, preferred_fetcher: str = "auto") -> dict:
    """Fetch a URL using the unified fetcher (JS rendering when available).

    For robots.txt and sitemaps, always uses urllib (no JS needed).
    For page content, uses the preferred fetcher chain.
    """
    # For non-HTML resources (robots.txt, sitemaps), use urllib directly
    parsed = urllib.parse.urlsplit(url)
    path_lower = parsed.path.lower()
    is_non_html = path_lower.endswith(("/robots.txt", ".xml")) or path_lower == "/robots.txt"

    if is_non_html or preferred_fetcher == "urllib":
        return _fetch_urllib_raw(url, user_agent, timeout)

    return fetch_rendered(url, user_agent=user_agent, timeout=timeout, preferred_fetcher=preferred_fetcher)


def _fetch_urllib_raw(url: str, user_agent: str, timeout: int = TIMEOUT) -> dict:
    """Raw urllib fetch for non-HTML resources (robots.txt, sitemaps)."""
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Encoding": "gzip",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read()
        encoding = response.headers.get("Content-Encoding", "").lower()
        if encoding == "gzip":
            raw = gzip.decompress(raw)
        content_type = response.headers.get_content_type()
        charset = response.headers.get_content_charset() or "utf-8"
        text = raw[:MAX_BODY_CHARS].decode(charset, errors="replace")
        return {
            "final_url": response.geturl(),
            "status": getattr(response, "status", None) or response.getcode(),
            "headers": dict(response.info()),
            "content_type": content_type,
            "text": text,
            "bytes": len(raw),
            "fetcher": "urllib",
        }


def parse_json_ld_types(blocks: list[str]) -> list[str]:
    types: list[str] = []

    def walk(node) -> None:
        if isinstance(node, dict):
            t = node.get("@type")
            if isinstance(t, str):
                types.append(t)
            elif isinstance(t, list):
                types.extend([x for x in t if isinstance(x, str)])
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    for block in blocks:
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            continue
        walk(data)
    return sorted(set(types))


def parse_robots(text: str) -> dict:
    sitemap_urls: list[str] = []
    current_agents: list[str] = []
    targeted = {"gptbot", "google-extended", "claudebot", "chatgpt-user", "ccbot", "perplexitybot"}
    ai_sections: dict[str, dict[str, list[str]]] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().lower()
        value = value.strip()
        if key == "sitemap":
            sitemap_urls.append(value)
            continue
        if key == "user-agent":
            current_agents = [value.lower()]
            continue
        if key in {"allow", "disallow"}:
            for agent in current_agents:
                if agent in targeted:
                    ai_sections.setdefault(agent, {"allow": [], "disallow": []})
                    ai_sections[agent][key].append(value)
    return {"sitemaps": sitemap_urls, "ai_crawler_directives": ai_sections}


def extract_urls_from_sitemap(xml_text: str) -> tuple[list[str], list[str]]:
    urls: list[str] = []
    sitemap_indexes: list[str] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return urls, sitemap_indexes
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    if root.tag.endswith("sitemapindex"):
        for loc in root.findall(".//sm:sitemap/sm:loc", ns) + root.findall(".//sitemap/loc"):
            if loc.text:
                sitemap_indexes.append(loc.text.strip())
    else:
        for loc in root.findall(".//sm:url/sm:loc", ns) + root.findall(".//url/loc"):
            if loc.text:
                urls.append(loc.text.strip())
    return urls, sitemap_indexes


def discover_sitemap_urls(start_url: str, user_agent: str) -> dict:
    parsed = urllib.parse.urlsplit(start_url)
    site_root = f"{parsed.scheme}://{parsed.netloc}"
    robots_url = urllib.parse.urljoin(site_root, "/robots.txt")
    robots_info = {
        "url": robots_url,
        "present": False,
        "status": None,
        "sitemaps": [],
        "ai_crawler_directives": {},
    }
    discovered_urls: list[str] = []
    try:
        robots_resp = fetch(robots_url, user_agent)
        robots_info["present"] = robots_resp["status"] == 200
        robots_info["status"] = robots_resp["status"]
        parsed_robots = parse_robots(robots_resp["text"])
        robots_info["sitemaps"] = parsed_robots["sitemaps"]
        robots_info["ai_crawler_directives"] = parsed_robots["ai_crawler_directives"]
    except Exception:
        pass

    to_visit = deque(robots_info["sitemaps"] or [urllib.parse.urljoin(site_root, "/sitemap.xml")])
    seen = set()
    sitemap_count = 0
    while to_visit and sitemap_count < MAX_SITEMAPS:
        sitemap_url = to_visit.popleft()
        if sitemap_url in seen:
            continue
        seen.add(sitemap_url)
        sitemap_count += 1
        try:
            resp = fetch(sitemap_url, user_agent)
        except Exception:
            continue
        if resp["status"] != 200:
            continue
        urls, nested = extract_urls_from_sitemap(resp["text"])
        for nested_url in nested:
            if nested_url not in seen:
                to_visit.append(nested_url)
        for url in urls:
            if same_origin(start_url, url) and looks_like_html_url(url):
                discovered_urls.append(canonicalize_url(url))
    return {
        "robots": robots_info,
        "urls": list(dict.fromkeys(discovered_urls)),
        "sitemap_count_processed": sitemap_count,
    }


def check_llms(site_url: str, user_agent: str) -> dict:
    parsed = urllib.parse.urlsplit(site_url)
    site_root = f"{parsed.scheme}://{parsed.netloc}"
    candidates = [
        urllib.parse.urljoin(site_root, "/llms.txt"),
        urllib.parse.urljoin(site_root, "/.well-known/llms.txt"),
    ]
    for candidate in candidates:
        try:
            resp = fetch(candidate, user_agent)
        except Exception:
            continue
        if resp["status"] == 200 and resp["text"].strip():
            return {
                "present": True,
                "url": candidate,
                "status": resp["status"],
                "preview": "\n".join(resp["text"].splitlines()[:8]),
            }
    return {"present": False, "url": candidates[0], "status": None, "preview": ""}


def safe_join(base: str, href: str) -> str | None:
    href = (href or "").strip()
    if not href:
        return None
    parsed = urllib.parse.urlsplit(href)
    if parsed.scheme.lower() in SKIP_SCHEMES:
        return None
    joined = urllib.parse.urljoin(base, href)
    clean = canonicalize_url(joined)
    if looks_like_html_url(clean):
        return clean
    return None


def analyze_page(url: str, user_agent: str, start_url: str, preferred_fetcher: str = "auto") -> tuple[dict, list[str]]:
    response = fetch(url, user_agent, preferred_fetcher=preferred_fetcher)
    text = response["text"]
    parser = PageParser()
    parser.feed(text)
    title = " ".join(parser.title_chunks).strip()
    visible_text = " ".join(parser.visible_text_chunks)
    visible_text = re.sub(r"\s+", " ", visible_text).strip()
    words = re.findall(r"\b[\w-]+\b", visible_text)
    canonical = parser.canonical
    if canonical:
        canonical = canonicalize_url(urllib.parse.urljoin(response["final_url"], canonical))
    json_ld_types = parse_json_ld_types(parser.json_ld_blocks)
    if "BreadcrumbList" in json_ld_types:
        parser.breadcrumb_hint = True
    if "FAQPage" in json_ld_types:
        parser.faq_hint = True
    if any(t in json_ld_types for t in ("Organization", "Person", "NewsArticle", "Article", "BlogPosting")):
        parser.author_hint = True

    internal_links = []
    external_links = 0
    for href in parser.links:
        joined = safe_join(response["final_url"], href)
        if not joined:
            continue
        if same_origin(start_url, joined):
            internal_links.append(joined)
        else:
            external_links += 1
    internal_links = list(dict.fromkeys(internal_links))

    headers = {k.lower(): v for k, v in response["headers"].items()}
    meta_robots = parser.meta.get("robots", "").strip()
    x_robots = headers.get("x-robots-tag", "").strip()
    robots_value = ", ".join(x for x in [meta_robots, x_robots] if x).strip(", ")
    initial_html_visible = bool(title and (len(words) >= 80 or parser.heading_counts["h1"] >= 1 and len(words) >= 50))
    excessive_script_ratio = parser.script_count >= 20 and len(words) < 150
    spa_detection = detect_spa_shell(text, len(words), parser.script_count)
    og_coverage = {
        "title": bool(parser.og.get("og:title")),
        "description": bool(parser.og.get("og:description")),
        "image": bool(parser.og.get("og:image")),
        "url": bool(parser.og.get("og:url")),
    }
    twitter_coverage = {
        "card": bool(parser.twitter.get("twitter:card")),
        "title": bool(parser.twitter.get("twitter:title")),
        "description": bool(parser.twitter.get("twitter:description")),
        "image": bool(parser.twitter.get("twitter:image")),
    }

    template = classify_url(response["final_url"], start_url)
    issues = []
    if not title:
        issues.append("missing_title")
    if not parser.meta.get("description"):
        issues.append("missing_meta_description")
    if not canonical:
        issues.append("missing_canonical")
    if parser.heading_counts["h1"] == 0:
        issues.append("missing_h1")
    if parser.heading_counts["h1"] > 1:
        issues.append("multiple_h1")
    if parser.image_count and parser.images_missing_alt:
        issues.append("images_missing_alt")
    if not initial_html_visible:
        issues.append("weak_initial_html_visibility")
    if excessive_script_ratio:
        issues.append("js_heavy_or_thin_html")
    if "noindex" in robots_value.lower():
        issues.append("noindex_detected")

    page = {
        "url": response["final_url"],
        "requested_url": url,
        "status": response["status"],
        "content_type": response["content_type"],
        "template": template,
        "title": title,
        "meta_description": parser.meta.get("description", ""),
        "canonical": canonical,
        "meta_robots": robots_value,
        "lang": parser.lang,
        "word_count": len(words),
        "html_bytes": response["bytes"],
        "h1_count": parser.heading_counts["h1"],
        "heading_counts": dict(parser.heading_counts),
        "internal_links": len(internal_links),
        "external_links": external_links,
        "sample_internal_links": internal_links[:10],
        "image_count": parser.image_count,
        "images_missing_alt": parser.images_missing_alt,
        "json_ld_types": json_ld_types,
        "og_coverage": og_coverage,
        "twitter_coverage": twitter_coverage,
        "has_breadcrumbs_hint": parser.breadcrumb_hint,
        "has_author_hint": parser.author_hint,
        "has_about_or_contact_hint": parser.about_contact_hint,
        "has_faq_hint": parser.faq_hint,
        "has_list_or_table": bool(parser.list_count or parser.table_count),
        "has_price_or_specs_hint": parser.price_hint,
        "render_visibility": {
            "body_text_in_initial_html": initial_html_visible,
            "excessive_script_ratio": excessive_script_ratio,
        },
        "spa_detection": spa_detection,
        "fetcher": response.get("fetcher", "urllib"),
        "issues_detected": issues,
    }
    return page, internal_links


def interleave_by_template(urls: list[str], start_url: str, limit: int) -> list[str]:
    groups: dict[str, deque[str]] = defaultdict(deque)
    for url in sorted(dict.fromkeys(urls), key=lambda u: title_priority(u, start_url)):
        groups[classify_url(url, start_url)].append(url)
    ordered = []
    ordered_templates = sorted(groups, key=lambda t: (0 if t == "homepage" else 1, t))
    while len(ordered) < limit and any(groups.values()):
        for template in ordered_templates:
            if groups[template]:
                ordered.append(groups[template].popleft())
                if len(ordered) >= limit:
                    break
    return ordered


def aggregate(pages: list[dict]) -> dict:
    title_counts = Counter(page["title"].strip().lower() for page in pages if page["title"].strip())
    desc_counts = Counter(page["meta_description"].strip().lower() for page in pages if page["meta_description"].strip())
    schema_counts = Counter()
    template_counts = Counter()
    issue_counts = Counter()
    for page in pages:
        template_counts[page["template"]] += 1
        for t in page["json_ld_types"]:
            schema_counts[t] += 1
        for issue in page["issues_detected"]:
            issue_counts[issue] += 1
    duplicate_titles = {k: v for k, v in title_counts.items() if v > 1}
    duplicate_descriptions = {k: v for k, v in desc_counts.items() if v > 1}
    totals = len(pages) or 1
    pages_with_schema = sum(1 for p in pages if p["json_ld_types"])
    pages_with_breadcrumbs = sum(1 for p in pages if p["has_breadcrumbs_hint"])
    pages_with_author = sum(1 for p in pages if p["has_author_hint"])
    pages_with_faq = sum(1 for p in pages if p["has_faq_hint"])
    pages_with_initial_html = sum(1 for p in pages if p["render_visibility"]["body_text_in_initial_html"])
    pages_flagged_spa = sum(1 for p in pages if p.get("spa_detection", {}).get("needs_js_rendering", False))
    fetcher_counts = Counter(p.get("fetcher", "unknown") for p in pages)
    return {
        "page_count": len(pages),
        "template_counts": dict(template_counts),
        "schema_type_counts": dict(schema_counts),
        "issue_counts": dict(issue_counts),
        "duplicate_title_count": len(duplicate_titles),
        "duplicate_meta_description_count": len(duplicate_descriptions),
        "pages_with_schema": pages_with_schema,
        "pages_with_breadcrumbs": pages_with_breadcrumbs,
        "pages_with_author_hints": pages_with_author,
        "pages_with_faq_hints": pages_with_faq,
        "pages_with_initial_html_content": pages_with_initial_html,
        "pages_flagged_spa": pages_flagged_spa,
        "fetcher_counts": dict(fetcher_counts),
        "coverage_rates": {
            "title": round(100 * sum(1 for p in pages if p["title"]) / totals, 1),
            "meta_description": round(100 * sum(1 for p in pages if p["meta_description"]) / totals, 1),
            "canonical": round(100 * sum(1 for p in pages if p["canonical"]) / totals, 1),
            "single_h1": round(100 * sum(1 for p in pages if p["h1_count"] == 1) / totals, 1),
            "schema": round(100 * pages_with_schema / totals, 1),
            "breadcrumbs_hint": round(100 * pages_with_breadcrumbs / totals, 1),
            "author_hint": round(100 * pages_with_author / totals, 1),
            "faq_hint": round(100 * pages_with_faq / totals, 1),
            "initial_html_content": round(100 * pages_with_initial_html / totals, 1),
        },
    }


def build_site_signals(start_url: str, user_agent: str, robots_bundle: dict) -> dict:
    parsed = urllib.parse.urlsplit(start_url)
    site_root = f"{parsed.scheme}://{parsed.netloc}"
    homepage_headers = {}
    try:
        # Security headers must come from the raw HTTP response, not a rendered fetcher.
        homepage = fetch(site_root, user_agent, preferred_fetcher="urllib")
        homepage_headers = {k.lower(): v for k, v in homepage["headers"].items()}
    except Exception:
        pass
    security_headers = {
        key: homepage_headers.get(key, "")
        for key in (
            "strict-transport-security",
            "content-security-policy",
            "x-frame-options",
            "referrer-policy",
            "permissions-policy",
        )
    }
    llms = check_llms(start_url, user_agent)
    return {
        "robots_txt": robots_bundle["robots"],
        "sitemap": {
            "urls_discovered": len(robots_bundle["urls"]),
            "sitemap_count_processed": robots_bundle["sitemap_count_processed"],
        },
        "llms_txt": llms,
        "security_headers": security_headers,
    }


def crawl(start_url: str, max_pages: int, user_agent: str, preferred_fetcher: str = "auto") -> dict:
    start_url = canonicalize_url(start_url)
    robots_bundle = discover_sitemap_urls(start_url, user_agent)
    sitemap_candidates = interleave_by_template(robots_bundle["urls"], start_url, max(max_pages * 2, max_pages))

    queue = deque([start_url, *sitemap_candidates])
    seen = set()
    pages = []
    bfs_discovered = 0

    while queue and len(pages) < max_pages:
        current = queue.popleft()
        current = canonicalize_url(current)
        if current in seen or not same_origin(start_url, current) or not looks_like_html_url(current):
            continue
        seen.add(current)
        try:
            page, discovered_links = analyze_page(current, user_agent, start_url, preferred_fetcher=preferred_fetcher)
        except urllib.error.HTTPError as exc:
            page = {
                "url": current,
                "requested_url": current,
                "status": exc.code,
                "content_type": "",
                "template": classify_url(current, start_url),
                "title": "",
                "meta_description": "",
                "canonical": "",
                "meta_robots": "",
                "lang": "",
                "word_count": 0,
                "html_bytes": 0,
                "h1_count": 0,
                "heading_counts": {},
                "internal_links": 0,
                "external_links": 0,
                "sample_internal_links": [],
                "image_count": 0,
                "images_missing_alt": 0,
                "json_ld_types": [],
                "og_coverage": {},
                "twitter_coverage": {},
                "has_breadcrumbs_hint": False,
                "has_author_hint": False,
                "has_about_or_contact_hint": False,
                "has_faq_hint": False,
                "has_list_or_table": False,
                "has_price_or_specs_hint": False,
                "render_visibility": {"body_text_in_initial_html": False, "excessive_script_ratio": False},
                "issues_detected": [f"http_{exc.code}"],
            }
            discovered_links = []
        except Exception as exc:
            page = {
                "url": current,
                "requested_url": current,
                "status": None,
                "content_type": "",
                "template": classify_url(current, start_url),
                "title": "",
                "meta_description": "",
                "canonical": "",
                "meta_robots": "",
                "lang": "",
                "word_count": 0,
                "html_bytes": 0,
                "h1_count": 0,
                "heading_counts": {},
                "internal_links": 0,
                "external_links": 0,
                "sample_internal_links": [],
                "image_count": 0,
                "images_missing_alt": 0,
                "json_ld_types": [],
                "og_coverage": {},
                "twitter_coverage": {},
                "has_breadcrumbs_hint": False,
                "has_author_hint": False,
                "has_about_or_contact_hint": False,
                "has_faq_hint": False,
                "has_list_or_table": False,
                "has_price_or_specs_hint": False,
                "render_visibility": {"body_text_in_initial_html": False, "excessive_script_ratio": False},
                "issues_detected": [f"fetch_error:{type(exc).__name__}"],
            }
            discovered_links = []
        pages.append(page)
        for link in discovered_links:
            if link not in seen and link not in queue:
                queue.append(link)
                bfs_discovered += 1

    result = {
        "target_url": start_url,
        "fetched_at": now_iso(),
        "crawl_cap": max_pages,
        "page_count": len(pages),
        "site_signals": build_site_signals(start_url, user_agent, robots_bundle),
        "summary": aggregate(pages),
        "pages": pages,
        "notes": {
            "sitemap_candidates_considered": len(sitemap_candidates),
            "bfs_discovered_links": bfs_discovered,
            "sample_is_page_capped": True,
        },
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Crawl a capped sample of site pages and extract SEO/GEO signals.")
    parser.add_argument("--url", required=True, help="Start URL, usually the homepage.")
    parser.add_argument("--max-pages", type=int, default=50, help="Maximum pages to sample (1-50).")
    parser.add_argument("--user-agent", default=DEFAULT_UA, help="HTTP User-Agent header.")
    parser.add_argument("--fetcher", default="auto", choices=["auto", "scrapling", "lightpanda", "agent_browser", "urllib"],
                        help="Preferred fetcher. 'auto' tries Scrapling → Lightpanda → agent-browser → urllib.")
    parser.add_argument("--out", help="Optional JSON output file.")
    args = parser.parse_args()

    max_pages = clamp_max_pages(args.max_pages)
    result = crawl(args.url, max_pages, args.user_agent, preferred_fetcher=args.fetcher)
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(payload, encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
