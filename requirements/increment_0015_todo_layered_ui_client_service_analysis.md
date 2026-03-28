# Increment 0015: Layered UI and Client-Service Analysis

**Requirement ID:** R15
**Status:** TODO

## Description

Selfdev should analyze features as end-to-end flows, not isolated files. A user-facing issue may originate in UI state handling, client state and network behavior, service logic, or a mismatch between those layers.

The system should be able to generate prompts that explicitly cover:
- UI details: layout, copy, responsiveness, accessibility, empty/loading/error/success states
- client behavior: data fetching, local state, optimistic updates, retries, and error rendering
- service behavior: API contract, validation, business rules, persistence, and background jobs
- boundary mismatches: schema drift, status-code mismatch, field naming drift, and stale assumptions

## Related Principles

- [UIX — UI State Coverage](../principles/UIX.md)
- [CSV — Client-Service Contract Integrity](../principles/CSV.md)
- [DTL — Detail Fidelity](../principles/DTL.md)
- [NSF — Next-State Feedback](../principles/NSF.md)
- [USR — User Perspective](../principles/USR.md)
- [SYS — System Perspective](../principles/SYS.md)
- [DBG — Debug Perspective](../principles/DBG.md)

## Acceptance Criteria

- [ ] Prompts can identify whether an issue is UI-only, service-only, or cross-layer
- [ ] UI prompts mention the affected view or component and the state transition that must be verified
- [ ] Client-service prompts mention the route, contract, or error path to inspect
- [ ] Cross-layer issues are not considered complete until both caller and callee behavior are verified
