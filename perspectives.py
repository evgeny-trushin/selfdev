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
    load_config,
)
from analyzers import CodeAnalyzer, GitAnalyzer


class PerspectiveAnalyzer(ABC):
    """Base class for perspective analyzers.

    Supports pluggable fitness via *fitness_fn*: pass a callable
    ``(metrics: Dict[str, float], prompts: List[Prompt]) -> float``
    to override the default averaging behaviour.
    """

    def __init__(self, root_dir: Path, state: OrganismState,
                 fitness_fn=None, config: dict = None):
        self.root_dir = root_dir
        self.state = state
        self.config = config if config is not None else load_config(root_dir)
        self.code_analyzer = CodeAnalyzer(root_dir)
        self.git_analyzer = GitAnalyzer(root_dir)
        self._fitness_fn = fitness_fn

    def compute_fitness(self, metrics: Dict[str, float],
                        prompts: List["Prompt"]) -> float:
        """Compute a scalar fitness score from *metrics* and *prompts*.

        If a custom *fitness_fn* was provided at construction time, delegate
        to it; otherwise return the mean of all metric values.
        """
        if self._fitness_fn is not None:
            return self._fitness_fn(metrics, prompts)
        if not metrics:
            return 0.0
        return sum(metrics.values()) / len(metrics)

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

        coverage_target = self.config.get("coverage_target", COVERAGE_TARGET)
        complexity_threshold = self.config.get("complexity_threshold", COMPLEXITY_THRESHOLD)

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
                evaluative_evidence="No test files detected in known test directories",
                directive_evidence="Run 'mkdir tests' and add initial test suite",
                expected_next_state="Running test command discovers at least one passing test",
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
                metric_target=coverage_target,
                evaluative_evidence=f"Found {test_count} test files for {source_count} source files",
                directive_evidence=f"Add test files corresponding to untested source modules",
                expected_next_state=f"Coverage ratio is at least 50%",
                acceptance_criteria=[
                    f"Add tests for {max(1, source_count - test_count)} more modules",
                    "Achieve at least 50% file coverage"
                ],
                reason=f"Test coverage ratio is {coverage_ratio:.0%}, below 50% threshold"
            ))

        untested_complex = [
            a for a in source_files
            if not self._is_file_tested(a, test_files)
            and a.complexity > complexity_threshold
        ]
        for analysis in untested_complex:
            prompts.append(Prompt(
                perspective=Perspective.TEST,
                priority=Priority.HIGH,
                title=f"Add tests for {analysis.path}",
                description=f"Complex file (complexity={analysis.complexity:.1f}) lacks tests.",
                file_path=analysis.path,
                metric_current=analysis.complexity,
                metric_target=complexity_threshold,
                evaluative_evidence=f"File {analysis.path} has complexity {analysis.complexity:.1f} but no test file",
                directive_evidence=f"Create a test file for {analysis.path}",
                expected_next_state=f"A test file exists that imports and tests functions from {analysis.path}",
                acceptance_criteria=[
                    "Create corresponding test file",
                    "Test main functions",
                    "Include edge cases"
                ],
                reason=f"Complexity {analysis.complexity:.1f} exceeds threshold {complexity_threshold} with no tests"
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

        complexity_threshold = self.config.get("complexity_threshold", COMPLEXITY_THRESHOLD)
        max_file_lines = self.config.get("max_file_lines", MAX_FILE_LINES)

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
                evaluative_evidence="0 Python files found by CodeAnalyzer in standard directories",
                directive_evidence="Ensure standard directories (src/, lib/) contain Python source files",
                expected_next_state="CodeAnalyzer returns >0 parsed files",
                acceptance_criteria=[
                    "Add Python source files to standard directories (src/, lib/, etc.)",
                    "Or specify a custom root with --root"
                ],
                reason="No analyzable Python files found in standard directories"
            )]

        total_complexity = sum(a.complexity for a in analyses.values())
        avg_complexity = total_complexity / len(analyses)
        long_files = [a for a in analyses.values() if a.lines > max_file_lines]
        high_complexity = [a for a in analyses.values() if a.complexity > complexity_threshold]

        complexity_fitness = max(0, 1 - (avg_complexity / (complexity_threshold * 2)))
        long_file_ratio = len(long_files) / len(analyses)
        length_fitness = 1 - long_file_ratio

        fitness = (complexity_fitness + length_fitness) / 2

        for analysis in long_files:
            prompts.append(Prompt(
                perspective=Perspective.SYSTEM,
                priority=Priority.MEDIUM,
                title=f"Refactor {analysis.path}",
                description=f"File has {analysis.lines} lines (max recommended: {max_file_lines})",
                file_path=analysis.path,
                metric_current=analysis.lines,
                metric_target=max_file_lines,
                evaluative_evidence=f"File has {analysis.lines} lines (limit {max_file_lines})",
                directive_evidence="Extract related functions into separate modules",
                expected_next_state=f"File length is <= {max_file_lines} lines",
                acceptance_criteria=[
                    "Extract related functions into separate modules",
                    f"Keep file under {max_file_lines} lines",
                    "Maintain single responsibility"
                ],
                tags=["refactoring", "modularization"],
                reason=f"File exceeds {max_file_lines}-line limit by {analysis.lines - max_file_lines} lines"
            ))

        for analysis in high_complexity:
            prompts.append(Prompt(
                perspective=Perspective.SYSTEM,
                priority=Priority.MEDIUM,
                title=f"Reduce complexity in {analysis.path}",
                description=f"Cyclomatic complexity is {analysis.complexity:.1f} (max: {complexity_threshold})",
                file_path=analysis.path,
                metric_current=analysis.complexity,
                metric_target=complexity_threshold,
                evaluative_evidence=f"Cyclomatic complexity is {analysis.complexity:.1f} (threshold {complexity_threshold})",
                directive_evidence="Extract complex conditions into smaller named functions",
                expected_next_state=f"Cyclomatic complexity <= {complexity_threshold}",
                acceptance_criteria=[
                    "Extract complex conditions into named functions",
                    "Reduce nesting depth",
                    "Use early returns where appropriate"
                ],
                tags=["complexity", "readability"],
                reason=f"Complexity {analysis.complexity:.1f} exceeds threshold {complexity_threshold}"
            ))

        return {
            "complexity": fitness,
            "coupling": 1.0,
            "cohesion": 1.0,
            "infrastructure_health": 1.0,
            "configuration_consistency": 1.0
        }, prompts
