#!/usr/bin/env python3
"""
Self-Development Organism
A system that analyzes codebase state and generates prompts from multiple perspectives.
Inspired by biological development principles and lateral thinking.

This module serves as the main entry point and orchestrator, combining all
sub-modules: models, analyzers, perspectives, diagnostics, and formatters.
"""

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import List

# Re-export all public symbols for backward compatibility
from models import (  # noqa: F401
    ROOT_DIR,
    STATE_FILE,
    REQUIREMENTS_FILE,
    PRINCIPLES_FILE,
    ANALYZABLE_DIRS,
    TEST_DIRS,
    COMPLEXITY_THRESHOLD,
    COVERAGE_TARGET,
    MAX_FILE_LINES,
    MAX_FUNCTION_LINES,
    DevelopmentStage,
    Perspective,
    Priority,
    Prompt,
    FileAnalysis,
    OrganismState,
)
from analyzers import CodeAnalyzer, GitAnalyzer  # noqa: F401
from perspectives import (  # noqa: F401
    PerspectiveAnalyzer,
    TestPerspective,
    SystemPerspective,
)
from user_perspective import UserPerspective  # noqa: F401
from diagnostics import AnalyticsPerspective, DebugPerspective  # noqa: F401

from formatters import PromptFormatter  # noqa: F401


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

        self.state.fitness_scores[perspective.value] = fitness

        print(self.formatter.format_header(perspective, fitness, self.state))

        prompts = sorted(prompts, key=lambda p: p.priority.value)
        if prompts:
            highest = prompts[0].priority
            prompts = [p for p in prompts if p.priority == highest]
            for prompt in prompts:
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

        print(self.formatter.format_summary(self.state, all_prompts))

        return all_prompts

    def advance_generation(self):
        """Advance to next generation"""
        scores = dict(self.state.fitness_scores)
        if scores:
            scores["overall"] = sum(scores.values()) / len(scores)
        self.state.fitness_history.append({
            "generation": self.state.generation,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **scores
        })

        git_analyzer = GitAnalyzer(self.root_dir)
        self.state.last_git_hash = git_analyzer.get_current_hash()

        self.state.generation += 1
        self.state.development_stage = self.state.get_stage().value

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


def main():
    """Main entry point for the self-development system"""
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
    parser.add_argument("--selfdev", action="store_true",
                        help="Analyze the selfdev system itself instead of the project")

    args = parser.parse_args()

    if args.selfdev:
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

    organism.state.save(STATE_FILE)


if __name__ == "__main__":
    main()
