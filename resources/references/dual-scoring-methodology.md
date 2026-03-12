# Dual Scoring Methodology

**Last Updated:** March 12, 2026

---

## Overview

The SGEO framework produces two independent scores from a single audit:

- **SEO Score (0-100):** Measures traditional search engine optimization
- **GEO Score (0-100):** Measures AI-powered search visibility

Both scores use the same raw evidence but apply different weights reflecting each domain's priorities.

---

## Weight Tables

### SEO Score Weights

| Category | Weight | Raw Score Source |
|----------|--------|-----------------|
| Technical Infrastructure | 25% | robots, security, redirects, broken links, rendering |
| On-Page Optimization | 20% | title, meta, headings, images, internal links, keywords |
| Content Quality & E-E-A-T | 15% | readability, depth, freshness, author signals |
| Structured Data | 15% | schema validation, rich result eligibility |
| Performance (CWV) | 10% | LCP, INP, CLS from PageSpeed |
| Social Signals | 5% | Open Graph, Twitter Card |
| Local SEO | 10% | GBP, NAP, local schema (0% if not local) |

**When Local SEO is N/A:** Redistribute 10% → Technical +5%, On-Page +5%

### GEO Score Weights

| Category | Weight | Raw Score Source |
|----------|--------|-----------------|
| AI Citability | 25% | citability_scorer.py, statistical density, Q&A structure |
| Brand Authority | 20% | brand_scanner.py, Wikipedia, reviews, Reddit, YouTube |
| Technical Infrastructure | 15% | SSR, crawlability, security, rendering |
| Content Quality & E-E-A-T | 15% | depth, original insights, external citations, author |
| AI Crawler Access | 10% | robots AI rules, llms.txt, llms-full.txt, meta AI tags |
| Structured Data | 10% | entity linking, sameAs count, FAQPage, speakable |
| Platform Optimization | 5% | AIO, ChatGPT, Perplexity, Gemini, Copilot readiness |

---

## Calculation

```
SEO Score = Σ(category_score[i] × seo_weight[i])
GEO Score = Σ(category_score[i] × geo_weight[i])
```

### Example

| Category | Raw Score | SEO Weight | SEO Contrib | GEO Weight | GEO Contrib |
|----------|-----------|------------|-------------|------------|-------------|
| Technical | 75 | 25% | 18.75 | 15% | 11.25 |
| On-Page | 80 | 20% | 16.00 | 0% | 0.00 |
| Content | 60 | 15% | 9.00 | 15% | 9.00 |
| Schema | 70 | 15% | 10.50 | 10% | 7.00 |
| CWV | 85 | 10% | 8.50 | 0% | 0.00 |
| Social | 90 | 5% | 4.50 | 0% | 0.00 |
| Local | N/A | 0% | 0.00 | 0% | 0.00 |
| Citability | 45 | 0% | 0.00 | 25% | 11.25 |
| Brand Auth | 30 | 0% | 0.00 | 20% | 6.00 |
| AI Crawlers | 65 | 0% | 0.00 | 10% | 6.50 |
| Platform | 55 | 0% | 0.00 | 5% | 2.75 |
| **Total** | | | **67.25** | | **53.75** |

**Result:** SEO: 67/100 (Fair) | GEO: 54/100 (Fair)

---

## Category Scoring Rules

### Technical Infrastructure (0-100)

| Check | Points | Method |
|-------|--------|--------|
| HTTPS active | 10 | redirect_checker.py |
| Security headers (6 total) | 15 | security_headers.py: (present/6) × 15 |
| robots.txt present + valid | 10 | robots_checker.py |
| Sitemap present + valid | 10 | robots_checker.py |
| No redirect chains | 10 | redirect_checker.py |
| No broken links | 15 | broken_links.py: max(0, 15 - broken_count × 3) |
| SSR/SSG (content without JS) | 15 | parse_html.py |
| Clean URL structure | 5 | parse_html.py |
| Canonical tags correct | 5 | parse_html.py |
| Mobile viewport set | 5 | parse_html.py |

### On-Page Optimization (0-100) — SEO Only

| Check | Points | Method |
|-------|--------|--------|
| Title tag (50-60 chars, keyword) | 15 | parse_html.py |
| Meta description (150-160 chars) | 10 | parse_html.py |
| Single H1, keyword-rich | 10 | parse_html.py |
| Heading hierarchy (H1→H2→H3) | 10 | parse_html.py |
| All images have alt text | 10 | parse_html.py |
| Images have dimensions | 5 | parse_html.py |
| Internal links ≥ 5 per page | 10 | internal_links.py |
| No orphan pages | 10 | internal_links.py |
| Keyword in first 100 words | 5 | parse_html.py |
| Descriptive anchor text | 5 | internal_links.py |
| Unique title/meta per page | 10 | duplicate_content.py |

### AI Citability (0-100) — GEO Only

| Check | Points | Method |
|-------|--------|--------|
| Statistical anchors (≥3 per page) | 20 | citability_scorer.py |
| Self-contained passages (134-167 words) | 20 | citability_scorer.py |
| Direct answer patterns | 15 | citability_scorer.py |
| FAQ sections present | 15 | parse_html.py |
| Comparison tables | 10 | citability_scorer.py |
| Source attribution (external links) | 10 | citability_scorer.py |
| "How it works" explanations | 10 | citability_scorer.py |

### Brand Authority (0-100) — GEO Only

| Check | Points | Method |
|-------|--------|--------|
| Wikipedia/Wikidata presence | 20 | brand_scanner.py |
| Review platforms (G2, Capterra, etc.) | 20 | brand_scanner.py |
| Reddit mentions | 15 | brand_scanner.py |
| YouTube presence | 15 | brand_scanner.py |
| Press/blog coverage | 10 | brand_scanner.py |
| Social media active | 10 | brand_scanner.py |
| Third-party citations | 10 | brand_scanner.py |

### Content Quality & E-E-A-T (0-100)

| Check | Points | Method |
|-------|--------|--------|
| Word count ≥ 1000 (homepage) | 10 | readability.py |
| Flesch Reading Ease ≥ 50 | 10 | readability.py |
| Paragraph length ≤ 4 sentences avg | 10 | readability.py |
| Author attribution present | 10 | parse_html.py |
| Author credentials/bio | 10 | parse_html.py |
| External citations (≥3) | 10 | citability_scorer.py |
| Date published present | 10 | parse_html.py |
| Date modified present | 10 | parse_html.py |
| Original insights/data | 10 | LLM analysis |
| No thin content (≥300 words/page) | 10 | readability.py |

### Structured Data (0-100)

| Check | Points | Method |
|-------|--------|--------|
| Valid JSON-LD syntax | 10 | schema_validator.py |
| Organization schema | 10 | schema_validator.py |
| WebSite + SearchAction | 10 | schema_validator.py |
| BreadcrumbList | 10 | schema_validator.py |
| Page-specific schema (Article, Product, etc.) | 15 | schema_validator.py |
| sameAs links (SEO: ≥2, GEO: ≥5) | 10 | schema_validator.py |
| FAQPage present (GEO bonus) | 10 | schema_validator.py |
| No deprecated types | 10 | schema_validator.py |
| No placeholder text | 5 | schema_validator.py |
| speakable property (GEO bonus) | 10 | schema_validator.py |

### AI Crawler Access (0-100) — GEO Only

| Check | Points | Method |
|-------|--------|--------|
| GPTBot allowed | 10 | robots_checker.py |
| ClaudeBot allowed | 10 | robots_checker.py |
| PerplexityBot allowed | 10 | robots_checker.py |
| Google-Extended allowed | 10 | robots_checker.py |
| Applebot-Extended allowed | 5 | robots_checker.py |
| Other AI bots managed | 5 | robots_checker.py |
| llms.txt present | 15 | llms_txt_checker.py |
| llms.txt quality ≥ 70 | 10 | llms_txt_checker.py |
| llms-full.txt present | 10 | llms_txt_checker.py |
| llms.txt in robots.txt | 5 | robots_checker.py |
| No AI-blocking meta tags | 10 | parse_html.py |

### Performance / CWV (0-100) — SEO Only

| Check | Points | Method |
|-------|--------|--------|
| LCP ≤ 2.5s | 30 | pagespeed.py |
| INP ≤ 200ms | 30 | pagespeed.py |
| CLS ≤ 0.1 | 20 | pagespeed.py |
| TTFB ≤ 800ms | 10 | pagespeed.py |
| Performance score ≥ 90 | 10 | pagespeed.py |

### Social Signals (0-100) — SEO Only

| Check | Points | Method |
|-------|--------|--------|
| og:title present | 15 | social_meta.py |
| og:description present | 15 | social_meta.py |
| og:image present + absolute URL | 20 | social_meta.py |
| og:image dimensions set | 10 | social_meta.py |
| twitter:card present | 15 | social_meta.py |
| twitter:title present | 10 | social_meta.py |
| twitter:image present + absolute | 15 | social_meta.py |

### Platform Optimization (0-100) — GEO Only

| Platform | Points | Key Signals |
|----------|--------|-------------|
| Google AI Overviews | 25 | Question headings, direct answers, FAQPage |
| ChatGPT Search | 25 | Wikipedia, entity recognition, citations |
| Perplexity AI | 20 | Reddit, timestamps, source attribution |
| Google Gemini | 15 | YouTube, multimodal, structured data |
| Bing Copilot | 15 | IndexNow, Bing Webmaster, schema |

---

## Score Interpretation

| Score | Rating | Color | Action |
|-------|--------|-------|--------|
| 90-100 | Excellent | 🟢 Green | Maintain and monitor |
| 70-89 | Good | 🔵 Blue | Minor optimizations |
| 50-69 | Fair | 🟡 Yellow | Significant improvements needed |
| 30-49 | Poor | 🟠 Orange | Major overhaul required |
| 0-29 | Critical | 🔴 Red | Immediate action required |

---

## Divergence Analysis

When SEO and GEO scores differ by more than 15 points, include a **Divergence Analysis** section:

```markdown
## Score Divergence Analysis

SEO Score: 72/100 | GEO Score: 48/100 | Delta: 24 points

**Why the gap:**
The site has strong traditional SEO foundations (good technical setup, on-page optimization)
but lacks AI search visibility signals (no brand authority, low citability, incomplete AI crawler access).

**Priority:** Focus on GEO improvements to close the gap.
```

---

**Methodology Status:** ✅ Active
**Next Review:** June 2026
