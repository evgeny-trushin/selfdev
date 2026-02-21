"""
Code and Git analyzers for the Self-Development Organism system.
"""

import ast
from pathlib import Path
from typing import Dict, List, Optional

from models import (
    FileAnalysis,
    ANALYZABLE_DIRS,
    TEST_DIRS,
    COMPLEXITY_THRESHOLD,
    MAX_FILE_LINES,
)


class CodeAnalyzer:
    """Analyzes code structure and metrics"""

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.file_analyses: Dict[str, FileAnalysis] = {}

    def analyze_file(self, file_path: Path) -> Optional[FileAnalysis]:
        """Analyze a single Python file"""
        if not file_path.exists() or not file_path.suffix == ".py":
            return None

        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content)
        except (SyntaxError, UnicodeDecodeError):
            return FileAnalysis(
                path=str(file_path.relative_to(self.root_dir)),
                lines=0,
                functions=0,
                classes=0,
                imports=0,
                complexity=0,
                has_tests=False,
                issues=["Syntax error in file"]
            )

        lines = len(content.splitlines())
        functions = sum(1 for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))
        classes = sum(1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
        imports = sum(1 for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom)))

        complexity = self._calculate_complexity(tree)

        rel_path = str(file_path.relative_to(self.root_dir))
        has_tests = any(td in rel_path for td in TEST_DIRS) or "test" in file_path.name.lower()

        issues = []
        if lines > MAX_FILE_LINES:
            issues.append(f"File too long: {lines} lines (max {MAX_FILE_LINES})")
        if complexity > COMPLEXITY_THRESHOLD:
            issues.append(f"High complexity: {complexity:.1f} (max {COMPLEXITY_THRESHOLD})")

        return FileAnalysis(
            path=rel_path,
            lines=lines,
            functions=functions,
            classes=classes,
            imports=imports,
            complexity=complexity,
            has_tests=has_tests,
            issues=issues
        )

    def _calculate_complexity(self, tree: ast.AST) -> float:
        """Calculate simplified cyclomatic complexity"""
        complexity = 1
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        return complexity

    def analyze_directory(self, dir_path: Path) -> Dict[str, FileAnalysis]:
        """Analyze all Python files in a directory"""
        results = {}
        if not dir_path.exists():
            return results

        for file_path in dir_path.rglob("*.py"):
            if "__pycache__" in str(file_path):
                continue
            analysis = self.analyze_file(file_path)
            if analysis:
                results[analysis.path] = analysis

        return results

    def get_all_analyses(self) -> Dict[str, FileAnalysis]:
        """Analyze all relevant directories"""
        all_results = {}

        for dir_name in ANALYZABLE_DIRS + TEST_DIRS:
            dir_path = self.root_dir / dir_name
            results = self.analyze_directory(dir_path)
            all_results.update(results)

        for file_path in self.root_dir.glob("*.py"):
            analysis = self.analyze_file(file_path)
            if analysis:
                all_results[analysis.path] = analysis

        self.file_analyses = all_results
        return all_results
