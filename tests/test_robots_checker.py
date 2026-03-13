"""Tests for robots_checker.py"""

import pytest
import responses
import sys
import os

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from robots_checker import fetch_robots_txt, _parse_robots, AI_CRAWLERS


class TestFetchRobotsTxt:
    """Tests for fetch_robots_txt function."""

    @responses.activate
    def test_successful_fetch(self, mock_robots_txt_basic):
        """Test successful robots.txt fetch."""
        responses.add(
            responses.GET,
            "https://example.com/robots.txt",
            body=mock_robots_txt_basic,
            status=200
        )

        result = fetch_robots_txt("https://example.com")

        assert result["status"] == 200
        assert result["raw"] == mock_robots_txt_basic
        assert result["error"] is None
        assert len(result["sitemaps"]) > 0

    @responses.activate
    def test_missing_robots_txt(self):
        """Test handling of missing robots.txt (404)."""
        responses.add(
            responses.GET,
            "https://example.com/robots.txt",
            status=404
        )

        result = fetch_robots_txt("https://example.com")

        assert result["status"] == 404
        assert any("No robots.txt found" in issue for issue in result["issues"])
        # All AI crawlers should be marked as allowed
        for crawler in AI_CRAWLERS:
            assert crawler in result["ai_crawler_status"]
            assert "allowed" in result["ai_crawler_status"][crawler].lower()

    @responses.activate
    def test_url_without_scheme(self, mock_robots_txt_basic):
        """Test URL normalization when scheme is missing."""
        responses.add(
            responses.GET,
            "https://example.com/robots.txt",
            body=mock_robots_txt_basic,
            status=200
        )

        result = fetch_robots_txt("example.com")

        assert result["url"] == "https://example.com/robots.txt"
        assert result["status"] == 200

    @responses.activate
    def test_http_error(self):
        """Test handling of HTTP errors."""
        responses.add(
            responses.GET,
            "https://example.com/robots.txt",
            status=500
        )

        result = fetch_robots_txt("https://example.com")

        assert result["status"] == 500
        assert result["error"] == "HTTP 500"

    def test_network_error(self):
        """Test handling of network errors."""
        # Don't use @responses.activate for this test
        # Test with invalid URL that will cause connection error
        result = fetch_robots_txt("https://invalid-domain-that-does-not-exist-12345.com")

        assert result["error"] is not None

    @responses.activate
    def test_timeout_parameter(self, mock_robots_txt_basic):
        """Test custom timeout parameter."""
        responses.add(
            responses.GET,
            "https://example.com/robots.txt",
            body=mock_robots_txt_basic,
            status=200
        )

        result = fetch_robots_txt("https://example.com", timeout=30)
        assert result["status"] == 200


class TestParseRobots:
    """Tests for _parse_robots function."""

    def test_basic_parsing(self, mock_robots_txt_basic):
        """Test basic robots.txt parsing."""
        result = {
            "user_agents": {},
            "sitemaps": [],
            "crawl_delays": {},
            "ai_crawler_status": {},
            "issues": []
        }

        _parse_robots(mock_robots_txt_basic, result)

        assert "*" in result["user_agents"]
        assert len(result["user_agents"]["*"]["disallow"]) == 2
        assert "/admin/" in result["user_agents"]["*"]["disallow"]
        assert len(result["sitemaps"]) == 1

    def test_ai_crawler_detection(self, mock_robots_txt_with_ai_crawlers):
        """Test AI crawler rule detection."""
        result = {
            "user_agents": {},
            "sitemaps": [],
            "crawl_delays": {},
            "ai_crawler_status": {},
            "issues": []
        }

        _parse_robots(mock_robots_txt_with_ai_crawlers, result)

        assert "GPTBot" in result["ai_crawler_status"]
        assert "fully blocked" in result["ai_crawler_status"]["GPTBot"]
        assert "ClaudeBot" in result["ai_crawler_status"]
        assert "partially blocked" in result["ai_crawler_status"]["ClaudeBot"]

    def test_crawl_delay_parsing(self, mock_robots_txt_with_crawl_delay):
        """Test crawl-delay directive parsing."""
        result = {
            "user_agents": {},
            "sitemaps": [],
            "crawl_delays": {},
            "ai_crawler_status": {},
            "issues": []
        }

        _parse_robots(mock_robots_txt_with_crawl_delay, result)

        assert "*" in result["crawl_delays"]
        assert result["crawl_delays"]["*"] == 10.0
        assert "Bingbot" in result["crawl_delays"]
        assert result["crawl_delays"]["Bingbot"] == 5.0

    def test_multiple_user_agents(self):
        """Test parsing of multiple consecutive user-agent declarations."""
        content = """User-agent: Googlebot
User-agent: Bingbot
Disallow: /private/

User-agent: *
Disallow: /admin/
"""
        result = {
            "user_agents": {},
            "sitemaps": [],
            "crawl_delays": {},
            "ai_crawler_status": {},
            "issues": []
        }

        _parse_robots(content, result)

        assert "Googlebot" in result["user_agents"]
        assert "Bingbot" in result["user_agents"]
        assert "/private/" in result["user_agents"]["Googlebot"]["disallow"]
        assert "/private/" in result["user_agents"]["Bingbot"]["disallow"]

    def test_allow_directive(self):
        """Test Allow directive parsing."""
        content = """User-agent: *
Disallow: /private/
Allow: /private/public/
"""
        result = {
            "user_agents": {},
            "sitemaps": [],
            "crawl_delays": {},
            "ai_crawler_status": {},
            "issues": []
        }

        _parse_robots(content, result)

        assert len(result["user_agents"]["*"]["allow"]) == 1
        assert "/private/public/" in result["user_agents"]["*"]["allow"]

    def test_comments_and_empty_lines(self):
        """Test that comments and empty lines are ignored."""
        content = """# This is a comment
User-agent: *

# Another comment
Disallow: /admin/

Sitemap: https://example.com/sitemap.xml
"""
        result = {
            "user_agents": {},
            "sitemaps": [],
            "crawl_delays": {},
            "ai_crawler_status": {},
            "issues": []
        }

        _parse_robots(content, result)

        assert "*" in result["user_agents"]
        assert len(result["sitemaps"]) == 1

    def test_wildcard_blocking(self):
        """Test wildcard blocking affects AI crawlers."""
        content = """User-agent: *
Disallow: /
"""
        result = {
            "user_agents": {},
            "sitemaps": [],
            "crawl_delays": {},
            "ai_crawler_status": {},
            "issues": []
        }

        _parse_robots(content, result)

        # AI crawlers should be marked as blocked by wildcard
        for crawler in AI_CRAWLERS:
            assert "blocked by wildcard" in result["ai_crawler_status"][crawler]

    def test_unmanaged_ai_crawlers_issue(self):
        """Test that unmanaged AI crawlers generate issues."""
        content = """User-agent: *
Disallow: /admin/
"""
        result = {
            "user_agents": {},
            "sitemaps": [],
            "crawl_delays": {},
            "ai_crawler_status": {},
            "issues": []
        }

        _parse_robots(content, result)

        # Should have issue about unmanaged AI crawlers
        assert any("AI crawlers not explicitly managed" in issue for issue in result["issues"])

    def test_missing_sitemap_issue(self):
        """Test that missing sitemap generates issue."""
        content = """User-agent: *
Disallow: /admin/
"""
        result = {
            "user_agents": {},
            "sitemaps": [],
            "crawl_delays": {},
            "ai_crawler_status": {},
            "issues": []
        }

        _parse_robots(content, result)

        assert any("No Sitemap directive" in issue for issue in result["issues"])

    def test_multiple_sitemaps(self):
        """Test parsing of multiple sitemap declarations."""
        content = """User-agent: *
Disallow:

Sitemap: https://example.com/sitemap.xml
Sitemap: https://example.com/sitemap-news.xml
Sitemap: https://example.com/sitemap-images.xml
"""
        result = {
            "user_agents": {},
            "sitemaps": [],
            "crawl_delays": {},
            "ai_crawler_status": {},
            "issues": []
        }

        _parse_robots(content, result)

        assert len(result["sitemaps"]) == 3

    def test_empty_disallow(self):
        """Test empty Disallow directive (allows everything)."""
        content = """User-agent: Googlebot
Disallow:
"""
        result = {
            "user_agents": {},
            "sitemaps": [],
            "crawl_delays": {},
            "ai_crawler_status": {},
            "issues": []
        }

        _parse_robots(content, result)

        assert "Googlebot" in result["user_agents"]
        # Empty disallow should not be added to the list
        assert len(result["user_agents"]["Googlebot"]["disallow"]) == 0

    def test_invalid_crawl_delay(self):
        """Test handling of invalid crawl-delay value."""
        content = """User-agent: *
Crawl-delay: invalid
Disallow: /
"""
        result = {
            "user_agents": {},
            "sitemaps": [],
            "crawl_delays": {},
            "ai_crawler_status": {},
            "issues": []
        }

        _parse_robots(content, result)

        # Should not crash, just skip invalid value
        assert "*" not in result["crawl_delays"]
