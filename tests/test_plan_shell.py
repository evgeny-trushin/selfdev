"""Tests for shell launchers."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PLAN_SH = PROJECT_ROOT / "plan.sh"
PLAN_PY = PROJECT_ROOT / "plan.py"
TODO_SH = PROJECT_ROOT / "todo.sh"
RUNTIME_PY_FILES = [
    "analyzers.py",
    "diagnostics.py",
    "formatters.py",
    "increment_tracker.py",
    "models.py",
    "organism.py",
    "performance.py",
    "perspectives.py",
    "user_perspective.py",
]


class PlanShellTests(unittest.TestCase):
    def _make_installed_layout(self, root: Path) -> Path:
        script_dir = root / "selfdev"
        script_dir.mkdir()
        shutil.copy2(PLAN_SH, script_dir / "plan.sh")
        shutil.copy2(PLAN_PY, script_dir / "plan.py")
        (script_dir / "plan.sh").chmod(0o755)
        return script_dir

    def test_help_is_delegated_to_plan_py(self):
        shell_help = subprocess.run(
            [str(PLAN_SH), "--help"],
            cwd="/tmp",
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        python_help = subprocess.run(
            [sys.executable, str(PLAN_PY), "--help"],
            cwd="/tmp",
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(python_help.returncode, 0, python_help.stderr)
        self.assertEqual(shell_help.returncode, 0, shell_help.stderr)
        self.assertEqual(shell_help.stdout, python_help.stdout)
        self.assertEqual(shell_help.stderr, python_help.stderr)

    def test_default_goal_uses_exact_next_todo_filepath_in_installed_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script_dir = self._make_installed_layout(root)
            todo_dir = root / "todo"
            todo_dir.mkdir()
            (root / "how").mkdir()
            (root / "organism_state.json").write_text(
                json.dumps({"generation": 44, "last_increment_shown": 1}),
                encoding="utf-8",
            )
            (todo_dir / "increment_0002_todo_parent_feature.md").write_text(
                "# Parent Feature\n\n"
                "## Description\n"
                "Generate the parent project increment prompt.\n\n"
                "## Acceptance Criteria\n"
                "- [ ] Parent prompt is generated\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [str(script_dir / "plan.sh")],
                cwd="/tmp",
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        lines = [line for line in result.stdout.splitlines() if line.strip()]
        self.assertIn("# PLANNING PROMPT", result.stdout)
        self.assertEqual(lines[0], "# PLANNING PROMPT")
        self.assertEqual(lines[1], "## GOAL")
        self.assertEqual(
            lines[2],
            "As a result of execution, create the next todo increment file at "
            f"`{root.resolve() / 'todo' / 'increment_0003_todo_#OUTPUT_THE_MODEL#_#OUTPUT_THE_SHORT_SUMMARY#.md'}`.",
        )
        self.assertNotIn("# PLANNING PROMPT — Increment 0002", result.stdout)
        self.assertNotIn("Parent Feature", result.stdout)
        self.assertNotIn("Generate the parent project increment prompt.", result.stdout)
        self.assertNotIn("Todo increments", result.stdout)
        self.assertNotIn("Uncommitted", result.stdout)
        self.assertNotIn("tests/test_", result.stdout)
        self.assertNotIn("increment_0002_todo_parent_feature.md", result.stdout)
        self.assertNotIn("No TODO increments remaining", result.stdout)


class TodoShellTests(unittest.TestCase):
    def _make_installed_layout(self, root: Path) -> Path:
        script_dir = root / "selfdev"
        script_dir.mkdir()
        (root / "todo").mkdir()
        (script_dir / "todo").mkdir()
        for filename in RUNTIME_PY_FILES:
            (script_dir / filename).symlink_to(PROJECT_ROOT / filename)
        (script_dir / "todo.sh").symlink_to(TODO_SH)
        return script_dir

    def test_state_uses_repo_root_by_default(self):
        expected_state = json.loads(
            (PROJECT_ROOT / "organism_state.json").read_text(encoding="utf-8")
        )

        result = subprocess.run(
            [str(TODO_SH), "--state"],
            cwd="/tmp",
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"Generation: {expected_state['generation']}", result.stdout)

    def test_default_prefers_parent_todo_before_local_todo(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script_dir = self._make_installed_layout(root)
            (root / "organism_state.json").write_text(
                json.dumps({"generation": 77, "development_stage": "maturation"}),
                encoding="utf-8",
            )
            (script_dir / "organism_state.json").write_text(
                json.dumps({"generation": 12, "development_stage": "maturation"}),
                encoding="utf-8",
            )

            result = subprocess.run(
                [str(script_dir / "todo.sh"), "--state"],
                cwd="/tmp",
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Generation: 77", result.stdout)
        self.assertNotIn("Generation: 12", result.stdout)

    def test_help_uses_current_entrypoint_names(self):
        result = subprocess.run(
            [str(TODO_SH), "--help"],
            cwd="/tmp",
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Run ./todo.sh", result.stdout)
        self.assertIn("Sequential increments from todo/", result.stdout)
        self.assertIn("Principles injected from how/", result.stdout)
        self.assertNotIn("develop.sh", result.stdout)
        self.assertNotIn("selfdev/tests", result.stdout)

    def test_success_footer_uses_current_entrypoint_names(self):
        result = subprocess.run(
            [str(TODO_SH), "--state"],
            cwd="/tmp",
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Run tests:  python -m pytest tests/", result.stdout)
        self.assertIn("Run ./todo.sh", result.stdout)
        self.assertNotIn("develop.sh", result.stdout)
        self.assertNotIn("selfdev/tests", result.stdout)


if __name__ == "__main__":
    unittest.main()
