# Crawl + Fetch Architecture

Read this when you need to explain the dual-track evidence, the rendered fetcher chain, SPA recovery, or how the wrapper collects performance evidence. The information here is **reference detail**; SKILL.md keeps only the high-level rules.

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

## Prerequisite Detection

When the wrapper runs, it checks which optional tools are available:

- **Scrapling:** `pip install "scrapling[fetchers]"` + `scrapling install` (downloads Camoufox browser)
- **Lightpanda:** Downloads nightly binary to `~/.local/bin/lightpanda` (macOS arm64, macOS x86_64, Linux x86_64, Linux aarch64)
- **agent-browser:** `npm install -g agent-browser` + `agent-browser install` (downloads Chrome)
- **Lighthouse:** requires `node` on PATH plus `scripts/node_modules/lighthouse` (installed with `npm install` in the `scripts/` directory)

It does **not** auto-install these tools by default.

- Use `--auto-install-prereqs` if you want the wrapper to install missing prerequisites (including running `npm install` in `scripts/` to fetch Lighthouse + chrome-launcher).
- Use `--skip-prereq-check` to skip the detection step entirely.

## SPA Detection

For each page, the crawler runs `detect_spa_shell()` against the raw search-engine baseline, not just the rendered browser output. It checks:

- `word_count < 100` AND `script_count >= 5` → likely SPA shell
- `word_count < 50` AND `script_count >= 3` → thin HTML
- Results are stored in `spa_detection` field per page and aggregated in the crawl summary

## SPA Recovery Layer

When the initial fetch returns a thin SPA shell (word_count < 100, script_count >= 5), `fetch_with_spa_recovery()` attempts:

1. **Scrapling retry** — re-fetch with longer timeout if the first fetcher wasn't Scrapling
2. **Scroll + wait + re-extract** — agent-browser scrolls to bottom, waits 5s for lazy content, then re-grabs HTML
3. **DOM route hint extraction** — runs JS in the browser to find possible SPA routes, but labels them as hints rather than crawlable proof:
   - `data-href`, `data-to`, `data-url`, `data-link` attributes
   - `onclick` handlers with router navigation
   - Next.js `__NEXT_DATA__` route data
   - Nuxt.js `__NUXT__` route data

DOM route hints can be used for audit sampling, but they are not counted as direct search-engine crawlability. If a page is reached only through a DOM route hint, call that out as assisted discovery.

## Search Discoverability Rules

For report conclusions, distinguish these link sources:

- `raw_a_href` — directly visible in raw HTML and safest to count as crawlable.
- `rendered_a_href` — visible after JavaScript rendering; useful evidence, but more fragile than raw HTML links.
- `dom_route_hint` — inferred from `data-*`, onclick handlers, or framework state; use only as audit assistance, not as proof that search engines can crawl the route.
- `route_guess` — guessed paths such as `/about` or `/pricing`; useful for sampling, but always report them as assisted discovery.

If a page is reached only through `dom_route_hint` or `route_guess`, mark it as not search-discoverable in the sample unless a sitemap or crawlable anchor also exposes it.

## Domain-Specific Route Guessing

When BFS + sitemap produce too few pages, the crawler tries domain-specific route templates. Site type is auto-detected from homepage content:

- **crypto**: /markets, /futures, /staking, /launchpad, /swap, /earn, etc. (~30 paths)
- **saas**: /product, /features, /pricing, /api, /changelog, etc.
- **ecommerce**: /shop, /products, /categories, /cart, /deals, etc.
- **fintech**: /accounts, /invest, /stocks, /loans, /calculator, etc.
- **media**: /articles, /news, /podcasts, /topics, /subscribe, etc.

## Sitemap-First Fallback

When BFS + route guessing produce fewer than 10 pages, the crawler aggressively tries remaining sitemap URLs that weren't visited yet. This prevents shallow audits on SPA sites where link discovery is weak, while still preserving each page's discovery source in `crawl.json`.

## Performance Evidence

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
