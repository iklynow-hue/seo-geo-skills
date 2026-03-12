# Core Web Vitals Thresholds

<!-- Updated: 2026-03-12 -->
<!-- Note: FID was removed September 9, 2024. Use INP instead. -->

## Current Metrics (March 2026)

| Metric | Good | Needs Improvement | Poor |
|--------|------|-------------------|------|
| **LCP** (Largest Contentful Paint) | ≤ 2.5s | 2.5s – 4.0s | > 4.0s |
| **INP** (Interaction to Next Paint) | ≤ 200ms | 200ms – 500ms | > 500ms |
| **CLS** (Cumulative Layout Shift) | ≤ 0.1 | 0.1 – 0.25 | > 0.25 |

## Supporting Metrics

| Metric | Good | Notes |
|--------|------|-------|
| **TTFB** (Time to First Byte) | ≤ 800ms | Server response time |
| **FCP** (First Contentful Paint) | ≤ 1.8s | First visible content |
| **TBT** (Total Blocking Time) | ≤ 200ms | Lab proxy for INP |
| **Speed Index** | ≤ 3.4s | Visual completeness |

## Scoring for SGEO

### SEO Score (Performance category, 10% weight)

| LCP | INP | CLS | Score |
|-----|-----|-----|-------|
| ≤ 2.5s | ≤ 200ms | ≤ 0.1 | 100 |
| ≤ 4.0s | ≤ 500ms | ≤ 0.25 | 50 |
| > 4.0s | > 500ms | > 0.25 | 0 |

Interpolate linearly between thresholds.

### GEO Score

CWV does not directly affect GEO scoring. AI crawlers care about content accessibility (SSR), not page speed. However, extremely slow pages may timeout during AI crawling.

## Deprecated: FID

**First Input Delay (FID) was removed September 9, 2024.**

- Do NOT reference FID in any reports
- Do NOT use FID thresholds
- INP replaced FID as the responsiveness metric
- If PageSpeed API returns FID data, ignore it

## PageSpeed API Notes

- Rate limit: ~25 requests/minute (free tier)
- Use `strategy=mobile` for primary scores (mobile-first indexing)
- Desktop scores are supplementary
- If API fails, mark CWV as "Unable to verify" with Hypothesis confidence
