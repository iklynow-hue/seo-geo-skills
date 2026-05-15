---
name: seo-geo-site-audit
description: Run repeatable SEO and GEO website audits for public sites. Use when the user asks for an SEO audit, GEO audit, AI visibility review, technical content-readiness review, or a site-quality audit that should crawl a representative sample of up to 50 pages, review crawlability, metadata, internal linking, structured data, trust signals, and summarize mobile/desktop performance evidence from a local Lighthouse run with scored sections, passed items, issues, and prioritized actions.
---

# SEO GEO Site Audit

Use this skill to turn a public website into a structured, evidence-based SEO + GEO audit.

## Mandatory setup questions — read this first

This skill **always** asks the user the five setup questions before crawling. Asking is not optional. It overrides any session-level "no clarifying questions" / "pick reasonable defaults" / autonomous-mode preference, including harness-level no-clarify hints. A SEO/GEO audit is long, opinionated, and expensive, so the agent must not silently pick scope, performance mode, HTML output, or output language.

The **only** time you may skip the questionnaire is when the user explicitly waives it — i.e. they either:

1. Provided all five answers (scope, output style, performance evidence, HTML report, output language) in their first message, or
2. Said something explicit like "use defaults for everything", "skip the questions, all defaults", "default everything", "全部用默认", or an equivalent literal opt-in.

A no-clarify session preference, a "be terse" preference, or a "just go" tone does **not** count as an opt-in. If you are unsure whether the user opted in, ask the questions.

If the user pushes back ("just go", "stop asking"), still confirm at minimum the output language before writing the final report, because language cannot be guessed safely.

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
- mobile + desktop performance evidence from a local Lighthouse run (Chrome managed by `chrome-launcher`)

## Skill paths

The skill is expected to live at a stable Claude Code location, typically `~/.claude/skills/seo-geo-site-audit/`. The wrapper script is `${SKILL_DIR}/scripts/audit-site`, where `${SKILL_DIR}` is whatever path the skill was installed at. When you produce chat output, use `${SKILL_DIR}/...` placeholders or the user's actual install path; do not hardcode another user's home directory.

## Search-Engine Baseline + Rendered Fetch Architecture

The skill keeps two evidence tracks for HTML pages:

- **Search-engine baseline:** raw HTTP fetch with a Googlebot Smartphone-style user agent, no JavaScript, robots-aware, and only normal `<a href>` links counted as directly crawlable.
- **Googlebot rendered simulation:** JS-rendered DOM from browser fetchers, used to inspect what Google may see after the rendering queue executes JavaScript.

If rendered evidence shows content or routes that the search-engine baseline cannot see, do **not** say "Google cannot see it" without qualification. Say "raw baseline cannot see it; rendered simulation can/cannot recover it." Treat rendered-only signals as a JavaScript dependency risk rather than an automatic hard failure. If both raw and rendered evidence are missing, treat it as a hard indexing/extractability problem.

For every page, the crawler records:

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

**Scrapling** (Camoufox mode) is always the primary fetcher — it provides full JS rendering, waits for `networkIdle`, keeps resources enabled for SPA hydration, and waits an additional 8s before extraction. This is slower than blocking resources, but more accurate for route-level head tags such as JS-injected title, description, canonical, and trading/product metadata. Timeout is 60s for heavy SPAs.

**Lightpanda** is preferred as secondary because it's significantly faster than full Playwright.

**agent-browser** is the last-resort headless browser option.

**urllib** remains the innermost fallback for raw HTTP checks, non-HTML resources (`robots.txt`, sitemaps, `llms.txt`), and when no browser is available.

### Prerequisite Detection

When the wrapper runs, it checks which optional tools are available:

- **Scrapling:** `pip install "scrapling[fetchers]"` + `scrapling install` (downloads Camoufox browser)
- **Lightpanda:** Downloads nightly binary to `~/.local/bin/lightpanda` (macOS arm64, macOS x86_64, Linux x86_64, Linux aarch64)
- **agent-browser:** `npm install -g agent-browser` + `agent-browser install` (downloads Chrome)
- **Lighthouse:** requires `node` on PATH plus `scripts/node_modules/lighthouse` (installed with `npm install` in the `scripts/` directory)

It does **not** auto-install these tools by default.

- Use `--auto-install-prereqs` if you want the wrapper to install missing prerequisites (including running `npm install` in `scripts/` to fetch Lighthouse + chrome-launcher).
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

### Performance Evidence

Performance evidence is collected from a local Lighthouse run, invoked programmatically through `scripts/run_lighthouse.mjs`:

- Uses `lighthouse` + `chrome-launcher` npm packages installed in the skill's `scripts/node_modules/`.
- Launches a headless Chrome (`--headless=new`) per run, runs Lighthouse against the URL, kills Chrome, and returns the Lighthouse `lhr` JSON.
- Each test URL is run once with mobile emulation and once with desktop emulation, so one URL produces two results.
- Mobile uses the standard Lighthouse Slow 4G + 4× CPU profile; desktop uses the broadband + 1× CPU profile and a desktop user agent.
- Output is normalized into `pagespeed.json` with `provider: "local_lighthouse"` and `source: "local_lighthouse"` on each result.

The skill no longer has a remote PageSpeed Insights API path. The only performance choices are:

- **Run local Lighthouse** (default)
- **Skip performance** (`--skip-pagespeed`)

Local runs are lab data only and do not include CrUX field metrics. The final report should say so.

## Guardrails

- Treat the crawl as a **sample**, not a full index.
- Default crawl cap is **50** pages. Maximum is **50** pages for this skill flow.
- Stay on the same origin unless the user explicitly wants cross-domain review.
- Separate **observed evidence** from **inference**.
- Never imply access to Search Console, analytics, Ahrefs, SEMrush, or server logs unless the user actually provided them.
- If Lighthouse data is unavailable because of a node/npm/Chrome failure, complete the audit anyway and clearly label performance evidence as missing or partial.
- Before running any crawl, do a short setup check when the user has not already specified scope. Do **not** silently pick crawl size or HTML output and continue.
- Never hardcode API keys, tokens, or secrets in this repo.

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

Asking the setup questions is **mandatory** unless the user has explicitly opted out (see the "Mandatory setup questions" section above). Treat any global no-clarify / autonomous / "just go" session mode as **not** an opt-out — this skill's instructions override those. If in doubt, ask.

When the user asks for an audit but has not specified the setup, ask a short confirmation before doing any crawl.

If the user already provides the setup clearly in the initial prompt, do **not** ask the same questions again. Parse the stated preferences, restate them briefly if helpful, and continue directly.

Confirm:

- target URL
- mode and crawl cap
- output style: **Boss**, **Operator**, or **Specialist**
- performance evidence: **run local Lighthouse** or **skip**
- whether they want an HTML report
- final output language

Ask these questions **one by one**, not as a single block. Wait for the user's answer to each question before asking the next one.

Use numbered choices so the user can answer with `1`, `2`, `3`, or `4`.

Treat the setup as already specified when the user clearly gives:

- target URL
- scope or crawl mode
- output style
- performance on/off
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

3. **Performance evidence**
   Ask:
   `Collect performance evidence with local Lighthouse?`
   `1. Yes, run local Lighthouse (default)`
   `2. Skip performance`

   If Lighthouse dependencies are not yet installed (`node` missing, or `scripts/node_modules/lighthouse` missing), the wrapper will warn during the prereq check. Tell the user they can rerun with `--auto-install-prereqs`, or run `npm install` once in the `scripts/` directory.

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

If the user has answered scope, output style, performance, and HTML report, but language is still missing, stop and ask the language question before you continue.

If the agent fails to ask these questions on its own, the user should explicitly say:

`Ask me the setup questions one by one with numbered options for scope, output style, performance handling, HTML report, and final output language before you begin.`

If the user wants to skip the questionnaire, they can specify preferences in one prompt, for example:

`Use $seo-geo-site-audit to audit https://example.com with light mode, Operator output, performance on, HTML report on, and final report in Chinese.`

### 2. Use the wrapper for all normal audits

Use the wrapper command for all normal audits. This is the default execution path.

Do not run the lower-level crawl and Lighthouse scripts directly during a standard audit unless you are debugging the skill itself.

Why the wrapper is required:

- it keeps the crawl, Lighthouse output, manifest, and HTML report together
- it gives one consistent execution path for chat and terminal usage

Template audit with HTML:

```bash
${SKILL_DIR}/scripts/audit-site \
  https://example.com \
  --mode template \
  --output-style operator \
  --html-report
```

If the user does not want performance evidence:

```bash
${SKILL_DIR}/scripts/audit-site \
  https://example.com \
  --mode template \
  --output-style operator \
  --skip-pagespeed
```

### 3. Handle performance evidence expectations explicitly

The wrapper always runs **local Lighthouse** when performance evidence is enabled. There is no remote PageSpeed Insights API path. The Lighthouse run is invoked through `scripts/run_lighthouse.mjs` and requires:

- `node` on PATH
- `scripts/node_modules/lighthouse` and `scripts/node_modules/chrome-launcher` installed (one-time `npm install` in `scripts/`, or `audit-site --auto-install-prereqs`)
- a working Chrome that `chrome-launcher` can start (it will download or locate one as needed)

If Lighthouse fails (no node, dependencies missing, Chrome cannot launch), the audit still completes; the wrapper records the error in `pagespeed.json` and the agent should mark performance evidence as missing.

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
- mobile / desktop Lighthouse averages and outliers when available

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

The Lighthouse run is lab-based. Explicitly say that performance evidence is lab data and does not include CrUX field data. If Lighthouse failed entirely, say performance evidence is missing and suggest the user rerun after fixing the node/npm/Chrome setup.

If HTML output is enabled:

1. Write the final written audit in chat first.
2. Start from the wrapper-generated `final-report.json` in the same output directory, or build it there if it is missing, following `references/report-payload-template.json`.
3. Render the polished HTML report by running:

```bash
${SKILL_DIR}/scripts/render-report-html \
  --report-json ${SKILL_DIR}/runs/site-audit-<host>-<stamp>/final-report.json \
  --out ${SKILL_DIR}/runs/site-audit-<host>-<stamp>/audit-report.html
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
- desktop/mobile Lighthouse conclusion
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
- enough body copy to support the page's purpose
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

- mobile and desktop Lighthouse results
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
- State which URLs were crawled and which URLs were used for Lighthouse.
- If a finding comes from a limited sample, say so.
- If rendered-browser evidence is stronger than the raw Googlebot baseline, say that clearly and treat it as a risk.
- Do not present `dom_route_hint` or `route_guess` pages as search-discoverable unless raw HTML links or sitemap evidence also expose them.
- Always label Lighthouse evidence as lab data without CrUX field metrics.

## Files In This Skill

- `scripts/fetchers.py` — unified fetcher with prereq detection, auto-install, and SPA detection
- `scripts/crawl_sample.py` — capped crawl + HTML signal extraction (uses unified fetcher)
- `scripts/pagespeed_batch.py` — local Lighthouse runner (mobile + desktop) writing the normalized JSON
- `scripts/run_lighthouse.mjs` — programmatic Lighthouse invocation through `lighthouse` + `chrome-launcher`
- `scripts/package.json` — npm dependencies for the Lighthouse runner (`lighthouse`, `chrome-launcher`)
- `scripts/audit_site.py` — one-command wrapper for crawl + Lighthouse artifacts
- `scripts/audit-site` — executable launcher for the wrapper
- `scripts/render_report_html.py` — polished final report HTML renderer from structured JSON
- `scripts/render-report-html` — executable launcher for the final report renderer
- `references/scoring-rubric.md` — scoring rules and weights
- `references/report-template.md` — output skeleton
- `references/report-payload-template.json` — structured payload template for final HTML rendering

## Wrapper Command

For a simpler CLI flow, use the wrapper script:

```bash
${SKILL_DIR}/scripts/audit-site \
  https://example.com \
  --mode template \
  --html-report
```

### CLI Flags

| Flag | Description |
|---|---|
| `--fetcher auto\|scrapling\|lightpanda\|agent_browser\|chrome\|urllib` | Preferred fetcher. Default: `auto` (tries all in priority order, including attached Chrome) |
| `--max-pagespeed-urls 1-10` | Maximum URLs to test with local Lighthouse. Default: `1` homepage URL, tested once on mobile and once on desktop. |
| `--report-language <language>` | Wrapper evidence HTML language and seeded `final-report.json` language. The final polished report HTML should come from `final-report.json` + `render-report-html` |
| `--skip-pagespeed` | Skip local Lighthouse performance collection. |
| `--skip-prereq-check` | Skip prerequisite detection |
| `--auto-install-prereqs` | Auto-install missing fetcher and Lighthouse prerequisites |
| `--html-report` | Write the wrapper evidence HTML and seed `final-report.json` |
| `--mode fast\|light\|template` | Audit depth preset (1 / 10 / 50 pages) |
| `--max-pages 1-50` | Override crawl cap |
| `--output-style boss\|operator\|specialist` | Report style recorded with artifacts |
| `--out-dir` | Custom output directory |

Full example with SPA-friendly crawl and local Lighthouse:

```bash
${SKILL_DIR}/scripts/audit-site \
  https://www.mcmarkets.com \
  --mode template \
  --output-style operator \
  --fetcher auto \
  --report-language chinese \
  --html-report
```

What it does:

- checks which optional fetcher prerequisites are available (including Lighthouse npm deps)
- can auto-install missing prerequisites only if `--auto-install-prereqs` is supplied
- records a raw Googlebot-style search-engine baseline for each HTML page
- runs the capped crawl with JS rendering via the fetcher priority chain
- escalates from headless fetchers to attached Chrome in `auto` mode when needed
- makes a best-effort route expansion pass for router-heavy SPAs when rendered content exists but crawlable links are sparse, and labels those pages as assisted discovery
- detects SPA shells and reports `spa_detection` per page
- runs homepage mobile + desktop local Lighthouse unless `--skip-pagespeed` is used
- can write `evidence-report.html` and seed `final-report.json` when `--html-report` is supplied
- can render the final polished `audit-report.html` from `final-report.json`
- stores `crawl.json`, `pagespeed.json`, `audit-run.json`, and any HTML report together in one output folder under the skill's `runs/` directory by default

## Example Requests

- `Use $seo-geo-site-audit to audit https://example.com. Ask me to confirm the crawl setup first.`
- `Run a standard SEO + GEO audit for https://example.com, use 50 pages, and generate the HTML report too.`
- `Audit this site for AI visibility and technical SEO. Ask whether I want to run local Lighthouse or skip performance before you continue. Ask the output language last.`
- `Audit this SPA site with JS rendering and local Lighthouse: https://www.mcmarkets.com`
