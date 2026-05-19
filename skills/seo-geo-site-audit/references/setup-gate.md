# Defaults + Inline Overrides

The skill runs immediately with these defaults. The user does not need to answer questions — the agent passes a URL to the wrapper and starts working. Overrides come from natural-language phrasings in the user's prompt or from CLI flags.

## Defaults

| Setting | Default | Wrapper flag |
|---|---|---|
| Mode | Light template audit (10 pages) | `--mode light` |
| Output style | Operator | `--output-style operator` |
| Performance evidence | Local Lighthouse, homepage, mobile + desktop | (no flag — on by default) |
| HTML report | On | `--html-report` |
| Output language | English | `--report-language english` |

## Inline override phrasings

When parsing the user's prompt, watch for these and pass the matching flag.

### English

| Phrasing | Effect |
|---|---|
| `fast`, `quick check`, `1 page`, `homepage only`, `just the homepage` | `--mode fast` (1 page) |
| `template`, `standard`, `full audit`, `50 pages`, `wider sample` | `--mode template` (50 pages) |
| `N pages`, `crawl N`, `cap at N` (N = 1–50) | `--max-pages N` |
| `boss style`, `executive summary`, `short version` | `--output-style boss` |
| `specialist`, `detailed`, `deep`, `everything` | `--output-style specialist` |
| `skip performance`, `skip lighthouse`, `no pagespeed`, `no perf` | `--skip-pagespeed` |
| `no html`, `json only`, `skip html`, `chat report only` | drop `--html-report` |
| `in Chinese`, `Chinese report`, `output in Chinese` | `--report-language chinese` |
| `in <language>`, `report in <language>` | `--report-language <language>` |
| `test more pages with Lighthouse`, `Lighthouse on N urls` | `--max-pagespeed-urls N` (1–10) |

### Chinese / 中文

| Phrasing | Effect |
|---|---|
| `快速检查`, `首页`, `只测首页` | `--mode fast` (1 page) |
| `模板审核`, `标准审核`, `50 页` | `--mode template` (50 pages) |
| `N 页`, `抓 N 个`, `上限 N` | `--max-pages N` |
| `老板风格`, `精简版`, `执行摘要` | `--output-style boss` |
| `专家版`, `详细`, `深度` | `--output-style specialist` |
| `跳过性能`, `不测 Lighthouse`, `不测性能` | `--skip-pagespeed` |
| `不要 HTML`, `只输出 JSON` | drop `--html-report` |
| `用中文输出`, `中文报告`, `结果用中文` | `--report-language chinese` |
| `用 <语言>` | `--report-language <语言>` |

## When the agent should ask

Three cases only:

1. **No URL supplied.** "Audit my site" without a URL → ask for the URL.
2. **Ambiguous non-English language.** User typed the request in a non-English language but didn't say "in <language>" for the report. Ask once: "Report in English or <other>?". Default stays English on no answer.
3. **Prerequisite install requires consent.** If `--auto-install-prereqs` would download network binaries (Lightpanda nightly, Camoufox), tell the user and ask before running. Default fallback: `--skip-prereq-check` and the urllib fetcher.

That's the full list. Don't ask about scope, output style, performance, or HTML.

## Why English is the default

The user-facing prompt language is not a reliable signal for the report language. Someone may type in Chinese but want an English deliverable; a `.cn` domain may have an English target audience. Defaulting to English and switching only on explicit "in <language>" phrasing keeps the choice deterministic.

## Session preferences

A session-level preference like "be quick", "no clarifying questions", or "autonomous mode" is the **same signal** as "use defaults" — run immediately. There is no override of session preferences. The defaults are the contract.

## Customizing the defaults

Forks can ship different defaults by changing the wrapper script's argparse values in `scripts/audit_site.py`. The skill itself reads whatever the wrapper produces; no skill-side coupling.
