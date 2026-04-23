# SEO GEO Skills

Public skill repo for:

- `skills/seo-geo-site-audit/`

This skill works with both Codex and Claude Code for sampled SEO + GEO audits of public sites, with:

- capped crawling up to 50 pages
- template-aware sampling
- local Lighthouse by default
- PageSpeed API support through a skill-local `.env`
- final polished HTML reporting from the same structured content as the written audit

## Install

Clone the repo:

```bash
git clone https://github.com/iklynow-hue/seo-geo-skills
cd seo-geo-skills
```

Link the skill into your local skills folder:

```bash
mkdir -p ~/.agents/skills
ln -s "$PWD/skills/seo-geo-site-audit" ~/.agents/skills/seo-geo-site-audit
```

For Claude Code, the skill also includes a local [CLAUDE.md](skills/seo-geo-site-audit/CLAUDE.md) entry file.

If you want to use PageSpeed API mode, create a local env file inside the skill directory:

```bash
cp skills/seo-geo-site-audit/.env.example skills/seo-geo-site-audit/.env
```

Then edit `skills/seo-geo-site-audit/.env` and set:

```bash
PAGESPEED_API_KEY=your_key_here
```

## Update

If your local install is a symlink, updating is simple:

```bash
cd seo-geo-skills
git pull
```

Because `~/.agents/skills/seo-geo-site-audit` points at this repo folder, the skill updates immediately after the pull.

If you copied the skill instead of symlinking it, replace the local folder with the newer `skills/seo-geo-site-audit` contents from this repo.

## Quick Start

The simplest way to try it:

1. Clone this repo and link the skill folder.
2. Open Codex or Claude Code.
3. Paste:

```text
Use $seo-geo-site-audit to audit https://example.com
```

4. Answer the setup questions one by one.
5. Let the wrapper run and review the generated artifacts.

Current implementation limits to know up front:

- crawl cap: `1` to `50` pages
- audit presets: `fast=1`, `light=10`, `template=50`
- default audit scope: `light=10`
- PageSpeed / performance test URLs: default `5`, maximum `10`
- best-effort SPA route expansion is capped and still sample-based, not a full app crawler

## Use Cases

Use `seo-geo-site-audit` when you want:

- an SEO audit
- a GEO / AI visibility audit
- a sampled site-quality review instead of a full crawl
- a scored report with evidence, issues, and recommended actions
- HTML output for sharing

## Chat Usage

Start with:

```text
Use $seo-geo-site-audit to audit https://example.com
```

The skill is designed to ask setup questions one by one before crawling:

1. Scope
2. Output style
3. Performance evidence mode
4. HTML report on/off
5. Final output language

Language confirmation is mandatory for the skill flow. The audit should not proceed to the final report until the user confirms the language or explicitly accepts the default English.

If you already know your preferences, you can put them in the first prompt and skip the questionnaire. If scope, output style, PageSpeed handling, HTML on/off, and final language are all clearly stated, the agent should use them directly instead of asking again.

Example:

```text
Use $seo-geo-site-audit to audit https://example.com with light mode, Operator output, PageSpeed API from the skill .env, HTML report on, and final report in Chinese.
```

Default first test:

- choose `Local Lighthouse`
- keep the default output style
- start with the default `10-page` light audit
- turn HTML on if you want a shareable artifact

Current performance choices:

- `1. Local Lighthouse (default)`
- `2. Skip PageSpeed`
- `3. Use PageSpeed API from the skill .env`

If you choose the API path, save the key in:

- `skills/seo-geo-site-audit/.env`

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

Use the wrapper for normal runs:

```bash
~/.agents/skills/seo-geo-site-audit/scripts/audit-site \
  https://example.com \
  --output-style operator
```

Example with HTML output in Chinese:

```bash
~/.agents/skills/seo-geo-site-audit/scripts/audit-site \
  https://example.com \
  --mode template \
  --output-style operator \
  --html-report \
  --report-language chinese
```

Then render the polished final HTML after you fill `final-report.json`:

```bash
~/.agents/skills/seo-geo-site-audit/scripts/render-report-html \
  --report-json ~/.agents/skills/seo-geo-site-audit/runs/site-audit-example.com-<stamp>/final-report.json \
  --out ~/.agents/skills/seo-geo-site-audit/runs/site-audit-example.com-<stamp>/audit-report.html
```

Useful options:

- `--mode fast|light|template` which map to `1`, `10`, and `50` pages
- `--max-pages 1-50`
- `--output-style boss|operator|specialist`
- `--max-pagespeed-urls 1-10`
- `--pagespeed-provider local|api|api_with_fallback`
- `--skip-pagespeed`
- `--html-report`
- `--report-language english|chinese` for the wrapper's evidence HTML and seeded final report payload
- `--fetcher auto|scrapling|lightpanda|agent_browser|chrome|urllib`
- `--local-lighthouse-fallback` as a compatibility alias for `api_with_fallback`
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

1. The wrapper gathers crawl and performance evidence.
2. The wrapper writes `evidence-report.html` and seeds `final-report.json`.
3. The agent writes the final audit in the selected language and fills `final-report.json`.
4. The renderer turns that payload into the final `audit-report.html`.

## Security

This repo is intended to be safe for public cloning.

- No API keys should ever be hardcoded in source, docs, or artifacts.
- PageSpeed keys should only come from:
  - `skills/seo-geo-site-audit/.env`
  - `PAGESPEED_API_KEY`
  - `GOOGLE_API_KEY`
- The code should only persist `api_key_used: true/false`, never the key itself.

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

这个技能同时适用于 Codex 和 Claude Code，用于对公开网站进行采样式 SEO + GEO 审核，支持：

- 最多 50 页的上限抓取
- 按模板类型抽样
- 默认使用本地 Lighthouse
- 通过技能目录下的 `.env` 接入 PageSpeed API
- 基于与终端报告相同结构内容生成最终 HTML 报告

## 安装

克隆仓库：

```bash
git clone https://github.com/iklynow-hue/seo-geo-skills
cd seo-geo-skills
```

将技能链接到本地 skills 目录：

```bash
mkdir -p ~/.agents/skills
ln -s "$PWD/skills/seo-geo-site-audit" ~/.agents/skills/seo-geo-site-audit
```

对于 Claude Code，这个技能也包含了本地入口文件 [CLAUDE.md](skills/seo-geo-site-audit/CLAUDE.md)。

如果你要使用 PageSpeed API 模式，请先在技能目录中创建本地 env 文件：

```bash
cp skills/seo-geo-site-audit/.env.example skills/seo-geo-site-audit/.env
```

然后编辑 `skills/seo-geo-site-audit/.env`，填入：

```bash
PAGESPEED_API_KEY=your_key_here
```

## 更新

如果你的本地安装方式是符号链接，更新会很简单：

```bash
cd seo-geo-skills
git pull
```

因为 `~/.agents/skills/seo-geo-site-audit` 直接指向这个仓库目录，所以 pull 完就会立即生效。

如果你不是用符号链接，而是手动复制技能目录，那么请用仓库里的 `skills/seo-geo-site-audit` 覆盖你本地那份旧目录。

## 快速开始

最简单的体验方式：

1. 克隆仓库并链接技能目录。
2. 打开 Codex 或 Claude Code。
3. 粘贴这句：

```text
Use $seo-geo-site-audit to audit https://example.com
```

4. 按顺序回答配置问题。
5. 等待包装脚本运行完成，并查看生成的产物。

当前实现的几个限制，建议先了解：

- 抓取页数范围：`1` 到 `50`
- 预设模式：`fast=1`、`light=10`、`template=50`
- 默认抓取范围：`light=10`
- PageSpeed / 性能检测 URL 数：默认 `5`，最大 `10`
- SPA 的最佳努力扩展仍然是采样逻辑，不是完整应用爬虫

## 适用场景

当你需要以下能力时，可以使用 `seo-geo-site-audit`：

- SEO 审核
- GEO / AI 可见性审核
- 采样式站点质量检查，而不是全站爬取
- 带评分、证据、问题和修复建议的结构化报告
- HTML 报告导出

## 聊天中使用

可以这样开始：

```text
Use $seo-geo-site-audit to audit https://example.com
```

在正式抓取前，技能会按顺序逐个确认：

1. 抓取范围
2. 输出风格
3. 性能证据模式
4. 是否生成 HTML 报告
5. 最后再询问输出语言

默认首次测试建议：

- 优先选择 `Local Lighthouse`
- 输出风格先保持默认
- 先用默认的 `10` 页 light audit
- 如果你想拿到可分享的产物，可以打开 HTML 输出

当前性能选项：

- `1. Local Lighthouse (default)`
- `2. Skip PageSpeed`
- `3. Use PageSpeed API from the skill .env`

如果你选择 API 路径，请先把 key 保存到：

- `skills/seo-geo-site-audit/.env`

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

正常运行请使用包装脚本：

```bash
~/.agents/skills/seo-geo-site-audit/scripts/audit-site \
  https://example.com \
  --output-style operator
```

中文 HTML 报告示例：

```bash
~/.agents/skills/seo-geo-site-audit/scripts/audit-site \
  https://example.com \
  --mode template \
  --output-style operator \
  --html-report \
  --report-language chinese
```

补全 `final-report.json` 后，再渲染最终交付版 HTML：

```bash
~/.agents/skills/seo-geo-site-audit/scripts/render-report-html \
  --report-json ~/.agents/skills/seo-geo-site-audit/runs/site-audit-example.com-<stamp>/final-report.json \
  --out ~/.agents/skills/seo-geo-site-audit/runs/site-audit-example.com-<stamp>/audit-report.html
```

常用参数：

- `--mode fast|light|template`，分别对应 `1`、`10`、`50` 页
- `--max-pages 1-50`
- `--output-style boss|operator|specialist`
- `--max-pagespeed-urls 1-10`
- `--pagespeed-provider local|api|api_with_fallback`
- `--skip-pagespeed`
- `--html-report`
- `--report-language english|chinese`，用于包装脚本的证据页 HTML 和最终报告种子 JSON
- `--fetcher auto|scrapling|lightpanda|agent_browser|chrome|urllib`
- `--local-lighthouse-fallback`，作为 `api_with_fallback` 的兼容别名
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

1. 包装脚本先收集抓取与性能证据。
2. 包装脚本写出 `evidence-report.html`，并生成 `final-report.json` 种子。
3. agent 用所选语言写出最终审核结论，并补全 `final-report.json`。
4. 渲染器再将其转换为最终的 `audit-report.html`。

## 安全说明

这个仓库设计为可安全公开克隆。

- 任何 API key 都不应该被硬编码到源码、文档或产物中。
- PageSpeed key 只应该来自：
  - `skills/seo-geo-site-audit/.env`
  - `PAGESPEED_API_KEY`
  - `GOOGLE_API_KEY`
- 代码只应保存 `api_key_used: true/false`，绝不能保存真实 key。

更多说明见：

- [skills/seo-geo-site-audit/SECURITY.md](skills/seo-geo-site-audit/SECURITY.md)

## 贡献策略

欢迎 clone 和 fork。

如果你觉得这个仓库对你有帮助，欢迎顺手点一个 star。

如果你遇到 bug，或者有改进建议，欢迎提交 issue。
