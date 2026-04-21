# SEO GEO Site Audit for Claude Code

Use this skill when the user wants an SEO audit, GEO audit, AI visibility review, or a structured site-quality audit for a public website.

Default operating rules:

- Ask the setup questions one by one before crawling if scope is incomplete.
- Use the wrapper script for normal audits:
  `/Users/klyment/.agents/skills/seo-geo-site-audit/scripts/audit-site`
- Prefer `--pagespeed-provider local` by default.
- Only use PageSpeed API when the user explicitly chooses it.
- If HTML output is enabled, ask one extra question for report language:
  `1. English`
  `2. Chinese`
  `3. Other (type it in)`

Security rules:

- Never hardcode API keys, tokens, or secrets in this repo.
- Never write PageSpeed API keys to tracked files, generated artifacts, docs, templates, or examples.
- Only accept a PageSpeed API key from runtime environment variables or from the user's current chat/session.
- If the user pastes a key in chat, use it only for that run and remind them to rotate it afterward.
- Do not include raw keys in error messages, logs, manifests, or saved JSON/HTML outputs.

Workflow summary:

- Crawl a capped representative sample up to 25 pages.
- Review technical SEO, on-page packaging, IA/internal linking, GEO extractability, EEAT/trust, structured data, and performance evidence.
- Produce Operator mode by default unless the user asks for Boss or Specialist.
- Treat all findings as sample-based evidence, not a complete site index.
