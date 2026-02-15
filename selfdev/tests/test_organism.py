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

class TestCodeAnalyzer(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.analyzer = CodeAnalyzer(Path(self.tmp_dir))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp_dir)

    def _write_file(self, name, content):
        path = Path(self.tmp_dir) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(content))
        return path

    def test_analyze_simple_file(self):
        path = self._write_file("simple.py", """\
            def hello():
                return "world"
        """)
        result = self.analyzer.analyze_file(path)
        self.assertIsNotNone(result)
        self.assertEqual(result.functions, 1)
        self.assertEqual(result.classes, 0)
        self.assertGreater(result.lines, 0)

    def test_analyze_file_with_class(self):
        path = self._write_file("with_class.py", """\
            class MyClass:
                def method_a(self):
                    pass
                def method_b(self):
                    pass
        """)
        result = self.analyzer.analyze_file(path)
        self.assertEqual(result.classes, 1)
        self.assertEqual(result.functions, 2)

    def test_analyze_file_complexity(self):
        path = self._write_file("complex.py", """\
            def process(x):
                if x > 0:
                    if x > 10:
                        return "big"
                    else:
                        return "small"
                elif x == 0:
                    return "zero"
                else:
                    for i in range(abs(x)):
                        if i % 2 == 0:
                            print(i)
                return None
        """)
        result = self.analyzer.analyze_file(path)
        self.assertGreater(result.complexity, 1)

    def test_analyze_nonexistent_file(self):
        path = Path(self.tmp_dir) / "nonexistent.py"
        result = self.analyzer.analyze_file(path)
        self.assertIsNone(result)

    def test_analyze_non_python_file(self):
        path = self._write_file("readme.md", "# Hello")
        result = self.analyzer.analyze_file(path)
        self.assertIsNone(result)

    def test_analyze_syntax_error_file(self):
        path = self._write_file("broken.py", """\
            def broken(
                # missing closing paren
        """)
        result = self.analyzer.analyze_file(path)
        self.assertIsNotNone(result)
        self.assertIn("Syntax error in file", result.issues)

    def test_analyze_directory(self):
        src = Path(self.tmp_dir) / "src"
        src.mkdir()
        (src / "a.py").write_text("def a(): pass")
        (src / "b.py").write_text("def b(): pass")
        results = self.analyzer.analyze_directory(src)
        self.assertEqual(len(results), 2)

    def test_analyze_directory_nonexistent(self):
        results = self.analyzer.analyze_directory(Path(self.tmp_dir) / "nope")
        self.assertEqual(len(results), 0)

    def test_analyze_file_long_file_issue(self):
        lines = ["x = 1"] * 350
        path = self._write_file("long.py", "\n".join(lines))
        result = self.analyzer.analyze_file(path)
        self.assertTrue(any("too long" in issue for issue in result.issues))

    def test_has_tests_detection(self):
        test_dir = Path(self.tmp_dir) / "tests"
        test_dir.mkdir()
        path = test_dir / "test_something.py"
        path.write_text("def test_it(): pass")
        result = self.analyzer.analyze_file(path)
        self.assertTrue(result.has_tests)

    def test_get_all_analyses(self):
        src = Path(self.tmp_dir) / "src"
        src.mkdir()
        (src / "module.py").write_text("def func(): pass")
        results = self.analyzer.get_all_analyses()
        self.assertGreaterEqual(len(results), 1)

    def test_complexity_calculation(self):
        import ast
        code = "if True:\n    for x in y:\n        while z:\n            pass"
        tree = ast.parse(code)
        complexity = self.analyzer._calculate_complexity(tree)
        # 1 (base) + 1 (if) + 1 (for) + 1 (while) = 4
        self.assertEqual(complexity, 4)

    def test_imports_counted(self):
        path = self._write_file("imports.py", """\
            import os
            import sys
            from pathlib import Path
        """)
        result = self.analyzer.analyze_file(path)
        self.assertEqual(result.imports, 3)

    def test_pycache_excluded(self):
        cache_dir = Path(self.tmp_dir) / "src" / "__pycache__"
        cache_dir.mkdir(parents=True)
        (cache_dir / "module.cpython-311.py").write_text("x = 1")
        src = Path(self.tmp_dir) / "src"
        results = self.analyzer.analyze_directory(src)
        self.assertEqual(len(results), 0)


# ==================== GitAnalyzer Tests (mocked) ====================

class TestGitAnalyzer(unittest.TestCase):
    """Tests for GitAnalyzer using the actual project repo (read-only)."""

    def test_get_current_hash_real_repo(self):
        repo_dir = Path(__file__).resolve().parent.parent
        analyzer = GitAnalyzer(repo_dir)
        h = analyzer.get_current_hash()
        self.assertTrue(len(h) > 0)
        self.assertEqual(len(h), 8)

    def test_get_recent_commits_real_repo(self):
        repo_dir = Path(__file__).resolve().parent.parent
        analyzer = GitAnalyzer(repo_dir)
        commits = analyzer.get_recent_commits(5)
        self.assertGreaterEqual(len(commits), 1)

    def test_get_branch_real_repo(self):
        repo_dir = Path(__file__).resolve().parent.parent
        analyzer = GitAnalyzer(repo_dir)
        branch = analyzer.get_branch()
        self.assertNotEqual(branch, "unknown")

    def test_git_analyzer_no_repo(self):
        with tempfile.TemporaryDirectory() as d:
            analyzer = GitAnalyzer(Path(d))
            self.assertEqual(analyzer.get_current_hash(), "")
            self.assertEqual(analyzer.get_recent_commits(), [])
            # get_branch returns empty string when subprocess succeeds but stdout is empty
            branch = analyzer.get_branch()
            self.assertIn(branch, ["", "unknown"])

    @patch("organism.subprocess.run")
    def test_get_current_hash_mock(self, mock_run):
        mock_run.return_value = MagicMock(stdout="abcdef1234567890\n")
        analyzer = GitAnalyzer(Path("/fake"))
        h = analyzer.get_current_hash()
        self.assertEqual(h, "abcdef12")

    @patch("organism.subprocess.run")
    def test_get_recent_commits_mock(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout="abc12345|fix bug|2026-01-01\ndef67890|add feature|2026-01-02"
        )
        analyzer = GitAnalyzer(Path("/fake"))
        commits = analyzer.get_recent_commits(2)
        self.assertEqual(len(commits), 2)
        self.assertEqual(commits[0]["message"], "fix bug")

    @patch("organism.subprocess.run")
    def test_get_uncommitted_mock(self, mock_run):
        mock_run.return_value = MagicMock(stdout=" M file.py\n?? new.py\n")
        analyzer = GitAnalyzer(Path("/fake"))
        changes = analyzer.get_uncommitted_changes()
        self.assertEqual(len(changes), 2)

    @patch("organism.subprocess.run")
    def test_get_branch_mock(self, mock_run):
        mock_run.return_value = MagicMock(stdout="feature/test\n")
        analyzer = GitAnalyzer(Path("/fake"))
        self.assertEqual(analyzer.get_branch(), "feature/test")

    @patch("organism.subprocess.run")
    def test_exception_handling(self, mock_run):
        mock_run.side_effect = Exception("git not found")
        analyzer = GitAnalyzer(Path("/fake"))
        self.assertEqual(analyzer.get_current_hash(), "")
        self.assertEqual(analyzer.get_recent_commits(), [])
        self.assertEqual(analyzer.get_uncommitted_changes(), [])
        self.assertEqual(analyzer.get_branch(), "unknown")


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
