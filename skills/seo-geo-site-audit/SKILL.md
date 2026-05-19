---
name: seo-geo-site-audit
description: Run repeatable SEO and GEO website audits for public sites. Use this skill whenever the user asks for an SEO audit, GEO audit, AI visibility review, technical content-readiness review, site-quality review, crawlability check, or asks Claude to audit, score, or grade a public website — even if they don't say the word "skill". The skill crawls a representative sample of up to 50 pages, compares raw Googlebot-style HTML against rendered DOM, reviews crawlability, metadata, internal linking, structured data, trust signals, and runs local Lighthouse for mobile/desktop performance evidence, then produces a scored report with passed items, P0-P3 issues, evidence, and prioritized actions.
---

# SEO GEO Site Audit

Turn a public website into a structured, evidence-based SEO + GEO audit.

## Mandatory setup gate

The audit **always** asks five setup questions before crawling. The gate overrides session-level no-clarify / autonomous / "just go" preferences — this skill's instructions take precedence. See [`references/setup-gate.md`](references/setup-gate.md) for the rationale, the literal questions, and the waiver rules.

Two facts to keep in working memory without opening the reference:

- **Default output language is English.** Do not infer a non-English language from the prompt's language, the target domain's TLD, or session locale. Switch only on explicit selection (option `2` at the language question, `--report-language`, or wording like "in Chinese" / "用中文").
- **Only two waiver forms count:** (1) the user supplied all five answers in the first message, or (2) the user said something literal like "use defaults for everything". Tone like "just go" or "be terse" is not a waiver.

## Architecture (read on demand)

Two evidence tracks per HTML page — a raw Googlebot-style HTTP baseline and a JS-rendered DOM — then comparison. Rendered fetching falls through Scrapling → Lightpanda → agent-browser → urllib. SPA recovery layer (Scrapling retry, scroll+wait, DOM route hints), domain-aware route guesser, and sitemap-first fallback when BFS produces too few pages. Performance evidence comes from local Lighthouse via `scripts/run_lighthouse.mjs`.

Full rules — fetcher priority logic, recovery triggers, SPA detection thresholds, route guess templates, Lighthouse invocation — live in [`references/architecture.md`](references/architecture.md).

Two principles to remember without opening the reference:

- **Raw vs rendered:** if a signal appears only after JS, call it a JavaScript dependency risk, not "Google cannot see it." If both raw and rendered are missing, it is a true missing signal.
- **Assisted discovery:** pages reached only through `dom_route_hint` or `route_guess` are not search-discoverable. Don't present them as crawlable unless a raw `<a href>` or sitemap also exposes them.

## Guardrails

- Treat the crawl as a **sample**, not a full index.
- Default crawl cap is **50** pages. Maximum is **50** pages for this skill flow.
- Stay on the same origin unless the user explicitly wants cross-domain review.
- Separate **observed evidence** from **inference**.
- Never imply access to Search Console, analytics, Ahrefs, SEMrush, or server logs unless the user actually provided them.
- If Lighthouse data is unavailable because of a node/npm/Chrome failure, complete the audit anyway and clearly label performance evidence as missing or partial.
- Never hardcode API keys, tokens, or secrets in this repo.

## Audit modes

- **Fast check** — 1 page
- **Light template audit** — 10 pages
- **Standard template audit** — 50 pages
- **Custom sample** — user-chosen cap up to 50

Prefer template coverage over brute-force depth. A good sample usually includes homepage, pricing, product/feature, docs/help, blog/article, and about/contact/trust.

## Skill paths

The skill typically lives at `~/.claude/skills/seo-geo-site-audit/`. The wrapper script is `${SKILL_DIR}/scripts/audit-site`. Use `${SKILL_DIR}/...` placeholders or the user's actual install path; don't hardcode another user's home directory.

## Workflow

1. **Run the setup gate first.** Ask the five questions one by one (numbered choices), waiting for each answer. See [`references/setup-gate.md`](references/setup-gate.md). If the user already supplied an answer in the original prompt, skip that single question — do not re-ask preferences they already stated. If all five are present, skip the questionnaire and run the audit.

2. **Use the wrapper for all normal audits.**

   ```bash
   ${SKILL_DIR}/scripts/audit-site \
     https://example.com \
     --mode template \
     --output-style operator \
     --html-report
   ```

   To skip performance: add `--skip-pagespeed`. Full flag list in [`references/cli-flags.md`](references/cli-flags.md).

   Don't run lower-level crawl or Lighthouse scripts directly during a standard audit unless debugging the skill itself.

3. **Handle performance evidence expectations.** The wrapper always runs **local Lighthouse** when performance is enabled — there is no remote PageSpeed Insights API path. Requires `node` on PATH, `scripts/node_modules/lighthouse` + `scripts/node_modules/chrome-launcher` (one-time `npm install` in `scripts/`, or `audit-site --auto-install-prereqs`), and a working Chrome that `chrome-launcher` can start. If Lighthouse fails, the audit still completes; the wrapper records the error in `pagespeed.json` and the agent should mark performance evidence as missing.

4. **Review the generated artifacts.** The wrapper can create `crawl.json`, `pagespeed.json`, `audit-run.json`, and optionally `evidence-report.html` + `final-report.json` (with `--html-report`). Inspect:
   - sitewide signals, template coverage, duplicate titles/descriptions
   - canonical / robots / H1 / meta coverage
   - schema coverage and breadcrumb/author/FAQ/contact/trust hints
   - whether meaningful body content is visible in initial HTML
   - search-engine baseline vs rendered DOM deltas (`summary.raw_coverage_rates`, `summary.rendered_coverage_rates`, `summary.rendered_only_signal_counts`, `summary.missing_after_rendering_signal_counts`)
   - pages discovered only through rendered links, DOM route hints, or route guesses
   - mobile / desktop Lighthouse averages and outliers when available

5. **Keep the output language explicit.** Use the language confirmed during setup. If an earlier run reached evidence review without a language answer, re-ask the language question immediately before writing the report — never silently default to English. The language controls the chat audit, the structured final report payload, and the final HTML report. For non-English languages other than Chinese, also populate `ui_text` in the final report payload so the HTML chrome matches.

6. **Score the audit.** Read [`references/scoring-rubric.md`](references/scoring-rubric.md) before scoring. Score each of the seven sections from 0-100 then compute a weighted overall score:
   1. Technical SEO & Indexability
   2. On-Page SEO & Content Packaging
   3. Information Architecture & Internal Linking
   4. GEO & AI Extractability
   5. EEAT & Trust Signals
   6. Entity & Structured Data
   7. Performance & Page Experience

   Round to whole numbers. Penalize recurring sitewide failures more than isolated page issues. Reward consistent structural wins. If the sample is small, say confidence is lower. Display section weights as percentages (`20%`, not `20`) and prefer a scorecard structure like `section / score / weight (%) / contribution / notes`.

7. **Write the report.** Follow [`references/report-template.md`](references/report-template.md); if HTML is on, also follow `references/report-payload-template.json`. Every section needs score, what passed, issues, evidence, recommended actions. Every issue needs severity (P0/P1/P2/P3), affected URLs/templates, why it matters, what to fix. Keep the written report in the selected output language. Always label Lighthouse evidence as lab data without CrUX field metrics.

   If HTML output is enabled, write the chat audit first, then render the polished HTML:

   ```bash
   ${SKILL_DIR}/scripts/render-report-html \
     --report-json ${SKILL_DIR}/runs/site-audit-<host>-<stamp>/final-report.json \
     --out ${SKILL_DIR}/runs/site-audit-<host>-<stamp>/audit-report.html
   ```

   Mention the generated `audit-report.html` path in the final response in addition to the written audit.

## Output modes (read on demand)

Three depth modes — Boss (shortest), Operator (default), Specialist (deepest). Exact content rules in [`references/output-modes.md`](references/output-modes.md).

## What to look for (read on demand)

Canonical per-section signal list (Technical SEO, On-Page, IA, GEO, EEAT, Entity, Performance) lives in [`references/audit-checklist.md`](references/audit-checklist.md). Read it when scoring an individual section.

## Reporting rules

- Start with the scorecard.
- Call out **passed items** as well as failures.
- Prefer patterns over one-off nitpicks.
- Keep unsupported assumptions out of the report.
- State which URLs were crawled and which were used for Lighthouse.
- If a finding comes from a limited sample, say so.
- If rendered-browser evidence is stronger than the raw baseline, say that clearly and treat it as a risk.
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
- `scripts/language_packs.py` — centralized EN/ZH UI strings for both renderers
- `scripts/_report_styles.py` — shared CSS palette tokens
- `scripts/package.json` — Lighthouse npm dependencies
- `tests/` — pytest/unittest suite for crawl + parse helpers
- `references/setup-gate.md` — long-form rationale + literal setup questions
- `references/cli-flags.md` — wrapper flag reference + security notes
- `references/example-requests.md` — example chat invocations
- `references/scoring-rubric.md` — scoring rules and weights
- `references/report-template.md` — output skeleton
- `references/report-payload-template.json` — structured payload template
- `references/architecture.md` — crawl + fetch + Lighthouse internals
- `references/audit-checklist.md` — per-section signal lists
- `references/output-modes.md` — Boss / Operator / Specialist content rules
