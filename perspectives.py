"""
Perspective analyzers for the Self-Development Organism system.
Includes the base class and code-quality perspectives (Test, System).
"""

from pathlib import Path
from typing import Dict, List, Tuple
from abc import ABC, abstractmethod

from models import (
    OrganismState,
    Perspective,
    Priority,
    Prompt,
    COMPLEXITY_THRESHOLD,
    COVERAGE_TARGET,
    MAX_FILE_LINES,
    TEST_DIRS,
    FileAnalysis,
)
from analyzers import CodeAnalyzer, GitAnalyzer


class PerspectiveAnalyzer(ABC):
    """Base class for perspective analyzers"""

    def __init__(self, root_dir: Path, state: OrganismState):
        self.root_dir = root_dir
        self.state = state
        self.code_analyzer = CodeAnalyzer(root_dir)
        self.git_analyzer = GitAnalyzer(root_dir)

    @abstractmethod
    def analyze(self) -> Tuple[Dict[str, float], List[Prompt]]:
        """Analyze from this perspective. Returns (fitness_metrics, prompts)"""
        pass

    @abstractmethod
    def get_perspective(self) -> Perspective:
        """Return the perspective type"""
        pass


class TestPerspective(PerspectiveAnalyzer):
    """Analyzes test coverage and quality"""

    def get_perspective(self) -> Perspective:
        return Perspective.TEST

    def analyze(self) -> Tuple[Dict[str, float], List[Prompt]]:
        prompts = []
        analyses = self.code_analyzer.get_all_analyses()

        source_files = [a for a in analyses.values() if not a.has_tests]
        test_files = [a for a in analyses.values() if a.has_tests]

        # Look for test directories at root level AND inside sub-directories
        test_dir_found = len(test_files) > 0

        if not test_dir_found:
            prompts.append(Prompt(
                perspective=Perspective.TEST,
                priority=Priority.CRITICAL,
                title="Create test directory",
                description="No test directory found. Tests are essential for code quality.",
                acceptance_criteria=[
                    "Create tests/ directory",
                    "Add at least one test file",
                    "Configure test runner"
                ],
                reason="No test files detected in the project"
            ))
            return {
                "code_coverage": 0.0,
                "mutation_score": 0.0,
                "test_pass_rate": 0.0,
                "data_integrity_validation": 0.0
            }, prompts

        source_count = len(source_files)
        test_count = len(test_files)

        if source_count > 0:
            coverage_ratio = test_count / source_count
        else:
            coverage_ratio = 1.0 if test_count > 0 else 0.5

        coverage_ratio = min(1.0, coverage_ratio)

        if coverage_ratio < 0.5:
            prompts.append(Prompt(
                perspective=Perspective.TEST,
                priority=Priority.HIGH,
                title="Increase test coverage",
                description=f"Only {test_count} test files for {source_count} source files.",
                metric_current=coverage_ratio * 100,
                metric_target=COVERAGE_TARGET,
                acceptance_criteria=[
                    f"Add tests for {max(1, source_count - test_count)} more modules",
                    "Achieve at least 50% file coverage"
                ],
                reason=f"Test coverage ratio is {coverage_ratio:.0%}, below 50% threshold"
            ))

        untested_complex = [
            a for a in source_files
            if not self._is_file_tested(a, test_files)
            and a.complexity > COMPLEXITY_THRESHOLD
        ]
        for analysis in untested_complex:
            prompts.append(Prompt(
                perspective=Perspective.TEST,
                priority=Priority.HIGH,
                title=f"Add tests for {analysis.path}",
                description=f"Complex file (complexity={analysis.complexity:.1f}) lacks tests.",
                file_path=analysis.path,
                metric_current=analysis.complexity,
                metric_target=COMPLEXITY_THRESHOLD,
                acceptance_criteria=[
                    "Create corresponding test file",
                    "Test main functions",
                    "Include edge cases"
                ],
                reason=f"Complexity {analysis.complexity:.1f} exceeds threshold {COMPLEXITY_THRESHOLD} with no tests"
            ))

        return {
            "code_coverage": coverage_ratio,
            "mutation_score": 1.0,
            "test_pass_rate": 1.0,
            "data_integrity_validation": 1.0
        }, prompts

    def _is_file_tested(self, source_analysis: FileAnalysis, test_files: List[FileAnalysis]) -> bool:
        """Check if a source file has a corresponding test file"""
        source_stem = Path(source_analysis.path).stem
        expected = {f"test_{source_stem}.py", f"{source_stem}_test.py"}
        return any(Path(tf.path).name in expected for tf in test_files)


class SystemPerspective(PerspectiveAnalyzer):
    """Analyzes architecture and code quality"""

    def get_perspective(self) -> Perspective:
        return Perspective.SYSTEM

    def analyze(self) -> Tuple[Dict[str, float], List[Prompt]]:
        prompts = []
        analyses = self.code_analyzer.get_all_analyses()

        if not analyses:
            return {
                "complexity": 0.5,
                "coupling": 0.5,
                "cohesion": 0.5,
                "infrastructure_health": 0.5,
                "configuration_consistency": 0.5
            }, [Prompt(
                perspective=Perspective.SYSTEM,
                priority=Priority.INFO,
                title="No Python files to analyze",
                description="No Python source files found in standard directories.",
                acceptance_criteria=[
                    "Add Python source files to standard directories (src/, lib/, etc.)",
                    "Or specify a custom root with --root"
                ],
                reason="No analyzable Python files found in standard directories"
            )]

        total_complexity = sum(a.complexity for a in analyses.values())
        avg_complexity = total_complexity / len(analyses)
        long_files = [a for a in analyses.values() if a.lines > MAX_FILE_LINES]
        high_complexity = [a for a in analyses.values() if a.complexity > COMPLEXITY_THRESHOLD]

        complexity_fitness = max(0, 1 - (avg_complexity / (COMPLEXITY_THRESHOLD * 2)))
        long_file_ratio = len(long_files) / len(analyses)
        length_fitness = 1 - long_file_ratio

        fitness = (complexity_fitness + length_fitness) / 2

        for analysis in long_files:
            prompts.append(Prompt(
                perspective=Perspective.SYSTEM,
                priority=Priority.MEDIUM,
                title=f"Refactor {analysis.path}",
                description=f"File has {analysis.lines} lines (max recommended: {MAX_FILE_LINES})",
                file_path=analysis.path,
                metric_current=analysis.lines,
                metric_target=MAX_FILE_LINES,
                acceptance_criteria=[
                    "Extract related functions into separate modules",
                    "Keep file under 300 lines",
                    "Maintain single responsibility"
                ],
                tags=["refactoring", "modularization"],
                reason=f"File exceeds {MAX_FILE_LINES}-line limit by {analysis.lines - MAX_FILE_LINES} lines"
            ))

        for analysis in high_complexity:
            prompts.append(Prompt(
                perspective=Perspective.SYSTEM,
                priority=Priority.MEDIUM,
                title=f"Reduce complexity in {analysis.path}",
                description=f"Cyclomatic complexity is {analysis.complexity:.1f} (max: {COMPLEXITY_THRESHOLD})",
                file_path=analysis.path,
                metric_current=analysis.complexity,
                metric_target=COMPLEXITY_THRESHOLD,
                acceptance_criteria=[
                    "Extract complex conditions into named functions",
                    "Reduce nesting depth",
                    "Use early returns where appropriate"
                ],
                tags=["complexity", "readability"],
                reason=f"Complexity {analysis.complexity:.1f} exceeds threshold {COMPLEXITY_THRESHOLD}"
            ))

        return {
            "complexity": fitness,
            "coupling": 1.0,
            "cohesion": 1.0,
            "infrastructure_health": 1.0,
            "configuration_consistency": 1.0
        }, prompts
