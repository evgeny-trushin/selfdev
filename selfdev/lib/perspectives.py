import re
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Tuple
from .models import (
    Perspective,
    Priority,
    Prompt,
    OrganismState
)
from .analyzers import CodeAnalyzer, GitAnalyzer
from .constants import (
    ANALYZABLE_DIRS,
    TEST_DIRS,
    COMPLEXITY_THRESHOLD,
    COVERAGE_TARGET,
    MAX_FILE_LINES,
)


class PerspectiveAnalyzer(ABC):
    """Base class for perspective analyzers"""

    def __init__(self, root_dir: Path, state: OrganismState):
        self.root_dir = root_dir
        self.state = state
        self.code_analyzer = CodeAnalyzer(root_dir)
        self.git_analyzer = GitAnalyzer(root_dir)

    @abstractmethod
    def analyze(self) -> Tuple[float, List[Prompt]]:
        """Analyze from this perspective. Returns (fitness_score, prompts)"""
        pass

    @abstractmethod
    def get_perspective(self) -> Perspective:
        """Return the perspective type"""
        pass


class UserPerspective(PerspectiveAnalyzer):
    """Analyzes from user's point of view"""

    def get_perspective(self) -> Perspective:
        return Perspective.USER

    def analyze(self) -> Tuple[float, List[Prompt]]:
        prompts = []
        fitness_components = []

        # Check for README
        readme_path = self.root_dir / "README.md"
        if readme_path.exists():
            content = readme_path.read_text()
            # Score based on content quality
            score = min(1.0, len(content) / 5000)  # Max 1.0 at 5000 chars
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
        else:
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

        # Check for package.json (features/dependencies documented)
        package_json = self.root_dir / "package.json"
        if package_json.exists():
            try:
                pkg = json.loads(package_json.read_text())
                if "description" in pkg and pkg["description"]:
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
            except json.JSONDecodeError:
                fitness_components.append(0.0)

        # Check for CHANGELOG
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

        # Calculate overall fitness
        fitness = sum(fitness_components) / len(fitness_components) if fitness_components else 0.5

        return fitness, prompts


class TestPerspective(PerspectiveAnalyzer):
    """Analyzes test coverage and quality"""

    def get_perspective(self) -> Perspective:
        return Perspective.TEST

    def analyze(self) -> Tuple[float, List[Prompt]]:
        prompts = []
        analyses = self.code_analyzer.get_all_analyses()

        # Count source and test files
        source_files = [a for a in analyses.values() if not a.has_tests]
        test_files = [a for a in analyses.values() if a.has_tests]

        # Check test directory exists
        test_dirs_exist = any((self.root_dir / td).exists() for td in TEST_DIRS)

        if not test_dirs_exist:
            prompts.append(Prompt(
                perspective=Perspective.TEST,
                priority=Priority.CRITICAL,
                title="Create test directory",
                description="No test directory found. Tests are essential for code quality.",
                acceptance_criteria=[
                    "Create tests/ directory",
                    "Add at least one test file",
                    "Configure test runner"
                ]
            ))
            return 0.0, prompts

        # Calculate test coverage ratio
        source_count = len(source_files)
        test_count = len(test_files)

        if source_count > 0:
            coverage_ratio = test_count / source_count
        else:
            coverage_ratio = 1.0 if test_count > 0 else 0.5

        fitness = min(1.0, coverage_ratio)

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
                ]
            ))

        # Check for untested complex files
        for analysis in source_files:
            # Check if a corresponding test file exists
            file_name = Path(analysis.path).name
            base_name = file_name.replace(".py", "")
            has_corresponding_test = False

            for test_analysis in test_files:
                test_path = test_analysis.path
                if f"test_{file_name}" in test_path or f"test_{base_name}" in test_path:
                    has_corresponding_test = True
                    break

            if not has_corresponding_test and analysis.complexity > COMPLEXITY_THRESHOLD:
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
                    ]
                ))

        return fitness, prompts


class SystemPerspective(PerspectiveAnalyzer):
    """Analyzes architecture and code quality"""

    def get_perspective(self) -> Perspective:
        return Perspective.SYSTEM

    def analyze(self) -> Tuple[float, List[Prompt]]:
        prompts = []
        analyses = self.code_analyzer.get_all_analyses()

        if not analyses:
            return 0.5, [Prompt(
                perspective=Perspective.SYSTEM,
                priority=Priority.INFO,
                title="No Python files to analyze",
                description="No Python source files found in standard directories."
            )]

        # Calculate metrics
        total_complexity = sum(a.complexity for a in analyses.values())
        avg_complexity = total_complexity / len(analyses)
        total_lines = sum(a.lines for a in analyses.values())
        long_files = [a for a in analyses.values() if a.lines > MAX_FILE_LINES]
        high_complexity = [a for a in analyses.values() if a.complexity > COMPLEXITY_THRESHOLD]

        # Calculate fitness
        fitness_components = []

        # Complexity fitness
        complexity_fitness = max(0, 1 - (avg_complexity / (COMPLEXITY_THRESHOLD * 2)))
        fitness_components.append(complexity_fitness)

        # File length fitness
        long_file_ratio = len(long_files) / len(analyses)
        length_fitness = 1 - long_file_ratio
        fitness_components.append(length_fitness)

        fitness = sum(fitness_components) / len(fitness_components)

        # Generate prompts for issues
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
                tags=["refactoring", "modularization"]
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
                tags=["complexity", "readability"]
            ))

        return fitness, prompts


class AnalyticsPerspective(PerspectiveAnalyzer):
    """Analyzes trends and patterns"""

    def get_perspective(self) -> Perspective:
        return Perspective.ANALYTICS

    def analyze(self) -> Tuple[float, List[Prompt]]:
        prompts = []

        # Analyze fitness history trends
        history = self.state.fitness_history

        if len(history) < 2:
            return 0.5, [Prompt(
                perspective=Perspective.ANALYTICS,
                priority=Priority.INFO,
                title="Insufficient history for trend analysis",
                description="Run more generations to enable trend analysis."
            )]

        # Calculate trend
        recent = history[-5:]
        if len(recent) >= 2:
            avg_recent = sum(h.get("overall", 0.5) for h in recent) / len(recent)
            avg_older = sum(h.get("overall", 0.5) for h in history[:-5]) / max(1, len(history) - 5)

            trend = avg_recent - avg_older

            if trend < -0.1:
                prompts.append(Prompt(
                    perspective=Perspective.ANALYTICS,
                    priority=Priority.HIGH,
                    title="Fitness declining",
                    description=f"Average fitness dropped by {abs(trend):.2f} over recent generations.",
                    metric_current=avg_recent,
                    metric_target=avg_older,
                    acceptance_criteria=[
                        "Review recent changes",
                        "Identify regression sources",
                        "Prioritize stability over features"
                    ]
                ))
            elif trend > 0.1:
                prompts.append(Prompt(
                    perspective=Perspective.ANALYTICS,
                    priority=Priority.INFO,
                    title="Positive fitness trend",
                    description=f"Fitness improved by {trend:.2f}. Keep current trajectory.",
                    tags=["positive", "trend"]
                ))

        # Analyze commit patterns
        commits = self.git_analyzer.get_recent_commits()
        if commits:
            # Check for commit message patterns
            fix_commits = sum(1 for c in commits if "fix" in c["message"].lower())
            if fix_commits > len(commits) * 0.5:
                prompts.append(Prompt(
                    perspective=Perspective.ANALYTICS,
                    priority=Priority.MEDIUM,
                    title="High bug fix rate detected",
                    description=f"{fix_commits}/{len(commits)} recent commits are fixes.",
                    acceptance_criteria=[
                        "Improve test coverage",
                        "Add pre-commit hooks",
                        "Review development process"
                    ]
                ))

        fitness = 0.7  # Analytics perspective has stable fitness
        return fitness, prompts


class DebugPerspective(PerspectiveAnalyzer):
    """Analyzes for bugs and issues"""

    def get_perspective(self) -> Perspective:
        return Perspective.DEBUG

    def analyze(self) -> Tuple[float, List[Prompt]]:
        prompts = []
        analyses = self.code_analyzer.get_all_analyses()

        # Collect all issues
        all_issues = []
        for analysis in analyses.values():
            for issue in analysis.issues:
                all_issues.append((analysis.path, issue))

        # Check for TODO/FIXME comments
        todo_pattern = re.compile(r'#\s*(TODO|FIXME|XXX|HACK|BUG)[\s:]*(.*)', re.IGNORECASE)
        todos = []

        for dir_name in ANALYZABLE_DIRS:
            dir_path = self.root_dir / dir_name
            if not dir_path.exists():
                continue
            for file_path in dir_path.rglob("*.py"):
                if "__pycache__" in str(file_path):
                    continue
                try:
                    content = file_path.read_text()
                    for i, line in enumerate(content.splitlines(), 1):
                        match = todo_pattern.search(line)
                        if match:
                            todos.append({
                                "file": str(file_path.relative_to(self.root_dir)),
                                "line": i,
                                "type": match.group(1).upper(),
                                "text": match.group(2).strip()
                            })
                except Exception:
                    continue

        # Generate prompts for TODOs
        for todo in todos[:10]:  # Limit to 10
            priority = Priority.HIGH if todo["type"] in ["FIXME", "BUG"] else Priority.MEDIUM
            prompts.append(Prompt(
                perspective=Perspective.DEBUG,
                priority=priority,
                title=f"{todo['type']}: {todo['text'][:50]}",
                description=f"Found in {todo['file']}:{todo['line']}",
                file_path=todo["file"],
                line_number=todo["line"],
                acceptance_criteria=[
                    f"Address the {todo['type']} comment",
                    "Remove or update the comment after resolution"
                ],
                tags=[todo["type"].lower()]
            ))

        # Check for uncommitted changes
        uncommitted = self.git_analyzer.get_uncommitted_changes()
        if uncommitted:
            prompts.append(Prompt(
                perspective=Perspective.DEBUG,
                priority=Priority.MEDIUM,
                title="Uncommitted changes detected",
                description=f"{len(uncommitted)} files have uncommitted changes.",
                acceptance_criteria=[
                    "Review and commit changes",
                    "Or stash if work in progress"
                ]
            ))

        # Calculate fitness based on issues
        issue_count = len(all_issues) + len(todos)
        max_issues = 20
        fitness = max(0.1, 1 - (issue_count / max_issues))

        return fitness, prompts
