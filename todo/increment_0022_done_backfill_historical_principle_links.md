# Increment 0022: Backfill Historical Principle Links

**Requirement ID:** R22
**Status:** TODO

## Description

Every increment file in `todo/` (formerly `requirements/`) has a `Related Principles` section whose link paths read `../how/CODE.md`. After increment 0019, those links resolve to a folder that no longer exists. This increment sweeps every `todo/*.md` body and replaces `../how/` with `../how/`. A test enforces the absence of any surviving old link.

Note: the runtime in `increment_tracker.py` extracts the principle **code** (e.g. `B1`) and ignores the path component, so the broken links did not break execution after 0019 — but they break for any human or agent that clicks them. This increment closes that gap.

Depends on: increments 0019 and 0020.

## Related Principles

- [B3 — Apoptosis](../how/B3.md): remove every trace of the obsolete name
- [CLN — Cleanliness](../how/CLN.md): consistent links across all increment files
- [TST — Testing](../how/TST.md): a grep-style assertion guards the new state
- [E2 — Selection Pressure](../how/E2.md): full suite must remain green

## TDD Steps

### Step 1: Write the failing test

Create `tests/test_increment_link_paths.py`:

```python
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
            if "../how/" in text:
                offenders.append(path.name)
        self.assertEqual(
            offenders, [],
            f"Old '../how/' link path found in: {offenders}"
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
```

### Step 2: Run the test and verify it fails

```
python -m pytest tests/test_increment_link_paths.py -v
```

Expected: `test_no_increment_references_old_principles_path` fails, listing every historical `_done_` increment (≈13 files) plus the 4 in-flight TODOs that haven't been touched yet.

### Step 3: Sweep `todo/*.md`

Run from the project root:

```bash
find todo -name 'increment_*.md' -type f -print0 \
  | xargs -0 sed -i '' 's|\.\./principles/|\.\./how/|g'
```

(macOS BSD `sed` — `-i ''` is the empty-extension form. On Linux drop the empty `''`.)

### Step 4: Re-run the link-path test

```
python -m pytest tests/test_increment_link_paths.py -v
```

Expected: both tests pass.

### Step 5: Run the full suite

```
python -m pytest tests/ -v
```

Expected: green.

### Step 6: Spot-check three files

Open by hand and verify links read `../how/CODE.md`:

- `todo/increment_0011_done_reliability.md`
- `todo/increment_0014_done_feedback_driven_prompt_logic.md` (will already be `_done_` after working through the queue, but if it is still `_todo_` at this point, that's also fine — the sweep is content-only)
- One of the new 0018-0021 increment files (their bodies already used `../how/` if you authored them after 0019, but the sweep is idempotent)

### Step 7: Final cross-check

```
grep -rn "principles/" todo/ || echo "clean"
```

Expected: prints `clean`.

```
grep -rn "principles" --include="*.py" --include="*.sh" || echo "clean"
```

Expected: prints `clean` (concept-level mentions in docstrings are fine if any remain — verify each match is conceptual, not a path).

## Acceptance Criteria

- [ ] No file under `todo/` contains the substring `../how/`
- [ ] Every `../how/CODE.md` link in `todo/*.md` resolves to an existing file in `how/`
- [ ] `tests/test_increment_link_paths.py` exists and passes
- [ ] `python -m pytest tests/` is green
- [ ] `./selfdev/develop.sh` continues to resolve and inject principle content correctly
