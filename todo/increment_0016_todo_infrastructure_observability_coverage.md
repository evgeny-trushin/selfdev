# Increment 0016: Infrastructure and Observability Coverage

**Requirement ID:** R16
**Status:** TODO

## Description

Selfdev should treat infrastructure, runtime behavior, and logging as first-class parts of development quality. Prompt generation should be able to surface deploy-time risks, configuration drift, missing health checks, missing structured logs, absent metrics, and poor traceability between client actions and backend effects.

This is especially important for long-running debugging, production readiness, and issues that cannot be understood from source code alone.

## Related Principles

- [INF — Infrastructure Readiness](../how/INF.md)
- [OBS — Observability First](../how/OBS.md)
- [NSF — Next-State Feedback](../how/NSF.md)
- [SYS — System Perspective](../how/SYS.md)
- [DBG — Debug Perspective](../how/DBG.md)
- [ANL — Analytics Perspective](../how/ANL.md)
- [G3 — Prioritized](../how/G3.md)
- [M3 — Transparency](../how/M3.md)

## Acceptance Criteria

- [ ] System can generate prompts about environment, configuration, deployment, or migration risks, not only source code changes
- [ ] Prompts can request structured logging, metrics, tracing, or correlation identifiers for important flows
- [ ] Infrastructure and observability gaps can influence system, debug, and analytics prioritization
- [ ] Runtime-critical prompts identify what evidence should appear in logs, metrics, or health signals after the fix
