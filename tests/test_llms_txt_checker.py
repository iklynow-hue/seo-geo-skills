"""Tests for llmstxt_generator.py"""

import pytest
import responses
import sys
import os

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from llmstxt_generator import validate_llmstxt, generate_llmstxt


class TestValidateLlmsTxt:
    """Tests for validate_llmstxt function."""

    @responses.activate
    def test_valid_llmstxt(self, mock_llmstxt_valid):
        """Test validation of valid llms.txt."""
        responses.add(
            responses.GET,
            "https://example.com/llms.txt",
            body=mock_llmstxt_valid,
            status=200
        )
        responses.add(
            responses.GET,
            "https://example.com/llms-full.txt",
            status=404
        )

        result = validate_llmstxt("https://example.com")

        assert result["exists"] is True
        assert result["format_valid"] is True
        assert result["has_title"] is True
        assert result["has_description"] is True
        assert result["has_sections"] is True
        assert result["has_links"] is True
        assert result["section_count"] >= 2
        assert result["link_count"] >= 2

    @responses.activate
    def test_missing_llmstxt(self):
        """Test handling of missing llms.txt."""
        responses.add(
            responses.GET,
            "https://example.com/llms.txt",
            status=404
        )
        responses.add(
            responses.GET,
            "https://example.com/llms-full.txt",
            status=404
        )

        result = validate_llmstxt("https://example.com")

        assert result["exists"] is False
        assert result["format_valid"] is False
        assert len(result["issues"]) > 0

    @responses.activate
    def test_llmstxt_no_title(self, mock_llmstxt_no_title):
        """Test detection of missing title."""
        responses.add(
            responses.GET,
            "https://example.com/llms.txt",
            body=mock_llmstxt_no_title,
            status=200
        )
        responses.add(
            responses.GET,
            "https://example.com/llms-full.txt",
            status=404
        )

        result = validate_llmstxt("https://example.com")

        assert result["has_title"] is False
        assert any("Missing title" in issue for issue in result["issues"])

    @responses.activate
    def test_llmstxt_minimal(self, mock_llmstxt_minimal):
        """Test validation of minimal llms.txt."""
        responses.add(
            responses.GET,
            "https://example.com/llms.txt",
            body=mock_llmstxt_minimal,
            status=200
        )
        responses.add(
            responses.GET,
            "https://example.com/llms-full.txt",
            status=404
        )

        result = validate_llmstxt("https://example.com")

        assert result["exists"] is True
        assert result["format_valid"] is False
        assert result["has_description"] is False
        assert any("Missing description" in issue for issue in result["issues"])

    @responses.activate
    def test_llmstxt_no_sections(self):
        """Test detection of missing sections."""
        content = """# Example Site
> Description here

- [Home](https://example.com/)
"""
        responses.add(
            responses.GET,
            "https://example.com/llms.txt",
            body=content,
            status=200
        )
        responses.add(
            responses.GET,
            "https://example.com/llms-full.txt",
            status=404
        )

        result = validate_llmstxt("https://example.com")

        assert result["has_sections"] is False
        assert any("No sections found" in issue for issue in result["issues"])

    @responses.activate
    def test_llmstxt_no_links(self):
        """Test detection of missing links."""
        content = """# Example Site
> Description here

## Main Pages
"""
        responses.add(
            responses.GET,
            "https://example.com/llms.txt",
            body=content,
            status=200
        )
        responses.add(
            responses.GET,
            "https://example.com/llms-full.txt",
            status=404
        )

        result = validate_llmstxt("https://example.com")

        assert result["has_links"] is False
        assert any("No page links found" in issue for issue in result["issues"])

    @responses.activate
    def test_llmstxt_full_version_exists(self, mock_llmstxt_valid):
        """Test detection of llms-full.txt."""
        responses.add(
            responses.GET,
            "https://example.com/llms.txt",
            body=mock_llmstxt_valid,
            status=200
        )
        responses.add(
            responses.GET,
            "https://example.com/llms-full.txt",
            body="# Full version content",
            status=200
        )

        result = validate_llmstxt("https://example.com")

        assert result["full_version"]["exists"] is True

    @responses.activate
    def test_suggestions_for_improvement(self, mock_llmstxt_minimal):
        """Test that suggestions are generated for minimal content."""
        responses.add(
            responses.GET,
            "https://example.com/llms.txt",
            body=mock_llmstxt_minimal,
            status=200
        )
        responses.add(
            responses.GET,
            "https://example.com/llms-full.txt",
            status=404
        )

        result = validate_llmstxt("https://example.com")

        assert len(result["suggestions"]) > 0

    def test_network_error(self):
        """Test handling of network errors."""
        # Test with invalid URL that will cause connection error
        result = validate_llmstxt("https://invalid-domain-that-does-not-exist-12345.com")

        assert result["exists"] is False
        assert len(result["issues"]) > 0


class TestGenerateLlmsTxt:
    """Tests for generate_llmstxt function."""

    @responses.activate
    def test_basic_generation(self):
        """Test basic llms.txt generation."""
        homepage_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Example Site - Homepage</title>
            <meta name="description" content="This is an example site">
        </head>
        <body>
            <nav>
                <a href="/">Home</a>
                <a href="/about">About Us</a>
                <a href="/products">Products</a>
                <a href="/blog">Blog</a>
                <a href="/contact">Contact</a>
            </nav>
        </body>
        </html>
        """

        responses.add(
            responses.GET,
            "https://example.com",
            body=homepage_html,
            status=200
        )

        result = generate_llmstxt("https://example.com")

        assert "generated_llmstxt" in result
        assert "generated_llmstxt_full" in result
        assert "# Example Site" in result["generated_llmstxt"]
        assert ">" in result["generated_llmstxt"]  # Description
        assert "##" in result["generated_llmstxt"]  # Sections

    @responses.activate
    def test_page_categorization(self):
        """Test that pages are categorized correctly."""
        homepage_html = """
        <!DOCTYPE html>
        <html>
        <head><title>Test Site</title></head>
        <body>
            <a href="/pricing">Pricing</a>
            <a href="/blog/article">Blog Article</a>
            <a href="/about">About</a>
            <a href="/help">Help Center</a>
        </body>
        </html>
        """

        responses.add(
            responses.GET,
            "https://example.com",
            body=homepage_html,
            status=200
        )

        result = generate_llmstxt("https://example.com")

        assert result["sections"]["Products & Services"] > 0
        assert result["sections"]["Resources & Blog"] > 0
        assert result["sections"]["Company"] > 0
        assert result["sections"]["Support"] > 0

    @responses.activate
    def test_max_pages_limit(self):
        """Test that max_pages parameter limits crawling."""
        homepage_html = """
        <!DOCTYPE html>
        <html>
        <head><title>Test Site</title></head>
        <body>
            """ + "\n".join([f'<a href="/page{i}">Page {i}</a>' for i in range(100)]) + """
        </body>
        </html>
        """

        responses.add(
            responses.GET,
            "https://example.com",
            body=homepage_html,
            status=200
        )

        result = generate_llmstxt("https://example.com", max_pages=10)

        assert result["pages_analyzed"] <= 10

    @responses.activate
    def test_external_links_ignored(self):
        """Test that external links are not included."""
        homepage_html = """
        <!DOCTYPE html>
        <html>
        <head><title>Test Site</title></head>
        <body>
            <a href="/internal">Internal Link</a>
            <a href="https://external.com/page">External Link</a>
            <a href="https://example.com/local">Local Link</a>
        </body>
        </html>
        """

        responses.add(
            responses.GET,
            "https://example.com",
            body=homepage_html,
            status=200
        )

        result = generate_llmstxt("https://example.com")

        # Should not include external.com links
        assert "external.com" not in result["generated_llmstxt"]

    @responses.activate
    def test_file_extensions_ignored(self):
        """Test that file downloads are not included."""
        homepage_html = """
        <!DOCTYPE html>
        <html>
        <head><title>Test Site</title></head>
        <body>
            <a href="/page">Page</a>
            <a href="/document.pdf">PDF</a>
            <a href="/image.jpg">Image</a>
            <a href="/style.css">CSS</a>
        </body>
        </html>
        """

        responses.add(
            responses.GET,
            "https://example.com",
            body=homepage_html,
            status=200
        )

        result = generate_llmstxt("https://example.com")

        # Should not include file extensions
        assert ".pdf" not in result["generated_llmstxt"]
        assert ".jpg" not in result["generated_llmstxt"]
        assert ".css" not in result["generated_llmstxt"]

    @responses.activate
    def test_contact_section_added(self):
        """Test that contact section is always added."""
        homepage_html = """
        <!DOCTYPE html>
        <html>
        <head><title>Test Site</title></head>
        <body><a href="/page">Page</a></body>
        </html>
        """

        responses.add(
            responses.GET,
            "https://example.com",
            body=homepage_html,
            status=200
        )

        result = generate_llmstxt("https://example.com")

        assert "## Contact" in result["generated_llmstxt"]
        assert "example.com" in result["generated_llmstxt"]

    def test_network_error_handling(self):
        """Test handling of network errors during generation."""
        # Test with invalid URL that will cause connection error
        result = generate_llmstxt("https://invalid-domain-that-does-not-exist-12345.com")

        assert "error" in result
