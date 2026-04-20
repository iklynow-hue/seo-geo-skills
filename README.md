# SEO/GEO Skills

This repo now includes a portable sampled site-audit skill for Codex and similar agents:

- `skills/seo-geo-site-audit/` — recommended skill for public-site SEO + GEO audits

The legacy SGEO toolkit still remains in the repo root, but if you want the cleaner audit flow with setup questions, optional HTML output, and capped crawl sampling, start with `seo-geo-site-audit`.

## Install

Clone the repo:

```bash
git clone https://github.com/iklynow-hue/seo-geo-skills
cd seo-geo-skills
```

Install the portable skill by placing it in your global skills folder. Example using `~/.agents/skills`:

```bash
mkdir -p ~/.agents/skills
ln -s "$PWD/skills/seo-geo-site-audit" ~/.agents/skills/seo-geo-site-audit
```

If you already have a local copy there, replace the existing folder or update the symlink target.

If you want the older SGEO root skill instead, the existing installer still works:

```bash
bash install.sh
```

## Use Cases

Use `seo-geo-site-audit` when you want:

- a sampled SEO audit for a public site
- a GEO or AI-visibility review
- a template audit that checks structure across key page types
- an operator-style report with passed items, issues, evidence, and actions
- optional PageSpeed coverage and an optional HTML artifact

## Run It

In Codex or Claude, the recommended prompts are:

```text
Use $seo-geo-site-audit to audit https://mcmarkets.com
Audit https://mcmarkets.com for SEO and GEO readiness. Ask me to confirm the setup first.
Run an Operator-mode audit for https://mcmarkets.com and ask whether I want HTML output.
```

The skill should pause first and confirm:

- crawl mode and page cap
- output style
- PageSpeed handling
- whether you want the optional HTML artifact

For terminal use, run the wrapper directly:

```bash
~/.agents/skills/seo-geo-site-audit/scripts/audit-site \
  https://mcmarkets.com \
  --mode template \
  --output-style operator \
  --prompt-pagespeed-key \
  --html-report
```

This writes the audit artifacts into one output folder under `/tmp` by default:

- `crawl.json`
- `pagespeed.json`
- `audit-run.json`
- `audit-summary.html` when `--html-report` is enabled

## PageSpeed API Key

The skill can use Google PageSpeed Insights in three ways:

1. environment variable
2. one-off terminal prompt
3. best-effort without a key

Environment variables:

- `PAGESPEED_API_KEY`
- `GOOGLE_API_KEY`

If you want a secure terminal prompt for the key, use:

```bash
~/.agents/skills/seo-geo-site-audit/scripts/audit-site \
  https://mcmarkets.com \
  --prompt-pagespeed-key
```

If no key is available, the audit can still continue, but the performance section should be treated as partial evidence if Google rate-limits or skips requests.

## How To Read The Scores

The audit produces seven weighted section scores:

| Section | Weight |
|---|---:|
| Technical SEO & Indexability | 20 |
| On-Page SEO & Content Packaging | 15 |
| Information Architecture & Internal Linking | 10 |
| GEO & AI Extractability | 20 |
| EEAT & Trust Signals | 15 |
| Entity & Structured Data | 10 |
| Performance & Page Experience | 10 |

Overall score interpretation:

| Score | Meaning |
|---|---|
| 90-100 | Excellent foundation |
| 75-89 | Good base with notable gaps |
| 60-74 | Mixed readiness |
| 40-59 | Weak foundation |
| 0-39 | Critical blockers |

Important reading notes:

- the crawl is sample-based, not a full-site crawl
- recurring sitewide issues matter more than isolated one-off issues
- confidence depends on how many pages were sampled and how complete the PageSpeed coverage was
- if PageSpeed ran without a key or partially failed, read the performance score with lower confidence

## Repo Layout

- `skills/seo-geo-site-audit/` — current portable skill
- `SKILL.md`, `scripts/`, `resources/` in the repo root — legacy SGEO toolkit

## Recommended Starting Prompt

If you want to test the installed skill in a fresh Codex session, use:

```text
Use $seo-geo-site-audit to audit https://mcmarkets.com. Ask me to confirm the crawl setup before you begin.
```
