---
name: seo-geo-site-audit
description: Run repeatable SEO and GEO website audits for public sites. Use when the user asks for an SEO audit, GEO audit, AI visibility review, technical content-readiness review, or a site-quality audit that should crawl a representative sample of up to 50 pages, review crawlability, metadata, internal linking, structured data, trust signals, and summarize mobile/desktop performance evidence from local Lighthouse or PageSpeed API results with scored sections, passed items, issues, and prioritized actions.
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
- mobile + desktop performance evidence from local Lighthouse or PageSpeed API

## Multi-Layer Fetch Architecture

The skill supports JS-rendered crawling through a fetcher priority chain:

```
Scrapling (StealthyFetcher/Camoufox, JS-rendered) — primary
  → Lightpanda (headless CDP browser, fast) — secondary
    → agent-browser (Playwright-based) — tertiary
      → urllib.request (raw HTTP, no JS) — fallback
```

**Why:** SPA sites (e.g., React, Angular, Vue) serve a thin JS shell in initial HTML. Raw HTTP requests see no content, no internal links, and produce shallow single-page audits. JS rendering fixes this.

**Scrapling** (Camoufox mode) is always the primary fetcher — it provides full JS rendering, waits for `networkIdle`, and is the most reliable for content extraction.

**Lightpanda** is preferred as secondary because it's significantly faster than full Playwright.

**agent-browser** is the last-resort headless browser option.

**urllib** remains the innermost fallback for non-HTML resources (robots.txt, sitemaps) and when no browser is available.

### Prerequisite Detection

When the wrapper runs, it checks which optional SPA fetchers are available:

- **Scrapling:** `pip install "scrapling[fetchers]"` + `scrapling install` (downloads Camoufox browser)
- **Lightpanda:** Downloads nightly binary to `~/.local/bin/lightpanda` (macOS arm64, macOS x86_64, Linux x86_64, Linux aarch64)
- **agent-browser:** `npm install -g agent-browser` + `agent-browser install` (downloads Chrome)

It does **not** auto-install these tools by default.

- Use `--auto-install-prereqs` if you want the wrapper to install missing prerequisites.
- Use `--skip-prereq-check` to skip the detection step entirely.

### SPA Detection

After fetching each page, the crawler runs `detect_spa_shell()` which checks:

- `word_count < 100` AND `script_count >= 5` → likely SPA shell
- `word_count < 50` AND `script_count >= 3` → thin HTML
- Results are stored in `spa_detection` field per page and aggregated in the crawl summary

### Performance Evidence Modes

The skill supports three performance evidence modes:

- **Local Lighthouse** — default and recommended for normal audits
- **PageSpeed API** — optional when you want CrUX / real-user field data
- **PageSpeed API with local Lighthouse fallback** — try API first, then recover locally on failure

When using **Lighthouse locally**, the skill:

1. Starts Lightpanda CDP on port 19222 when Lightpanda is available
2. Otherwise runs Lighthouse through its normal local browser path
3. Preserves the requested `mobile` or `desktop` strategy
4. Parses the Lighthouse JSON into the same schema as API results
5. Tags results with `"source": "local_lighthouse"` (vs `"source": "api"`)

Use `--pagespeed-provider local` for local-only runs, `--pagespeed-provider api` for API-only runs, or `--pagespeed-provider api_with_fallback` to try API first and recover locally. Requires `lighthouse` CLI or `npx` available for local runs.

PageSpeed API improvements:
- Timeout increased from 20s to 45s
- Retries increased from 2 to 3 with exponential backoff (2s, 4s, 8s)

## Guardrails

- Treat the crawl as a **sample**, not a full index.
- Default crawl cap is **50** pages. Maximum is **50** pages for this skill flow.
- Stay on the same origin unless the user explicitly wants cross-domain review.
- Separate **observed evidence** from **inference**.
- Never imply access to Search Console, analytics, Ahrefs, SEMrush, or server logs unless the user actually provided them.
- If PageSpeed data is unavailable because of quota or API failure, complete the audit anyway and clearly label performance evidence as partial.
- Before running any crawl, do a short setup check when the user has not already specified scope. Do **not** silently pick crawl size, PageSpeed behavior, or HTML output and continue.
- Never hardcode API keys, tokens, or secrets in this repo.
- Never store a PageSpeed API key in tracked files, generated artifacts, manifests, or HTML output.
- Only accept a PageSpeed API key from the skill `.env` file or environment variables.

## Audit Modes

Choose the lightest mode that matches the request:

- **Fast check** — `1` page
- **Light template audit** — `10` pages
- **Standard template audit** — `50` pages
- **Custom sample** — user-chosen page cap up to `50`

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
- performance evidence mode:
  local Lighthouse, PageSpeed API from the skill `.env`, or skip
- whether they want an HTML report
- if HTML output is on, the report language

Ask these questions **one by one**, not as a single block. Wait for the user's answer to each question before asking the next one.

Use numbered choices so the user can answer with `1`, `2`, `3`, or `4`.

Default setup sequence:

1. **Scope**
   Ask:
   `Choose the audit scope:`
   `1. Fast check (1 page)`
   `2. Light template audit (10 pages, default)`
   `3. Standard template audit (50 pages)`
   `4. Custom page cap up to 50`

   If the user chooses `4`, ask one follow-up before continuing:
   `Reply with a crawl cap from 1 to 50.`

2. **Output style**
   Ask:
   `Choose the output style:`
   `1. Operator (default)`
   `2. Boss`
   `3. Specialist`

3. **PageSpeed**
   Ask:
   `Choose PageSpeed handling:`
   `1. Local Lighthouse (default)`
   `2. Skip PageSpeed`
   `3. Use PageSpeed API from the skill .env`

   If the user chooses `3`, ask one follow-up before continuing:
   `Save your key to /Users/klyment/.agents/skills/seo-geo-site-audit/.env as PAGESPEED_API_KEY=your_key and tell me when it is ready.`

4. **HTML report**
   Ask:
   `Do you want the HTML report?`
   `1. Off (default)`
   `2. On`

   If the user chooses `2`, ask one follow-up before continuing:
   `Choose the HTML report language:`
   `1. English (default)`
   `2. Chinese`
   `3. Other (type it in)`

   If the user chooses `3`, ask one more follow-up before continuing:
   `Reply with the output language in the next message.`

Default values you may use if the user asks for defaults:

- **Light template audit**
- **10** pages
- **Operator** output
- performance evidence via **local Lighthouse**
- HTML report **off**
- if HTML is on, report language **English**

Do not start the crawl until the user confirms the setup or explicitly says to use the defaults.

If the agent fails to ask these questions on its own, the user should explicitly say:

`Ask me the setup questions one by one with numbered options for scope, output style, PageSpeed handling, and HTML report before you begin.`

### 2. Use the wrapper for all normal audits

Use the wrapper command for all normal audits. This is the default execution path.

Do not run the lower-level crawl and PageSpeed scripts directly during a standard audit unless you are debugging the skill itself.

Why the wrapper is required:

- it keeps the crawl, PageSpeed output, manifest, and HTML report together
- it gives one consistent execution path for Codex, Claude, and terminal usage

Template audit with HTML:

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

If the user wants PageSpeed API mode, have them save the key in `/Users/klyment/.agents/skills/seo-geo-site-audit/.env` first and then continue through the wrapper.

### 3. Handle performance evidence expectations explicitly

The wrapper defaults to **local Lighthouse** for performance evidence.

If the user explicitly chooses PageSpeed API, the PageSpeed script uses the official PageSpeed Insights API.

- It tries `/Users/klyment/.agents/skills/seo-geo-site-audit/.env` first.
- Inside that file, it looks for `PAGESPEED_API_KEY` first, then `GOOGLE_API_KEY`.
- After that, it falls back to exported shell environment variables with the same names.

So in chat flows:

- if the user chooses local Lighthouse, continue normally through the wrapper without requiring an API key
- if the user chooses API mode, ask them to save the key in the skill `.env`, then execute through the wrapper with `--pagespeed-provider api`
- if they want API evidence but also want resilience, use `--pagespeed-provider api_with_fallback`
- if they do not want to manage a key, continue with local Lighthouse or skip and label performance evidence accordingly
- never write the raw key into repo files, JSON artifacts, HTML output, or error messages

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

Keep the final written audit in the selected output language.

When HTML output is enabled, also pass the selected language to the wrapper with `--report-language`.

Built-in static HTML localization currently supports **English** and **Chinese** directly.

If the audit used local Lighthouse, explicitly say the performance evidence is lab-based and does not include CrUX field data.

If the audit used API mode and PageSpeed results were partial or failed, explicitly say that in the final result and tell the user they can rerun with `--pagespeed-provider api_with_fallback` or switch to local Lighthouse.

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

- `scripts/fetchers.py` — unified fetcher with prereq detection, auto-install, and SPA detection
- `scripts/crawl_sample.py` — capped crawl + HTML signal extraction (uses unified fetcher)
- `scripts/pagespeed_batch.py` — mobile / desktop PageSpeed collection + local Lighthouse fallback
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

### New CLI Flags

| Flag | Description |
|---|---|
| `--fetcher auto\|scrapling\|lightpanda\|agent_browser\|urllib` | Preferred fetcher. Default: `auto` (tries all in priority order) |
| `--pagespeed-provider local\|api\|api_with_fallback` | Performance evidence source. Default: `local` |
| `--report-language <language>` | HTML report language. Built-in localization supports English and Chinese |
| `--local-lighthouse-fallback` | Compatibility alias for `--pagespeed-provider api_with_fallback` |
| `--skip-prereq-check` | Skip prerequisite detection |
| `--auto-install-prereqs` | Auto-install missing fetcher prerequisites |

Full example with SPA-friendly crawl and local Lighthouse as the default performance source:

```bash
/Users/klyment/.agents/skills/seo-geo-site-audit/scripts/audit-site \
  https://www.mcmarkets.com \
  --mode template \
  --output-style operator \
  --fetcher auto \
  --report-language chinese \
  --html-report
```

Example with API first and local Lighthouse fallback:

```bash
/Users/klyment/.agents/skills/seo-geo-site-audit/scripts/audit-site \
  https://www.mcmarkets.com \
  --mode template \
  --output-style operator \
  --fetcher auto \
  --pagespeed-provider api_with_fallback \
  --html-report
```

What it does:

- checks which optional fetcher prerequisites are available
- can auto-install missing prerequisites only if `--auto-install-prereqs` is supplied
- runs the capped crawl with JS rendering via the fetcher priority chain
- detects SPA shells and reports `spa_detection` per page
- runs representative mobile + desktop performance checks unless `--skip-pagespeed` is used
- uses local Lighthouse by default, or API / API-with-fallback when explicitly selected
- can write `audit-report.html` when `--html-report` is supplied
- can localize the static HTML artifact in English or Chinese via `--report-language`
- stores `crawl.json`, `pagespeed.json`, `audit-run.json`, and any HTML report together in one output folder under `/tmp` by default

## Example Requests

- `Use $seo-geo-site-audit to audit https://example.com. Ask me to confirm the crawl setup first.`
- `Run a standard SEO + GEO audit for https://example.com, use 50 pages, and generate the HTML report too.`
- `Audit this site for AI visibility and technical SEO. Ask whether I want local Lighthouse, skip, use an env API key, or paste a key in chat before you continue.`
- `Audit this SPA site with JS rendering and local Lighthouse: https://www.mcmarkets.com`
