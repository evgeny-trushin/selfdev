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

        # User | Usability, documentation quality, user experience elements
        metrics = {
            "usability": 0.5,
            "documentation_quality": 0.5,
            "user_experience_elements": 0.5
        }

        doc_fitness_components = []

        self._check_readme(doc_fitness_components, prompts)
        self._check_package_json(doc_fitness_components, prompts)

        if doc_fitness_components:
            metrics["documentation_quality"] = sum(doc_fitness_components) / len(doc_fitness_components)
            # Default other metrics to doc quality to represent general user fitness
            metrics["usability"] = metrics["documentation_quality"]
            metrics["user_experience_elements"] = metrics["documentation_quality"]

        return metrics, prompts

    def _check_readme(self, doc_fitness_components, prompts):
        readme_path = self.root_dir / "README.md"
        if not readme_path.exists():
            doc_fitness_components.append(0.0)
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
        doc_fitness_components.append(score)
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

    def _check_package_json(self, doc_fitness_components, prompts):
        package_json = self.root_dir / "package.json"
        if not package_json.exists():
            return
        try:
            pkg = json.loads(package_json.read_text())
        except json.JSONDecodeError:
            doc_fitness_components.append(0.0)
            return
        if pkg.get("description"):
            doc_fitness_components.append(1.0)
        else:
            doc_fitness_components.append(0.5)
            prompts.append(Prompt(
                perspective=Perspective.USER,
                priority=Priority.MEDIUM,
                title="Add package description",
                description="package.json lacks description field.",
                file_path="package.json",
                acceptance_criteria=["Add meaningful description to package.json"]
            ))

