"""Tests for plan.py — inc_token, adhoc_increment, prompt assembly, CLI."""

import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import plan  # noqa: E402


class IncTokenTests(unittest.TestCase):
    def test_numbered_increment_returns_zero_padded_number(self):
        inc = {"number": 14, "title": "anything"}
        self.assertEqual(plan.inc_token(inc), "0014")

    def test_numbered_increment_pads_single_digit(self):
        inc = {"number": 3, "title": "anything"}
        self.assertEqual(plan.inc_token(inc), "0003")

    def test_adhoc_with_title_uses_slug(self):
        inc = {"number": None, "title": "Design Dark Mode Toggle"}
        self.assertEqual(plan.inc_token(inc), "design_dark_mode_toggle")

    def test_adhoc_with_empty_title_falls_back_to_adhoc(self):
        inc = {"number": None, "title": ""}
        self.assertEqual(plan.inc_token(inc), "adhoc")

    def test_adhoc_truncates_long_titles_to_40_chars(self):
        inc = {"number": None, "title": "a" * 100}
        self.assertEqual(plan.inc_token(inc), "a" * 40)


class AdhocIncrementTests(unittest.TestCase):
    def test_shape_matches_parse_increment_keys(self):
        inc = plan.adhoc_increment("Design dark mode toggle")
        self.assertEqual(
            set(inc.keys()),
            {"number", "status", "title", "description",
             "principles", "acceptance_criteria", "raw", "path"},
        )

    def test_number_is_none_status_is_adhoc(self):
        inc = plan.adhoc_increment("anything")
        self.assertIsNone(inc["number"])
        self.assertEqual(inc["status"], "adhoc")
        self.assertIsNone(inc["path"])

    def test_title_truncates_to_60_chars(self):
        inc = plan.adhoc_increment("x" * 200)
        self.assertEqual(inc["title"], "x" * 60)

    def test_description_preserves_full_text(self):
        text = "Fix flaky upload test that intermittently hangs on CI"
        inc = plan.adhoc_increment(text)
        self.assertEqual(inc["description"], text)

    def test_strips_surrounding_whitespace(self):
        inc = plan.adhoc_increment("  design X  \n")
        self.assertEqual(inc["description"], "design X")
        self.assertEqual(inc["title"], "design X")

    def test_principles_and_criteria_default_empty(self):
        inc = plan.adhoc_increment("anything")
        self.assertEqual(inc["principles"], [])
        self.assertEqual(inc["acceptance_criteria"], [])


class TokenisedPathsTests(unittest.TestCase):
    def _inc(self, number=None, title="design X"):
        return {
            "number": number, "title": title, "description": title,
            "principles": [], "acceptance_criteria": ["the change is visible"],
            "raw": title, "path": None, "status": "adhoc" if number is None else "todo",
        }

    def test_state_before_numbered_uses_zero_padded_token(self):
        out = plan.state_before(self._inc(number=14))
        self.assertIn("/tmp/plan_before_0014.png", out)
        self.assertNotIn("{inc[", out)

    def test_state_before_adhoc_uses_slug_token(self):
        out = plan.state_before(self._inc(title="Design Dark Mode"))
        self.assertIn("/tmp/plan_before_design_dark_mode.png", out)

    def test_state_after_diff_line_is_substituted(self):
        out = plan.state_after(self._inc(number=14))
        # The diff line must contain real paths, never literal "{inc['number']:04d}".
        self.assertIn("/tmp/plan_before_0014.png", out)
        self.assertIn("/tmp/plan_after_0014.png", out)
        self.assertNotIn("{inc['number']", out)

    def test_verification_gate_paths_are_substituted(self):
        out = plan.verification_gates(self._inc(number=14))
        self.assertIn("/tmp/plan_before_0014.png", out)
        self.assertIn("/tmp/plan_after_0014.png", out)

    def test_tdd_plan_numbered_uses_increment_prefix(self):
        out = plan.tdd_plan(self._inc(number=14, title="Add Cache"))
        self.assertIn("tests/test_increment_0014_add_cache.py", out)

    def test_tdd_plan_adhoc_drops_increment_prefix(self):
        out = plan.tdd_plan(self._inc(title="Add Cache"))
        self.assertIn("tests/test_add_cache.py", out)
        self.assertNotIn("test_increment_", out)


class BuildPromptTests(unittest.TestCase):
    def _conventions(self):
        return {"X1": "# X1 principle body"}

    def _numbered(self):
        return {
            "number": 14, "status": "todo",
            "title": "Add cache layer",
            "description": "Add an in-memory cache layer in front of the API.",
            "principles": [], "acceptance_criteria": ["cache hits are logged"],
            "raw": "", "path": Path("/tmp/fake.md"),
        }

    def _adhoc(self):
        return plan.adhoc_increment("Design dark mode toggle")

    def test_numbered_header_includes_padded_number(self):
        out = plan.build_plan_prompt(self._numbered(), self._conventions())
        self.assertIn("# PLANNING PROMPT — Increment 0014", out)
        self.assertNotIn("# PLANNING PROMPT — Ad-hoc", out)

    def test_adhoc_header_says_ad_hoc(self):
        out = plan.build_plan_prompt(self._adhoc(), self._conventions())
        self.assertIn("# PLANNING PROMPT — Ad-hoc requirement", out)
        self.assertNotIn("Increment 0000", out)

    def test_opening_directive_present_in_both_modes(self):
        directive = "Read the conventions below once, then apply them."
        self.assertIn(directive, plan.build_plan_prompt(self._numbered(), self._conventions()))
        self.assertIn(directive, plan.build_plan_prompt(self._adhoc(), self._conventions()))

    def test_adhoc_requirement_note_present_only_in_adhoc(self):
        note = "Ad-hoc requirement (not tied to a numbered increment)"
        self.assertIn(note, plan.build_plan_prompt(self._adhoc(), self._conventions()))
        self.assertNotIn(note, plan.build_plan_prompt(self._numbered(), self._conventions()))

    def test_numbered_commit_section_uses_increment_template(self):
        out = plan.build_plan_prompt(self._numbered(), self._conventions())
        self.assertIn('git commit -m "increment 0014: add cache layer"', out)
        self.assertIn("./todo.sh", out)

    def test_adhoc_commit_section_uses_conventional_placeholder(self):
        out = plan.build_plan_prompt(self._adhoc(), self._conventions())
        self.assertIn('git commit -m "<type>(<scope>): <one-line summary>"', out)
        # The trailing "advance to the next increment" line is dropped in ad-hoc mode
        # (./todo.sh may still appear elsewhere as a fallback diff example).
        self.assertNotIn("verify and advance to the next increment", out)
        self.assertNotIn('increment 0000', out)


class CLITests(unittest.TestCase):
    def _run_main(self, argv):
        buf_out, buf_err = io.StringIO(), io.StringIO()
        with patch.object(sys, "argv", ["plan.py", *argv]), \
             patch("sys.stdout", buf_out), patch("sys.stderr", buf_err):
            try:
                plan.main()
            except SystemExit as e:
                return buf_out.getvalue(), buf_err.getvalue(), e.code
        return buf_out.getvalue(), buf_err.getvalue(), 0

    def test_freeform_args_trigger_adhoc_mode(self):
        out, err, code = self._run_main(["design", "dark", "mode", "toggle"])
        self.assertIn("# PLANNING PROMPT — Ad-hoc requirement", out)
        self.assertIn("design dark mode toggle", out)
        self.assertEqual(code, 0)

    def test_increment_plus_freeform_warns_and_uses_adhoc(self):
        out, err, code = self._run_main(["--increment=14", "design", "X"])
        self.assertIn("# PLANNING PROMPT — Ad-hoc requirement", out)
        self.assertIn("design X", out)
        self.assertIn("ignoring --increment", err.lower())
        self.assertEqual(code, 0)

    def test_all_principles_flag_unchanged(self):
        out, _, code = self._run_main(["--all-principles"])
        self.assertIn("## PROJECT CONVENTIONS", out)
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
