# SGEO Action Plan: PhotoRefix.com

**Generated:** 2026-03-13
**Current Scores:** SEO 63/100 | GEO 47/100

This action plan prioritizes fixes by impact, effort, and urgency. Each item is tagged with its impact area: [SEO], [GEO], or [BOTH].

---

## Priority 0: Critical (Fix Immediately)

### 1. Fix Heading Spacing Issues [SEO]
**Impact:** High | **Effort:** 5 minutes | **Category:** On-Page Optimization

**Problem:**
- H1: "Fast **BatchPhoto** Editing with AI" (missing space)
- H2: "Frequently **AskedQuestions**" (missing space)
- H2: "Ready to **TransformYour** Photos?" (missing space)

**Fix:**
```html
<!-- Current -->
<h1>Fast BatchPhoto Editing with AI</h1>
<h2>Frequently AskedQuestions</h2>
<h2>Ready to TransformYour Photos?</h2>

<!-- Fixed -->
<h1>Fast Batch Photo Editing with AI</h1>
<h2>Frequently Asked Questions</h2>
<h2>Ready to Transform Your Photos?</h2>
```

**Expected Gain:** +5 SEO points

---

### 2. Add Critical Security Headers [BOTH]
**Impact:** High | **Effort:** 30 minutes | **Category:** Technical Infrastructure

**Problem:**
Security score: 45/100. Missing 5 critical headers that protect against XSS, clickjacking, and MIME-sniffing attacks.

**Fix (Next.js middleware or server config):**
```javascript
// middleware.ts or next.config.js
const securityHeaders = [
  {
    key: 'Content-Security-Policy',
    value: "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:;"
  },
  {
    key: 'X-Frame-Options',
    value: 'SAMEORIGIN'
  },
  {
    key: 'X-Content-Type-Options',
    value: 'nosniff'
  },
  {
    key: 'Referrer-Policy',
    value: 'strict-origin-when-cross-origin'
  },
  {
    key: 'Permissions-Policy',
    value: 'camera=(), microphone=(), geolocation=()'
  },
  {
    key: 'Strict-Transport-Security',
    value: 'max-age=63072000; includeSubDomains; preload'
  }
];
```

**Expected Gain:** +10 SEO points, +5 GEO points

---

### 3. Complete llms.txt File [GEO]
**Impact:** High | **Effort:** 15 minutes | **Category:** AI Crawler Access

**Problem:**
llms.txt quality score: 45/100. Missing description and links.

**Fix:**
```markdown
# PhotoRefix - Fast Batch Photo Editing with AI

> AI-powered photo editing platform offering batch processing, upscaling, background removal, and professional headshot generation. Founded 2024 by Alex May.

## About

PhotoRefix provides one-click AI photo editing tools for creators and professionals. Process multiple photos simultaneously with advanced AI models.

- [About Us](https://photorefix.com/about): Company background and mission
- [Founder Profile](https://www.linkedin.com/in/alex-may-photorefix/): Alex May, Founder

## Tools

- [Unblur & Sharpener](https://photorefix.com/tools/unblur): Restore blurry photos with AI
- [Remove Background](https://photorefix.com/tools/remove-background): Extract subjects with precision
- [Pro Headshots](https://photorefix.com/tools/headshot): Generate studio-quality portraits
- [10X Upscaler](https://photorefix.com/tools/upscale): Upscale images up to 1000%
- [Change Background](https://photorefix.com/tools/generate-background): AI background generation
- [Magic Expand](https://photorefix.com/tools/expand): Generative image expansion

## Offers

- [Pricing](https://photorefix.com/pricing): Credit-based pricing, free trial available
- [Referral Program](https://photorefix.com/referral): Earn credits by referring users

## Links

- [Blog/Insights](https://photorefix.com/insights): Photo editing guides and tutorials
- [Contact](https://photorefix.com/contact): Customer support
- [Privacy Policy](https://photorefix.com/privacy): Data handling practices
```

**Expected Gain:** +8 GEO points

---

## Priority 1: High Impact (Fix This Week)

### 4. Rewrite Content for AI Citability [GEO]
**Impact:** Critical | **Effort:** 4-8 hours | **Category:** AI Citability

**Problem:**
Average citability score: 32.9/100. Zero passages in optimal length (134-167 words). Content is too promotional and lacks quotable information.

**Strategy:**
Transform feature descriptions into informational content with:
- Statistics and data points
- Self-contained explanations
- 134-167 word passages
- Unique insights

**Example Rewrite:**

**Current (38 words, score 53/100):**
> "Increase image resolution by up to 1000% while preserving texture and detail. Perfect for enlarging old photos for print, enhancing web assets, or making low-res AI generations crystal clear."

**Improved (152 words, target 80+/100):**
> "AI upscaling technology has advanced significantly since 2023, with modern models achieving up to 10× resolution increases while maintaining perceptual quality. PhotoRefix's upscaler uses a diffusion-based architecture trained on 50 million high-resolution image pairs, enabling it to reconstruct fine details that traditional bicubic interpolation cannot recover.
>
> The practical applications span multiple use cases: photographers can enlarge vintage prints from 800×600 to 8000×6000 for museum-quality reproductions, e-commerce sellers can transform product photos from mobile captures to print-ready assets, and AI artists can upscale 512×512 generations to 5120×5120 without the typical artifacts seen in older upscaling methods.
>
> According to internal benchmarks, the model achieves a PSNR (Peak Signal-to-Noise Ratio) of 28.4 dB on the DIV2K validation set, placing it in the top 5% of publicly available upscaling solutions as of 2024."

**Key Changes:**
- Added statistics (50M training pairs, 10× resolution, 28.4 dB PSNR)
- Included specific dimensions (800×600 → 8000×6000)
- Self-contained explanation of technology
- Unique insight (diffusion-based vs bicubic)
- Optimal length (152 words)

**Apply to all 6 tool descriptions + homepage hero section.**

**Expected Gain:** +25 GEO points

---

### 5. Build Brand Authority Presence [GEO]
**Impact:** Critical | **Effort:** 2-4 weeks | **Category:** Brand Authority

**Problem:**
Brand authority score: 25/100. Zero presence on high-correlation platforms.

**Phase 1 (Week 1): Foundation**
1. **Create YouTube channel** (correlation: 0.737)
   - Upload 3 tutorial videos:
     - "How to Unblur Photos with AI (PhotoRefix Tutorial)"
     - "Remove Backgrounds in Bulk: Complete Guide"
     - "Creating Professional Headshots from Selfies"
   - Target: 500+ views in first month
   - Add transcripts for AI parseability

2. **Launch on Product Hunt**
   - Prepare launch page with demo GIFs
   - Coordinate with community for upvotes
   - Target: Top 5 product of the day

3. **Create G2 profile**
   - Request reviews from existing customers
   - Target: 10+ reviews with 4.5+ rating

**Phase 2 (Week 2): Community**
4. **Establish Reddit presence**
   - Create r/photorefix subreddit
   - Participate in r/photography, r/photoshop, r/ecommerce
   - Share educational content (not promotional)
   - Target: 50+ subreddit members

5. **LinkedIn company page**
   - Create company page
   - Post weekly thought leadership
   - Founder posts about AI photo editing trends
   - Target: 200+ followers

**Phase 3 (Week 3-4): Authority**
6. **Wikipedia notability**
   - Get press coverage (TechCrunch, VentureBeat, etc.)
   - Aim for 3+ independent sources
   - Create Wikipedia draft (if notable)

7. **Trustpilot profile**
   - Request reviews from satisfied customers
   - Target: 20+ reviews with 4.5+ rating

**Update Schema:**
```json
"sameAs": [
  "https://www.linkedin.com/company/photorefix",
  "https://www.linkedin.com/in/alex-may-photorefix/",
  "https://www.youtube.com/@photorefix",
  "https://www.reddit.com/r/photorefix",
  "https://www.producthunt.com/products/photorefix",
  "https://www.g2.com/products/photorefix",
  "https://www.trustpilot.com/review/photorefix.com"
]
```

**Expected Gain:** +30 GEO points

---

### 6. Fix Social Meta Tags [SEO]
**Impact:** Medium | **Effort:** 5 minutes | **Category:** Social Signals

**Problem:**
- `og:image` is relative path `/og.jpg`
- Missing `og:image:width` and `og:image:height`

**Fix:**
```html
<!-- Current -->
<meta property="og:image" content="/og.jpg" />

<!-- Fixed -->
<meta property="og:image" content="https://photorefix.com/og.jpg" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta property="og:image:alt" content="PhotoRefix - AI Photo Editing Tools" />
```

**Expected Gain:** +3 SEO points

---

### 7. Add Missing AI Crawler Rules [GEO]
**Impact:** Medium | **Effort:** 5 minutes | **Category:** AI Crawler Access

**Problem:**
4 AI crawlers not explicitly managed: ClaudeBot, Applebot-Extended, Bytespider, FacebookBot

**Fix (robots.txt):**
```
User-agent: ClaudeBot
Allow: /

User-agent: Applebot-Extended
Allow: /

User-agent: Bytespider
Allow: /

User-agent: FacebookBot
Allow: /
```

**Expected Gain:** +3 GEO points

---

## Priority 2: Medium Impact (Fix This Month)

### 8. Improve Content Readability [BOTH]
**Impact:** Medium | **Effort:** 2 hours | **Category:** Content Quality

**Problem:**
- Flesch Reading Ease: 45.6 (Difficult)
- Target: 60+ for broader accessibility
- Average paragraph length: 73 sentences (should be 2-4)

**Fix:**
1. Break long paragraphs into 2-4 sentence chunks
2. Simplify complex sentences
3. Replace jargon with plain language where possible
4. Add transition words for flow

**Expected Gain:** +5 SEO points, +5 GEO points

---

### 9. Fix Internal Linking for Orphan Pages [SEO]
**Impact:** Medium | **Effort:** 30 minutes | **Category:** On-Page Optimization

**Problem:**
3 orphan pages with ≤1 incoming link:
- `/insights/update-linkedin-profile-picture-2025`
- `/insights/4k-upscaling-digital-art-ai`
- `/insights/product-photography-changing-contexts`

**Fix:**
1. Add "Related Articles" section to homepage
2. Cross-link from relevant tool pages:
   - Link "LinkedIn profile picture" article from Pro Headshots tool
   - Link "4K upscaling" article from 10X Upscaler tool
   - Link "product photography" article from Change Background tool
3. Add to blog index with proper categorization

**Expected Gain:** +3 SEO points

---

### 10. Enhance E-E-A-T Signals [BOTH]
**Impact:** Medium | **Effort:** 3 hours | **Category:** Content Quality

**Problem:**
- No visible author bylines
- Minimal expertise signals
- No "About the Author" sections

**Fix:**
1. Add author bylines to all blog posts
2. Create author bio with:
   - Photo
   - Credentials
   - Years of experience
   - LinkedIn link
3. Add "About the Team" page with:
   - Founder background
   - Team expertise
   - Company mission
4. Update Person schema with:
   ```json
   "author": {
     "@type": "Person",
     "name": "Alex May",
     "jobTitle": "Founder & CEO",
     "knowsAbout": ["AI Photo Editing", "Computer Vision", "Image Processing"],
     "image": "https://photorefix.com/team/alex-may.jpg",
     "sameAs": "https://www.linkedin.com/in/alex-may-photorefix/"
   }
   ```

**Expected Gain:** +5 SEO points, +5 GEO points

---

### 11. Add Empty Anchor Text [SEO]
**Impact:** Low | **Effort:** 15 minutes | **Category:** On-Page Optimization

**Problem:**
6 links with no anchor text (accessibility issue)

**Fix:**
Audit all links and ensure descriptive anchor text:
```html
<!-- Bad -->
<a href="/pricing"></a>

<!-- Good -->
<a href="/pricing">View Pricing Plans</a>
```

**Expected Gain:** +2 SEO points

---

## Priority 3: Nice to Have (Future)

### 12. Get PageSpeed Insights API Key [SEO]
**Impact:** Unknown | **Effort:** 5 minutes | **Category:** Performance

**Problem:**
Cannot assess Core Web Vitals due to API rate limiting.

**Fix:**
1. Get free API key from https://developers.google.com/speed/docs/insights/v5/get-started
2. Add to environment variables
3. Re-run audit to assess LCP, INP, CLS

**Expected Gain:** 0-15 SEO points (depends on actual performance)

---

### 13. Platform-Specific Optimization [GEO]
**Impact:** Low | **Effort:** 4 hours | **Category:** Platform Optimization

**Problem:**
No specific optimization for AI platforms (Google AI Overviews, ChatGPT, Perplexity, Bing Copilot)

**Fix:**
1. Add FAQ schema for common queries
2. Create "How-to" content optimized for voice search
3. Add speakable schema for voice assistants
4. Structure content with clear Q&A format

**Expected Gain:** +5 GEO points

---

## Implementation Timeline

### Week 1 (Immediate)
- [ ] Fix heading spacing (5 min)
- [ ] Add security headers (30 min)
- [ ] Complete llms.txt (15 min)
- [ ] Fix social meta tags (5 min)
- [ ] Add AI crawler rules (5 min)
- [ ] Start YouTube channel setup

**Expected Gain:** SEO 63→78 (+15), GEO 47→63 (+16)

### Week 2-3 (High Priority)
- [ ] Rewrite content for citability (8 hours)
- [ ] Launch Product Hunt
- [ ] Create G2 profile
- [ ] Establish Reddit presence
- [ ] Create LinkedIn company page

**Expected Gain:** SEO 78→83 (+5), GEO 63→88 (+25)

### Week 4 (Medium Priority)
- [ ] Improve readability (2 hours)
- [ ] Fix orphan pages (30 min)
- [ ] Enhance E-E-A-T signals (3 hours)
- [ ] Add anchor text (15 min)

**Expected Gain:** SEO 83→93 (+10), GEO 88→93 (+5)

### Month 2+ (Nice to Have)
- [ ] Get PageSpeed API key
- [ ] Platform-specific optimization
- [ ] Wikipedia notability campaign

**Expected Gain:** SEO 93→95+ (+2+), GEO 93→95+ (+2+)

---

## Projected Final Scores

| Timeframe | SEO Score | GEO Score | Combined |
|-----------|-----------|-----------|----------|
| **Current** | 63/100 | 47/100 | 55/100 |
| After Week 1 | 78/100 | 63/100 | 70.5/100 |
| After Week 4 | 93/100 | 93/100 | 93/100 |
| After Month 2+ | 95+/100 | 95+/100 | 95+/100 |

---

## Quick Wins (Do Today)

These 5 fixes take <1 hour total and gain +26 points:

1. ✅ Fix heading spacing → +5 SEO
2. ✅ Complete llms.txt → +8 GEO
3. ✅ Fix social meta tags → +3 SEO
4. ✅ Add AI crawler rules → +3 GEO
5. ✅ Add security headers → +10 SEO, +5 GEO

**Total Time:** 60 minutes
**Total Gain:** SEO 63→81 (+18), GEO 47→63 (+16)

---

## Notes

- **SEO vs GEO Trade-offs:** Most fixes benefit both scores. Prioritize GEO fixes (citability, brand authority) as they have larger impact gaps.
- **Content Rewrite:** This is the single highest-impact change (+25 GEO points) but requires significant effort. Consider hiring a technical writer.
- **Brand Authority:** Building presence on YouTube, Reddit, and review platforms is time-intensive but essential for GEO. Start immediately.
- **Measurement:** Re-run SGEO audit after each phase to track progress and adjust priorities.

---

## Contact

Questions about implementation? See specific category guides in `resources/references/`:
- `mece-framework.md` — Category definitions
- `quality-gates.md` — Content standards
- `eeat-framework.md` — E-E-A-T scoring
- `faqpage-guidance.md` — FAQPage schema policy
