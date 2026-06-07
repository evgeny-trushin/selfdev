# Increment 0019: Rename `principles/` Folder to `how/`

**Requirement ID:** R19
**Status:** TODO

## Description

Rename the top-level `principles/` folder to `how/` and flip the `PRINCIPLES_DIRNAME` constant introduced in increment 0018. Update all source and test references that point at the literal `"principles"` directory name. `requirements/` is untouched in this increment; that rename is increment 0020.

Depends on: increment 0018 (constant must exist before it can be flipped).

## Related Principles

- [E1 — Small Mutations](../how/E1.md): rename one folder at a time
- [E2 — Selection Pressure](../how/E2.md): all tests must remain green
- [B3 — Apoptosis](../how/B3.md): remove the obsolete name entirely
- [CLN — Cleanliness](../how/CLN.md): no stale `"principles"` literals survive

## TDD Steps

### Step 1: Update fixture-building tests to expect `how/`

Modify `tests/test_increment_tracker.py:62-68` from:

```python
    """Base class that sets up a temp dir with requirements/ and principles/."""
    ...
        self.req_dir = self.tmp_dir / "requirements"
        ...
        self.prin_dir = self.tmp_dir / "principles"
```

to:

```python
    """Base class that sets up a temp dir with requirements/ and how/."""
    ...
        self.req_dir = self.tmp_dir / "requirements"
        ...
        self.prin_dir = self.tmp_dir / "how"
```

Modify `tests/test_revert_redo.py` lines 49, 134, 204, 350 — every `self.prin_dir = self.tmp_dir / "principles"` becomes `self.prin_dir = self.tmp_dir / "how"`.

Update inline markdown fixtures (test files contain literals like `[B1](../how/B1.md)` at:
- `tests/test_increment_tracker.py:45, 209, 210, 280, 354, 355, 362, 363, 367, 373, 379` (and any others)
- `tests/test_revert_redo.py:36` (and any others)

Replace `../how/` → `../how/` everywhere inside these test files.

### Step 2: Run tests and verify they fail

```
python -m pytest tests/ -v
```

Expected: failures pointing at the constant mismatch — `IncrementTracker` still constructs `root_dir / "principles"` but fixtures now build `how/`.

### Step 3: Flip the constant in `models.py`

Edit `models.py` from:

```python
PRINCIPLES_DIRNAME = "principles"
```

to:

```python
PRINCIPLES_DIRNAME = "how"
```

### Step 4: Move the folder on disk

```
git mv principles how
```

### Step 5: Update the `develop.sh` help text

Edit `develop.sh:89` from:

```bash
    echo "  - Principles injected from principles/"
```

to:

```bash
    echo "  - Principles injected from how/"
```

### Step 6: Run all tests

```
python -m pytest tests/ -v
```

Expected: green.

### Step 7: Verify the live workflow still resolves principle links

```
./selfdev/develop.sh
```

Expected: the current TODO increment prints with injected principle content. (Note: link paths inside the existing increment files still read `../how/...` — this is increment 0022's job. For the runtime, only `PRINCIPLES_DIRNAME` matters because the code now strips paths and looks up `how/CODE.md`. Verify by reading the printed prompt and confirming no "principle not found" warning appears for any code.)

If "principle not found" warnings appear, do **not** modify the link resolution logic here — that's a sign increment 0022 needs to run before this can ship cleanly. In that case, halt and re-order.

### Step 8: Refactor — rename the constant to `HOW_DIRNAME`

Find/replace `PRINCIPLES_DIRNAME` → `HOW_DIRNAME` across `models.py` and `increment_tracker.py` and tests. Adjust `tests/test_path_constants.py`:

```python
    def test_how_dirname_constant_exists(self):
        self.assertEqual(models.HOW_DIRNAME, "how")
```

(Remove the now-stale `test_principles_dirname_constant_exists` test.)

Run `python -m pytest tests/` — must still be green.

## Acceptance Criteria

- [ ] `how/` directory exists at project root with all the files previously under `principles/`
- [ ] `principles/` directory does not exist
- [ ] `models.HOW_DIRNAME == "how"`; `models.PRINCIPLES_DIRNAME` no longer exists
- [ ] `develop.sh` help text references `how/`
- [ ] No source or test file (under `*.py` or `*.sh`) contains the literal string `"principles"` used as a path component for runtime resolution (concept-level references are fine)
- [ ] `python -m pytest tests/` is green
- [ ] `./selfdev/develop.sh` prints a prompt with all referenced principles resolved
