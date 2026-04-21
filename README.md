# SEO GEO Skills

Public skill repo for:

- `skills/seo-geo-site-audit/`

This skill works with both Codex and Claude Code for sampled SEO + GEO audits of public sites, with:

- capped crawling up to 25 pages
- template-aware sampling
- local Lighthouse by default
- optional PageSpeed API support
- optional bilingual HTML reporting

## Install

Clone the repo:

```bash
git clone https://github.com/iklynow-hue/seo-geo-skills
cd seo-geo-skills
```

Link the skill into your local skills folder:

```bash
mkdir -p ~/.agents/skills
ln -s "$PWD/skills/seo-geo-site-audit" ~/.agents/skills/seo-geo-site-audit
```

For Claude Code, the skill also includes a local [CLAUDE.md](skills/seo-geo-site-audit/CLAUDE.md) entry file.

## Use Cases

Use `seo-geo-site-audit` when you want:

- an SEO audit
- a GEO / AI visibility audit
- a sampled site-quality review instead of a full crawl
- a scored report with evidence, issues, and recommended actions
- optional HTML output for sharing

## Chat Usage

Start with:

```text
Use $seo-geo-site-audit to audit https://example.com
```

The skill is designed to ask setup questions one by one before crawling:

1. Scope
2. Output style
3. Performance evidence mode
4. HTML report on/off
5. HTML report language, only if HTML output is enabled

Current performance choices:

- `1. Local Lighthouse (recommended)`
- `2. Skip PageSpeed`
- `3. Use existing PageSpeed API key from env`
- `4. I will paste the API key in chat`

If HTML output is enabled, the follow-up language choices are:

- `1. English`
- `2. Chinese`
- `3. Other (type it in)`

## Terminal Usage

Use the wrapper for normal runs:

```bash
~/.agents/skills/seo-geo-site-audit/scripts/audit-site \
  https://example.com \
  --mode template \
  --output-style operator
```

Useful options:

- `--mode fast|light|template`
- `--max-pages 1-25`
- `--output-style boss|operator|specialist`
- `--pagespeed-provider local|api|api_with_fallback`
- `--api-key YOUR_KEY`
- `--skip-pagespeed`
- `--html-report`
- `--report-language english|chinese`
- `--fetcher auto|scrapling|lightpanda|agent_browser|urllib`
- `--auto-install-prereqs`
- `--skip-prereq-check`
- `--out-dir /path/to/output`

Artifacts:

- `crawl.json`
- `pagespeed.json` unless skipped
- `audit-run.json`
- `audit-report.html` when HTML output is enabled

## Security

This repo is intended to be safe for public cloning.

- No API keys should ever be hardcoded in source, docs, or artifacts.
- PageSpeed keys should only come from:
  - `PAGESPEED_API_KEY`
  - `GOOGLE_API_KEY`
  - a one-off key provided by the user in the current chat/session
- The code should only persist `api_key_used: true/false`, never the key itself.

See:

- [skills/seo-geo-site-audit/SECURITY.md](skills/seo-geo-site-audit/SECURITY.md)

## Contribution Policy

Cloning and forking are welcome.

Please do not open pull requests for this repository. The maintainer is not reviewing PRs right now.

If you need to report a bug or suggest an improvement, open an issue instead.
