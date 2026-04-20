---
name: seo-geo-site-audit
description: Run repeatable SEO and GEO website audits for public sites. Use when the user asks for an SEO audit, GEO audit, AI visibility review, technical content-readiness review, or a site-quality audit that should crawl a representative sample of up to 25 pages, review crawlability, metadata, internal linking, structured data, trust signals, and summarize desktop/mobile PageSpeed results with scored sections, passed items, issues, and prioritized actions.
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
- Default crawl cap is **25** pages. Maximum is **25** pages for this skill flow.
- Stay on the same origin unless the user explicitly wants cross-domain review.
- Separate **observed evidence** from **inference**.
- Never imply access to Search Console, analytics, Ahrefs, SEMrush, or server logs unless the user actually provided them.
- If PageSpeed data is unavailable because of quota or API failure, complete the audit anyway and clearly label performance evidence as partial.
- Before running any crawl, do a short setup check when the user has not already specified scope. Do **not** silently pick crawl size, PageSpeed behavior, or HTML output and continue.

## Audit Modes

Choose the lightest mode that matches the request:

- **Fast check** — `1` page
- **Light template audit** — `10` pages
- **Standard template audit** — `25` pages
- **Custom sample** — user-chosen page cap up to `25`

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

Ask these questions **one by one**, not as a single block. Wait for the user's answer to each question before asking the next one.

Use numbered choices so the user can answer with `1`, `2`, `3`, or `4`.

Recommended setup sequence:

1. **Scope**
   Ask:
   `Choose the audit scope:`
   `1. Fast check (1 page)`
   `2. Light template audit (10 pages)`
   `3. Standard template audit (25 pages, recommended and maximum)`
   `4. Custom page cap up to 25`

   If the user chooses `4`, ask one follow-up before continuing:
   `Reply with a crawl cap from 1 to 25.`

2. **Output style**
   Ask:
   `Choose the output style:`
   `1. Operator (recommended)`
   `2. Boss`
   `3. Specialist`

3. **PageSpeed**
   Ask:
   `Choose PageSpeed handling:`
   `1. Best-effort without key (recommended)`
   `2. Skip PageSpeed`
   `3. I will paste the API key in chat`

   If the user chooses `3`, ask one follow-up before continuing:
   `Reply with your API key in the next message.`

4. **HTML report**
   Ask:
   `Do you want the optional HTML report?`
   `1. Off (recommended)`
   `2. On`

Recommended defaults you may suggest:

- **Template audit**
- **25** pages
- **Operator** output
- PageSpeed **best-effort** unless the user wants to paste a key in chat
- HTML report **off** unless requested

Do not start the crawl until the user confirms the setup or explicitly says to use the defaults.

If the agent fails to ask these questions on its own, the user should explicitly say:

`Ask me the setup questions one by one with numbered options for scope, output style, PageSpeed handling, and HTML report before you begin.`

### 2. Use the wrapper for all normal audits

Use the wrapper command for all normal audits. This is the default execution path.

Do not run the lower-level crawl and PageSpeed scripts directly during a standard audit unless you are debugging the skill itself.

Why the wrapper is required:

- it keeps the crawl, PageSpeed output, manifest, and optional HTML report together
- it gives one consistent execution path for Codex, Claude, and terminal usage

Template audit with optional HTML:

```bash
/Users/klyment/.agents/skills/seo-geo-site-audit/scripts/audit-site \
  https://example.com \
  --mode template \
  --output-style operator \
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

If the user pastes an API key in chat, still use the wrapper and pass that key to it with `--api-key`.

### 3. Handle PageSpeed key expectations explicitly

The PageSpeed script uses the official PageSpeed Insights API.

- It tries `PAGESPEED_API_KEY` first, then `GOOGLE_API_KEY`.

So in chat flows:

- if the user already has an env key, continue normally through the wrapper
- if they paste a key in chat, still execute through the wrapper with `--api-key`
- if they do not want to manage a key, continue best-effort or skip and label performance evidence accordingly
- if the user pasted a key in chat, warn them after the audit that they may want to rotate or replace that key because it was shared in conversation text

### 4. Review the generated artifacts

The wrapper can create:

- `crawl.json`
- `pagespeed.json`
- `audit-run.json`
- `audit-report.html` when `--html-report` is enabled

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

If the user requested HTML output, mention the generated `audit-report.html` path in the final response in addition to the written audit.

If the audit used best-effort PageSpeed and PageSpeed results were partial or failed, explicitly say that in the final result and tell the user they can rerun the audit with an API key for more reliable performance evidence.

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
- Ask them one by one with numbered options.
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
  --html-report
```

What it does:

- runs the capped crawl
- runs representative mobile + desktop PageSpeed unless `--skip-pagespeed` is used
- can write `audit-report.html` when `--html-report` is supplied
- stores `crawl.json`, `pagespeed.json`, `audit-run.json`, and any optional HTML report together in one output folder under `/tmp` by default

## Example Requests

- `Use $seo-geo-site-audit to audit https://example.com. Ask me to confirm the crawl setup first.`
- `Run a standard SEO + GEO audit for https://example.com, use 25 pages, and generate the HTML report too.`
- `Audit this site for AI visibility and technical SEO. Ask whether I want best-effort PageSpeed, skip, or paste a key in chat before you continue.`
