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
from fetchers import (
    SEARCH_ENGINE_UA,
    detect_spa_shell,
    fetch_raw_http,
    fetch_with_spa_recovery,
)

DEFAULT_SEARCH_UA = SEARCH_ENGINE_UA
DEFAULT_UA = DEFAULT_SEARCH_UA
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
COMMON_ROUTE_GUESSES = (
    "about",
    "about-us",
    "company",
    "contact",
    "support",
    "help",
    "faq",
    "docs",
    "documentation",
    "guides",
    "pricing",
    "plans",
    "fees",
    "security",
    "privacy",
    "terms",
    "legal",
    "blog",
    "news",
    "learn",
    "markets",
    "trade",
    "swap",
    "portfolio",
    "earn",
    "vault",
    "points",
)

# Domain-specific route templates for sites where COMMON_ROUTE_GUESSES is too generic.
# Key is a keyword found in the homepage title/meta/domain; value is extra paths to try.
DOMAIN_ROUTE_TEMPLATES: dict[str, list[str]] = {
    "crypto": [
        "markets", "market", "trade", "trading", "exchange", "spot", "futures",
        "perpetual", "swap", "convert", "earn", "staking", "savings", "vault",
        "launchpad", "launchpool", "nft", "defi", "web3", "wallet", "portfolio",
        "deposit", "withdraw", "transfer", "referral", "rewards", "vip",
        "api", "api-docs", "whitepaper", "token", "coins", "pairs",
    ],
    "saas": [
        "product", "features", "solutions", "pricing", "plans", "enterprise",
        "integrations", "plugins", "api", "developers", "docs", "changelog",
        "status", "roadmap", "customers", "case-studies", "partners",
        "signup", "sign-up", "register", "login", "demo", "free-trial",
    ],
    "ecommerce": [
        "shop", "store", "products", "categories", "collections", "deals",
        "sale", "cart", "checkout", "account", "orders", "shipping",
        "returns", "size-guide", "reviews", "brands", "new-arrivals",
        "best-sellers", "gift-cards", "wishlist",
    ],
    "fintech": [
        "accounts", "cards", "loans", "mortgage", "invest", "investing",
        "stocks", "etf", "crypto", "banking", "savings", "checking",
        "insurance", "wealth", "robo-advisor", "portfolio", "transfer",
        "fees", "rates", "calculator", "app", "security",
    ],
    "media": [
        "articles", "news", "stories", "videos", "podcasts", "newsletter",
        "topics", "categories", "trending", "latest", "editors-picks",
        "authors", "contributors", "subscribe", "membership", "archive",
    ],
}


def detect_site_domain_type(url: str, homepage_text: str) -> str | None:
    """Detect site category from URL and homepage content for domain-specific route guessing."""
    combined = (url + " " + homepage_text[:2000]).lower()
    signals = {
        "crypto": ["crypto", "bitcoin", "btc", "ethereum", "defi", "blockchain", "token", "swap", "staking", "futures", "perpetual", "web3"],
        "saas": ["saas", "software", "platform", "dashboard", "api", "subscription", "enterprise", "cloud"],
        "ecommerce": ["shop", "store", "cart", "checkout", "product", "buy", "order", "shipping", "delivery"],
        "fintech": ["bank", "finance", "invest", "stock", "trading", "loan", "mortgage", "payment", "fintech"],
        "media": ["news", "article", "blog", "magazine", "publish", "editorial", "journalist", "podcast"],
    }
    scores: dict[str, int] = {}
    for category, keywords in signals.items():
        scores[category] = sum(1 for kw in keywords if kw in combined)
    best = max(scores, key=scores.get)  # type: ignore[arg-type]
    if scores[best] >= 3:
        return best
    return None


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


def guess_locale_prefix(url: str) -> str:
    parts = [segment for segment in urllib.parse.urlsplit(url).path.split("/") if segment]
    if not parts:
        return ""
    first = parts[0].lower()
    if re.fullmatch(r"[a-z]{2}(?:-[a-z]{2})?", first):
        return f"/{first}"
    return ""


def build_route_guesses(start_url: str, page: dict, domain_type: str | None = None) -> list[str]:
    parsed = urllib.parse.urlsplit(start_url)
    site_root = f"{parsed.scheme}://{parsed.netloc}"
    final_url = canonicalize_url(page.get("url", start_url))
    locale_prefix = guess_locale_prefix(final_url)
    guesses: list[str] = []

    canonical = page.get("canonical") or ""
    if canonical:
        guesses.append(canonicalize_url(canonical))

    # Generic routes
    for route in COMMON_ROUTE_GUESSES:
        for prefix in ("", locale_prefix):
            path = f"{prefix}/{route}" if prefix else f"/{route}"
            guesses.append(canonicalize_url(urllib.parse.urljoin(site_root, path)))

    # Domain-specific routes
    if domain_type and domain_type in DOMAIN_ROUTE_TEMPLATES:
        for route in DOMAIN_ROUTE_TEMPLATES[domain_type]:
            for prefix in ("", locale_prefix):
                path = f"{prefix}/{route}" if prefix else f"/{route}"
                guess = canonicalize_url(urllib.parse.urljoin(site_root, path))
                if guess not in guesses:
                    guesses.append(guess)

    start_canonical = canonicalize_url(start_url)
    return list(dict.fromkeys(url for url in guesses if same_origin(start_url, url) and url != start_canonical))


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


def dedupe_urls(urls: list[str]) -> list[str]:
    return list(dict.fromkeys(urls))


def queue_has_url(queue: deque, url: str) -> bool:
    return any(item[0] == url for item in queue)


def parse_page_response(response: dict, start_url: str) -> dict:
    text = response.get("text", "")
    parser = PageParser()
    parser.feed(text)
    title = " ".join(parser.title_chunks).strip()
    visible_text = " ".join(parser.visible_text_chunks)
    visible_text = re.sub(r"\s+", " ", visible_text).strip()
    words = re.findall(r"\b[\w-]+\b", visible_text)
    canonical = parser.canonical
    final_url = response.get("final_url", "")
    if canonical:
        canonical = canonicalize_url(urllib.parse.urljoin(final_url, canonical))
    json_ld_types = parse_json_ld_types(parser.json_ld_blocks)
    if "BreadcrumbList" in json_ld_types:
        parser.breadcrumb_hint = True
    if "FAQPage" in json_ld_types:
        parser.faq_hint = True
    if any(t in json_ld_types for t in ("Organization", "Person", "NewsArticle", "Article", "BlogPosting")):
        parser.author_hint = True

    internal_links: list[str] = []
    external_links = 0
    for href in parser.links:
        joined = safe_join(final_url, href)
        if not joined:
            continue
        if same_origin(start_url, joined):
            internal_links.append(joined)
        else:
            external_links += 1

    return {
        "parser": parser,
        "title": title,
        "visible_text": visible_text,
        "words": words,
        "word_count": len(words),
        "canonical": canonical,
        "json_ld_types": json_ld_types,
        "internal_links": dedupe_urls(internal_links),
        "external_links": external_links,
        "headers": {k.lower(): v for k, v in response.get("headers", {}).items()},
        "script_count": parser.script_count,
    }


def dom_hint_links(response: dict, base_url: str, start_url: str) -> dict[str, list[str]]:
    raw_hints = response.get("dom_link_hints") or {}
    if isinstance(response.get("dom_links"), list):
        raw_hints = {"anchors": response.get("dom_links", [])}
    hint_keys = ("anchors", "attribute_hints", "onclick_hints", "framework_hints")
    normalized: dict[str, list[str]] = {}
    for key in hint_keys:
        links: list[str] = []
        for href in raw_hints.get(key, []) if isinstance(raw_hints, dict) else []:
            joined = safe_join(base_url, str(href))
            if joined and same_origin(start_url, joined):
                links.append(joined)
        normalized[key] = dedupe_urls(links)
    return normalized


def signal_status(raw_present: bool, rendered_present: bool) -> str:
    if raw_present and rendered_present:
        return "raw_and_rendered"
    if raw_present:
        return "raw_only"
    if rendered_present:
        return "rendered_only"
    return "missing"


def build_rendered_signal_delta(
    *,
    raw_title: str,
    rendered_title: str,
    raw_meta_description: str,
    rendered_meta_description: str,
    raw_canonical: str,
    rendered_canonical: str,
    raw_h1_count: int,
    rendered_h1_count: int,
    raw_word_count: int,
    rendered_word_count: int,
    raw_internal_links: int,
    rendered_internal_links: int,
    dom_route_hint_links: int,
    raw_json_ld_types: list[str],
    rendered_json_ld_types: list[str],
) -> dict:
    """Compare raw Googlebot baseline signals against rendered DOM signals."""
    signals = {
        "title": {
            "raw_present": bool(raw_title),
            "rendered_present": bool(rendered_title),
            "status": signal_status(bool(raw_title), bool(rendered_title)),
            "raw_value": raw_title[:160],
            "rendered_value": rendered_title[:160],
        },
        "meta_description": {
            "raw_present": bool(raw_meta_description),
            "rendered_present": bool(rendered_meta_description),
            "status": signal_status(bool(raw_meta_description), bool(rendered_meta_description)),
            "raw_value": raw_meta_description[:220],
            "rendered_value": rendered_meta_description[:220],
        },
        "canonical": {
            "raw_present": bool(raw_canonical),
            "rendered_present": bool(rendered_canonical),
            "status": signal_status(bool(raw_canonical), bool(rendered_canonical)),
            "raw_value": raw_canonical[:240],
            "rendered_value": rendered_canonical[:240],
        },
        "h1": {
            "raw_present": raw_h1_count > 0,
            "rendered_present": rendered_h1_count > 0,
            "status": signal_status(raw_h1_count > 0, rendered_h1_count > 0),
            "raw_count": raw_h1_count,
            "rendered_count": rendered_h1_count,
        },
        "body_words": {
            "raw_present": raw_word_count >= 50,
            "rendered_present": rendered_word_count >= 50,
            "status": signal_status(raw_word_count >= 50, rendered_word_count >= 50),
            "raw_count": raw_word_count,
            "rendered_count": rendered_word_count,
        },
        "internal_links": {
            "raw_present": raw_internal_links > 0,
            "rendered_present": rendered_internal_links > 0,
            "status": signal_status(raw_internal_links > 0, rendered_internal_links > 0),
            "raw_count": raw_internal_links,
            "rendered_count": rendered_internal_links,
            "dom_route_hint_count": dom_route_hint_links,
        },
        "json_ld": {
            "raw_present": bool(raw_json_ld_types),
            "rendered_present": bool(rendered_json_ld_types),
            "status": signal_status(bool(raw_json_ld_types), bool(rendered_json_ld_types)),
            "raw_types": raw_json_ld_types,
            "rendered_types": rendered_json_ld_types,
        },
    }
    rendered_only = [name for name, signal in signals.items() if signal["status"] == "rendered_only"]
    missing = [name for name, signal in signals.items() if signal["status"] == "missing"]
    raw_and_rendered = [name for name, signal in signals.items() if signal["status"] == "raw_and_rendered"]
    if rendered_only and not missing:
        conclusion = "rendering_recovers_all_missing_primary_signals"
    elif rendered_only:
        conclusion = "rendering_recovers_some_signals"
    elif missing:
        conclusion = "signals_missing_after_rendering"
    else:
        conclusion = "raw_baseline_contains_primary_signals"
    return {
        "signals": signals,
        "rendered_only_signals": rendered_only,
        "missing_after_rendering": missing,
        "raw_and_rendered_signals": raw_and_rendered,
        "conclusion": conclusion,
    }


def empty_rendered_signal_delta() -> dict:
    return build_rendered_signal_delta(
        raw_title="",
        rendered_title="",
        raw_meta_description="",
        rendered_meta_description="",
        raw_canonical="",
        rendered_canonical="",
        raw_h1_count=0,
        rendered_h1_count=0,
        raw_word_count=0,
        rendered_word_count=0,
        raw_internal_links=0,
        rendered_internal_links=0,
        dom_route_hint_links=0,
        raw_json_ld_types=[],
        rendered_json_ld_types=[],
    )


def fetch(url: str, user_agent: str, timeout: int = TIMEOUT, preferred_fetcher: str = "auto") -> dict:
    """Fetch a URL using the unified fetcher (JS rendering when available).

    For robots.txt and sitemaps, always uses urllib (no JS needed).
    For HTML page content, uses fetch_with_spa_recovery for SPA shell detection.
    """
    # For non-HTML resources (robots.txt, sitemaps), use urllib directly
    parsed = urllib.parse.urlsplit(url)
    path_lower = parsed.path.lower()
    is_non_html = path_lower.endswith(("/robots.txt", ".xml")) or path_lower == "/robots.txt"

    if is_non_html or preferred_fetcher == "urllib":
        return _fetch_urllib_raw(url, user_agent, timeout)

    return fetch_with_spa_recovery(url, user_agent=user_agent, timeout=timeout, preferred_fetcher=preferred_fetcher)


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
    robots_rules: dict[str, dict[str, list[str]]] = {}
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
                robots_rules.setdefault(agent, {"allow": [], "disallow": []})
                robots_rules[agent][key].append(value)
                if agent in targeted:
                    ai_sections.setdefault(agent, {"allow": [], "disallow": []})
                    ai_sections[agent][key].append(value)
    search_sections = {
        agent: robots_rules[agent]
        for agent in ("googlebot", "googlebot-news", "googlebot-image", "*")
        if agent in robots_rules
    }
    return {
        "sitemaps": sitemap_urls,
        "ai_crawler_directives": ai_sections,
        "search_crawler_directives": search_sections,
        "robots_rules": robots_rules,
    }


def robots_path(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    path = parsed.path or "/"
    if parsed.query:
        return f"{path}?{parsed.query}"
    return path


def path_matches_robots_rule(path: str, pattern: str) -> bool:
    if pattern == "":
        return True
    escaped = re.escape(pattern).replace(r"\*", ".*")
    if escaped.endswith(r"\$"):
        escaped = escaped[:-2] + "$"
    return re.match(escaped, path) is not None


def allowed_by_robots(url: str, robots_info: dict, agent: str = "googlebot") -> dict:
    if not robots_info.get("present"):
        return {"allowed": True, "matched_agent": None, "matched_rule": None}

    rules_by_agent = robots_info.get("robots_rules", {})
    agent = agent.lower()
    matched_agent = None
    if agent in rules_by_agent:
        matched_agent = agent
    elif "*" in rules_by_agent:
        matched_agent = "*"
    if not matched_agent:
        return {"allowed": True, "matched_agent": None, "matched_rule": None}

    path = robots_path(url)
    best_rule = None
    best_length = -1
    best_allowed = True
    for directive, allowed in (("allow", True), ("disallow", False)):
        for pattern in rules_by_agent.get(matched_agent, {}).get(directive, []):
            if not path_matches_robots_rule(path, pattern):
                continue
            length = len(pattern)
            if length > best_length or (length == best_length and allowed):
                best_rule = f"{directive}: {pattern}"
                best_length = length
                best_allowed = allowed

    return {
        "allowed": best_allowed,
        "matched_agent": matched_agent,
        "matched_rule": best_rule,
    }


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
            resp = _fetch_urllib_raw(candidate, user_agent)
        except Exception:
            continue
        preview = "\n".join(resp["text"].splitlines()[:8])
        stripped = resp["text"].strip().lower()
        looks_like_empty_html = stripped.startswith("<!doctype html") or stripped.startswith("<html")
        if resp["status"] == 200 and resp["text"].strip() and not looks_like_empty_html:
            return {
                "present": True,
                "url": candidate,
                "status": resp["status"],
                "content_type": resp.get("content_type", ""),
                "preview": preview,
            }
        if resp["status"] == 200:
            return {
                "present": False,
                "url": candidate,
                "status": resp["status"],
                "content_type": resp.get("content_type", ""),
                "preview": preview,
                "issue": "llms_txt_returns_html_shell",
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


def analyze_page(
    url: str,
    user_agent: str,
    start_url: str,
    preferred_fetcher: str = "auto",
    robots_info: dict | None = None,
    discovery_source: str = "unknown",
) -> tuple[dict, dict[str, list[str]]]:
    raw_response: dict | None = None
    raw_error = ""
    try:
        raw_response = fetch_raw_http(url, user_agent=DEFAULT_SEARCH_UA, timeout=TIMEOUT)
    except urllib.error.HTTPError as exc:
        body = exc.read()[:MAX_BODY_CHARS].decode("utf-8", errors="replace")
        raw_response = {
            "final_url": exc.geturl(),
            "status": exc.code,
            "headers": dict(exc.headers.items()) if exc.headers else {},
            "content_type": exc.headers.get_content_type() if exc.headers else "",
            "text": body,
            "bytes": len(body.encode("utf-8", errors="replace")),
            "fetcher": "raw_http",
            "user_agent": DEFAULT_SEARCH_UA,
        }
    except Exception as exc:
        raw_error = type(exc).__name__

    response = fetch(url, user_agent, preferred_fetcher=preferred_fetcher)
    rendered = parse_page_response(response, start_url)
    rendered_parser: PageParser = rendered["parser"]

    if raw_response:
        raw = parse_page_response(raw_response, start_url)
        raw_parser: PageParser = raw["parser"]
        raw_text = raw_response.get("text", "")
    else:
        raw = {
            "title": "",
            "word_count": 0,
            "canonical": "",
            "json_ld_types": [],
            "internal_links": [],
            "external_links": 0,
            "headers": {},
            "script_count": 0,
        }
        raw_parser = PageParser()
        raw_text = ""

    dom_hints = dom_hint_links(response, response.get("final_url", url), start_url)
    rendered_a_links = rendered["internal_links"]
    raw_a_links = raw["internal_links"]
    dom_route_hint_links = dedupe_urls(
        dom_hints["attribute_hints"] + dom_hints["onclick_hints"] + dom_hints["framework_hints"]
    )
    rendered_only_links = [link for link in rendered_a_links if link not in raw_a_links]

    raw_title = raw["title"]
    rendered_title = rendered["title"]
    raw_meta_description = raw_parser.meta.get("description", "").strip()
    rendered_meta_description = rendered_parser.meta.get("description", "").strip()
    raw_canonical = raw["canonical"]
    rendered_canonical = rendered["canonical"]
    raw_h1_count = raw_parser.heading_counts["h1"]
    rendered_h1_count = rendered_parser.heading_counts["h1"]

    raw_meta_robots = raw_parser.meta.get("robots", "").strip()
    rendered_meta_robots = rendered_parser.meta.get("robots", "").strip()
    x_robots = raw["headers"].get("x-robots-tag", "").strip()
    robots_value = ", ".join(x for x in [raw_meta_robots, rendered_meta_robots, x_robots] if x).strip(", ")
    robots_access = allowed_by_robots(url, robots_info or {}, agent="googlebot")

    raw_initial_html_visible = bool(
        raw["title"]
        and (raw["word_count"] >= 80 or raw_parser.heading_counts["h1"] >= 1 and raw["word_count"] >= 50)
    )
    rendered_visible = bool(
        rendered["title"]
        and (rendered["word_count"] >= 80 or rendered_parser.heading_counts["h1"] >= 1 and rendered["word_count"] >= 50)
    )
    excessive_script_ratio = raw["script_count"] >= 20 and raw["word_count"] < 150
    spa_detection = detect_spa_shell(raw_text, raw["word_count"], raw["script_count"])

    og_coverage = {
        "title": bool(raw_parser.og.get("og:title") or rendered_parser.og.get("og:title")),
        "description": bool(raw_parser.og.get("og:description") or rendered_parser.og.get("og:description")),
        "image": bool(raw_parser.og.get("og:image") or rendered_parser.og.get("og:image")),
        "url": bool(raw_parser.og.get("og:url") or rendered_parser.og.get("og:url")),
    }
    twitter_coverage = {
        "card": bool(raw_parser.twitter.get("twitter:card") or rendered_parser.twitter.get("twitter:card")),
        "title": bool(raw_parser.twitter.get("twitter:title") or rendered_parser.twitter.get("twitter:title")),
        "description": bool(raw_parser.twitter.get("twitter:description") or rendered_parser.twitter.get("twitter:description")),
        "image": bool(raw_parser.twitter.get("twitter:image") or rendered_parser.twitter.get("twitter:image")),
    }

    final_url = (raw_response or response).get("final_url", response.get("final_url", url))
    template = classify_url(final_url, start_url)
    title = raw_title or rendered_title
    meta_description = raw_meta_description or rendered_meta_description
    canonical = raw_canonical or rendered_canonical
    json_ld_types = raw["json_ld_types"] or rendered["json_ld_types"]
    h1_count = raw_h1_count or rendered_h1_count
    heading_counts = dict(raw_parser.heading_counts if raw_h1_count else rendered_parser.heading_counts)

    rendered_signal_delta = build_rendered_signal_delta(
        raw_title=raw_title,
        rendered_title=rendered_title,
        raw_meta_description=raw_meta_description,
        rendered_meta_description=rendered_meta_description,
        raw_canonical=raw_canonical,
        rendered_canonical=rendered_canonical,
        raw_h1_count=raw_h1_count,
        rendered_h1_count=rendered_h1_count,
        raw_word_count=raw["word_count"],
        rendered_word_count=rendered["word_count"],
        raw_internal_links=len(raw_a_links),
        rendered_internal_links=len(rendered_a_links),
        dom_route_hint_links=len(dom_route_hint_links),
        raw_json_ld_types=raw["json_ld_types"],
        rendered_json_ld_types=rendered["json_ld_types"],
    )

    issues = []
    if not title:
        issues.append("missing_title")
    elif not raw_title and rendered_title:
        issues.append("title_requires_js_rendering")
    if not meta_description:
        issues.append("missing_meta_description")
    elif not raw_meta_description and rendered_meta_description:
        issues.append("meta_description_requires_js_rendering")
    if not canonical:
        issues.append("missing_canonical")
    elif not raw_canonical and rendered_canonical:
        issues.append("canonical_requires_js_rendering")
    if h1_count == 0:
        issues.append("missing_h1")
    elif raw_h1_count == 0 and rendered_h1_count > 0:
        issues.append("h1_requires_js_rendering")
    if h1_count > 1:
        issues.append("multiple_h1")
    if rendered_parser.image_count and rendered_parser.images_missing_alt:
        issues.append("images_missing_alt")
    if not raw_initial_html_visible:
        issues.append("weak_initial_html_visibility")
    if rendered_visible and not raw_initial_html_visible:
        issues.append("content_requires_js_rendering")
    if not raw_a_links and (rendered_a_links or dom_route_hint_links):
        issues.append("navigation_requires_js_rendering")
    if raw["json_ld_types"] == [] and rendered["json_ld_types"]:
        issues.append("schema_requires_js_rendering")
    if excessive_script_ratio or spa_detection.get("needs_js_rendering"):
        issues.append("js_heavy_or_thin_html")
    if "noindex" in robots_value.lower():
        issues.append("noindex_detected")
    if not robots_access.get("allowed", True):
        issues.append("robots_disallow_for_googlebot")
    if discovery_source in {"route_guess", "dom_route_hint"}:
        issues.append("not_search_discoverable_in_sample")

    page = {
        "url": final_url,
        "requested_url": url,
        "status": (raw_response or response).get("status"),
        "rendered_status": response.get("status"),
        "content_type": (raw_response or response).get("content_type", ""),
        "template": template,
        "discovery_source": discovery_source,
        "title": title,
        "raw_title": raw_title,
        "rendered_title": rendered_title,
        "meta_description": meta_description,
        "raw_meta_description": raw_meta_description,
        "rendered_meta_description": rendered_meta_description,
        "canonical": canonical,
        "raw_canonical": raw_canonical,
        "rendered_canonical": rendered_canonical,
        "meta_robots": robots_value,
        "lang": raw_parser.lang or rendered_parser.lang,
        "word_count": raw["word_count"],
        "rendered_word_count": rendered["word_count"],
        "html_bytes": (raw_response or response).get("bytes", 0),
        "rendered_html_bytes": response.get("bytes", 0),
        "h1_count": h1_count,
        "raw_h1_count": raw_h1_count,
        "rendered_h1_count": rendered_h1_count,
        "heading_counts": heading_counts,
        "rendered_heading_counts": dict(rendered_parser.heading_counts),
        "internal_links": len(raw_a_links),
        "rendered_internal_links": len(rendered_a_links),
        "dom_route_hint_links": len(dom_route_hint_links),
        "external_links": raw["external_links"],
        "rendered_external_links": rendered["external_links"],
        "sample_internal_links": raw_a_links[:10],
        "sample_rendered_internal_links": rendered_a_links[:10],
        "sample_dom_route_hint_links": dom_route_hint_links[:10],
        "image_count": rendered_parser.image_count,
        "images_missing_alt": rendered_parser.images_missing_alt,
        "json_ld_types": json_ld_types,
        "raw_json_ld_types": raw["json_ld_types"],
        "rendered_json_ld_types": rendered["json_ld_types"],
        "og_coverage": og_coverage,
        "twitter_coverage": twitter_coverage,
        "has_breadcrumbs_hint": raw_parser.breadcrumb_hint or rendered_parser.breadcrumb_hint,
        "has_author_hint": raw_parser.author_hint or rendered_parser.author_hint,
        "has_about_or_contact_hint": raw_parser.about_contact_hint or rendered_parser.about_contact_hint,
        "has_faq_hint": raw_parser.faq_hint or rendered_parser.faq_hint,
        "has_list_or_table": bool(raw_parser.list_count or raw_parser.table_count or rendered_parser.list_count or rendered_parser.table_count),
        "has_price_or_specs_hint": raw_parser.price_hint or rendered_parser.price_hint,
        "render_visibility": {
            "body_text_in_initial_html": raw_initial_html_visible,
            "body_text_after_render": rendered_visible,
            "excessive_script_ratio": excessive_script_ratio,
        },
        "search_engine_visibility": {
            "baseline_user_agent": "Googlebot Smartphone",
            "rendered_simulation": "headless browser fetch with JavaScript when available",
            "raw_fetch_error": raw_error,
            "raw_status": raw_response.get("status") if raw_response else None,
            "allowed_by_robots": bool(robots_access.get("allowed", True)),
            "robots_matched_agent": robots_access.get("matched_agent"),
            "robots_matched_rule": robots_access.get("matched_rule"),
            "raw_title_present": bool(raw_title),
            "rendered_title_present": bool(rendered_title),
            "raw_meta_description_present": bool(raw_meta_description),
            "rendered_meta_description_present": bool(rendered_meta_description),
            "raw_canonical_present": bool(raw_canonical),
            "rendered_canonical_present": bool(rendered_canonical),
            "raw_h1_count": raw_h1_count,
            "rendered_h1_count": rendered_h1_count,
            "raw_word_count": raw["word_count"],
            "rendered_word_count": rendered["word_count"],
            "content_requires_js_rendering": rendered_visible and not raw_initial_html_visible,
            "raw_internal_a_links": len(raw_a_links),
            "rendered_internal_a_links": len(rendered_a_links),
            "rendered_only_internal_a_links": len(rendered_only_links),
            "dom_route_hint_links": len(dom_route_hint_links),
            "navigation_requires_js_rendering": not raw_a_links and bool(rendered_a_links or dom_route_hint_links),
        },
        "rendered_signal_delta": rendered_signal_delta,
        "googlebot_rendering": {
            "raw_baseline": {
                "user_agent": "Googlebot Smartphone",
                "status": raw_response.get("status") if raw_response else None,
                "title": raw_title,
                "meta_description": raw_meta_description,
                "canonical": raw_canonical,
                "h1_count": raw_h1_count,
                "word_count": raw["word_count"],
                "internal_links": len(raw_a_links),
                "json_ld_types": raw["json_ld_types"],
            },
            "rendered_dom": {
                "fetcher": response.get("fetcher", "urllib"),
                "status": response.get("status"),
                "title": rendered_title,
                "meta_description": rendered_meta_description,
                "canonical": rendered_canonical,
                "h1_count": rendered_h1_count,
                "word_count": rendered["word_count"],
                "internal_links": len(rendered_a_links),
                "json_ld_types": rendered["json_ld_types"],
            },
            "delta": rendered_signal_delta,
        },
        "spa_detection": spa_detection,
        "fetcher": response.get("fetcher", "urllib"),
        "issues_detected": issues,
    }

    discovery_links = {
        "raw_a_href": raw_a_links,
        "rendered_a_href": rendered_only_links,
        "dom_route_hint": dom_route_hint_links,
    }
    return page, discovery_links


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
    pages_with_rendered_content = sum(1 for p in pages if p.get("render_visibility", {}).get("body_text_after_render"))
    pages_flagged_spa = sum(1 for p in pages if p.get("spa_detection", {}).get("needs_js_rendering", False))
    pages_requiring_js_content = sum(1 for p in pages if p.get("search_engine_visibility", {}).get("content_requires_js_rendering"))
    pages_requiring_js_navigation = sum(1 for p in pages if p.get("search_engine_visibility", {}).get("navigation_requires_js_rendering"))
    pages_with_rendered_recovered_signals = sum(
        1 for p in pages if p.get("rendered_signal_delta", {}).get("rendered_only_signals")
    )
    pages_missing_signals_after_rendering = sum(
        1 for p in pages if p.get("rendered_signal_delta", {}).get("missing_after_rendering")
    )
    pages_allowed_by_robots = sum(1 for p in pages if p.get("search_engine_visibility", {}).get("allowed_by_robots", True))
    pages_assisted_discovery = sum(1 for p in pages if p.get("discovery_source") in {"route_guess", "dom_route_hint"})
    fetcher_counts = Counter(p.get("fetcher", "unknown") for p in pages)
    discovery_source_counts = Counter(p.get("discovery_source", "unknown") for p in pages)
    rendered_only_signal_counts = Counter()
    missing_after_rendering_counts = Counter()
    for page in pages:
        rendered_only_signal_counts.update(page.get("rendered_signal_delta", {}).get("rendered_only_signals", []))
        missing_after_rendering_counts.update(page.get("rendered_signal_delta", {}).get("missing_after_rendering", []))
    return {
        "page_count": len(pages),
        "template_counts": dict(template_counts),
        "discovery_source_counts": dict(discovery_source_counts),
        "schema_type_counts": dict(schema_counts),
        "issue_counts": dict(issue_counts),
        "duplicate_title_count": len(duplicate_titles),
        "duplicate_meta_description_count": len(duplicate_descriptions),
        "pages_with_schema": pages_with_schema,
        "pages_with_breadcrumbs": pages_with_breadcrumbs,
        "pages_with_author_hints": pages_with_author,
        "pages_with_faq_hints": pages_with_faq,
        "pages_with_initial_html_content": pages_with_initial_html,
        "pages_with_rendered_content": pages_with_rendered_content,
        "pages_flagged_spa": pages_flagged_spa,
        "pages_requiring_js_content": pages_requiring_js_content,
        "pages_requiring_js_navigation": pages_requiring_js_navigation,
        "pages_with_rendered_recovered_signals": pages_with_rendered_recovered_signals,
        "pages_missing_signals_after_rendering": pages_missing_signals_after_rendering,
        "rendered_only_signal_counts": dict(rendered_only_signal_counts),
        "missing_after_rendering_signal_counts": dict(missing_after_rendering_counts),
        "pages_allowed_by_robots": pages_allowed_by_robots,
        "pages_assisted_discovery": pages_assisted_discovery,
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
            "rendered_content": round(100 * pages_with_rendered_content / totals, 1),
            "robots_allowed_googlebot": round(100 * pages_allowed_by_robots / totals, 1),
            "content_not_js_dependent": round(100 * (totals - pages_requiring_js_content) / totals, 1),
            "navigation_not_js_dependent": round(100 * (totals - pages_requiring_js_navigation) / totals, 1),
        },
        "raw_coverage_rates": {
            "title": round(100 * sum(1 for p in pages if p.get("raw_title")) / totals, 1),
            "meta_description": round(100 * sum(1 for p in pages if p.get("raw_meta_description")) / totals, 1),
            "canonical": round(100 * sum(1 for p in pages if p.get("raw_canonical")) / totals, 1),
            "single_h1": round(100 * sum(1 for p in pages if p.get("raw_h1_count") == 1) / totals, 1),
            "schema": round(100 * sum(1 for p in pages if p.get("raw_json_ld_types")) / totals, 1),
            "internal_links": round(100 * sum(1 for p in pages if p.get("internal_links", 0) > 0) / totals, 1),
            "body_words_50_plus": round(100 * sum(1 for p in pages if p.get("word_count", 0) >= 50) / totals, 1),
        },
        "rendered_coverage_rates": {
            "title": round(100 * sum(1 for p in pages if p.get("rendered_title")) / totals, 1),
            "meta_description": round(100 * sum(1 for p in pages if p.get("rendered_meta_description")) / totals, 1),
            "canonical": round(100 * sum(1 for p in pages if p.get("rendered_canonical")) / totals, 1),
            "single_h1": round(100 * sum(1 for p in pages if p.get("rendered_h1_count") == 1) / totals, 1),
            "schema": round(100 * sum(1 for p in pages if p.get("rendered_json_ld_types")) / totals, 1),
            "internal_links": round(100 * sum(1 for p in pages if p.get("rendered_internal_links", 0) > 0) / totals, 1),
            "body_words_50_plus": round(100 * sum(1 for p in pages if p.get("rendered_word_count", 0) >= 50) / totals, 1),
        },
        "googlebot_rendering_summary": {
            "pages_with_any_rendered_only_signal": pages_with_rendered_recovered_signals,
            "pages_with_any_signal_missing_after_rendering": pages_missing_signals_after_rendering,
            "rendered_only_signal_counts": dict(rendered_only_signal_counts),
            "missing_after_rendering_signal_counts": dict(missing_after_rendering_counts),
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

    queue = deque([(start_url, "start"), *[(url, "sitemap") for url in sitemap_candidates]])
    seen = set()
    pages = []
    bfs_discovered = 0
    rendered_discovered = 0
    dom_route_hints_enqueued = 0
    route_guess_candidates_considered = 0
    route_guess_pages_enqueued = 0
    best_effort_route_guessing_used = False
    browser_escalation_used = False
    sitemap_fallback_used = False
    domain_type: str | None = None

    while queue and len(pages) < max_pages:
        current, discovery_source = queue.popleft()
        current = canonicalize_url(current)
        if current in seen or not same_origin(start_url, current) or not looks_like_html_url(current):
            continue
        seen.add(current)
        try:
            page, discovered_links = analyze_page(
                current,
                user_agent,
                start_url,
                preferred_fetcher=preferred_fetcher,
                robots_info=robots_bundle["robots"],
                discovery_source=discovery_source,
            )
        except urllib.error.HTTPError as exc:
            page = {
                "url": current,
                "requested_url": current,
                "status": exc.code,
                "rendered_status": None,
                "content_type": "",
                "template": classify_url(current, start_url),
                "discovery_source": discovery_source,
                "title": "",
                "rendered_title": "",
                "meta_description": "",
                "canonical": "",
                "rendered_canonical": "",
                "meta_robots": "",
                "lang": "",
                "word_count": 0,
                "rendered_word_count": 0,
                "html_bytes": 0,
                "rendered_html_bytes": 0,
                "h1_count": 0,
                "rendered_h1_count": 0,
                "heading_counts": {},
                "rendered_heading_counts": {},
                "internal_links": 0,
                "rendered_internal_links": 0,
                "dom_route_hint_links": 0,
                "external_links": 0,
                "rendered_external_links": 0,
                "sample_internal_links": [],
                "sample_rendered_internal_links": [],
                "sample_dom_route_hint_links": [],
                "image_count": 0,
                "images_missing_alt": 0,
                "json_ld_types": [],
                "rendered_json_ld_types": [],
                "og_coverage": {},
                "twitter_coverage": {},
                "has_breadcrumbs_hint": False,
                "has_author_hint": False,
                "has_about_or_contact_hint": False,
                "has_faq_hint": False,
                "has_list_or_table": False,
                "has_price_or_specs_hint": False,
                "render_visibility": {"body_text_in_initial_html": False, "body_text_after_render": False, "excessive_script_ratio": False},
                "search_engine_visibility": {"allowed_by_robots": True, "raw_status": exc.code},
                "issues_detected": [f"http_{exc.code}"],
            }
            discovered_links = {"raw_a_href": [], "rendered_a_href": [], "dom_route_hint": []}
        except Exception as exc:
            page = {
                "url": current,
                "requested_url": current,
                "status": None,
                "rendered_status": None,
                "content_type": "",
                "template": classify_url(current, start_url),
                "discovery_source": discovery_source,
                "title": "",
                "rendered_title": "",
                "meta_description": "",
                "canonical": "",
                "rendered_canonical": "",
                "meta_robots": "",
                "lang": "",
                "word_count": 0,
                "rendered_word_count": 0,
                "html_bytes": 0,
                "rendered_html_bytes": 0,
                "h1_count": 0,
                "rendered_h1_count": 0,
                "heading_counts": {},
                "rendered_heading_counts": {},
                "internal_links": 0,
                "rendered_internal_links": 0,
                "dom_route_hint_links": 0,
                "external_links": 0,
                "rendered_external_links": 0,
                "sample_internal_links": [],
                "sample_rendered_internal_links": [],
                "sample_dom_route_hint_links": [],
                "image_count": 0,
                "images_missing_alt": 0,
                "json_ld_types": [],
                "rendered_json_ld_types": [],
                "og_coverage": {},
                "twitter_coverage": {},
                "has_breadcrumbs_hint": False,
                "has_author_hint": False,
                "has_about_or_contact_hint": False,
                "has_faq_hint": False,
                "has_list_or_table": False,
                "has_price_or_specs_hint": False,
                "render_visibility": {"body_text_in_initial_html": False, "body_text_after_render": False, "excessive_script_ratio": False},
                "search_engine_visibility": {"allowed_by_robots": True, "raw_status": None},
                "issues_detected": [f"fetch_error:{type(exc).__name__}"],
            }
            discovered_links = {"raw_a_href": [], "rendered_a_href": [], "dom_route_hint": []}
        pages.append(page)

        # Detect domain type from homepage for route guessing
        if len(pages) == 1 and not domain_type:
            domain_type = detect_site_domain_type(start_url, page.get("title", "") + " " + page.get("meta_description", ""))

        for link in discovered_links.get("raw_a_href", []):
            if link not in seen and not queue_has_url(queue, link):
                queue.append((link, "raw_a_href"))
                bfs_discovered += 1
        for link in discovered_links.get("rendered_a_href", []):
            if link not in seen and not queue_has_url(queue, link):
                queue.append((link, "rendered_a_href"))
                rendered_discovered += 1

        # Browser escalation: relax condition — trigger for any browser-backed fetcher
        # when homepage has weak content and no links discovered
        needs_browser_escalation = (
            preferred_fetcher == "auto"
            and current == canonicalize_url(start_url)
            and len(pages) == 1
            and not discovered_links.get("raw_a_href")
            and not discovered_links.get("rendered_a_href")
            and page.get("fetcher") in {"scrapling", "lightpanda", "agent_browser"}
            and (
                page.get("word_count", 0) < 40
                or not page.get("title")
                or page.get("spa_detection", {}).get("needs_js_rendering", False)
            )
        )
        if needs_browser_escalation:
            browser_escalation_used = True
            try:
                chrome_page, chrome_links = analyze_page(
                    current,
                    user_agent,
                    start_url,
                    preferred_fetcher="chrome",
                    robots_info=robots_bundle["robots"],
                    discovery_source=discovery_source,
                )
                old_link_count = len(discovered_links.get("raw_a_href", [])) + len(discovered_links.get("rendered_a_href", []))
                new_link_count = len(chrome_links.get("raw_a_href", [])) + len(chrome_links.get("rendered_a_href", []))
                if chrome_page.get("rendered_word_count", 0) > page.get("rendered_word_count", 0) or new_link_count > old_link_count:
                    pages[-1] = chrome_page
                    page = chrome_page
                    discovered_links = chrome_links
                    for link in discovered_links.get("raw_a_href", []):
                        if link not in seen and not queue_has_url(queue, link):
                            queue.append((link, "raw_a_href"))
                            bfs_discovered += 1
                    for link in discovered_links.get("rendered_a_href", []):
                        if link not in seen and not queue_has_url(queue, link):
                            queue.append((link, "rendered_a_href"))
                            rendered_discovered += 1
            except Exception:
                pass

        has_rendered_content = bool(page.get("rendered_title") or page.get("title")) or page.get("rendered_word_count", 0) >= 80
        browser_backed_fetch = page.get("fetcher") in {"scrapling", "lightpanda", "agent_browser", "chrome"}
        stalled_discovery = (
            len(pages) == 1
            and not discovered_links.get("raw_a_href")
            and not discovered_links.get("rendered_a_href")
            and not queue
        )
        if browser_backed_fetch and has_rendered_content and stalled_discovery:
            for link in discovered_links.get("dom_route_hint", []):
                if link not in seen and not queue_has_url(queue, link):
                    queue.append((link, "dom_route_hint"))
                    dom_route_hints_enqueued += 1
            # Use larger limit when domain-specific routes are available
            guess_limit = max(4, min(max_pages * 3, 12))
            if domain_type:
                guess_limit = max(guess_limit, min(max_pages * 4, 30))
            guesses = build_route_guesses(start_url, page, domain_type=domain_type)[:guess_limit]
            if guesses:
                best_effort_route_guessing_used = True
                route_guess_candidates_considered += len(guesses)
                for guess in guesses:
                    if guess not in seen and not queue_has_url(queue, guess):
                        queue.append((guess, "route_guess"))
                        route_guess_pages_enqueued += 1

    # Sitemap-first fallback: if BFS + route guessing produced too few pages,
    # aggressively add remaining sitemap URLs that weren't tried yet
    if len(pages) < min(max_pages, 10) and robots_bundle["urls"]:
        sitemap_fallback_used = True
        remaining_sitemap = [
            canonicalize_url(u) for u in robots_bundle["urls"]
            if canonicalize_url(u) not in seen and same_origin(start_url, u) and looks_like_html_url(u)
        ]
        remaining_sitemap = interleave_by_template(remaining_sitemap, start_url, max_pages - len(pages))
        for url in remaining_sitemap:
            if len(pages) >= max_pages:
                break
            if url in seen:
                continue
            seen.add(url)
            try:
                page, discovered_links = analyze_page(
                    url,
                    user_agent,
                    start_url,
                    preferred_fetcher=preferred_fetcher,
                    robots_info=robots_bundle["robots"],
                    discovery_source="sitemap_fallback",
                )
                pages.append(page)
                for link in discovered_links.get("raw_a_href", []):
                    if link not in seen and not queue_has_url(queue, link):
                        queue.append((link, "raw_a_href"))
                        bfs_discovered += 1
                for link in discovered_links.get("rendered_a_href", []):
                    if link not in seen and not queue_has_url(queue, link):
                        queue.append((link, "rendered_a_href"))
                        rendered_discovered += 1
            except Exception:
                continue

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
            "rendered_discovered_links": rendered_discovered,
            "dom_route_hints_enqueued": dom_route_hints_enqueued,
            "best_effort_route_guessing_used": best_effort_route_guessing_used,
            "route_guess_candidates_considered": route_guess_candidates_considered,
            "route_guess_pages_enqueued": route_guess_pages_enqueued,
            "browser_escalation_used": browser_escalation_used,
            "sitemap_fallback_used": sitemap_fallback_used,
            "domain_type_detected": domain_type,
            "sample_is_page_capped": len(pages) >= max_pages,
        },
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Crawl a capped sample of site pages and extract SEO/GEO signals.")
    parser.add_argument("--url", required=True, help="Start URL, usually the homepage.")
    parser.add_argument("--max-pages", type=int, default=50, help="Maximum pages to sample (1-50).")
    parser.add_argument("--user-agent", default=DEFAULT_UA, help="HTTP User-Agent header.")
    parser.add_argument("--fetcher", default="auto", choices=["auto", "scrapling", "lightpanda", "agent_browser", "chrome", "urllib"],
                        help="Preferred fetcher. 'auto' tries Scrapling → Lightpanda → agent-browser → attached Chrome → urllib.")
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
