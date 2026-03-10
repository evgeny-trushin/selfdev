# Increment 0002: State-Aware Prompt Generation

**Requirement ID:** R2  
**Status:** TODO

## Description

The system must:
- Analyze the current codebase state (files, tests, coverage, complexity)
- Track evolutionary history via Git commits
- Generate contextual prompts based on what has been achieved
- Identify gaps between current state and desired state

## Related Principles

- [G1 — Context-Aware](../principles/G1.md): Every prompt includes current state, metrics, trends
- [G2 — Actionable](../principles/G2.md): Prompts must be immediately actionable
- [G3 — Prioritized](../principles/G3.md): Rank prompts by impact, effort, dependencies
- [G4 — Measurable](../principles/G4.md): Include acceptance criteria in each prompt
- [D1 — Pre-Solution Questioning](../principles/D1.md): Complete internal Q&A before generating
- [D2 — Cognitive Behaviors](../principles/D2.md): Explore multiple approaches, detect conflicts

## Acceptance Criteria

- [ ] System analyzes codebase files, tests, coverage, and complexity
- [ ] Git history is used to track evolutionary state
- [ ] Prompts reflect current state context
- [ ] Gaps between current and desired state are identified
