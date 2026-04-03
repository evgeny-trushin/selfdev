"""Tests for INCREMENT 0013: Acceptance Criteria.

Validates that the system is "fit":
1. All perspectives can run independently
2. Prompts generated are actionable
3. State persists between runs
4. Fitness scores are calculated correctly
5. No unhandled exceptions during normal operation
"""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models import OrganismState, Perspective, Priority, Prompt
from organism import SelfDevelopmentOrganism
from analyzers import GitAnalyzer


def _mock_git_analyzer():
    mock = MagicMock(spec=GitAnalyzer)
    mock.get_current_hash.return_value = "abc12345"
    mock.get_recent_commits.return_value = [
        {"hash": "abc12345", "message": "test", "date": "2026-01-01"}
    ]
    mock.get_uncommitted_changes.return_value = []
    mock.get_branch.return_value = "main"
    mock.get_changed_files_in_last_commit.return_value = []
    return mock


def _make_organism(tmp_dir):
    organism = SelfDevelopmentOrganism(root_dir=Path(tmp_dir))
    mock_git = _mock_git_analyzer()
    for p in organism.perspectives.values():
        p.git_analyzer = mock_git
    return organism


class TestPerspectivesRunIndependently(unittest.TestCase):
    """AC-1: Each perspective runs independently without errors."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_user_perspective_independent(self):
        organism = _make_organism(self.tmp_dir)
        prompts = organism.run_perspective(Perspective.USER)
        self.assertIsInstance(prompts, list)

    def test_test_perspective_independent(self):
        organism = _make_organism(self.tmp_dir)
        prompts = organism.run_perspective(Perspective.TEST)
        self.assertIsInstance(prompts, list)

    def test_system_perspective_independent(self):
        organism = _make_organism(self.tmp_dir)
        prompts = organism.run_perspective(Perspective.SYSTEM)
        self.assertIsInstance(prompts, list)

    def test_analytics_perspective_independent(self):
        organism = _make_organism(self.tmp_dir)
        prompts = organism.run_perspective(Perspective.ANALYTICS)
        self.assertIsInstance(prompts, list)

    def test_debug_perspective_independent(self):
        organism = _make_organism(self.tmp_dir)
        prompts = organism.run_perspective(Perspective.DEBUG)
        self.assertIsInstance(prompts, list)


class TestPromptsAreActionable(unittest.TestCase):
    """AC-2: Prompts include title, description, priority, and acceptance_criteria."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_prompt_fields_present(self):
        organism = _make_organism(self.tmp_dir)
        all_prompts = organism.run_all_perspectives()
        for prompt in all_prompts:
            self.assertIsInstance(prompt, Prompt)
            self.assertTrue(prompt.title, f"Prompt missing title: {prompt}")
            self.assertTrue(prompt.description, f"Prompt missing description: {prompt}")
            self.assertIsInstance(prompt.priority, Priority)
            self.assertIsInstance(prompt.acceptance_criteria, list)

    def test_prompt_has_perspective(self):
        organism = _make_organism(self.tmp_dir)
        all_prompts = organism.run_all_perspectives()
        for prompt in all_prompts:
            self.assertIsInstance(prompt.perspective, Perspective)


class TestStatePersistence(unittest.TestCase):
    """AC-3: organism_state.json persists generation, fitness_scores, and fitness_history."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.state_path = Path(self.tmp_dir) / "organism_state.json"

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_state_save_and_load(self):
        state = OrganismState(generation=5)
        state.fitness_scores = {"user": 0.8, "test": 0.6}
        state.fitness_history = [{"generation": 0, "increment": 1}]
        state.save(self.state_path)

        loaded = OrganismState.load(self.state_path)
        self.assertEqual(loaded.generation, 5)
        self.assertEqual(loaded.fitness_scores["user"], 0.8)
        self.assertEqual(loaded.fitness_scores["test"], 0.6)
        self.assertEqual(len(loaded.fitness_history), 1)

    def test_state_persists_between_organism_runs(self):
        organism = _make_organism(self.tmp_dir)
        organism.run_all_perspectives()
        organism.state.save(Path(self.tmp_dir) / "organism_state.json")

        organism2 = SelfDevelopmentOrganism(root_dir=Path(self.tmp_dir))
        self.assertEqual(organism2.state.fitness_scores, organism.state.fitness_scores)

    def test_state_file_valid_json(self):
        state = OrganismState(generation=3)
        state.fitness_scores = {"system": 0.9}
        state.save(self.state_path)

        with open(self.state_path) as f:
            data = json.load(f)
        self.assertIn("generation", data)
        self.assertIn("fitness_scores", data)
        self.assertIn("fitness_history", data)


class TestFitnessScoresCorrect(unittest.TestCase):
    """AC-4: Fitness scores are floats between 0.0 and 1.0."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_fitness_scores_are_floats(self):
        organism = _make_organism(self.tmp_dir)
        organism.run_all_perspectives()
        for name, score in organism.state.fitness_scores.items():
            self.assertIsInstance(score, float, f"{name} score is not a float")

    def test_fitness_scores_in_range(self):
        organism = _make_organism(self.tmp_dir)
        organism.run_all_perspectives()
        for name, score in organism.state.fitness_scores.items():
            self.assertGreaterEqual(score, 0.0, f"{name} score below 0.0")
            self.assertLessEqual(score, 1.0, f"{name} score above 1.0")

    def test_all_perspectives_produce_scores(self):
        organism = _make_organism(self.tmp_dir)
        organism.run_all_perspectives()
        for perspective in Perspective:
            self.assertIn(
                perspective.value, organism.state.fitness_scores,
                f"Missing fitness score for {perspective.value}"
            )


class TestNoUnhandledExceptions(unittest.TestCase):
    """AC-5: No unhandled exceptions when running on an empty directory."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_empty_dir_no_exceptions(self):
        organism = _make_organism(self.tmp_dir)
        organism.run_all_perspectives()

    def test_each_perspective_empty_dir_no_exceptions(self):
        for perspective in Perspective:
            with self.subTest(perspective=perspective.value):
                organism = _make_organism(self.tmp_dir)
                prompts = organism.run_perspective(perspective)
                self.assertIsInstance(prompts, list)

    def test_state_load_missing_file(self):
        state = OrganismState.load(Path(self.tmp_dir) / "nonexistent.json")
        self.assertIsInstance(state, OrganismState)

    def test_state_load_corrupt_file(self):
        corrupt_path = Path(self.tmp_dir) / "bad_state.json"
        corrupt_path.write_text("not valid json {{{")
        state = OrganismState.load(corrupt_path)
        self.assertIsInstance(state, OrganismState)


if __name__ == "__main__":
    unittest.main()
