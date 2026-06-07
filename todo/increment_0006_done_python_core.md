# Increment 0006: Python-Based Core

**Requirement ID:** T1  
**Status:** TODO

## Description

- Python 3.8+ compatible
- Minimal dependencies (use stdlib where possible)
- AST-based code analysis
- JSON state persistence

## Related Principles

- [M1 — Self-Application](../how/M1.md): The system improves its own prompt generation
- [M2 — Bounded Evolution](../how/M2.md): Only modify files in allowed directories
- [B3 — Apoptosis](../how/B3.md): Remove dead code, unused dependencies
- [E1 — Small Mutations](../how/E1.md): Each change is focused and independently testable

## Acceptance Criteria

- [ ] Runs on Python 3.8+
- [ ] No external dependencies beyond stdlib for core
- [ ] AST module is used for code analysis
- [ ] State is persisted as JSON
