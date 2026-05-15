# SEO GEO Site Audit for Claude Code

Use this skill when the user wants an SEO audit, GEO audit, AI visibility review, or a structured site-quality audit for a public website.

This skill targets Claude Code. It is invoked as `$seo-geo-site-audit` and runs from wherever the skill is installed (typically `~/.claude/skills/seo-geo-site-audit/` or this repo, symlinked into that location). Refer to the wrapper script as `${SKILL_DIR}/scripts/audit-site`; do not hardcode absolute user paths into chat replies.

Default operating rules:

- Ask the setup questions one by one before crawling if scope is incomplete.
- If the user already specifies scope, output style, HTML preference, and final output language clearly, do not re-ask them. Continue with those stated preferences.
- If the user only specifies some preferences, ask only for the missing items.
- Treat language confirmation as mandatory. Do not consider setup complete until the user confirms the final output language or explicitly accepts the default English.
- Use the wrapper script for normal audits: `${SKILL_DIR}/scripts/audit-site`.
- Performance evidence is always **local Lighthouse** (Chrome managed by `chrome-launcher`, invoked through `scripts/run_lighthouse.mjs`). There is no remote API path. The only performance choice is on / skip.
- Ask the output language as a required question before writing the report. If it was not captured during setup, ask it as the final question after crawl/evidence review:
  `1. English (default)`
  `2. Chinese`
  `3. Other (type it in)`
- If HTML output is enabled, use the wrapper-generated `final-report.json` seed (or create it if missing), then render the final `audit-report.html` from it so the HTML matches the written report.

Security rules:

- Never hardcode API keys, tokens, or secrets in this repo.
- The skill does not require any third-party API key. Do not ask the user for one.
- Do not include credentials or private data in error messages, logs, manifests, or saved JSON/HTML outputs.

Workflow summary:

- Crawl a capped representative sample up to 50 pages.
- For every HTML page, compare the raw Googlebot-style baseline against rendered browser evidence.
- If rendered content, rendered links, DOM route hints, or route guesses expose pages that the raw baseline does not, report that as a crawlability/indexability risk.
- For router-heavy SPAs or local apps, use best-effort browser discovery for audit sampling, but do not describe DOM hints or guessed routes as search-discoverable.
- The crawler has an SPA recovery layer: if the initial fetch returns a thin shell, it retries with Scrapling (longer timeout), scroll+wait+re-extract via agent-browser, and DOM route hint extraction (catches data-href, onclick routes, Next.js/Nuxt router data).
- Domain-specific route templates are tried when BFS + sitemap produce too few pages (crypto, saas, ecommerce, fintech, media).
- Sitemap-first fallback kicks in when fewer than 10 pages are discovered.
- Review technical SEO, on-page packaging, IA/internal linking, GEO extractability, EEAT/trust, structured data, and performance evidence.
- Produce Operator mode by default unless the user asks for Boss or Specialist.
- Treat all findings as sample-based evidence, not a complete site index.
