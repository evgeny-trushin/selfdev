# Increment 0020: Rename `requirements/` Folder to `todo/`

**Requirement ID:** R20
**Status:** TODO

## Description

Rename the top-level `requirements/` folder to `todo/` and flip the `REQUIREMENTS_DIRNAME` constant. Update all source, test, and user-facing string references. After this increment, the selfdev increment-driven loop reads from `todo/` and `how/` (renamed in 0019); the old names are gone.

Depends on: increment 0019 (so only one folder is being renamed at a time).

## Related Principles

- [E1 — Small Mutations](../how/E1.md): one folder rename per increment
- [E2 — Selection Pressure](../how/E2.md): all tests green at each boundary
- [B3 — Apoptosis](../how/B3.md): remove the obsolete name
- [M3 — Transparency](../how/M3.md): user-visible hints match the new name

## TDD Steps

### Step 1: Update fixture-building tests to expect `todo/`

In `tests/test_increment_tracker.py:66`, change:

```python
        self.req_dir = self.tmp_dir / "requirements"
```

to:

```python
        self.req_dir = self.tmp_dir / "todo"
```

In `tests/test_revert_redo.py`, change every occurrence (lines 47, 132, 202, 348):

```python
        self.req_dir = self.tmp_dir / "requirements"
```

to:

```python
        self.req_dir = self.tmp_dir / "todo"
```

### Step 2: Add a hint-message assertion test

Add to `tests/test_increment_tracker.py` (inside an existing test class with a tracker fixture):

```python
    def test_advance_hint_mentions_todo_folder(self):
        """User-facing rename hint references the new folder name."""
        # Build any TODO increment so we have something to prompt on.
        (self.req_dir / "increment_0099_todo_dummy.md").write_text(
            "# Increment 0099: Dummy\n"
            "**Requirement ID:** R99\n**Status:** TODO\n\n"
            "## Description\nx\n\n## Acceptance Criteria\n- [ ] x\n"
        )
        prompt = self.tracker.advance_prompt() if hasattr(self.tracker, "advance_prompt") \
            else self.tracker.format_prompt(self.tracker.current_todo())
        self.assertIn("todo/", prompt)
        self.assertNotIn("requirements/", prompt)
```

(If neither helper method name exists, locate the function that emits the `mv requirements/...` hint at `increment_tracker.py:837` and call it directly.)

### Step 3: Run tests and verify they fail

```
python -m pytest tests/ -v
```

Expected: fixture-setup tests fail because `IncrementTracker` still looks in `root_dir / "requirements"`; the hint-text test fails because the literal at `increment_tracker.py:837` still says `requirements/`.

### Step 4: Flip the constant

Edit `models.py`:

```python
REQUIREMENTS_DIRNAME = "requirements"
```

becomes:

```python
REQUIREMENTS_DIRNAME = "todo"
```

### Step 5: Move the folder on disk

```
git mv requirements todo
```

### Step 6: Update user-facing literals

Edit `develop.sh:88`:

```bash
    echo "  - Sequential increments from requirements/"
```

becomes:

```bash
    echo "  - Sequential increments from todo/"
```

Edit `increment_tracker.py:837`:

```python
            lines.append(f"    mv requirements/{old_name} requirements/{new_name}")
```

becomes:

```python
            lines.append(f"    mv {REQUIREMENTS_DIRNAME}/{old_name} {REQUIREMENTS_DIRNAME}/{new_name}")
```

(The constant is already imported from 0018.)

### Step 7: Run all tests

```
python -m pytest tests/ -v
```

Expected: green.

### Step 8: Verify the live workflow

```
./selfdev/develop.sh
```

Expected: prints the next TODO increment from `todo/`. Confirm the printed `mv ...` hint reads `mv todo/... todo/...`.

### Step 9: Refactor — rename the constant to `TODO_DIRNAME`

Find/replace `REQUIREMENTS_DIRNAME` → `TODO_DIRNAME` across `models.py`, `increment_tracker.py`, and `tests/test_path_constants.py`. Also rename `REQUIREMENTS_DIR` → `TODO_DIR` in `models.py` for consistency. Update `tests/test_path_constants.py`:

```python
    def test_todo_dirname_constant_exists(self):
        self.assertEqual(models.TODO_DIRNAME, "todo")

    def test_todo_dir_uses_dirname_constant(self):
        self.assertTrue(str(models.TODO_DIR).endswith(models.TODO_DIRNAME))
```

Search the project for any remaining references to `REQUIREMENTS_DIR` (e.g., in `organism.py`):

```
grep -rn "REQUIREMENTS_DIR\|PRINCIPLES_DIR" --include="*.py"
```

Replace each with `TODO_DIR` / `HOW_DIR` respectively. Re-run tests.

## Acceptance Criteria

- [ ] `todo/` directory exists at project root with all the files previously under `requirements/`
- [ ] `requirements/` directory does not exist
- [ ] `models.TODO_DIRNAME == "todo"`; `REQUIREMENTS_DIRNAME` no longer exists
- [ ] `develop.sh` help text references `todo/`
- [ ] `./selfdev/develop.sh` emits a rename hint of the form `mv todo/... todo/...`
- [ ] No source or test file contains the literal `"requirements"` used as a path component for runtime resolution
- [ ] `python -m pytest tests/` is green
