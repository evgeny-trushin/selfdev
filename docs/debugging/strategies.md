# Debugging Strategies for Multi-Agent AI Coding

This file consolidates the techniques from all source reports in this directory:

- `claude_sonnet_4_6_20260524_113514.md`
- `gemini.md`
- `openai_chatgpt_5_4_agent_20260524_113651.md`
- `openai_chatgpt_5_5_pro_research_20260524_113658.md`
- `perplexity_20260524_113620.md`
- `qwen_20260524_113526.md`

Popularity is the number of source reports that mention the technique family. Items with the same popularity are ordered by practical importance in the reports and by whether they appear in recommendations, roadmaps, or feature inventories.

`UNIQUE` highlights techniques that appear in only one or two reports, or that are unusually specific compared with the shared consensus.

## 6/6 - Core Consensus Techniques

1. **Change provenance ledger** - Popularity: 6/6. Record every meaningful agent action as a queryable change object with `agent_id`, `task_id`, timestamps, inputs observed, outputs produced, files touched, test evidence, risk status, and causal links. This is the main answer to "who changed what, why, and with what evidence?"

2. **Multi-granularity attribution** - Popularity: 6/6. Extend attribution beyond commits to lines, AST nodes, functions, components, tests, routes, schemas, dependencies, prompts, configs, and runtime effects. The goal is to answer ownership questions at the level where the bug is actually observed.

3. **Agent state JSON snapshots** - Popularity: 6/6. Persist structured state at each meaningful step: identity, role, goal, subgoal, files read, commands run, browser actions, screenshots, errors, assumptions, confidence, risk, prompt context, memory reads, and tests selected or skipped.

4. **State diffs beyond file diffs** - Popularity: 6/6. Compare reasoning state, task state, browser state, test state, DB state, dependency state, and prompt context between steps or agents. This exposes drift, dropped assumptions, and behavior changes that a git diff cannot show.

5. **Event-sourced action and observation log** - Popularity: 6/6. Store every observation, tool call, file edit, browser action, test run, handoff, and human intervention as an append-only event. The event log becomes the replayable history of the agent run.

6. **OpenTelemetry / GenAI tracing** - Popularity: 6/6. Emit standardized spans for user requests, agent invocations, tool calls, file reads/writes, tests, browser actions, CI steps, and human review. Use GenAI attributes for model, prompt, tokens, tool type, agent identity, and operation name.

7. **Correlation IDs across the whole lifecycle** - Popularity: 6/6. Propagate IDs from user request to task, agent, step, patch, commit, test run, trace, deployment, and incident. This lets a reviewer jump from a production failure back to the exact agent step that caused it.

8. **Semantic and AST diffing** - Popularity: 6/6. Use tree-sitter, GumTree, Difftastic, diffsitter, RefactoringMiner-style logic, type checkers, or compiler information to identify structural changes, moves, refactors, signature changes, data-flow changes, and behavior changes instead of raw line churn.

9. **Intent-grouped diffs** - Popularity: 6/6. Group changes by bug fix, refactor, test addition, UI copy, layout, API contract change, dependency update, generated boilerplate, rollback, speculative experiment, or conflict resolution. This makes multi-agent PRs reviewable by purpose, not by file order.

10. **Playwright trace integration** - Popularity: 6/6. Attach Playwright traces to relevant changes and tests. Use action timelines, DOM snapshots, screenshots, network logs, console logs, source panels, videos, and metadata as evidence for what actually happened in the browser.

11. **Browser, DOM, and accessibility snapshots as evidence** - Popularity: 6/6. Capture DOM snapshots, accessibility tree snapshots, screenshots, storage state, console output, and network slices before and after changes. These artifacts connect code edits to user-facing behavior.

12. **Visual provenance overlays** - Popularity: 6/6. Overlay changed UI regions with agent colors, change-type patterns, confidence/risk badges, and links to source files, tasks, tests, and traces. Use a toggle so provenance is inspectable without permanently cluttering the app.

13. **"Why did this change?" panel** - Popularity: 6/6. For a file, line, component, route, or UI element, show the responsible agent, triggering task, observed evidence, reasoning summary, related tests, verification status, and downstream impact.

14. **Before/after screenshots and semantic visual diffs** - Popularity: 6/6. Capture visual baselines for touched routes or stories, then label differences as text, layout, color, spacing, component replacement, direct edit, or indirect side effect.

15. **Hidden consequence overlay** - Popularity: 6/6. Highlight changes that may not alter pixels: event handlers, ARIA labels, keyboard focus, network calls, analytics events, validation rules, permissions, telemetry payloads, and auth boundaries.

16. **Timeline playback of UI and agent evolution** - Popularity: 6/6. Provide a scrubbable timeline or filmstrip showing the UI, files, tests, and state at each agent step. This helps reconstruct the sequence that produced a regression.

17. **Agent conversation timeline and role swimlanes** - Popularity: 6/6. Show planner, builder, tester, reviewer, critic, and debugger lanes with collapsed summaries, expandable messages, tool calls, state links, and handoff arrows.

18. **Task handoff records** - Popularity: 6/6. When one agent delegates to another, persist the subtask, inputs, expected output, snapshot refs, status, and resulting changes. This prevents lost context at collaboration boundaries.

19. **Causal DAG and task graph** - Popularity: 6/6. Model tasks, subtasks, changes, tests, traces, deployments, and incidents as a graph. This supports questions like "which tests depend on this file?" and "what downstream changes break if this step is reverted?"

20. **Branch, worktree, or sandbox per agent** - Popularity: 6/6. Isolate parallel agents in separate branches, git worktrees, containers, VMs, browsers, and databases. This prevents silent overwrites and makes conflicts explicit at merge time.

21. **Automatic checkpoints and savepoints** - Popularity: 6/6. Create named restore points before risky actions, after subgoals, before tests, before migrations, and before dependency changes. Store enough state to inspect or roll back the action later.

22. **Deterministic replay** - Popularity: 6/6. Replay recorded prompts, model outputs, tool calls, terminal output, browser actions, and state snapshots without re-calling external services. This makes non-deterministic agent paths inspectable.

23. **Causal rollback and rollback-by-task** - Popularity: 6/6. Revert a causal chain, not just a file. A rollback should preview dependent changes, tests, UI regions, migrations, and other agents' work before applying the revert.

24. **Alternative solution comparison** - Popularity: 6/6. Run or preserve competing agent solutions side by side, compare their diffs, traces, tests, risks, and assumptions, then select one or merge the best semantic clusters.

25. **Partial merge / semantic cherry-pick** - Popularity: 6/6. Merge at the level of intent groups, AST subtrees, tests, or components rather than whole files. This supports taking one agent's API fix and another agent's tests without manual patch surgery.

26. **Conflict maps and resolution views** - Popularity: 6/6. Detect and display conflicts across files, AST nodes, UI regions, tests, dependencies, schemas, routes, prompts, and assumptions. Show evidence for each side before a human or mediator agent resolves it.

27. **Disagreement and duplicate-work detection** - Popularity: 6/6. Detect agents pursuing the same task, editing the same region, or making contradictory assumptions. Surface duplicate work early to reduce wasted cycles and hidden divergence.

28. **Prompt, context, and memory inspector** - Popularity: 6/6. Expose which user instructions, system constraints, memories, files, docs, prior errors, and examples were included or ignored in each agent step.

29. **Context drift, stale memory, and hallucinated fact detection** - Popularity: 6/6. Compare retrieved memories and assertions against current repo state, trusted docs, and actual tool results. Flag stale context and unsupported invented facts before they influence code.

30. **Assumption ledger** - Popularity: 6/6. Require agents to record important assumptions and mark them as validated, contradicted, obsolete, or still unverified. This helps explain why a plausible patch later failed.

31. **Risk, confidence, and uncertainty indicators** - Popularity: 6/6. Show risk and confidence per change group, file, UI element, test, assumption, and explanation. Risk should derive from blast radius, critical paths, security relevance, dependency changes, migrations, and missing tests.

32. **Evidence-quality scoring** - Popularity: 6/6. Grade claims by the strength of their evidence: direct passing tests, trace coverage, visual diffs, accessibility checks, security scans, benchmarks, docs, or only inference. Avoid treating model confidence as proof.

33. **Evidence-rich PR review workspace** - Popularity: 6/6. Review AI changes through summaries linked to receipts: semantic diff groups, provenance badges, Playwright traces, screenshots, test cards, risk banners, and raw logs.

34. **Unsupported-claim warnings** - Popularity: 6/6. Flag summary claims that lack matching code changes, tests, traces, docs, benchmarks, or other evidence. This prevents agent-written PR descriptions from hiding weak verification.

35. **Reviewer checklists and reviewer question suggestions** - Popularity: 6/6. Generate targeted review prompts from change intent and risk, such as auth checks for permission diffs, migration checks for schema changes, or mobile checks for layout changes.

36. **Test coverage overlays and changed-region warnings** - Popularity: 6/6. Overlay tested, partially tested, and untested regions on the UI and PR. Flag changed UI regions or code paths that have no matching test trace or assertion.

37. **Agent-to-test mapping** - Popularity: 6/6. Record which agent wrote, selected, modified, skipped, or relied on each test. Link tests to changed components and explain whether they actually exercise the modified behavior.

38. **Regression blame attribution** - Popularity: 6/6. Correlate failing tests, browser traces, CI output, production incidents, and deploy IDs back to the responsible task, agent, step, patch, or assumption.

39. **Accessibility, security, and privacy diff panels** - Popularity: 6/6. Diff ARIA roles, labels, focus order, keyboard navigation, color contrast, auth paths, permission boundaries, PII flows, telemetry, cookies, and retention policies.

40. **API, schema, route, dependency, and feature-flag diffs** - Popularity: 6/6. Treat contracts and operational configuration as first-class debug surfaces. Show breaking API changes, migration effects, route changes, lockfile impact, and rollout audience changes.

41. **Runtime behavior and performance diffs** - Popularity: 6/6. Compare latency, memory, CPU, bundle size, logs, traces, analytics events, and other runtime effects before and after an agent change.

42. **Security taint, secret, and prompt-injection scans** - Popularity: 6/6. Track untrusted inputs to sinks, scan prompts and logs for secrets, flag prompt-injection exposure, and detect new insecure flows introduced by agent-written code.

43. **Deployment-readiness report** - Popularity: 6/6. Summarize risk, test coverage, visual evidence, accessibility/security results, unresolved conflicts, required approvals, rollback plan, and outstanding assumptions before merging or deploying.

44. **Human approval gates** - Popularity: 6/6. Require explicit human approval for high-risk actions such as protected-branch writes, auth changes, migrations, payment code, dependency upgrades, production deploys, or low-evidence changes.

45. **Metrics dashboards and error budgets for agents** - Popularity: 6/6. Track token cost, latency, tool-call failures, regression rate, accepted changes, rollback rate, review time, flakiness, and error budgets per agent, task type, or subsystem.

46. **Audit logs and cryptographic provenance** - Popularity: 6/6. Preserve signed or tamper-evident records for agent actions, change bundles, generated artifacts, data flows, and approvals. This supports compliance and forensic debugging.

47. **Trust calibration and evaluation metrics** - Popularity: 6/6. Measure time to understand a change, time to identify regression cause, time to approve, hidden regressions caught, unsupported claims caught, attribution accuracy, rollback speed, and false confidence rate.

## 5/6 - Very Common Techniques

48. **Natural-language test explanations** - Popularity: 5/6. Generate bounded explanations of what each test asserts and what behavior it does not cover. This helps reviewers detect tests that pass but fail to prove the changed behavior.

49. **Missing negative-test and edge-case detection** - Popularity: 5/6. Detect absent tests for invalid input, loading states, empty states, permission states, mobile viewports, error paths, and accessibility cases. This counters happy-path-only agent testing.

50. **Generated-code indicators and watermarking** - Popularity: 5/6. Mark generated regions, files, or patches with provenance metadata so later reviewers can see what was AI-authored and apply the right review standard.

51. **Agent heatmaps and hotspot views** - Popularity: 5/6. Visualize which files, components, routes, or UI regions each agent touched most. Use this to spot overloaded areas, unexpected ownership, or duplicate work.

52. **User-journey graphs** - Popularity: 5/6. Turn end-to-end traces into route/state graphs that show which user journeys were exercised and which changed regions were missed.

53. **Flakiness visualization** - Popularity: 5/6. Track pass/fail history, retry traces, timing variance, and locator instability so reviewers can separate genuine regressions from brittle tests.

## 4/6 - Common But More Specialized Techniques

54. **Database migration replay and rollback simulation** - Popularity: 4/6. Rehearse migrations on a shadow database, preview data loss and dependent code impact, and attach migration evidence to the review.

55. **Context-window hygiene and memory pruning** - Popularity: 4/6. Inspect oversized prompt context, remove stale memories, and warn when summarization or context compaction drops critical constraints.

56. **Visual or browser trace comparison** - Popularity: 4/6. Compare a failing browser trace to a passing trace, or compare two agent runs side by side, to locate the exact action, DOM change, redirect, or network call that diverged.

57. **Runtime-effect attribution into production observability** - Popularity: 4/6. Connect deployed agent-authored changes to production metrics, logs, alerts, incidents, feature flags, and runtime traces.

## 3/6 - Useful Niche UX Techniques

58. **Reviewer canvas notes and UI annotations** - Popularity: 3/6. Let reviewers pin notes directly to UI regions, components, or diff groups, then link those notes back to agent actions and review decisions.

59. **Change explainer for non-developers** - Popularity: 3/6. Produce evidence-linked summaries for PMs, designers, QA, security, or compliance reviewers without hiding the detailed technical trace.

60. **Adaptive information density** - Popularity: 3/6. Show high-level summaries by default, but expand automatically for risky, low-evidence, or conflict-heavy changes. The UI should not force all users through raw logs.

## 2/6 - Distinctive Techniques

61. **UNIQUE: OpenLineage-style cross-system lineage** - Popularity: 2/6. Reuse data-lineage patterns to connect code changes to jobs, datasets, dashboards, analytics events, and downstream data products.

62. **UNIQUE: Symbolic chronicle embedding** - Popularity: 2/6. Embed signed, timestamped provenance records inside generated content or adjacent metadata so contribution history survives later transformations.

63. **UNIQUE: Browser trace comparator** - Popularity: 2/6. Provide a dedicated comparator for two browser traces, especially passing vs failing runs or agent A vs agent B solutions.

64. **UNIQUE: Cross-tool provenance export / attestation** - Popularity: 2/6. Export signed change bundles containing patches, traces, screenshots, approvals, tests, and policy decisions for audits or incident reviews.

## 1/6 - Unique Debugging Techniques

65. **UNIQUE: Information Flow Control and FIDES variable isolation** - Popularity: 1/6. Label data by trust level and prevent untrusted or sensitive content from flowing into privileged tools, shell commands, SQL execution, or unsafe prompt contexts.

66. **UNIQUE: PIBT and negotiation-token deadlock handling** - Popularity: 1/6. Detect wait-for cycles between agents and use priority inheritance, backtracking, role hierarchy, or negotiation budgets to break collaboration deadlocks deterministically.

67. **UNIQUE: Bot sponsorship enforcement** - Popularity: 1/6. Require every AI-authored PR or commit to have a named human sponsor responsible for review and accountability.

68. **UNIQUE: Audit-as-Code readiness scoring** - Popularity: 1/6. Treat traceability, explainability, evidence completeness, and approval state as machine-checkable deployment gates.

69. **UNIQUE: Collective agent conscience** - Popularity: 1/6. Maintain a shared belief and assumption store across agents so conflicts become explicit social or governance events instead of hidden divergent context.

70. **UNIQUE: Human-in-the-loop patch editor** - Popularity: 1/6. Let a human edit an agent patch in a structured AST-aware interface without restarting the whole agent run.

71. **UNIQUE: Plugin ecosystem for custom diff types** - Popularity: 1/6. Allow domain-specific plugins for shader diffs, analytics diffs, policy diffs, schema diffs, visual tests, or specialized compliance checks.

72. **UNIQUE: Memory pruning suggestions** - Popularity: 1/6. Recommend stale or low-value memories for removal or refresh based on usage, age, contradiction rate, and current repo state.

73. **UNIQUE: Safe sandbox runner for risky actions** - Popularity: 1/6. Route dangerous commands, database migrations, dependency upgrades, and production-like tests through isolated environments with scoped credentials and replayable outputs.

74. **UNIQUE: Trust calibration surveys as product telemetry** - Popularity: 1/6. Use structured reviewer feedback to detect whether the debugging UI creates over-trust, under-trust, or accurate trust in agent changes.

## Practical Takeaway

The reports converge on one architecture: every agent action should be treated simultaneously as a distributed-systems event, a code-review artifact, and a user-facing behavior change. The highest-return starting point is a minimal provenance ledger with stable IDs, state snapshots, OpenTelemetry spans, Playwright traces, semantic diff grouping, evidence cards, and worktree or sandbox isolation. The unique techniques are mostly governance and safety extensions that become valuable once the foundational traceability layer exists.
