# Increment 0016: Infrastructure and Observability Coverage

**Requirement ID:** R16
**Status:** TODO

## Description

Selfdev should treat infrastructure, runtime behavior, and logging as first-class parts of development quality. Prompt generation should be able to surface deploy-time risks, configuration drift, missing health checks, missing structured logs, absent metrics, and poor traceability between client actions and backend effects.

This is especially important for long-running debugging, production readiness, and issues that cannot be understood from source code alone.

## Related Principles

- [INF — Infrastructure Readiness](../principles/INF.md)
- [OBS — Observability First](../principles/OBS.md)
- [NSF — Next-State Feedback](../principles/NSF.md)
- [SYS — System Perspective](../principles/SYS.md)
- [DBG — Debug Perspective](../principles/DBG.md)
- [ANL — Analytics Perspective](../principles/ANL.md)
- [G3 — Prioritized](../principles/G3.md)
- [M3 — Transparency](../principles/M3.md)

## Acceptance Criteria

- [ ] System can generate prompts about environment, configuration, deployment, or migration risks, not only source code changes
- [ ] Prompts can request structured logging, metrics, tracing, or correlation identifiers for important flows
- [ ] Infrastructure and observability gaps can influence system, debug, and analytics prioritization
- [ ] Runtime-critical prompts identify what evidence should appear in logs, metrics, or health signals after the fix
