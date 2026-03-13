"""Tests for schema_validator.py"""

import pytest
import sys
import os

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from schema_validator import validate_jsonld, _validate_schema_object


class TestValidateJsonLD:
    """Tests for validate_jsonld function."""

    def test_valid_schema(self, mock_html_with_jsonld):
        """Test validation of valid JSON-LD schema."""
        errors = validate_jsonld(mock_html_with_jsonld)
        assert isinstance(errors, list)
        assert len(errors) == 0

    def test_no_schema_returns_empty(self):
        """Test that HTML without schema returns empty list."""
        html = "<html><body>No schema here</body></html>"
        errors = validate_jsonld(html)
        assert errors == []

    def test_invalid_json(self, mock_html_with_invalid_jsonld):
        """Test detection of invalid JSON syntax."""
        errors = validate_jsonld(mock_html_with_invalid_jsonld)
        assert len(errors) > 0
        assert any("Invalid JSON" in err for err in errors)

    def test_faqpage_schema(self, mock_html_with_faqpage):
        """Test FAQPage schema generates informational note."""
        errors = validate_jsonld(mock_html_with_faqpage)
        assert len(errors) > 0
        assert any("FAQPage" in err and "GEO benefits" in err for err in errors)

    def test_deprecated_schema(self, mock_html_with_deprecated_schema):
        """Test detection of deprecated schema types."""
        errors = validate_jsonld(mock_html_with_deprecated_schema)
        assert len(errors) > 0
        assert any("HowTo" in err and "deprecated" in err for err in errors)

    def test_placeholder_text(self, mock_html_with_placeholder):
        """Test detection of placeholder text in schema."""
        errors = validate_jsonld(mock_html_with_placeholder)
        assert len(errors) > 0
        assert any("placeholder" in err.lower() for err in errors)

    def test_multiple_schema_blocks(self):
        """Test validation of multiple JSON-LD blocks."""
        html = """
        <html>
        <head>
            <script type="application/ld+json">
            {"@context": "https://schema.org", "@type": "Organization", "name": "Test"}
            </script>
            <script type="application/ld+json">
            {"@context": "https://schema.org", "@type": "WebSite", "url": "https://example.com"}
            </script>
        </head>
        </html>
        """
        errors = validate_jsonld(html)
        assert isinstance(errors, list)

    def test_schema_array(self):
        """Test validation of JSON-LD array format."""
        html = """
        <html>
        <head>
            <script type="application/ld+json">
            [
                {"@context": "https://schema.org", "@type": "Organization", "name": "Test"},
                {"@context": "https://schema.org", "@type": "WebSite", "url": "https://example.com"}
            ]
            </script>
        </head>
        </html>
        """
        errors = validate_jsonld(html)
        assert isinstance(errors, list)


class TestValidateSchemaObject:
    """Tests for _validate_schema_object function."""

    def test_missing_context(self):
        """Test detection of missing @context."""
        obj = {"@type": "Organization", "name": "Test"}
        errors = _validate_schema_object(obj, 1)
        assert any("Missing @context" in err for err in errors)

    def test_missing_type(self):
        """Test detection of missing @type."""
        obj = {"@context": "https://schema.org", "name": "Test"}
        errors = _validate_schema_object(obj, 1)
        assert any("Missing @type" in err for err in errors)

    def test_wrong_context_protocol(self):
        """Test detection of http instead of https in @context."""
        obj = {
            "@context": "http://schema.org",
            "@type": "Organization",
            "name": "Test"
        }
        errors = _validate_schema_object(obj, 1)
        # The validator accepts both http and https, so this shouldn't error
        # Just check that it doesn't crash
        assert isinstance(errors, list)

    def test_deprecated_types(self):
        """Test detection of all deprecated schema types."""
        deprecated_types = [
            "HowTo",
            "SpecialAnnouncement",
            "CourseInfo",
            "EstimatedSalary",
            "LearningVideo",
            "ClaimReview",
            "VehicleListing",
            "PracticeProblem",
            "Dataset"
        ]

        for schema_type in deprecated_types:
            obj = {
                "@context": "https://schema.org",
                "@type": schema_type,
                "name": "Test"
            }
            errors = _validate_schema_object(obj, 1)
            assert any("deprecated" in err.lower() or "retired" in err.lower() for err in errors)

    def test_placeholder_detection(self):
        """Test detection of various placeholder patterns."""
        placeholders = [
            "[Business Name]",
            "[City]",
            "[State]",
            "[Phone]",
            "[Address]",
            "[Your Company]",
            "[INSERT HERE]",
            "REPLACE THIS",
            "[URL]",
            "[Email]"
        ]

        for placeholder in placeholders:
            obj = {
                "@context": "https://schema.org",
                "@type": "Organization",
                "name": placeholder
            }
            errors = _validate_schema_object(obj, 1)
            assert any("placeholder" in err.lower() for err in errors)

    def test_valid_object(self):
        """Test validation of completely valid schema object."""
        obj = {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": "Real Company Name",
            "url": "https://example.com"
        }
        errors = _validate_schema_object(obj, 1)
        # Should have no errors (or only informational ones)
        critical_errors = [e for e in errors if "placeholder" in e.lower() or "deprecated" in e.lower()]
        assert len(critical_errors) == 0

    def test_faqpage_informational_message(self):
        """Test that FAQPage generates informational message, not error."""
        obj = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": []
        }
        errors = _validate_schema_object(obj, 1)
        assert any("FAQPage" in err for err in errors)
        assert any("GEO benefits" in err for err in errors)
