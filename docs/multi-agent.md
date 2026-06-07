# Multi-Agent Support Strategy for Selfdev

## Short Answer

Selfdev can support multi-agent work best as a managed queue system:

1. Multiple agents may read the repository, `how/`, `todo/`, git history, tests, and docs in parallel.
2. One planning authority writes official numbered increment files in `todo/`.
3. One execution authority writes production code for the current increment.
4. Review, knowledge, and test agents produce reports, not direct code changes.
5. The reducer is deterministic where possible: tests, parser checks, queue state, commit diff, and `./develop.sh --advance`.

The right strategy is not a flat swarm of agents editing the same repo. The right strategy is map-reduce-and-manage: parallel read-heavy agents, structured reduction into a single `todo/` queue, and a single writer for code changes.

## Current Repo Fit

Selfdev already has the core primitives needed for this pattern.

- `todo/` is the durable queue. `increment_tracker.py` selects the lowest numbered `_todo_` file as the current increment.
- `how/` is the durable knowledge base. Increment files reference these principles and the prompt formatter injects them into the execution prompt.
- `develop.sh` and `organism.py` provide the execution loop: show current increment, run tests before advance, rename `_todo_` to `_done_`, update `organism_state.json`, then show the next increment.
- `.github/agents/`, `.claude/agents/`, and `.codex/agents/` already describe specialized roles: knowledge analysis, planning, and doing.
- `docs/multi-agents/` already contains research supporting the same conclusion: parallel exploration is useful, parallel writes are risky, and coding systems need a managed write path.

There are also gaps that matter before true concurrent use.

- The current tracker is filename-driven and has no file lock or lease mechanism.
- Default `./develop.sh` is stateful. If the current increment was already shown, running it again can call `advance_generation()`. In multi-agent mode, only the orchestrator or do-agent should run the default command.
- `.github/agents/` and `.claude/agents/` use current names `todo/` and `how/`, but `.codex/agents/` still refers to older `requirements/` and `principles/` names. That should be corrected before Codex agents are used as the canonical instructions.
- The README mentions `selfdev-agent`, `plan-agent`, and `do-agent` links, while the actual files are named `selfdev-plan-agent.md`, `selfdev-do-agent.md`, and `know-agent.md`. That is a discoverability issue, not a blocker for the architecture.

## Recommended Strategy: Managed Queue, Single Writer

Use `todo/` as the shared work queue and keep code writes serial.

```text
user request
  -> orchestrator chooses mode
  -> read-only agents collect evidence
  -> plan-agent writes one official todo increment
  -> do-agent executes the current todo increment
  -> verifier agents review diff and test output
  -> orchestrator advances todo to done
```

### Agent Roles

| Role | Reads | Writes | Purpose |
|---|---|---|---|
| Orchestrator | Everything | Queue lock, run ledger, final decisions | Owns sequencing, prevents duplicate writers, decides when an increment is ready. |
| know-agent | `how/`, `todo/`, docs, source | Report files only | Checks knowledge consistency, stale references, principle coverage, and queue health. |
| selfdev-plan-agent | Relevant source, `todo/`, `how/`, git history | One official numbered increment file such as `todo/increment_0023_todo_multi_agent_queue_lock.md` after orchestration approval | Turns a request into a bounded, TDD-ready increment. |
| selfdev-do-agent | Current increment, referenced `how/`, source, tests | Production code, tests, current increment status, commit | Implements exactly one current increment at a time. |
| verifier-agent | Diff, test output, current increment | Review report only | Checks whether the implementation satisfies acceptance criteria. |
| docs-agent | Docs and reports | Docs only | Updates generated or durable documentation after code is stable. |

The important rule is simple: many agents can read; only one agent writes code; only one agent writes the official queue at a time.

## Viable Strategies

### 1. Managed Queue With One Writer

This is the recommended default.

Use it for normal selfdev work: feature requests, bug fixes, refactors, docs updates with code impact, and test-driven increments.

Flow:

1. Orchestrator opens a planning lease.
2. One planner creates `todo/increment_0023_todo_multi_agent_queue_lock.md`.
3. Orchestrator verifies the new increment parses and has concrete acceptance criteria.
4. One do-agent runs the current increment loop.
5. Review agents inspect the diff and test evidence.
6. Orchestrator runs `./develop.sh --advance` only after the code and tests are verified.

Strengths:

- Fits the existing `todo/` lifecycle.
- Preserves a single coherent code context.
- Keeps acceptance criteria as the contract between planner and executor.
- Easy to audit through filenames, commits, and test output.

Weaknesses:

- Not maximally parallel for implementation.
- Requires discipline around who may run `./develop.sh`.
- Needs a lock file before multiple live sessions are safe.

### 2. Multiple Planners, One Reducer, One Writer

Use this when the request is vague or architectural and benefits from multiple opinions.

The parallel agents do not write official `todo/` files directly. They write candidate plans into a run folder, then the orchestrator reduces them into one official increment.

Concrete run layout:

```text
multi-agents/
  runs/
    20260524-multi-agent-support/
      manifest.json
      reports/
        know-agent.md
        system-scout.md
        test-scout.md
      proposals/
        planner-a.md
        planner-b.md
      decisions.md
      verification.md
```

Reducer rule:

- Candidate plans under `multi-agents/runs/20260524-multi-agent-support/proposals/` are advisory.
- The official queue remains `todo/`.
- The orchestrator writes exactly one accepted increment into `todo/`.
- If several increments are needed, the orchestrator writes them in dependency order.

Strengths:

- Good for broad analysis and design alternatives.
- Avoids competing planners creating duplicate increment numbers.
- Keeps the final `todo/` queue clean.

Weaknesses:

- Needs extra run bookkeeping.
- Requires a reducer decision, not blind aggregation.
- More token and wall-clock cost than one planner.

### 3. Isolated Worktree Writers

Use this only when subtasks are truly independent by file or module.

Example safe case:

- Agent A updates docs only.
- Agent B adds tests for a separate module.
- Agent C spikes a candidate implementation in an isolated worktree.
- The orchestrator reviews all diffs and applies one final merge.

Do not use this for tightly coupled changes, shared abstractions, or anything that touches the same runtime contract.

Strengths:

- Useful for experiments.
- Allows implementation candidates without corrupting the main checkout.
- Good for large migrations with clear file ownership.

Weaknesses:

- Merge still requires human-grade judgment.
- Passing tests in one worktree may not mean the combined result is correct.
- It is overkill for the current selfdev loop unless queue locking and run ledgers exist.

## Shared State Model

Use these state surfaces deliberately.

| Surface | Owner | Purpose | Multi-agent rule |
|---|---|---|---|
| `todo/` | Orchestrator plus one planner | Official ordered work queue | One writer at a time. Never let several planners write official increments concurrently. |
| `how/` | Knowledge maintainer | Reusable principles | Changes require a dedicated increment. Do not casually add principles during execution. |
| `organism_state.json` | `develop.sh` / orchestrator | Generation and last shown increment | Only orchestrator or do-agent should mutate it. Read-only agents should not run default `./develop.sh`. |
| Source files | do-agent | Product implementation | One writer in the main checkout. Other agents use reports or isolated worktrees. |
| Tests | do-agent, then verifier | Verification contract | Do-agent writes tests for the current increment; verifier reads and runs tests. |
| `multi-agents/runs/` | Orchestrator | Parallel research and proposals | Agents may write isolated reports here without touching the official queue. |

## Required Locking Before Concurrent Execution

The first implementation change should add a lock or lease around queue and code writes.

A concrete lock file can live at `todo/.selfdev-agent-lock.json`:

```json
{
  "lock_id": "20260524T122900Z-selfdev-do-agent",
  "owner": "selfdev-do-agent",
  "purpose": "execute current todo increment",
  "current_increment": "todo/increment_0014_todo_feedback_driven_prompt_logic.md",
  "created_at": "2026-05-24T12:29:00Z",
  "expires_at": "2026-05-24T13:29:00Z"
}
```

Rules:

- A planner must not create or rename official `todo/` files while a do-agent lock is active.
- A do-agent must not start if another do-agent lock exists and has not expired.
- `./develop.sh --advance` must refuse to run unless the caller owns the active do-agent lock.
- Read-only agents do not need the lock.
- Expired locks may be removed only after checking git status and current process state.

## Safe Command Policy

For concurrent agents, command permissions should be role-specific.

| Role | Safe commands | Restricted commands |
|---|---|---|
| know-agent | `rg`, `sed`, `find`, `git log`, `git show`, direct file reads | `./develop.sh` default mode, writes outside report folder |
| plan-agent | file reads, `./develop.sh --state`, parser checks, targeted tests if needed | production code edits, `./develop.sh --advance` |
| do-agent | `./develop.sh`, tests, implementation edits, commits | writing unrelated increments, broad refactors outside current increment |
| verifier-agent | tests, lint, diff inspection, report writing | production code edits, queue rename, advance |
| orchestrator | all coordination commands | direct code edits unless acting as do-agent |

Important detail: read-only agents should use `./develop.sh --state` or direct `todo/` reads. They should not run default `./develop.sh` because the default path can advance the current increment when `last_increment_shown` matches.

## How `/todo/` Should Work With Multi Agents

The user's suggested model is the right base:

- One agent creates `todo/`.
- One agent reads and writes code from that `todo/`.

The more precise selfdev version is:

1. `selfdev-plan-agent` creates exactly one official increment such as `todo/increment_0023_todo_multi_agent_queue_lock.md`.
2. `selfdev-do-agent` reads the current increment through `./develop.sh` or direct file inspection.
3. `selfdev-do-agent` implements only that increment.
4. `verifier-agent` checks diff, tests, and acceptance criteria from a clean context.
5. Orchestrator runs `./develop.sh --advance` and confirms the file became `_done_`.
6. The next increment becomes available.

If several planning agents are used, they should create proposal reports, not official queue files. The orchestrator performs the final write into `todo/`.

## Reduction Rules

Parallel agent outputs need a reducer. The reducer should prefer objective signals in this order:

1. Test results.
2. Parser success for `todo/` files.
3. Exact acceptance criteria mapping.
4. Git diff and changed-file list.
5. Runtime logs or command output.
6. Human approval when the decision is architectural or subjective.

The reducer should not merge two natural-language plans by concatenation. It should choose one path, rewrite it as one coherent increment, and reject duplicate or conflicting assumptions.

## First Implementation Increments

If this strategy is implemented in code, split it into small increments.

1. `todo/increment_0023_todo_multi_agent_queue_lock.md`
   - Add lock-file read, write, expiry, and ownership checks.
   - Add tests that prove two do-agents cannot advance the same increment.

2. `todo/increment_0024_todo_multi_agent_run_ledger.md`
   - Add `multi-agents/runs/` as a report/proposal ledger.
   - Add validation that reports do not mutate official queue state.

3. `todo/increment_0025_todo_read_only_agent_peek_mode.md`
   - Add a safe `./develop.sh --peek` mode that shows the current increment without mutating `organism_state.json`.
   - Update read-only agent instructions to use `--peek`.

4. `todo/increment_0026_todo_codex_agent_path_sync.md`
   - Update `.codex/agents/` from `requirements/` and `principles/` to `todo/` and `how/`.
   - Add a docs consistency test so agent instructions cannot drift again.

5. `todo/increment_0027_todo_verifier_report_contract.md`
   - Define a verifier report schema with acceptance-criteria mapping, commands run, pass/fail status, and unresolved risks.
   - Keep verifier output outside production code unless a follow-up increment is created.

## Final Recommendation

Adopt managed queue orchestration:

- `todo/` is the source of truth for official work.
- `how/` is the source of truth for reusable execution principles.
- `multi-agents/runs/` is the scratch space for parallel research, proposals, and verifier reports.
- The orchestrator owns queue mutation.
- The planner owns requirement creation.
- The do-agent owns code changes for one current increment.
- Review and knowledge agents stay read-only except for their own reports.

This gives selfdev useful multi-agent support without losing the main advantage of the current design: small, sequential, testable increments that any AI agent can execute without reinterpretation.
