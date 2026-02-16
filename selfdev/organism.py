#!/usr/bin/env python3
"""
Self-Development Organism
A system that analyzes codebase state and generates prompts from multiple perspectives.
Inspired by biological development principles and lateral thinking.
"""

from pathlib import Path
from typing import List, Tuple

# Re-export from library modules for backward compatibility
try:
    from lib.constants import (
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
    )
    from lib.models import (
        DevelopmentStage,
        Perspective,
        Priority,
        Prompt,
        FileAnalysis,
        OrganismState,
    )
    from lib.analyzers import (
        CodeAnalyzer,
        GitAnalyzer,
    )
    from lib.perspectives import (
        PerspectiveAnalyzer,
        UserPerspective,
        TestPerspective,
        SystemPerspective,
        AnalyticsPerspective,
        DebugPerspective,
    )
    from lib.formatter import PromptFormatter
    from lib.core import SelfDevelopmentOrganism
except ImportError:
    # Handle case where run as module or from different context
    from .lib.constants import (
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
    )
    from .lib.models import (
        DevelopmentStage,
        Perspective,
        Priority,
        Prompt,
        FileAnalysis,
        OrganismState,
    )
    from .lib.analyzers import (
        CodeAnalyzer,
        GitAnalyzer,
    )
    from .lib.perspectives import (
        PerspectiveAnalyzer,
        UserPerspective,
        TestPerspective,
        SystemPerspective,
        AnalyticsPerspective,
        DebugPerspective,
    )
    from .lib.formatter import PromptFormatter
    from .lib.core import SelfDevelopmentOrganism


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
        # If running from inside selfdev/, root is this dir
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
