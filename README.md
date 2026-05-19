# SEO GEO Skills

Claude Code skill for sampled SEO + GEO audits of public sites.

- Crawl up to 50 pages, template-aware sampling
- Raw Googlebot baseline vs browser-rendered evidence
- Local Lighthouse (no remote API)
- Final polished HTML report from the same payload as the chat audit

中文版见[下方](#seo-geo-skills-中文)。

## Install

Paste this into a Claude Code session:

```text
Install this skill: https://github.com/iklynow-hue/seo-geo-skills
```

Claude reads this README and runs the install. Open a fresh Claude Code session afterward so the skill is picked up.

### Manual install

**Prerequisites:** `git`, `python3`, `node` + `npm`. Chrome is downloaded by `chrome-launcher` on first Lighthouse run if not present.

Clone the repo **anywhere you keep code** (the source location is your choice), then create a symlink at the **fixed** path Claude Code reads from.

```bash
# 1. Clone wherever you want — pick your own path.
REPO_DIR=~/Projects/seo-geo-skills
git clone https://github.com/iklynow-hue/seo-geo-skills "$REPO_DIR"

# 2. Symlink the skill into the path Claude Code scans (this path is fixed).
mkdir -p ~/.claude/skills
ln -s "$REPO_DIR/skills/seo-geo-site-audit" ~/.claude/skills/seo-geo-site-audit

# 3. Install the Lighthouse runner's npm deps (~120 MB, one-time).
cd "$REPO_DIR/skills/seo-geo-site-audit/scripts" && npm install
```

**Why a symlink?** Claude Code auto-discovers skills from `~/.claude/skills/`. Your source can live wherever you keep code; the symlink bridges the two paths so edits in your repo show up immediately in any new Claude Code session.

**Per-project install instead:** replace `~/.claude/skills/` with `.claude/skills/` inside the project root.

### Update

```bash
cd "$REPO_DIR" && git pull
# If scripts/package.json changed:
cd skills/seo-geo-site-audit/scripts && npm install
```

### Optional fetchers

`urllib` works alone, but SPA accuracy improves with one of these. Skip initially; the wrapper detects what's available at run time. Add `--auto-install-prereqs` later if you want.

- `scrapling[fetchers]` — `pip install "scrapling[fetchers]" && scrapling install`
- `lightpanda` — `~/.local/bin/lightpanda` on first auto-install
- `agent-browser` — `npm install -g agent-browser && agent-browser install`

## Use it

The skill runs immediately on the URL. No setup questions. Defaults:

| Setting | Default |
|---|---|
| Mode | Light template audit (10 pages) |
| Output style | Operator |
| Performance | Local Lighthouse — homepage, mobile + desktop |
| HTML report | On |
| Output language | English |

### Example prompts

| You say | The skill does |
|---|---|
| `Audit https://example.com` | Defaults |
| `Conduct an SEO and GEO audit for https://example.com` | Defaults (any audit-like phrasing triggers the skill) |
| `Quick check on https://example.com, skip Lighthouse` | Fast mode (1 page) + `--skip-pagespeed` |
| `Run a 50-page audit for https://example.com, output in Chinese` | Template mode + Chinese report |
| `Audit https://example.com with specialist depth` | Specialist output style |
| `审核 https://example.com 50 页 用中文` | Template mode + Chinese report |
| `Audit my site` (no URL) | Skill asks for the URL — the only hard requirement |

### When the agent asks

Three cases only:

- The URL is missing.
- The prompt is in a non-English language but the report language wasn't stated — one confirmation: "Report in English or `<other>`?".
- `--auto-install-prereqs` would download network binaries — consent first.

The report defaults to **English** even when the prompt is in another language. Switch only on explicit "in `<language>`" / "用中文" or the `--report-language` flag.

### Limits

- Crawl cap 1–50 (`fast=1`, `light=10`, `template=50`).
- Lighthouse: 1 homepage URL by default (mobile + desktop), max 10 via `--max-pagespeed-urls`.
- SPA route expansion is sample-based, not a full app crawler.
- Routes from `dom_route_hint` / `route_guess` are labeled **assisted discovery** — not crawlability proof.

## Terminal usage

Replace `${SKILL_DIR}` with `~/.claude/skills/seo-geo-site-audit`.

```bash
"${SKILL_DIR}/scripts/audit-site" https://example.com \
  --mode template --output-style operator --html-report
```

Common flags (full list in [`skills/seo-geo-site-audit/references/cli-flags.md`](skills/seo-geo-site-audit/references/cli-flags.md)): `--mode`, `--max-pages`, `--output-style`, `--max-pagespeed-urls`, `--skip-pagespeed`, `--html-report`, `--report-language`, `--fetcher`, `--auto-install-prereqs`, `--out-dir`.

After Claude fills `final-report.json`, render the polished HTML:

```bash
"${SKILL_DIR}/scripts/render-report-html" \
  --report-json "${SKILL_DIR}/runs/site-audit-<host>-<stamp>/final-report.json" \
  --out "${SKILL_DIR}/runs/site-audit-<host>-<stamp>/audit-report.html"
```

### Artifacts

- `crawl.json` — per-page signals
- `pagespeed.json` — Lighthouse data (unless skipped)
- `audit-run.json` — run manifest
- `evidence-report.html` — raw evidence (with `--html-report`)
- `final-report.json` — payload Claude fills in
- `audit-report.html` — final polished HTML

## SPA handling

The crawl keeps two evidence tracks per HTML page:

- **`search_engine_visibility`** — raw Googlebot-style HTTP baseline, no JavaScript.
- **Rendered browser evidence** — what the SPA shows after JS runs.

Signals that appear only after rendering are flagged as a JavaScript-dependency risk (not "Google can't see it"). Pages reached only through `dom_route_hint` / `route_guess` are audit assistance, not crawlability proof.

## Security

The repo is intended to be safe for public cloning.

- No API keys / tokens / secrets in source, docs, or artifacts.
- Lighthouse runs locally — no third-party API key required.
- Chrome's sandbox stays on by default; opt-in via `SEO_GEO_ALLOW_NO_SANDBOX=1` only for trusted root / CI / container environments.
- `--auto-install-prereqs` is opt-in. Lightpanda binary downloads require a registered SHA256 or explicit `SEO_GEO_ALLOW_UNVERIFIED_LIGHTPANDA=1`.

Full notes: [`skills/seo-geo-site-audit/SECURITY.md`](skills/seo-geo-site-audit/SECURITY.md).

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

**前置：** `git`、`python3`、`node` + `npm`。首次运行 Lighthouse 时 `chrome-launcher` 会按需下载 Chrome。

把仓库 **clone 到你自己平时放代码的位置**（任意路径都行），然后把 skill **软链到 Claude Code 固定查找的目录**。

```bash
# 1. clone 到你想放的位置（路径你自己决定）。
REPO_DIR=~/Projects/seo-geo-skills
git clone https://github.com/iklynow-hue/seo-geo-skills "$REPO_DIR"

# 2. 软链到 Claude Code 扫描的固定路径。
mkdir -p ~/.claude/skills
ln -s "$REPO_DIR/skills/seo-geo-site-audit" ~/.claude/skills/seo-geo-site-audit

# 3. 安装 Lighthouse runner 的 npm 依赖（约 120 MB，一次性）。
cd "$REPO_DIR/skills/seo-geo-site-audit/scripts" && npm install
```

**为什么用软链？** Claude Code 在 `~/.claude/skills/` 下自动发现 skill。源码可以放在任意路径，软链负责把固定的发现位置指向你的实际仓库，这样你在仓库里改了文件，新开的 Claude Code 会话立刻能看到。

**只想项目内用：** 把上面的 `~/.claude/skills/` 换成项目根下的 `.claude/skills/`。

### 更新

```bash
cd "$REPO_DIR" && git pull
# 如果 scripts/package.json 有变更：
cd skills/seo-geo-site-audit/scripts && npm install
```

### 可选爬虫前置依赖

只用 `urllib` 也能跑，但 SPA 站点上以下任意一个工具在场会更准确。建议先跳过；包装脚本会在运行时检测，需要时再加 `--auto-install-prereqs`：

- `scrapling[fetchers]` — `pip install "scrapling[fetchers]" && scrapling install`
- `lightpanda` — 首次 auto-install 时下载到 `~/.local/bin/lightpanda`
- `agent-browser` — `npm install -g agent-browser && agent-browser install`

## 使用

收到 URL 后 skill 直接开跑，不再追问。默认值：

| 项 | 默认 |
|---|---|
| 模式 | 轻量模板审核（10 页） |
| 输出风格 | Operator |
| 性能 | 本地 Lighthouse — 首页，移动 + 桌面 |
| HTML 报告 | 开 |
| 输出语言 | English |

### 示例

| 你说 | skill 实际行为 |
|---|---|
| `Audit https://example.com` | 全部默认 |
| `帮我对 https://example.com 做一次 SEO 和 GEO 审核` | 同上（任何"审核"类措辞都会触发） |
| `审核 https://example.com，跑 50 页，用中文输出` | Template (50 页) + 中文报告 |
| `快速检查 https://example.com，跳过 Lighthouse` | Fast (1 页) + `--skip-pagespeed` |
| `深度审核 https://example.com，专家风格` | Specialist 输出风格 |
| `审核 https://example.com 50 页 用中文` | Template + 中文报告（更短的写法） |
| `帮我审核我的站点`（没给 URL） | 反问 URL — 唯一硬性要求 |

### 只在三种情况会问

- 没给 URL。
- 请求是非英文写的，但没说"用 X 语言输出"——只确认一次："输出用 English 还是 `<其他>`？"
- `--auto-install-prereqs` 要联网下载二进制（Lightpanda 等）时先确认。

报告默认 **English**，即使你的请求是中文写的也一样。只有显式说"用中文" / "in Chinese"或加 `--report-language` flag 才切换。

### 限制

- 抓取页数 1–50（`fast=1`、`light=10`、`template=50`；默认 `light`）。
- Lighthouse 默认 1 个首页 URL（mobile + desktop），最多 10 个（`--max-pagespeed-urls`）。
- SPA 路由扩展仍是采样逻辑，不是完整应用爬虫。
- 只通过 `dom_route_hint` / `route_guess` 找到的路由会被标为**辅助发现**，不算爬取证据。

## 终端使用

把 `${SKILL_DIR}` 换成 `~/.claude/skills/seo-geo-site-audit`。

```bash
"${SKILL_DIR}/scripts/audit-site" https://example.com \
  --mode template --output-style operator --html-report --report-language chinese
```

完整参数列表见 [`skills/seo-geo-site-audit/references/cli-flags.md`](skills/seo-geo-site-audit/references/cli-flags.md)。

Claude 补全 `final-report.json` 后，再渲染最终交付版 HTML：

```bash
"${SKILL_DIR}/scripts/render-report-html" \
  --report-json "${SKILL_DIR}/runs/site-audit-<host>-<stamp>/final-report.json" \
  --out "${SKILL_DIR}/runs/site-audit-<host>-<stamp>/audit-report.html"
```

### 产物

- `crawl.json` — 单页信号
- `pagespeed.json` — Lighthouse 数据（除非跳过）
- `audit-run.json` — 本次运行 manifest
- `evidence-report.html` — 原始证据 HTML（启用 `--html-report` 时）
- `final-report.json` — Claude 补全的种子 payload
- `audit-report.html` — 最终交付 HTML

## 爬虫对 SPA 的处理

每个 HTML 页面保留两条证据线：

- **`search_engine_visibility`** — raw Googlebot 风格 HTTP 基线，不执行 JS。
- **浏览器渲染证据** — SPA 在 JS 执行后展示给用户的内容。

只在渲染后出现的内容、导航、结构化数据或路由会被标为 JavaScript 依赖风险，而不是"Google 看不到"。只通过 `dom_route_hint` / `route_guess` 找到的页面属于审计辅助发现，不会写成搜索引擎可直接爬取。

## 安全说明

仓库设计为可安全公开克隆。

- 源码、文档、产物中都不应硬编码 API key / token / 密钥。
- Lighthouse 在本地运行，不需要第三方 API key。
- Chrome 沙箱默认开启；只在受信任的 root/CI/容器环境里通过 `SEO_GEO_ALLOW_NO_SANDBOX=1` 关闭。
- `--auto-install-prereqs` 是 opt-in。Lightpanda 二进制下载默认要求注册 SHA256，或显式设置 `SEO_GEO_ALLOW_UNVERIFIED_LIGHTPANDA=1`。

完整说明见 [`skills/seo-geo-site-audit/SECURITY.md`](skills/seo-geo-site-audit/SECURITY.md)。

## 贡献

欢迎 clone / fork。觉得有用的话顺手点个 star 就很感谢。遇到 bug 或有建议，欢迎提 issue。
