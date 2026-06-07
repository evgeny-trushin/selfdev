"""Every increment file must use ../how/ for principle links."""
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TODO_DIR = PROJECT_ROOT / "todo"


class TestIncrementLinkPaths(unittest.TestCase):

    def test_no_increment_references_old_principles_path(self):
        offenders = []
        for path in sorted(TODO_DIR.glob("increment_*.md")):
            text = path.read_text()
            if "../principles/" in text:
                offenders.append(path.name)
        self.assertEqual(
            offenders, [],
            f"Old '../principles/' link path found in: {offenders}"
        )

    def test_every_resolved_principle_code_has_a_file_in_how(self):
        import re
        how_dir = PROJECT_ROOT / "how"
        pattern = re.compile(r"\(\.\./how/([A-Z][A-Z0-9]*)\.md\)")
        missing = []
        for path in sorted(TODO_DIR.glob("increment_*.md")):
            for code in pattern.findall(path.read_text()):
                if not (how_dir / f"{code}.md").exists():
                    missing.append(f"{path.name}:{code}")
        self.assertEqual(missing, [], f"Missing principle files: {missing}")


if __name__ == "__main__":
    unittest.main()
