"""
User perspective analyzer for the Self-Development Organism system.

Checks documentation quality, package metadata, changelog presence,
and requirements.md compliance.
"""

import json
from pathlib import Path
from typing import List, Optional, Tuple

from models import (
    OrganismState,
    Perspective,
    Priority,
    Prompt,
    DevelopmentStage,
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

    def _check_requirements(self, fitness_components, prompts):
        """Check requirements.md presence."""
        requirements_path = self.root_dir / "requirements.md"
        if requirements_path.exists():
            fitness_components.append(1.0)
        else:
            # Not critical, just a bonus if it exists
            fitness_components.append(0.5)

