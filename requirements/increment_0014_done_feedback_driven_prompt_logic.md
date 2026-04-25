# Increment 0014: Feedback-Driven Prompt Logic

**Requirement ID:** R14
**Status:** TODO

## Description

Inspired by OpenClaw-RL, selfdev should treat development artifacts as next-state signals instead of relying only on coarse static summaries. For each generated prompt, the system should prefer observed evidence from user-visible behavior, test output, terminal stderr, API responses, screenshots, diffs, or logs.

Prompt logic should separate:
- evaluative evidence: what indicates success, failure, or non-progress
- directive evidence: what hints at how the previous change or assumption was wrong
- expected next state: what artifact should change once the issue is fixed

This keeps prompts grounded in small, testable details and helps agents focus on the exact corrective move instead of broad advice.

## Related Principles

- [DTL — Detail Fidelity](../principles/DTL.md)
- [NSF — Next-State Feedback](../principles/NSF.md)
- [G1 — Context-Aware](../principles/G1.md)
- [G2 — Actionable](../principles/G2.md)
- [G4 — Measurable](../principles/G4.md)
- [E1 — Small Mutations](../principles/E1.md)
- [M3 — Transparency](../principles/M3.md)

## Acceptance Criteria

- [ ] Prompt logic can reference at least one concrete observed artifact for a detected issue
- [ ] Prompts distinguish current evidence, suspected corrective direction, and expected verification state
- [ ] Prompts stay small enough to map to a single focused change or tightly related set of files
- [ ] Missing evidence produces a "collect signal first" prompt instead of a speculative fix prompt
