# SEO GEO Skills

Claude Code skill for sampled SEO + GEO audits of public sites.

- Capped crawl up to 50 pages, template-aware sampling
- Raw Googlebot-style HTTP baseline compared with browser-rendered evidence
- Local Lighthouse (no remote API) via `lighthouse` + `chrome-launcher`
- Final polished HTML report from the same structured payload as the chat audit

中文版见[下方](#seo-geo-skills-中文)。

## Install

Paste this into a Claude Code session:

```text
Install this skill: https://github.com/iklynow-hue/seo-geo-skills
```

Claude reads this README and runs the install. Open a fresh Claude Code session afterward so the skill is picked up.

### Manual install

**Prerequisites:** `git`, `python3`, `node` + `npm`. Chrome is downloaded by `chrome-launcher` on first Lighthouse run if not present.

```bash
# 1. Clone to a stable location
mkdir -p ~/.claude
git clone https://github.com/iklynow-hue/seo-geo-skills ~/.claude/seo-geo-skills

# 2. Symlink the skill into Claude Code's user skills folder
mkdir -p ~/.claude/skills
ln -s ~/.claude/seo-geo-skills/skills/seo-geo-site-audit ~/.claude/skills/seo-geo-site-audit

# 3. Install the Lighthouse runner's npm deps (~120 MB, one-time)
cd ~/.claude/seo-geo-skills/skills/seo-geo-site-audit/scripts && npm install
```

Per-project install instead: replace `~/.claude/skills/` with `.claude/skills/` inside the project root.

### Update

```bash
cd ~/.claude/seo-geo-skills && git pull
# If scripts/package.json changed:
cd skills/seo-geo-site-audit/scripts && npm install
```

### Optional fetchers

`urllib` works alone, but SPA accuracy improves with one of these. Skip initially; the wrapper detects what's available at run time. Add `--auto-install-prereqs` later if you want.

- `scrapling[fetchers]` — `pip install "scrapling[fetchers]" && scrapling install`
- `lightpanda` — `~/.local/bin/lightpanda` on first auto-install
- `agent-browser` — `npm install -g agent-browser && agent-browser install`

## Use it

In chat:

- `Conduct an SEO and GEO audit for https://example.com`
- `Audit this site for AI visibility: https://example.com`
- `Run a 50-page audit for https://example.com, generate the HTML report, output in Chinese`

The skill asks five setup questions before crawling:

1. **Scope** — Fast (1) / Light (10) / Standard (50) / Custom (1–50)
2. **Output style** — Operator (default) / Boss / Specialist
3. **Performance** — Local Lighthouse (default) / Skip
4. **HTML report** — Off (default) / On
5. **Output language** — English (default) / Chinese / Other

### The five questions are mandatory

The skill asks them even in sessions where you've told Claude to skip clarifying questions. Audits are long and opinionated; the skill refuses to silently pick scope, performance, HTML, or language for you. Two waivers exist:

- Answer all five upfront — `Audit https://example.com — 50 pages, Operator, Lighthouse on, HTML on, output in Chinese.`
- Explicit defaults opt-in — `Audit https://example.com, use defaults for everything.`

"Just go" / "be quick" / "stop asking" do **not** waive the questions.

### Limits to know

- Crawl cap: 1–50 pages (`fast=1`, `light=10`, `template=50`; default `light`).
- Lighthouse: 1 homepage URL by default (mobile + desktop), max 10 via `--max-pagespeed-urls`.
- SPA route expansion is sample-based, not a full app crawler.
- Routes from `dom_route_hint` or `route_guess` are labeled **assisted discovery** — not search-engine crawl proof.

## Terminal usage

Replace `${SKILL_DIR}` with your install path, e.g. `~/.claude/skills/seo-geo-site-audit`.

```bash
"${SKILL_DIR}/scripts/audit-site" https://example.com --output-style operator
```

Standard audit with HTML in Chinese:

```bash
"${SKILL_DIR}/scripts/audit-site" \
  https://example.com \
  --mode template \
  --output-style operator \
  --html-report \
  --report-language chinese
```

After Claude fills `final-report.json`, render the polished HTML:

```bash
"${SKILL_DIR}/scripts/render-report-html" \
  --report-json "${SKILL_DIR}/runs/site-audit-example.com-<stamp>/final-report.json" \
  --out "${SKILL_DIR}/runs/site-audit-example.com-<stamp>/audit-report.html"
```

Common flags (full list in [`skills/seo-geo-site-audit/references/cli-flags.md`](skills/seo-geo-site-audit/references/cli-flags.md)):

- `--mode fast|light|template` — 1 / 10 / 50 pages
- `--max-pages 1-50` — override cap
- `--output-style boss|operator|specialist`
- `--max-pagespeed-urls 1-10` — default 1 (homepage only)
- `--skip-pagespeed`, `--html-report`
- `--report-language english|chinese`
- `--fetcher auto|scrapling|lightpanda|agent_browser|chrome|urllib`
- `--auto-install-prereqs`, `--skip-prereq-check`, `--out-dir /path`

### Artifacts produced

- `crawl.json` — crawl evidence + per-page signals
- `pagespeed.json` — Lighthouse data (unless skipped)
- `audit-run.json` — manifest of the run
- `evidence-report.html` — raw evidence HTML (with `--html-report`)
- `final-report.json` — seeded payload that Claude fills in
- `audit-report.html` — final polished HTML, rendered from `final-report.json`

### Final HTML flow

1. The wrapper collects crawl + Lighthouse evidence.
2. It writes `evidence-report.html` and seeds `final-report.json`.
3. Claude writes the chat audit in the chosen language and completes `final-report.json`.
4. The renderer turns the payload into `audit-report.html`.

## How the crawler thinks about SPAs

Two evidence tracks per HTML page:

- **`search_engine_visibility`** — raw Googlebot-style HTTP baseline, no JavaScript.
- **Rendered browser evidence** — what the SPA shows after JS runs.

Content, navigation, schema, or routes that only appear after rendering are flagged as a JavaScript-dependency risk, not as "Google can't see it." Pages reached only through `dom_route_hint` or `route_guess` are audit assistance, not crawlability proof.

## Security

The repo is intended to be safe for public cloning.

- No API keys / tokens / secrets in source, docs, or artifacts.
- Lighthouse runs locally — no third-party API key required.
- Chrome's sandbox stays on by default; opt-in via `SEO_GEO_ALLOW_NO_SANDBOX=1` only for trusted root/CI/container environments.
- Auto-install of optional fetchers is opt-in only (`--auto-install-prereqs`). Lightpanda binary downloads require a registered SHA256 or an explicit `SEO_GEO_ALLOW_UNVERIFIED_LIGHTPANDA=1`.

Full security notes: [`skills/seo-geo-site-audit/SECURITY.md`](skills/seo-geo-site-audit/SECURITY.md).

## Contributing

Cloning and forking are welcome. Stars are appreciated. Bugs and suggestions → please open an issue.

---

# SEO GEO Skills 中文

Claude Code 技能，对公开网站做采样式 SEO + GEO 审核。

- 最多抓取 50 页，按模板抽样
- 对比 raw Googlebot 风格 HTTP 基线和浏览器渲染证据
- 通过 `lighthouse` + `chrome-launcher` 在本地跑 Lighthouse（不需要远程 API）
- 最终 HTML 报告与终端审核报告共用同一份结构化 payload

## 安装

在 Claude Code 会话中粘贴：

```text
帮我安装这个 skill: https://github.com/iklynow-hue/seo-geo-skills
```

Claude 会读取本 README 并执行安装。完成后请开一个新的 Claude Code 会话让 skill 被加载。

### 手动安装

**前置：** `git`、`python3`、`node` + `npm`。首次运行 Lighthouse 时，`chrome-launcher` 会按需下载 Chrome。

```bash
# 1. 克隆到稳定位置
mkdir -p ~/.claude
git clone https://github.com/iklynow-hue/seo-geo-skills ~/.claude/seo-geo-skills

# 2. 将 skill 软链到 Claude Code 用户级 skills 目录
mkdir -p ~/.claude/skills
ln -s ~/.claude/seo-geo-skills/skills/seo-geo-site-audit ~/.claude/skills/seo-geo-site-audit

# 3. 安装 Lighthouse runner 的 npm 依赖（约 120 MB，一次性）
cd ~/.claude/seo-geo-skills/skills/seo-geo-site-audit/scripts && npm install
```

只想在项目内使用：把上面的 `~/.claude/skills/` 替换成项目根下的 `.claude/skills/`。

### 更新

```bash
cd ~/.claude/seo-geo-skills && git pull
# 如果 scripts/package.json 有变更：
cd skills/seo-geo-site-audit/scripts && npm install
```

### 可选爬虫前置依赖

只用 `urllib` 也能跑，但 SPA 站点上以下任意一个工具在场会更准确。建议先跳过；包装脚本会在运行时检测，需要时再加 `--auto-install-prereqs`：

- `scrapling[fetchers]` — `pip install "scrapling[fetchers]" && scrapling install`
- `lightpanda` — 首次 auto-install 时下载到 `~/.local/bin/lightpanda`
- `agent-browser` — `npm install -g agent-browser && agent-browser install`

## 使用

聊天里直接说：

- `帮我对 https://example.com 做一次 SEO 和 GEO 审核`
- `帮我审核这个站点的 AI 可见性: https://example.com`
- `跑一次 50 页的审核 https://example.com，输出 HTML 报告，结果用中文`

抓取前 skill 会按顺序问五个问题：

1. **抓取范围** — Fast (1) / Light (10，默认) / Standard (50) / 自定义
2. **输出风格** — Operator（默认）/ Boss / Specialist
3. **性能证据** — 本地 Lighthouse（默认）/ 跳过
4. **HTML 报告** — 关（默认）/ 开
5. **输出语言** — English（默认）/ Chinese / Other

### 这五个问题是强制的

即使你告诉 Claude 在当前会话里不要追问，skill 仍会问这五项。审核又长又主观，skill 不允许它默默替你定范围、性能、HTML、语言。只有两种放弃问询的方式：

- 首句一次性给齐五个答案：`审核 https://example.com —— 50 页，Operator 风格，Lighthouse 开，HTML 开，中文输出。`
- 明确说用默认：`审核 https://example.com，全部用默认。`

"直接做"、"快点"、"别问了" **不会**跳过问询，这是有意的。

### 已知限制

- 抓取页数：1–50（`fast=1`、`light=10`、`template=50`；默认 `light`）。
- Lighthouse：默认 1 个首页 URL（mobile + desktop），最多 10 个（`--max-pagespeed-urls`）。
- SPA 路由扩展仍是采样逻辑，不是完整应用爬虫。
- 只通过 `dom_route_hint` 或 `route_guess` 找到的路由会被标为**辅助发现**，不算搜索引擎可爬证据。

## 终端使用

把 `${SKILL_DIR}` 替换为你的实际安装路径，例如 `~/.claude/skills/seo-geo-site-audit`。

```bash
"${SKILL_DIR}/scripts/audit-site" https://example.com --output-style operator
```

中文 HTML 报告示例：

```bash
"${SKILL_DIR}/scripts/audit-site" \
  https://example.com \
  --mode template \
  --output-style operator \
  --html-report \
  --report-language chinese
```

Claude 补全 `final-report.json` 后，再渲染最终交付版 HTML：

```bash
"${SKILL_DIR}/scripts/render-report-html" \
  --report-json "${SKILL_DIR}/runs/site-audit-example.com-<stamp>/final-report.json" \
  --out "${SKILL_DIR}/runs/site-audit-example.com-<stamp>/audit-report.html"
```

常用参数（完整列表见 [`skills/seo-geo-site-audit/references/cli-flags.md`](skills/seo-geo-site-audit/references/cli-flags.md)）：`--mode`、`--max-pages`、`--output-style`、`--max-pagespeed-urls`、`--skip-pagespeed`、`--html-report`、`--report-language`、`--fetcher`、`--auto-install-prereqs`、`--skip-prereq-check`、`--out-dir`。

### 产物

- `crawl.json` — 抓取证据 + 单页信号
- `pagespeed.json` — Lighthouse 数据（除非跳过）
- `audit-run.json` — 本次运行 manifest
- `evidence-report.html` — 原始证据 HTML（启用 `--html-report` 时）
- `final-report.json` — Claude 补全的种子 payload
- `audit-report.html` — 由 `final-report.json` 渲染的最终交付 HTML

### 最终 HTML 流程

1. 包装脚本收集抓取 + Lighthouse 证据。
2. 写出 `evidence-report.html`，并生成 `final-report.json` 种子。
3. Claude 用所选语言写出终端审核结论，并补全 `final-report.json`。
4. 渲染器将其转为最终的 `audit-report.html`。

## 爬虫对 SPA 的处理

每个 HTML 页面保留两条证据线：

- **`search_engine_visibility`** — raw Googlebot 风格 HTTP 基线，不执行 JS。
- **浏览器渲染证据** — SPA 在 JS 执行后展示给用户的内容。

只在渲染后出现的内容、导航、结构化数据或路由会被标为 JavaScript 依赖风险，而不是"Google 看不到"。只通过 `dom_route_hint` 或 `route_guess` 找到的页面属于审计辅助发现，不会写成搜索引擎可直接爬取。

## 安全说明

仓库设计为可安全公开克隆。

- 源码、文档、产物中都不应硬编码 API key / token / 密钥。
- Lighthouse 在本地运行，不需要第三方 API key。
- Chrome 沙箱默认开启；只在受信任的 root/CI/容器环境里通过 `SEO_GEO_ALLOW_NO_SANDBOX=1` 关闭。
- 可选爬虫工具的自动安装是 opt-in（`--auto-install-prereqs`）。Lightpanda 二进制下载默认要求注册 SHA256，或显式设置 `SEO_GEO_ALLOW_UNVERIFIED_LIGHTPANDA=1`。

完整安全说明见 [`skills/seo-geo-site-audit/SECURITY.md`](skills/seo-geo-site-audit/SECURITY.md)。

## 贡献

欢迎 clone / fork。觉得有用的话顺手点个 star 就很感谢。遇到 bug 或有建议，欢迎提 issue。
