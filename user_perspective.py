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
        fitness_components = []

        self._check_readme(fitness_components, prompts)
        self._check_package_json(fitness_components, prompts)

        if fitness_components:
            doc_score = fitness_components[0]
            usability_score = fitness_components[1] if len(fitness_components) > 1 else 0.5
        else:
            doc_score = 0.5
            usability_score = 0.5

        return {
            "usability": usability_score,
            "documentation_quality": doc_score,
            "user_experience_elements": 1.0
        }, prompts

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
                ],
                reason="README.md is missing from project root"
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
                ],
                reason=f"README.md is only {len(content)} chars, below 500-char minimum"
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
                acceptance_criteria=["Add meaningful description to package.json"],
                reason="package.json description field is empty or missing"
            ))

