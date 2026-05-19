"""URL canonicalization, origin matching, template classification, and route guessing."""
import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from crawl_sample import (  # noqa: E402
    build_route_guesses,
    canonicalize_url,
    classify_url,
    clamp_max_pages,
    guess_locale_prefix,
    looks_like_html_url,
    normalize_host,
    same_origin,
)


class CanonicalizeTests(unittest.TestCase):
    def test_strips_trailing_slash_except_root(self) -> None:
        self.assertEqual(canonicalize_url("https://x.com/foo/"), "https://x.com/foo")
        self.assertEqual(canonicalize_url("https://x.com/"), "https://x.com/")

    def test_lowercases_scheme_and_host(self) -> None:
        self.assertEqual(canonicalize_url("HTTPS://X.COM/Foo"), "https://x.com/Foo")

    def test_drops_fragment(self) -> None:
        self.assertEqual(canonicalize_url("https://x.com/p#section"), "https://x.com/p")

    def test_preserves_query(self) -> None:
        self.assertEqual(canonicalize_url("https://x.com/p?q=1"), "https://x.com/p?q=1")


class NormalizeHostTests(unittest.TestCase):
    def test_strips_www(self) -> None:
        self.assertEqual(normalize_host("WWW.Example.COM"), "example.com")

    def test_keeps_subdomain(self) -> None:
        self.assertEqual(normalize_host("blog.example.com"), "blog.example.com")


class SameOriginTests(unittest.TestCase):
    def test_www_and_apex_treated_same(self) -> None:
        self.assertTrue(same_origin("https://www.example.com/a", "https://example.com/b"))

    def test_different_scheme_is_different_origin(self) -> None:
        self.assertFalse(same_origin("http://example.com/", "https://example.com/"))

    def test_different_host_is_different_origin(self) -> None:
        self.assertFalse(same_origin("https://example.com/", "https://other.com/"))


class LooksLikeHtmlUrlTests(unittest.TestCase):
    def test_http_path_is_html(self) -> None:
        self.assertTrue(looks_like_html_url("https://x.com/page"))

    def test_pdf_excluded(self) -> None:
        self.assertFalse(looks_like_html_url("https://x.com/file.pdf"))

    def test_image_excluded(self) -> None:
        self.assertFalse(looks_like_html_url("https://x.com/img.png"))

    def test_non_http_scheme_excluded(self) -> None:
        self.assertFalse(looks_like_html_url("file:///etc/passwd"))


class ClassifyUrlTests(unittest.TestCase):
    HOMEPAGE = "https://example.com/"

    def test_homepage(self) -> None:
        self.assertEqual(classify_url("https://example.com/", self.HOMEPAGE), "homepage")

    def test_pricing(self) -> None:
        self.assertEqual(classify_url("https://example.com/pricing", self.HOMEPAGE), "pricing")

    def test_product(self) -> None:
        self.assertEqual(classify_url("https://example.com/products/x", self.HOMEPAGE), "product")

    def test_docs(self) -> None:
        self.assertEqual(classify_url("https://example.com/docs/intro", self.HOMEPAGE), "docs")

    def test_blog(self) -> None:
        self.assertEqual(classify_url("https://example.com/blog/post-a", self.HOMEPAGE), "blog")

    def test_trust(self) -> None:
        self.assertEqual(classify_url("https://example.com/about", self.HOMEPAGE), "trust")

    def test_legal(self) -> None:
        self.assertEqual(classify_url("https://example.com/privacy", self.HOMEPAGE), "legal")

    def test_external(self) -> None:
        self.assertEqual(classify_url("https://other.com/", self.HOMEPAGE), "external")

    def test_other_fallback(self) -> None:
        self.assertEqual(classify_url("https://example.com/random", self.HOMEPAGE), "other")


class LocalePrefixTests(unittest.TestCase):
    def test_two_letter_locale(self) -> None:
        self.assertEqual(guess_locale_prefix("https://x.com/de/page"), "/de")

    def test_region_locale(self) -> None:
        self.assertEqual(guess_locale_prefix("https://x.com/en-us/page"), "/en-us")

    def test_no_locale(self) -> None:
        self.assertEqual(guess_locale_prefix("https://x.com/foo/bar"), "")


class ClampMaxPagesTests(unittest.TestCase):
    def test_lower_bound(self) -> None:
        self.assertEqual(clamp_max_pages(0), 1)
        self.assertEqual(clamp_max_pages(-5), 1)

    def test_upper_bound(self) -> None:
        self.assertEqual(clamp_max_pages(999), 50)

    def test_within_range(self) -> None:
        self.assertEqual(clamp_max_pages(25), 25)


class RouteGuessTests(unittest.TestCase):
    def test_includes_common_routes(self) -> None:
        guesses = build_route_guesses("https://example.com/", {"url": "https://example.com/"})
        self.assertIn("https://example.com/about", guesses)
        self.assertIn("https://example.com/pricing", guesses)

    def test_skips_start_url(self) -> None:
        guesses = build_route_guesses("https://example.com/", {"url": "https://example.com/"})
        self.assertNotIn("https://example.com/", guesses)

    def test_domain_type_extends(self) -> None:
        base = build_route_guesses("https://example.com/", {"url": "https://example.com/"})
        crypto = build_route_guesses("https://example.com/", {"url": "https://example.com/"}, domain_type="crypto")
        self.assertGreater(len(crypto), len(base))
        self.assertTrue(any(url.endswith("/staking") for url in crypto))


if __name__ == "__main__":
    unittest.main()
