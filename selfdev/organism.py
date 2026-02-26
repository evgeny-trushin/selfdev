    def run_perspective(self, perspective: Perspective, print_results: bool = True) -> List[Prompt]:
        """Run analysis from a specific perspective.

        When *print_results* is True (default / single-perspective mode),
        prompts are filtered to the highest priority found within this
        perspective and printed immediately.

        When *print_results* is False (batch mode used by
        *run_all_perspectives*), no output is produced — the caller is
        responsible for global filtering and printing.
        """
        # Handle potential enum mismatch (e.g. from different import paths in tests)
        # This fallback allows tests to use 'selfdev.models.Perspective' even if
        # this module uses 'models.Perspective' (via relative import)
        if perspective not in self.perspectives:
            for key in self.perspectives:
                if key.value == perspective.value:
                    perspective = key
                    break

        analyzer = self.perspectives[perspective]
        fitness, prompts = analyzer.analyze()

        self.state.fitness_scores[perspective.value] = fitness

        prompts = sorted(prompts, key=lambda p: p.priority.value)

        if print_results:
            print(self.formatter.format_header(perspective, fitness, self.state))
            if prompts:
                highest = prompts[0].priority
                filtered = [p for p in prompts if p.priority == highest]
                for prompt in filtered:
                    print(self.formatter.format_prompt(prompt))
                    print()
            else:
                print("  No issues found from this perspective.")

        return prompts
