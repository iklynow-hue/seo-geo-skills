# Schema Types Reference

<!-- Updated: 2026-03-12 -->

## Active & Recommended

| Schema Type | SEO Value | GEO Value | Notes |
|-------------|-----------|-----------|-------|
| **Organization** | ✅ High | ✅ High | Required. Include sameAs links. |
| **WebSite** | ✅ High | ✅ Medium | Include SearchAction for site search. |
| **BreadcrumbList** | ✅ High | ✅ Low | Helps navigation understanding. |
| **Article** | ✅ High | ✅ High | Include author, datePublished, dateModified. |
| **BlogPosting** | ✅ High | ✅ High | Subtype of Article. |
| **Product** | ✅ High | ✅ Medium | Include offers, aggregateRating. |
| **SoftwareApplication** | ✅ High | ✅ High | For SaaS/tools. Include offers, rating. |
| **FAQPage** | ⚠️ Restricted | ✅ High | **KEEP for GEO**. Google restricts rich results to gov/healthcare. |
| **QAPage** | ✅ Medium | ✅ Medium | For user-submitted Q&A (forums). |
| **Person** | ✅ Medium | ✅ High | For author pages. Include sameAs. |
| **LocalBusiness** | ✅ High | ✅ Low | For local businesses. Include address, hours. |
| **Event** | ✅ High | ✅ Low | For events. Include startDate, location. |
| **Recipe** | ✅ High | ✅ Low | For recipes. Include ingredients, instructions. |
| **VideoObject** | ✅ High | ✅ High | For embedded videos. Include uploadDate, duration. |
| **ImageObject** | ✅ Low | ✅ Medium | For key images. Include contentUrl, license. |
| **Review** | ✅ High | ✅ Medium | For product/service reviews. |
| **AggregateRating** | ✅ High | ✅ Medium | Summary of reviews. |

## Deprecated / Restricted

| Schema Type | Status | Action |
|-------------|--------|--------|
| **HowTo** | ❌ Deprecated (Sept 2023) | Remove. No rich results. |
| **FAQPage** | ⚠️ Restricted (Aug 2023) | **KEEP for GEO**. No Google rich results for commercial sites. |
| **Book Actions** | ❌ Deprecated (June 2025) | Remove. |
| **Course Info** | ❌ Deprecated (June 2025) | Remove. |
| **Estimated Salary** | ❌ Deprecated (June 2025) | Remove. |
| **ClaimReview** | ❌ Deprecated (June 2025) | Remove. |
| **Learning Video** | ❌ Deprecated (June 2025) | Remove. |
| **Special Announcement** | ❌ Deprecated (June 2025) | Remove. |
| **Vehicle Listing** | ❌ Deprecated (June 2025) | Remove. |
| **Practice Problem** | ❌ Deprecated (Nov 2025) | Remove. |

## GEO-Specific Properties

These properties enhance AI search visibility:

| Property | Schema Types | GEO Value | Notes |
|----------|--------------|-----------|-------|
| **sameAs** | Organization, Person | ✅ Critical | ≥5 links for GEO (Wikipedia, LinkedIn, Twitter, YouTube, etc.) |
| **speakable** | Article, WebPage | ✅ High | Marks content for voice assistants. |
| **dateModified** | Article, BlogPosting | ✅ High | Signals content freshness to AI. |
| **author** | Article, BlogPosting | ✅ High | Links to Person schema for E-E-A-T. |
| **citation** | Article, ScholarlyArticle | ✅ High | External source attribution. |
| **about** | Article, WebPage | ✅ Medium | Links to Thing for entity recognition. |
| **mentions** | Article, WebPage | ✅ Medium | Links to Thing for entity graph. |

## Validation

- Use Google Rich Results Test: https://search.google.com/test/rich-results
- Use Schema.org Validator: https://validator.schema.org/
- Check for placeholder text ("Your Company", "example.com")
- Verify all required properties are present
- Ensure JSON-LD syntax is valid (no trailing commas, proper escaping)

## Common Mistakes

❌ Using Microdata or RDFa (use JSON-LD only)
❌ Placeholder text in schema
❌ Missing required properties
❌ Deprecated types still present
❌ Schema doesn't match visible content
❌ Invalid JSON syntax
❌ Only 1-2 sameAs links (need ≥5 for GEO)
