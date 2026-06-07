"""Migration from requirements/principles to todo/how."""
import subprocess
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = PROJECT_ROOT / "migrate_to_todo_how.sh"


class TestMigrateToTodoHow(unittest.TestCase):

    def run_migration(self, root: Path) -> subprocess.CompletedProcess[str]:
        self.assertTrue(SCRIPT.exists(), f"Migration script missing: {SCRIPT}")
        self.assertTrue(SCRIPT.stat().st_mode & 0o111, f"Migration script is not executable: {SCRIPT}")
        return subprocess.run(
            [str(SCRIPT), str(root)],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_renames_requirements_and_principles_and_rewrites_path_refs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            requirements = root / "requirements"
            principles = root / "principles"
            requirements.mkdir()
            principles.mkdir()
            (requirements / "increment_0001_todo_demo.md").write_text(
                "\n".join([
                    "# Increment",
                    "See [P1](../principles/P1.md).",
                    "Folders: `requirements/`, `principles/`, `requirements`, `principles`.",
                    "Typo folder mention: `requirments/`.",
                ]),
                encoding="utf-8",
            )
            (principles / "P1.md").write_text(
                "Principle file links back to ../requirements/ and `principles`.",
                encoding="utf-8",
            )

            result = self.run_migration(root)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((root / "requirements").exists())
            self.assertFalse((root / "principles").exists())
            todo_text = (root / "todo" / "increment_0001_todo_demo.md").read_text(
                encoding="utf-8"
            )
            how_text = (root / "how" / "P1.md").read_text(encoding="utf-8")
            self.assertIn("../how/P1.md", todo_text)
            self.assertIn("`todo/`", todo_text)
            self.assertIn("`how/`", todo_text)
            self.assertIn("`todo`", todo_text)
            self.assertIn("`how`", todo_text)
            self.assertIn("../todo/", how_text)
            self.assertIn("`how`", how_text)
            self.assertNotIn("../principles/", todo_text)
            self.assertNotIn("requirements/", todo_text)
            self.assertNotIn("requirments/", todo_text)

    def test_renames_misspelled_requirments_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "requirments").mkdir()
            (root / "principles").mkdir()
            (root / "requirments" / "increment_0001_todo_demo.md").write_text(
                "See ../principles/P1.md and `requirments/`.",
                encoding="utf-8",
            )
            (root / "principles" / "P1.md").write_text("Content", encoding="utf-8")

            result = self.run_migration(root)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((root / "requirments").exists())
            self.assertTrue((root / "todo").is_dir())
            migrated = (root / "todo" / "increment_0001_todo_demo.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("../how/P1.md", migrated)
            self.assertIn("`todo/`", migrated)

    def test_refuses_to_overwrite_existing_target_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "requirements").mkdir()
            (root / "todo").mkdir()
            (root / "principles").mkdir()

            result = self.run_migration(root)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Refusing to overwrite", result.stderr)
            self.assertTrue((root / "requirements").is_dir())
            self.assertTrue((root / "todo").is_dir())

    def test_is_idempotent_after_migration(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "todo").mkdir()
            (root / "how").mkdir()
            (root / "todo" / "increment_0001_todo_demo.md").write_text(
                "See [P1](../how/P1.md) and `todo/`.",
                encoding="utf-8",
            )
            (root / "how" / "P1.md").write_text("Content", encoding="utf-8")

            result = self.run_migration(root)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("No legacy folders found", result.stdout)
            self.assertIn("No stale path references found", result.stdout)


if __name__ == "__main__":
    unittest.main()
