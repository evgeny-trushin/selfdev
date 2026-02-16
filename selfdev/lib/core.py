from datetime import datetime, timezone
from pathlib import Path
from typing import List

from .models import (
    OrganismState,
    Perspective,
    Prompt
)
from .perspectives import (
    UserPerspective,
    TestPerspective,
    SystemPerspective,
    AnalyticsPerspective,
    DebugPerspective
)
from .formatter import PromptFormatter
from .analyzers import GitAnalyzer
from .constants import (
    ROOT_DIR,
    STATE_FILE
)

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
