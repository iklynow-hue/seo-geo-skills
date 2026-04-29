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

## Search-Engine Baseline + Rendered Fetch Architecture

The skill keeps two evidence tracks for HTML pages:

- **Search-engine baseline:** raw HTTP fetch with a Googlebot Smartphone-style user agent, no JavaScript, robots-aware, and only normal `<a href>` links counted as directly crawlable.
- **Googlebot rendered simulation:** JS-rendered DOM from browser fetchers, used to inspect what Google may see after the rendering queue executes JavaScript.

If rendered evidence shows content or routes that the search-engine baseline cannot see, do **not** say "Google cannot see it" without qualification. Say "raw baseline cannot see it; rendered simulation can/cannot recover it." Treat rendered-only signals as a JavaScript dependency risk rather than an automatic hard failure. If both raw and rendered evidence are missing, treat it as a hard indexing/extractability problem.

For every page, the crawler now records:

- `raw_title`, `raw_meta_description`, `raw_canonical`, `raw_h1_count`, `raw_json_ld_types`
- `rendered_title`, `rendered_meta_description`, `rendered_canonical`, `rendered_h1_count`, `rendered_json_ld_types`
- `rendered_signal_delta`, comparing raw vs rendered status for title, description, canonical, H1, body words, internal links, and JSON-LD
- `googlebot_rendering`, with `raw_baseline`, `rendered_dom`, and the comparison delta

Report wording should distinguish:

- `missing_*` — missing after both raw and rendered inspection
- `*_requires_js_rendering` — absent in raw HTML but present after rendering
- `content_requires_js_rendering` — meaningful content is rendered-only
- `navigation_requires_js_rendering` — crawlable links are rendered-only or inferred from route hints

Rendered fetching uses this priority chain:

```
Scrapling (StealthyFetcher/Camoufox, JS-rendered) — primary
  → Lightpanda (headless CDP browser, fast) — secondary
    → agent-browser (Playwright-based) — tertiary
      → urllib.request (raw HTTP, no JS) — fallback
```

**Why:** SPA sites (e.g., React, Angular, Vue) often serve a thin JS shell in initial HTML. Raw HTTP requests may see no meaningful content or crawlable links. JS rendering helps inspect the site, but the report must still say when content depends on rendering or assisted discovery.

**Scrapling** (Camoufox mode) is always the primary fetcher — it provides full JS rendering, waits for `networkIdle`, keeps resources enabled for SPA hydration, and waits an additional 8s before extraction. This is slower than blocking resources, but it is more accurate for route-level head tags such as JS-injected title, description, canonical, and trading/product metadata. Timeout is 60s for heavy SPAs.

**Lightpanda** is preferred as secondary because it's significantly faster than full Playwright.

**agent-browser** is the last-resort headless browser option.

**urllib** remains the innermost fallback for raw HTTP checks, non-HTML resources (`robots.txt`, sitemaps, `llms.txt`), and when no browser is available.

### Prerequisite Detection

When the wrapper runs, it checks which optional SPA fetchers are available:

- **Scrapling:** `pip install "scrapling[fetchers]"` + `scrapling install` (downloads Camoufox browser)
- **Lightpanda:** Downloads nightly binary to `~/.local/bin/lightpanda` (macOS arm64, macOS x86_64, Linux x86_64, Linux aarch64)
- **agent-browser:** `npm install -g agent-browser` + `agent-browser install` (downloads Chrome)

It does **not** auto-install these tools by default.

- Use `--auto-install-prereqs` if you want the wrapper to install missing prerequisites.
- Use `--skip-prereq-check` to skip the detection step entirely.

### SPA Detection

For each page, the crawler runs `detect_spa_shell()` against the raw search-engine baseline, not just the rendered browser output. It checks:

- `word_count < 100` AND `script_count >= 5` → likely SPA shell
- `word_count < 50` AND `script_count >= 3` → thin HTML
- Results are stored in `spa_detection` field per page and aggregated in the crawl summary

### SPA Recovery Layer

When the initial fetch returns a thin SPA shell (word_count < 100, script_count >= 5), `fetch_with_spa_recovery()` attempts:

1. **Scrapling retry** — re-fetch with longer timeout if the first fetcher wasn't Scrapling
2. **Scroll + wait + re-extract** — agent-browser scrolls to bottom, waits 5s for lazy content, then re-grabs HTML
3. **DOM route hint extraction** — runs JS in the browser to find possible SPA routes, but labels them as hints rather than crawlable proof:
   - `data-href`, `data-to`, `data-url`, `data-link` attributes
   - `onclick` handlers with router navigation
   - Next.js `__NEXT_DATA__` route data
   - Nuxt.js `__NUXT__` route data

DOM route hints can be used for audit sampling, but they are not counted as direct search-engine crawlability. If a page is reached only through a DOM route hint, call that out as assisted discovery.

### Search Discoverability Rules

For report conclusions, distinguish these link sources:

- `raw_a_href` — directly visible in raw HTML and safest to count as crawlable.
- `rendered_a_href` — visible after JavaScript rendering; useful evidence, but more fragile than raw HTML links.
- `dom_route_hint` — inferred from `data-*`, onclick handlers, or framework state; use only as audit assistance, not as proof that search engines can crawl the route.
- `route_guess` — guessed paths such as `/about` or `/pricing`; useful for sampling, but always report them as assisted discovery.

If a page is reached only through `dom_route_hint` or `route_guess`, mark it as not search-discoverable in the sample unless a sitemap or crawlable anchor also exposes it.

### Domain-Specific Route Guessing

When BFS + sitemap produce too few pages, the crawler tries domain-specific route templates. Site type is auto-detected from homepage content:

- **crypto**: /markets, /futures, /staking, /launchpad, /swap, /earn, etc. (~30 paths)
- **saas**: /product, /features, /pricing, /api, /changelog, etc.
- **ecommerce**: /shop, /products, /categories, /cart, /deals, etc.
- **fintech**: /accounts, /invest, /stocks, /loans, /calculator, etc.
- **media**: /articles, /news, /podcasts, /topics, /subscribe, etc.

### Sitemap-First Fallback

When BFS + route guessing produce fewer than 10 pages, the crawler aggressively tries remaining sitemap URLs that weren't visited yet. This prevents shallow audits on SPA sites where link discovery is weak, while still preserving each page's discovery source in `crawl.json`.

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
- Default URL coverage is homepage-only: one URL tested with both mobile and desktop strategies. Use `--max-pagespeed-urls` only when you explicitly need extra template performance coverage.

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

If the user already provides the setup clearly in the initial prompt, do **not** ask the same questions again. Parse the stated preferences, restate them briefly if helpful, and continue directly.

Confirm:

- target URL
- mode and crawl cap
- output style: **Boss**, **Operator**, or **Specialist**
- performance evidence mode:
  local Lighthouse, PageSpeed API from the skill `.env`, or skip
- whether they want an HTML report
- final output language

Ask these questions **one by one**, not as a single block. Wait for the user's answer to each question before asking the next one.

Use numbered choices so the user can answer with `1`, `2`, `3`, or `4`.

Treat the setup as already specified when the user clearly gives:

- target URL
- scope or crawl mode
- output style
- PageSpeed handling
- HTML report on/off
- final output language

If all of those are present, skip the setup questionnaire and run the audit.

If only some are present, ask **only** for the missing items. Do not re-ask preferences the user already stated clearly.

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

5. **Final output language**
   Ask:
   `Choose the final output language:`
   `1. English (default)`
   `2. Chinese`
   `3. Other (type it in)`

   If the user chooses `3`, ask one more follow-up before continuing:
   `Reply with the output language in the next message.`

Language confirmation is **mandatory**. Do not treat the setup as complete until the user confirms the final report language or explicitly says to use the default English.

Default values you may use if the user asks for defaults:

- **Light template audit**
- **10** pages
- **Operator** output
- performance evidence via **local Lighthouse**
- HTML report **off**
- final output language **English**

Do not start the crawl until the user confirms the setup or explicitly says to use the defaults.

If the user has answered scope, output style, PageSpeed handling, and HTML report, but language is still missing, stop and ask the language question before you continue.

If the agent fails to ask these questions on its own, the user should explicitly say:

`Ask me the setup questions one by one with numbered options for scope, output style, PageSpeed handling, HTML report, and final output language before you begin.`

If the user wants to skip the questionnaire, they can specify preferences in one prompt, for example:

`Use $seo-geo-site-audit to audit https://example.com with light mode, Operator output, PageSpeed API from the skill .env, HTML report on, and final report in Chinese.`

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
- `evidence-report.html` when `--html-report` is enabled
- `final-report.json` as a seeded structured payload when `--html-report` is enabled

Inspect:

- sitewide signals
- template coverage
- duplicate titles / descriptions
- canonical / robots / H1 / meta coverage
- schema coverage
- breadcrumb, author, FAQ, contact, and trust hints
- whether meaningful body content is visible in initial HTML
- search-engine baseline vs Googlebot rendered simulation deltas
- `summary.raw_coverage_rates`, `summary.rendered_coverage_rates`, `summary.rendered_only_signal_counts`, and `summary.missing_after_rendering_signal_counts`
- pages discovered only through rendered links, DOM route hints, or route guesses
- mobile / desktop PageSpeed averages and outliers when available

Use `references/scoring-rubric.md` for scoring rules.

### 5. Keep the output language explicit

The output language must always be explicitly confirmed with the user.

If you already captured it during setup, keep using that confirmed language.

If an earlier run reached evidence review without a language answer, ask the language question immediately before writing the report and do not silently default to English.

Ask:
`Choose the final output language:`
`1. English (default)`
`2. Chinese`
`3. Other (type it in)`

If the user chooses `3`, ask one more follow-up:
`Reply with the output language in the next message.`

This language controls:

- the written audit in chat
- the structured final report payload
- the final HTML report if HTML output is on

For **English** and **Chinese**, the HTML renderer has built-in chrome labels.

For any **other language**, keep the written report in that language and also populate `ui_text` in the final report payload so the HTML chrome matches the same language instead of falling back to English.

### 6. Score the audit

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
- In the final report scorecard, treat each section score as a **0-100** score.
- Display section **weight as a percentage** such as `20%`, not a bare number like `20`.
- If possible, show each section's **contribution to total score** as `score × weight%`.

### 7. Write the report

Read `references/report-template.md` and follow it closely.
If HTML output is on, also read `references/report-payload-template.json`.

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

Keep the final written audit in the selected output language.

For the final scorecard presentation:

- make it obvious that section scores are each out of **100**
- show weights as percentages
- prefer a scorecard structure like:
  section / section score / weight (%) / contribution to total / notes
- avoid wording that makes section scores look like they should add up to 100 on their own

If the audit used local Lighthouse, explicitly say the performance evidence is lab-based and does not include CrUX field data.

If the audit used API mode and PageSpeed results were partial or failed, explicitly say that in the final result and tell the user they can rerun with `--pagespeed-provider api_with_fallback` or switch to local Lighthouse.

If HTML output is enabled:

1. Write the final written audit in chat first.
2. Start from the wrapper-generated `final-report.json` in the same output directory, or build it there if it is missing, following `references/report-payload-template.json`.
3. Render the polished HTML report by running:

```bash
/Users/klyment/.agents/skills/seo-geo-site-audit/scripts/render-report-html \
  --report-json /Users/klyment/.agents/skills/seo-geo-site-audit/runs/site-audit-<host>-<stamp>/final-report.json \
  --out /Users/klyment/.agents/skills/seo-geo-site-audit/runs/site-audit-<host>-<stamp>/audit-report.html
```

4. Mention the generated `audit-report.html` path in the final response in addition to the written audit.

The final HTML report should match the written audit in substance, not just the crawl evidence page.

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
- meaningful raw HTML content visible to Googlebot baseline
- rendered content that materially exceeds raw HTML should be flagged as JS-dependent, but not described as invisible to Google unless rendered evidence is also missing
- raw-vs-rendered deltas for title, description, canonical, H1, body copy, links, and schema
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
- raw `<a href>` internal links as the strongest discovery evidence
- rendered `<a href>` links as secondary evidence
- DOM route hints and guessed routes as assisted discovery only
- breadcrumbs
- reasonable internal-link density
- important pages reachable without deep burying
- template consistency

### GEO & AI Extractability

- answer-first summaries
- FAQ / definitions / facts / lists / tables
- structured, extractable prose
- raw HTML visibility of core facts
- clear warning when AI-readable facts only appear after JavaScript rendering
- clear separation between Google rendering support and AI crawler/GEO extractability, because many AI crawlers and retrieval systems still prefer or require non-JS HTML
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
- If rendered-browser evidence is stronger than the raw Googlebot baseline, say that clearly and treat it as a risk.
- Do not present `dom_route_hint` or `route_guess` pages as search-discoverable unless raw HTML links or sitemap evidence also expose them.

## Files In This Skill

- `scripts/fetchers.py` — unified fetcher with prereq detection, auto-install, and SPA detection
- `scripts/crawl_sample.py` — capped crawl + HTML signal extraction (uses unified fetcher)
- `scripts/pagespeed_batch.py` — mobile / desktop PageSpeed collection + local Lighthouse fallback
- `scripts/audit_site.py` — one-command wrapper for crawl + PageSpeed artifacts
- `scripts/audit-site` — executable launcher for the wrapper
- `scripts/render_report_html.py` — polished final report HTML renderer from structured JSON
- `scripts/render-report-html` — executable launcher for the final report renderer
- `references/scoring-rubric.md` — scoring rules and weights
- `references/report-template.md` — output skeleton
- `references/report-payload-template.json` — structured payload template for final HTML rendering

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
| `--fetcher auto\|scrapling\|lightpanda\|agent_browser\|chrome\|urllib` | Preferred fetcher. Default: `auto` (tries all in priority order, including attached Chrome) |
| `--pagespeed-provider local\|api\|api_with_fallback` | Performance evidence source. Default: `local` |
| `--max-pagespeed-urls 1-10` | Maximum PageSpeed URLs. Default: `1` homepage URL, tested once on mobile and once on desktop. |
| `--report-language <language>` | Wrapper evidence HTML language and seeded `final-report.json` language. The final polished report HTML should come from `final-report.json` + `render-report-html` |
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
- records a raw Googlebot-style search-engine baseline for each HTML page
- runs the capped crawl with JS rendering via the fetcher priority chain
- escalates from headless fetchers to attached Chrome in `auto` mode when needed
- makes a best-effort route expansion pass for router-heavy SPAs when rendered content exists but crawlable links are sparse, and labels those pages as assisted discovery
- detects SPA shells and reports `spa_detection` per page
- runs homepage mobile + desktop performance checks unless `--skip-pagespeed` is used
- uses local Lighthouse by default, or API / API-with-fallback when explicitly selected
- can write `evidence-report.html` and seed `final-report.json` when `--html-report` is supplied
- can render the final polished `audit-report.html` from `final-report.json`
- stores `crawl.json`, `pagespeed.json`, `audit-run.json`, and any HTML report together in one output folder under the skill's `runs/` directory by default

## Example Requests

- `Use $seo-geo-site-audit to audit https://example.com. Ask me to confirm the crawl setup first.`
- `Run a standard SEO + GEO audit for https://example.com, use 50 pages, and generate the HTML report too.`
- `Audit this site for AI visibility and technical SEO. Ask whether I want local Lighthouse, skip, or use the skill .env for PageSpeed API before you continue. Ask the output language last.`
- `Audit this SPA site with JS rendering and local Lighthouse: https://www.mcmarkets.com`
