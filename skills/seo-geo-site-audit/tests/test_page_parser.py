"""PageParser must extract title, meta, headings, links, JSON-LD, and structural hints."""
import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from crawl_sample import PageParser, parse_json_ld_types  # noqa: E402


FIXTURE_HTML = """<!doctype html>
<html lang="en">
<head>
  <title>Example Page Title</title>
  <meta name="description" content="An example meta description.">
  <meta name="author" content="Jane Doe">
  <link rel="canonical" href="https://example.com/page">
  <meta property="og:title" content="OG Title">
  <meta property="og:image" content="https://example.com/og.png">
  <meta name="twitter:card" content="summary_large_image">
  <script type="application/ld+json">{"@context":"https://schema.org","@type":"Organization","name":"Example"}</script>
</head>
<body>
  <nav aria-label="breadcrumb"><a href="/">Home</a></nav>
  <h1>Main Heading</h1>
  <h2>Subhead one</h2>
  <h2>Subhead two</h2>
  <p>Some body content about products and pricing.</p>
  <a href="/about">About us</a>
  <a href="/contact">Contact</a>
  <a href="mailto:hi@example.com">Email</a>
  <img src="/hero.png" alt="">
  <img src="/secondary.png" alt="Secondary image">
  <ul><li>a</li><li>b</li></ul>
  <table><tr><td>cell</td></tr></table>
</body>
</html>
"""


class PageParserTests(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = PageParser()
        self.parser.feed(FIXTURE_HTML)

    def test_title(self) -> None:
        self.assertEqual(" ".join(self.parser.title_chunks).strip(), "Example Page Title")

    def test_meta_description(self) -> None:
        self.assertEqual(self.parser.meta.get("description"), "An example meta description.")

    def test_canonical(self) -> None:
        self.assertEqual(self.parser.canonical, "https://example.com/page")

    def test_lang(self) -> None:
        self.assertEqual(self.parser.lang, "en")

    def test_heading_counts(self) -> None:
        self.assertEqual(self.parser.heading_counts["h1"], 1)
        self.assertEqual(self.parser.heading_counts["h2"], 2)

    def test_link_count_and_filters(self) -> None:
        # PageParser captures all raw hrefs (about, contact, mailto, breadcrumb).
        # Filtering of mailto: happens in safe_join, not in the parser.
        self.assertEqual(len(self.parser.links), 4)

    def test_image_alt_tracking(self) -> None:
        self.assertEqual(self.parser.image_count, 2)
        self.assertEqual(self.parser.images_missing_alt, 1)

    def test_list_and_table(self) -> None:
        self.assertGreaterEqual(self.parser.list_count, 1)
        self.assertGreaterEqual(self.parser.table_count, 1)

    def test_breadcrumb_hint(self) -> None:
        self.assertTrue(self.parser.breadcrumb_hint)

    def test_author_hint(self) -> None:
        self.assertTrue(self.parser.author_hint)

    def test_price_hint(self) -> None:
        self.assertTrue(self.parser.price_hint)

    def test_og_capture(self) -> None:
        self.assertEqual(self.parser.og.get("og:title"), "OG Title")
        self.assertIn("og:image", self.parser.og)

    def test_twitter_capture(self) -> None:
        self.assertEqual(self.parser.twitter.get("twitter:card"), "summary_large_image")

    def test_json_ld_block_captured(self) -> None:
        self.assertEqual(len(self.parser.json_ld_blocks), 1)

    def test_json_ld_types_extracted(self) -> None:
        types = parse_json_ld_types(self.parser.json_ld_blocks)
        self.assertIn("Organization", types)


class NestedJsonLdTests(unittest.TestCase):
    def test_nested_types_walked(self) -> None:
        block = """[
          {"@context":"https://schema.org","@type":"Article","author":{"@type":"Person","name":"X"}},
          {"@type":["BreadcrumbList","ItemList"]}
        ]"""
        types = parse_json_ld_types([block])
        for expected in ("Article", "Person", "BreadcrumbList", "ItemList"):
            self.assertIn(expected, types)

    def test_invalid_json_ld_ignored(self) -> None:
        types = parse_json_ld_types(["not-valid-json"])
        self.assertEqual(types, [])


if __name__ == "__main__":
    unittest.main()
