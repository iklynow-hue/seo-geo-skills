# Code Style and Conventions

## Python Style
- **Version**: Python 3.8+ required
- **Imports**: Standard library first, then third-party (requests, beautifulsoup4, lxml)
- **Script structure**: Standalone scripts with main() function pattern
- **Error handling**: Use try/except for network operations and file I/O
- **Output format**: JSON output via --json flag for script integration

## Naming Conventions
- **Scripts**: snake_case (e.g., `citability_scorer.py`, `robots_checker.py`)
- **Functions**: snake_case (e.g., `run_script`, `calculate_category_scores`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `SCRIPT_DIR`, `MECE_WEIGHTS`)
- **Variables**: snake_case

## File Organization
```
seo-geo-skills/
├── SKILL.md                    # Main skill definition
├── MECE-FRAMEWORK.md           # Framework documentation
├── install.sh / install.ps1    # Installation scripts
├── uninstall.sh / uninstall.ps1
├── scripts/                    # 19+ audit scripts
└── resources/references/       # Reference documentation
```

## Documentation
- Markdown for all documentation files
- README.md contains user-facing documentation
- SKILL.md contains Claude CLI skill orchestration logic
- Reference docs in resources/references/ for framework details

## Output Files
- `SGEO-AUDIT-REPORT.md` — Detailed findings
- `SGEO-ACTION-PLAN.md` — Prioritized fixes
- `SGEO-REPORT.html` — Interactive dashboard
- All outputs go to current directory or outputs/ folder
