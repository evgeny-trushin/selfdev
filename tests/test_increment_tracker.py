"""Tests for the IncrementTracker module.

Covers: discovery, parsing (strict + flexible), completeness checks,
principle resolution, lifecycle (mark_done), prompt generation,
self-inspection prompts, done summaries, and revert/redo helpers.
"""

import shutil
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from increment_tracker import IncrementTracker
from analyzers import GitAnalyzer


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def _make_increment(req_dir: Path, number: int, status: str = "todo",
                    short_desc: str = "feature", content: str = None) -> Path:
    """Create an increment file with sensible default content."""
    filename = f"increment_{number:04d}_{status}_{short_desc}.md"
    path = req_dir / filename
    if content is None:
        content = textwrap.dedent(f"""\
            # Increment {number:04d}: Feature {number}

            **Requirement ID:** R{number}

            ## Description
            Implement feature {number}.

            ## Acceptance Criteria
            - [ ] Feature {number} works
            - [ ] Tests pass

            ## Related Principles
            - [B1](../principles/B1.md)
        """)
    path.write_text(content, encoding="utf-8")
    return path


def _make_principle(prin_dir: Path, code: str,
                    content: str = None) -> Path:
    """Create a principle file."""
    path = prin_dir / f"{code}.md"
    if content is None:
        content = f"# {code} — Principle\nContent for {code}."
    path.write_text(content, encoding="utf-8")
    return path


class _TrackerTestCase(unittest.TestCase):
    """Base class that sets up a temp dir with requirements/ and principles/."""

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.req_dir = self.tmp_dir / "requirements"
        self.req_dir.mkdir()
        self.prin_dir = self.tmp_dir / "principles"
        self.prin_dir.mkdir()
        _make_principle(self.prin_dir, "B1")
        _make_principle(self.prin_dir, "P2")
        self.tracker = IncrementTracker(self.tmp_dir)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)


# -------------------------------------------------------------------
# Discovery
# -------------------------------------------------------------------

class TestDiscovery(_TrackerTestCase):
    """Tests for _increment_files, current_todo, done_count, etc."""

    def test_no_files(self):
        self.assertIsNone(self.tracker.current_todo())
        self.assertEqual(self.tracker.done_count(), 0)
        self.assertEqual(self.tracker.total_count(), 0)
        self.assertTrue(self.tracker.all_done())

    def test_single_todo(self):
        _make_increment(self.req_dir, 1)
        self.assertIsNotNone(self.tracker.current_todo())
        self.assertIn("0001", self.tracker.current_todo().name)
        self.assertFalse(self.tracker.all_done())

    def test_current_todo_returns_lowest(self):
        _make_increment(self.req_dir, 3)
        _make_increment(self.req_dir, 1)
        _make_increment(self.req_dir, 2)
        self.assertIn("0001", self.tracker.current_todo().name)

    def test_done_count(self):
        _make_increment(self.req_dir, 1, status="done")
        _make_increment(self.req_dir, 2, status="done")
        _make_increment(self.req_dir, 3, status="todo")
        self.assertEqual(self.tracker.done_count(), 2)

    def test_total_count(self):
        _make_increment(self.req_dir, 1, status="done")
        _make_increment(self.req_dir, 2, status="todo")
        self.assertEqual(self.tracker.total_count(), 2)

    def test_all_done_when_only_done_files(self):
        _make_increment(self.req_dir, 1, status="done")
        _make_increment(self.req_dir, 2, status="done")
        self.assertTrue(self.tracker.all_done())

    def test_not_all_done_with_mixed(self):
        _make_increment(self.req_dir, 1, status="done")
        _make_increment(self.req_dir, 2, status="todo")
        self.assertFalse(self.tracker.all_done())

    def test_current_todo_skips_done(self):
        _make_increment(self.req_dir, 1, status="done")
        _make_increment(self.req_dir, 2, status="done")
        _make_increment(self.req_dir, 3, status="todo")
        self.assertIn("0003", self.tracker.current_todo().name)


# -------------------------------------------------------------------
# Parsing — strict format
# -------------------------------------------------------------------

class TestParseStrict(_TrackerTestCase):
    """Tests for parse_increment with standard ## heading format."""

    def test_basic_fields(self):
        path = _make_increment(self.req_dir, 1)
        data = IncrementTracker.parse_increment(path)
        self.assertEqual(data["number"], 1)
        self.assertEqual(data["status"], "todo")
        self.assertEqual(data["requirement_id"], "R1")
        self.assertIn("feature 1", data["description"].lower())
        self.assertTrue(len(data["acceptance_criteria"]) >= 2)

    def test_title_extraction(self):
        path = _make_increment(self.req_dir, 5, short_desc="cool_stuff")
        data = IncrementTracker.parse_increment(path)
        self.assertIn("Feature 5", data["title"])

    def test_short_desc_from_filename(self):
        path = _make_increment(self.req_dir, 7, short_desc="multi_word_desc")
        data = IncrementTracker.parse_increment(path)
        self.assertEqual(data["short_desc"], "multi_word_desc")

    def test_status_todo(self):
        path = _make_increment(self.req_dir, 1, status="todo")
        data = IncrementTracker.parse_increment(path)
        self.assertEqual(data["status"], "todo")

    def test_status_done(self):
        path = _make_increment(self.req_dir, 1, status="done")
        data = IncrementTracker.parse_increment(path)
        self.assertEqual(data["status"], "done")

    def test_related_principles_extracted(self):
        path = _make_increment(self.req_dir, 1)
        data = IncrementTracker.parse_increment(path)
        self.assertTrue(len(data["related_principles"]) >= 1)
        codes = [c for c, _ in data["related_principles"]]
        self.assertIn("B1", codes)

    def test_acceptance_criteria_checkbox_stripped(self):
        content = textwrap.dedent("""\
            # Inc 1

            **Requirement ID:** R1

            ## Description
            Do the thing.

            ## Acceptance Criteria
            - [ ] First criterion
            - [x] Second criterion
            - Third criterion
        """)
        path = _make_increment(self.req_dir, 1, content=content)
        data = IncrementTracker.parse_increment(path)
        self.assertEqual(data["acceptance_criteria"][0], "First criterion")
        self.assertEqual(data["acceptance_criteria"][1], "Second criterion")
        self.assertEqual(data["acceptance_criteria"][2], "Third criterion")

    def test_raw_content_preserved(self):
        path = _make_increment(self.req_dir, 1)
        data = IncrementTracker.parse_increment(path)
        self.assertIn("## Description", data["raw_content"])

    def test_multiple_principles(self):
        content = textwrap.dedent("""\
            # Inc 1

            **Requirement ID:** R1

            ## Description
            Something.

            ## Related Principles
            - [B1](../principles/B1.md)
            - [P2 — Random Entry](../principles/P2.md)
        """)
        path = _make_increment(self.req_dir, 1, content=content)
        data = IncrementTracker.parse_increment(path)
        codes = [c for c, _ in data["related_principles"]]
        self.assertIn("B1", codes)
        self.assertIn("P2", codes)


# -------------------------------------------------------------------
# Parsing — flexible fallback format
# -------------------------------------------------------------------

class TestParseFlexible(_TrackerTestCase):
    """Tests for pass-2 flexible fallback parsing."""

    def test_heading_any_level(self):
        """### heading is used when no # heading exists."""
        content = "### W6: Screenshot Feature\nImplement screenshots.\n"
        path = _make_increment(self.req_dir, 6, content=content)
        data = IncrementTracker.parse_increment(path)
        self.assertIn("Screenshot", data["title"])

    def test_requirement_id_from_heading(self):
        """Requirement ID extracted from heading prefix like 'W6:'."""
        content = "### W6: Screenshot Feature\nDo stuff.\n"
        path = _make_increment(self.req_dir, 6, content=content)
        data = IncrementTracker.parse_increment(path)
        self.assertEqual(data["requirement_id"], "W6")

    def test_description_fallback_body_text(self):
        """Description from body text between heading and section marker."""
        content = textwrap.dedent("""\
            ### R1: My Feature

            This is the description.
            It has multiple lines.

            **Acceptance Criteria:**
            1. Do thing
        """)
        path = _make_increment(self.req_dir, 1, content=content)
        data = IncrementTracker.parse_increment(path)
        self.assertIn("description", data["description"].lower())

    def test_bold_acceptance_criteria(self):
        """Acceptance criteria from **Acceptance Criteria:** bold format."""
        content = textwrap.dedent("""\
            ### R1: Feature

            Description here.

            **Acceptance Criteria:**
            1. First thing
            2. Second thing
        """)
        path = _make_increment(self.req_dir, 1, content=content)
        data = IncrementTracker.parse_increment(path)
        self.assertEqual(len(data["acceptance_criteria"]), 2)
        self.assertEqual(data["acceptance_criteria"][0], "First thing")
        self.assertEqual(data["acceptance_criteria"][1], "Second thing")

    def test_bold_related_principles(self):
        """Related principles from **Related Principles:** bold format."""
        content = textwrap.dedent("""\
            ### R1: Feature

            Description here.

            **Related Principles:**
            - [B1](../principles/B1.md)
        """)
        path = _make_increment(self.req_dir, 1, content=content)
        data = IncrementTracker.parse_increment(path)
        codes = [c for c, _ in data["related_principles"]]
        self.assertIn("B1", codes)

    def test_title_fallback_to_short_desc(self):
        """When no heading at all, title falls back to short_desc."""
        content = "Just some text without headings.\n"
        path = _make_increment(self.req_dir, 1, short_desc="my_thing",
                               content=content)
        data = IncrementTracker.parse_increment(path)
        self.assertEqual(data["title"], "my_thing")

    def test_numbered_criteria_stripped(self):
        """Numbered list prefixes are stripped from criteria."""
        content = textwrap.dedent("""\
            ### R1: Feature

            Description.

            **Acceptance Criteria:**
            1. Alpha
            2. Beta
        """)
        path = _make_increment(self.req_dir, 1, content=content)
        data = IncrementTracker.parse_increment(path)
        self.assertEqual(data["acceptance_criteria"][0], "Alpha")
        self.assertEqual(data["acceptance_criteria"][1], "Beta")


# -------------------------------------------------------------------
# Parse completeness
# -------------------------------------------------------------------

class TestParseCompleteness(_TrackerTestCase):
    """Tests for _is_parse_complete."""

    def test_complete_with_description(self):
        path = _make_increment(self.req_dir, 1)
        data = IncrementTracker.parse_increment(path)
        self.assertTrue(IncrementTracker._is_parse_complete(data))

    def test_incomplete_empty_description(self):
        data = {"description": "", "title": "X"}
        self.assertFalse(IncrementTracker._is_parse_complete(data))

    def test_incomplete_whitespace_description(self):
        data = {"description": "   \n  ", "title": "X"}
        self.assertFalse(IncrementTracker._is_parse_complete(data))

    def test_incomplete_missing_description_key(self):
        data = {"title": "X"}
        self.assertFalse(IncrementTracker._is_parse_complete(data))


# -------------------------------------------------------------------
# Principle loading and resolution
# -------------------------------------------------------------------

class TestPrincipleResolution(_TrackerTestCase):
    """Tests for load_principle and resolve_principles."""

    def test_load_existing_principle(self):
        content = self.tracker.load_principle("B1")
        self.assertIsNotNone(content)
        self.assertIn("B1", content)

    def test_load_missing_principle(self):
        content = self.tracker.load_principle("NONEXISTENT")
        self.assertIsNone(content)

    def test_resolve_principles(self):
        refs = [("B1", "../principles/B1.md"), ("P2", "../principles/P2.md")]
        resolved = self.tracker.resolve_principles(refs)
        self.assertEqual(len(resolved), 2)
        codes = [r["code"] for r in resolved]
        self.assertIn("B1", codes)
        self.assertIn("P2", codes)

    def test_resolve_principles_deduplicates(self):
        refs = [("B1", "../principles/B1.md"), ("B1", "../principles/B1.md")]
        resolved = self.tracker.resolve_principles(refs)
        self.assertEqual(len(resolved), 1)

    def test_resolve_principles_skips_missing(self):
        refs = [("B1", "../principles/B1.md"), ("ZZZ", "../principles/ZZZ.md")]
        resolved = self.tracker.resolve_principles(refs)
        self.assertEqual(len(resolved), 1)
        self.assertEqual(resolved[0]["code"], "B1")

    def test_resolved_principle_has_title(self):
        refs = [("B1", "../principles/B1.md")]
        resolved = self.tracker.resolve_principles(refs)
        self.assertIn("title", resolved[0])
        self.assertTrue(len(resolved[0]["title"]) > 0)

    def test_resolved_principle_has_content(self):
        refs = [("B1", "../principles/B1.md")]
        resolved = self.tracker.resolve_principles(refs)
        self.assertIn("content", resolved[0])
        self.assertTrue(len(resolved[0]["content"]) > 0)


# -------------------------------------------------------------------
# Lifecycle: mark_done
# -------------------------------------------------------------------

class TestMarkDone(_TrackerTestCase):
    """Tests for mark_done (rename _todo_ → _done_)."""

    def test_rename_todo_to_done(self):
        path = _make_increment(self.req_dir, 1, status="todo")
        new_path = self.tracker.mark_done(path)
        self.assertIn("_done_", new_path.name)
        self.assertNotIn("_todo_", new_path.name)
        self.assertTrue(new_path.exists())
        self.assertFalse(path.exists())

    def test_mark_done_preserves_content(self):
        path = _make_increment(self.req_dir, 1, status="todo")
        original_content = path.read_text()
        new_path = self.tracker.mark_done(path)
        self.assertEqual(new_path.read_text(), original_content)

    def test_mark_done_updates_counts(self):
        path = _make_increment(self.req_dir, 1, status="todo")
        self.assertEqual(self.tracker.done_count(), 0)
        self.tracker.mark_done(path)
        self.assertEqual(self.tracker.done_count(), 1)


# -------------------------------------------------------------------
# Prompt generation: format_increment_prompt
# -------------------------------------------------------------------

class TestFormatIncrementPrompt(_TrackerTestCase):
    """Tests for format_increment_prompt."""

    def test_basic_prompt_structure(self):
        path = _make_increment(self.req_dir, 1)
        prompt = self.tracker.format_increment_prompt(path)
        self.assertIn("INCREMENT 0001", prompt)
        self.assertIn("SCOPE:", prompt)
        self.assertIn("REQUIREMENT:", prompt)
        self.assertIn("ACCEPTANCE CRITERIA:", prompt)
        self.assertIn("RULES:", prompt)
        self.assertIn("COMPLETION CRITERIA:", prompt)
        self.assertIn("TRACEABILITY:", prompt)
        self.assertIn("WORKFLOW:", prompt)

    def test_prompt_includes_description(self):
        path = _make_increment(self.req_dir, 1)
        prompt = self.tracker.format_increment_prompt(path)
        self.assertIn("Implement feature 1", prompt)

    def test_prompt_includes_principles(self):
        path = _make_increment(self.req_dir, 1)
        prompt = self.tracker.format_increment_prompt(path)
        self.assertIn("APPLICABLE PRINCIPLES:", prompt)
        self.assertIn("B1", prompt)

    def test_prompt_includes_commit_message(self):
        path = _make_increment(self.req_dir, 1, short_desc="cool_feature")
        prompt = self.tracker.format_increment_prompt(path)
        self.assertIn("INCREMENT 0001: Cool Feature", prompt)

    def test_prompt_shows_progress(self):
        _make_increment(self.req_dir, 1, status="done")
        path = _make_increment(self.req_dir, 2, status="todo")
        prompt = self.tracker.format_increment_prompt(path)
        self.assertIn("1/2", prompt)

    def test_prompt_forbidden_rules(self):
        path = _make_increment(self.req_dir, 1)
        prompt = self.tracker.format_increment_prompt(path)
        self.assertIn("FORBIDDEN", prompt)
        self.assertIn("Do NOT auto-advance", prompt)

    def test_prompt_falls_back_to_self_inspection(self):
        """Empty file triggers self-inspection prompt."""
        content = ""
        path = _make_increment(self.req_dir, 1, content=content)
        prompt = self.tracker.format_increment_prompt(path)
        self.assertIn("SELF-INSPECTION", prompt)


# -------------------------------------------------------------------
# Self-inspection prompt
# -------------------------------------------------------------------

class TestSelfInspectionPrompt(_TrackerTestCase):
    """Tests for format_self_inspection_prompt."""

    def test_empty_file_diagnosis(self):
        path = _make_increment(self.req_dir, 1, content="")
        data = IncrementTracker.parse_increment(path)
        prompt = self.tracker.format_self_inspection_prompt(path, data)
        self.assertIn("SELF-INSPECTION REQUIRED", prompt)
        self.assertIn("EMPTY", prompt)
        self.assertIn("ACTION REQUIRED", prompt)

    def test_non_standard_format_diagnosis(self):
        content = "Some random text that the parser can't handle well.\nNo headings."
        path = _make_increment(self.req_dir, 1, content=content)
        data = IncrementTracker.parse_increment(path)
        # Force description to be empty to trigger non-standard path
        data["description"] = ""
        prompt = self.tracker.format_self_inspection_prompt(path, data)
        self.assertIn("SELF-INSPECTION REQUIRED", prompt)
        self.assertIn("Non-standard format", prompt)
        self.assertIn("RAW FILE CONTENT", prompt)
        self.assertIn("PARSE RESULTS", prompt)

    def test_self_inspection_shows_progress(self):
        _make_increment(self.req_dir, 1, status="done")
        path = _make_increment(self.req_dir, 2, content="")
        data = IncrementTracker.parse_increment(path)
        prompt = self.tracker.format_self_inspection_prompt(path, data)
        self.assertIn("1/2", prompt)

    def test_self_inspection_has_workflow(self):
        path = _make_increment(self.req_dir, 1, content="")
        data = IncrementTracker.parse_increment(path)
        prompt = self.tracker.format_self_inspection_prompt(path, data)
        self.assertIn("WORKFLOW:", prompt)
        self.assertIn("git add", prompt)

    def test_self_inspection_commit_message(self):
        path = _make_increment(self.req_dir, 5, short_desc="my_thing",
                               content="")
        data = IncrementTracker.parse_increment(path)
        prompt = self.tracker.format_self_inspection_prompt(path, data)
        self.assertIn("INCREMENT 0005", prompt)


# -------------------------------------------------------------------
# Done summary
# -------------------------------------------------------------------

class TestFormatDoneSummary(_TrackerTestCase):
    """Tests for format_done_summary."""

    def test_done_summary_basic(self):
        done = _make_increment(self.req_dir, 1, status="done")
        summary = self.tracker.format_done_summary(done, None)
        self.assertIn("COMPLETED", summary)
        self.assertIn("INCREMENT 0001", summary)

    def test_done_summary_with_next(self):
        done = _make_increment(self.req_dir, 1, status="done")
        next_path = _make_increment(self.req_dir, 2, status="todo")
        summary = self.tracker.format_done_summary(done, next_path)
        self.assertIn("Next increment ready", summary)

    def test_done_summary_all_complete(self):
        done = _make_increment(self.req_dir, 1, status="done")
        summary = self.tracker.format_done_summary(done, None)
        self.assertIn("ALL INCREMENTS COMPLETED", summary)

    def test_done_summary_with_changed_files(self):
        done = _make_increment(self.req_dir, 1, status="done")
        summary = self.tracker.format_done_summary(
            done, None, changed_files=["foo.py", "bar.py"])
        self.assertIn("CHANGED FILES", summary)
        self.assertIn("foo.py", summary)
        self.assertIn("bar.py", summary)

    def test_done_summary_shows_acceptance_criteria(self):
        done = _make_increment(self.req_dir, 1, status="done")
        summary = self.tracker.format_done_summary(done, None)
        self.assertIn("ACCEPTANCE CRITERIA STATUS", summary)
        self.assertIn("[done]", summary)

    def test_done_summary_shows_progress(self):
        _make_increment(self.req_dir, 1, status="done")
        done = _make_increment(self.req_dir, 2, status="done")
        _make_increment(self.req_dir, 3, status="todo")
        summary = self.tracker.format_done_summary(done, None)
        self.assertIn("2/3", summary)


# -------------------------------------------------------------------
# _find_increment_file
# -------------------------------------------------------------------

class TestFindIncrementFile(_TrackerTestCase):
    """Tests for _find_increment_file."""

    def test_find_todo_file(self):
        _make_increment(self.req_dir, 3, status="todo")
        result = self.tracker._find_increment_file(3)
        self.assertIsNotNone(result)
        self.assertIn("0003", result.name)

    def test_find_done_file(self):
        _make_increment(self.req_dir, 3, status="done")
        result = self.tracker._find_increment_file(3)
        self.assertIsNotNone(result)
        self.assertIn("_done_", result.name)

    def test_find_nonexistent_file(self):
        result = self.tracker._find_increment_file(99)
        self.assertIsNone(result)

    def test_find_prefers_todo_over_done(self):
        """When both todo and done exist for the same number, todo is found first."""
        _make_increment(self.req_dir, 1, status="todo", short_desc="a")
        _make_increment(self.req_dir, 1, status="done", short_desc="b")
        result = self.tracker._find_increment_file(1)
        self.assertIsNotNone(result)
        self.assertIn("_todo_", result.name)


if __name__ == "__main__":
    unittest.main()
