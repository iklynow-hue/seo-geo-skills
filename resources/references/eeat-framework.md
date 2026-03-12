# E-E-A-T Framework for SGEO Audits

<!-- Updated: 2026-03-12 -->

## Overview

E-E-A-T = Experience, Expertise, Authoritativeness, Trustworthiness

As of December 2025, E-E-A-T applies to ALL competitive queries, not just YMYL.
Both SEO and GEO scoring use E-E-A-T, but with different emphasis.

---

## Scoring (0-100)

### Experience (0-25)

| Signal | Points | Detection |
|--------|--------|-----------|
| First-hand testing/usage described | 8 | LLM analysis |
| Case studies with measurable results | 8 | LLM analysis |
| Screenshots, videos, original images | 5 | parse_html.py |
| "We tested", "In our experience" language | 4 | LLM analysis |

### Expertise (0-25)

| Signal | Points | Detection |
|--------|--------|-----------|
| Author byline present | 5 | parse_html.py |
| Author bio with credentials | 5 | parse_html.py |
| Author page exists | 5 | internal_links.py |
| Technical depth (specific, not generic) | 5 | LLM analysis |
| Certifications/qualifications mentioned | 5 | LLM analysis |

### Authoritativeness (0-25)

| Signal | Points | Detection |
|--------|--------|-----------|
| External citations (≥3 authoritative sources) | 8 | citability_scorer.py |
| Cited by others (backlinks from authority sites) | 7 | brand_scanner.py |
| Industry recognition (awards, features) | 5 | brand_scanner.py |
| Wikipedia/Wikidata presence | 5 | brand_scanner.py |

### Trustworthiness (0-25)

| Signal | Points | Detection |
|--------|--------|-----------|
| HTTPS active | 5 | security_headers.py |
| Privacy policy present | 3 | internal_links.py |
| Contact information visible | 3 | parse_html.py |
| Terms of service present | 2 | internal_links.py |
| Transparent about limitations | 4 | LLM analysis |
| Content freshness (dateModified) | 4 | parse_html.py |
| No deceptive patterns | 4 | LLM analysis |

---

## SEO vs GEO Emphasis

### SEO E-E-A-T Focus
- Author credentials and site authority
- Backlink profile quality
- Content freshness signals
- YMYL compliance (if applicable)

### GEO E-E-A-T Focus
- First-hand experience signals (AI systems value original insights)
- Verifiable expertise (credentials AI can validate)
- Third-party validation (Wikipedia, reviews, press)
- Source attribution (external citations AI can follow)

---

## YMYL Categories

Your Money or Your Life topics require HIGHEST E-E-A-T standards:

- Health and medical information
- Financial advice and transactions
- Legal information
- News and current events
- Safety information
- Government/civic information

For YMYL content, minimum E-E-A-T score should be 70/100.
For non-YMYL, minimum 40/100 is acceptable.
