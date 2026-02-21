# Increment 0011: Reliability

**Requirement ID:** N2  
**Status:** TODO

## Description

- Graceful handling of missing files
- Safe defaults for new projects
- Rollback capability on failures

## Related Principles

- [B3 — Apoptosis](../principles/B3.md): Remove what doesn't serve the organism
- [B4 — Feedback Loops](../principles/B4.md): Increasing error rates trigger debug prompts
- [E2 — Selection Pressure](../principles/E2.md): All tests must pass, no regressions
- [E1 — Small Mutations](../principles/E1.md): Rollback should be easy

## Acceptance Criteria

- [ ] Missing files are handled gracefully (no crashes)
- [ ] New projects get safe default values
- [ ] Failures can be rolled back
