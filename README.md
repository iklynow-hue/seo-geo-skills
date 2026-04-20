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

## How To Use It

In Codex or Claude, start with:

```text
Use $seo-geo-site-audit to audit https://mcmarkets.com
```

The skill is designed to ask you to confirm:

- crawl mode and page cap
- output style
- PageSpeed handling
- whether you want HTML output

If the agent follows the skill well, it should ask those questions before crawling.

If it does not ask, say this explicitly:

```text
Use $seo-geo-site-audit to audit https://mcmarkets.com. Ask me to confirm crawl size, output style, PageSpeed handling, and whether I want HTML output before you begin.
```

That prompt is the safest starting point in fresh sessions.

## Wrapper Command

For terminal use, run the wrapper directly:

```bash
~/.agents/skills/seo-geo-site-audit/scripts/audit-site \
  https://mcmarkets.com \
  --mode template \
  --output-style operator \
  --prompt-pagespeed-key \
  --html-report
```

Useful options:

- `--mode fast|template|full|deep`
- `--max-pages N`
- `--output-style boss|operator|specialist`
- `--prompt-pagespeed-key`
- `--api-key YOUR_KEY`
- `--skip-pagespeed`
- `--html-report`
- `--out-dir /path/to/output`

Artifacts written by the wrapper:

- `crawl.json`
- `pagespeed.json` unless skipped
- `audit-run.json`
- `audit-summary.html` when `--html-report` is enabled

## PageSpeed API Key

The skill can use Google PageSpeed Insights by:

- `PAGESPEED_API_KEY`
- `GOOGLE_API_KEY`
- a one-off terminal prompt via `--prompt-pagespeed-key`
- best-effort mode without a key

If no key is available, the audit can still continue, but the performance section may be partial if Google rate-limits requests.

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
