"""Render-stability tests.

The HTML report renderer takes an agent-authored payload and must keep the
layout stable regardless of what prose the agent wrote. Specifically:

- Disallowed tags in the prose (e.g. <h1>, <a>, <script>) must NOT render
  as real elements that would break the card layout. They get escaped.
- The small allowlist of inline tags (<strong>, <em>, <code>, <br>,
  <small>) must pass through as actual HTML so emphasis still renders.
- The structural CSS classes that drive the layout grid must always be
  present in the output (no payload value can suppress them).
"""
import re
import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from render_report_html import build_html, sanitize_prose  # noqa: E402


def _minimal_payload(**overrides) -> dict:
    base = {
        "target_url": "https://example.com",
        "language": "english",
        "title": "Stability Test",
        "generated_at": "2026-05-19T00:00:00Z",
        "snapshot": [
            {"label": "Domain", "value": "example.com"},
            {"label": "Pages sampled", "value": "10"},
            {"label": "Performance check", "value": "Homepage (mobile + desktop)"},
        ],
        "section_scores": [
            {"section": "Technical SEO", "score": 50, "weight": "20%", "notes": "test"},
        ],
        "top_wins": ["A win"],
        "top_issues": ["An issue"],
        "sections": [
            {
                "title": "1. Technical SEO & Indexability",
                "score": 50,
                "passed_items": ["robots.txt present"],
                "issues": [
                    {"severity": "P0", "title": "site missing <h1>", "detail": "use a single <h1> per page"},
                ],
                "recommended_actions": ["Add an <h1> with the primary intent"],
            }
        ],
        "pagespeed_conclusion": {
            "mobile": {"average_performance": "71", "pattern": "moderate", "largest_issues": []},
            "desktop": {"average_performance": "100", "pattern": "perfect", "largest_issues": []},
        },
        "roadmap": {"P0": ["Fix <h1> coverage"], "P1": [], "P2": [], "P3": []},
        "method_notes": ["Sampled review."],
        "artifacts": [],
    }
    base.update(overrides)
    return base


class SanitizeProseTests(unittest.TestCase):
    def test_plain_text_pass_through(self):
        self.assertEqual(sanitize_prose("Plain text"), "Plain text")

    def test_strong_passes_through(self):
        self.assertEqual(sanitize_prose("<strong>X</strong>"), "<strong>X</strong>")

    def test_code_passes_through(self):
        self.assertEqual(sanitize_prose("<code>foo</code>"), "<code>foo</code>")

    def test_br_passes_through(self):
        self.assertEqual(sanitize_prose("a<br>b"), "a<br>b")

    def test_h1_escapes(self):
        self.assertEqual(sanitize_prose("missing <h1> tag"), "missing &lt;h1&gt; tag")

    def test_anchor_escapes(self):
        self.assertEqual(
            sanitize_prose('<a href="x">y</a>'),
            '&lt;a href="x"&gt;y&lt;/a&gt;',
        )

    def test_script_escapes(self):
        self.assertEqual(
            sanitize_prose("<script>alert(1)</script>"),
            "&lt;script&gt;alert(1)&lt;/script&gt;",
        )

    def test_pre_escaped_entity_preserved(self):
        # Agent already escaped the markup; sanitizer must not double-escape.
        self.assertEqual(
            sanitize_prose("pre-escaped &lt;link&gt; stays"),
            "pre-escaped &lt;link&gt; stays",
        )

    def test_mixed_allowed_and_disallowed(self):
        self.assertEqual(
            sanitize_prose("good <strong>x</strong> + bad <h2>y</h2>"),
            "good <strong>x</strong> + bad &lt;h2&gt;y&lt;/h2&gt;",
        )


class RenderStabilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.html = build_html(_minimal_payload())

    def test_layout_classes_present(self):
        # If any of these disappear, the layout grid is broken.
        for marker in (
            "snapshot-grid",
            "score-table",
            "scorecard-wrap",
            "issues-list",
            "issue-item",
            "action-list",
            "roadmap-grid",
            "roadmap-column",
        ):
            self.assertIn(marker, self.html, f"missing structural class: {marker}")

    def test_fixed_table_layout(self):
        # Scorecard must use table-layout: fixed so column widths are stable
        # against varying notes content.
        self.assertIn("table-layout: fixed", self.html)
        # And the colgroup widths are declared.
        for col in ("col-section", "col-score", "col-weight", "col-contrib", "col-notes"):
            self.assertIn(col, self.html)

    def test_main_width_locked(self):
        # All top-level boxes share one max-width on <main>.
        self.assertIn("max-width: 820px", self.html)

    def test_h1_in_issue_title_does_not_render_as_heading(self):
        # The agent wrote 'site missing <h1>' as a title. That literal <h1>
        # must NOT escape into the document as a real <h1> element (which
        # would blow up the card layout).
        body = self.html.split("<body>", 1)[1] if "<body>" in self.html else self.html
        # Strip the chrome <h1> in the hero section + any allowed h2/h3
        # in section/group headings.
        # Count occurrences of '<h1>' that appear *inside* an issue card.
        issue_cards = re.findall(
            r"<li class='issue-item[^']*'>.*?</li>",
            body,
            flags=re.DOTALL,
        )
        for card in issue_cards:
            self.assertNotIn("<h1>", card, f"raw <h1> leaked into issue card: {card[:200]}")
            self.assertNotIn("<h1 ", card)
            self.assertNotIn("</h1>", card)
        # And the escaped form should be present
        joined = "".join(issue_cards)
        self.assertIn("&lt;h1&gt;", joined)

    def test_strong_in_recommended_action_passes_through(self):
        # Recommended action items support inline emphasis; verify by adding
        # a known marker.
        payload = _minimal_payload()
        payload["sections"][0]["recommended_actions"] = [
            "<strong>Bold action</strong> and a <code>flag</code>",
        ]
        out = build_html(payload)
        self.assertIn("<strong>Bold action</strong>", out)
        self.assertIn("<code>flag</code>", out)

    def test_severity_stripe_classes_present(self):
        # tier-pX class on the <li> drives the left stripe; without it the
        # severity edge would not render.
        payload = _minimal_payload()
        payload["sections"][0]["issues"] = [
            {"severity": s, "title": f"{s} title", "detail": "x"}
            for s in ("P0", "P1", "P2", "P3")
        ]
        out = build_html(payload)
        for tier in ("tier-p0", "tier-p1", "tier-p2", "tier-p3"):
            self.assertIn(tier, out, f"missing tier class: {tier}")

    def test_unknown_severity_falls_back(self):
        payload = _minimal_payload()
        payload["sections"][0]["issues"] = [
            {"severity": "Critical", "title": "Unknown severity", "detail": "x"}
        ]
        out = build_html(payload)
        # Falls back to the generic tier — must still render an issue-item.
        self.assertIn("tier-generic", out)
        self.assertIn("Unknown severity", out)

    def test_long_unbreakable_token_does_not_overflow_layout(self):
        # A 200-char no-space token must still be wrapped inside the card.
        # We can't measure layout here, but CSS rule overflow-wrap: anywhere
        # plus word-break: break-word must be in the stylesheet so the
        # browser will break the token.
        self.assertIn("overflow-wrap: anywhere", self.html)
        self.assertIn("word-break: break-word", self.html)

    def test_powered_by_link_present(self):
        # Hero footer chip links to the repo by default.
        self.assertIn("github.com/iklynow-hue/seo-geo-skills", self.html)


if __name__ == "__main__":
    unittest.main()
