# Debugging Strategy Agents

This directory contains one agent design for each strategy in `../strategies.md`. Each file is intentionally focused on one debugging strategy. Shared operating rules live here so the agent files do not repeat the same boilerplate.

## Shared Operating Contract

Every debugging strategy agent must:

1. Start from evidence, not model confidence.
2. Preserve stable IDs: `user_request_id`, `task_id`, `agent_id`, `step_id`, `change_id`, `patch_id`, `commit_sha`, `test_run_id`, `trace_id`, and `deployment_id` when they exist.
3. Distinguish direct evidence, inferred evidence, missing evidence, and unsupported claims.
4. Record all artifact references as paths, URLs, hashes, trace IDs, screenshots, logs, or test names.
5. Avoid destructive actions unless the caller explicitly asks for them and the rollback impact is known.
6. Escalate to a human when the target touches auth, payments, production data, migrations, secrets, permissions, privacy, compliance, or protected branches.
7. Report unknown ownership or missing evidence as unknown; never invent attribution.
8. Prefer narrow findings with exact files, routes, tests, steps, spans, screenshots, or ledger IDs.
9. Handoff to related agents when the question crosses strategy boundaries.
10. End with a verification checklist that states what was checked and what remains unverified.

## Standard Output Shape

Each agent should produce:

- `summary`: one paragraph explaining the finding or decision.
- `evidence`: concrete artifact references and why each matters.
- `status`: `verified`, `partially_verified`, `inferred`, `blocked`, or `unsupported`.
- `risk`: `low`, `medium`, `high`, or `critical`, with reason.
- `handoffs`: related agents that should continue the investigation.
- `next_actions`: exact checks, tests, traces, reviews, or approvals needed.

## Standard Investigation Order

1. Identify the question and target artifact.
2. Collect raw evidence before reading summaries.
3. Join evidence by stable IDs.
4. Apply the agent-specific decision rules.
5. Record missing evidence explicitly.
6. Produce the standard output shape.

## File Naming

Files use the same ranking as `../strategies.md`:

- `001-change-provenance-ledger-agent.md`
- `002-multi-granularity-attribution-agent.md`
- ...
- `074-trust-calibration-surveys-as-product-telemetry-agent.md`
