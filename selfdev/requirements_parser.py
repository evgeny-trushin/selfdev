"""
Requirements parser module.
Parses requirements.md generically.
"""

import re
from typing import List, Dict

from models import Priority

class RequirementsParser:
    """Parses requirements.md into structured requirement sections."""

    @staticmethod
    def parse_requirements(content: str) -> List[dict]:
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
    def classify_priority(req_id: str) -> Priority:
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
