"""Tests for the Self-Development Organism system."""

import json
import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from organism import (
    DevelopmentStage,
    Perspective,
    Priority,
    Prompt,
    FileAnalysis,
    OrganismState,
    CodeAnalyzer,
    GitAnalyzer,
    UserPerspective,
    TestPerspective,
    SystemPerspective,
    AnalyticsPerspective,
    DebugPerspective,
    PromptFormatter,
    SelfDevelopmentOrganism,
)


# ==================== Helper ====================

def _mock_git_analyzer():
    """Create a mock GitAnalyzer that doesn't require a real git repo."""
    mock = MagicMock(spec=GitAnalyzer)
    mock.get_current_hash.return_value = "abc12345"
    mock.get_recent_commits.return_value = [
        {"hash": "abc12345", "message": "Initial commit", "date": "2026-01-01"}
    ]
    mock.get_uncommitted_changes.return_value = []
    mock.get_branch.return_value = "main"
    return mock


# ==================== Enum Tests ====================

class TestEnums(unittest.TestCase):

    def test_development_stages(self):
        self.assertEqual(DevelopmentStage.EMBRYONIC.value, "embryonic")
        self.assertEqual(DevelopmentStage.GROWTH.value, "growth")
        self.assertEqual(DevelopmentStage.MATURATION.value, "maturation")
        self.assertEqual(DevelopmentStage.HOMEOSTASIS.value, "homeostasis")

    def test_perspectives(self):
        self.assertEqual(len(Perspective), 5)
        values = [p.value for p in Perspective]
        self.assertIn("user", values)
        self.assertIn("test", values)
        self.assertIn("system", values)
        self.assertIn("analytics", values)
        self.assertIn("debug", values)

    def test_priority_ordering(self):
        self.assertLess(Priority.CRITICAL.value, Priority.HIGH.value)
        self.assertLess(Priority.HIGH.value, Priority.MEDIUM.value)
        self.assertLess(Priority.MEDIUM.value, Priority.LOW.value)
        self.assertLess(Priority.LOW.value, Priority.INFO.value)


# ==================== Dataclass Tests ====================

class TestPromptDataclass(unittest.TestCase):

    def test_prompt_creation_minimal(self):
        p = Prompt(
            perspective=Perspective.USER,
            priority=Priority.HIGH,
            title="Test prompt",
            description="A test description",
        )
        self.assertEqual(p.perspective, Perspective.USER)
        self.assertEqual(p.priority, Priority.HIGH)
        self.assertIsNone(p.file_path)
        self.assertIsNone(p.line_number)
        self.assertEqual(p.acceptance_criteria, [])
        self.assertEqual(p.tags, [])

    def test_prompt_creation_full(self):
        p = Prompt(
            perspective=Perspective.SYSTEM,
            priority=Priority.CRITICAL,
            title="Refactor module",
            description="Module too complex",
            file_path="src/module.py",
            line_number=42,
            metric_current=15.0,
            metric_target=10.0,
            acceptance_criteria=["Reduce complexity"],
            tags=["refactoring"],
        )
        self.assertEqual(p.file_path, "src/module.py")
        self.assertEqual(p.line_number, 42)
        self.assertEqual(p.metric_current, 15.0)
        self.assertIn("Reduce complexity", p.acceptance_criteria)


class TestFileAnalysis(unittest.TestCase):

    def test_file_analysis_defaults(self):
        fa = FileAnalysis(
            path="test.py",
            lines=100,
            functions=5,
            classes=1,
            imports=3,
            complexity=5.0,
            has_tests=False,
        )
        self.assertEqual(fa.issues, [])
        self.assertFalse(fa.has_tests)


# ==================== OrganismState Tests ====================

class TestOrganismState(unittest.TestCase):

    def test_default_state(self):
        state = OrganismState()
        self.assertEqual(state.generation, 0)
        self.assertEqual(state.development_stage, "embryonic")
        self.assertEqual(state.fitness_scores, {})
        self.assertEqual(state.fitness_history, [])

    def test_get_stage_embryonic(self):
        state = OrganismState(generation=0)
        self.assertEqual(state.get_stage(), DevelopmentStage.EMBRYONIC)
        state.generation = 3
        self.assertEqual(state.get_stage(), DevelopmentStage.EMBRYONIC)

    def test_get_stage_growth(self):
        state = OrganismState(generation=4)
        self.assertEqual(state.get_stage(), DevelopmentStage.GROWTH)
        state.generation = 10
        self.assertEqual(state.get_stage(), DevelopmentStage.GROWTH)

    def test_get_stage_maturation(self):
        state = OrganismState(generation=11)
        self.assertEqual(state.get_stage(), DevelopmentStage.MATURATION)
        state.generation = 20
        self.assertEqual(state.get_stage(), DevelopmentStage.MATURATION)

    def test_get_stage_homeostasis(self):
        state = OrganismState(generation=21)
        self.assertEqual(state.get_stage(), DevelopmentStage.HOMEOSTASIS)
        state.generation = 100
        self.assertEqual(state.get_stage(), DevelopmentStage.HOMEOSTASIS)

    def test_save_and_load(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = Path(f.name)
        try:
            state = OrganismState(generation=5)
            state.fitness_scores = {"user": 0.8, "test": 0.6}
            state.save(path)

            loaded = OrganismState.load(path)
            self.assertEqual(loaded.generation, 5)
            self.assertAlmostEqual(loaded.fitness_scores["user"], 0.8)
            self.assertAlmostEqual(loaded.fitness_scores["test"], 0.6)
            self.assertNotEqual(loaded.last_updated, "")
        finally:
            path.unlink()

    def test_load_missing_file(self):
        path = Path("/tmp/nonexistent_state_test.json")
        state = OrganismState.load(path)
        self.assertEqual(state.generation, 0)
        self.assertNotEqual(state.created_at, "")

    def test_load_corrupted_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("not valid json{{{")
            path = Path(f.name)
        try:
            state = OrganismState.load(path)
            self.assertEqual(state.generation, 0)
        finally:
            path.unlink()


# ==================== CodeAnalyzer Tests ====================
# Moved to test_analyzers.py


# ==================== GitAnalyzer Tests (mocked) ====================
# Moved to test_analyzers.py


# ==================== Perspective Tests ====================

class TestUserPerspective(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.state = OrganismState()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp_dir)

    def test_no_readme_critical_prompt(self):
        analyzer = UserPerspective(Path(self.tmp_dir), self.state)
        fitness, prompts = analyzer.analyze()
        critical = [p for p in prompts if p.priority == Priority.CRITICAL]
        self.assertGreater(len(critical), 0)
        self.assertIn("README", critical[0].title)

    def test_with_readme(self):
        (Path(self.tmp_dir) / "README.md").write_text("# Project\n" + "x" * 5000)
        analyzer = UserPerspective(Path(self.tmp_dir), self.state)
        fitness, prompts = analyzer.analyze()
        critical = [p for p in prompts if p.priority == Priority.CRITICAL]
        self.assertEqual(len(critical), 0)
        self.assertGreater(fitness, 0.5)

    def test_short_readme_high_prompt(self):
        (Path(self.tmp_dir) / "README.md").write_text("# Hi")
        analyzer = UserPerspective(Path(self.tmp_dir), self.state)
        fitness, prompts = analyzer.analyze()
        high = [p for p in prompts if p.priority == Priority.HIGH]
        self.assertGreater(len(high), 0)

    def test_changelog_exists(self):
        (Path(self.tmp_dir) / "README.md").write_text("# Project\n" + "x" * 5000)
        (Path(self.tmp_dir) / "CHANGELOG.md").write_text("# Changelog")
        analyzer = UserPerspective(Path(self.tmp_dir), self.state)
        fitness, prompts = analyzer.analyze()
        low = [p for p in prompts if p.priority == Priority.LOW]
        self.assertEqual(len(low), 0)

    def test_no_changelog_low_prompt(self):
        (Path(self.tmp_dir) / "README.md").write_text("# Project\n" + "x" * 5000)
        analyzer = UserPerspective(Path(self.tmp_dir), self.state)
        fitness, prompts = analyzer.analyze()
        low = [p for p in prompts if p.priority == Priority.LOW]
        self.assertGreater(len(low), 0)

    def test_package_json_with_description(self):
        (Path(self.tmp_dir) / "README.md").write_text("# Project\n" + "x" * 5000)
        (Path(self.tmp_dir) / "package.json").write_text(
            json.dumps({"name": "test", "description": "A test project"})
        )
        analyzer = UserPerspective(Path(self.tmp_dir), self.state)
        fitness, prompts = analyzer.analyze()
        self.assertGreater(fitness, 0.5)

    def test_package_json_without_description(self):
        (Path(self.tmp_dir) / "README.md").write_text("# Project\n" + "x" * 5000)
        (Path(self.tmp_dir) / "package.json").write_text(
            json.dumps({"name": "test"})
        )
        analyzer = UserPerspective(Path(self.tmp_dir), self.state)
        fitness, prompts = analyzer.analyze()
        medium = [p for p in prompts if p.priority == Priority.MEDIUM]
        self.assertGreater(len(medium), 0)


class TestTestPerspective(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.state = OrganismState()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp_dir)

    def test_no_test_dir_critical(self):
        analyzer = TestPerspective(Path(self.tmp_dir), self.state)
        fitness, prompts = analyzer.analyze()
        self.assertEqual(fitness, 0.0)
        critical = [p for p in prompts if p.priority == Priority.CRITICAL]
        self.assertGreater(len(critical), 0)

    def test_with_test_dir(self):
        (Path(self.tmp_dir) / "tests").mkdir()
        (Path(self.tmp_dir) / "tests" / "test_a.py").write_text("def test_a(): pass")
        analyzer = TestPerspective(Path(self.tmp_dir), self.state)
        fitness, prompts = analyzer.analyze()
        self.assertGreater(fitness, 0.0)

    def test_with_source_and_test_files(self):
        src = Path(self.tmp_dir) / "src"
        src.mkdir()
        (src / "module.py").write_text("def func(): pass")
        tests = Path(self.tmp_dir) / "tests"
        tests.mkdir()
        (tests / "test_module.py").write_text("def test_func(): pass")
        analyzer = TestPerspective(Path(self.tmp_dir), self.state)
        fitness, prompts = analyzer.analyze()
        self.assertGreater(fitness, 0.0)

    def test_low_coverage_prompt(self):
        src = Path(self.tmp_dir) / "src"
        src.mkdir()
        for i in range(5):
            (src / f"module_{i}.py").write_text(f"def func_{i}(): pass")
        tests = Path(self.tmp_dir) / "tests"
        tests.mkdir()
        (tests / "test_one.py").write_text("def test_one(): pass")
        analyzer = TestPerspective(Path(self.tmp_dir), self.state)
        fitness, prompts = analyzer.analyze()
        high = [p for p in prompts if p.priority == Priority.HIGH]
        self.assertGreater(len(high), 0)


class TestSystemPerspective(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.state = OrganismState()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp_dir)

    def test_no_files_info_prompt(self):
        analyzer = SystemPerspective(Path(self.tmp_dir), self.state)
        fitness, prompts = analyzer.analyze()
        self.assertEqual(fitness, 0.5)
        self.assertEqual(len(prompts), 1)
        self.assertEqual(prompts[0].priority, Priority.INFO)

    def test_with_source_files(self):
        src = Path(self.tmp_dir) / "src"
        src.mkdir()
        (src / "module.py").write_text("def func(): pass")
        analyzer = SystemPerspective(Path(self.tmp_dir), self.state)
        fitness, prompts = analyzer.analyze()
        self.assertGreater(fitness, 0.0)

    def test_long_file_refactor_prompt(self):
        src = Path(self.tmp_dir) / "src"
        src.mkdir()
        (src / "big.py").write_text("\n".join(["x = 1"] * 400))
        analyzer = SystemPerspective(Path(self.tmp_dir), self.state)
        fitness, prompts = analyzer.analyze()
        refactor = [p for p in prompts if "Refactor" in p.title]
        self.assertGreater(len(refactor), 0)

    def test_high_complexity_prompt(self):
        src = Path(self.tmp_dir) / "src"
        src.mkdir()
        # Generate a file with high complexity
        lines = ["def func():"]
        for i in range(15):
            lines.append(f"    if x == {i}:")
            lines.append(f"        return {i}")
        (src / "complex.py").write_text("\n".join(lines))
        analyzer = SystemPerspective(Path(self.tmp_dir), self.state)
        fitness, prompts = analyzer.analyze()
        complexity_prompts = [p for p in prompts if "complexity" in p.title.lower()]
        self.assertGreater(len(complexity_prompts), 0)


class TestAnalyticsPerspective(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp_dir)

    def test_insufficient_history(self):
        state = OrganismState()
        analyzer = AnalyticsPerspective(Path(self.tmp_dir), state)
        analyzer.git_analyzer = _mock_git_analyzer()
        fitness, prompts = analyzer.analyze()
        self.assertEqual(fitness, 0.5)
        self.assertEqual(prompts[0].priority, Priority.INFO)

    def test_with_history_declining_trend(self):
        state = OrganismState()
        state.fitness_history = [
            {"overall": 0.8, "generation": i} for i in range(6)
        ] + [
            {"overall": 0.4, "generation": i} for i in range(6, 11)
        ]
        analyzer = AnalyticsPerspective(Path(self.tmp_dir), state)
        analyzer.git_analyzer = _mock_git_analyzer()
        fitness, prompts = analyzer.analyze()
        declining = [p for p in prompts if "declining" in p.title.lower()]
        self.assertGreater(len(declining), 0)

    def test_with_history_improving_trend(self):
        state = OrganismState()
        state.fitness_history = [
            {"overall": 0.3, "generation": i} for i in range(6)
        ] + [
            {"overall": 0.8, "generation": i} for i in range(6, 11)
        ]
        analyzer = AnalyticsPerspective(Path(self.tmp_dir), state)
        analyzer.git_analyzer = _mock_git_analyzer()
        fitness, prompts = analyzer.analyze()
        positive = [p for p in prompts if "positive" in p.title.lower() or "Positive" in p.title]
        self.assertGreater(len(positive), 0)

    def test_high_fix_rate_prompt(self):
        state = OrganismState()
        state.fitness_history = [
            {"overall": 0.5, "generation": i} for i in range(3)
        ]
        mock_git = _mock_git_analyzer()
        mock_git.get_recent_commits.return_value = [
            {"hash": f"abc{i}", "message": f"fix bug {i}", "date": "2026-01-01"}
            for i in range(8)
        ] + [
            {"hash": "def0", "message": "add feature", "date": "2026-01-01"},
            {"hash": "def1", "message": "update docs", "date": "2026-01-01"},
        ]
        analyzer = AnalyticsPerspective(Path(self.tmp_dir), state)
        analyzer.git_analyzer = mock_git
        fitness, prompts = analyzer.analyze()
        fix_rate = [p for p in prompts if "fix rate" in p.title.lower() or "bug fix" in p.title.lower()]
        self.assertGreater(len(fix_rate), 0)


class TestDebugPerspective(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.state = OrganismState()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp_dir)

    def test_clean_debug(self):
        analyzer = DebugPerspective(Path(self.tmp_dir), self.state)
        analyzer.git_analyzer = _mock_git_analyzer()
        fitness, prompts = analyzer.analyze()
        self.assertGreater(fitness, 0.5)

    def test_uncommitted_changes(self):
        mock_git = _mock_git_analyzer()
        mock_git.get_uncommitted_changes.return_value = [" M file.py", "?? new.py"]
        analyzer = DebugPerspective(Path(self.tmp_dir), self.state)
        analyzer.git_analyzer = mock_git
        fitness, prompts = analyzer.analyze()
        uncommitted = [p for p in prompts if "uncommitted" in p.title.lower() or "Uncommitted" in p.title]
        self.assertGreater(len(uncommitted), 0)

    def test_todo_detection(self):
        src = Path(self.tmp_dir) / "src"
        src.mkdir()
        (src / "module.py").write_text("# TODO: Fix this\ndef func(): pass\n# FIXME: broken")
        analyzer = DebugPerspective(Path(self.tmp_dir), self.state)
        analyzer.git_analyzer = _mock_git_analyzer()
        fitness, prompts = analyzer.analyze()
        todo_prompts = [p for p in prompts if any(t in p.tags for t in ["todo", "fixme"])]
        self.assertGreater(len(todo_prompts), 0)

    def test_fitness_decreases_with_issues(self):
        src = Path(self.tmp_dir) / "src"
        src.mkdir()
        todos = "\n".join([f"# TODO: item {i}" for i in range(15)])
        (src / "module.py").write_text(todos)
        analyzer = DebugPerspective(Path(self.tmp_dir), self.state)
        analyzer.git_analyzer = _mock_git_analyzer()
        fitness, prompts = analyzer.analyze()
        self.assertLess(fitness, 0.5)


# ==================== PromptFormatter Tests ====================
# Moved to test_formatter.py


# ==================== SelfDevelopmentOrganism Tests ====================

class TestSelfDevelopmentOrganism(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp_dir)

    def test_organism_initialization(self):
        organism = SelfDevelopmentOrganism(root_dir=Path(self.tmp_dir))
        self.assertEqual(len(organism.perspectives), 5)

    def test_run_single_perspective(self):
        organism = SelfDevelopmentOrganism(root_dir=Path(self.tmp_dir))
        organism.formatter.use_colors = False
        prompts = organism.run_perspective(Perspective.USER)
        self.assertIsInstance(prompts, list)

    def test_run_all_perspectives(self):
        organism = SelfDevelopmentOrganism(root_dir=Path(self.tmp_dir))
        organism.formatter.use_colors = False
        # Mock git analyzers for all perspectives
        mock_git = _mock_git_analyzer()
        for p in organism.perspectives.values():
            p.git_analyzer = mock_git
        all_prompts = organism.run_all_perspectives()
        self.assertIsInstance(all_prompts, list)
        self.assertIn("user", organism.state.fitness_scores)
        self.assertIn("test", organism.state.fitness_scores)

    def test_advance_generation(self):
        organism = SelfDevelopmentOrganism(root_dir=Path(self.tmp_dir))
        # Reset state to a clean baseline for this test
        organism.state = OrganismState()
        organism.state.fitness_scores = {"user": 0.5, "test": 0.3}
        # Mock git analyzer
        mock_git = _mock_git_analyzer()
        for p in organism.perspectives.values():
            p.git_analyzer = mock_git
        initial_gen = organism.state.generation
        organism.advance_generation()
        self.assertEqual(organism.state.generation, initial_gen + 1)
        self.assertEqual(len(organism.state.fitness_history), 1)

    def test_print_state(self):
        organism = SelfDevelopmentOrganism(root_dir=Path(self.tmp_dir))
        organism.state.fitness_scores = {"user": 0.7}
        # Should not raise
        organism.print_state()

    def test_perspectives_sorted_by_priority(self):
        organism = SelfDevelopmentOrganism(root_dir=Path(self.tmp_dir))
        organism.formatter.use_colors = False
        prompts = organism.run_perspective(Perspective.USER)
        if len(prompts) > 1:
            for i in range(len(prompts) - 1):
                self.assertLessEqual(prompts[i].priority.value, prompts[i + 1].priority.value)


# ==================== CLI Tests ====================

class TestCLI(unittest.TestCase):

    def test_self_flag(self):
        result = subprocess.run(
            [sys.executable, str(Path(__file__).resolve().parent.parent / "organism.py"),
             "--self", "--state", "--no-color"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("ORGANISM STATE", result.stdout)

    def test_help_flag(self):
        result = subprocess.run(
            [sys.executable, str(Path(__file__).resolve().parent.parent / "organism.py"),
             "--help"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("Self-Development System", result.stdout)

    def test_root_flag(self):
        with tempfile.TemporaryDirectory() as d:
            result = subprocess.run(
                [sys.executable, str(Path(__file__).resolve().parent.parent / "organism.py"),
                 "--root", d, "--state", "--no-color"],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0)

    def test_self_analysis_runs(self):
        result = subprocess.run(
            [sys.executable, str(Path(__file__).resolve().parent.parent / "organism.py"),
             "--self", "--user", "--no-color"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("USER", result.stdout)


if __name__ == "__main__":
    unittest.main()
