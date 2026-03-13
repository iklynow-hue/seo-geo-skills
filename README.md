# SGEO — Unified SEO + GEO Master Audit

Combined SEO and GEO analysis with MECE (Mutually Exclusive, Collectively Exhaustive) framework.
Produces dual scores: **SEO Score** (traditional search) and **GEO Score** (AI search visibility).

## Quick Start

```bash
# Clone
git clone <your-repository-url>
cd seo-geo-master-check

# Install (macOS / Linux)
bash install.sh

# Install (Windows — PowerShell)
powershell -ExecutionPolicy Bypass -File install.ps1

# Run audit
claude
> sgeo audit https://example.com
```

## Features

- **Dual Scoring**: Independent SEO and GEO scores from single audit
- **MECE Framework**: No overlap, complete coverage across 10 categories
- **Script-Backed**: 22 Python scripts for deterministic verification
- **Cross-Platform**: Works on macOS, Linux, and Windows
- **FAQPage Policy**: Keep FAQPage schema for AI search benefits (despite Google restriction)

## Commands

| Command | Description |
|---------|-------------|
| `sgeo audit <url>` | Full dual-score audit (SEO + GEO) |
| `sgeo seo <url>` | SEO-only audit |
| `sgeo geo <url>` | GEO-only audit |
| `sgeo page <url>` | Deep single-page analysis |
| `sgeo schema <url>` | Schema validation |
| `sgeo content <url>` | Content quality & citability |
| `sgeo brand <url>` | Brand authority scan |
| `sgeo technical <url>` | Technical infrastructure checks |
| `sgeo github <repo>` | GitHub repository SEO optimization |
| `sgeo compare <url>` | Side-by-side SEO vs GEO score comparison |
| `sgeo llmstxt <url>` | llms.txt analysis and generation |

## Scoring

### SEO Score (0-100)
- Technical Infrastructure: 25%
- On-Page Optimization: 20%
- Content Quality: 15%
- Structured Data: 15%
- Performance (CWV): 10%
- Social Signals: 5%
- Local SEO: 10% (if applicable)

### GEO Score (0-100)
- AI Citability: 25%
- Brand Authority: 20%
- Technical Infrastructure: 15%
- Content Quality: 15%
- AI Crawler Access: 10%
- Structured Data: 10%
- Platform Optimization: 5%

## Installation

### Requirements
- Python 3.8+
- `requests`, `beautifulsoup4`, `lxml`

### macOS / Linux
```bash
cd seo-geo-skills
bash install.sh
```

### Windows (PowerShell)
```powershell
cd seo-geo-skills
powershell -ExecutionPolicy Bypass -File install.ps1
```

This will:
1. Install Python dependencies
2. Create symlink at `~/.claude/skills/sgeo`
3. Verify installation

### Uninstall

macOS / Linux:
```bash
bash uninstall.sh
```

Windows (PowerShell):
```powershell
powershell -ExecutionPolicy Bypass -File uninstall.ps1
```

## Project Structure

```
seo-geo-skills/
├── SKILL.md                    # Main skill definition
├── MECE-FRAMEWORK.md           # Framework documentation
├── install.sh                  # Install script (macOS/Linux)
├── install.ps1                 # Install script (Windows)
├── uninstall.sh                # Uninstall script (macOS/Linux)
├── uninstall.ps1               # Uninstall script (Windows)
├── scripts/                    # 22 audit scripts
│   ├── fetch_page.py
│   ├── parse_html.py
│   ├── robots_checker.py
│   ├── llms_txt_checker.py
│   ├── security_headers.py
│   ├── broken_links.py
│   ├── redirect_checker.py
│   ├── readability.py
│   ├── social_meta.py
│   ├── internal_links.py
│   ├── pagespeed.py
│   ├── schema_validator.py
│   ├── citability_scorer.py
│   ├── brand_scanner.py
│   ├── llmstxt_generator.py
│   ├── onpage_checker.py
│   ├── duplicate_content.py
│   ├── hreflang_checker.py
│   ├── link_profile.py
│   ├── sgeo_to_pdf_bridge.py
│   ├── generate_report.py      # HTML dashboard generator
│   └── generate_pdf_report.py  # PDF report generator
└── resources/
    └── references/
        ├── mece-framework.md
        ├── dual-scoring-methodology.md
        ├── faqpage-guidance.md
        ├── quality-gates.md
        ├── cwv-thresholds.md
        ├── eeat-framework.md
        └── schema-types.md
```

## Output Files

After running `sgeo audit <url>`, you'll get:

1. **SGEO-AUDIT-REPORT.md** — Detailed findings with MECE categorization
2. **SGEO-ACTION-PLAN.md** — Prioritized fixes tagged as SEO, GEO, or Both
3. **SGEO-REPORT.html** — Interactive dashboard with dual scores
4. **SGEO-REPORT.pdf** — PDF version of the report (requires reportlab)

### PDF Reports

Generate both HTML and PDF reports:
```bash
python scripts/generate_report.py https://example.com
# Outputs: outputs/<domain>/SGEO-REPORT.html + SGEO-REPORT.pdf
```

Skip PDF generation:
```bash
python scripts/generate_report.py https://example.com --no-pdf
```

Skip auto-opening in browser:
```bash
python scripts/generate_report.py https://example.com --no-open
```

## Configuration

SGEO supports configuration files to set default options without CLI flags. Configuration is loaded from multiple sources with the following priority (highest to lowest):

1. CLI flags (highest priority)
2. `sgeo.config.json` in project root
3. `~/.sgeorc` (YAML format, requires PyYAML)
4. Default values (lowest priority)

### Supported Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `timeout` | 30 | Script execution timeout in seconds |
| `max_workers` | 10 | Number of parallel workers for audit scripts |
| `user_agent` | SGEO-Audit-Bot/1.0 | Custom user agent for HTTP requests |
| `api_keys.pagespeed` | null | PageSpeed Insights API key |
| `output_dir` | outputs/ | Output directory for reports |
| `auto_open_report` | true | Auto-open HTML report in browser |
| `generate_pdf` | true | Generate PDF report along with HTML |

### Setup

#### Global Configuration (YAML)

Create `~/.sgeorc` for user-wide settings:

```bash
cp .sgeorc.example ~/.sgeorc
# Edit with your preferences
nano ~/.sgeorc
```

Example `~/.sgeorc`:
```yaml
timeout: 30
max_workers: 10
api_keys:
  pagespeed: "YOUR_API_KEY_HERE"
auto_open_report: true
generate_pdf: true
```

Requires PyYAML:
```bash
pip install pyyaml
```

#### Project Configuration (JSON)

Create `sgeo.config.json` in project root for project-specific settings:

```bash
cp sgeo.config.json.example sgeo.config.json
# Edit with your preferences
nano sgeo.config.json
```

Example `sgeo.config.json`:
```json
{
  "timeout": 30,
  "max_workers": 10,
  "api_keys": {
    "pagespeed": "YOUR_API_KEY_HERE"
  },
  "auto_open_report": false,
  "generate_pdf": true
}
```

### CLI Override

CLI flags always override config file values:

```bash
# Use config file settings
python scripts/generate_report.py https://example.com

# Override workers from config
python scripts/generate_report.py https://example.com --workers 20

# Override timeout from config
python scripts/generate_report.py https://example.com --timeout 60
```

## Key Principles

### 1. MECE Framework
Every finding belongs to exactly ONE category. No double-counting.

### 2. Dual Scoring
SEO and GEO scores use different weights reflecting each domain's priorities.

### 3. FAQPage Schema
**Keep it.** Google restricts rich results to gov/healthcare, but AI search engines (ChatGPT, Perplexity, Claude, Gemini) actively use FAQPage for content understanding.

### 4. LLM-First, Script-Verified
Start with LLM reasoning, verify with scripts. Never block on script failure.

### 5. Confidence Labels
- **Confirmed**: Script-verified
- **Likely**: LLM-inferred from content
- **Hypothesis**: Needs verification

## Examples

### Full Audit
```bash
claude
> sgeo audit https://example.com
```

Output:
```
SEO Score: 72/100 (Good)
GEO Score: 54/100 (Fair)

Top SEO Issues:
1. [Critical] Missing security headers (CSP, HSTS)
2. [Warning] No author attribution on blog posts
3. [Warning] Only 2 sameAs links (need 5+ for GEO)

Top GEO Issues:
1. [Critical] No Wikipedia/Wikidata presence
2. [Critical] llms.txt missing
3. [Warning] Low citability score (45/100)
```

### SEO-Only Audit
```bash
> sgeo seo https://example.com
```

### GEO-Only Audit
```bash
> sgeo geo https://example.com
```

## Integration

### Claude CLI
Already integrated via symlink at `~/.claude/skills/sgeo`

### Codex CLI
Same symlink works for Codex CLI

### Standalone
```bash
cd seo-geo-skills
python3 scripts/generate_report.py https://example.com

# Skip auto-opening the report in browser
python3 scripts/generate_report.py https://example.com --no-open
```

## Testing

### Running Tests

The project includes a comprehensive pytest test suite covering all major functionality.

#### Install Test Dependencies

```bash
pip install -r requirements-dev.txt
```

#### Run All Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=scripts --cov-report=html

# Run specific test file
pytest tests/test_schema_validator.py

# Run specific test class
pytest tests/test_robots_checker.py::TestParseRobots

# Run specific test
pytest tests/test_readability.py::TestCountSyllables::test_single_syllable_words
```

#### Test Coverage

The test suite includes:

- **test_schema_validator.py** - JSON-LD validation, FAQPage handling, deprecated schemas, placeholder detection
- **test_robots_checker.py** - robots.txt parsing, AI crawler detection, sitemap validation, crawl-delay handling
- **test_llms_txt_checker.py** - llms.txt validation, format checking, content generation
- **test_security_headers.py** - HTTPS detection, security header validation, HSTS configuration, scoring
- **test_readability.py** - Syllable counting, Flesch scores, sentence analysis, text extraction

All tests use mocked HTTP responses (via `responses` library) to avoid external dependencies.

## Dependencies

### Required
```bash
python3 -m pip install requests beautifulsoup4 lxml
# On Windows, use: python -m pip install requests beautifulsoup4 lxml
```

### Development
```bash
python3 -m pip install -r requirements-dev.txt
```

### Optional
```bash
python3 -m pip install playwright
playwright install chromium  # For screenshots
```

## License

MIT

## Credits

Built on proven patterns from:
- Agentic-SEO-Skill (traditional SEO)
- GEO-SEO-Claude (AI search optimization)

Combined into unified MECE framework with dual scoring.
