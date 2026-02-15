#!/usr/bin/env python3
"""
Self-Development Organism
A system that analyzes codebase state and generates prompts from multiple perspectives.
Inspired by biological development principles and lateral thinking.
"""

import os
import sys
import json
import ast
import re
import subprocess
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, Tuple
from abc import ABC, abstractmethod
from enum import Enum
from collections import defaultdict

# ==================== Constants ====================

ROOT_DIR = Path(__file__).resolve().parent
STATE_FILE = Path(__file__).resolve().parent / "organism_state.json"
REQUIREMENTS_FILE = Path(__file__).resolve().parent / "requirements.md"
PRINCIPLES_FILE = Path(__file__).resolve().parent / "principles.md"

# Directories to analyze
ANALYZABLE_DIRS = ["src", "components", "pages", "lib", "utils", "services"]
TEST_DIRS = ["tests", "__tests__", "test", "spec"]

# Thresholds
COMPLEXITY_THRESHOLD = 10  # McCabe complexity
COVERAGE_TARGET = 80  # Percentage
MAX_FILE_LINES = 300
MAX_FUNCTION_LINES = 50


# ==================== Enums ====================

class DevelopmentStage(Enum):
    EMBRYONIC = "embryonic"      # Generation 0-3
    GROWTH = "growth"            # Generation 4-10
    MATURATION = "maturation"    # Generation 11-20
    HOMEOSTASIS = "homeostasis"  # Generation 21+


class Perspective(Enum):
    USER = "user"
    TEST = "test"
    SYSTEM = "system"
    ANALYTICS = "analytics"
    DEBUG = "debug"


class Priority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    INFO = 5


# ==================== Data Classes ====================

@dataclass
class Prompt:
    """A generated development prompt"""
    perspective: Perspective
    priority: Priority
    title: str
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    metric_current: Optional[float] = None
    metric_target: Optional[float] = None
    acceptance_criteria: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


@dataclass
class FileAnalysis:
    """Analysis results for a single file"""
    path: str
    lines: int
    functions: int
    classes: int
    imports: int
    complexity: float
    has_tests: bool
    issues: List[str] = field(default_factory=list)


@dataclass
class OrganismState:
    """Current state of the self-developing organism"""
    generation: int = 0
    created_at: str = ""
    last_updated: str = ""
    development_stage: str = "embryonic"
    fitness_scores: Dict[str, float] = field(default_factory=dict)
    fitness_history: List[Dict] = field(default_factory=list)
    prompts_generated: int = 0
    prompts_completed: int = 0
    last_git_hash: str = ""

    @classmethod
    def load(cls, path: Path) -> "OrganismState":
        """Load state from file or create new"""
        if path.exists():
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                return cls(**data)
            except (json.JSONDecodeError, TypeError):
                pass
        return cls(created_at=datetime.now(timezone.utc).isoformat())

    def save(self, path: Path) -> None:
        """Save state to file"""
        self.last_updated = datetime.now(timezone.utc).isoformat()
        with open(path, "w") as f:
            json.dump(asdict(self), f, indent=2)

    def get_stage(self) -> DevelopmentStage:
        """Get current development stage based on generation"""
        if self.generation <= 3:
            return DevelopmentStage.EMBRYONIC
        elif self.generation <= 10:
            return DevelopmentStage.GROWTH
        elif self.generation <= 20:
            return DevelopmentStage.MATURATION
        else:
            return DevelopmentStage.HOMEOSTASIS


# ==================== Code Analyzer ====================

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

        # Calculate complexity (simplified McCabe)
        complexity = self._calculate_complexity(tree)

        # Check if this is a test file
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

        # Also analyze root Python files
        for file_path in self.root_dir.glob("*.py"):
            analysis = self.analyze_file(file_path)
            if analysis:
                all_results[analysis.path] = analysis

        self.file_analyses = all_results
        return all_results


# ==================== Git Analyzer ====================

class GitAnalyzer:
    """Analyzes Git history and state"""

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir

    def get_current_hash(self) -> str:
        """Get current commit hash"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.root_dir,
                capture_output=True,
                text=True
            )
            return result.stdout.strip()[:8]
        except Exception:
            return ""

    def get_recent_commits(self, count: int = 10) -> List[Dict]:
        """Get recent commits"""
        try:
            result = subprocess.run(
                ["git", "log", f"-{count}", "--pretty=format:%H|%s|%ad", "--date=iso"],
                cwd=self.root_dir,
                capture_output=True,
                text=True
            )
            commits = []
            for line in result.stdout.strip().split("\n"):
                if "|" in line:
                    parts = line.split("|", 2)
                    commits.append({
                        "hash": parts[0][:8],
                        "message": parts[1] if len(parts) > 1 else "",
                        "date": parts[2] if len(parts) > 2 else ""
                    })
            return commits
        except Exception:
            return []

    def get_uncommitted_changes(self) -> List[str]:
        """Get list of uncommitted files"""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.root_dir,
                capture_output=True,
                text=True
            )
            return [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]
        except Exception:
            return []

    def get_branch(self) -> str:
        """Get current branch name"""
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.root_dir,
                capture_output=True,
                text=True
            )
            return result.stdout.strip()
        except Exception:
            return "unknown"


# ==================== Perspective Analyzers ====================

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
            if analysis.complexity > COMPLEXITY_THRESHOLD:
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


# ==================== Prompt Formatter ====================

class PromptFormatter:
    """Formats prompts for console output"""

    COLORS = {
        Priority.CRITICAL: "\033[91m",  # Red
        Priority.HIGH: "\033[93m",       # Yellow
        Priority.MEDIUM: "\033[94m",     # Blue
        Priority.LOW: "\033[92m",        # Green
        Priority.INFO: "\033[90m",       # Gray
    }
    RESET = "\033[0m"
    BOLD = "\033[1m"

    def __init__(self, use_colors: bool = True):
        self.use_colors = use_colors

    def _c(self, color: str, text: str) -> str:
        """Apply color if enabled"""
        if self.use_colors:
            return f"{color}{text}{self.RESET}"
        return text

    def format_prompt(self, prompt: Prompt) -> str:
        """Format a single prompt"""
        lines = []

        # Priority and title
        priority_color = self.COLORS.get(prompt.priority, "")
        priority_str = prompt.priority.name
        lines.append(self._c(priority_color, f"[{priority_str}]") + f" {self.BOLD}{prompt.title}{self.RESET}")

        # Description
        lines.append(f"  {prompt.description}")

        # File location
        if prompt.file_path:
            loc = prompt.file_path
            if prompt.line_number:
                loc += f":{prompt.line_number}"
            lines.append(f"  Location: {loc}")

        # Metrics
        if prompt.metric_current is not None and prompt.metric_target is not None:
            lines.append(f"  Current: {prompt.metric_current:.1f} -> Target: {prompt.metric_target:.1f}")

        # Acceptance criteria
        if prompt.acceptance_criteria:
            lines.append("  Acceptance Criteria:")
            for criterion in prompt.acceptance_criteria:
                lines.append(f"    - {criterion}")

        return "\n".join(lines)

    def format_header(self, perspective: Perspective, fitness: float, state: OrganismState) -> str:
        """Format the header for a perspective"""
        stage = state.get_stage()

        lines = [
            "",
            "=" * 60,
            f"  PERSPECTIVE: {perspective.value.upper()}",
            f"  Generation: {state.generation}  |  Stage: {stage.value}",
            f"  Fitness: {fitness:.2%}",
            "=" * 60,
            ""
        ]
        return "\n".join(lines)

    def format_summary(self, state: OrganismState, all_prompts: List[Prompt]) -> str:
        """Format a summary of all prompts"""
        lines = [
            "",
            "-" * 60,
            "  SUMMARY",
            "-" * 60,
            f"  Total Prompts: {len(all_prompts)}",
        ]

        # Count by priority
        by_priority = defaultdict(int)
        for p in all_prompts:
            by_priority[p.priority] += 1

        for priority in Priority:
            if by_priority[priority] > 0:
                lines.append(f"    {priority.name}: {by_priority[priority]}")

        # Overall fitness
        if state.fitness_scores:
            overall = sum(state.fitness_scores.values()) / len(state.fitness_scores)
            lines.append(f"\n  Overall Fitness: {overall:.2%}")

        lines.append("-" * 60)
        return "\n".join(lines)


# ==================== Main Organism Class ====================

class SelfDevelopmentOrganism:
    """Main class orchestrating the self-development system"""

    def __init__(self, root_dir: Path = ROOT_DIR):
        self.root_dir = root_dir
        self.state = OrganismState.load(STATE_FILE)
        self.formatter = PromptFormatter()

        self.perspectives = {
            Perspective.USER: UserPerspective(root_dir, self.state),
            Perspective.TEST: TestPerspective(root_dir, self.state),
            Perspective.SYSTEM: SystemPerspective(root_dir, self.state),
            Perspective.ANALYTICS: AnalyticsPerspective(root_dir, self.state),
            Perspective.DEBUG: DebugPerspective(root_dir, self.state),
        }

    def run_perspective(self, perspective: Perspective) -> List[Prompt]:
        """Run analysis from a specific perspective"""
        analyzer = self.perspectives[perspective]
        fitness, prompts = analyzer.analyze()

        # Update state
        self.state.fitness_scores[perspective.value] = fitness

        # Print results
        print(self.formatter.format_header(perspective, fitness, self.state))

        if prompts:
            for prompt in sorted(prompts, key=lambda p: p.priority.value):
                print(self.formatter.format_prompt(prompt))
                print()
        else:
            print("  No issues found from this perspective.")

        return prompts

    def run_all_perspectives(self) -> List[Prompt]:
        """Run all perspective analyses"""
        all_prompts = []

        for perspective in Perspective:
            prompts = self.run_perspective(perspective)
            all_prompts.extend(prompts)

        # Print summary
        print(self.formatter.format_summary(self.state, all_prompts))

        return all_prompts

    def advance_generation(self):
        """Advance to next generation"""
        # Record current fitness
        self.state.fitness_history.append({
            "generation": self.state.generation,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **self.state.fitness_scores
        })

        # Update git hash
        git_analyzer = GitAnalyzer(self.root_dir)
        self.state.last_git_hash = git_analyzer.get_current_hash()

        # Increment generation
        self.state.generation += 1
        self.state.development_stage = self.state.get_stage().value

        # Save state
        self.state.save(STATE_FILE)

        print(f"\nAdvanced to Generation {self.state.generation}")
        print(f"Development Stage: {self.state.development_stage}")

    def print_state(self):
        """Print current organism state"""
        print("\n" + "=" * 60)
        print("  ORGANISM STATE")
        print("=" * 60)
        print(f"  Generation: {self.state.generation}")
        print(f"  Stage: {self.state.get_stage().value}")
        print(f"  Created: {self.state.created_at[:19] if self.state.created_at else 'N/A'}")
        print(f"  Last Updated: {self.state.last_updated[:19] if self.state.last_updated else 'N/A'}")
        print(f"  Git Hash: {self.state.last_git_hash or 'N/A'}")

        if self.state.fitness_scores:
            print("\n  Fitness Scores:")
            for perspective, score in self.state.fitness_scores.items():
                print(f"    {perspective}: {score:.2%}")

        print("=" * 60)


# ==================== CLI Entry Point ====================

def main():
    """Main entry point for the self-development system"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Self-Development System - Analyze codebase from multiple perspectives"
    )
    parser.add_argument("--user", action="store_true", help="Run user perspective analysis")
    parser.add_argument("--test", action="store_true", help="Run test perspective analysis")
    parser.add_argument("--system", action="store_true", help="Run system perspective analysis")
    parser.add_argument("--analytics", action="store_true", help="Run analytics perspective analysis")
    parser.add_argument("--debug", action="store_true", help="Run debug perspective analysis")
    parser.add_argument("--all", action="store_true", help="Run all perspectives")
    parser.add_argument("--state", action="store_true", help="Show current state")
    parser.add_argument("--advance", action="store_true", help="Advance to next generation")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    parser.add_argument("--root", type=str, default=None,
                        help="Root directory to analyze (default: parent directory)")
    parser.add_argument("--self", action="store_true",
                        help="Analyze the selfdev project itself")

    args = parser.parse_args()

    # Determine root directory
    if args.self:
        root_dir = Path(__file__).resolve().parent
    elif args.root:
        root_dir = Path(args.root).resolve()
    else:
        root_dir = ROOT_DIR

    organism = SelfDevelopmentOrganism(root_dir=root_dir)

    if args.no_color:
        organism.formatter.use_colors = False

    if args.state:
        organism.print_state()
        return

    if args.advance:
        organism.advance_generation()
        return

    # Determine which perspectives to run
    perspectives_to_run = []

    if args.user:
        perspectives_to_run.append(Perspective.USER)
    if args.test:
        perspectives_to_run.append(Perspective.TEST)
    if args.system:
        perspectives_to_run.append(Perspective.SYSTEM)
    if args.analytics:
        perspectives_to_run.append(Perspective.ANALYTICS)
    if args.debug:
        perspectives_to_run.append(Perspective.DEBUG)

    if args.all or not perspectives_to_run:
        organism.run_all_perspectives()
    else:
        all_prompts = []
        for perspective in perspectives_to_run:
            prompts = organism.run_perspective(perspective)
            all_prompts.extend(prompts)

        if len(perspectives_to_run) > 1:
            print(organism.formatter.format_summary(organism.state, all_prompts))

    # Save state after analysis
    organism.state.save(STATE_FILE)


if __name__ == "__main__":
    main()
