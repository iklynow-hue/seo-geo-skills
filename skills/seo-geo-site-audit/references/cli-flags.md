# CLI Flags — `audit-site` wrapper

The wrapper script is `${SKILL_DIR}/scripts/audit-site`. All normal audits should go through it.

## Flag reference

| Flag | Description |
|---|---|
| `--fetcher auto\|scrapling\|lightpanda\|agent_browser\|chrome\|urllib` | Preferred fetcher. Default: `auto` (tries all in priority order, including attached Chrome). |
| `--max-pagespeed-urls 1-10` | Maximum URLs to test with local Lighthouse. Default: `1` homepage URL, tested once on mobile and once on desktop. |
| `--report-language <language>` | Wrapper evidence HTML language and seeded `final-report.json` language. The final polished report HTML should come from `final-report.json` + `render-report-html`. |
| `--skip-pagespeed` | Skip local Lighthouse performance collection. |
| `--skip-prereq-check` | Skip prerequisite detection. |
| `--auto-install-prereqs` | Auto-install missing fetcher and Lighthouse prerequisites (opt-in network installs of pip/npm/curl-fetched binaries). |
| `--html-report` | Write the wrapper evidence HTML and seed `final-report.json`. |
| `--mode fast\|light\|template` | Audit depth preset (1 / 10 / 50 pages). |
| `--max-pages 1-50` | Override crawl cap. |
| `--output-style boss\|operator\|specialist` | Report style recorded with artifacts. |
| `--out-dir` | Custom output directory. |

## Full example

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

- Checks which optional fetcher prerequisites are available (including Lighthouse npm deps).
- Can auto-install missing prerequisites only if `--auto-install-prereqs` is supplied.
- Records a raw Googlebot-style search-engine baseline for each HTML page.
- Runs the capped crawl with JS rendering via the fetcher priority chain.
- Escalates from headless fetchers to attached Chrome in `auto` mode when needed.
- Makes a best-effort route expansion pass for router-heavy SPAs when rendered content exists but crawlable links are sparse, and labels those pages as assisted discovery.
- Detects SPA shells and reports `spa_detection` per page.
- Runs homepage mobile + desktop local Lighthouse unless `--skip-pagespeed` is used.
- Can write `evidence-report.html` and seed `final-report.json` when `--html-report` is supplied.
- Can render the final polished `audit-report.html` from `final-report.json`.
- Stores `crawl.json`, `pagespeed.json`, `audit-run.json`, and any HTML report together in one output folder under the skill's `runs/` directory by default.

## Security notes for `--auto-install-prereqs`

- Default is **opt-out** — installs only run when the flag is supplied.
- `install_lightpanda()` refuses unverified binary downloads unless a checksum is registered in `LIGHTPANDA_SHA256` or `SEO_GEO_ALLOW_UNVERIFIED_LIGHTPANDA=1` is set.
- Pin a release tag with `SEO_GEO_LIGHTPANDA_TAG=<tag>` to avoid pulling nightly binaries.
- The Lighthouse runner keeps Chrome's sandbox on by default. Set `SEO_GEO_ALLOW_NO_SANDBOX=1` only for trusted root / CI / container environments.
