"""
User perspective analyzer for the Self-Development Organism system.

Checks documentation quality, package metadata, changelog presence,
and requirements.md compliance.  Parses requirements.md generically —
no project-specific knowledge required.
"""

import json
import re
from pathlib import Path
from typing import List, Optional, Tuple

from models import (
    OrganismState,
    Perspective,
    Priority,
    Prompt,
    DevelopmentStage,
    REQUIREMENTS_FILE,
)
from perspectives import PerspectiveAnalyzer


class UserPerspective(PerspectiveAnalyzer):
    """Analyzes from user's point of view"""

    def get_perspective(self) -> Perspective:
        return Perspective.USER

    def analyze(self) -> Tuple[float, List[Prompt]]:
        prompts = []
        fitness_components = []

        self._check_readme(fitness_components, prompts)
        self._check_package_json(fitness_components, prompts)
        self._check_changelog(fitness_components, prompts)
        self._check_requirements(fitness_components, prompts)

        fitness = sum(fitness_components) / len(fitness_components) if fitness_components else 0.5
        return fitness, prompts

    def _check_readme(self, fitness_components, prompts):
        readme_path = self.root_dir / "README.md"
        if not readme_path.exists():
            fitness_components.append(0.0)
            prompts.append(Prompt(
                perspective=Perspective.USER,
                priority=Priority.CRITICAL,
                title="Create README.md",
                description="No README.md found. Users need documentation to understand the project.",
                acceptance_criteria=[
                    "Create README.md in project root",
                    "Include project description",
                    "Add basic usage instructions"
                ]
            ))
            return

        content = readme_path.read_text()
        score = min(1.0, len(content) / 5000)
        fitness_components.append(score)
        if len(content) < 500:
            prompts.append(Prompt(
                perspective=Perspective.USER,
                priority=Priority.HIGH,
                title="Enhance README documentation",
                description="README.md is minimal. Add installation instructions, usage examples, and feature descriptions.",
                file_path="README.md",
                metric_current=len(content),
                metric_target=2000,
                acceptance_criteria=[
                    "Include installation instructions",
                    "Add at least 2 usage examples",
                    "Document main features"
                ]
            ))

    def _check_package_json(self, fitness_components, prompts):
        package_json = self.root_dir / "package.json"
        if not package_json.exists():
            return
        try:
            pkg = json.loads(package_json.read_text())
        except json.JSONDecodeError:
            fitness_components.append(0.0)
            return
        if pkg.get("description"):
            fitness_components.append(1.0)
        else:
            fitness_components.append(0.5)
            prompts.append(Prompt(
                perspective=Perspective.USER,
                priority=Priority.MEDIUM,
                title="Add package description",
                description="package.json lacks description field.",
                file_path="package.json",
                acceptance_criteria=["Add meaningful description to package.json"]
            ))

    def _check_changelog(self, fitness_components, prompts):
        changelog_exists = (self.root_dir / "CHANGELOG.md").exists()
        fitness_components.append(1.0 if changelog_exists else 0.3)
        if not changelog_exists:
            prompts.append(Prompt(
                perspective=Perspective.USER,
                priority=Priority.LOW,
                title="Create CHANGELOG.md",
                description="No changelog found. Users benefit from knowing what changed between versions.",
                acceptance_criteria=["Create CHANGELOG.md following Keep a Changelog format"]
            ))

    # ------------------------------------------------------------------
    # Generic requirements.md parser
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_requirements(content: str) -> List[dict]:
        """Parse requirements.md into structured requirement sections.

        Recognises headings like ``### R1: Title``, ``### FR3: Title``,
        ``### NFR2: Title``, ``### OA-R5: Title``.
        Extracts the first descriptive paragraph and any
        ``**Acceptance Criteria:**`` / ``## Acceptance Checks`` bullet list.
        """
        pattern = re.compile(
            r'^###\s+([A-Z][\w-]*\d+):\s+(.+)$', re.MULTILINE
        )
        matches = list(pattern.finditer(content))
        requirements: List[dict] = []
        for i, m in enumerate(matches):
            req_id = m.group(1)
            title = m.group(2).strip()
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            body = content[start:end].strip()

            # Extract acceptance criteria bullet list
            ac_lines: List[str] = []
            ac_match = re.search(
                r'\*\*Acceptance Criteria:?\*\*\s*\n((?:\s*[-\d.]+\s+.+\n?)+)',
                body,
            )
            if ac_match:
                for line in ac_match.group(1).strip().splitlines():
                    cleaned = re.sub(r'^\s*[-\d.]+\s*', '', line).strip()
                    if cleaned:
                        ac_lines.append(cleaned)

            # First meaningful paragraph as description (skip tables/code)
            desc_lines: List[str] = []
            for line in body.splitlines():
                stripped = line.strip()
                if not stripped:
                    if desc_lines:
                        break
                    continue
                if stripped.startswith(('|', '```', '**Acceptance')):
                    if desc_lines:
                        break
                    continue
                desc_lines.append(stripped)
            description = ' '.join(desc_lines) if desc_lines else title

            requirements.append({
                'id': req_id,
                'title': title,
                'description': description,
                'acceptance_criteria': ac_lines,
            })
        return requirements

    @staticmethod
    def _classify_priority(req_id: str) -> Priority:
        """Map requirement ID prefix to a priority level.

        Convention (most-specific match wins):
          FR / R  → CRITICAL  (functional / core)
          W / D   → HIGH      (website / deployment)
          T       → MEDIUM    (technical)
          NFR / N → MEDIUM    (non-functional)
          OA-R    → LOW       (UI detail)
        Anything else defaults to MEDIUM.
        """
        prefix = re.sub(r'\d+$', '', req_id)   # strip trailing digits
        mapping = {
            'FR': Priority.CRITICAL,
            'R': Priority.CRITICAL,
            'W': Priority.HIGH,
            'D': Priority.HIGH,
            'T': Priority.MEDIUM,
            'NFR': Priority.MEDIUM,
            'N': Priority.MEDIUM,
            'OA-R': Priority.LOW,
        }
        # Try longest prefix first so NFR beats N, OA-R beats O, etc.
        for pfx in sorted(mapping, key=len, reverse=True):
            if prefix == pfx:
                return mapping[pfx]
        return Priority.MEDIUM

    def _check_requirements(self, fitness_components, prompts):
        """Parse requirements.md and generate a prompt per requirement.

        This is a generic parser — it works with any project's
        requirements.md as long as requirements use ``### ID: Title``
        headings and optionally list ``**Acceptance Criteria:**``.

        Searches for requirements.md in the project root first,
        then falls back to the selfdev directory (REQUIREMENTS_FILE)
        only when analysing the project this selfdev instance belongs to.
        """
        requirements_path = self.root_dir / "requirements.md"
        if not requirements_path.exists():
            # Fallback: selfdev's own requirements.md, but only when
            # root_dir is the project that contains this selfdev instance
            if REQUIREMENTS_FILE.exists() and REQUIREMENTS_FILE.parent.parent == self.root_dir:
                requirements_path = REQUIREMENTS_FILE
            else:
                return
        if not requirements_path.exists():
            return

        try:
            content = requirements_path.read_text()
        except OSError:
            return

        reqs = self._parse_requirements(content)
        if not reqs:
            return

        for req in reqs:
            priority = self._classify_priority(req['id'])
            prompts.append(Prompt(
                perspective=Perspective.USER,
                priority=priority,
                title=f"[{req['id']}] {req['title']}",
                description=req['description'],
                file_path="requirements.md",
                acceptance_criteria=(
                    req['acceptance_criteria'] if req['acceptance_criteria']
                    else [req['title']]
                ),
                tags=[req['id']],
            ))

        fitness_components.append(min(1.0, len(reqs) / 10.0))

