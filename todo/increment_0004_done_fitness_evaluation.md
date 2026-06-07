# Increment 0004: Fitness Evaluation

**Requirement ID:** R4  
**Status:** TODO

## Description

Each perspective evaluates fitness differently:

| Perspective | Primary Fitness Metrics |
|------------|-------------------------|
| User | Usability, documentation quality, user experience elements |
| Test | Code coverage, mutation score, test pass rate, data integrity validation |
| System | Complexity, coupling, cohesion, infrastructure health, configuration consistency |
| Analytics | Feature adoption, user retention, error rate trends, usage patterns |
| Debug | Error count, broken integrations, stale data, deployment failures, infrastructure drift |

## Related Principles

- [B1 — Morphogenesis](../how/B1.md): Priority gradients from critical to nice-to-have
- [B2 — Differentiation](../how/B2.md): Perspectives specialize over generations
- [G3 — Prioritized](../how/G3.md): Rank by impact, effort, dependencies
- [G4 — Measurable](../how/G4.md): Specific metric thresholds
- [USR — User Perspective](../how/USR.md)
- [TST — Test Perspective](../how/TST.md)
- [SYS — System Perspective](../how/SYS.md)
- [ANL — Analytics Perspective](../how/ANL.md)
- [DBG — Debug Perspective](../how/DBG.md)

## Acceptance Criteria

- [ ] Each perspective computes its own fitness metrics
- [ ] Fitness scores are numeric and comparable
- [ ] Metric definitions match the table above
