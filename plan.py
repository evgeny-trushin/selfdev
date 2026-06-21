#!/usr/bin/env python3
"""
Planning System for Self-Development Organism.

Generates a structured planning prompt that walks an agent through:
  1. Behavioral guardrails
  2. Requirement framing
  3. TDD planning
  4. Verification gates
  5. Completion reporting

Usage:
    python3 plan.py                    # Print a generic planning prompt
    python3 plan.py "Fix upload retry" # Plan a free-form requirement
    python3 plan.py --all-principles   # Dump full convention guide
"""

from __future__ import annotations

import argparse
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


def _default_project_root(script_dir: Path) -> Path:
    parent_root = script_dir.parent
    if (parent_root / "todo").is_dir():
        return parent_root
    return script_dir


ROOT_DIR = _default_project_root(SCRIPT_DIR)
HOW_DIR = ROOT_DIR / "how"
TODO_DIR = ROOT_DIR / "todo"
STATE_FILE = ROOT_DIR / "organism_state.json"


# ---------------------------------------------------------------------------
# Increment filename helpers
# ---------------------------------------------------------------------------
_INCREMENT_NUMBER_RE = re.compile(r"(?<!\d)(\d{1,4})(?!\d)")
_INCREMENT_STATUS_RE = re.compile(
    r"(?i)(^|[_-])(?P<status>todo|done)(?=$|[_-])"
)


def _increment_number_from_name(filename: str) -> int | None:
    match = _INCREMENT_NUMBER_RE.search(Path(filename).stem)
    return int(match.group(1)) if match else None


def _increment_status_from_name(filename: str) -> str | None:
    match = _INCREMENT_STATUS_RE.search(Path(filename).stem)
    return match.group("status").lower() if match else None


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
            ["git", "-C", str(ROOT_DIR), *args],
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


def requirement_file_slug(requirement: str | None) -> str:
    text = (requirement or "").strip()
    if not text:
        return "#OUTPUT_THE_MODEL#_#OUTPUT_THE_SHORT_SUMMARY#"
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def next_todo_increment_path(requirement: str | None = None) -> Path:
    numbers = [
        number
        for path in TODO_DIR.glob("*.md")
        for number in [_increment_number_from_name(path.name)]
        if number is not None and _increment_status_from_name(path.name) in {"todo", "done"}
    ]
    next_number = (max(numbers) + 1) if numbers else 1
    filename = (
        f"increment_{next_number:04d}_todo_"
        f"{requirement_file_slug(requirement)}.md"
    )
    return TODO_DIR / filename


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
# Behavioral guardrails
# ---------------------------------------------------------------------------

def behavioral_guardrails() -> str:
    return "\n".join([
        "## BEHAVIORAL GUARDRAILS\n",
        "- Surface assumptions, ambiguity, and tradeoffs before editing.",
        "- If the requirement has multiple plausible meanings, ask before implementing.",
        "- Choose the minimum code path that satisfies the requirement.",
        "- Avoid speculative features, abstractions, configuration, or edge handling.",
        "- Touch only lines that trace directly to the request.",
        "- Match existing style; do not refactor, reformat, or delete unrelated code.",
        "- Remove only unused code introduced by your own change.",
        "- Use the acceptance criteria plus the TDD and verification gates below as the success contract.",
    ])


# ---------------------------------------------------------------------------
# Queue-free planning prompt
# ---------------------------------------------------------------------------

def build_queue_free_plan_prompt(requirement: str | None = None) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    next_path = next_todo_increment_path(requirement)
    goal_block = "\n".join([
        "## GOAL",
        "",
        "As a result of execution, create the next todo increment file at "
        f"`{next_path}`.",
    ])
    request_text = (requirement or "").strip()
    if request_text:
        requirement_block = "\n".join([
            "## REQUIREMENT",
            "",
            request_text,
        ])
    else:
        requirement_block = "\n".join([
            "## REQUIREMENT",
            "",
            "Use the user's current request as the requirement.",
        ])

    tdd_block = "\n".join([
        "## TDD IMPLEMENTATION PLAN",
        "",
        "1. RED: write or update the smallest focused automated test for the requested behavior.",
        "2. Confirm the focused test fails for the missing behavior before editing production code.",
        "3. GREEN: implement the minimum code needed to satisfy that test.",
        "4. REFACTOR: clean only the touched logic while the focused test stays green.",
    ])

    verification_block = "\n".join([
        "## VERIFICATION GATES",
        "",
        "1. Run the focused test that failed in RED and confirm it passes.",
        "2. Run the smallest relevant broader check for the changed area.",
        "3. For UI or CLI behavior, compare the before and after output directly.",
        "4. Report the exact commands run and the observed result.",
    ])

    completion_block = "\n".join([
        "## COMPLETION",
        "",
        "Summarize the changed behavior, verification commands, and remaining risk.",
    ])

    sections = [
        "# PLANNING PROMPT",
        goal_block,
        f"_Generated: {now}_",
        (
            "_Plan the implementation. Do not read, select, summarize, or advance "
            "the increment queue from this command._"
        ),
        "---",
        behavioral_guardrails(),
        "---",
        requirement_block,
        "---",
        tdd_block,
        "---",
        verification_block,
        "---",
        completion_block,
    ]
    return "\n\n".join(sections)


# ---------------------------------------------------------------------------
# Increment loader
# ---------------------------------------------------------------------------

def _increment_files(status: str = "todo") -> list[Path]:
    wanted = status.lower()
    files = []
    for path in TODO_DIR.glob("*.md"):
        number = _increment_number_from_name(path.name)
        if number is None:
            continue
        if _increment_status_from_name(path.name) == wanted:
            files.append(path)
    return sorted(
        files,
        key=lambda p: (_increment_number_from_name(p.name) or 0, p.name),
    )


def current_todo() -> Path | None:
    todos = _increment_files("todo")
    return todos[0] if todos else None


def find_increment(number: int) -> Path | None:
    for status in ("todo", "done"):
        for f in _increment_files(status):
            if _increment_number_from_name(f.name) == number:
                return f
    return None


def parse_increment(path: Path) -> dict:
    content = _read(path)
    name = path.stem

    number = _increment_number_from_name(name) or 0
    status = _increment_status_from_name(name) or "done"

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
        behavioral_guardrails(),
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
        description="Generate a structured planning prompt without selecting work."
    )
    parser.add_argument(
        "--increment", type=int, default=None,
        help=argparse.SUPPRESS,
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

    if args.all_principles:
        print(format_conventions(load_conventions()))
        return

    freeform = " ".join(args.requirement).strip()
    if freeform:
        if args.increment is not None:
            print(
                f"warning: ignoring --increment={args.increment}; "
                f"free-form requirement supplied",
                file=sys.stderr,
            )
        print(build_queue_free_plan_prompt(freeform))
        return

    if args.increment is not None:
        print(
            "Error: increment selection belongs to todo.sh; "
            "plan.sh does not output increment details.",
            file=sys.stderr,
        )
        raise SystemExit(2)

    print(build_queue_free_plan_prompt())


if __name__ == "__main__":
    main()
