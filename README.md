# SEO GEO Skills

Public skill repo for:

- `skills/seo-geo-site-audit/`

This skill works with both Codex and Claude Code for sampled SEO + GEO audits of public sites, with:

- capped crawling up to 25 pages
- template-aware sampling
- local Lighthouse by default
- optional PageSpeed API support
- built-in HTML reporting in English or Chinese

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

- crawl cap: `1` to `25` pages
- audit presets: `fast=1`, `light=10`, `template=25`
- PageSpeed / performance test URLs: default `5`, maximum `10`
- built-in static HTML localization: English and Chinese

## Use Cases

Use `seo-geo-site-audit` when you want:

- an SEO audit
- a GEO / AI visibility audit
- a sampled site-quality review instead of a full crawl
- a scored report with evidence, issues, and recommended actions
- optional HTML output for sharing

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
5. HTML report language, only if HTML output is enabled

Recommended first test:

- choose `Local Lighthouse`
- keep the default output style
- start with a fast check or template audit
- turn HTML on if you want a shareable artifact

Current performance choices:

- `1. Local Lighthouse (recommended)`
- `2. Skip PageSpeed`
- `3. Use existing PageSpeed API key from env`
- `4. I will paste the API key in chat`

If HTML output is enabled, the follow-up language choices are:

- `1. English`
- `2. Chinese`
- `3. Other (type it in)`

Code note:

- the wrapper's built-in static HTML localization currently supports English and Chinese
- if you pass another value to `--report-language`, the HTML artifact currently falls back to English

If the agent skips the setup questions, you can prompt it more explicitly:

```text
Use $seo-geo-site-audit to audit https://example.com. Ask me the setup questions one by one with numbered options for scope, output style, performance handling, HTML report, and report language before you begin.
```

## Terminal Usage

Use the wrapper for normal runs:

```bash
~/.agents/skills/seo-geo-site-audit/scripts/audit-site \
  https://example.com \
  --mode template \
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

Useful options:

- `--mode fast|light|template` which map to `1`, `10`, and `25` pages
- `--max-pages 1-25`
- `--output-style boss|operator|specialist`
- `--max-pagespeed-urls 1-10`
- `--pagespeed-provider local|api|api_with_fallback`
- `--api-key YOUR_KEY`
- `--prompt-pagespeed-key`
- `--skip-pagespeed`
- `--html-report`
- `--report-language english|chinese`
- `--fetcher auto|scrapling|lightpanda|agent_browser|urllib`
- `--local-lighthouse-fallback` as a compatibility alias for `api_with_fallback`
- `--auto-install-prereqs`
- `--skip-prereq-check`
- `--out-dir /path/to/output`

Artifacts:

- `crawl.json`
- `pagespeed.json` unless skipped
- `audit-run.json`
- `audit-report.html` when HTML output is enabled

## Security

This repo is intended to be safe for public cloning.

- No API keys should ever be hardcoded in source, docs, or artifacts.
- PageSpeed keys should only come from:
  - `PAGESPEED_API_KEY`
  - `GOOGLE_API_KEY`
  - a one-off key provided by the user in the current chat/session
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

- 最多 25 页的上限抓取
- 按模板类型抽样
- 默认使用本地 Lighthouse
- 可选接入 PageSpeed API
- 可选双语 HTML 报告

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

- 抓取页数范围：`1` 到 `25`
- 预设模式：`fast=1`、`light=10`、`template=25`
- PageSpeed / 性能检测 URL 数：默认 `5`，最大 `10`
- 内置静态 HTML 本地化目前支持英文和中文

## 适用场景

当你需要以下能力时，可以使用 `seo-geo-site-audit`：

- SEO 审核
- GEO / AI 可见性审核
- 采样式站点质量检查，而不是全站爬取
- 带评分、证据、问题和修复建议的结构化报告
- 可选 HTML 报告导出

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
5. 如果开启 HTML，询问报告语言

第一次测试建议：

- 优先选择 `Local Lighthouse`
- 输出风格先保持默认
- 先做 fast check 或 template audit
- 如果你想拿到可分享的产物，可以打开 HTML 输出

当前性能选项：

- `1. Local Lighthouse (recommended)`
- `2. Skip PageSpeed`
- `3. Use existing PageSpeed API key from env`
- `4. I will paste the API key in chat`

如果开启 HTML 输出，还会继续询问：

- `1. English`
- `2. Chinese`
- `3. Other (type it in)`

代码层面的当前说明：

- 包装脚本内置的静态 HTML 本地化目前只支持英文和中文
- 如果传入其他 `--report-language` 值，当前 HTML 产物会回退到英文

如果 agent 没有主动逐项提问，可以更明确地这样说：

```text
Use $seo-geo-site-audit to audit https://example.com. Ask me the setup questions one by one with numbered options for scope, output style, performance handling, HTML report, and report language before you begin.
```

## 终端使用

正常运行请使用包装脚本：

```bash
~/.agents/skills/seo-geo-site-audit/scripts/audit-site \
  https://example.com \
  --mode template \
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

常用参数：

- `--mode fast|light|template`，分别对应 `1`、`10`、`25` 页
- `--max-pages 1-25`
- `--output-style boss|operator|specialist`
- `--max-pagespeed-urls 1-10`
- `--pagespeed-provider local|api|api_with_fallback`
- `--api-key YOUR_KEY`
- `--prompt-pagespeed-key`
- `--skip-pagespeed`
- `--html-report`
- `--report-language english|chinese`
- `--fetcher auto|scrapling|lightpanda|agent_browser|urllib`
- `--local-lighthouse-fallback`，作为 `api_with_fallback` 的兼容别名
- `--auto-install-prereqs`
- `--skip-prereq-check`
- `--out-dir /path/to/output`

输出产物：

- `crawl.json`
- `pagespeed.json`，如果没有跳过
- `audit-run.json`
- `audit-report.html`，当启用 HTML 输出时生成

## 安全说明

这个仓库设计为可安全公开克隆。

- 任何 API key 都不应该被硬编码到源码、文档或产物中。
- PageSpeed key 只应该来自：
  - `PAGESPEED_API_KEY`
  - `GOOGLE_API_KEY`
  - 用户在当前聊天 / 会话中一次性提供的 key
- 代码只应保存 `api_key_used: true/false`，绝不能保存真实 key。

更多说明见：

- [skills/seo-geo-site-audit/SECURITY.md](skills/seo-geo-site-audit/SECURITY.md)

## 贡献策略

欢迎 clone 和 fork。

如果你觉得这个仓库对你有帮助，欢迎顺手点一个 star。

如果你遇到 bug，或者有改进建议，欢迎提交 issue。
