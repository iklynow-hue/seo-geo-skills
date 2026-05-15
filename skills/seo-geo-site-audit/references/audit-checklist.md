# What To Look For — Audit Checklist by Section

Read this when scoring individual sections. Each list is the canonical signal set the rubric expects you to evaluate.

## Technical SEO & Indexability

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

## On-Page SEO & Content Packaging

- intent-match clarity
- descriptive titles / descriptions
- usable heading structure
- enough body copy to support the page's purpose
- helpful media and alt text
- commercial or informational clarity

## Information Architecture & Internal Linking

- navigational discoverability
- raw `<a href>` internal links as the strongest discovery evidence
- rendered `<a href>` links as secondary evidence
- DOM route hints and guessed routes as assisted discovery only
- breadcrumbs
- reasonable internal-link density
- important pages reachable without deep burying
- template consistency

## GEO & AI Extractability

- answer-first summaries
- FAQ / definitions / facts / lists / tables
- structured, extractable prose
- raw HTML visibility of core facts
- clear warning when AI-readable facts only appear after JavaScript rendering
- clear separation between Google rendering support and AI crawler/GEO extractability, because many AI crawlers and retrieval systems still prefer or require non-JS HTML
- `llms.txt` presence if available
- clean entity naming and context windows for retrieval

## EEAT & Trust Signals

- about / contact / support presence
- author or editorial signals on content pages
- trust / security / policy pages
- clear ownership and organization identity

## Entity & Structured Data

- Organization / WebSite / BreadcrumbList
- page-type schema where appropriate
- sameAs coverage when visible in JSON-LD
- schema consistency across templates

## Performance & Page Experience

- mobile and desktop Lighthouse results
- LCP, INP, CLS
- render-blocking resources
- image and script weight
- stability and interaction quality
