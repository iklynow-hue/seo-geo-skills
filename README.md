# SGEO — Unified SEO + GEO Master Audit

Combined SEO and GEO analysis with MECE (Mutually Exclusive, Collectively Exhaustive) framework.
Produces dual scores: **SEO Score** (traditional search) and **GEO Score** (AI search visibility).

## Quick Start

```bash
# Install
cd ~/projects/seo-geo-master-check
bash install.sh

# Run audit
claude
> sgeo audit https://photorefix.com
```

## Features

- **Dual Scoring**: Independent SEO and GEO scores from single audit
- **MECE Framework**: No overlap, complete coverage across 10 categories
- **Script-Backed**: 19+ Python scripts for deterministic verification
- **Portable**: Works on macOS and Linux, integrates with Claude CLI and Codex CLI
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

### Install
```bash
cd ~/projects/seo-geo-master-check
bash install.sh
```

This will:
1. Install Python dependencies
2. Create symlink at `~/.claude/skills/sgeo`
3. Verify installation

### Uninstall
```bash
bash uninstall.sh
```

## Project Structure

```
seo-geo-master-check/
├── SKILL.md                    # Main skill definition
├── MECE-FRAMEWORK.md           # Framework documentation
├── install.sh                  # Installation script
├── uninstall.sh                # Uninstallation script
├── scripts/                    # 19+ audit scripts
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
│   ├── validate_schema.py
│   ├── citability_scorer.py
│   ├── brand_scanner.py
│   ├── llmstxt_generator.py
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
3. **SGEO-REPORT.html** — Interactive dashboard with dual scores (if scripts run)

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
> sgeo audit https://photorefix.com
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
cd ~/projects/seo-geo-master-check
python3 scripts/generate_report.py https://example.com
```

## Dependencies

### Required
```bash
pip install requests beautifulsoup4 lxml
```

### Optional
```bash
pip install playwright
playwright install chromium  # For screenshots
```

## License

MIT

## Credits

Built on proven patterns from:
- Agentic-SEO-Skill (traditional SEO)
- GEO-SEO-Claude (AI search optimization)

Combined into unified MECE framework with dual scoring.
