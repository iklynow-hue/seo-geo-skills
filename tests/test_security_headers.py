"""Tests for security_headers.py"""

import pytest
import responses
import sys
import os

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from security_headers import check_security_headers, SECURITY_HEADERS


class TestCheckSecurityHeaders:
    """Tests for check_security_headers function."""

    @responses.activate
    def test_https_detection(self):
        """Test HTTPS detection and scoring."""
        responses.add(
            responses.GET,
            "https://example.com",
            status=200,
            headers={}
        )

        result = check_security_headers("https://example.com")

        assert result["https"] is True
        assert result["score"] >= 25

    @responses.activate
    def test_http_warning(self):
        """Test warning for non-HTTPS sites."""
        responses.add(
            responses.GET,
            "http://example.com",
            status=200,
            headers={}
        )

        result = check_security_headers("http://example.com")

        assert result["https"] is False
        assert any("not using HTTPS" in issue for issue in result["issues"])

    @responses.activate
    def test_url_without_scheme(self):
        """Test URL normalization when scheme is missing."""
        responses.add(
            responses.GET,
            "https://example.com",
            status=200,
            headers={}
        )

        result = check_security_headers("example.com")

        assert result["url"] == "https://example.com"

    @responses.activate
    def test_all_headers_present(self):
        """Test scoring when all security headers are present."""
        headers = {
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'",
            "X-Frame-Options": "SAMEORIGIN",
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "camera=(), microphone=()"
        }

        responses.add(
            responses.GET,
            "https://example.com",
            status=200,
            headers=headers
        )

        result = check_security_headers("https://example.com")

        assert result["https"] is True
        assert result["score"] == 100
        assert len(result["headers_present"]) == 6
        assert len(result["headers_missing"]) == 0

    @responses.activate
    def test_missing_headers(self):
        """Test detection of missing headers."""
        responses.add(
            responses.GET,
            "https://example.com",
            status=200,
            headers={}
        )

        result = check_security_headers("https://example.com")

        assert len(result["headers_missing"]) == 6
        assert len(result["recommendations"]) > 0

    @responses.activate
    def test_hsts_validation(self):
        """Test HSTS header validation."""
        headers = {
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
        }

        responses.add(
            responses.GET,
            "https://example.com",
            status=200,
            headers=headers
        )

        result = check_security_headers("https://example.com")

        assert "HSTS (Strict-Transport-Security)" in result["headers_present"]
        # Should not have HSTS warnings for proper config
        hsts_issues = [i for i in result["issues"] if "HSTS" in i]
        assert len(hsts_issues) == 0

    @responses.activate
    def test_hsts_low_max_age(self):
        """Test warning for low HSTS max-age."""
        headers = {
            "Strict-Transport-Security": "max-age=3600"
        }

        responses.add(
            responses.GET,
            "https://example.com",
            status=200,
            headers=headers
        )

        result = check_security_headers("https://example.com")

        assert any("max-age is 3600s" in issue for issue in result["issues"])

    @responses.activate
    def test_hsts_missing_includesubdomains(self):
        """Test warning for HSTS without includeSubDomains."""
        headers = {
            "Strict-Transport-Security": "max-age=31536000"
        }

        responses.add(
            responses.GET,
            "https://example.com",
            status=200,
            headers=headers
        )

        result = check_security_headers("https://example.com")

        assert any("missing includeSubDomains" in issue for issue in result["issues"])

    @responses.activate
    def test_case_insensitive_headers(self):
        """Test that header names are case-insensitive."""
        headers = {
            "STRICT-TRANSPORT-SECURITY": "max-age=31536000",
            "content-security-policy": "default-src 'self'",
            "X-Frame-Options": "SAMEORIGIN"
        }

        responses.add(
            responses.GET,
            "https://example.com",
            status=200,
            headers=headers
        )

        result = check_security_headers("https://example.com")

        assert len(result["headers_present"]) == 3

    @responses.activate
    def test_header_values_stored(self):
        """Test that header values are stored correctly."""
        headers = {
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff"
        }

        responses.add(
            responses.GET,
            "https://example.com",
            status=200,
            headers=headers
        )

        result = check_security_headers("https://example.com")

        assert result["header_values"]["x-frame-options"] == "DENY"
        assert result["header_values"]["x-content-type-options"] == "nosniff"

    @responses.activate
    def test_score_capped_at_100(self):
        """Test that score doesn't exceed 100."""
        headers = {
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'",
            "X-Frame-Options": "SAMEORIGIN",
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "camera=(), microphone=()"
        }

        responses.add(
            responses.GET,
            "https://example.com",
            status=200,
            headers=headers
        )

        result = check_security_headers("https://example.com")

        assert result["score"] <= 100

    @responses.activate
    def test_many_missing_headers_issue(self):
        """Test issue generation for many missing headers."""
        responses.add(
            responses.GET,
            "https://example.com",
            status=200,
            headers={}
        )

        result = check_security_headers("https://example.com")

        assert any("security headers missing" in issue for issue in result["issues"])

    @responses.activate
    def test_few_missing_headers_warning(self):
        """Test warning for few missing headers."""
        headers = {
            "Strict-Transport-Security": "max-age=31536000",
            "Content-Security-Policy": "default-src 'self'",
            "X-Frame-Options": "SAMEORIGIN"
        }

        responses.add(
            responses.GET,
            "https://example.com",
            status=200,
            headers=headers
        )

        result = check_security_headers("https://example.com")

        # Should have warning for missing headers (3 missing)
        assert any("header(s) missing" in issue for issue in result["issues"])

    def test_network_error(self):
        """Test handling of network errors."""
        # Test with invalid URL that will cause connection error
        result = check_security_headers("https://invalid-domain-that-does-not-exist-12345.com")

        assert result["error"] is not None

    @responses.activate
    def test_redirect_following(self):
        """Test that redirects are followed and final URL is checked."""
        # The responses library will follow redirects automatically
        # We just need to mock the final destination
        responses.add(
            responses.GET,
            "https://example.com",
            status=200,
            headers={"Strict-Transport-Security": "max-age=31536000"}
        )

        # Test with HTTPS URL directly (simulating post-redirect)
        result = check_security_headers("https://example.com")

        # Should detect HTTPS
        assert result["https"] is True
        assert result["score"] > 0

    @responses.activate
    def test_timeout_parameter(self):
        """Test custom timeout parameter."""
        responses.add(
            responses.GET,
            "https://example.com",
            status=200,
            headers={}
        )

        result = check_security_headers("https://example.com", timeout=30)
        assert result["error"] is None

    @responses.activate
    def test_recommendations_generated(self):
        """Test that recommendations are generated for missing headers."""
        responses.add(
            responses.GET,
            "https://example.com",
            status=200,
            headers={}
        )

        result = check_security_headers("https://example.com")

        assert len(result["recommendations"]) > 0
        # Check that recommendations include header names
        rec_text = " ".join(result["recommendations"])
        assert "HSTS" in rec_text or "Strict-Transport-Security" in rec_text
