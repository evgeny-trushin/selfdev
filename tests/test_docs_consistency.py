"""Documentation and agent files must reference current folder names."""
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Allow-list: design history that legitimately records the old names.
ALLOWED_PATHS = {
    PROJECT_ROOT / "docs" / "superpowers" / "specs"
        / "2026-05-19-rename-requirements-principles-design.md",
    PROJECT_ROOT / "docs" / "superpowers" / "plans"
        / "2026-05-19-rename-folders.md",
}

DOC_FILES = [
    PROJECT_ROOT / "README.md",
    *((PROJECT_ROOT / ".claude" / "agents").glob("*.md")),
    *((PROJECT_ROOT / ".github" / "agents").glob("*.md")),
]


class TestDocsConsistency(unittest.TestCase):

    def test_no_stale_requirements_folder_reference(self):
        offenders = []
        for path in DOC_FILES:
            if path in ALLOWED_PATHS or not path.exists():
                continue
            text = path.read_text()
            if "requirements/" in text:
                offenders.append(str(path.relative_to(PROJECT_ROOT)))
        self.assertEqual(offenders, [], f"Stale 'requirements/' references in: {offenders}")

    def test_no_stale_principles_folder_reference(self):
        offenders = []
        for path in DOC_FILES:
            if path in ALLOWED_PATHS or not path.exists():
                continue
            text = path.read_text()
            if "principles/" in text:
                offenders.append(str(path.relative_to(PROJECT_ROOT)))
        self.assertEqual(offenders, [], f"Stale 'principles/' references in: {offenders}")


if __name__ == "__main__":
    unittest.main()
