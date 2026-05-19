# Example user requests

How users typically invoke this skill in chat:

- `Use $seo-geo-site-audit to audit https://example.com. Ask me to confirm the crawl setup first.`
- `Run a standard SEO + GEO audit for https://example.com, use 50 pages, and generate the HTML report too.`
- `Audit this site for AI visibility and technical SEO. Ask whether I want to run local Lighthouse or skip performance before you continue. Ask the output language last.`
- `Audit this SPA site with JS rendering and local Lighthouse: https://www.mcmarkets.com`
- `Use $seo-geo-site-audit to audit https://example.com with light mode, Operator output, performance on, HTML report on, and final report in Chinese.`
  → This form supplies all five setup answers inline and waives the question-by-question gate.
- `Audit https://example.com — use defaults for everything.`
  → Explicit "use defaults" waiver. Runs the light template audit, Operator output, Lighthouse on, HTML report off, English.
