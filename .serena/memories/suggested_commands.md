# Suggested Commands

## Installation
```bash
# macOS / Linux
bash install.sh

# Windows (PowerShell)
powershell -ExecutionPolicy Bypass -File install.ps1
```

## Uninstallation
```bash
# macOS / Linux
bash uninstall.sh

# Windows (PowerShell)
powershell -ExecutionPolicy Bypass -File uninstall.ps1
```

## Usage (via Claude CLI)
```bash
claude
> sgeo audit https://example.com        # Full dual-score audit
> sgeo seo https://example.com          # SEO-only audit
> sgeo geo https://example.com          # GEO-only audit
> sgeo page https://example.com         # Single page analysis
> sgeo schema https://example.com       # Schema validation
> sgeo content https://example.com      # Content quality check
> sgeo brand https://example.com        # Brand authority scan
```

## Standalone Script Execution
```bash
# Generate HTML report directly
python3 scripts/generate_report.py https://example.com

# Skip auto-opening browser
python3 scripts/generate_report.py https://example.com --no-open

# Run individual audit scripts
python3 scripts/fetch_page.py <url> --output /tmp/page.html
python3 scripts/robots_checker.py <url>
python3 scripts/citability_scorer.py <url> --json
python3 scripts/schema_validator.py /tmp/page.html --json
```

## Development
```bash
# Install dependencies manually
python3 -m pip install requests beautifulsoup4 lxml

# Make scripts executable
chmod +x scripts/*.py

# Check Python version
python3 --version  # Must be 3.8+
```

## System Commands (macOS/Darwin)
- Shell: zsh (default on macOS)
- Standard Unix commands: ls, cd, grep, find, cat, etc.
