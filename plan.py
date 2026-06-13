#!/usr/bin/env python3
"""
Planning System for Self-Development Organism.

Generates a structured planning prompt that walks an agent through:
  1. Project conventions (how/ principles)
  2. State-before snapshot (current codebase state)
  3. Increment planning with TDD approach
  4. State-after target (expected observable change)
  5. Two verification gates: automated tests + visual screenshot diff

Usage:
    python3 plan.py                    # Plan next TODO increment
    python3 plan.py --increment=0014   # Plan a specific increment
    python3 plan.py --all-principles   # Dump full convention guide
"""

from __future__ import annotations

import argparse
import glob
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
HOW_DIR = SCRIPT_DIR / "how"
TODO_DIR = SCRIPT_DIR / "todo"
STATE_FILE = SCRIPT_DIR / "organism_state.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _git(*args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(SCRIPT_DIR), *args],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except subprocess.CalledProcessError:
        return ""


def _load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def inc_token(inc: dict) -> str:
    """Per-increment string token used in screenshot/test paths.

    Numbered increments → zero-padded number (e.g. "0014").
    Ad-hoc increments   → slug derived from the title, truncated to 40 chars.
    """
    if inc.get("number") is not None:
        return f"{inc['number']:04d}"
    slug = re.sub(r"[^a-z0-9]+", "_", (inc.get("title") or "").lower()).strip("_")
    return (slug or "adhoc")[:40]


# ---------------------------------------------------------------------------
# Convention loader
# ---------------------------------------------------------------------------

def load_conventions() -> dict[str, str]:
    """Return {code: content} for every file in how/."""
    result: dict[str, str] = {}
    for f in sorted(HOW_DIR.glob("*.md")):
        result[f.stem] = _read(f)
    return result


def format_conventions(conventions: dict[str, str]) -> str:
    lines = ["## PROJECT CONVENTIONS (how/)\n"]
    for code, body in conventions.items():
        lines.append(f"### [{code}]")
        lines.append(body.strip())
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Increment loader
# ---------------------------------------------------------------------------

def _increment_files(status: str = "todo") -> list[Path]:
    pattern = str(TODO_DIR / f"increment_*_{status}_*.md")
    return sorted(Path(f) for f in glob.glob(pattern))


def current_todo() -> Path | None:
    todos = _increment_files("todo")
    return todos[0] if todos else None


def find_increment(number: int) -> Path | None:
    for status in ("todo", "done"):
        for f in _increment_files(status):
            m = re.search(r"increment_(\d+)", f.stem)
            if m and int(m.group(1)) == number:
                return f
    return None


def parse_increment(path: Path) -> dict:
    content = _read(path)
    name = path.stem

    num_m = re.search(r"increment_(\d+)", name)
    number = int(num_m.group(1)) if num_m else 0
    status = "todo" if "_todo_" in name else "done"

    title_m = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    title = title_m.group(1).strip() if title_m else name

    desc_m = re.search(r"## Description\s*\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    description = desc_m.group(1).strip() if desc_m else content.strip()

    principles: list[tuple[str, str]] = []
    princ_m = re.search(r"## Related Principles\s*\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    if princ_m:
        for m in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", princ_m.group(1)):
            code = m.group(1).split("—")[0].split("–")[0].strip()
            principles.append((code, m.group(2)))

    criteria: list[str] = []
    ac_m = re.search(r"## Acceptance Criteria\s*\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    if ac_m:
        for line in ac_m.group(1).strip().splitlines():
            cleaned = re.sub(r"^-\s*\[[ x]\]\s*", "", line.strip())
            cleaned = re.sub(r"^-\s*", "", cleaned).strip()
            if cleaned:
                criteria.append(cleaned)

    return {
        "number": number,
        "status": status,
        "title": title,
        "description": description,
        "principles": principles,
        "acceptance_criteria": criteria,
        "raw": content,
        "path": path,
    }


def adhoc_increment(text: str) -> dict:
    """Build a synthetic increment dict from free-form requirement text.

    Mirrors the shape of `parse_increment`'s return value so the rest of
    the prompt-assembly pipeline can stay mode-agnostic. No files are
    created or read.
    """
    text = text.strip()
    return {
        "number": None,
        "status": "adhoc",
        "title": text[:60].rstrip(),
        "description": text,
        "principles": [],
        "acceptance_criteria": [],
        "raw": text,
        "path": None,
    }


# ---------------------------------------------------------------------------
# State snapshot
# ---------------------------------------------------------------------------

def state_before(inc: dict) -> str:
    state = _load_state()
    generation = state.get("generation", 0)
    last_shown = state.get("last_increment_shown", None)
    done_count = len(_increment_files("done"))
    todo_count = len(_increment_files("todo"))

    git_branch = _git("rev-parse", "--abbrev-ref", "HEAD")
    git_sha = _git("rev-parse", "--short", "HEAD")
    git_msg = _git("log", "-1", "--pretty=%s")
    git_status = _git("status", "--short")

    lines = [
        "## STATE BEFORE\n",
        f"- Generation     : {generation}",
        f"- Done increments: {done_count}",
        f"- Todo increments: {todo_count}",
        f"- Last shown     : {last_shown}",
        f"- Branch         : {git_branch} @ {git_sha}",
        f"- Last commit    : {git_msg}",
    ]
    if git_status:
        lines.append(f"- Uncommitted    :\n```\n{git_status}\n```")
    else:
        lines.append("- Uncommitted    : (clean)")

    token = inc_token(inc)
    lines += [
        "",
        "### Screenshot gate BEFORE",
        "Run the following command to capture baseline state:",
        "```",
        f"# screencapture -x /tmp/plan_before_{token}.png",
        "# (or your project's own screenshot/test-report command)",
        "```",
        "Store the path; you will diff it against the AFTER screenshot.",
    ]
    return "\n".join(lines)


def state_after(inc: dict) -> str:
    criteria = inc["acceptance_criteria"]
    token = inc_token(inc)
    lines = [
        "## STATE AFTER (target)\n",
        "When this increment is correctly implemented, the following must be true:\n",
    ]
    for c in criteria:
        lines.append(f"- [ ] {c}")

    if not criteria:
        lines.append("- [ ] (no explicit acceptance criteria — derive from description)")

    lines += [
        "",
        "### Screenshot gate AFTER",
        "After implementation, capture the new state and diff:",
        "```",
        f"# screencapture -x /tmp/plan_after_{token}.png",
        f"# diff /tmp/plan_before_{token}.png /tmp/plan_after_{token}.png",
        "# (or open both images and verify the expected visual change)",
        "```",
        "If the screenshots are identical, the change may be invisible / no-op — investigate.",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# TDD plan
# ---------------------------------------------------------------------------

def tdd_plan(inc: dict) -> str:
    token = inc_token(inc)
    title_slug = re.sub(r"[^a-z0-9]+", "_", inc["title"].lower()).strip("_") or "adhoc"

    if inc.get("number") is not None:
        test_path = f"tests/test_increment_{token}_{title_slug}.py"
    else:
        test_path = f"tests/test_{token}.py"

    lines = [
        "## TDD IMPLEMENTATION PLAN\n",
        "Follow Red → Green → Refactor strictly. Do not write production code before a failing test.\n",
        "### Step 1 — RED: write a failing test",
        "```",
        f"# Create or extend: {test_path}",
        "# Assert the behaviour described in the acceptance criteria BEFORE implementing.",
        f"# Run: python -m pytest {test_path} -v",
        "# Expected result: FAILED (proves the test is real, not vacuous)",
        "```",
        "",
        "### Step 2 — GREEN: implement the minimum code to pass",
        "```",
        "# Implement only what is needed to make the failing test pass.",
        "# Run: python -m pytest tests/ -v",
        "# Expected result: PASSED",
        "```",
        "",
        "### Step 3 — REFACTOR: clean without breaking",
        "```",
        "# Remove duplication, rename for clarity, enforce conventions.",
        "# Run: python -m pytest tests/ -v   # must stay green",
        "# Run: python -m py_compile <changed files>",
        "```",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Verification gates
# ---------------------------------------------------------------------------

def verification_gates(inc: dict) -> str:
    token = inc_token(inc)
    lines = [
        "## VERIFICATION GATES\n",
        "Both gates must pass before committing.\n",
        "### Gate 1 — Automated (tests + lint)",
        "```",
        "python -m pytest tests/ -v                         # all tests green",
        "python -m py_compile <every changed .py file>      # no syntax errors",
        "```",
        "Expected: zero failures, zero syntax errors.\n",
        "### Gate 2 — Visual (screenshot diff)",
        "```",
        f"# 1. Open /tmp/plan_before_{token}.png",
        f"# 2. Open /tmp/plan_after_{token}.png",
        "# 3. Confirm the observable change matches the acceptance criteria.",
        "# 4. If UI is not applicable, replace with terminal output diff:",
        f"#    diff <(./todo.sh 2>&1) /tmp/plan_output_before_{token}.txt",
        "```",
        "Expected: a visible, intentional difference that proves the increment is done.\n",
        "If either gate fails: do NOT commit. Return to Step 1 (RED).",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Principle injection
# ---------------------------------------------------------------------------

def inject_principles(inc: dict) -> str:
    if not inc["principles"]:
        return ""
    lines = ["## APPLICABLE PRINCIPLES\n"]
    for code, rel_path in inc["principles"]:
        abs_path = (inc["path"].parent / rel_path).resolve()
        body = _read(abs_path).strip()
        lines.append(f"### {code}")
        lines.append(body)
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Full prompt assembly
# ---------------------------------------------------------------------------

def build_plan_prompt(inc: dict, conventions: dict[str, str]) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    short_title = re.sub(
        r"^increment\s+\d+[:\s]+", "", inc["title"], flags=re.IGNORECASE
    ).lower().strip()

    is_adhoc = inc.get("number") is None
    header = (
        "# PLANNING PROMPT — Ad-hoc requirement"
        if is_adhoc
        else f"# PLANNING PROMPT — Increment {inc['number']:04d}"
    )
    directive = (
        "_Read the conventions below once, then apply them. "
        "Do not restate them, do not narrate the steps — just follow them. "
        "The acceptance criteria below are the only success signal._"
    )

    requirement_block = f"## REQUIREMENT\n\n**{inc['title']}**\n\n{inc['description']}"
    if is_adhoc:
        requirement_block += (
            "\n\n_Ad-hoc requirement (not tied to a numbered increment). "
            "Derive acceptance criteria from the description and treat them "
            "as the contract._"
        )

    if is_adhoc:
        commit_block = "\n".join([
            "## COMMIT",
            "After both gates pass:",
            "```",
            "git add -A",
            'git commit -m "<type>(<scope>): <one-line summary>"',
            "git push",
            "```",
        ])
    else:
        commit_block = "\n".join([
            "## COMMIT",
            "After both gates pass:",
            "```",
            "git add -A",
            f'git commit -m "increment {inc["number"]:04d}: {short_title}"',
            "git push",
            "```",
            "Then run `./todo.sh` to verify and advance to the next increment.",
        ])

    sections = [
        header,
        f"_Generated: {now}_",
        directive,
        "---",
        format_conventions(conventions),
        "---",
        state_before(inc),
        "---",
        requirement_block,
        "---",
        inject_principles(inc),
        "---",
        tdd_plan(inc),
        "---",
        state_after(inc),
        "---",
        verification_gates(inc),
        "---",
        commit_block,
    ]
    return "\n\n".join(s for s in sections if s)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a structured planning prompt for a selfdev increment."
    )
    parser.add_argument(
        "--increment", type=int, default=None,
        help="Increment number to plan (default: current TODO)"
    )
    parser.add_argument(
        "--all-principles", action="store_true",
        help="Print the full convention guide and exit"
    )
    parser.add_argument(
        "requirement", nargs="*",
        help="Free-form requirement text (ad-hoc mode, no file created)"
    )
    args = parser.parse_args()

    conventions = load_conventions()

    if args.all_principles:
        print(format_conventions(conventions))
        return

    freeform = " ".join(args.requirement).strip()
    if freeform:
        if args.increment is not None:
            print(
                f"warning: ignoring --increment={args.increment}; "
                f"free-form requirement supplied",
                file=sys.stderr,
            )
        inc = adhoc_increment(freeform)
        print(build_plan_prompt(inc, conventions))
        return

    if args.increment is not None:
        path = find_increment(args.increment)
        if path is None:
            print(f"Error: increment {args.increment:04d} not found in {TODO_DIR}")
            raise SystemExit(1)
    else:
        path = current_todo()
        if path is None:
            print("No TODO increments remaining. All done!")
            raise SystemExit(0)

    inc = parse_increment(path)
    print(build_plan_prompt(inc, conventions))


if __name__ == "__main__":
    main()
