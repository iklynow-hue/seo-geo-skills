"""build_rendered_signal_delta: raw vs rendered status across the 7 signals."""
import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from crawl_sample import build_rendered_signal_delta, signal_status  # noqa: E402


class SignalStatusTests(unittest.TestCase):
    def test_both_present(self) -> None:
        self.assertEqual(signal_status(True, True), "raw_and_rendered")

    def test_raw_only(self) -> None:
        self.assertEqual(signal_status(True, False), "raw_only")

    def test_rendered_only(self) -> None:
        self.assertEqual(signal_status(False, True), "rendered_only")

    def test_missing(self) -> None:
        self.assertEqual(signal_status(False, False), "missing")


def _delta(**kwargs) -> dict:
    defaults = dict(
        raw_title="",
        rendered_title="",
        raw_meta_description="",
        rendered_meta_description="",
        raw_canonical="",
        rendered_canonical="",
        raw_h1_count=0,
        rendered_h1_count=0,
        raw_word_count=0,
        rendered_word_count=0,
        raw_internal_links=0,
        rendered_internal_links=0,
        dom_route_hint_links=0,
        raw_json_ld_types=[],
        rendered_json_ld_types=[],
    )
    defaults.update(kwargs)
    return build_rendered_signal_delta(**defaults)


class RenderedSignalDeltaTests(unittest.TestCase):
    def test_raw_baseline_complete(self) -> None:
        delta = _delta(
            raw_title="Title",
            rendered_title="Title",
            raw_meta_description="Description",
            rendered_meta_description="Description",
            raw_canonical="https://x.com/",
            rendered_canonical="https://x.com/",
            raw_h1_count=1,
            rendered_h1_count=1,
            raw_word_count=200,
            rendered_word_count=200,
            raw_internal_links=5,
            rendered_internal_links=5,
            raw_json_ld_types=["Organization"],
            rendered_json_ld_types=["Organization"],
        )
        self.assertEqual(delta["conclusion"], "raw_baseline_contains_primary_signals")
        self.assertEqual(delta["rendered_only_signals"], [])
        self.assertEqual(delta["missing_after_rendering"], [])

    def test_rendering_recovers_all(self) -> None:
        delta = _delta(
            rendered_title="Title",
            rendered_meta_description="D",
            rendered_canonical="https://x.com/",
            rendered_h1_count=1,
            rendered_word_count=200,
            rendered_internal_links=5,
            rendered_json_ld_types=["Organization"],
        )
        self.assertEqual(delta["conclusion"], "rendering_recovers_all_missing_primary_signals")
        self.assertEqual(set(delta["rendered_only_signals"]), {
            "title", "meta_description", "canonical", "h1", "body_words", "internal_links", "json_ld"
        })
        self.assertEqual(delta["missing_after_rendering"], [])

    def test_partial_recovery(self) -> None:
        delta = _delta(
            raw_title="Title",
            rendered_title="Title",
            rendered_meta_description="D",
            rendered_h1_count=1,
        )
        self.assertEqual(delta["conclusion"], "rendering_recovers_some_signals")
        self.assertIn("meta_description", delta["rendered_only_signals"])
        self.assertIn("canonical", delta["missing_after_rendering"])

    def test_signals_missing_after_rendering(self) -> None:
        delta = _delta(
            raw_title="Title",
            rendered_title="Title",
            raw_word_count=10,
            rendered_word_count=10,
        )
        self.assertEqual(delta["conclusion"], "signals_missing_after_rendering")
        self.assertIn("meta_description", delta["missing_after_rendering"])
        self.assertIn("canonical", delta["missing_after_rendering"])

    def test_h1_count_threshold(self) -> None:
        zero = _delta(raw_h1_count=0, rendered_h1_count=0)
        self.assertEqual(zero["signals"]["h1"]["status"], "missing")
        one = _delta(raw_h1_count=1, rendered_h1_count=2)
        self.assertEqual(one["signals"]["h1"]["status"], "raw_and_rendered")

    def test_body_words_threshold_50(self) -> None:
        below = _delta(raw_word_count=49, rendered_word_count=49)
        self.assertEqual(below["signals"]["body_words"]["status"], "missing")
        at = _delta(raw_word_count=50, rendered_word_count=50)
        self.assertEqual(at["signals"]["body_words"]["status"], "raw_and_rendered")


if __name__ == "__main__":
    unittest.main()
