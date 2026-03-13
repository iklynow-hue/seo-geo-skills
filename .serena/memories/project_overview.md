# Project Overview

## Purpose
SGEO (Unified SEO + GEO Master Audit) is a Claude CLI skill that performs comprehensive website audits combining traditional SEO analysis with GEO (Generative Engine Optimization) for AI search visibility.

## Key Features
- Dual scoring system: Independent SEO Score (traditional search) and GEO Score (AI search visibility)
- MECE framework (Mutually Exclusive, Collectively Exhaustive) for audit categorization
- 19+ Python scripts for deterministic verification
- Cross-platform support (macOS, Linux, Windows)
- Generates markdown reports and HTML dashboards

## Tech Stack
- **Language**: Python 3.8+
- **Core Dependencies**: requests, beautifulsoup4, lxml
- **Optional**: playwright (for screenshots)
- **Integration**: Claude CLI skill system via symlink at ~/.claude/skills/sgeo

## Project Type
Claude CLI agent skill with Python-based audit scripts
