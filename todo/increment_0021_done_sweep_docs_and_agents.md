# Increment 0021: Sweep Documentation and Agent Definitions

**Requirement ID:** R21
**Status:** TODO

## Description

Update every documentation and agent-definition file so it references the new folder names `todo/` and `how/` instead of `requirements/` and `principles/`. This increment touches no code paths — purely textual sweeps — and adds a consistency test that prevents regressions.

Depends on: increments 0019 and 0020.

## Related Principles

- [CLN — Cleanliness](../how/CLN.md): no stale references in user-facing copy
- [USR — User Empathy](../how/USR.md): bootstrap prompts must mention the real folder names
- [M3 — Transparency](../how/M3.md): docs match the code
- [TST — Testing](../how/TST.md): consistency is enforced by a test

## TDD Steps

### Step 1: Write the failing consistency test

Create `tests/test_docs_consistency.py`:

```python
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
```

### Step 2: Run the test and verify it fails

```
python -m pytest tests/test_docs_consistency.py -v
```

Expected: both tests fail, listing `README.md` and the six agent files as offenders.

### Step 3: Sweep `README.md`

Replace every occurrence of `requirements/` with `todo/` and every occurrence of `principles/` with `how/`. Key locations include (verify with `grep -n` first):

- The one-liner bootstrap prompt that says `copy its 'selfdev/', 'requirements/', and 'principles/' folders`
- The "Project structure" ASCII tree
- The "Increment-driven loop" section that shows `requirements/` example listing

Also update prose that says "principles injected from `principles/`" → "principles injected from `how/`".

### Step 4: Sweep agent definitions

For each of these six files, replace `requirements/` → `todo/` and `principles/` → `how/`:

- `.claude/agents/know-agent.md`
- `.claude/agents/selfdev-do-agent.md`
- `.claude/agents/selfdev-plan-agent.md`
- `.github/agents/know-agent.md`
- `.github/agents/selfdev-do-agent.md`
- `.github/agents/selfdev-plan-agent.md`

### Step 5: Re-run the consistency test

```
python -m pytest tests/test_docs_consistency.py -v
```

Expected: both tests pass.

### Step 6: Run the full suite

```
python -m pytest tests/ -v
```

Expected: green.

### Step 7: Manual smoke test — bootstrap prompt

Open `README.md` and read the one-liner bootstrap prompt under "How to Use". Confirm it now reads:

> "Clone https://github.com/evgeny-trushin/selfdev to a temp dir, copy its `selfdev/`, `todo/`, and `how/` folders into my project root, then run `./selfdev/develop.sh`. ..."

## Acceptance Criteria

- [ ] `README.md` contains no `requirements/` or `principles/` references
- [ ] All six agent definition files (`.claude/agents/*.md` and `.github/agents/*.md`) contain no `requirements/` or `principles/` references
- [ ] `tests/test_docs_consistency.py` exists, runs, and passes
- [ ] The README bootstrap one-liner names `todo/` and `how/`
- [ ] `python -m pytest tests/` is green
