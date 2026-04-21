# SEO GEO Skills

Public skill repo for:

- `skills/seo-geo-site-audit/`

This skill works with both Codex and Claude Code for sampled SEO + GEO audits of public sites, with:

- capped crawling up to 25 pages
- template-aware sampling
- local Lighthouse by default
- optional PageSpeed API support
- optional bilingual HTML reporting

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

Current performance choices:

- `1. Local Lighthouse (recommended)`
- `2. Skip PageSpeed`
- `3. Use existing PageSpeed API key from env`
- `4. I will paste the API key in chat`

If HTML output is enabled, the follow-up language choices are:

- `1. English`
- `2. Chinese`
- `3. Other (type it in)`

## Terminal Usage

Use the wrapper for normal runs:

```bash
~/.agents/skills/seo-geo-site-audit/scripts/audit-site \
  https://example.com \
  --mode template \
  --output-style operator
```

Useful options:

- `--mode fast|light|template`
- `--max-pages 1-25`
- `--output-style boss|operator|specialist`
- `--pagespeed-provider local|api|api_with_fallback`
- `--api-key YOUR_KEY`
- `--skip-pagespeed`
- `--html-report`
- `--report-language english|chinese`
- `--fetcher auto|scrapling|lightpanda|agent_browser|urllib`
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

Please do not open pull requests for this repository. The maintainer is not reviewing PRs right now.

If you need to report a bug or suggest an improvement, open an issue instead.

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

当前性能选项：

- `1. Local Lighthouse (recommended)`
- `2. Skip PageSpeed`
- `3. Use existing PageSpeed API key from env`
- `4. I will paste the API key in chat`

如果开启 HTML 输出，还会继续询问：

- `1. English`
- `2. Chinese`
- `3. Other (type it in)`

## 终端使用

正常运行请使用包装脚本：

```bash
~/.agents/skills/seo-geo-site-audit/scripts/audit-site \
  https://example.com \
  --mode template \
  --output-style operator
```

常用参数：

- `--mode fast|light|template`
- `--max-pages 1-25`
- `--output-style boss|operator|specialist`
- `--pagespeed-provider local|api|api_with_fallback`
- `--api-key YOUR_KEY`
- `--skip-pagespeed`
- `--html-report`
- `--report-language english|chinese`
- `--fetcher auto|scrapling|lightpanda|agent_browser|urllib`
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

请不要为这个仓库提交 Pull Request，维护者目前没有时间审核 PR。

如果你想反馈 bug 或建议改进，请直接提交 issue。
