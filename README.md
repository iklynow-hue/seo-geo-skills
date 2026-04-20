# SEO GEO Site Audit Skill

This repo is now focused on one skill only:

- `skills/seo-geo-site-audit/`

Use it for sampled SEO + GEO audits of public sites, with optional PageSpeed coverage and an optional HTML audit artifact.

## Install

Clone the repo:

```bash
git clone https://github.com/iklynow-hue/seo-geo-skills
cd seo-geo-skills
```

Link the skill into your global skills folder:

```bash
mkdir -p ~/.agents/skills
ln -s "$PWD/skills/seo-geo-site-audit" ~/.agents/skills/seo-geo-site-audit
```

If you already have an older local copy, replace it or update the symlink target.

## When To Use It

Use `seo-geo-site-audit` when you want:

- a sampled site audit instead of a full crawl
- SEO + GEO analysis in one pass
- a template-based review across key page types
- a scored audit with passed items, issues, evidence, and actions
- optional PageSpeed data
- optional HTML output for the artifact bundle
- optional SPA-friendly rendering through installed browser fetchers

## How To Use It

In Codex or Claude, start with:

```text
Use $seo-geo-site-audit to audit https://mcmarkets.com
```

The skill is designed to ask you to confirm:

- crawl mode and page cap
- output style
- PageSpeed handling
- whether you want the HTML report

If the agent follows the skill well, it should ask those questions **one by one** before crawling, with numbered choices.

Expected flow:

1. Scope
   `1. Fast check (1 page)`
   `2. Light template audit (10 pages)`
   `3. Standard template audit (25 pages, recommended and maximum)`
   `4. Custom page cap up to 25`

2. Output style
   `1. Operator (recommended)`
   `2. Boss`
   `3. Specialist`

3. PageSpeed
   `1. Best-effort without key (recommended)`
   `2. Skip PageSpeed`
   `3. I will paste the API key in chat`

   If you choose `3`, the agent should ask you to paste the key in the next message.
   After the audit, it should also remind you that you may want to rotate or replace that key because it was shared in chat.

4. HTML report
   `1. Off (recommended)`
   `2. On`

If it does not ask, say this explicitly:

```text
Use $seo-geo-site-audit to audit https://mcmarkets.com. Ask me the setup questions one by one with numbered options for scope, output style, PageSpeed handling, and HTML report before you begin.
```

That prompt is the safest starting point in fresh sessions.

## Wrapper Command

The wrapper is the required execution path for normal audits.

Even when you use the skill from chat, the agent should ultimately run the wrapper rather than stitching together the lower-level scripts manually.

For terminal use, run the wrapper directly:

```bash
~/.agents/skills/seo-geo-site-audit/scripts/audit-site \
  https://mcmarkets.com \
  --mode template \
  --output-style operator \
  --html-report
```

Useful options:

- `--mode fast|light|template`
- `--max-pages 1-25`
- `--output-style boss|operator|specialist`
- `--api-key YOUR_KEY`
- `--skip-pagespeed`
- `--html-report`
- `--fetcher auto|scrapling|lightpanda|agent_browser|urllib`
- `--local-lighthouse-fallback`
- `--auto-install-prereqs`
- `--skip-prereq-check`
- `--out-dir /path/to/output`

Artifacts written by the wrapper:

- `crawl.json`
- `pagespeed.json` unless skipped
- `audit-run.json`
- `audit-report.html` when `--html-report` is enabled

## PageSpeed API Key

The skill can use Google PageSpeed Insights by:

- `PAGESPEED_API_KEY`
- `GOOGLE_API_KEY`
- pasting a key in chat so the wrapper can run with `--api-key`
- best-effort mode without a key

If no key is available, the audit can still continue, but the performance section may be partial if Google rate-limits requests.

If best-effort PageSpeed fails or comes back partial, the final result should say so clearly and tell you that rerunning with an API key will give more reliable performance evidence.

## SPA Support Notes

The crawl can use a fetcher priority chain:

- `scrapling`
- `lightpanda`
- `agent-browser`
- `urllib`

By default the wrapper only checks which of those are available. It does **not** auto-install them unless you pass:

```bash
--auto-install-prereqs
```

If you want local Lighthouse fallback when the PageSpeed API fails, use:

```bash
--local-lighthouse-fallback
```

That fallback preserves the requested mobile or desktop strategy and prefers Lightpanda CDP when available.

## How To Read The Scores

The audit uses seven weighted sections:

| Section | Weight |
|---|---:|
| Technical SEO & Indexability | 20 |
| On-Page SEO & Content Packaging | 15 |
| Information Architecture & Internal Linking | 10 |
| GEO & AI Extractability | 20 |
| EEAT & Trust Signals | 15 |
| Entity & Structured Data | 10 |
| Performance & Page Experience | 10 |

Interpretation:

| Score | Meaning |
|---|---|
| 90-100 | Excellent foundation |
| 75-89 | Good base with notable gaps |
| 60-74 | Mixed readiness |
| 40-59 | Weak foundation |
| 0-39 | Critical blockers |

Read the results with these guardrails:

- it is a sample, not a full-site crawl
- repeated sitewide issues matter more than isolated one-offs
- lower crawl coverage means lower confidence
- incomplete PageSpeed coverage means lower confidence in the performance section
