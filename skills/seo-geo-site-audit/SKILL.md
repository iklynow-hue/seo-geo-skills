---
name: seo-geo-site-audit
description: Run repeatable SEO and GEO website audits for public sites. Use when the user asks for an SEO audit, GEO audit, AI visibility review, technical content-readiness review, or a site-quality audit that should crawl a representative sample of up to 100 pages, review crawlability, metadata, internal linking, structured data, trust signals, and summarize desktop/mobile PageSpeed results with scored sections, passed items, issues, and prioritized actions.
---

# SEO GEO Site Audit

Use this skill to turn a public website into a structured, evidence-based SEO + GEO audit.

This skill is optimized for:

- site-level audits with a capped crawl sample
- homepage + template audits
- SEO + GEO + EEAT style reviews
- operator-ready reports with scores, passed items, issues, and actions

It intentionally combines the strongest parts of classic technical SEO audits with GEO / AI-readiness checks:

- crawlability and indexability
- on-page packaging and internal linking
- structured data and entity consistency
- answer-first / extractability patterns for AI systems
- trust and EEAT signals
- mobile + desktop PageSpeed evidence

## Guardrails

- Treat the crawl as a **sample**, not a full index.
- Default crawl cap is **25** pages. Maximum is **100** pages.
- Stay on the same origin unless the user explicitly wants cross-domain review.
- Separate **observed evidence** from **inference**.
- Never imply access to Search Console, analytics, Ahrefs, SEMrush, or server logs unless the user actually provided them.
- If PageSpeed data is unavailable because of quota or API failure, complete the audit anyway and clearly label performance evidence as partial.
- Before running any crawl, do a short setup check when the user has not already specified scope. Do **not** silently pick crawl size, PageSpeed behavior, or HTML output and continue.

## Audit Modes

Choose the lightest mode that matches the request:

- **Fast check** — `1` page
- **Template audit** — `10` to `25` pages across key templates
- **Full site audit** — `25` to `50` pages
- **Deep investigation** — `50` to `100` pages

Prefer template coverage over brute-force depth. A good audit sample usually includes:

- homepage
- pricing or commercial page
- product / solution / feature page
- docs / help / guide page
- blog / article page
- about / contact / trust / legal page

## Workflow

### 1. Run a short setup check first

When the user asks for an audit but has not specified the setup, ask a short confirmation before doing any crawl.

Confirm:

- target URL
- mode and crawl cap
- output style: **Boss**, **Operator**, or **Specialist**
- PageSpeed handling:
  existing env key, one-off prompted key, best-effort without key, or skip
- whether they want an optional HTML artifact

Recommended defaults you may suggest:

- **Template audit**
- **25** pages
- **Operator** output
- PageSpeed **best-effort** unless the user wants to provide a key
- HTML artifact **off** unless requested

Do not start the crawl until the user confirms the setup or explicitly says to use the defaults.

If the agent fails to ask these questions on its own, the user should explicitly say:

`Ask me to confirm crawl size, output style, PageSpeed handling, and whether I want HTML output before you begin.`

### 2. Prefer the wrapper for full audits

Use the wrapper command for normal audits because it keeps the crawl, PageSpeed output, manifest, and optional HTML summary together.

Template audit with optional HTML:

```bash
/Users/klyment/.agents/skills/seo-geo-site-audit/scripts/audit-site \
  https://example.com \
  --mode template \
  --output-style operator \
  --html-report
```

If the user wants a secure terminal prompt for the PageSpeed key:

```bash
/Users/klyment/.agents/skills/seo-geo-site-audit/scripts/audit-site \
  https://example.com \
  --mode template \
  --output-style operator \
  --prompt-pagespeed-key \
  --html-report
```

If the user does not want PageSpeed:

```bash
/Users/klyment/.agents/skills/seo-geo-site-audit/scripts/audit-site \
  https://example.com \
  --mode template \
  --output-style operator \
  --skip-pagespeed
```

Use the lower-level scripts directly only when you need custom orchestration or debugging.

### 3. Handle PageSpeed key expectations explicitly

The PageSpeed script uses the official PageSpeed Insights API.

- It tries `PAGESPEED_API_KEY` first, then `GOOGLE_API_KEY`.
- `--prompt-pagespeed-key` only works in an interactive terminal session.
- Chat-based skill invocation will not always surface a terminal prompt automatically.

So in chat flows:

- if the user already has an env key, continue normally
- if they want a prompted key, use the wrapper command with `--prompt-pagespeed-key`
- if they do not want to manage a key, continue best-effort and label performance evidence as partial when needed

### 4. Review the generated artifacts

The wrapper can create:

- `crawl.json`
- `pagespeed.json`
- `audit-run.json`
- `audit-summary.html` when `--html-report` is enabled

Inspect:

- sitewide signals
- template coverage
- duplicate titles / descriptions
- canonical / robots / H1 / meta coverage
- schema coverage
- breadcrumb, author, FAQ, contact, and trust hints
- whether meaningful body content is visible in initial HTML
- mobile / desktop PageSpeed averages and outliers when available

Use `references/scoring-rubric.md` for scoring rules.

### 5. Score the audit

Read `references/scoring-rubric.md` before assigning scores.

Score each section from **0 to 100**:

1. Technical SEO & Indexability
2. On-Page SEO & Content Packaging
3. Information Architecture & Internal Linking
4. GEO & AI Extractability
5. EEAT & Trust Signals
6. Entity & Structured Data
7. Performance & Page Experience

Then compute a weighted overall score.

Rules:

- Do not fake precision. Round to the nearest whole number.
- Penalize recurring sitewide failures more than isolated page issues.
- Reward consistent structural wins across templates.
- If the audit sample is small, explicitly say confidence is lower.

### 6. Write the report

Read `references/report-template.md` and follow it closely.

Every section must include:

- **score**
- **what passed**
- **issues**
- **evidence**
- **recommended actions**

Every issue should include:

- severity: **P0 / P1 / P2 / P3**
- affected URLs or template types
- why it matters
- what to fix

If the user requested HTML output, mention the generated `audit-summary.html` path in the final response in addition to the written audit.

## Output Modes

### Boss mode

Use when leadership wants the shortest useful answer.

Include:

- overall score
- 5 to 10 biggest findings
- strongest wins
- top actions by priority

### Operator mode

Default.

Include:

- scorecard
- section-by-section passed items and issues
- representative evidence
- desktop/mobile PageSpeed conclusion
- prioritized implementation roadmap

### Specialist mode

Use when the user wants maximum depth.

Include everything in Operator mode plus:

- more raw evidence
- template-level patterns
- duplicate clusters
- page examples for each major issue
- caveats and uncertainty notes

## What To Look For

### Technical SEO & Indexability

- 200 status pages
- clean canonicals
- sensible robots directives
- sitemap presence and quality
- titles and meta descriptions
- one clear H1
- render-visible HTML content
- duplicate metadata patterns
- hreflang or locale consistency when relevant

### On-Page SEO & Content Packaging

- intent-match clarity
- descriptive titles / descriptions
- usable heading structure
- enough body copy to support the page’s purpose
- helpful media and alt text
- commercial or informational clarity

### Information Architecture & Internal Linking

- navigational discoverability
- breadcrumbs
- reasonable internal-link density
- important pages reachable without deep burying
- template consistency

### GEO & AI Extractability

- answer-first summaries
- FAQ / definitions / facts / lists / tables
- structured, extractable prose
- initial HTML visibility of core facts
- `llms.txt` presence if available
- clean entity naming and context windows for retrieval

### EEAT & Trust Signals

- about / contact / support presence
- author or editorial signals on content pages
- trust / security / policy pages
- clear ownership and organization identity

### Entity & Structured Data

- Organization / WebSite / BreadcrumbList
- page-type schema where appropriate
- sameAs coverage when visible in JSON-LD
- schema consistency across templates

### Performance & Page Experience

- mobile and desktop PageSpeed results
- LCP, INP, CLS
- render-blocking resources
- image and script weight
- stability and interaction quality

## Reporting Rules

- Ask the setup questions before crawling when scope is incomplete.
- Start with the scorecard.
- Call out **passed items** as well as failures.
- Prefer patterns over one-off nitpicks.
- Keep unsupported assumptions out of the report.
- State which URLs were crawled and which URLs were used for PageSpeed.
- If a finding comes from a limited sample, say so.

## Files In This Skill

- `scripts/crawl_sample.py` — capped crawl + HTML signal extraction
- `scripts/pagespeed_batch.py` — mobile / desktop PageSpeed collection
- `scripts/audit_site.py` — one-command wrapper for crawl + PageSpeed artifacts
- `scripts/audit-site` — executable launcher for the wrapper
- `references/scoring-rubric.md` — scoring rules and weights
- `references/report-template.md` — output skeleton

## Wrapper Command

For a simpler CLI flow, use the wrapper script:

```bash
/Users/klyment/.agents/skills/seo-geo-site-audit/scripts/audit-site \
  https://example.com \
  --mode template \
  --prompt-pagespeed-key \
  --html-report
```

What it does:

- runs the capped crawl
- runs representative mobile + desktop PageSpeed unless `--skip-pagespeed` is used
- prompts for the Google PageSpeed Insights API key when `--prompt-pagespeed-key` is supplied
- can write `audit-summary.html` when `--html-report` is supplied
- stores `crawl.json`, `pagespeed.json`, `audit-run.json`, and any optional HTML artifact together in one output folder under `/tmp` by default

## Example Requests

- `Use $seo-geo-site-audit to audit https://example.com. Ask me to confirm the crawl setup first.`
- `Run a full SEO + GEO audit for https://example.com, use 50 pages, and generate an HTML artifact too.`
- `Audit this site for AI visibility and technical SEO. Ask whether I want PageSpeed with a key before you continue.`
