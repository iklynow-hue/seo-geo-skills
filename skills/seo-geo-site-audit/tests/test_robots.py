"""parse_robots + allowed_by_robots: sitemaps, user-agent sections, allow/disallow precedence."""
import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from crawl_sample import allowed_by_robots, parse_robots  # noqa: E402


ROBOTS_FIXTURE = """\
# Sample robots
User-agent: *
Disallow: /private
Allow: /private/public

User-agent: Googlebot
Disallow: /search

User-agent: GPTBot
Disallow: /

Sitemap: https://example.com/sitemap.xml
Sitemap: https://example.com/news-sitemap.xml
"""


class ParseRobotsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.parsed = parse_robots(ROBOTS_FIXTURE)

    def test_sitemaps_extracted(self) -> None:
        self.assertEqual(
            self.parsed["sitemaps"],
            ["https://example.com/sitemap.xml", "https://example.com/news-sitemap.xml"],
        )

    def test_wildcard_rules_present(self) -> None:
        self.assertIn("*", self.parsed["robots_rules"])
        self.assertIn("/private", self.parsed["robots_rules"]["*"]["disallow"])

    def test_googlebot_rules_present(self) -> None:
        self.assertIn("googlebot", self.parsed["robots_rules"])

    def test_ai_crawler_directives_captured(self) -> None:
        self.assertIn("gptbot", self.parsed["ai_crawler_directives"])
        self.assertEqual(self.parsed["ai_crawler_directives"]["gptbot"]["disallow"], ["/"])

    def test_search_sections_filtered(self) -> None:
        self.assertIn("*", self.parsed["search_crawler_directives"])
        self.assertIn("googlebot", self.parsed["search_crawler_directives"])


class AllowedByRobotsTests(unittest.TestCase):
    def _robots_info(self) -> dict:
        parsed = parse_robots(ROBOTS_FIXTURE)
        return {"present": True, **parsed}

    def test_allowed_when_no_robots(self) -> None:
        result = allowed_by_robots("https://example.com/anything", {"present": False}, agent="googlebot")
        self.assertTrue(result["allowed"])

    def test_googlebot_specific_disallow(self) -> None:
        info = self._robots_info()
        result = allowed_by_robots("https://example.com/search?q=x", info, agent="googlebot")
        self.assertFalse(result["allowed"])
        self.assertEqual(result["matched_agent"], "googlebot")

    def test_googlebot_falls_through_to_other_paths(self) -> None:
        info = self._robots_info()
        result = allowed_by_robots("https://example.com/public", info, agent="googlebot")
        self.assertTrue(result["allowed"])

    def test_unknown_agent_uses_wildcard(self) -> None:
        info = self._robots_info()
        result = allowed_by_robots("https://example.com/private", info, agent="claudebot")
        self.assertFalse(result["allowed"])
        self.assertEqual(result["matched_agent"], "*")

    def test_longest_match_wins(self) -> None:
        info = self._robots_info()
        # /private is disallowed, /private/public is allowed (longer pattern)
        result = allowed_by_robots("https://example.com/private/public", info, agent="claudebot")
        self.assertTrue(result["allowed"])


if __name__ == "__main__":
    unittest.main()
