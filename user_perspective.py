"""
User perspective analyzer for the Self-Development Organism system.

Checks documentation quality and package metadata.
Requirements checking is now handled by the increment tracker.
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple

from models import (
    OrganismState,
    Perspective,
    Priority,
    Prompt,
)
from perspectives import PerspectiveAnalyzer


class UserPerspective(PerspectiveAnalyzer):
    """Analyzes from user's point of view"""

    def get_perspective(self) -> Perspective:
        return Perspective.USER

    def analyze(self) -> Tuple[Dict[str, float], List[Prompt]]:
        prompts = []

        # User: Usability, documentation quality, user experience elements
        usability_score = self._check_package_json(prompts)
        doc_score = self._check_readme(prompts)

        metrics = {
            "usability": usability_score,
            "documentation_quality": doc_score,
            "user_experience_elements": 0.5, # default for now
        }

        return metrics, prompts

    def _check_readme(self, prompts) -> float:
        readme_path = self.root_dir / "README.md"
        if not readme_path.exists():
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
            return 0.0

        content = readme_path.read_text()
        score = min(1.0, len(content) / 5000)
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
        return score

    def _check_package_json(self, prompts) -> float:
        package_json = self.root_dir / "package.json"
        if not package_json.exists():
            return 0.5
        try:
            pkg = json.loads(package_json.read_text())
        except json.JSONDecodeError:
            return 0.0

        if pkg.get("description"):
            return 1.0
        else:
            prompts.append(Prompt(
                perspective=Perspective.USER,
                priority=Priority.MEDIUM,
                title="Add package description",
                description="package.json lacks description field.",
                file_path="package.json",
                acceptance_criteria=["Add meaningful description to package.json"]
            ))
            return 0.5

