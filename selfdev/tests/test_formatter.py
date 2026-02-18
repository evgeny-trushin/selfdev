import unittest
from selfdev.lib.formatter import PromptFormatter
from selfdev.lib.models import Prompt, Priority, Perspective, OrganismState

class TestPromptFormatter(unittest.TestCase):
    def setUp(self):
        # Disable colors to make assertions easier
        self.formatter = PromptFormatter(use_colors=False)

    def test_format_prompt(self):
        prompt = Prompt(
            perspective=Perspective.USER,
            priority=Priority.HIGH,
            title="Test Title",
            description="Test Description",
            file_path="test_file.py",
            line_number=10,
            metric_current=5.0,
            metric_target=10.0,
            acceptance_criteria=["Criterion 1", "Criterion 2"]
        )
        output = self.formatter.format_prompt(prompt)

        # Check that key information is present in the output
        self.assertIn("[HIGH] Test Title", output)
        self.assertIn("Test Description", output)
        self.assertIn("Location: test_file.py:10", output)
        self.assertIn("Current: 5.0 -> Target: 10.0", output)
        self.assertIn("Acceptance Criteria:", output)
        self.assertIn("- Criterion 1", output)
        self.assertIn("- Criterion 2", output)

    def test_format_header(self):
        state = OrganismState(generation=2)
        # 0.85 fitness
        output = self.formatter.format_header(Perspective.TEST, 0.85, state)

        self.assertIn("PERSPECTIVE: TEST", output)
        self.assertIn("Generation: 2", output)
        self.assertIn("Stage: embryonic", output)  # Based on generation 2
        self.assertIn("Fitness: 85.00%", output)

    def test_format_summary(self):
        state = OrganismState(fitness_scores={"user": 0.5, "test": 0.5})
        prompts = [
            Prompt(Perspective.USER, Priority.CRITICAL, "P1", "D1"),
            Prompt(Perspective.TEST, Priority.LOW, "P2", "D2")
        ]

        output = self.formatter.format_summary(state, prompts)

        self.assertIn("SUMMARY", output)
        self.assertIn("Total Prompts: 2", output)
        self.assertIn("CRITICAL: 1", output)
        self.assertIn("LOW: 1", output)
        self.assertIn("Overall Fitness: 50.00%", output)

if __name__ == '__main__':
    unittest.main()
