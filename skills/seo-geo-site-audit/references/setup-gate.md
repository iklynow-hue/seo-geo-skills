# Mandatory Setup Gate — Detail

The audit always begins with five setup questions before any crawl. This page captures the long rationale; SKILL.md keeps just the rule.

## Why this is mandatory

An audit is long, opinionated, and expensive. Silently picking scope, performance mode, HTML output, or output language produces reports that the user can't trust. The setup gate exists to make those choices visible.

The gate **overrides** any session-level "no clarifying questions", "pick reasonable defaults", autonomous-mode, harness-level no-clarify hint, or "be terse" tone. None of those count as opting out. Only explicit waivers do.

## What counts as an explicit waiver

1. The user provides all five answers (scope, output style, performance evidence, HTML report, output language) in their first message — for example: "Use $seo-geo-site-audit to audit https://example.com with light mode, Operator output, performance on, HTML report on, and final report in Chinese."
2. The user explicitly says something like "use defaults for everything", "skip the questions, all defaults", "default everything", "全部用默认", or an equivalent literal opt-in.

If unsure whether the user waived, ask.

If the user pushes back ("just go", "stop asking"), still confirm the output language before writing the final report — language cannot be guessed safely.

## Default language is English — do not infer from prompt language

When the user picks the "default" path (option 1 to any question, or a blanket "use defaults"), or when their answer is missing or unrecognized, the output language is **English**, regardless of:

- the language the user is writing the request in (someone asking in Chinese still gets an English report by default),
- the language of the target domain (a `.cn` site still defaults to English),
- the agent's session locale.

Only an explicit, unambiguous selection switches the report to a non-English language:

- typing `2` at the language question, or
- saying "Chinese" / "中文" / "Spanish" / "in <language>" / "用中文" / "report in <language>", or
- providing the `--report-language` flag.

If the user said "default" or didn't answer, render English. Do not auto-translate based on tone.

## The five questions, in order

Ask one by one. Use numbered choices so the user can answer with `1`, `2`, `3`, or `4`. If the user already supplied an answer for a question in the original prompt, skip that question.

### 1. Scope

```
Choose the audit scope:
1. Fast check (1 page)
2. Light template audit (10 pages, default)
3. Standard template audit (50 pages)
4. Custom page cap up to 50
```

If the user chooses `4`, follow up: `Reply with a crawl cap from 1 to 50.`

### 2. Output style

```
Choose the output style:
1. Operator (default)
2. Boss
3. Specialist
```

### 3. Performance evidence

```
Collect performance evidence with local Lighthouse?
1. Yes, run local Lighthouse (default)
2. Skip performance
```

If Lighthouse dependencies are not yet installed (`node` missing, or `scripts/node_modules/lighthouse` missing), tell the user they can rerun with `--auto-install-prereqs` or run `npm install` once in the `scripts/` directory.

### 4. HTML report

```
Do you want the HTML report?
1. Off (default)
2. On
```

### 5. Final output language

```
Choose the final output language:
1. English (default)
2. Chinese
3. Other (type it in)
```

If the user chooses `3`, follow up: `Reply with the output language in the next message.`

Language confirmation is **mandatory**. Do not treat setup as complete until the user confirms the final report language or explicitly says to use the default English.

## Defaults (when the user says "use defaults")

- Light template audit
- 10 pages
- Operator output style
- Performance evidence via local Lighthouse
- HTML report off
- Final output language English

## Asking the questions one by one

Ask one question, wait for the answer, then ask the next. Do not batch into a single block. This keeps the user's choices visible and reduces drift.

If the user supplies scope, output style, performance, and HTML report in the original prompt but language is still missing, stop and ask the language question before continuing.

If the agent forgets to ask, the user can prompt explicitly: "Ask me the setup questions one by one with numbered options for scope, output style, performance handling, HTML report, and final output language before you begin."
