# SEO GEO Site Audit Report Template

## Audit Snapshot

- **Target:** [domain or URL]
- **Mode:** [Fast / Template / Full / Deep]
- **Output style:** [Boss / Operator / Specialist]
- **Crawl cap:** [N]
- **Pages sampled:** [N]
- **PageSpeed URLs tested:** [list]
- **Confidence:** [High / Medium / Low]

## Executive Summary

- **Overall score:** [0-100] — [band]
- **Technical SEO:** [score]
- **On-page SEO:** [score]
- **IA & internal linking:** [score]
- **GEO & AI extractability:** [score]
- **EEAT & trust:** [score]
- **Entity & structured data:** [score]
- **Performance & page experience:** [score]

### Top wins

- [win]
- [win]
- [win]

### Top issues

- [issue]
- [issue]
- [issue]

## Scorecard

| Section | Section score (0-100) | Weight (%) | Contribution to total | Notes |
|---|---:|---:|---:|---|
| Technical SEO & Indexability |  | 20% |  |  |
| On-Page SEO & Content Packaging |  | 15% |  |  |
| Information Architecture & Internal Linking |  | 10% |  |  |
| GEO & AI Extractability |  | 20% |  |  |
| EEAT & Trust Signals |  | 15% |  |  |
| Entity & Structured Data |  | 10% |  |  |
| Performance & Page Experience |  | 10% |  |  |
| **Weighted overall** |  | **100%** |  |  |

## Raw vs Rendered Googlebot Evidence

Use this section when the site uses JavaScript rendering or when raw and rendered evidence differ.

| Signal | Raw Googlebot baseline | Rendered DOM simulation | Conclusion |
|---|---:|---:|---|
| Title |  |  |  |
| Meta description |  |  |  |
| Canonical |  |  |  |
| H1 |  |  |  |
| Body words |  |  |  |
| Internal links |  |  |  |
| JSON-LD |  |  |  |

Interpretation rules:

- If raw is missing and rendered is present, call it a JS dependency risk.
- If both raw and rendered are missing, call it a true missing-signal issue.
- If rendered links are present but raw links are absent, mark them as rendered-discoverable, not raw-crawlable.
- If only DOM route hints or route guesses expose a page, do not present that route as search-discoverable.

## Section Findings

### 1. Technical SEO & Indexability — [score]

**Passed items**

- [pass]
- [pass]

**Issues**

- **[P?] [issue]** — [why it matters]

**Evidence**

- [url or pattern]

**Recommended actions**

- [action]

### 2. On-Page SEO & Content Packaging — [score]

**Passed items**

- [pass]

**Issues**

- **[P?] [issue]** — [why it matters]

**Evidence**

- [evidence]

**Recommended actions**

- [action]

### 3. Information Architecture & Internal Linking — [score]

**Passed items**

- [pass]

**Issues**

- **[P?] [issue]** — [why it matters]

**Evidence**

- [evidence]

**Recommended actions**

- [action]

### 4. GEO & AI Extractability — [score]

**Passed items**

- [pass]

**Issues**

- **[P?] [issue]** — [why it matters]

**Evidence**

- [evidence]

**Recommended actions**

- [action]

### 5. EEAT & Trust Signals — [score]

**Passed items**

- [pass]

**Issues**

- **[P?] [issue]** — [why it matters]

**Evidence**

- [evidence]

**Recommended actions**

- [action]

### 6. Entity & Structured Data — [score]

**Passed items**

- [pass]

**Issues**

- **[P?] [issue]** — [why it matters]

**Evidence**

- [evidence]

**Recommended actions**

- [action]

### 7. Performance & Page Experience — [score]

**Passed items**

- [pass]

**Issues**

- **[P?] [issue]** — [why it matters]

**Evidence**

- mobile average: [score / metrics]
- desktop average: [score / metrics]
- notable outliers: [urls]

**Recommended actions**

- [action]

## PageSpeed Conclusion

### Mobile

- **Average performance:** [score]
- **Pattern:** [brief conclusion]
- **Largest issues:** [list]

### Desktop

- **Average performance:** [score]
- **Pattern:** [brief conclusion]
- **Largest issues:** [list]

## Prioritized Roadmap

### P0

- [critical blocker]

### P1

- [major action]

### P2

- [important improvement]

### P3

- [polish]

## Method Notes

- Crawl is a sampled audit, not a full-site crawl.
- Observed evidence comes from fetched pages and PageSpeed results only.
