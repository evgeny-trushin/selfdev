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

        # Analytics | Feature adoption, user retention, error rate trends, usage patterns
        metrics = {
            "feature_adoption": 0.5,
            "user_retention": 0.5,
            "error_rate_trends": 0.5,
            "usage_patterns": 0.5
        }

        history = self.state.fitness_history

        if len(history) < 2:
            return metrics, [Prompt(
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

        error_trend_fitness = 1.0
        for prompt in prompts:
            if prompt.priority == Priority.HIGH:
                error_trend_fitness -= 0.3
            elif prompt.priority == Priority.MEDIUM:
                error_trend_fitness -= 0.15

        metrics["error_rate_trends"] = max(0.1, error_trend_fitness)

        # In absence of real telemetry, default other metrics to mirror error trend
        # so overall fitness matches the error_trend_fitness
        metrics["feature_adoption"] = metrics["error_rate_trends"]
        metrics["user_retention"] = metrics["error_rate_trends"]
        metrics["usage_patterns"] = metrics["error_rate_trends"]

        return metrics, prompts


class DebugPerspective(PerspectiveAnalyzer):
    """Analyzes for bugs and issues"""

    def get_perspective(self) -> Perspective:
        return Perspective.DEBUG

    def analyze(self) -> Tuple[Dict[str, float], List[Prompt]]:
        prompts = []

        # Debug | Error count, broken integrations, stale data, deployment failures, infrastructure drift
        metrics = {
            "error_count": 0.5,
            "broken_integrations": 0.5,
            "stale_data": 0.5,
            "deployment_failures": 0.5,
            "infrastructure_drift": 0.5
        }

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
        fitness = max(0.1, 1.0 - (issue_count / max_issues))
        metrics["error_count"] = fitness

        # Set other metrics to mirror overall fitness for debug perspective
        metrics["broken_integrations"] = fitness
        metrics["stale_data"] = fitness
        metrics["deployment_failures"] = fitness
        metrics["infrastructure_drift"] = fitness

        return metrics, prompts

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
