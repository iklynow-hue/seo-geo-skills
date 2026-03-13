# SGEO Audit Report: PhotoRefix.com

**Audit Date:** 2026-03-13
**URL:** https://photorefix.com
**Framework:** MECE (Mutually Exclusive, Collectively Exhaustive)

---

## Executive Summary

| Metric | Score | Rating |
|--------|-------|--------|
| **SEO Score** | **63/100** | **Fair** |
| **GEO Score** | **47/100** | **Poor** |

PhotoRefix has solid technical foundations and good structured data implementation, but faces critical weaknesses in AI citability and brand authority that severely limit GEO performance. The site is well-optimized for traditional search but needs significant work to compete in AI search results.

### Critical Findings:
- 🔴 **AI Citability: 33/100** — Content lacks quotable passages, statistics, and optimal-length blocks
- 🔴 **Brand Authority: 25/100** — No Wikipedia, YouTube, Reddit, or review platform presence
- 🔴 **Heading Spacing Issues** — "BatchPhoto", "AskedQuestions", "TransformYour" missing spaces
- ⚠️ **Security Headers** — 5 critical headers missing (CSP, X-Frame-Options, etc.)
- ⚠️ **llms.txt Incomplete** — Missing description and links (45/100 quality score)

---

## MECE Category Breakdown

### 1. Technical Infrastructure
**SEO Weight:** 25% | **GEO Weight:** 15%
**SEO Score:** 65/100 | **GEO Score:** 70/100

#### ✅ Strengths:
- HTTPS enabled with HSTS header
- robots.txt properly configured with sitemap
- 8 AI crawlers explicitly allowed (GPTBot, ChatGPT-User, Google-Extended, CCBot, anthropic-ai, Claude-Web, PerplexityBot, Amazonbot)
- No redirect chains (direct 200 response)
- Zero broken links detected (28/28 healthy)
- Fast response time (211ms)

#### 🔴 Critical Issues:
**Security Headers (Score: 45/100)**
- Missing Content-Security-Policy (CSP) — prevents XSS, clickjacking
- Missing X-Frame-Options — allows clickjacking attacks
- Missing X-Content-Type-Options — enables MIME-sniffing attacks
- Missing Referrer-Policy — leaks referrer information
- Missing Permissions-Policy — no browser feature controls
- HSTS missing `includeSubDomains` directive

**Evidence:**
```
Headers Present: Strict-Transport-Security: max-age=63072000
Headers Missing: CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy
```

#### ⚠️ Warnings:
**AI Crawler Management**
- 4 AI crawlers not explicitly managed: ClaudeBot, Applebot-Extended, Bytespider, FacebookBot
- These inherit wildcard (*) rules but should be explicitly allowed for clarity

**Internal Linking**
- 3 orphan pages with ≤1 incoming link:
  - `/insights/update-linkedin-profile-picture-2025`
  - `/insights/4k-upscaling-digital-art-ai`
  - `/insights/product-photography-changing-contexts`
- 6 links with no anchor text (accessibility issue)
- 2 pages with <3 internal links

**Impact:** [BOTH] Security gaps affect trust signals for both SEO and GEO. Missing AI crawler rules reduce GEO visibility.

---

### 2. On-Page Optimization
**SEO Weight:** 20%
**SEO Score:** 70/100

#### ✅ Strengths:
- Title tag: "PhotoRefix - Fast Batch Photo Editing with AI" (well-optimized)
- Meta description: Present and compelling (155 characters)
- Canonical URL: Properly set to https://photorefix.com/
- 13 images with descriptive alt text
- 53 internal links (good distribution)
- Proper heading hierarchy (H1 → H2 → H3)

#### 🔴 Critical Issues:
**Heading Text Quality**
- H1: "Fast **BatchPhoto** Editing with AI" — missing space between "Batch" and "Photo"
- H2: "Frequently **AskedQuestions**" — missing space
- H2: "Ready to **TransformYour** Photos?" — missing space

**Evidence:**
```json
"h1": ["Fast BatchPhoto Editing with AI"],
"h2": ["Frequently AskedQuestions", "Ready to TransformYour Photos?"]
```

**Social Meta Issues**
- `og:image: "/og.jpg"` — relative path, should be absolute URL
- Missing `og:image:width` and `og:image:height` (recommended: 1200×630)

**Impact:** [SEO] Heading spacing errors hurt readability and professionalism. Relative og:image may fail on some platforms.

---

### 3. Content Quality & E-E-A-T
**SEO Weight:** 15% | **GEO Weight:** 15%
**SEO Score:** 60/100 | **GEO Score:** 55/100

#### ✅ Strengths:
- Word count: 843 words (adequate for homepage)
- Clear value proposition and feature descriptions
- Founder attribution in Organization schema (Alex May)
- Customer testimonials included

#### ⚠️ Warnings:
**Readability Issues**
- Flesch Reading Ease: 45.6 (Difficult, 9th-12th grade)
- Target: 60+ for broader accessibility
- Average paragraph length: 73 sentences (should be 2-4)
- Complex word percentage: 19.2%

**Evidence:**
```json
"flesch_reading_ease": 45.6,
"reading_level": "Difficult (9th-12th grade)",
"avg_paragraph_length": 73.0
```

**E-E-A-T Signals**
- No visible author bylines on content
- Founder schema present but minimal expertise signals
- No "About the Author" sections
- Missing credentials, certifications, or industry recognition

**Impact:** [BOTH] Poor readability reduces engagement. Weak E-E-A-T signals hurt trust for both traditional and AI search.

---

### 4. Structured Data
**SEO Weight:** 15% | **GEO Weight:** 10%
**SEO Score:** 80/100 | **GEO Score:** 65/100

#### ✅ Strengths:
- 4 schema types implemented (SoftwareApplication, FAQPage, Organization, WebSite)
- All schemas valid JSON-LD format
- SoftwareApplication with AggregateRating (4.9/5, 127 reviews)
- FAQPage with 5 questions (good for AI understanding)
- Organization schema with founder details
- WebSite schema with SearchAction

**Evidence:**
```json
{
  "@type": "SoftwareApplication",
  "aggregateRating": {
    "ratingValue": "4.9",
    "ratingCount": "127"
  }
}
```

#### ℹ️ Informational:
**FAQPage Schema**
- Status: Restricted for Google rich results (gov/healthcare only since Aug 2023)
- Recommendation: **KEEP** — AI search engines (ChatGPT, Perplexity, Claude, Gemini) actively use FAQPage for content understanding
- No penalty risk from Google

#### ⚠️ Warnings:
**Entity Linking (GEO Critical)**
- Only 1 `sameAs` link: LinkedIn founder profile
- Missing: Wikipedia, Wikidata, Crunchbase, Product Hunt, G2, Trustpilot
- Target: 5+ sameAs links for strong entity recognition

**Missing Properties**
- No `speakable` property for voice search optimization
- No `knowsAbout` for founder expertise
- No `jobTitle` for founder
- Missing `dateModified` on content (AI freshness signal)

**Impact:** [GEO] Limited entity linking severely reduces AI search visibility. FAQPage helps but needs more authority signals.

---

### 5. Social Signals
**SEO Weight:** 5%
**SEO Score:** 85/100

#### ✅ Strengths:
- Complete Open Graph tags (7/7 core tags)
- Complete Twitter Card tags (4/4 core tags)
- Consistent titles and descriptions across platforms

**Evidence:**
```json
"og_tags": {
  "og:type": "website",
  "og:title": "PhotoRefix - Fast Batch Photo Editing with AI",
  "og:description": "Process multiple photos simultaneously...",
  "og:image": "/og.jpg",
  "og:site_name": "PhotoRefix"
}
```

#### ⚠️ Warnings:
- `og:image` is relative path (should be `https://photorefix.com/og.jpg`)
- Missing `og:image:width` and `og:image:height`

**Impact:** [SEO] Minor — most platforms will resolve relative paths, but absolute URLs are best practice.

---

### 6. AI Citability
**GEO Weight:** 25%
**GEO Score:** 30/100 🔴

#### 🔴 Critical Issues:
**Citability Analysis (19 content blocks analyzed)**
- Average citability score: **32.9/100** (Poor)
- Grade distribution:
  - A (90-100): 0 blocks
  - B (70-89): 0 blocks
  - C (50-69): 1 block
  - D (30-49): 6 blocks
  - F (0-29): 12 blocks
- **Zero passages in optimal length** (134-167 words for AI citation)

**Evidence:**
```json
"average_citability_score": 32.9,
"optimal_length_passages": 0,
"grade_distribution": {"A": 0, "B": 0, "C": 1, "D": 6, "F": 12}
```

**Top Citable Block (Still Only "C" Grade):**
- Heading: "10X Upscaler"
- Score: 53/100 (Moderate Citability)
- Word count: 38 words (too short)
- Issues: No statistics, weak self-containment

**Why Content Fails Citability:**
1. **Too promotional** — focuses on features, not information
2. **No statistics** — lacks data points AI can cite
3. **Too short** — most blocks <40 words, optimal is 134-167
4. **Not self-contained** — requires context to understand
5. **No unique insights** — generic feature descriptions

**Impact:** [GEO] **CRITICAL** — AI search engines cannot extract quotable passages. This is the #1 blocker for GEO visibility.

---

### 7. Brand Authority
**GEO Weight:** 20%
**GEO Score:** 25/100 🔴

#### 🔴 Critical Issues:
**Platform Presence Analysis**

**Wikipedia/Wikidata (20% weight)**
- ❌ No Wikipedia page
- ❌ No Wikidata entry
- ❌ Not cited in any Wikipedia articles
- Impact: Missing the highest-correlation authority signal

**YouTube (25% weight, correlation: 0.737)**
- ❌ No official YouTube channel
- ❌ No tutorial or demo videos
- ❌ No customer review videos
- Impact: Missing strongest brand mention correlation

**Reddit (25% weight)**
- ❌ No subreddit (r/photorefix)
- ❌ No mentions in relevant subreddits
- ❌ No official Reddit presence
- Impact: Missing authentic community discussions

**LinkedIn (15% weight)**
- ✅ Founder has LinkedIn profile (in schema)
- ❌ No company LinkedIn page
- ❌ No employee thought leadership
- Impact: Partial presence, needs company page

**Review Platforms (15% weight)**
- ❌ Not on G2
- ❌ Not on Trustpilot
- ❌ Not on Capterra
- ❌ Not on Product Hunt
- Impact: Missing social proof signals

**Evidence:**
```json
"sameAs": ["https://www.linkedin.com/in/alex-may-photorefix/"]
```
Only 1 sameAs link — need 5+ for strong authority.

**Impact:** [GEO] **CRITICAL** — Brand mentions correlate 3× more strongly with AI visibility than backlinks (Ahrefs Dec 2025). Zero presence = zero authority.

---

### 8. AI Crawler Access
**GEO Weight:** 10%
**GEO Score:** 70/100

#### ✅ Strengths:
- robots.txt exists and accessible (200 status)
- 8 AI crawlers explicitly allowed with full access
- llms.txt file exists at `/llms.txt`
- Sitemap properly declared

**Evidence:**
```json
"ai_crawler_status": {
  "GPTBot": "explicitly allowed",
  "ChatGPT-User": "explicitly allowed",
  "Google-Extended": "explicitly allowed",
  "PerplexityBot": "explicitly allowed",
  "anthropic-ai": "explicitly allowed",
  "Amazonbot": "explicitly allowed"
}
```

#### ⚠️ Warnings:
**llms.txt Quality (45/100)**
- ✅ Title present: "PhotoRefix - Fast Batch Photo Editing with AI"
- ❌ Missing description (> blockquote)
- ❌ No links to key pages
- ❌ Sections defined but empty (About, Tools, Offers, Links)

**Evidence:**
```
# PhotoRefix - Fast Batch Photo Editing with AI

## About
[empty]

## Tools
[empty]

## Links
[empty]
```

**Missing AI Crawler Rules**
- ClaudeBot (not managed)
- Applebot-Extended (not managed)
- Bytespider (not managed)
- FacebookBot (not managed)

**Impact:** [GEO] Good foundation but incomplete. llms.txt needs content to guide AI understanding.

---

### 9. Performance (Core Web Vitals)
**SEO Weight:** 10%
**SEO Score:** N/A (Cannot assess)

#### ⚠️ Environment Limitation:
PageSpeed Insights API rate limited. Cannot assess:
- Largest Contentful Paint (LCP)
- Interaction to Next Paint (INP)
- Cumulative Layout Shift (CLS)

**Evidence:**
```json
"error": "Rate limited by Google API. Wait a few minutes or add an API key."
```

**Recommendation:** Add PageSpeed API key or manually check at https://pagespeed.web.dev/

**Impact:** [SEO] Cannot score — assumed neutral (70/100) for calculation purposes.

---

### 10. Platform Optimization
**GEO Weight:** 5%
**GEO Score:** 40/100

#### ⚠️ Warnings:
- No specific optimization for Google AI Overviews
- No optimization for ChatGPT web search
- No optimization for Perplexity AI
- No optimization for Bing Copilot
- Generic content not tailored for AI consumption

**Impact:** [GEO] Basic presence but no platform-specific optimization.

---

## Confidence Levels

| Finding | Confidence | Method |
|---------|-----------|--------|
| Security headers missing | ✅ Confirmed | Script-verified (security_headers.py) |
| Heading spacing issues | ✅ Confirmed | Script-verified (parse_html.py) |
| AI citability score 33/100 | ✅ Confirmed | Script-verified (citability_scorer.py) |
| Zero brand authority presence | ✅ Confirmed | Script-verified (brand_scanner.py) |
| llms.txt incomplete | ✅ Confirmed | Script-verified (llms_txt_checker.py) |
| FAQPage schema present | ✅ Confirmed | Script-verified (schema_validator.py) |
| Readability 45.6 Flesch | ✅ Confirmed | Script-verified (readability.py) |
| 3 orphan pages | ✅ Confirmed | Script-verified (internal_links.py) |
| Core Web Vitals | ⚠️ Hypothesis | API rate limited, needs manual check |

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| Pages Crawled | 21 |
| Total Internal Links | 305 |
| Broken Links | 0 |
| Schema Types | 4 |
| AI Crawlers Allowed | 8 |
| Security Headers Present | 1/6 |
| Citability Grade | F (32.9/100) |
| Brand Authority Platforms | 1/10 |
| Word Count | 843 |
| Flesch Reading Ease | 45.6 |

---

## Next Steps

See **SGEO-ACTION-PLAN.md** for prioritized fixes with effort estimates and impact ratings.
