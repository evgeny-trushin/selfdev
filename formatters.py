"""
Output formatting for the Self-Development Organism system.
"""

from collections import defaultdict
from typing import List

from models import (
    OrganismState,
    Perspective,
    Priority,
    Prompt,
)


class PromptFormatter:
    """Formats prompts for console output (plain text, no ANSI colors — see principle CLN).

    Accepts an optional *templates* dict to override default format strings.
    Supported keys:
      - ``prompt_title``:  "{priority} {title}"
      - ``header_title``:  "PERSPECTIVE: {perspective}"
      - ``summary_title``: "SUMMARY"
    """

    def __init__(self, templates: dict = None):
        self.templates = templates or {}

    def format_prompt(self, prompt: Prompt, fitness: float = None) -> str:
        """Format a single prompt with state context and actionable details"""
        lines = []

        priority_str = prompt.priority.name
        title_tpl = self.templates.get("prompt_title", "[{priority}] {title}")
        lines.append(title_tpl.format(priority=priority_str, title=prompt.title))

        # State context: perspective and fitness (principle G1)
        context_parts = [f"Perspective: {prompt.perspective.value}"]
        if fitness is not None:
            context_parts.append(f"Fitness: {fitness:.0%}")
        lines.append(f"  ({', '.join(context_parts)})")

        lines.append(f"  {prompt.description}")

        if prompt.file_path:
            loc = prompt.file_path
            if prompt.line_number:
                loc += f":{prompt.line_number}"
            lines.append(f"  Location: {loc}")

        if prompt.metric_current is not None and prompt.metric_target is not None:
            lines.append(f"  Current: {prompt.metric_current:.1f} -> Target: {prompt.metric_target:.1f}")

        # Layer information
        if getattr(prompt, "layer", None):
            lines.append(f"  Layer: {prompt.layer.value}")
        if getattr(prompt, "affected_view", None):
            lines.append(f"  Affected View: {prompt.affected_view}")
        if getattr(prompt, "route", None):
            lines.append(f"  Route: {prompt.route}")
        if getattr(prompt, "contract", None):
            lines.append(f"  Contract: {prompt.contract}")
        if getattr(prompt, "state_transition", None):
            lines.append(f"  State Transition: {prompt.state_transition}")
        if getattr(prompt, "ui_details", None):
            lines.append(f"  UI Details: {prompt.ui_details}")
        if getattr(prompt, "client_details", None):
            lines.append(f"  Client Details: {prompt.client_details}")
        if getattr(prompt, "service_details", None):
            lines.append(f"  Service Details: {prompt.service_details}")
        if getattr(prompt, "boundary_details", None):
            lines.append(f"  Boundary Details: {prompt.boundary_details}")

        # Transparency: why this prompt was generated (principle M3)
        if prompt.reason:
            lines.append(f"  Reason: {prompt.reason}")

        if prompt.evaluative_evidence:
            lines.append(f"  Evaluative Evidence: {prompt.evaluative_evidence}")
        if prompt.directive_evidence:
            lines.append(f"  Directive Evidence: {prompt.directive_evidence}")
        if prompt.expected_next_state:
            lines.append(f"  Expected Next State: {prompt.expected_next_state}")

        if prompt.acceptance_criteria:
            lines.append("  Acceptance Criteria:")
            for criterion in prompt.acceptance_criteria:
                lines.append(f"    - {criterion}")

        return "\n".join(lines)

    def format_header(self, perspective: Perspective, fitness: float, state: OrganismState) -> str:
        """Format the header for a perspective"""
        stage = state.get_stage()
        header_tpl = self.templates.get(
            "header_title", "PERSPECTIVE: {perspective}")

        lines = [
            "",
            "=" * 60,
            f"  {header_tpl.format(perspective=perspective.value.upper())}",
            f"  Generation: {state.generation}  |  Stage: {stage.value}",
            f"  Fitness: {fitness:.2%}",
            "=" * 60,
            ""
        ]
        return "\n".join(lines)

    def format_summary(self, state: OrganismState, all_prompts: List[Prompt]) -> str:
        """Format a summary of all prompts"""
        summary_title = self.templates.get("summary_title", "SUMMARY")
        lines = [
            "",
            "-" * 60,
            f"  {summary_title}",
            "-" * 60,
            f"  Total Prompts: {len(all_prompts)}",
        ]

        by_priority = defaultdict(int)
        for p in all_prompts:
            by_priority[p.priority] += 1

        for priority in Priority:
            if by_priority[priority] > 0:
                lines.append(f"    {priority.name}: {by_priority[priority]}")

        if state.fitness_scores:
            overall = sum(state.fitness_scores.values()) / len(state.fitness_scores)
            lines.append(f"\n  Overall Fitness: {overall:.2%}")

        lines.append("-" * 60)
        return "\n".join(lines)
