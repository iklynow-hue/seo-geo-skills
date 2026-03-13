"""Pytest fixtures for SEO/GEO Master Check tests."""

import pytest


@pytest.fixture
def mock_html_with_jsonld():
    """HTML with valid JSON-LD schema."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page</title>
        <meta name="description" content="Test description">
        <script type="application/ld+json">
        {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": "Test Company",
            "url": "https://example.com"
        }
        </script>
    </head>
    <body>
        <h1>Test Page</h1>
        <p>This is a test page with some content.</p>
    </body>
    </html>
    """


@pytest.fixture
def mock_html_with_faqpage():
    """HTML with FAQPage schema."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <script type="application/ld+json">
        {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [{
                "@type": "Question",
                "name": "What is this?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "This is a test."
                }
            }]
        }
        </script>
    </head>
    <body><h1>FAQ</h1></body>
    </html>
    """


@pytest.fixture
def mock_html_with_deprecated_schema():
    """HTML with deprecated schema type."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <script type="application/ld+json">
        {
            "@context": "https://schema.org",
            "@type": "HowTo",
            "name": "How to do something"
        }
        </script>
    </head>
    <body><h1>How To</h1></body>
    </html>
    """


@pytest.fixture
def mock_html_with_placeholder():
    """HTML with placeholder text in schema."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <script type="application/ld+json">
        {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": "[Business Name]",
            "address": "[City], [State]"
        }
        </script>
    </head>
    <body><h1>Test</h1></body>
    </html>
    """


@pytest.fixture
def mock_html_with_invalid_jsonld():
    """HTML with invalid JSON-LD."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <script type="application/ld+json">
        {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": "Test",
            invalid json here
        }
        </script>
    </head>
    <body><h1>Test</h1></body>
    </html>
    """


@pytest.fixture
def mock_robots_txt_basic():
    """Basic robots.txt content."""
    return """User-agent: *
Disallow: /admin/
Disallow: /private/

Sitemap: https://example.com/sitemap.xml
"""


@pytest.fixture
def mock_robots_txt_with_ai_crawlers():
    """robots.txt with AI crawler rules."""
    return """User-agent: *
Disallow: /admin/

User-agent: GPTBot
Disallow: /

User-agent: ClaudeBot
Disallow: /private/

User-agent: Googlebot
Allow: /

Sitemap: https://example.com/sitemap.xml
Sitemap: https://example.com/sitemap-news.xml
"""


@pytest.fixture
def mock_robots_txt_with_crawl_delay():
    """robots.txt with crawl-delay directive."""
    return """User-agent: *
Crawl-delay: 10
Disallow: /admin/

User-agent: Bingbot
Crawl-delay: 5
Disallow:
"""


@pytest.fixture
def mock_llmstxt_valid():
    """Valid llms.txt content."""
    return """# Example Site
> A comprehensive example website

## Main Pages
- [Home](https://example.com/): Homepage
- [About](https://example.com/about): About us

## Products & Services
- [Product A](https://example.com/products/a): Our flagship product
- [Product B](https://example.com/products/b): Secondary offering

## Contact
- Website: https://example.com
- Email: contact@example.com
"""


@pytest.fixture
def mock_llmstxt_minimal():
    """Minimal llms.txt content (missing elements)."""
    return """# Example Site

- [Home](https://example.com/)
"""


@pytest.fixture
def mock_llmstxt_no_title():
    """llms.txt without title."""
    return """## Main Pages
- [Home](https://example.com/)
"""


@pytest.fixture
def mock_readable_text():
    """Simple readable text for testing."""
    return """
    This is a simple sentence. It has easy words. The text is clear.

    Another paragraph here. It contains more sentences. They are short and simple.
    """


@pytest.fixture
def mock_complex_text():
    """Complex text with long sentences."""
    return """
    This is an extraordinarily complicated sentence that contains numerous
    multisyllabic words and demonstrates significantly elevated complexity
    through its utilization of sophisticated vocabulary and unnecessarily
    extended grammatical constructions that could potentially confuse readers.

    Furthermore, this subsequent paragraph continues the pattern of verbose
    communication by incorporating additional unnecessarily complicated
    terminology and maintaining excessively lengthy sentence structures.
    """


@pytest.fixture
def mock_html_content():
    """HTML content for text extraction testing."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page</title>
        <script>console.log('test');</script>
        <style>.test { color: red; }</style>
    </head>
    <body>
        <nav>Navigation menu</nav>
        <header>Header content</header>
        <main>
            <h1>Main Content</h1>
            <p>This is the main content. It should be extracted.</p>
            <p>Another paragraph with useful information.</p>
        </main>
        <footer>Footer content</footer>
    </body>
    </html>
    """
