# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- **CRITICAL**: Fixed FAQPage schema handling - now correctly notes it's restricted for Google rich results but recommended for AI search engines (GEO benefits)
- **SECURITY**: Enhanced SSRF protection in fetch_page.py to validate redirect targets
- **SECURITY**: Fixed XXE vulnerability in onpage_checker.py XML parser fallback
- Standardized error handling across all 21 scripts with consistent result["error"] pattern
- Updated README.md with correct repository information and PDF documentation
- Added SKILL_DIR setup instructions to SKILL.md

### Added
- **Integration test suite** with 112 passing tests covering all major functionality
- **Configuration file support** - ~/.sgeorc (YAML) and sgeo.config.json with priority system
- **Rate limit handling** with exponential backoff for all API-calling scripts (6 scripts)
- **Progress indicators** for long-running operations (5 scripts)
- **Performance optimizations**:
  - MinHash with numpy for 10-100x speedup in duplicate detection
  - Connection pooling in broken_links.py, link_profile.py, internal_links.py
  - LRU cache for HTML parsing to avoid redundant operations
- Comprehensive CODE-REVIEW.md with detailed analysis of all scripts
- A-PLUS-ROADMAP.md tracking upgrade from B+ to A+ grade
- CONTRIBUTING.md with development guidelines and PR process
- CHANGELOG.md for version tracking
- PDF report generation documentation in README.md
- Testing section in README.md with coverage information
- Configuration section in README.md with setup examples

### Changed
- Schema validator now treats FAQPage as informational rather than error
- parse_html.py updated to align with FAQPage policy
- generate_report.py now loads configuration from files with CLI override support
- All scripts now use consistent exception catching patterns
- requirements.txt updated with optional dependencies (numpy, pyyaml, reportlab)
- requirements-dev.txt created for test dependencies

## [1.0.0] - 2026-03-13

### Added
- Initial release with 21 Python audit scripts
- MECE framework for dual SEO/GEO scoring
- HTML dashboard generation with interactive visualizations
- PDF report generation support
- Cross-platform installation (macOS, Linux, Windows)
- Comprehensive documentation and reference materials

### Features
- Technical Infrastructure checks (robots.txt, security headers, redirects, broken links)
- On-Page Optimization analysis (headings, meta tags, internal links)
- Content Quality assessment (readability, E-E-A-T, citability)
- Structured Data validation (JSON-LD schema, FAQPage handling)
- AI Crawler Access checks (llms.txt, AI bot management)
- Brand Authority scanning (Wikipedia, YouTube, Reddit presence)
- Performance monitoring (Core Web Vitals via PageSpeed Insights)
- Duplicate content detection (MinHash/Jaccard similarity)
- Hreflang validation (8-point compliance check)
- Link profile analysis (orphan pages, anchor text distribution)

[Unreleased]: https://github.com/yourusername/seo-geo-master-check/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/yourusername/seo-geo-master-check/releases/tag/v1.0.0
