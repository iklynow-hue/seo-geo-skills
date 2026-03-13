# Codebase Structure

## Top-Level Files
- `SKILL.md` — Claude CLI skill orchestration logic and command definitions
- `MECE-FRAMEWORK.md` — Framework documentation for audit categorization
- `README.md` — User-facing documentation
- `install.sh` / `install.ps1` — Cross-platform installation scripts
- `uninstall.sh` / `uninstall.ps1` — Uninstallation scripts
- `.gitignore` — Excludes outputs/, __pycache__, .DS_Store

## Scripts Directory (19+ audit scripts)
Key scripts:
- `fetch_page.py` — Fetch and save HTML content
- `parse_html.py` — Parse HTML and extract metadata
- `robots_checker.py` — Check robots.txt rules
- `llms_txt_checker.py` — Check llms.txt for AI crawler guidance
- `security_headers.py` — Validate security headers (CSP, HSTS, etc.)
- `broken_links.py` — Find broken links
- `redirect_checker.py` — Validate redirects
- `readability.py` — Content readability analysis
- `social_meta.py` — Open Graph and Twitter Card validation
- `internal_links.py` — Internal link structure analysis
- `pagespeed.py` — Core Web Vitals via PageSpeed API
- `validate_schema.py` / `schema_validator.py` — Schema.org validation
- `citability_scorer.py` — AI citability scoring
- `brand_scanner.py` — Brand authority and platform presence
- `onpage_checker.py` — On-page SEO checks (supports --multi for sitemap crawl)
- `generate_report.py` — HTML dashboard generator with dual scores
- `generate_pdf_report.py` — PDF report generator
- `sgeo_to_pdf_bridge.py` — Bridge for PDF generation

## Resources Directory
- `resources/references/` — Framework reference documentation
  - `mece-framework.md` — Category definitions
  - `dual-scoring-methodology.md` — Weight calculations
  - `faqpage-guidance.md` — FAQPage schema policy
  - `quality-gates.md` — Content quality thresholds
  - `cwv-thresholds.md` — Core Web Vitals standards
  - `eeat-framework.md` — E-E-A-T scoring criteria
  - `schema-types.md` — Active/deprecated schema types

## Integration
- Symlink at `~/.claude/skills/sgeo` points to project root
- Claude CLI loads SKILL.md for command definitions
- Scripts are called via absolute paths from SKILL_DIR variable
