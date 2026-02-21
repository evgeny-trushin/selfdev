"""
Increment Tracker for the Self-Development Organism system.

Manages the requirements/increment_XXXX_todo_*.md ↔ done lifecycle:
  1. Find the current TODO increment (lowest numbered _todo_ file).
  2. Read it and resolve all referenced principles from principles/.
  3. On --advance, verify the current increment, rename todo → done,
     and present the next increment with injected principles.
"""

import os
import re
import glob
from pathlib import Path
from typing import Optional, List, Tuple

from analyzers import GitAnalyzer


class IncrementTracker:
    """Tracks and manages sequential requirement increments."""

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.requirements_dir = root_dir / "requirements"
        self.principles_dir = root_dir / "principles"

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def _increment_files(self, status: str = "todo") -> List[Path]:
        """Return sorted list of increment files matching *status* (todo|done)."""
        pattern = str(self.requirements_dir / f"increment_*_{status}_*.md")
        files = sorted(glob.glob(pattern))
        return [Path(f) for f in files]

    def current_todo(self) -> Optional[Path]:
        """Return the first (lowest-numbered) TODO increment file, or None."""
        todos = self._increment_files("todo")
        return todos[0] if todos else None

    def done_count(self) -> int:
        """Return how many increments have been completed."""
        return len(self._increment_files("done"))

    def total_count(self) -> int:
        """Total number of increment files (todo + done)."""
        return len(self._increment_files("todo")) + len(self._increment_files("done"))

    def all_done(self) -> bool:
        """True when no TODO increments remain."""
        return len(self._increment_files("todo")) == 0

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------

    # Section markers used by the flexible parser to detect boundaries.
    _SECTION_MARKERS = [
        r'\n\*\*Acceptance Criteria[^*]*\*\*',
        r'\n## Acceptance Criteria',
        r'\n\*\*Related Principles[^*]*\*\*',
        r'\n## Related Principles',
        r'\n\*\*Current Inventory[^*]*\*\*',
        r'\n\*\*Screenshot Assets[^*]*\*\*',
        r'\n\*\*Platform Reference[^*]*\*\*',
        r'\n---\s*$',
    ]

    @staticmethod
    def parse_increment(path: Path) -> dict:
        """Parse an increment markdown file into structured data.

        Uses a two-pass approach for resilience:
          Pass 1 (strict):   looks for ``# `` headings, ``## Description``,
                             ``## Acceptance Criteria``, ``**Requirement ID:**``
          Pass 2 (flexible): handles alternative formats — any heading level,
                             bold section headers, numbered criteria lists, and
                             body-text descriptions.

        Returns dict with keys:
          number, short_desc, status, title, requirement_id,
          description, related_principles (list of (code, path) tuples),
          acceptance_criteria (list of strings), raw_content
        """
        content = path.read_text(encoding="utf-8")
        name = path.stem  # e.g. increment_0001_todo_multi_perspective_validation

        # Extract number
        num_match = re.search(r'increment_(\d+)', name)
        number = int(num_match.group(1)) if num_match else 0

        # Extract status from filename
        status = "todo" if "_todo_" in name else "done"

        # Extract short description from filename
        desc_match = re.search(r'_(?:todo|done)_(.+)$', name)
        short_desc = desc_match.group(1) if desc_match else ""

        # ----------------------------------------------------------
        # Pass 1: strict parsing (original patterns)
        # ----------------------------------------------------------

        # Title from single-# heading
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else ""

        # Requirement ID from explicit tag
        req_match = re.search(r'\*\*Requirement ID:\*\*\s*(\S+)', content)
        requirement_id = req_match.group(1) if req_match else ""

        # Description from ``## Description`` section
        desc_section = ""
        d_match = re.search(
            r'## Description\s*\n(.*?)(?=\n## |\Z)',
            content, re.DOTALL,
        )
        if d_match:
            desc_section = d_match.group(1).strip()

        # Related principles from ``## Related Principles`` section
        principles = []
        princ_match = re.search(
            r'## Related Principles\s*\n(.*?)(?=\n## |\Z)',
            content, re.DOTALL,
        )
        if princ_match:
            for m in re.finditer(
                r'\[([^\]]+)\]\(([^)]+)\)', princ_match.group(1)
            ):
                link_text = m.group(1)
                link_path = m.group(2)
                code = link_text.split("—")[0].split("–")[0].strip()
                principles.append((code, link_path))

        # Acceptance criteria from ``## Acceptance Criteria`` section
        criteria = []
        ac_match = re.search(
            r'## Acceptance Criteria\s*\n(.*?)(?=\n## |\Z)',
            content, re.DOTALL,
        )
        if ac_match:
            for line in ac_match.group(1).strip().splitlines():
                line = line.strip()
                cleaned = re.sub(r'^-\s*\[[ x]\]\s*', '', line)
                cleaned = re.sub(r'^-\s*', '', cleaned).strip()
                if cleaned:
                    criteria.append(cleaned)

        # ----------------------------------------------------------
        # Pass 2: flexible fallback
        # ----------------------------------------------------------

        # Title fallback: accept any heading level (##, ###, …)
        if not title:
            any_heading = re.search(r'^#{1,6}\s+(.+)$', content, re.MULTILINE)
            if any_heading:
                title = any_heading.group(1).strip()
        if not title:
            title = short_desc

        # Requirement ID fallback: extract prefix from heading
        # e.g. "### W6: Screenshot…" → requirement_id = "W6"
        # e.g. "### R1: Multi-Perspective…" → requirement_id = "R1"
        if not requirement_id and title:
            id_match = re.match(
                r'([A-Z][A-Za-z0-9_]*(?:-\d+)?)\s*[:—–]\s', title,
            )
            if id_match:
                requirement_id = id_match.group(1)

        # Description fallback: body text between first heading and the
        # earliest known section marker (bold or heading style).
        if not desc_section:
            first_heading = re.search(
                r'^#{1,6}\s+.+$', content, re.MULTILINE,
            )
            if first_heading:
                remaining = content[first_heading.end():]
                earliest_pos = len(remaining)
                for marker in IncrementTracker._SECTION_MARKERS:
                    m = re.search(marker, remaining, re.MULTILINE)
                    if m and m.start() < earliest_pos:
                        earliest_pos = m.start()
                desc_section = remaining[:earliest_pos].strip()

        # Related principles fallback: ``**Related Principles:**`` bold
        if not principles:
            princ_bold = re.search(
                r'\*\*Related Principles[^*]*\*\*:?\s*\n'
                r'(.*?)(?=\n\*\*[A-Z]|\n#{1,6}\s|\n---|\Z)',
                content, re.DOTALL,
            )
            if princ_bold:
                for m in re.finditer(
                    r'\[([^\]]+)\]\(([^)]+)\)', princ_bold.group(1)
                ):
                    link_text = m.group(1)
                    link_path = m.group(2)
                    code = link_text.split("—")[0].split("–")[0].strip()
                    principles.append((code, link_path))

        # Acceptance criteria fallback: ``**Acceptance Criteria:**`` bold
        if not criteria:
            ac_bold = re.search(
                r'\*\*Acceptance Criteria[^*]*\*\*:?\s*\n'
                r'(.*?)(?=\n\*\*[A-Z]|\n#{1,6}\s|\n---|\Z)',
                content, re.DOTALL,
            )
            if ac_bold:
                for line in ac_bold.group(1).strip().splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    # Strip checkbox, dash, or numbered-list prefix
                    cleaned = re.sub(r'^-\s*\[[ x]\]\s*', '', line)
                    cleaned = re.sub(r'^-\s*', '', cleaned)
                    cleaned = re.sub(r'^\d+\.\s*', '', cleaned).strip()
                    if cleaned:
                        criteria.append(cleaned)

        return {
            "number": number,
            "short_desc": short_desc,
            "status": status,
            "title": title,
            "requirement_id": requirement_id,
            "description": desc_section,
            "related_principles": principles,
            "acceptance_criteria": criteria,
            "raw_content": content,
        }

    # ------------------------------------------------------------------
    # Parse-completeness check
    # ------------------------------------------------------------------

    @staticmethod
    def _is_parse_complete(inc_data: dict) -> bool:
        """Return True when the parsed increment has minimum viable content.

        A parse is considered complete only when the parser extracted a
        non-empty *description*.  Both truly empty files and files with
        content in an unrecognisable format will return False, triggering
        the self-inspection prompt.
        """
        return bool(inc_data.get("description", "").strip())

    def load_principle(self, code: str) -> Optional[str]:
        """Load principle content by code (e.g. 'P2', 'B1', 'USR')."""
        path = self.principles_dir / f"{code}.md"
        if path.exists():
            return path.read_text(encoding="utf-8")
        return None

    def resolve_principles(self, principle_refs: List[Tuple[str, str]]) -> List[dict]:
        """Resolve a list of (code, rel_path) into loaded principle dicts.

        Returns list of {code, title, content} dicts.
        """
        results = []
        seen = set()
        for code, rel_path in principle_refs:
            if code in seen:
                continue
            seen.add(code)
            content = self.load_principle(code)
            if content is None:
                continue
            # Extract title from first heading
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            title = title_match.group(1).strip() if title_match else code
            results.append({
                "code": code,
                "title": title,
                "content": content.strip(),
            })
        return results

    # ------------------------------------------------------------------
    # Lifecycle: verify & advance
    # ------------------------------------------------------------------

    def mark_done(self, increment_path: Path) -> Path:
        """Rename an increment file from _todo_ to _done_.

        Returns the new path.
        """
        old_name = increment_path.name
        new_name = old_name.replace("_todo_", "_done_", 1)
        new_path = increment_path.parent / new_name
        increment_path.rename(new_path)
        return new_path

    # ------------------------------------------------------------------
    # Self-inspection prompt (edge-case safety net)
    # ------------------------------------------------------------------

    def format_self_inspection_prompt(self, increment_path: Path,
                                      inc_data: dict) -> str:
        """Generate a diagnostic prompt when the parser cannot extract
        meaningful content from an increment file.

        Three scenarios are handled:
          1. File is empty → prompt to write the requirement spec.
          2. File has content but parsing yields empty key fields →
             self-inspection prompt with raw content included.
          3. (Future) Any other anomaly the caller needs to surface.
        """
        lines: List[str] = []
        raw = inc_data.get("raw_content", "")
        progress = self.done_count()
        total = self.total_count()

        lines.append("=" * 70)
        lines.append(
            f"  ⚠️  INCREMENT {inc_data['number']:04d}: SELF-INSPECTION REQUIRED"
        )
        lines.append(f"  File: {increment_path.name}")
        lines.append(f"  Progress: {progress}/{total} increments completed")
        lines.append("=" * 70)
        lines.append("")

        if not raw.strip():
            # --- Scenario 1: empty file ---
            lines.append("DIAGNOSIS: File is EMPTY")
            lines.append("-" * 40)
            lines.append("  The increment file exists but contains no content.")
            lines.append("")
            lines.append("ACTION REQUIRED:")
            lines.append("-" * 40)
            lines.append("  Write the requirement specification into this file.")
            lines.append("  Recommended structure (any heading level accepted):")
            lines.append("")
            lines.append("    ### <ID>: <Title>")
            lines.append("    <Requirement description — one or more paragraphs>")
            lines.append("")
            lines.append("    **Acceptance Criteria:**")
            lines.append("    1. <criterion>")
            lines.append("    2. <criterion>")
            lines.append("")
            lines.append("    **Related Principles:**")
            lines.append("    - [CODE](../principles/CODE.md)")
            lines.append("")
        else:
            # --- Scenario 2: has content but non-standard format ---
            lines.append("DIAGNOSIS: Non-standard format — key fields could not"
                         " be extracted")
            lines.append("-" * 40)
            lines.append(
                "  The file contains content, but the parser could not extract"
            )
            lines.append(
                "  a description or acceptance criteria.  The raw content is"
            )
            lines.append("  included below for manual interpretation.")
            lines.append("")

            # Show what the parser found / missed
            lines.append("PARSE RESULTS:")
            lines.append("-" * 40)
            fields = [
                ("Title", inc_data.get("title", "")),
                ("Requirement ID", inc_data.get("requirement_id", "")),
                ("Description", inc_data.get("description", "")),
                ("Acceptance Criteria",
                 str(len(inc_data.get("acceptance_criteria", [])))),
                ("Related Principles",
                 str(len(inc_data.get("related_principles", [])))),
            ]
            for label, value in fields:
                status = "✅" if value and value != "0" else "❌ EMPTY"
                lines.append(f"  {label}: {status}")
            lines.append("")

            lines.append("RAW FILE CONTENT:")
            lines.append("-" * 40)
            lines.append(raw)
            lines.append("")

            lines.append("ACTION REQUIRED:")
            lines.append("-" * 40)
            lines.append("  Review the raw content above and choose one of:")
            lines.append("")
            lines.append(
                "  Option A — Implement as-is: treat the raw text as the"
            )
            lines.append(
                "    requirement and implement it directly."
            )
            lines.append("")
            lines.append(
                "  Option B — Reformat first: restructure the file so the"
            )
            lines.append(
                "    parser can extract fields automatically.  Recommended"
            )
            lines.append("    structure:")
            lines.append("")
            lines.append("      ### <ID>: <Title>")
            lines.append("      <Requirement description>")
            lines.append("")
            lines.append("      **Acceptance Criteria:**")
            lines.append("      1. <criterion>")
            lines.append("")

        # Workflow reminder
        short = inc_data['short_desc'].replace('_', ' ').title()
        commit_msg = f"INCREMENT {inc_data['number']:04d}: {short}"
        lines.append("WORKFLOW:")
        lines.append("-" * 40)
        lines.append("  1. Resolve the issue above")
        lines.append("  2. Run tests:  python -m pytest selfdev/tests/")
        lines.append("  3. Run linter: python -m py_compile <changed files>")
        lines.append("  4. List changed files in the commit body")
        lines.append(f'  5. git add -A && git commit -m "{commit_msg}"')
        lines.append("  6. git push")
        lines.append("  7. Run ./develop.sh  (verify & get next increment)")
        lines.append("")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Prompt generation
    # ------------------------------------------------------------------

    def format_increment_prompt(self, increment_path: Path) -> str:
        """Build a full prompt string for the given increment.

        If the parser extracts meaningful content, the normal structured
        prompt is returned.  Otherwise a *self-inspection* prompt is
        generated so the AI (or developer) can diagnose and proceed.
        """
        inc = self.parse_increment(increment_path)

        # --- Edge-case: parsing produced null / empty key fields ---
        if not self._is_parse_complete(inc):
            return self.format_self_inspection_prompt(increment_path, inc)

        principles = self.resolve_principles(inc["related_principles"])

        lines: List[str] = []

        # Header
        lines.append("=" * 70)
        lines.append(f"  INCREMENT {inc['number']:04d}: {inc['title']}")
        lines.append(f"  Requirement: {inc['requirement_id']}")
        lines.append(f"  Status: TODO")
        progress = self.done_count()
        total = self.total_count()
        lines.append(f"  Progress: {progress}/{total} increments completed")
        lines.append("=" * 70)
        lines.append("")

        # Scoped target
        lines.append("SCOPE:")
        lines.append("-" * 40)
        lines.append(f"  Target increment: {inc['number']:04d} — {inc['title']}")
        lines.append(f"  Requirement ID:   {inc['requirement_id']}")
        lines.append(f"  Only files related to this increment may be created or modified.")
        lines.append("")

        # Description
        lines.append("REQUIREMENT:")
        lines.append("-" * 40)
        lines.append(inc["description"])
        lines.append("")

        # Acceptance criteria
        if inc["acceptance_criteria"]:
            lines.append("ACCEPTANCE CRITERIA:")
            lines.append("-" * 40)
            for i, criterion in enumerate(inc["acceptance_criteria"], 1):
                lines.append(f"  {i}. {criterion}")
            lines.append("")

        # Allowed / forbidden actions
        lines.append("RULES:")
        lines.append("-" * 40)
        lines.append("  ALLOWED:")
        lines.append("    - Implement the requirement described above.")
        lines.append("    - Create or modify files directly related to this increment.")
        lines.append("    - Add or update tests that verify this increment.")
        lines.append("  FORBIDDEN:")
        lines.append("    - Do NOT auto-advance increments by rerunning develop.sh.")
        lines.append("    - Do NOT mark an increment done until tests pass and all")
        lines.append("      referenced files are implemented.")
        lines.append("    - Do NOT modify unrelated increments or requirements.")
        lines.append("    - Do NOT skip acceptance criteria.")
        lines.append("")

        # Completion criteria
        lines.append("COMPLETION CRITERIA:")
        lines.append("-" * 40)
        lines.append("  For this increment, complete ALL of the following in order:")
        lines.append("    1. Implement the requirement (code changes).")
        lines.append("    2. Run tests and linter — all must pass.")
        lines.append("    3. List all changed/created files in the commit message body.")
        lines.append("    4. Only then advance ONE step (commit & push).")
        lines.append("")

        # Traceability
        lines.append("TRACEABILITY:")
        lines.append("-" * 40)
        lines.append("  In your final summary / commit message body:")
        lines.append("    - Map each acceptance criterion to the file(s) that satisfy it.")
        lines.append("    - Map each review comment to the exact commit diff hunk.")
        lines.append("    - Reference the increment number in every commit message.")
        lines.append("")

        # Injected principles
        if principles:
            lines.append("APPLICABLE PRINCIPLES:")
            lines.append("=" * 70)
            for p in principles:
                lines.append("")
                lines.append(f"--- {p['code']} ---")
                lines.append(p["content"])
                lines.append("")
            lines.append("=" * 70)

        # Workflow with commit message
        short = inc['short_desc'].replace('_', ' ').title()
        commit_msg = f"INCREMENT {inc['number']:04d}: {short}"
        lines.append("")
        lines.append("WORKFLOW:")
        lines.append("-" * 40)
        lines.append(f"  1. Implement the requirement above")
        lines.append(f"  2. Run tests:  python -m pytest selfdev/tests/")
        lines.append(f"  3. Run linter: python -m py_compile <changed files>")
        lines.append(f"  4. List changed files in the commit body")
        lines.append(f'  5. git add -A && git commit -m "{commit_msg}"')
        lines.append(f"  6. git push")
        lines.append(f"  7. Run ./develop.sh  (verify & get next increment)")
        lines.append("")

        return "\n".join(lines)

    def format_done_summary(self, done_path: Path, next_path: Optional[Path],
                            changed_files: Optional[List[str]] = None) -> str:
        """Build a summary for a just-completed increment.

        *changed_files* — if supplied — are listed for traceability.
        """
        inc = self.parse_increment(done_path)
        lines: List[str] = []

        lines.append("")
        lines.append("=" * 70)
        lines.append(f"  ✓ COMPLETED: INCREMENT {inc['number']:04d}")
        lines.append(f"    {inc['title']}")
        lines.append(f"    Renamed: ...{done_path.name}")
        progress = self.done_count()
        total = self.total_count()
        lines.append(f"    Progress: {progress}/{total} increments completed")
        lines.append("=" * 70)

        # Traceability: list changed files
        if changed_files:
            lines.append("")
            lines.append("  CHANGED FILES:")
            for f in changed_files:
                lines.append(f"    - {f}")

        # Traceability: map acceptance criteria
        if inc["acceptance_criteria"]:
            lines.append("")
            lines.append("  ACCEPTANCE CRITERIA STATUS:")
            for i, criterion in enumerate(inc["acceptance_criteria"], 1):
                lines.append(f"    {i}. [done] {criterion}")

        lines.append("")

        if next_path:
            lines.append("  ➜ Next increment ready. See below.")
            lines.append("")
        else:
            lines.append("  ★ ALL INCREMENTS COMPLETED!")
            lines.append("")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Revert / Redo prompt generation
    # ------------------------------------------------------------------

    def _find_increment_file(self, number: int) -> Optional[Path]:
        """Find an increment file (todo or done) by its number."""
        for status in ("todo", "done"):
            pattern = str(self.requirements_dir / f"increment_{number:04d}_{status}_*.md")
            files = glob.glob(pattern)
            if files:
                return Path(files[0])
        return None

    def format_revert_prompt(self, increment_number: int) -> str:
        """Generate a prompt to revert a single increment using git history.

        The prompt instructs the developer/AI to find all commits related
        to the given increment and revert them.
        """
        git = GitAnalyzer(self.root_dir)
        commits = git.get_commits_for_increment(increment_number)
        inc_file = self._find_increment_file(increment_number)
        inc_data = self.parse_increment(inc_file) if inc_file else None

        lines: List[str] = []
        lines.append("=" * 70)
        lines.append(f"  REVERT INCREMENT {increment_number:04d}")
        if inc_data:
            lines.append(f"  {inc_data['title']}")
        lines.append("=" * 70)
        lines.append("")

        lines.append("OBJECTIVE:")
        lines.append("-" * 40)
        lines.append(f"  Revert all changes introduced by increment {increment_number:04d}.")
        lines.append("  Use git history to identify and undo the relevant commits.")
        lines.append("")

        lines.append("GIT COMMITS FOR THIS INCREMENT:")
        lines.append("-" * 40)
        if commits:
            for c in commits:
                lines.append(f"  {c['hash'][:8]}  {c['message']}")
                diff_stat = git.get_diff_for_commit(c['hash'])
                if diff_stat:
                    for dl in diff_stat.splitlines():
                        lines.append(f"    {dl}")
        else:
            lines.append("  No commits found matching this increment.")
            lines.append("  Search manually: git log --all --grep='INCREMENT "
                         f"{increment_number:04d}'")
        lines.append("")

        lines.append("STEPS:")
        lines.append("-" * 40)
        if commits:
            hashes = " ".join(c['hash'][:8] for c in reversed(commits))
            lines.append(f"  1. Review the commits above for correctness.")
            lines.append(f"  2. Revert in reverse chronological order:")
            for i, c in enumerate(commits, 1):
                lines.append(f"     git revert --no-commit {c['hash'][:8]}")
            lines.append(f"  3. Resolve any merge conflicts.")
            lines.append(f"  4. Run tests:  python -m pytest selfdev/tests/")
            lines.append(f"  5. git add -A && git commit -m \"REVERT INCREMENT"
                         f" {increment_number:04d}\"")
            lines.append(f"  6. git push")
        else:
            lines.append("  1. Manually identify the changes for this increment.")
            lines.append("  2. Undo the changes.")
            lines.append("  3. Run tests:  python -m pytest selfdev/tests/")
            lines.append(f"  4. git add -A && git commit -m \"REVERT INCREMENT"
                         f" {increment_number:04d}\"")
            lines.append(f"  5. git push")
        lines.append("")

        if inc_file and "_done_" in inc_file.name:
            lines.append("POST-REVERT:")
            lines.append("-" * 40)
            lines.append(f"  Rename the increment file back to todo:")
            todo_name = inc_file.name.replace("_done_", "_todo_", 1)
            lines.append(f"    mv {inc_file.name} {todo_name}")
            lines.append("")

        return "\n".join(lines)

    def format_revert_from_prompt(self, from_increment: int) -> str:
        """Generate a prompt to revert from a given increment down to the
        current todo increment.

        This covers reverting all increments in the range
        [current_todo_number, from_increment].
        """
        current = self.current_todo()
        current_num = 0
        if current:
            inc_data = self.parse_increment(current)
            current_num = inc_data["number"]

        if current_num == 0:
            # All done — revert from from_increment to latest done
            done_files = self._increment_files("done")
            if done_files:
                last_done = self.parse_increment(done_files[-1])
                current_num = last_done["number"]

        git = GitAnalyzer(self.root_dir)

        lines: List[str] = []
        lines.append("=" * 70)
        lines.append(f"  REVERT INCREMENTS {from_increment:04d} → "
                      f"{current_num:04d}")
        lines.append("=" * 70)
        lines.append("")

        lines.append("OBJECTIVE:")
        lines.append("-" * 40)
        lines.append(f"  Revert all changes from increment {from_increment:04d}"
                      f" down to {current_num:04d}.")
        lines.append("  Process increments in reverse order (highest first).")
        lines.append("")

        # Collect commits for each increment in range
        lines.append("INCREMENTS TO REVERT (reverse order):")
        lines.append("-" * 40)
        for num in range(from_increment, current_num - 1, -1):
            inc_file = self._find_increment_file(num)
            title = ""
            if inc_file:
                inc_data = self.parse_increment(inc_file)
                title = inc_data.get("title", "")

            commits = git.get_commits_for_increment(num)
            lines.append(f"  INCREMENT {num:04d}: {title}")
            if commits:
                for c in commits:
                    lines.append(f"    {c['hash'][:8]}  {c['message']}")
            else:
                lines.append(f"    (no commits found)")
            lines.append("")

        lines.append("STEPS:")
        lines.append("-" * 40)
        lines.append(f"  1. Revert each increment from {from_increment:04d} "
                      f"down to {current_num:04d}.")
        lines.append(f"  2. For each increment, revert its commits in reverse"
                      " chronological order:")
        lines.append(f"     git revert --no-commit <hash>")
        lines.append(f"  3. Resolve any merge conflicts at each step.")
        lines.append(f"  4. Run tests:  python -m pytest selfdev/tests/")
        lines.append(f"  5. git add -A && git commit -m \"REVERT INCREMENTS"
                      f" {from_increment:04d}-{current_num:04d}\"")
        lines.append(f"  6. git push")
        lines.append("")

        lines.append("POST-REVERT:")
        lines.append("-" * 40)
        lines.append(f"  Rename done increment files back to todo for"
                      f" {current_num:04d}–{from_increment:04d}.")
        lines.append("")

        return "\n".join(lines)

    def format_redo_prompt(self, increment_number: int) -> str:
        """Generate a prompt to redo (revert then re-implement) an increment.

        First section: instructions to revert the increment (same as
        format_revert_prompt).  Second section: the original increment
        requirement to implement again.
        """
        revert_section = self.format_revert_prompt(increment_number)

        inc_file = self._find_increment_file(increment_number)
        if inc_file:
            inc = self.parse_increment(inc_file)
            principles = self.resolve_principles(inc["related_principles"])
        else:
            inc = None
            principles = []

        lines: List[str] = []
        lines.append(revert_section)
        lines.append("")
        lines.append("=" * 70)
        lines.append(f"  AFTER REVERT — RE-IMPLEMENT INCREMENT"
                      f" {increment_number:04d}")
        lines.append("=" * 70)
        lines.append("")

        if inc and inc.get("description"):
            lines.append("REQUIREMENT:")
            lines.append("-" * 40)
            lines.append(inc["description"])
            lines.append("")

            if inc["acceptance_criteria"]:
                lines.append("ACCEPTANCE CRITERIA:")
                lines.append("-" * 40)
                for i, criterion in enumerate(inc["acceptance_criteria"], 1):
                    lines.append(f"  {i}. {criterion}")
                lines.append("")

            if principles:
                lines.append("APPLICABLE PRINCIPLES:")
                lines.append("=" * 70)
                for p in principles:
                    lines.append("")
                    lines.append(f"--- {p['code']} ---")
                    lines.append(p["content"])
                    lines.append("")
                lines.append("=" * 70)
        else:
            lines.append("  (Increment file not found or empty —"
                          " re-create the requirement before implementing.)")
        lines.append("")

        short = inc['short_desc'].replace('_', ' ').title() if inc else f"Increment {increment_number:04d}"
        commit_msg = f"INCREMENT {increment_number:04d}: {short} (redo)"
        lines.append("WORKFLOW:")
        lines.append("-" * 40)
        lines.append(f"  1. Complete the revert steps above first.")
        lines.append(f"  2. Implement the requirement from scratch.")
        lines.append(f"  3. Run tests:  python -m pytest selfdev/tests/")
        lines.append(f"  4. Run linter: python -m py_compile <changed files>")
        lines.append(f"  5. List changed files in the commit body")
        lines.append(f'  6. git add -A && git commit -m "{commit_msg}"')
        lines.append(f"  7. git push")
        lines.append(f"  8. Run ./develop.sh  (verify & get next increment)")
        lines.append("")

        return "\n".join(lines)
