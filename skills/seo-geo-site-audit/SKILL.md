---
name: seo-geo-site-audit
description: Use when the user asks for an SEO audit, GEO audit, AI visibility review, technical content-readiness review, site-quality review, crawlability check, or asks Claude to audit, score, or grade a public website — even if they don't say the word "skill". The skill crawls a representative sample of up to 50 pages, compares raw Googlebot-style HTML against rendered DOM, reviews crawlability, metadata, internal linking, structured data, trust signals, and runs local Lighthouse for mobile/desktop performance evidence, then produces a scored HTML report.
---

# SEO GEO Site Audit

Turn a public website into a structured, evidence-based SEO + GEO audit.

## How to invoke

Just give the skill the target URL. It runs immediately with defaults. Override inline if needed.

| Default | Value |
|---|---|
| Mode | Light template audit (10 pages) |
| Output style | Operator |
| Performance | Local Lighthouse on the homepage (mobile + desktop) |
| HTML report | On |
| Output language | English |

Defaults match the common case. Don't ask the user 5 questions. Run the wrapper and write the report.

## Inline overrides

The agent parses these from the user's prompt and passes the matching flags to the wrapper:

| Phrasing | Override |
|---|---|
| `fast`, `quick check`, `1 page`, `homepage only` | `--mode fast` (1 page) |
| `template`, `standard`, `full`, `50 pages` | `--mode template` (50 pages) |
| `N pages` (1–50) | `--max-pages N` |
| `boss style`, `executive summary` | `--output-style boss` |
| `specialist`, `detailed`, `deep` | `--output-style specialist` |
| `skip performance`, `skip lighthouse`, `no pagespeed` | `--skip-pagespeed` |
| `no html`, `json only`, `skip html` | drop `--html-report` |
| `in Chinese`, `中文`, `用中文` | `--report-language chinese` |
| `in <language>`, `report in <language>` | `--report-language <language>` |

If the user inlines all preferences in the first message, parse and run. If the user gave only a URL, run with defaults silently.

## When to actually ask

Three narrow cases. Otherwise, never ask:

1. **No URL.** "Audit my site" without a URL — ask for the URL.
2. **Language explicitly mentioned but ambiguous** — e.g. user typed in Spanish but didn't say "in Spanish for the report". Ask once: "Final report in English or Spanish?"
3. **Wrapper prerequisites missing.** If `--auto-install-prereqs` would download Lightpanda nightly or Camoufox, mention the install + ask permission once before running. Default to `--skip-prereq-check` and the urllib fallback if the user says no.

A vague session-level "be quick" or "no clarifying questions" is the **same** signal as "use defaults" — just run.

## Default language stays English

If the user typed the request in Chinese, the report still defaults to **English** unless the user explicitly asks for a non-English report. Don't auto-translate based on prompt language.

Switch only on:
- `2` selected after a deliberate language question (case 2 above),
- a phrase like "in Chinese", "中文", "Spanish report", "report in German",
- the `--report-language` CLI flag.

## Architecture (read on demand)

Two evidence tracks per HTML page — a raw Googlebot-style HTTP baseline and a JS-rendered DOM — then comparison. Rendered fetching falls through Scrapling → Lightpanda → agent-browser → urllib. SPA recovery layer (Scrapling retry, scroll+wait, DOM route hints), domain-aware route guesser, sitemap-first fallback. Performance evidence comes from local Lighthouse via `scripts/run_lighthouse.mjs`.

Full rules — fetcher priority, recovery triggers, SPA detection thresholds, route guess templates, Lighthouse invocation — live in [`references/architecture.md`](references/architecture.md).

Two principles to keep in working memory:

- **Raw vs rendered.** If a signal appears only after JS, call it a JavaScript-dependency risk, not "Google cannot see it." If both raw and rendered are missing, it is a true missing signal.
- **Assisted discovery.** Pages reached only through `dom_route_hint` or `route_guess` are not search-discoverable. Don't present them as crawlable unless a raw `<a href>` or sitemap also exposes them.

## Guardrails

- Treat the crawl as a **sample**, not a full index.
- Default crawl cap is **10** pages (light mode). Maximum is **50**.
- Stay on the same origin unless the user explicitly wants cross-domain review.
- Separate **observed evidence** from **inference**.
- Never imply access to Search Console, analytics, Ahrefs, SEMrush, or server logs unless the user actually provided them.
- If Lighthouse data is unavailable because of a node/npm/Chrome failure, complete the audit anyway and clearly label performance evidence as missing or partial.
- Never hardcode API keys, tokens, or secrets in this repo.

## Skill paths

The skill typically lives at `~/.claude/skills/seo-geo-site-audit/`. The wrapper script is `${SKILL_DIR}/scripts/audit-site`. Use `${SKILL_DIR}/...` or the user's actual install path; don't hardcode another user's home directory.

## Workflow

1. **Parse the prompt.** Extract the target URL and any inline overrides (see the override table above). If no URL, ask for it. Otherwise proceed silently — do not list defaults back at the user before running.

2. **Run the wrapper with `--html-report` by default.** Append any flags from the override parse.

   ```bash
   ${SKILL_DIR}/scripts/audit-site \
     <URL> \
     --mode light \
     --output-style operator \
     --html-report
   ```

   Add `--skip-pagespeed`, `--report-language chinese`, etc. as overrides dictate.

3. **Inspect the artifacts.** The wrapper writes `crawl.json`, `pagespeed.json`, `audit-run.json`, `evidence-report.html`, and seeds `final-report.json`. Read the crawl summary, page list, security headers, and the Lighthouse aggregate. Look for:
   - sitewide signals (`coverage_rates`, duplicate titles, security headers, schema coverage)
   - SPA flags + raw-vs-rendered deltas
   - pages reached only through `dom_route_hint` / `route_guess`
   - mobile vs desktop Lighthouse averages

4. **Score the audit.** Read [`references/scoring-rubric.md`](references/scoring-rubric.md). Score each of the seven sections 0–100, then weight:
   1. Technical SEO & Indexability
   2. On-Page SEO & Content Packaging
   3. Information Architecture & Internal Linking
   4. GEO & AI Extractability
   5. EEAT & Trust Signals
   6. Entity & Structured Data
   7. Performance & Page Experience

   Round to whole numbers. Penalize recurring sitewide failures more than isolated page issues. If the sample is small, say confidence is lower.

5. **Write the report.** Follow [`references/report-template.md`](references/report-template.md). Every section needs score, what passed, issues, recommended actions. Every issue needs severity (P0/P1/P2/P3), why it matters, what to fix — embed supporting numbers directly in the issue detail prose. Always label Lighthouse evidence as lab data without CrUX field metrics.

6. **Render the HTML.** Fill `final-report.json`, then run:

   ```bash
   ${SKILL_DIR}/scripts/render-report-html \
     --report-json ${SKILL_DIR}/runs/site-audit-<host>-<stamp>/final-report.json \
     --out ${SKILL_DIR}/runs/site-audit-<host>-<stamp>/audit-report.html
   ```

   Mention the `audit-report.html` path in the final response alongside the chat audit.

## Output modes (read on demand)

Boss (shortest) / Operator (default) / Specialist (deepest). Content rules in [`references/output-modes.md`](references/output-modes.md).

## What to look for (read on demand)

Per-section signal lists in [`references/audit-checklist.md`](references/audit-checklist.md). Read when scoring a specific section.

## Reporting rules

- Start with the scorecard.
- Call out **passed items** as well as failures.
- Prefer patterns over one-off nitpicks.
- Keep unsupported assumptions out of the report.
- State which URLs were crawled and which were used for Lighthouse.
- If a finding comes from a limited sample, say so.
- If rendered-browser evidence is stronger than the raw baseline, say so and treat it as a risk.
- Don't present `dom_route_hint` or `route_guess` pages as search-discoverable without raw HTML or sitemap evidence.
- Always label Lighthouse evidence as lab data without CrUX field metrics.

## Files in this skill

- `scripts/fetchers.py` — unified fetcher with prereq detection, auto-install, SPA detection
- `scripts/crawl_sample.py` — capped crawl + HTML signal extraction
- `scripts/pagespeed_batch.py` — local Lighthouse runner writing the normalized JSON
- `scripts/run_lighthouse.mjs` — programmatic Lighthouse via `lighthouse` + `chrome-launcher`
- `scripts/audit_site.py` — wrapper that orchestrates crawl + Lighthouse + artifacts
- `scripts/audit-site` — executable launcher for the wrapper
- `scripts/render_report_html.py` — polished final-report HTML renderer
- `scripts/render-report-html` — executable launcher for the renderer
- `scripts/language_packs.py` — centralized EN/ZH UI strings
- `scripts/_report_styles.py` — shared CSS palette tokens
- `scripts/package.json` — Lighthouse npm dependencies
- `tests/` — pytest/unittest suite for crawl + parse helpers
- `references/setup-gate.md` — defaults + override phrasings reference
- `references/cli-flags.md` — wrapper flag reference + security notes
- `references/example-requests.md` — example chat invocations
- `references/scoring-rubric.md` — scoring rules and weights
- `references/report-template.md` — output skeleton
- `references/report-payload-template.json` — structured payload template
- `references/architecture.md` — crawl + fetch + Lighthouse internals
- `references/audit-checklist.md` — per-section signal lists
- `references/output-modes.md` — Boss / Operator / Specialist content rules

## Common rationalizations to avoid

| Excuse | Reality |
|---|---|
| "User only gave a URL, I should ask 5 questions first" | Defaults exist for that. Just run. |
| "Their session is autonomous, I should skip even the URL check" | The URL is a hard requirement. Ask if missing. |
| "User typed in Chinese, the report should be Chinese too" | English by default. Switch only on explicit phrasing. |
| "I should restate the defaults to confirm" | The user can read the report; no need to narrate defaults. |
| "Performance check on just the homepage isn't enough" | Homepage is the highest-traffic page on most sites — it's a fair single check. Use `--max-pagespeed-urls N` if the user asks for more. |
