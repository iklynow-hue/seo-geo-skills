---
name: sgeo
description: >
  Unified SEO + GEO audit with MECE framework and dual scoring. Produces
  independent SEO Score (traditional search) and GEO Score (AI search visibility).
  Use when user says "sgeo", "audit", "seo", "geo", "AI search", "site audit",
  "check seo", "check geo", or provides a URL for analysis. Supports full site
  audits, single page analysis, schema validation, and GitHub repo SEO.
---

# SGEO — Unified SEO + GEO Master Audit Skill

Combined SEO and GEO analysis with MECE (Mutually Exclusive, Collectively Exhaustive) framework.
Produces dual scores: **SEO Score** (traditional search) and **GEO Score** (AI search visibility).

## Available Commands

| Command | Description |
|---------|-------------|
| `sgeo audit <url>` | Full dual-score audit (SEO + GEO) |
| `sgeo seo <url>` | SEO-only audit (traditional search focus) |
| `sgeo geo <url>` | GEO-only audit (AI search focus) |
| `sgeo page <url>` | Deep single-page dual analysis |
| `sgeo technical <url>` | Technical infrastructure checks |
| `sgeo schema <url>` | Schema detection, validation, generation |
| `sgeo content <url>` | Content quality, E-E-A-T, citability |
| `sgeo brand <url>` | Brand authority and platform presence |
| `sgeo llmstxt <url>` | llms.txt analysis and generation |
| `sgeo github <repo>` | GitHub repository SEO optimization |
| `sgeo compare <url>` | Side-by-side SEO vs GEO score comparison |

---

## MECE Framework

All audit categories are **Mutually Exclusive** (no overlap) and **Collectively Exhaustive** (full coverage).
Read `resources/references/mece-framework.md` for the complete category definitions.

### Category Map

```
┌─────────────────────────────────────────────────────────────────┐
│                    SGEO MECE AUDIT FRAMEWORK                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  SHARED FOUNDATION (Both SEO + GEO)                             │
│  ├── 1. Technical Infrastructure (SEO:25% / GEO:15%)            │
│  ├── 2. Content Quality & E-E-A-T (SEO:15% / GEO:15%)          │
│  └── 3. Structured Data (SEO:15% / GEO:10%)                    │
│                                                                 │
│  SEO-SPECIFIC                          GEO-SPECIFIC             │
│  ├── 4. On-Page Optimization (20%)     ├── 6. AI Citability (25%)│
│  ├── 5. Social Signals (5%)            ├── 7. Brand Authority (20%)│
│  └── 9. Local SEO (10%*)              ├── 8. AI Crawler Access (10%)│
│      * if applicable                   └── 10. Platform Opt. (5%)│
│                                                                 │
│  PERFORMANCE (embedded in Technical)                            │
│  └── Core Web Vitals (SEO:10% / GEO:0%)                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Dual Scoring Weights

### SEO Score (Traditional Search)

| # | Category | Weight | Focus |
|---|----------|--------|-------|
| 1 | Technical Infrastructure | 25% | Crawlability, security, performance, CWV |
| 2 | On-Page Optimization | 20% | Title, meta, headings, images, internal links |
| 3 | Content Quality | 15% | E-E-A-T, depth, readability, freshness |
| 4 | Structured Data | 15% | Schema validation, rich result eligibility |
| 5 | Performance (CWV) | 10% | LCP, INP, CLS |
| 6 | Social Signals | 5% | Open Graph, Twitter Card |
| 7 | Local SEO | 10% | If applicable (0% if not local business) |
| | **Total** | **100%** | |

### GEO Score (AI Search Visibility)

| # | Category | Weight | Focus |
|---|----------|--------|-------|
| 1 | AI Citability | 25% | Quotable passages, statistics, direct answers |
| 2 | Brand Authority | 20% | Wikipedia, reviews, Reddit, YouTube, press |
| 3 | Technical Infrastructure | 15% | SSR, crawlability, security |
| 4 | Content Quality | 15% | E-E-A-T, depth, original insights |
| 5 | AI Crawler Access | 10% | robots.txt AI rules, llms.txt, meta AI tags |
| 6 | Structured Data | 10% | Entity linking, sameAs, FAQPage, speakable |
| 7 | Platform Optimization | 5% | AIO, ChatGPT, Perplexity, Gemini, Copilot |
| | **Total** | **100%** | |

---

## Orchestration Logic

### Step 1 — Identify the Task

Parse the user's request to determine which workflow to activate:

- **Full audit** (`sgeo audit <url>`): Run all categories, produce dual scores
- **SEO-only** (`sgeo seo <url>`): Run SEO categories only
- **GEO-only** (`sgeo geo <url>`): Run GEO categories only
- **Single page** (`sgeo page <url>`): Deep dive on one URL, dual scores
- **Specific area**: Route to matching sub-skill
- **Generic URL request**: Treat as full audit

### Step 2 — Collect Evidence

**Primary method (LLM-first)** — use built-in `read_url_content` tool:
```
read_url_content(url) → returns parsed HTML content
```

**Script-backed verification** (recommended when execution is available):
```bash
SKILL_DIR="<absolute_path_to_this_skill_directory>"

# Phase 1: Fetch and parse
python3 $SKILL_DIR/scripts/fetch_page.py <url> --output /tmp/page.html
python3 $SKILL_DIR/scripts/parse_html.py /tmp/page.html --url <url> --json

# Phase 2: Technical checks (run in parallel)
python3 $SKILL_DIR/scripts/robots_checker.py <url>
python3 $SKILL_DIR/scripts/llms_txt_checker.py <url>
python3 $SKILL_DIR/scripts/security_headers.py <url>
python3 $SKILL_DIR/scripts/redirect_checker.py <url>
python3 $SKILL_DIR/scripts/broken_links.py <url> --workers 5
python3 $SKILL_DIR/scripts/internal_links.py <url> --depth 1 --max-pages 20
python3 $SKILL_DIR/scripts/social_meta.py <url>

# Phase 3: Content analysis
python3 $SKILL_DIR/scripts/readability.py /tmp/page.html --json
python3 $SKILL_DIR/scripts/citability_scorer.py <url> --json
python3 $SKILL_DIR/scripts/schema_validator.py /tmp/page.html --json

# Phase 4: On-page quality + multi-page checks
python3 $SKILL_DIR/scripts/onpage_checker.py <url>                    # single page
python3 $SKILL_DIR/scripts/onpage_checker.py <url> --multi --max-pages 10  # multi-page (sitemap crawl)

# Phase 5: Performance (may be rate-limited)
python3 $SKILL_DIR/scripts/pagespeed.py <url> --strategy mobile

# Phase 6: Brand authority (GEO-specific)
python3 $SKILL_DIR/scripts/brand_scanner.py <url> --json

# Phase 7: Generate HTML dashboard with dual scores
python3 $SKILL_DIR/scripts/generate_report.py <url> --output SGEO-REPORT.html
```

> **`SKILL_DIR`** = absolute path to this skill directory (the folder containing this SKILL.md).
> Do not use third-party mirrors as primary evidence when direct fetch or bundled scripts are available.

### Step 3 — LLM-First Analysis

Use the LLM as the primary analyst:

1. Synthesize evidence from page content, metadata, and script outputs
   - **Always run `onpage_checker.py --multi`** for full audits to catch:
     - Heading text quality issues (missing spaces like "BatchPhoto", duplicate headings)
     - Viewport accessibility violations (maximum-scale=1 blocks zoom)
     - Multi-page schema coverage gaps (tool/blog pages with zero structured data)
     - Schema quality issues (missing dateModified, minimal author schemas)
     - Cross-page review count inconsistencies
   - These findings feed into On-Page Optimization, Structured Data, and Content Quality categories
2. Produce findings with explicit proof:
   - `Finding` — What was found
   - `Evidence` — Specific element, metric, or snippet
   - `Impact` — Why it matters (specify SEO, GEO, or both)
   - `Fix` — Clear implementation step
   - `Confidence` — Confirmed (script-verified), Likely (LLM-inferred), Hypothesis (needs verification)
3. Categorize each finding into exactly ONE MECE category
4. Score each category independently for SEO and GEO

### Step 4 — Apply Quality Gates

Reference the quality standards in `resources/references/`:

- **MECE Framework**: Read [mece-framework.md](resources/references/mece-framework.md) for category definitions
- **Dual Scoring**: Read [dual-scoring-methodology.md](resources/references/dual-scoring-methodology.md) for weight calculations
- **FAQPage Guidance**: Read [faqpage-guidance.md](resources/references/faqpage-guidance.md) for the keep-for-AI stance
- **Content Minimums**: Read [quality-gates.md](resources/references/quality-gates.md) for word counts, unique content %
- **Schema Types**: Read [schema-types.md](resources/references/schema-types.md) for active/deprecated/restricted types
- **CWV Thresholds**: Read [cwv-thresholds.md](resources/references/cwv-thresholds.md) for current metrics
- **E-E-A-T Framework**: Read [eeat-framework.md](resources/references/eeat-framework.md) for scoring criteria

### Step 5 — Score and Report

Calculate dual scores:

```
SEO Score = Σ(Category Score × SEO Weight)
GEO Score = Σ(Category Score × GEO Weight)
```

#### Score Interpretation

| Score | Rating | Action |
|-------|--------|--------|
| 90-100 | Excellent | Maintain and monitor |
| 70-89 | Good | Minor optimizations |
| 50-69 | Fair | Significant improvements needed |
| 30-49 | Poor | Major overhaul required |
| 0-29 | Critical | Immediate action required |

### Step 6 — Mandatory Deliverables

For `sgeo audit`, `sgeo page`, and generic URL requests:

1. Create `SGEO-AUDIT-REPORT.md` — Detailed findings with MECE categorization
2. Create `SGEO-ACTION-PLAN.md` — Prioritized fixes tagged as SEO, GEO, or Both
3. If HTML dashboard generated, include path to `SGEO-REPORT.html`
4. Final response must include:
   - SEO Score: XX/100 (Rating)
   - GEO Score: XX/100 (Rating)
   - Top 3 SEO fixes
   - Top 3 GEO fixes
   - Category breakdown table

### Step 7 — Error Handling

If a check fails due to network, DNS, permissions, or API rate limits:
- Report it as an **environment limitation**, not a confirmed site issue
- Keep confidence as `Hypothesis` for impacted categories
- Continue with available evidence
- Do not enter repeated fallback loops — retry at most once, then finalize
- Always produce both markdown files even with partial data

---

## FAQPage Schema Policy

**Stance: KEEP for GEO, note Google restriction**

| Aspect | Detail |
|--------|--------|
| Google Rich Results | ❌ Restricted to gov/healthcare (Aug 2023) |
| AI Search Engines | ✅ ChatGPT, Perplexity, Claude, Gemini all use it |
| Schema.org Status | ✅ Active (not deprecated) |
| Penalty Risk | None — Google ignores, doesn't penalize |
| Voice Search | ✅ Benefits voice assistant understanding |
| Featured Snippets | ✅ Still helps with snippet selection |

**In reports, always note:**
> ℹ️ FAQPage schema detected. Google restricts rich results to gov/healthcare sites, but AI search engines actively use this for content understanding and citation. **Recommendation: KEEP** for GEO benefits.

---

## Critical Rules

1. **INP not FID** — FID was removed September 9, 2024. Use INP (Interaction to Next Paint). Never reference FID.
2. **FAQPage: KEEP** — Restricted for Google rich results but valuable for AI search. Do NOT recommend removal.
3. **HowTo schema is deprecated** — Rich results removed September 2023. Never recommend.
4. **JSON-LD only** — Always use `<script type="application/ld+json">`. Never recommend Microdata or RDFa.
5. **E-E-A-T everywhere** — Applies to ALL competitive queries, not just YMYL (December 2025).
6. **Mobile-first is complete** — 100% mobile-first indexing since July 5, 2024.
7. **MECE compliance** — Every finding must belong to exactly ONE category. No double-counting.
8. **Dual scores always** — Full audits must produce both SEO and GEO scores.
9. **LLM-first, script-verified** — Start with LLM reasoning, verify with scripts. Never block on script failure.
10. **Always produce file artifacts** — `SGEO-AUDIT-REPORT.md` and `SGEO-ACTION-PLAN.md` are required.
11. **Bound retries** — If a check fails, retry once max. Then finalize with confidence labels.
12. **No third-party mirrors** — Use direct fetch and bundled scripts, not jina.ai or similar.

---

## Dependencies

### Required
- Python 3.8+
- `requests`
- `beautifulsoup4`
- `lxml`

### Optional
- `playwright` (for visual analysis / screenshots)

### Install
```bash
# Quick install
bash <SKILL_DIR>/install.sh

# Or manual
pip install requests beautifulsoup4 lxml
```

---

## Output Format

All reports use consistent severity levels:
- 🔴 **Critical** — Directly impacts rankings or AI visibility (fix immediately)
- ⚠️ **Warning** — Optimization opportunity (fix within 1 month)
- ✅ **Pass** — Meets or exceeds standards
- ℹ️ **Info** — Informational or not applicable

Each finding is tagged:
- `[SEO]` — Affects SEO score only
- `[GEO]` — Affects GEO score only
- `[BOTH]` — Affects both scores

Structure reports as:
1. Dual score summary (SEO + GEO side by side)
2. MECE category breakdown with individual scores
3. Findings grouped by MECE category
4. Prioritized action plan tagged by impact area
