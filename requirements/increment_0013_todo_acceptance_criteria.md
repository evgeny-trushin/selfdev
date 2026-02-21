# Increment 0013: Acceptance Criteria

**Requirement ID:** AC  
**Status:** TODO

## Description

The system is considered "fit" when:
1. All perspectives can run independently
2. Prompts generated are actionable
3. State persists between runs
4. Fitness scores are calculated correctly
5. No unhandled exceptions during normal operation

## Related Principles

- [E2 — Selection Pressure](../principles/E2.md): Only accept changes that improve fitness
- [G4 — Measurable](../principles/G4.md): Specific metric thresholds and tests to pass
- [G2 — Actionable](../principles/G2.md): Prompts must be immediately actionable
- [M3 — Transparency](../principles/M3.md): Expected outcomes are documented

## Verification

- [ ] `develop.sh --user` runs without error
- [ ] `develop.sh --test` runs without error
- [ ] `develop.sh --system` runs without error
- [ ] `develop.sh --analytics` runs without error
- [ ] `develop.sh --debug` runs without error
- [ ] `organism_state.json` persists between runs
- [ ] Fitness scores are numeric
- [ ] No unhandled exceptions in normal operation
