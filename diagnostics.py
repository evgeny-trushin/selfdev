"""
Diagnostic perspective analyzers for the Self-Development Organism system.
Analytics (trends/patterns) and Debug (issues/TODOs) perspectives.
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple

from models import (
    OrganismState,
    Perspective,
    Priority,
    Prompt,
    ANALYZABLE_DIRS,
)
from perspectives import PerspectiveAnalyzer


class AnalyticsPerspective(PerspectiveAnalyzer):
    """Analyzes trends and patterns"""

    def get_perspective(self) -> Perspective:
        return Perspective.ANALYTICS

    def analyze(self) -> Tuple[Dict[str, float], List[Prompt]]:
        prompts = []

        history = self.state.fitness_history

        if len(history) < 2:
            return {
                "feature_adoption": 0.5,
                "user_retention": 0.5,
                "error_rate_trends": 0.5,
                "usage_patterns": 0.5
            }, [Prompt(
                perspective=Perspective.ANALYTICS,
                priority=Priority.INFO,
                title="Insufficient history for trend analysis",
                description="Run more generations to enable trend analysis.",
                evaluative_evidence=f"Fitness history contains only {len(history)} entries (needs >=2)",
                directive_evidence="Run the development cycle multiple times to collect metrics",
                expected_next_state="History array has >= 2 completed generations",
                acceptance_criteria=[
                    "Complete at least 2 generations to build fitness history",
                    "Run ./develop.sh after each increment to record metrics"
                ],
                reason="Fitness history has fewer than 2 entries"
            )]

        older = history[:-5]
        recent = history[-5:]
        if len(recent) >= 2 and len(older) >= 1:
            avg_recent = sum(h.get("overall", 0.5) for h in recent) / len(recent)
            avg_older = sum(h.get("overall", 0.5) for h in older) / len(older)

            trend = avg_recent - avg_older

            if trend < -0.1:
                prompts.append(Prompt(
                    perspective=Perspective.ANALYTICS,
                    priority=Priority.HIGH,
                    title="Fitness declining",
                    description=f"Average fitness dropped by {abs(trend):.2f} over recent generations.",
                    metric_current=avg_recent,
                    metric_target=avg_older,
                    evaluative_evidence=f"Average fitness dropped from {avg_older:.2f} to {avg_recent:.2f} (trend {trend:+.2f})",
                    directive_evidence="Review recent commits to identify regression sources",
                    expected_next_state="Subsequent fitness trends return to positive or zero",
                    acceptance_criteria=[
                        "Review recent changes",
                        "Identify regression sources",
                        "Prioritize stability over features"
                    ],
                    reason=f"Fitness trend is {trend:+.2f}, below -0.1 threshold"
                ))
            elif trend > 0.1:
                prompts.append(Prompt(
                    perspective=Perspective.ANALYTICS,
                    priority=Priority.INFO,
                    title="Positive fitness trend",
                    description=f"Fitness improved by {trend:.2f}. Keep current trajectory.",
                    evaluative_evidence=f"Fitness improved by {trend:+.2f}",
                    directive_evidence="Review positive changes for best practices",
                    expected_next_state="Sustained fitness improvement in future metrics",
                    acceptance_criteria=[
                        "Continue current development approach",
                        "Monitor for sustained improvement"
                    ],
                    tags=["positive", "trend"],
                    reason=f"Fitness trend is {trend:+.2f}, above +0.1 threshold"
                ))

        commits = self.git_analyzer.get_recent_commits()
        if commits:
            fix_commits = sum(1 for c in commits if "fix" in c["message"].lower())
            if fix_commits > len(commits) * 0.5:
                prompts.append(Prompt(
                    perspective=Perspective.ANALYTICS,
                    priority=Priority.MEDIUM,
                    title="High bug fix rate detected",
                    description=f"{fix_commits}/{len(commits)} recent commits are fixes.",
                    evaluative_evidence=f"{fix_commits} out of {len(commits)} recent commits contain 'fix'",
                    directive_evidence="Review test coverage and bug introduction rate",
                    expected_next_state="Bug fix ratio drops below 50% in subsequent commits",
                    acceptance_criteria=[
                        "Improve test coverage",
                        "Add pre-commit hooks",
                        "Review development process"
                    ],
                    reason=f"Bug-fix ratio {fix_commits}/{len(commits)} exceeds 50% threshold"
                ))

        fitness = 1.0
        for prompt in prompts:
            if prompt.priority == Priority.HIGH:
                fitness -= 0.3
            elif prompt.priority == Priority.MEDIUM:
                fitness -= 0.15
        fitness = max(0.1, fitness)
        return {
            "feature_adoption": 1.0,
            "user_retention": 1.0,
            "error_rate_trends": fitness,
            "usage_patterns": 1.0
        }, prompts


class DebugPerspective(PerspectiveAnalyzer):
    """Analyzes for bugs and issues"""

    def get_perspective(self) -> Perspective:
        return Perspective.DEBUG

    def analyze(self) -> Tuple[Dict[str, float], List[Prompt]]:
        prompts = []
        analyses = self.code_analyzer.get_all_analyses()

        all_issues = []
        for analysis in analyses.values():
            for issue in analysis.issues:
                all_issues.append((analysis.path, issue))

        for file_path, issue_text in all_issues:
            prompts.append(Prompt(
                perspective=Perspective.DEBUG,
                priority=Priority.MEDIUM,
                title=f"Code issue in {file_path}",
                description=issue_text,
                file_path=file_path,
                evaluative_evidence=f"CodeAnalyzer found issue: '{issue_text}' in {file_path}",
                directive_evidence=f"Resolve the issue in {file_path}",
                expected_next_state=f"CodeAnalyzer reports 0 issues for {file_path}",
                acceptance_criteria=["Resolve the reported code quality issue"],
                tags=["code-quality"],
                reason=f"Static analysis detected issue in {file_path}"
            ))

        todos = self._find_todo_comments()
        self._generate_todo_prompts(todos, prompts)

        uncommitted = self.git_analyzer.get_uncommitted_changes()
        if uncommitted:
            prompts.append(Prompt(
                perspective=Perspective.DEBUG,
                priority=Priority.MEDIUM,
                title="Uncommitted changes detected",
                description=f"{len(uncommitted)} files have uncommitted changes.",
                evaluative_evidence=f"git status shows {len(uncommitted)} uncommitted files",
                directive_evidence="Review changes and run git commit",
                expected_next_state="git status working tree is clean",
                acceptance_criteria=[
                    "Review and commit changes",
                    "Or stash if work in progress"
                ],
                reason=f"{len(uncommitted)} modified files not yet committed"
            ))

        issue_count = len(all_issues) + len(todos)
        max_issues = 20
        fitness = max(0.1, 1 - (issue_count / max_issues))

        return {
            "error_count": fitness,
            "broken_integrations": 1.0,
            "stale_data": 1.0,
            "deployment_failures": 1.0,
            "infrastructure_drift": 1.0
        }, prompts

    def _find_todo_comments(self) -> List[dict]:
        """Scan source directories for TODO/FIXME comments, skipping test files"""
        todo_pattern = re.compile(r'#\s*(TODO|FIXME|XXX|HACK|BUG)[\s:]*(.*)', re.IGNORECASE)
        todos = []

        analyses = self.code_analyzer.get_all_analyses()
        for file_path_str in analyses.keys():
            file_path = self.root_dir / file_path_str
            if not file_path.exists():
                continue
            # Skip test files — markers inside them are test fixtures, not real issues
            if file_path.name.startswith("test_") or "/tests/" in str(file_path):
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

        return todos

    def _generate_todo_prompts(self, todos: List[dict], prompts: List[Prompt]):
        """Generate prompts for found TODO/FIXME comments"""
        for todo in todos[:10]:
            priority = Priority.HIGH if todo["type"] in ["FIXME", "BUG"] else Priority.MEDIUM
            prompts.append(Prompt(
                perspective=Perspective.DEBUG,
                priority=priority,
                title=f"{todo['type']}: {todo['text'][:50]}",
                description=f"Found in {todo['file']}:{todo['line']}",
                file_path=todo["file"],
                line_number=todo["line"],
                evaluative_evidence=f"Found {todo['type']} comment at {todo['file']}:{todo['line']}",
                directive_evidence=f"Resolve the issue detailed in the comment: '{todo['text']}'",
                expected_next_state=f"The comment at {todo['file']}:{todo['line']} is resolved and removed",
                acceptance_criteria=[
                    f"Address the {todo['type']} comment",
                    "Remove or update the comment after resolution"
                ],
                tags=[todo["type"].lower()],
                reason=f"{todo['type']} comment found at {todo['file']}:{todo['line']}"
            ))
