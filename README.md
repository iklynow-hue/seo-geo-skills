# SEO GEO Skills

Claude Code skill for sampled SEO + GEO audits of public sites.

- capped crawling up to 50 pages
- template-aware sampling
- raw Googlebot-style baseline compared with rendered browser evidence
- local Lighthouse via a programmatic node runner (`lighthouse` + `chrome-launcher`)
- final polished HTML reporting from the same structured content as the written audit

## Install in one paste

In a Claude Code session, paste this:

```text
Install this skill: https://github.com/iklynow-hue/seo-geo-skills
```

Claude will read this README and run the install for you. After it finishes, **start a new Claude Code session** so the skill is picked up, then say:

```text
Conduct a SEO and GEO audit for https://example.com
```

Claude will autodiscover the `seo-geo-site-audit` skill, walk through the setup questions, and run the audit.

## What Claude should run to install

If you (or Claude) are running the install manually, this is the exact recipe.

**Prerequisites:** `git`, `python3`, `node` + `npm`. Chrome will be downloaded by `chrome-launcher` on first Lighthouse run if not present.

```bash
# 1. Clone the repo to a stable location
mkdir -p ~/.claude
git clone https://github.com/iklynow-hue/seo-geo-skills ~/.claude/seo-geo-skills

# 2. Symlink the skill into Claude Code's user skills folder
mkdir -p ~/.claude/skills
ln -s ~/.claude/seo-geo-skills/skills/seo-geo-site-audit ~/.claude/skills/seo-geo-site-audit

# 3. Install the local Lighthouse runner's npm deps (one-time, ~120MB)
cd ~/.claude/seo-geo-skills/skills/seo-geo-site-audit/scripts && npm install
```

That's it. Open a new Claude Code session and the skill will autotrigger on any SEO/GEO audit request.

### Optional: per-project install instead

If you want the skill only available inside one project, symlink it under that project instead of `~/.claude/skills/`:

```bash
mkdir -p .claude/skills
ln -s ~/.claude/seo-geo-skills/skills/seo-geo-site-audit .claude/skills/seo-geo-site-audit
```

### Optional fetcher prerequisites

The crawl works with `urllib` alone, but it is more accurate on SPA sites when one or more of these are present. Skip them initially — the wrapper detects what is available at run time, and you can add `--auto-install-prereqs` later.

- `scrapling[fetchers]` (`pip install "scrapling[fetchers]"` + `scrapling install`)
- `lightpanda` (downloads to `~/.local/bin/lightpanda` on first auto-install)
- `agent-browser` (`npm install -g agent-browser` + `agent-browser install`)

## Update

The skill is a symlink, so updates are just:

```bash
cd ~/.claude/seo-geo-skills && git pull
```

If `package.json` changed under `skills/seo-geo-site-audit/scripts/`, rerun `npm install` in that directory.

## Use it

After install, open a fresh Claude Code session and say things like:

- `Conduct a SEO and GEO audit for https://example.com`
- `Audit this site for AI visibility: https://example.com`
- `Run a 50-page SEO + GEO audit for https://example.com, generate the HTML report, output in Chinese`

Claude will pick up the `seo-geo-site-audit` skill from `~/.claude/skills/` and walk through:

1. Scope (1 / 10 / 50 / custom pages)
2. Output style (Operator / Boss / Specialist)
3. Performance evidence (run local Lighthouse or skip)
4. HTML report on / off
5. Final output language

If you already know what you want, put it all in the first message and it skips the questionnaire.

Current implementation limits to know up front:

- crawl cap: `1` to `50` pages
- audit presets: `fast=1`, `light=10`, `template=50`
- default audit scope: `light=10`
- Lighthouse URLs: default `1` homepage URL, maximum `10`
- best-effort SPA route expansion is capped and still sample-based, not a full app crawler
- SPA route hints and guessed URLs are labeled as assisted discovery, not search-engine crawl proof

## Use Cases

Use `seo-geo-site-audit` when you want:

- an SEO audit
- a GEO / AI visibility audit
- a sampled site-quality review instead of a full crawl
- a scored report with evidence, issues, and recommended actions
- HTML output for sharing

## SPA And Search Crawlability

The crawler keeps two evidence tracks for each HTML page:

- `search_engine_visibility`: raw Googlebot-style HTTP baseline, no JavaScript.
- rendered browser evidence: what the SPA shows after JavaScript runs.

This is intentional. Browser rendering helps inspect SPA content, but the report should treat any content, navigation, schema, or route that only appears after rendering as a risk. Pages discovered only through `dom_route_hint` or `route_guess` are audit assistance, not proof that search engines can crawl them.

## Chat Usage

Start with:

```text
Use $seo-geo-site-audit to audit https://example.com
```

The skill is designed to ask setup questions one by one before crawling:

1. Scope
2. Output style
3. Performance evidence (run local Lighthouse or skip)
4. HTML report on/off
5. Final output language

Language confirmation is mandatory for the skill flow. The audit should not proceed to the final report until the user confirms the language or explicitly accepts the default English.

If you already know your preferences, you can put them in the first prompt and skip the questionnaire. If scope, output style, performance on/off, HTML on/off, and final language are all clearly stated, the agent should use them directly instead of asking again.

Example:

```text
Use $seo-geo-site-audit to audit https://example.com with light mode, Operator output, local Lighthouse on, HTML report on, and final report in Chinese.
```

Default first test:

- keep local Lighthouse on
- keep the default output style
- start with the default `10-page` light audit
- turn HTML on if you want a shareable artifact

Current performance choices:

- `1. Run local Lighthouse (default)`
- `2. Skip performance`

Performance collection defaults to the landing page only. The wrapper tests one homepage URL with both mobile and desktop strategies, which keeps audits fast and avoids long Lighthouse waits on heavy SPA routes. Use `--max-pagespeed-urls` only when you explicitly need extra template coverage.

The final language choices are:

- `1. English (default)`
- `2. Chinese`
- `3. Other (type it in)`

Language note:

- the written audit and final polished HTML should use the same selected language
- English and Chinese are first-class built-in options
- for another language, the agent can still render the final report in that language by filling the structured report payload before rendering HTML

If the agent skips the setup questions, you can prompt it more explicitly:

```text
Use $seo-geo-site-audit to audit https://example.com. Ask me the setup questions one by one with numbered options for scope, output style, performance handling, HTML report, and final output language before you begin.
```

## Terminal Usage

Use the wrapper for normal runs (replace `${SKILL_DIR}` with your actual install path, e.g. `~/.claude/skills/seo-geo-site-audit`):

```bash
"${SKILL_DIR}/scripts/audit-site" \
  https://example.com \
  --output-style operator
```

Example with HTML output in Chinese:

```bash
"${SKILL_DIR}/scripts/audit-site" \
  https://example.com \
  --mode template \
  --output-style operator \
  --html-report \
  --report-language chinese
```

Then render the polished final HTML after you fill `final-report.json`:

```bash
"${SKILL_DIR}/scripts/render-report-html" \
  --report-json "${SKILL_DIR}/runs/site-audit-example.com-<stamp>/final-report.json" \
  --out "${SKILL_DIR}/runs/site-audit-example.com-<stamp>/audit-report.html"
```

Useful options:

- `--mode fast|light|template` which map to `1`, `10`, and `50` pages
- `--max-pages 1-50`
- `--output-style boss|operator|specialist`
- `--max-pagespeed-urls 1-10` (default `1`; homepage only, tested once on mobile and once on desktop)
- `--skip-pagespeed`
- `--html-report`
- `--report-language english|chinese` for the wrapper's evidence HTML and seeded final report payload
- `--fetcher auto|scrapling|lightpanda|agent_browser|chrome|urllib`
- `--auto-install-prereqs`
- `--skip-prereq-check`
- `--out-dir /path/to/output`

Artifacts:

- `crawl.json`
- `pagespeed.json` unless skipped
- `audit-run.json`
- `evidence-report.html` when HTML output is enabled
- `final-report.json` as a seeded payload for the final polished report
- `audit-report.html` after you render the final polished report from `final-report.json`

Final HTML flow in the skill:

1. The wrapper gathers crawl and Lighthouse evidence.
2. The wrapper writes `evidence-report.html` and seeds `final-report.json`.
3. The agent writes the final audit in the selected language and fills `final-report.json`.
4. The renderer turns that payload into the final `audit-report.html`.

## Security

This repo is intended to be safe for public cloning.

- No API keys, tokens, or secrets should be hardcoded in source, docs, or artifacts.
- The skill does not require any third-party API key for performance evidence; Lighthouse runs locally.

See:

- [skills/seo-geo-site-audit/SECURITY.md](skills/seo-geo-site-audit/SECURITY.md)

## Contribution Policy

Cloning and forking are welcome.

If you find this repo useful, a star is always appreciated.

If you run into a bug or have a suggestion, feel free to open an issue.

---

# SEO GEO Skills 中文说明

公开技能仓库：

- `skills/seo-geo-site-audit/`

这是一个 Claude Code 技能，用于对公开网站进行采样式 SEO + GEO 审核，支持：

- 最多 50 页的上限抓取
- 按模板类型抽样
- 对比 raw Googlebot 风格基线和浏览器渲染证据
- 通过 `lighthouse` + `chrome-launcher` 在本地编程式运行 Lighthouse
- 基于与终端报告相同结构内容生成最终 HTML 报告

## 一次粘贴完成安装

在 Claude Code 会话里直接粘贴：

```text
帮我安装这个 skill: https://github.com/iklynow-hue/seo-geo-skills
```

Claude 会读取本 README 并替你执行安装。完成后**重启一个 Claude Code 会话**让 skill 被加载，然后说：

```text
帮我对 https://example.com 做一次 SEO 和 GEO 审核
```

Claude 会自动匹配 `seo-geo-site-audit` skill，按顺序问你配置，再开始审核。

## 手动安装步骤（也是 Claude 会执行的）

**前置：** `git`、`python3`、`node` + `npm`。Chrome 在首次跑 Lighthouse 时如未安装会由 `chrome-launcher` 自动下载。

```bash
# 1. 把仓库 clone 到稳定位置
mkdir -p ~/.claude
git clone https://github.com/iklynow-hue/seo-geo-skills ~/.claude/seo-geo-skills

# 2. 把 skill 软链到 Claude Code 用户级 skills 目录
mkdir -p ~/.claude/skills
ln -s ~/.claude/seo-geo-skills/skills/seo-geo-site-audit ~/.claude/skills/seo-geo-site-audit

# 3. 安装本地 Lighthouse runner 的 npm 依赖（一次性，约 120MB）
cd ~/.claude/seo-geo-skills/skills/seo-geo-site-audit/scripts && npm install
```

打开新的 Claude Code 会话，任何 SEO/GEO 审核请求都会自动触发本 skill。

### 可选：仅项目级安装

如果只想在某个项目内使用，把符号链接放到项目的 `.claude/skills/` 而不是 `~/.claude/skills/`：

```bash
mkdir -p .claude/skills
ln -s ~/.claude/seo-geo-skills/skills/seo-geo-site-audit .claude/skills/seo-geo-site-audit
```

### 可选爬虫前置依赖

爬虫只用 `urllib` 也能跑，但 SPA 站点上下面任意一个工具在场会更准确。可以先跳过——包装脚本会在运行时自动检测，你之后随时可以加 `--auto-install-prereqs`：

- `scrapling[fetchers]` (`pip install "scrapling[fetchers]"` + `scrapling install`)
- `lightpanda` (首次 auto-install 时下载到 `~/.local/bin/lightpanda`)
- `agent-browser` (`npm install -g agent-browser` + `agent-browser install`)

## 更新

skill 是符号链接，更新只需一行：

```bash
cd ~/.claude/seo-geo-skills && git pull
```

如果 `skills/seo-geo-site-audit/scripts/` 下的 `package.json` 有变化，在该目录里再跑一次 `npm install`。

## 用起来

安装完后开一个新 Claude Code 会话，直接说：

- `帮我对 https://example.com 做一次 SEO 和 GEO 审核`
- `帮我审核这个站点的 AI 可见性: https://example.com`
- `跑一次 50 页的 SEO + GEO 审核 https://example.com，输出 HTML 报告，结果用中文`

Claude 会从 `~/.claude/skills/` 找到 `seo-geo-site-audit` skill，并按顺序问你：

1. 抓取范围（1 / 10 / 50 / 自定义）
2. 输出风格（Operator / Boss / Specialist）
3. 性能证据（运行本地 Lighthouse 或跳过）
4. 是否要 HTML 报告
5. 最终输出语言

如果第一句话里已经把这些都写清楚，会跳过问询直接开始。

当前实现的几个限制，建议先了解：

- 抓取页数范围：`1` 到 `50`
- 预设模式：`fast=1`、`light=10`、`template=50`
- 默认抓取范围：`light=10`
- Lighthouse URL 数：默认 `1` 个首页 URL，最大 `10`
- SPA 的最佳努力扩展仍然是采样逻辑，不是完整应用爬虫
- SPA 路由 hints 和猜测路径会标记为辅助发现，不会当成搜索引擎可爬证明

## 适用场景

当你需要以下能力时，可以使用 `seo-geo-site-audit`：

- SEO 审核
- GEO / AI 可见性审核
- 采样式站点质量检查，而不是全站爬取
- 带评分、证据、问题和修复建议的结构化报告
- HTML 报告导出

## SPA 与搜索爬取能力

爬虫会为每个 HTML 页面保留两条证据线：

- `search_engine_visibility`：raw Googlebot 风格 HTTP 基线，不执行 JavaScript。
- 浏览器渲染证据：SPA 在 JavaScript 运行后展示给用户的内容。

这样做是为了避免把"浏览器能看到"误判成"搜索引擎一定能稳定看到"。如果内容、导航、结构化数据或路由只在渲染后出现，报告应该把它当作风险说明。只通过 `dom_route_hint` 或 `route_guess` 找到的页面属于审计辅助发现，不应写成搜索引擎可直接爬取。

## 聊天中使用

可以这样开始：

```text
Use $seo-geo-site-audit to audit https://example.com
```

在正式抓取前，技能会按顺序逐个确认：

1. 抓取范围
2. 输出风格
3. 性能证据（运行本地 Lighthouse 或跳过）
4. 是否生成 HTML 报告
5. 最后再询问输出语言

默认首次测试建议：

- 保持本地 Lighthouse 打开
- 输出风格先保持默认
- 先用默认的 `10` 页 light audit
- 如果你想拿到可分享的产物，可以打开 HTML 输出

当前性能选项：

- `1. 运行本地 Lighthouse（默认）`
- `2. 跳过性能`

性能采集默认只测 landing page / 首页。包装脚本会对 1 个首页 URL 分别跑 mobile 和 desktop，这样可以避免重型 SPA 路由导致 Lighthouse 等待时间过长。只有在明确需要额外模板覆盖时，再使用 `--max-pagespeed-urls` 提高 URL 数量。

最后的语言选项是：

- `1. English (default)`
- `2. Chinese`
- `3. Other (type it in)`

语言说明：

- 终端中的最终报告与最终 HTML 报告应该使用同一种语言
- 英文和中文是内置的一等选项
- 如果用户输入其他语言，agent 仍可先写结构化 `final-report.json`，再渲染出同语言 HTML

如果 agent 没有主动逐项提问，可以更明确地这样说：

```text
Use $seo-geo-site-audit to audit https://example.com. Ask me the setup questions one by one with numbered options for scope, output style, performance handling, HTML report, and final output language before you begin.
```

## 终端使用

正常运行请使用包装脚本（把 `${SKILL_DIR}` 替换为你的实际安装路径，例如 `~/.claude/skills/seo-geo-site-audit`）：

```bash
"${SKILL_DIR}/scripts/audit-site" \
  https://example.com \
  --output-style operator
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

补全 `final-report.json` 后，再渲染最终交付版 HTML：

```bash
"${SKILL_DIR}/scripts/render-report-html" \
  --report-json "${SKILL_DIR}/runs/site-audit-example.com-<stamp>/final-report.json" \
  --out "${SKILL_DIR}/runs/site-audit-example.com-<stamp>/audit-report.html"
```

常用参数：

- `--mode fast|light|template`，分别对应 `1`、`10`、`50` 页
- `--max-pages 1-50`
- `--output-style boss|operator|specialist`
- `--max-pagespeed-urls 1-10`（默认 `1`；只测首页，并分别跑 mobile 和 desktop）
- `--skip-pagespeed`
- `--html-report`
- `--report-language english|chinese`，用于包装脚本的证据页 HTML 和最终报告种子 JSON
- `--fetcher auto|scrapling|lightpanda|agent_browser|chrome|urllib`
- `--auto-install-prereqs`
- `--skip-prereq-check`
- `--out-dir /path/to/output`

输出产物：

- `crawl.json`
- `pagespeed.json`，如果没有跳过
- `audit-run.json`
- `evidence-report.html`，当启用 HTML 输出时生成
- `final-report.json`，作为最终交付稿的种子结构
- `audit-report.html`，在你用 `final-report.json` 渲染最终交付 HTML 后生成

技能里的最终 HTML 流程：

1. 包装脚本先收集抓取与 Lighthouse 证据。
2. 包装脚本写出 `evidence-report.html`，并生成 `final-report.json` 种子。
3. agent 用所选语言写出最终审核结论，并补全 `final-report.json`。
4. 渲染器再将其转换为最终的 `audit-report.html`。

## 安全说明

这个仓库设计为可安全公开克隆。

- 任何 API key、token、密钥都不应该被硬编码到源码、文档或产物中。
- 本技能不依赖任何第三方 API key 来收集性能证据；Lighthouse 在本地运行。

更多说明见：

- [skills/seo-geo-site-audit/SECURITY.md](skills/seo-geo-site-audit/SECURITY.md)

## 贡献策略

欢迎 clone 和 fork。

如果你觉得这个仓库对你有帮助，欢迎顺手点一个 star。

如果你遇到 bug，或者有改进建议，欢迎提交 issue。
