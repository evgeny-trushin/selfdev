# Increment 0008: State Persistence

**Requirement ID:** T3  
**Status:** TODO

## Description

- `organism_state.json` for tracking evolution
- Git integration for history
- Generation counting
- Fitness history recording

## Related Principles

- [E3 — Memory](../principles/E3.md): Track which prompts led to improvements
- [M3 — Transparency](../principles/M3.md): All decisions are logged
- [B4 — Feedback Loops](../principles/B4.md): Use historical data for stability and growth signals
- [G1 — Context-Aware](../principles/G1.md): State informs prompt generation context

## Acceptance Criteria

- [ ] `organism_state.json` stores evolutionary state
- [ ] Git commits are used for history tracking
- [ ] Generation number increments correctly
- [ ] Fitness history is recorded per generation
