"""Tests for the PromptFormatter."""

import unittest
from pathlib import Path
import sys

# Add selfdev root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.formatter import PromptFormatter
from lib.models import (
    Perspective,
    Priority,
    Prompt,
    OrganismState,
)

class TestPromptFormatter(unittest.TestCase):

    def test_format_prompt_no_color(self):
        formatter = PromptFormatter(use_colors=False)
        p = Prompt(
            perspective=Perspective.USER,
            priority=Priority.HIGH,
            title="Test title",
            description="Test description",
            acceptance_criteria=["Criterion 1"],
        )
        output = formatter.format_prompt(p)
        self.assertIn("[HIGH]", output)
        self.assertIn("Test title", output)
        self.assertIn("Test description", output)
        self.assertIn("Criterion 1", output)

    def test_format_prompt_with_location(self):
        formatter = PromptFormatter(use_colors=False)
        p = Prompt(
            perspective=Perspective.SYSTEM,
            priority=Priority.MEDIUM,
            title="Refactor",
            description="Too complex",
            file_path="src/module.py",
            line_number=42,
        )
        output = formatter.format_prompt(p)
        self.assertIn("src/module.py:42", output)

    def test_format_prompt_with_metrics(self):
        formatter = PromptFormatter(use_colors=False)
        p = Prompt(
            perspective=Perspective.TEST,
            priority=Priority.HIGH,
            title="Coverage",
            description="Low coverage",
            metric_current=30.0,
            metric_target=80.0,
        )
        output = formatter.format_prompt(p)
        self.assertIn("30.0", output)
        self.assertIn("80.0", output)

    def test_format_header(self):
        formatter = PromptFormatter(use_colors=False)
        state = OrganismState(generation=5)
        output = formatter.format_header(Perspective.USER, 0.75, state)
        self.assertIn("USER", output)
        self.assertIn("75.00%", output)
        self.assertIn("growth", output)

    def test_format_summary(self):
        formatter = PromptFormatter(use_colors=False)
        state = OrganismState()
        state.fitness_scores = {"user": 0.8, "test": 0.6}
        prompts = [
            Prompt(perspective=Perspective.USER, priority=Priority.HIGH,
                   title="A", description="a"),
            Prompt(perspective=Perspective.TEST, priority=Priority.CRITICAL,
                   title="B", description="b"),
        ]
        output = formatter.format_summary(state, prompts)
        self.assertIn("Total Prompts: 2", output)
        self.assertIn("CRITICAL: 1", output)
        self.assertIn("HIGH: 1", output)

    def test_color_output(self):
        formatter = PromptFormatter(use_colors=True)
        p = Prompt(
            perspective=Perspective.USER,
            priority=Priority.CRITICAL,
            title="Critical issue",
            description="Very critical",
        )
        output = formatter.format_prompt(p)
        self.assertIn("\033[91m", output)

    def test_format_prompt_without_location(self):
        formatter = PromptFormatter(use_colors=False)
        p = Prompt(
            perspective=Perspective.USER,
            priority=Priority.INFO,
            title="Info only",
            description="No location",
        )
        output = formatter.format_prompt(p)
        self.assertNotIn("Location:", output)

    def test_format_prompt_file_path_only(self):
        formatter = PromptFormatter(use_colors=False)
        p = Prompt(
            perspective=Perspective.USER,
            priority=Priority.LOW,
            title="File only",
            description="Has file",
            file_path="src/module.py",
        )
        output = formatter.format_prompt(p)
        self.assertIn("src/module.py", output)
        self.assertNotIn(":", output.split("src/module.py")[1].split("\n")[0])

if __name__ == "__main__":
    unittest.main()
