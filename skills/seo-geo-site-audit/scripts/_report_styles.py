"""Shared style tokens for the audit's two HTML renderers.

Both ``audit_site.build_html_report`` (evidence view) and
``render_report_html.build_html`` (final report) inline their own
component CSS, but they share the same Ollama-inspired palette and
font tokens. Defining those tokens here means a future palette
change lands in one place instead of two.

The component CSS (panels, navigation, scorecard, etc.) is still
per-renderer; only the ``:root`` block plus shared base resets are
centralized here.
"""
from __future__ import annotations


PALETTE_CSS = """    :root {
      color-scheme: light;
      --bg: #ffffff;
      --surface: #fafafa;
      --ink: #000000;
      --ink-near: #262626;
      --ink-button: #404040;
      --muted: #525252;
      --muted-soft: #737373;
      --silver: #a3a3a3;
      --line: #e5e5e5;
      --line-dark: #d4d4d4;
      --radius-container: 12px;
      --radius-pill: 9999px;
      --font-display: "SF Pro Rounded", "SF Pro Display", -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
      --font-body: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
    }
    * { box-sizing: border-box; }
"""
