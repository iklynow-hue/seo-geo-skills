"""Sitemap parsing should not silently collapse large XML files to 0 URLs."""
import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from crawl_sample import MAX_BODY_CHARS, MAX_SITEMAP_CHARS, extract_urls_from_sitemap


class SitemapParsingTests(unittest.TestCase):
    def test_large_sitemap_parses_beyond_html_body_limit(self) -> None:
        rows = []
        for index in range(6000):
            rows.append(f"<url><loc>https://example.com/page-{index}</loc></url>")
        sitemap = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            + "".join(rows)
            + "</urlset>"
        )

        self.assertGreater(len(sitemap), MAX_BODY_CHARS)
        urls, nested = extract_urls_from_sitemap(sitemap)

        self.assertEqual(len(urls), 6000)
        self.assertEqual(nested, [])

    def test_sitemap_limit_exceeds_html_body_limit(self) -> None:
        self.assertGreater(MAX_SITEMAP_CHARS, MAX_BODY_CHARS)


if __name__ == "__main__":
    unittest.main()
