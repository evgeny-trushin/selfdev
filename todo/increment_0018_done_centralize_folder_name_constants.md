# Increment 0018: Centralize Folder Name Constants

**Requirement ID:** R18
**Status:** TODO

## Description

Replace hardcoded `"requirements"` and `"principles"` string literals used for path construction with named constants in `models.py`. This is a behaviour-preserving refactor that creates a single flip-point for the subsequent renames in increments 0019 and 0020.

`models.py` already exposes resolved `Path` constants `REQUIREMENTS_DIR` and `PRINCIPLES_DIR`, but `increment_tracker.py` rebuilds its own paths from a `root_dir` parameter and so does not benefit. The fix is to add **dirname string** constants and use them in both places.

## Related Principles

- [E1 — Small Mutations](../how/E1.md): smallest possible step before the rename
- [E2 — Selection Pressure](../how/E2.md): all tests must remain green
- [CLN — Cleanliness](../how/CLN.md): remove magic-string duplication
- [M3 — Transparency](../how/M3.md): one obvious place to change folder names

Note: link paths use `../how/` (the final folder name). Until increment 0019 runs, the runtime still resolves these via the `principles/` directory because it extracts only the principle code (e.g. `E1`) and ignores the link path.

## TDD Steps

### Step 1: Write the failing test

Create `tests/test_path_constants.py`:

```python
"""Path-name constants live in one place."""
import unittest
import models


class TestPathConstants(unittest.TestCase):

    def test_requirements_dirname_constant_exists(self):
        self.assertEqual(models.REQUIREMENTS_DIRNAME, "requirements")

    def test_principles_dirname_constant_exists(self):
        self.assertEqual(models.PRINCIPLES_DIRNAME, "principles")

    def test_requirements_dir_uses_dirname_constant(self):
        self.assertTrue(str(models.REQUIREMENTS_DIR).endswith(models.REQUIREMENTS_DIRNAME))

    def test_principles_dir_uses_dirname_constant(self):
        self.assertTrue(str(models.PRINCIPLES_DIR).endswith(models.PRINCIPLES_DIRNAME))


if __name__ == "__main__":
    unittest.main()
```

### Step 2: Run the test and verify it fails

```
python -m pytest tests/test_path_constants.py -v
```

Expected: FAIL — `AttributeError: module 'models' has no attribute 'REQUIREMENTS_DIRNAME'`.

### Step 3: Add the constants in `models.py`

Edit `models.py` lines 17-19 from:

```python
STATE_FILE = ROOT_DIR / "organism_state.json"
REQUIREMENTS_DIR = ROOT_DIR / "requirements"
PRINCIPLES_DIR = ROOT_DIR / "principles"
```

to:

```python
STATE_FILE = ROOT_DIR / "organism_state.json"
REQUIREMENTS_DIRNAME = "requirements"
PRINCIPLES_DIRNAME = "principles"
REQUIREMENTS_DIR = ROOT_DIR / REQUIREMENTS_DIRNAME
PRINCIPLES_DIR = ROOT_DIR / PRINCIPLES_DIRNAME
```

### Step 4: Refactor `increment_tracker.py` to use the new constants

In `increment_tracker.py`, add to the imports block near the top:

```python
from models import REQUIREMENTS_DIRNAME, PRINCIPLES_DIRNAME
```

Then edit lines 25-26 from:

```python
        self.requirements_dir = root_dir / "requirements"
        self.principles_dir = root_dir / "principles"
```

to:

```python
        self.requirements_dir = root_dir / REQUIREMENTS_DIRNAME
        self.principles_dir = root_dir / PRINCIPLES_DIRNAME
```

### Step 5: Verify all tests pass

```
python -m pytest tests/ -v
```

Expected: every test passes, including the new `test_path_constants.py`.

### Step 6: Verify no behaviour change end-to-end

```
./selfdev/develop.sh
```

Expected: same output as before this increment (still finds the next `_todo_` increment in `requirements/`).

## Acceptance Criteria

- [ ] `models.REQUIREMENTS_DIRNAME == "requirements"` and `models.PRINCIPLES_DIRNAME == "principles"`
- [ ] `models.REQUIREMENTS_DIR` and `models.PRINCIPLES_DIR` are derived from the new dirname constants
- [ ] `increment_tracker.py:25-26` use `REQUIREMENTS_DIRNAME` / `PRINCIPLES_DIRNAME` instead of hardcoded strings
- [ ] `tests/test_path_constants.py` exists and passes
- [ ] `python -m pytest tests/` is green
- [ ] `./selfdev/develop.sh` runs successfully with no output change
