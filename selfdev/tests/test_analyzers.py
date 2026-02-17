"""Tests for CodeAnalyzer and GitAnalyzer."""

import unittest
import tempfile
import textwrap
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add selfdev root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.analyzers import CodeAnalyzer, GitAnalyzer

class TestCodeAnalyzer(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.analyzer = CodeAnalyzer(Path(self.tmp_dir))

    def tearDown(self):
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


class TestGitAnalyzer(unittest.TestCase):
    """Tests for GitAnalyzer."""

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
            branch = analyzer.get_branch()
            self.assertIn(branch, ["", "unknown"])

    @patch("lib.analyzers.subprocess.run")
    def test_get_current_hash_mock(self, mock_run):
        mock_run.return_value = MagicMock(stdout="abcdef1234567890\n")
        analyzer = GitAnalyzer(Path("/fake"))
        h = analyzer.get_current_hash()
        self.assertEqual(h, "abcdef12")

    @patch("lib.analyzers.subprocess.run")
    def test_get_recent_commits_mock(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout="abc12345|fix bug|2026-01-01\ndef67890|add feature|2026-01-02"
        )
        analyzer = GitAnalyzer(Path("/fake"))
        commits = analyzer.get_recent_commits(2)
        self.assertEqual(len(commits), 2)
        self.assertEqual(commits[0]["message"], "fix bug")

    @patch("lib.analyzers.subprocess.run")
    def test_get_uncommitted_mock(self, mock_run):
        mock_run.return_value = MagicMock(stdout=" M file.py\n?? new.py\n")
        analyzer = GitAnalyzer(Path("/fake"))
        changes = analyzer.get_uncommitted_changes()
        self.assertEqual(len(changes), 2)

    @patch("lib.analyzers.subprocess.run")
    def test_get_branch_mock(self, mock_run):
        mock_run.return_value = MagicMock(stdout="feature/test\n")
        analyzer = GitAnalyzer(Path("/fake"))
        self.assertEqual(analyzer.get_branch(), "feature/test")

    @patch("lib.analyzers.subprocess.run")
    def test_exception_handling(self, mock_run):
        mock_run.side_effect = Exception("git not found")
        analyzer = GitAnalyzer(Path("/fake"))
        self.assertEqual(analyzer.get_current_hash(), "")
        self.assertEqual(analyzer.get_recent_commits(), [])
        self.assertEqual(analyzer.get_uncommitted_changes(), [])
        self.assertEqual(analyzer.get_branch(), "unknown")

if __name__ == "__main__":
    unittest.main()
