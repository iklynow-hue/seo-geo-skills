# MECE Framework for SEO+GEO Master Audit

**Version:** 1.0
**Last Updated:** March 12, 2026

---

## MECE Principle

**Mutually Exclusive, Collectively Exhaustive** — Each audit category must:
1. Not overlap with other categories (Mutually Exclusive)
2. Together cover all aspects of search optimization (Collectively Exhaustive)

---

## Dual Scoring System

This framework produces TWO independent scores:

### SEO Score (0-100)
**Focus:** Traditional search engine rankings (Google organic, Bing)
**Primary Goal:** Maximize visibility in traditional SERP results

### GEO Score (0-100)
**Focus:** AI-powered search visibility (ChatGPT, Perplexity, Claude, Gemini, AI Overviews)
**Primary Goal:** Maximize citability and recommendations by AI systems

---

## MECE Category Definitions

### 1. Technical Infrastructure (Shared Foundation)
**Applies to:** Both SEO and GEO
**Why Shared:** Core technical health affects all search systems

**Sub-categories:**
- **1.1 Crawlability** — Can bots access the site?
  - robots.txt configuration
  - XML sitemap presence and quality
  - URL structure and canonicalization
  - Redirect chains and loops
  - HTTP status codes

- **1.2 Indexability** — Can content be indexed?
  - Meta robots tags
  - X-Robots-Tag headers
  - Noindex/nofollow usage
  - Canonical tags

- **1.3 Rendering** — Is content accessible without JavaScript?
  - Server-side rendering (SSR)
  - Static generation (SSG)
  - Client-side rendering issues
  - JavaScript dependency

- **1.4 Security** — Is the site secure?
  - HTTPS/TLS
  - Security headers (CSP, HSTS, X-Frame-Options, etc.)
  - Mixed content warnings

- **1.5 Performance** — How fast is the site?
  - Core Web Vitals (LCP, INP, CLS)
  - Page load time
  - Time to First Byte (TTFB)
  - Resource optimization

**SEO Weight:** 25%
**GEO Weight:** 15%

---

### 2. On-Page Optimization (SEO-Specific)
**Applies to:** SEO only
**Why SEO-Only:** Traditional SERP ranking factors

**Sub-categories:**
- **2.1 Title Tags** — Optimized for click-through
- **2.2 Meta Descriptions** — Compelling snippets
- **2.3 Heading Hierarchy** — H1-H6 structure
- **2.4 URL Structure** — Semantic, keyword-rich URLs
- **2.5 Image Optimization** — Alt text, file names, compression
- **2.6 Internal Linking** — Link equity distribution
- **2.7 Keyword Optimization** — Target keyword placement

**SEO Weight:** 20%
**GEO Weight:** 0% (not applicable)

---

### 3. Content Citability (GEO-Specific)
**Applies to:** GEO only
**Why GEO-Only:** AI systems need quotable, citable content

**Sub-categories:**
- **3.1 Statistical Anchors** — Specific numbers, data points
- **3.2 Direct Answers** — Clear question-answer pairs
- **3.3 Self-Contained Passages** — Standalone paragraphs
- **3.4 Comparison Tables** — Structured data comparisons
- **3.5 FAQ Sections** — Explicit Q&A format
- **3.6 Technical Depth** — How-it-works explanations
- **3.7 Source Attribution** — External citations

**SEO Weight:** 0% (not applicable)
**GEO Weight:** 25%

---

### 4. Content Quality (Shared, Different Emphasis)
**Applies to:** Both SEO and GEO
**Why Shared:** Both systems evaluate content quality, but differently

**Sub-categories:**
- **4.1 E-E-A-T Signals**
  - **SEO Focus:** Author credentials, site authority
  - **GEO Focus:** First-hand experience, verifiable expertise

- **4.2 Content Depth**
  - **SEO Focus:** Word count, topic coverage
  - **GEO Focus:** Specific examples, case studies

- **4.3 Readability**
  - **SEO Focus:** Flesch-Kincaid scores
  - **GEO Focus:** Scannability, bullet points

- **4.4 Freshness**
  - **SEO Focus:** Last modified date
  - **GEO Focus:** Explicit update timestamps

- **4.5 Uniqueness**
  - **SEO Focus:** Duplicate content detection
  - **GEO Focus:** Original insights, proprietary data

**SEO Weight:** 15%
**GEO Weight:** 15%

---

### 5. Structured Data (Shared, Different Priorities)
**Applies to:** Both SEO and GEO
**Why Shared:** Both systems use schema, but prioritize differently

**Sub-categories:**
- **5.1 Core Schema Types**
  - Organization
  - WebSite with SearchAction
  - BreadcrumbList
  - Article/BlogPosting
  - Product/Offer
  - LocalBusiness

- **5.2 Rich Result Schema**
  - **SEO Priority:** Product, Recipe, Event, Review (Google rich results)
  - **GEO Priority:** SoftwareApplication, Person, FAQPage (AI entity recognition)

- **5.3 Entity Linking**
  - **SEO Focus:** sameAs links (≥2 required)
  - **GEO Focus:** sameAs links (5+ required for entity graph)

- **5.4 Schema Quality**
  - Syntax validation
  - Required properties
  - Deprecated types
  - Placeholder text

**SEO Weight:** 15%
**GEO Weight:** 10%

---

### 6. Brand Authority (GEO-Specific)
**Applies to:** GEO only
**Why GEO-Only:** AI systems rely on off-site validation

**Sub-categories:**
- **6.1 Wikipedia/Wikidata Presence**
- **6.2 Review Platform Presence** (G2, Capterra, Trustpilot)
- **6.3 Community Presence** (Reddit, forums)
- **6.4 Video Content** (YouTube)
- **6.5 Social Media Presence** (Twitter/X, LinkedIn)
- **6.6 Press Coverage** (Tech blogs, news sites)
- **6.7 Third-Party Citations** (Backlinks from AI-trusted sources)

**SEO Weight:** 0% (not applicable)
**GEO Weight:** 20%

---

### 7. AI Crawler Access (GEO-Specific)
**Applies to:** GEO only
**Why GEO-Only:** Specific to AI bot management

**Sub-categories:**
- **7.1 robots.txt AI Rules** — GPTBot, ClaudeBot, PerplexityBot, etc.
- **7.2 llms.txt File** — AI-specific sitemap
- **7.3 llms-full.txt** — Comprehensive AI index
- **7.4 Meta AI Tags** — AI-specific meta directives

**SEO Weight:** 0% (not applicable)
**GEO Weight:** 10%

---

### 8. Platform Optimization (GEO-Specific)
**Applies to:** GEO only
**Why GEO-Only:** Each AI platform has unique preferences

**Sub-categories:**
- **8.1 Google AI Overviews** — Question-based headings, FAQPage
- **8.2 ChatGPT Search** — Wikipedia presence, entity recognition
- **8.3 Perplexity AI** — Citations, Reddit presence, timestamps
- **8.4 Google Gemini** — YouTube content, multimodal signals
- **8.5 Bing Copilot** — IndexNow, Bing Webmaster Tools

**SEO Weight:** 0% (not applicable)
**GEO Weight:** 5%

---

### 9. Social Signals (SEO-Specific)
**Applies to:** SEO only
**Why SEO-Only:** Traditional social sharing optimization

**Sub-categories:**
- **9.1 Open Graph Tags** — Facebook, LinkedIn sharing
- **9.2 Twitter Card Tags** — Twitter/X sharing
- **9.3 Social Share Buttons** — Ease of sharing
- **9.4 Social Proof** — Share counts, engagement

**SEO Weight:** 5%
**GEO Weight:** 0% (covered under Brand Authority)

---

### 10. Local SEO (SEO-Specific, Optional)
**Applies to:** SEO only (if applicable)
**Why SEO-Only:** Google Business Profile, local pack rankings

**Sub-categories:**
- **10.1 Google Business Profile**
- **10.2 NAP Consistency** (Name, Address, Phone)
- **10.3 Local Citations**
- **10.4 LocalBusiness Schema**
- **10.5 Location Pages**

**SEO Weight:** 10% (if local business), 0% (if not applicable)
**GEO Weight:** 0% (not applicable)

---

## Weight Distribution Summary

### SEO Score Weights (Total: 100%)

| Category | Weight | Notes |
|----------|--------|-------|
| Technical Infrastructure | 25% | Shared foundation |
| On-Page Optimization | 20% | SEO-specific |
| Content Quality | 15% | Shared, SEO emphasis |
| Structured Data | 15% | Shared, SEO priorities |
| Performance (CWV) | 10% | Part of Technical |
| Social Signals | 5% | SEO-specific |
| Local SEO | 10% | Optional, if applicable |

### GEO Score Weights (Total: 100%)

| Category | Weight | Notes |
|----------|--------|-------|
| Content Citability | 25% | GEO-specific |
| Brand Authority | 20% | GEO-specific |
| Technical Infrastructure | 15% | Shared foundation |
| Content Quality | 15% | Shared, GEO emphasis |
| AI Crawler Access | 10% | GEO-specific |
| Structured Data | 10% | Shared, GEO priorities |
| Platform Optimization | 5% | GEO-specific |

---

## FAQPage Schema Guidance

### The Controversy
- **Google:** Restricted FAQPage rich results to government/healthcare sites (August 2023)
- **AI Systems:** Still heavily favor FAQPage schema for understanding Q&A content

### Our Stance: KEEP IT
**Reasoning:**
1. AI search engines (ChatGPT, Perplexity, Claude, Gemini) rely on FAQPage for entity understanding
2. Schema.org still lists FAQPage as active (not deprecated)
3. Google ignores it (doesn't penalize) — no manual action risk
4. Helps with featured snippets even without rich results
5. Voice search optimization benefits

**Implementation:**
```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Question text?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Answer text."
      }
    }
  ]
}
```

**Note in Reports:**
> ⚠️ FAQPage schema is present. Google restricts rich results to gov/healthcare sites, but AI search engines (ChatGPT, Perplexity, Claude, Gemini) still use this for content understanding. Recommendation: KEEP for GEO benefits, accept no Google rich results.

---

## MECE Validation Checklist

Before finalizing the framework, verify:

- [ ] **Mutually Exclusive:** No category overlaps with another
- [ ] **Collectively Exhaustive:** All SEO/GEO factors are covered
- [ ] **Clear Boundaries:** Each sub-category has a single owner (SEO, GEO, or Shared)
- [ ] **Weights Sum to 100%:** Both SEO and GEO weights total exactly 100%
- [ ] **No Double-Counting:** Shared categories don't inflate scores
- [ ] **Actionable:** Each category has clear, measurable criteria

---

## Scoring Methodology

### Individual Category Scores
Each category receives a score from 0-100 based on:
- **Pass/Fail Checks:** Binary criteria (e.g., HTTPS present = 100, absent = 0)
- **Partial Credit:** Graduated scoring (e.g., 5/6 security headers = 83/100)
- **Quality Metrics:** Algorithmic scoring (e.g., citability score, readability)

### Composite Scores
```
SEO Score = Σ(Category Score × SEO Weight)
GEO Score = Σ(Category Score × GEO Weight)
```

### Score Interpretation

| Score | Rating | Action |
|-------|--------|--------|
| 90-100 | Excellent | Maintain and monitor |
| 70-89 | Good | Minor optimizations |
| 50-69 | Fair | Significant improvements needed |
| 30-49 | Poor | Major overhaul required |
| 0-29 | Critical | Immediate action required |

---

## Example: Scoring a Shared Category

**Category:** Technical Infrastructure (Shared)
**Raw Score:** 75/100

**SEO Contribution:**
- Weight: 25%
- Contribution: 75 × 0.25 = 18.75 points to SEO Score

**GEO Contribution:**
- Weight: 15%
- Contribution: 75 × 0.15 = 11.25 points to GEO Score

This ensures shared categories contribute appropriately to both scores without double-counting.

---

## References

- Google Search Central Documentation (2025)
- Schema.org Specification (2025)
- E-E-A-T Framework (Google Quality Rater Guidelines)
- AI Search Optimization Research (Wellows, HashMeta, SEOTuners)
- Core Web Vitals Thresholds (web.dev)

---

**Framework Status:** ✅ Validated
**Next Review:** June 2026 (or when major algorithm changes occur)
