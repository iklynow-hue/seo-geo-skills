# FAQPage Schema Guidance for SGEO Audits

**Last Updated:** March 12, 2026
**Status:** Active Policy

---

## The Controversy

### Google's Position (August 2023)
Google restricted FAQPage rich results to **government and healthcare authority sites only**.

**What this means:**
- Commercial sites won't get FAQ rich snippets in Google Search
- The schema is still valid and won't cause penalties
- Google simply ignores it for rich result display

**Official Google Statement:**
> "We're limiting FAQ rich results to well-known, authoritative government and health websites."

### AI Search Engines' Position (2024-2026)
AI-powered search systems (ChatGPT, Perplexity, Claude, Gemini, Google AI Overviews) **actively use FAQPage schema** for:
- Content understanding and entity recognition
- Question-answer extraction for citations
- Voice search optimization
- Featured snippet selection (even without rich results)
- Training data for answer generation

**Research Evidence:**
- 45% of AI-cited passages come from structured Q&A content (Wellows, 2025)
- FAQPage schema increases AI citation likelihood by 3.2x (HashMeta, 2025)
- Voice assistants prioritize FAQPage-marked content for spoken answers

---

## SGEO Policy: KEEP IT

**Official Stance:** ✅ **KEEP FAQPage schema for GEO benefits**

### Reasoning

| Factor | Analysis |
|--------|----------|
| **Google Penalty Risk** | ❌ None — Google ignores, doesn't penalize |
| **AI Search Value** | ✅ High — All major AI systems use it |
| **Schema.org Status** | ✅ Active (not deprecated) |
| **Voice Search** | ✅ Improves voice assistant understanding |
| **Featured Snippets** | ✅ Still helps with snippet selection |
| **Entity Recognition** | ✅ Helps AI build knowledge graphs |
| **Citation Likelihood** | ✅ 3.2x increase in AI citations |

### Trade-off Analysis

**What you LOSE by removing FAQPage:**
- AI search visibility (GEO Score impact: -5 to -10 points)
- Voice search optimization
- Entity graph signals
- Featured snippet eligibility (non-rich result)
- Structured Q&A understanding

**What you GAIN by removing FAQPage:**
- Nothing (Google already ignores it)

**Conclusion:** The cost of removal far exceeds any benefit.

---

## Implementation Guidelines

### Correct Usage

```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "How long does shipping take?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Standard shipping takes 3-5 business days. Express shipping delivers within 1-2 business days."
      }
    },
    {
      "@type": "Question",
      "name": "What is your return policy?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "We offer 30-day returns on all items. Products must be unused and in original packaging."
      }
    }
  ]
}
```

### Best Practices

1. **Match on-page content** — Every question/answer in schema must appear visibly on the page
2. **Use natural language** — Write questions as users would ask them
3. **Provide complete answers** — Don't truncate or summarize in schema
4. **Avoid promotional content** — Focus on informational Q&A, not sales pitches
5. **Minimum 2 Q&A pairs** — Single Q&A should use QAPage instead
6. **Maximum 50 Q&A pairs** — Beyond this, split into multiple pages

### Invalid Use Cases (Don't Do This)

❌ **Forum pages** where users can submit answers → Use QAPage instead
❌ **Product support pages** with user-submitted answers → Use QAPage instead
❌ **Advertising/promotional Q&A** → No schema
❌ **Hidden content** not visible on page → Violates Google guidelines
❌ **Duplicate questions** across multiple pages → Consolidate

---

## Reporting Guidelines

When FAQPage schema is detected in an SGEO audit, include this note:

### For Full Audits (SGEO-AUDIT-REPORT.md)

```markdown
### FAQPage Schema Detected

**Status:** ✅ Present and valid
**Google Rich Results:** ❌ Restricted to gov/healthcare sites (Aug 2023)
**AI Search Engines:** ✅ Actively used by ChatGPT, Perplexity, Claude, Gemini

**Impact:**
- [GEO] Improves AI citation likelihood by 3.2x
- [GEO] Enhances voice search optimization
- [GEO] Strengthens entity recognition signals
- [SEO] No Google rich results, but helps featured snippets

**Recommendation:** ✅ **KEEP** for GEO benefits. Accept that Google won't show rich results.

**Note:** This is NOT a penalty risk. Google simply ignores FAQPage for commercial sites but doesn't penalize its presence.
```

### For Action Plans (SGEO-ACTION-PLAN.md)

Do NOT include "Remove FAQPage schema" as an action item.

If the user specifically asks about it, include this:

```markdown
## FAQPage Schema — No Action Needed

**Current Status:** Present and valid
**User Question:** "Should I remove FAQPage schema?"
**Answer:** No. Keep it for AI search benefits.

**Explanation:**
While Google restricts FAQ rich results to gov/healthcare sites, AI search engines (ChatGPT, Perplexity, Claude, Gemini) actively use FAQPage schema for content understanding and citations. Removing it would hurt your GEO Score with no SEO benefit.

**Trade-off:**
- Remove: Lose AI visibility, gain nothing
- Keep: Maintain AI visibility, accept no Google rich results

**Recommendation:** Keep FAQPage schema.
```

---

## Comparison with Other Q&A Schema

| Schema Type | Use Case | Google Rich Results | AI Search Value |
|-------------|----------|---------------------|-----------------|
| **FAQPage** | Site-authored Q&A, no user submissions | ❌ Gov/healthcare only | ✅ High |
| **QAPage** | User-submitted answers (forums, support) | ✅ Available | ✅ Medium |
| **HowTo** | Step-by-step instructions | ❌ Deprecated (Sept 2023) | ⚠️ Low |

**Key Distinction:**
- FAQPage = Company writes both Q&A (like a help center)
- QAPage = Users submit answers (like Stack Overflow)

---

## Historical Context

### Timeline

| Date | Event |
|------|-------|
| 2019 | Google launches FAQ rich results |
| 2020-2022 | Widespread adoption, some spam abuse |
| Aug 2023 | Google restricts to gov/healthcare only |
| 2024-2025 | AI search engines continue using FAQPage |
| Mar 2026 | SGEO policy: Keep for GEO benefits |

### Why Google Restricted It

Google's stated reasons:
1. **Spam abuse** — Sites creating fake FAQs to dominate SERPs
2. **Quality concerns** — Low-quality Q&A content
3. **SERP clutter** — Too many FAQ snippets crowding results

**Important:** This was a **rich result restriction**, not a schema deprecation. The schema itself remains valid and useful.

---

## Competitor Analysis

### What Others Are Doing

**Sites that removed FAQPage after Aug 2023:**
- Lost AI search visibility
- No SEO benefit gained
- Regretted the decision

**Sites that kept FAQPage:**
- Maintained AI citation rates
- No Google penalty
- Better voice search performance

**Recommendation:** Follow the "keep it" strategy.

---

## Future-Proofing

### What If Google Changes Policy Again?

**Scenario 1:** Google re-enables FAQPage for all sites
- ✅ You're already compliant and ready

**Scenario 2:** Google deprecates FAQPage entirely
- ⚠️ AI search engines will likely continue using it
- ⚠️ Easy to remove later if truly deprecated

**Scenario 3:** Status quo continues
- ✅ You maintain AI search advantage

**Conclusion:** Keeping FAQPage is the low-risk, high-reward strategy.

---

## References

- Google Search Central: FAQ Structured Data Guidelines
- Schema.org: FAQPage Specification
- Wellows Research: AI Citation Patterns (2025)
- HashMeta: E-E-A-T Framework for AI Search (2025)
- SEOTuners: AI SEO Audit Checklist (2025)

---

**Policy Status:** ✅ Active
**Next Review:** June 2026 (or when Google announces policy changes)
