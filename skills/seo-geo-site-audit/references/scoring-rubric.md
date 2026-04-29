# SEO GEO Site Audit Scoring Rubric

Use this rubric after reviewing the crawl JSON and PageSpeed JSON.

## Section weights

| Section | Weight |
|---|---:|
| Technical SEO & Indexability | 20 |
| On-Page SEO & Content Packaging | 15 |
| Information Architecture & Internal Linking | 10 |
| GEO & AI Extractability | 20 |
| EEAT & Trust Signals | 15 |
| Entity & Structured Data | 10 |
| Performance & Page Experience | 10 |
| **Total** | **100** |

## Score bands

| Score | Band | Meaning |
|---|---|---|
| 90-100 | Excellent | Strong foundation, mostly optimization work |
| 75-89 | Good | Healthy overall, some important gaps |
| 60-74 | Mixed | Usable base, but clear structural weaknesses |
| 40-59 | Weak | Important issues likely limiting growth |
| 0-39 | Critical | Fundamental blockers or severe inconsistency |

## Severity scale

| Severity | Meaning |
|---|---|
| P0 | Blocking issue. Can materially prevent indexing, rendering, or trust. |
| P1 | Major issue. Strongly limits rankings, citations, or conversions. |
| P2 | Meaningful improvement opportunity. |
| P3 | Low-risk polish or completeness issue. |

## How to score each section

Do not pretend the score is mathematically exact. Use the evidence and round to a whole number.

### 1. Technical SEO & Indexability (20)

Reward:

- most sampled pages return 200
- robots and sitemap are present and sane
- canonical tags are consistent
- title / meta / H1 coverage is strong
- core content appears in raw Googlebot-visible HTML
- rendered-browser content does not materially exceed the search-engine baseline
- duplicate metadata is limited
- raw and rendered signal coverage agree, or rendered-only signals are clearly non-critical

Penalize heavily:

- large share of missing canonicals
- widespread missing descriptions or H1 problems
- no sitemap
- no meaningful body content in raw Googlebot-visible HTML
- important content or navigation only appears after JavaScript rendering
- sampled pages are found only through DOM route hints or route guesses
- heavy duplicate title / meta clusters
- many important pages marked noindex accidentally

Raw vs rendered scoring guidance:

- If raw HTML is missing a signal but rendered DOM recovers it, score it as a JavaScript dependency risk, not as a full missing-signal failure.
- If raw HTML and rendered DOM both miss a signal, score it as a true missing-signal issue.
- If raw internal links are absent but rendered `<a href>` links exist, penalize discovery robustness; if only DOM route hints exist, penalize more heavily.
- For Google SEO, rendered-only title/description/H1/schema can be P1/P2 depending on page importance and performance. For GEO/AI visibility, keep the penalty higher because many AI crawlers do not reliably render JavaScript.

### 2. On-Page SEO & Content Packaging (15)

Reward:

- titles and descriptions reflect page intent
- headings are usable
- sufficient page copy exists for the page type
- media has alt coverage
- pages clearly serve informational or commercial goals

Penalize:

- thin pages
- vague titles
- missing descriptions
- low-information hero pages
- weak or absent alt text

### 3. Information Architecture & Internal Linking (10)

Reward:

- major templates are discoverable
- important pages are linked with crawlable raw `<a href>` anchors where possible
- breadcrumbs exist on deeper pages
- internal links are healthy
- important pages are not buried
- navigation structure is coherent

Penalize:

- low internal-link density
- navigation that depends on JS-only handlers, framework state, or guessed routes
- weak breadcrumb coverage
- orphan-like pages in sitemap with poor linking
- inconsistent template navigation

### 4. GEO & AI Extractability (20)

Reward:

- answer-first summaries
- FAQ / facts / lists / tables / definitions
- extractable HTML structure
- entity naming is consistent
- `llms.txt` exists or the site otherwise exposes machine-friendly summaries
- core facts are visible without JS-heavy rendering

Penalize:

- core facts hidden behind interaction or client-only rendering
- overly vague marketing copy
- missing structured answer blocks
- poor extractability of product, policy, or factual content

Raw vs rendered scoring guidance:

- Give partial credit when rendered DOM contains answer-first content, facts, links, and schema.
- Do not give full GEO credit when key facts only appear after JavaScript rendering; raw HTML, `llms.txt`, feeds, docs, and structured data are stronger retrieval surfaces.
- If `llms.txt` is strong but page HTML is raw-empty, treat `llms.txt` as a win and the page as a remaining extraction risk.

### 5. EEAT & Trust Signals (15)

Reward:

- about, contact, support, policy, and security/trust pages exist
- content pages show author/editorial context when appropriate
- organization identity is clear
- trust claims are easy to verify on-site

Penalize:

- weak ownership signals
- no visible support / contact paths
- no editorial or author context on knowledge content
- trust pages absent for high-stakes sites

### 6. Entity & Structured Data (10)

Reward:

- Organization / WebSite / BreadcrumbList appear where appropriate
- content or product pages expose page-type schema
- sameAs or organization identity signals are consistent
- schema appears structurally valid and purposeful

Penalize:

- no JSON-LD on important templates
- breadcrumb schema absent on deep pages
- page-type schema missing across core templates
- entity inconsistency

### 7. Performance & Page Experience (10)

Use PageSpeed evidence from both mobile and desktop.

Reward:

- mobile performance is not severely lagging desktop
- LCP, INP, and CLS are within healthy ranges or near them
- SEO / best-practices categories are strong
- recurring bottlenecks are limited

Penalize:

- poor mobile performance
- bad LCP, INP, or CLS patterns
- repeated render-blocking, image, or JS issues
- major template outliers

## What must be included in every section

Each section must contain:

1. **Score**
2. **Passed items**
3. **Issues**
4. **Evidence**
5. **Recommended actions**

## Overall score

Compute a weighted score out of 100, then provide one-line interpretation:

- `Excellent foundation`
- `Good base with notable gaps`
- `Mixed readiness`
- `Weak foundation`
- `Critical blockers`

## Confidence statement

Always include:

- crawl cap used
- number of pages actually sampled
- PageSpeed URLs tested
- any important blind spots or failures
