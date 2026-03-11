"""
Diagnostic perspective analyzers for the Self-Development Organism system.
Analytics (trends/patterns) and Debug (issues/TODOs) perspectives.
"""

import re
from pathlib import Path
from typing import List, Tuple

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

    def analyze(self) -> Tuple[float, List[Prompt]]:
        prompts = []

        history = self.state.fitness_history

        if len(history) < 2:
            return 0.5, [Prompt(
                perspective=Perspective.ANALYTICS,
                priority=Priority.INFO,
                title="Insufficient history for trend analysis",
                description="Run more generations to enable trend analysis."
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

        commits = self.git_analyzer.get_recent_commits()
        if commits:
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

        # Check evolutionary state using git history stats
        total_commits = self.git_analyzer.get_total_commits()
        if total_commits > 0:
            stats = self.git_analyzer.get_commit_history_stats(count=10)
            prompts.append(Prompt(
                perspective=Perspective.ANALYTICS,
                priority=Priority.INFO,
                title="Codebase Evolutionary State",
                description=f"Repository has {total_commits} total commits. "
                            f"Recent changes (last 10 commits): {stats['insertions']} insertions, "
                            f"{stats['deletions']} deletions across {stats['files_changed']} files.",
                tags=["evolution", "history"]
            ))

        # Calculate gap to desired state
        latest_fitness = 0.5
        if history:
            latest_fitness = history[-1].get("overall", 0.5)

        target_fitness = 1.0
        gap = target_fitness - latest_fitness
        if gap > 0.05:  # more than 5% gap
            # Only generate prompt if history is sufficient, otherwise the score is just defaults
            if len(history) >= 2:
                prompts.append(Prompt(
                    perspective=Perspective.ANALYTICS,
                    priority=Priority.MEDIUM,  # Use medium so it doesn't penalize fitness too much
                    title="System Desired State Gap",
                    description=f"Current fitness is {latest_fitness:.1%} compared to the target of {target_fitness:.1%}.",
                    metric_current=latest_fitness * 100,
                    metric_target=target_fitness * 100,
                    acceptance_criteria=[
                        f"Close the {(gap * 100):.1f}% gap to desired state",
                        "Address critical and high priority prompts across perspectives",
                        "Improve test coverage and code quality"
                    ],
                    tags=["gap-analysis", "fitness"]
                ))

        fitness = 1.0
        # Only High and Medium *from standard analysis* should penalize.
        # Let's count penalties specifically:
        penalty = 0.0
        for prompt in prompts:
            if prompt.title in ["System Desired State Gap", "Codebase Evolutionary State", "Positive fitness trend", "Insufficient history for trend analysis"]:
                continue
            if prompt.priority == Priority.HIGH:
                penalty += 0.3
            elif prompt.priority == Priority.MEDIUM:
                penalty += 0.15

        fitness = max(0.1, fitness - penalty)
        return fitness, prompts


class DebugPerspective(PerspectiveAnalyzer):
    """Analyzes for bugs and issues"""

    def get_perspective(self) -> Perspective:
        return Perspective.DEBUG

    def analyze(self) -> Tuple[float, List[Prompt]]:
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
                acceptance_criteria=["Resolve the reported code quality issue"],
                tags=["code-quality"]
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
                acceptance_criteria=[
                    "Review and commit changes",
                    "Or stash if work in progress"
                ]
            ))

        issue_count = len(all_issues) + len(todos)
        max_issues = 20
        fitness = max(0.1, 1 - (issue_count / max_issues))

        return fitness, prompts

    def _find_todo_comments(self) -> List[dict]:
        """Scan source directories for TODO/FIXME comments"""
        todo_pattern = re.compile(r'#\s*(TODO|FIXME|XXX|HACK|BUG)[\s:]*(.*)', re.IGNORECASE)
        todos = []

        analyses = self.code_analyzer.get_all_analyses()
        for file_path_str in analyses.keys():
            file_path = self.root_dir / file_path_str
            if not file_path.exists():
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
                acceptance_criteria=[
                    f"Address the {todo['type']} comment",
                    "Remove or update the comment after resolution"
                ],
                tags=[todo["type"].lower()]
            ))
