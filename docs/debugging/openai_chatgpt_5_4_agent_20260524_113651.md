# Debuggable Multi‑Agent AI Coding Systems: Techniques, Patterns and Product Design

## Introduction

Large language models are increasingly being used as *agents* that
autonomously plan tasks, write code, interpret tests and modify software
projects. The frontier of **multi‑agent coding** aims to speed up
development by allowing several specialised agents (planner, coder,
tester, critic, reviewer, etc.) to work concurrently on the same
codebase. However, today's tools provide little visibility into what
each agent did and why. This research report analyses the core
challenges of multi‑agent AI coding, surveys emerging tools from
observability, testing and tracing, and proposes a feature‑rich product
architecture to improve debuggability, explainability, auditability and
human trust.

## 1 Core Problem: Why Multi‑Agent Coding Is Hard to Debug

**Non‑determinism and concurrency:** Standard debugging tools assume a
single deterministic thread of execution. Multi‑agent coding breaks
these assumptions. AugmentCode notes that breakpoints, step‑through
debuggers, log grepping and regression tests all rely on reproducible
paths and single threads, while parallel agents are non‑deterministic
and interleave actions, destroying causal
ordering[\[1\]](https://www.augmentcode.com/guides/debug-parallel-ai-agents#:~:text=Why%20Parallel%20Agents%20Break%20Every,Standard%20Debugging%20Tool).
Even with temperature 0, identical prompts can produce different
traces[\[2\]](https://www.augmentcode.com/guides/debug-parallel-ai-agents#:~:text=Why%20Parallel%20Agents%20Break%20Every,Standard%20Debugging%20Tool),
and concurrent state access multiplies race
conditions[\[3\]](https://www.augmentcode.com/guides/debug-parallel-ai-agents#:~:text=Each%20failure%20mode%20exists%20to,failures%20on%20every%20parallel%20run).

**Emergent interaction bugs:** Anthropic engineers report emergent
behaviours where small changes to one agent change how sub‑agents
behave[\[4\]](https://www.augmentcode.com/guides/debug-parallel-ai-agents#:~:text=%22multi,lies%20in%20the%20interaction%20structure).
Cascading hallucinations propagate across
agents[\[5\]](https://www.augmentcode.com/guides/debug-parallel-ai-agents#:~:text=Cascading%20hallucinations%20compound%20across%20agent,recognizable%20relationship%20to%20its%20origin),
while feedback loops can cause goal drift and repetitive
loops[\[6\]](https://www.augmentcode.com/guides/debug-parallel-ai-agents#:~:text=Feedback%20loops%20emerge%20when%20one,proxy%20for%20semantic%20loop%20detection).
These failures often stem from interactions between agents rather than a
single faulty tool call. The AGDebugger study found that developers
struggled to review long agent conversations and lacked interactive
debugging
support[\[7\]](https://arxiv.org/pdf/2503.02068#:~:text=Abstract%20Fully%20autonomous%20teams%20of,3%20Mar%202025).

**Invisible reasoning and state:** LLM‑based agents do not expose call
stacks or memory. Developers cannot see which files an agent read, what
intermediate state it saw, or why a particular decision was made.
Without structured logging (agent ID, correlation IDs, logical
timestamps and metadata) it is impossible to reconstruct
causality[\[8\]](https://www.augmentcode.com/guides/debug-parallel-ai-agents#:~:text=Parallel%20agent%20debugging%20becomes%20tractable,shared%20state%20reads%20and%20writes).
Present systems rarely capture the prompt context, external documents
read, or assumptions made. As a result, hallucinated fixes, duplicated
work, stale context and silent regressions go unnoticed.

**Overlapping edits and stale context:** Parallel agents editing the
same repository risk read--modify--write races and silent state
overwrites[\[9\]](https://www.augmentcode.com/guides/debug-parallel-ai-agents#:~:text=Silent%20state%20overwrites%20occur%20when,Missing%20data).
Without isolation, one agent may undo another's work or operate on stale
dependencies. Git worktrees and isolated workspaces help but do not
capture process‑level
isolation[\[10\]](https://www.augmentcode.com/guides/debug-parallel-ai-agents#:~:text=Pattern%202%3A%20Isolated%20Git%20Worktrees,for%20Parallel%20Agents).

**Unclear ownership and accountability:** Traditional version control
records commit authorship, but when multiple agents propose changes
concurrently, it becomes difficult to answer: *Which agent changed this
file or UI element?* The arXiv paper on multi‑agent provenance argues
that successive transformations often leave little trace of individual
contributions and calls for symbolic chronicles that embed signed,
time‑stamped records analogous to a chain of
custody[\[11\]](https://arxiv.org/pdf/2504.12612v2#:~:text=ative%20chain%2C%20content%20undergoes%20successive,content%20in%20the%20very%20act)[\[12\]](https://arxiv.org/pdf/2504.12612v2#:~:text=agent%20systems%20may%20undergo%20complete,discernible%20trace%20of%20prior%20contributions).
Without provenance, accountability and trust suffer.

**Human questions a debuggable system must answer:** A human reviewer
needs to know:

  -----------------------------------------------------------------------
  Question                            Why it matters
  ----------------------------------- -----------------------------------
  **Who changed what?**               Ownership of files, components, UI
                                      elements, tests, database schemas
                                      and prompts must be tracked per
                                      agent to attribute accountability
                                      and identify conflicting edits.

  **Why was the change made?**        Each change should be linked to the
                                      task, bug report, test failure or
                                      agent hypothesis that motivated it;
                                      otherwise reasoning is opaque.

  **What inputs influenced the        The system should record the code,
  change?**                           DOM nodes, API responses, browser
                                      state, test results or logs that
                                      the agent saw when making the
                                      decision. Without this context,
                                      humans cannot evaluate whether the
                                      agent acted appropriately.

  **How do changes relate?**          Agents may coordinate sub‑tasks;
                                      grouping related changes helps
                                      reviewers understand intent. We
                                      need to know which changes are
                                      speculative, confirmed, reverted or
                                      untested.

  **Which agent introduced            When tests fail, the system must
  regressions?**                      attribute the failure to the
                                      responsible agent and show the
                                      causal chain.

  **What was tested?**                Humans must see which components
                                      were tested visually, functionally
                                      and semantically, and which
                                      behaviours changed even if the diff
                                      is small.

  **How were conflicts resolved?**    The system should log disagreements
                                      between agents, the proposed
                                      resolutions and final decisions.
  -----------------------------------------------------------------------

## 2 Visual Explainability for Code and UI Changes

A debuggable multi‑agent system must bridge the gap between code diffs
and user‑facing behaviour. **Visual overlays** and **rich provenance
metadata** can make changes comprehensible.

### 2.1 Colour‑coded overlays and annotations

-   **Agent‑specific colours:** Each agent is assigned a distinct
    colour. In the browser preview or design canvas, modified UI
    elements are outlined in the agent's colour. Colours differentiate
    direct edits (e.g., text or style changes) from indirect effects
    (refactors, dependency updates). A legend indicates which colour
    corresponds to which agent and change type.
-   **Hoverable annotations:** Hovering over a highlighted element
    reveals a tooltip showing the responsible agent, timestamp, task
    objective, related files/tests, a confidence level and a summary of
    the agent's reasoning.
-   **Change provenance panel:** A side panel lists all visual elements
    and maps them to source files, commits, agent actions, Playwright
    tests and state changes. Selecting an element highlights the
    corresponding code and test steps.
-   **Conflict overlays:** When multiple agents modify the same element,
    the overlay shows overlapping colour bands. Clicking opens a
    conflict resolution dialog showing each agent's proposed changes and
    reasoning.
-   **Grey‑out unchanged regions:** A mode greys out untouched UI and
    highlights only modified regions, helping reviewers focus on
    relevant changes.

### 2.2 Visual diff maps and pixel‑level diffs

Visual diffing goes beyond textual diffs by comparing rendered UIs:

-   **Before‑and‑after screenshots:** For every meaningful UI
    modification, the system captures pre‑ and post‑change screenshots.
    BigBinary explains that Playwright traces include DOM snapshots and
    screenshots before, during and after each
    action[\[13\]](https://www.bigbinary.com/blog/how-to-analyze-playwright-traces#:~:text=What%20are%20Playwright%20traces%3F).
    Similar snapshots can be captured for each agent edit.
-   **Pixel‑level diffs with semantic grouping:** The diff algorithm
    labels changes as layout shifts, copy changes, colour changes,
    spacing changes or component replacements. Differences are grouped
    by semantics rather than raw pixels, so a changed colour value is
    distinguished from a moved component. Unchanged regions fade to the
    background.
-   **DOM tree overlays:** The system overlays inserted, removed and
    modified nodes in the DOM tree. Playwright's Trace Viewer lets users
    inspect element visibility, overlays and highlight click
    positions[\[14\]](https://www.bigbinary.com/blog/how-to-analyze-playwright-traces#:~:text=%23%20Snapshots%3A%20Time);
    similar functionality can be integrated into the debugging console.
-   **Component boundary highlighting:** For frameworks like React, Vue,
    Svelte or server‑rendered HTML, the overlay outlines component
    boundaries. This helps attribute changes to specific components and
    design-system elements.
-   **Why‑did‑this‑change panel:** For each UI element, a panel explains
    why it changed, showing the agent's reasoning and the associated
    tests or bug reports.

### 2.3 Timeline playback and heatmaps

-   **UI evolution timeline:** The system records snapshots at each
    agent step. A timeline slider lets the user scrub through changes,
    seeing how the UI evolved across agent actions. Snapshots are linked
    to commit hashes and agent IDs.
-   **Agent heatmaps:** Heatmaps show where each agent spent effort on
    the UI. Colours indicate time spent or number of changes per region.
    Users can filter by agent or change type.
-   **Hidden consequence indicators:** Overlays highlight hidden changes
    such as modified event handlers, ARIA labels, network calls,
    analytics events, permissions, validation rules or accessibility
    behaviour.

### 2.4 Integration locations

Visual explainability should appear where developers already work:
inside IDEs (e.g., VS Code extension), the browser preview for front‑end
work, design canvases (e.g., Figma), CI reports (attach before/after
screenshots and diffs to failed tests), code review tools (GitHub PRs)
and a dedicated **AI debugging console**. The console aggregates code,
visual diffs, test traces and agent metadata.

## 3 State Representation and Inspectable Hidden Layers

An effective debugging platform must expose the hidden state that agents
operate on. The **AgentTrace framework** suggests three instrumentation
surfaces---cognitive (reasoning and planning), operational (tool calls)
and contextual (inter‑agent messages and shared
state)[\[8\]](https://www.augmentcode.com/guides/debug-parallel-ai-agents#:~:text=Parallel%20agent%20debugging%20becomes%20tractable,shared%20state%20reads%20and%20writes).
Building on this idea, we propose a **canonical agent state JSON** saved
at each step, containing at least:

  --------------------------------------------------------------------------------------------------------------------------------------------------------------------
  Category                            Example fields
  ----------------------------------- --------------------------------------------------------------------------------------------------------------------------------
  **Identity**                        `agent_id`, `agent_name`, `role`, `version`, `task_assignment`, `subgoal`, `confidence_level`, `risk_level`, `memory_usage`,
                                      `token_budget_used`. OpenTelemetry's generative AI spec defines similar fields such as `gen_ai.agent.id`, `gen_ai.agent.name`
                                      and
                                      `gen_ai.agent.version`[\[15\]](https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/#:~:text=Attributes%3A).

  **Inputs observed**                 `files_read` (list of file paths and version hashes), `browser_actions` (visited URLs, DOM snapshots), `api_calls` (URL,
                                      parameters, responses), `terminal_output`, `logs`, `errors`, `test_failures`, `prompt_context` (user/system messages),
                                      `external_docs` consulted.

  **Outputs produced**                `files_modified` (paths, diff hunks), `commands_run`, `browser_actions_performed`, `test_results`, `screenshots_captured`,
                                      `tool_calls_made`, `dependencies_introduced`, `database_migrations`, `prompts_sent_to_subagents`, `external_requests`.

  **Reasoning state**                 `current_hypothesis`, `assumptions`, `open_questions`, `planned_steps`, `memory_read_keys`, `memory_write_keys`,
                                      `safety_constraints_triggered`, `heuristics_used`, `confidence_updates`.

  **Environment**                     `working_directory`, `branch`, `execution_sandbox_id`, `allowed_files`, `credentials_scoped`, `runtime_config`, `tool_versions`.
  --------------------------------------------------------------------------------------------------------------------------------------------------------------------

Snapshots of this JSON should be captured after each agent action and
persisted in a **state timeline**. Tools can compute **state diffs**
across snapshots---not only file diffs but also reasoning‑state diffs,
task‑state diffs, UI‑state diffs, test‑state diffs, browser‑state diffs,
application‑state diffs and database‑state diffs. For example, a
reasoning‑state diff may show that an agent changed its hypothesis after
reading a file; a test‑state diff may show which tests moved from
failing to passing; a UI‑state diff may capture DOM differences.

### 3.1 Representations for hidden layers

-   **JSON snapshots:** Standard machine‑readable format for storing
    state; can be diffed and versioned. Each snapshot should include a
    **logical timestamp** and correlation
    ID[\[8\]](https://www.augmentcode.com/guides/debug-parallel-ai-agents#:~:text=Parallel%20agent%20debugging%20becomes%20tractable,shared%20state%20reads%20and%20writes).
-   **Graph structures:** Agents operate on task graphs (DAGs).
    Representing states as nodes and transitions as edges allows
    interactive inspection and search. Graph databases like Neo4j can
    store these relationships.
-   **Event streams:** Each state change becomes an event in a stream.
    Observability tools can attach spans and metrics to events (see
    Section 9). Events include tool calls, file edits, test runs and
    memory operations.
-   **Agent journals:** A human‑readable diary summarising the agent's
    reasoning at each step. This can be a summarised subset of the full
    chain‑of‑thought and should cite evidence (e.g., file names, line
    numbers) rather than revealing raw prompts for privacy.
-   **Replayable sessions:** By recording all tool calls and responses,
    deterministic replay is possible (see Section 8). The AugmentCode
    pattern suggests capturing every LLM request with its full prompt
    and response, every tool call with inputs and outputs, every agent
    message and the state snapshot at each
    handoff[\[16\]](https://www.augmentcode.com/guides/debug-parallel-ai-agents#:~:text=Pattern%206%3A%20Deterministic%20Replay).
-   **Causal dependency maps:** Visualising dependencies between state
    changes helps identify hidden couplings. For instance, a state map
    might show that a UI change depends on a specific file edit and a
    test result.

### 3.2 Storage and query

State snapshots and events should be stored in a **provenance database**
with a query language to answer questions like "show all state snapshots
where the agent's hypothesis changed," or "list all tools used before
the test passed." A time‑series database or event store (e.g.,
ClickHouse, Kafka) can handle large volumes. Snapshots should be
compressed and pruned but kept long enough for auditing. Provenance
metadata should attach to git commits and CI artefacts for review.

## 4 Multi‑Agent Provenance and Ownership

Provenance aims to record **who did what when and why** across multiple
agents. The **symbolic chronicle** proposed by Chang & Echizen embeds
signed, time‑stamped records into the generated content, enabling
post‑hoc attribution without relying on external
metadata[\[11\]](https://arxiv.org/pdf/2504.12612v2#:~:text=ative%20chain%2C%20content%20undergoes%20successive,content%20in%20the%20very%20act).
Our system extends this idea to code and UI changes via a **change
provenance ledger**.

### 4.1 Granularity of attribution

Attribution can operate at various levels:

-   **Commit‑level and branch‑level:** Each agent uses an isolated git
    worktree or branch. Commits include metadata fields for `agent_id`,
    `task_id` and `reason`. Worktree isolation prevents state
    corruption[\[10\]](https://www.augmentcode.com/guides/debug-parallel-ai-agents#:~:text=Pattern%202%3A%20Isolated%20Git%20Worktrees,for%20Parallel%20Agents).
-   **Line‑level:** Similar to `git blame`, each line in a file is
    attributed to an agent. When agents generate code, the diff view
    shows which agent introduced each line. AST‑aware diffing (see
    Section 7) improves accuracy.
-   **Component‑level:** Ownership of UI components or functions is
    tracked. The overlay shows which agent created or modified a
    component; click‑through reveals the commit and reasoning.
-   **Test‑level:** Tests are attributed to the agent that wrote or
    selected them. When a test fails, the responsible agent is
    identified.
-   **Decision‑level:** Each decision (e.g., choose to refactor vs.
    patch) is captured as a decision node with `agent_id`, `inputs`,
    `outputs` and `rationale`.
-   **Prompt‑level:** Every prompt used is hashed and stored with the
    agent ID. Updates to prompts are versioned to track how instructions
    changed.
-   **Runtime‑effect level:** Link runtime effects (network calls, file
    writes, UI manipulations) to the agent and step that caused them.

### 4.2 Change provenance ledger

The ledger is a tamper‑evident record of all meaningful actions taken by
agents. Each entry contains:

-   Unique ID and logical timestamp (vector clock) to establish order.
-   Agent ID, role and version.
-   Task or bug identifier causing the change.
-   Inputs observed (files, prompts, tests, UI state) and outputs
    produced.
-   Diff summary (files changed, functions touched, UI elements
    modified).
-   Reasoning summary (explanation of why the change was made).
-   Test status and coverage impact.
-   Confidence and risk scores (see Section 13).
-   Links to parent entries (causal dependencies) forming a DAG.

Such a ledger enables queries like "show all changes made by Agent A" or
"show all UI elements affected by the authentication refactor." It also
supports summarisation: grouping ledger entries by task or by impacted
component helps humans digest large change sets. To provide
cryptographic integrity, each ledger entry can include a hash chain or
digital signatures.

### 4.3 Data sources for attribution

Attribution should combine information from git commits, AST diffs,
semantic diffs, event logs, file‑system traces, tool invocation records,
browser traces and test traces. External instrumentation like
OpenTelemetry emits attributes such as `gen_ai.agent.id` and
`gen_ai.agent.name`[\[15\]](https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/#:~:text=Attributes%3A).
Combining these sources ensures that provenance remains robust even when
some metadata is missing.

## 5 Agent Communication and Collaboration Debugging

Agents rarely operate in isolation; they collaborate by passing messages
and handing off tasks. AGDebugger's user study showed that developers
find it difficult to review long conversations and need interactive
debugging
support[\[7\]](https://arxiv.org/pdf/2503.02068#:~:text=Abstract%20Fully%20autonomous%20teams%20of,3%20Mar%202025).
To make inter‑agent collaboration understandable, the system should
provide:

-   **Conversation timeline view:** A zoomable timeline with parallel
    swimlanes per agent shows messages sent, tools invoked and state
    changes over time. The AugmentCode article notes that current
    observability platforms lack cross‑agent timeline visualisations and
    only present tree‑structured
    traces[\[17\]](https://www.augmentcode.com/guides/debug-parallel-ai-agents#:~:text=The%20Observability%20Gap%3A%20No%20Mainstream,Agent%20Visualization).
-   **Summarised messages:** Long agent messages are summarised into
    concise bullet points with links to full content. Summaries should
    include the key instruction, tool call and result.
-   **Task handoff records:** When one agent delegates a subtask, the
    handoff entry records the subtask description, arguments, and
    expected outputs. The receiving agent's actions are linked back to
    this handoff.
-   **Disagreement tracking and conflict detection:** The system detects
    when agents produce conflicting outputs or assumptions. Conflicts
    may involve file edits, UI changes or test expectations (see
    Section 12). A conflict resolution UI shows each agent's reasoning
    and allows agents or humans to vote or merge solutions.
-   **Critic and reviewer roles:** Separate critic/reviewer agents
    evaluate the builder's output and provide feedback. The ledger
    records critiques, suggestions and final decisions.
-   **Dependency graphs:** Visualising the dependency graph between
    subtasks helps avoid circular dependencies and deadlocks. Graph
    nodes represent subtasks; edges represent prerequisites. Deadlock
    detection algorithms can flag cycles.
-   **Evidence quality scoring:** The system scores the quality and
    reliability of evidence (e.g., an API response vs. a hallucinated
    assumption) and displays it in summaries to calibrate trust.
-   **Human‑in‑the‑loop tools:** The conversation UI allows human
    developers to intervene by editing messages, adjusting prompts or
    injecting clarifications. AGDebugger enabled participants to reset
    to earlier points and edit messages, allowing counterfactual testing
    and rapid debugging[\[18\]](https://arxiv.org/pdf/2503.02068).

## 6 Visual and Semantic Testing for AI Coding Agents

Robust testing is essential to validate AI‑generated code. Instead of
treating tests as pass/fail gates, a debuggable system treats test
artefacts---screenshots, traces, coverage maps---as first‑class
evidence.

### 6.1 Playwright trace integration

Playwright's Trace Viewer captures comprehensive artefacts: complete DOM
snapshots before, during and after each action; screenshots at every
step; network activity logs; console logs; and an action
timeline[\[13\]](https://www.bigbinary.com/blog/how-to-analyze-playwright-traces#:~:text=What%20are%20Playwright%20traces%3F).
Users can hover over the timeline to preview frames and inspect DOM
highlights[\[19\]](https://www.bigbinary.com/blog/how-to-analyze-playwright-traces#:~:text=1).
The metadata tab reveals environment details (browser, platform, config,
viewport)[\[20\]](https://www.bigbinary.com/blog/how-to-analyze-playwright-traces#:~:text=3).
Snapshots enable time‑travel debugging, letting users compare element
states before and after
actions[\[21\]](https://www.bigbinary.com/blog/how-to-analyze-playwright-traces#:~:text=%23%20Snapshots%3A%20Time).

A multi‑agent debugging system should attach Playwright traces (or
similar) to each test run. For each agent, the system records which
tests it added or modified and links test steps to code and UI changes.
Visual overlays highlight which UI regions were covered by tests, and
agent‑specific colours indicate who wrote or selected each test.

### 6.2 Visual test coverage and gaps

-   **Coverage overlays:** After running tests, overlay the UI with
    green (tested), yellow (partially tested) and red (untested)
    regions. Each region lists which tests exercised it. This helps
    identify changed UI elements that lack coverage.
-   **Test mapping:** Map tests to changed components and agent actions.
    For example, if a test fails, show which agent last modified the
    component and how it relates to the test.
-   **Flakiness visualisation:** Display histograms of test pass/fail
    over multiple runs to detect flakiness. Flaky tests highlight areas
    where agent changes may have introduced intermittent issues.
-   **User‑journey graphs:** Represent end‑to‑end tests as paths through
    the application; overlay these paths with agent‑modified components
    to see if key user journeys are affected.
-   **Natural‑language test explanations:** Generate natural‑language
    summaries of what each test proves. If a test passes but does not
    assert the changed behaviour, flag a potential false negative.

### 6.3 Accessibility and semantic testing

Beyond visual similarity, tests should check accessibility. Use tools
that capture accessibility tree snapshots, ARIA attributes, focus order,
keyboard‑navigation traces and colour contrast. Differences in these
states are surfaced in diff panels (see Section 14). Semantic tests
verify data‑flow and API contracts (see Section 7) to detect regressions
beyond the UI.

## 7 Semantic Diffs Beyond Normal Git Diffs

Traditional line‑based diffs treat code as text. They cannot detect
moved functions, refactorings or API contract changes. Baz's blog
explains that Git diff is limited---it treats renamed functions as
separate changes and cannot infer intent or
dependencies[\[22\]](https://baz.co/resources/why-your-code-gen-ai-doesnt-understand-diffs#:~:text=Git%20diffs%20are%20usually%20what,track%20dependencies%20and%20reconstruct%20intent).
AST‑based diffing builds an abstract syntax tree and compares syntax
nodes, preserving
structure[\[23\]](https://baz.co/resources/why-your-code-gen-ai-doesnt-understand-diffs#:~:text=Where%20Git%20diffing%20focuses%20on,and%20structure%20between%20those%20elements).

### 7.1 Types of semantic diffs

-   **AST diffs:** Compare abstract syntax trees to detect added,
    removed and modified nodes. Group changes by functions, classes or
    modules instead of by lines. AST diffing accurately tracks critical
    changes, identifies refactors and reduces
    noise[\[24\]](https://baz.co/resources/why-your-code-gen-ai-doesnt-understand-diffs#:~:text=Key%20Benefits%20of%20AST%20Diffing).
-   **Type‑aware diffs:** Use type information to detect changes to
    function signatures, class hierarchies or generics. This helps
    verify API compatibility.
-   **Data‑flow and control‑flow diffs:** Compute differences in data
    flows or control flows between versions, highlighting how the
    execution path or state dependencies changed.
-   **API contract diffs:** Compare OpenAPI/GraphQL schemas or
    TypeScript types to detect breaking API changes.
-   **Dependency graph diffs:** Diff the dependency tree (imports and
    package.json) to see new, removed or upgraded dependencies.
-   **Schema diffs:** For databases, diff migration files and actual
    schema to track changes. Similarly for route diffs, permission diffs
    and state machine diffs.
-   **Component tree diffs:** For UI frameworks, diff the component
    hierarchy (e.g., React tree) to highlight component replacements or
    structural changes.
-   **Prompt diffs:** When prompts evolve, compute differences to
    highlight new instructions, removed constraints or updated examples.
-   **Performance, security and accessibility diffs:** Compare telemetry
    metrics (latency, memory), permission models, security taints and
    accessibility checks between versions.

### 7.2 Intent‑aware grouping

Semantic diffing should group changes by **intent** rather than file.
Each group could represent a bug fix, refactor, test addition, copy
change, layout change, API contract change, dependency update, generated
boilerplate, speculative experiment, rollback, conflict resolution or
human‑requested change. Grouping by intent helps reviewers navigate
complex diffs, especially when multiple agents contribute. The grouping
is derived from ledger metadata: the `reason` field and the task
description. In the code review UI (Section 10), the diff viewer shows
groups as collapsible sections with summary cards.

## 8 Replay, Rollback, Branching and Time‑Travel Debugging

### 8.1 Replay and deterministic execution

AugmentCode emphasises **deterministic replay**: recording all LLM
responses and tool outputs during a run and substituting them during
replay to reproduce
behaviour[\[16\]](https://www.augmentcode.com/guides/debug-parallel-ai-agents#:~:text=Pattern%206%3A%20Deterministic%20Replay).
To support this, the system must capture prompts, responses, tool
inputs/outputs, agent messages and state snapshots. Recorded events can
be loaded into a replay client that intercepts calls and returns
recorded results. This enables time‑travel debugging without hitting
external APIs or incurring cost. Replay artifacts are stored with the
change provenance ledger.

### 8.2 Automatic checkpointing and branching

-   **Checkpoint per agent step:** After each agent completes a
    sub‑goal, the system creates a checkpoint capturing the entire state
    (files, database, tests, memory). Checkpoints include metadata:
    agent ID, task ID, timestamp and risk level.
-   **Branch‑per‑agent workflows:** Each agent runs in its own branch or
    isolated
    worktree[\[10\]](https://www.augmentcode.com/guides/debug-parallel-ai-agents#:~:text=Pattern%202%3A%20Isolated%20Git%20Worktrees,for%20Parallel%20Agents).
    The system can automatically merge branches using semantic diffing
    and conflict resolution policies. Unmerged branches can be compared
    side‑by‑side and parts of each merged manually.
-   **Sandbox per agent:** For runtime isolation, each agent executes in
    a containerised sandbox with scoped credentials and file access.
    Harvey AI's approach emphasises passing each worker a full
    configuration at startup and prohibiting runtime access to the
    control
    plane[\[25\]](https://www.augmentcode.com/guides/debug-parallel-ai-agents#:~:text=system%20state%20beyond%20their%20intended,access%20to%20the%20control%20plane).

### 8.3 Rollback and time travel

-   **Rollback by causality:** The ledger and state snapshots allow
    rolling back changes by causal chain. A user can select a change
    (e.g., a failing commit) and request a rollback that removes its
    direct effects and dependent changes. The system warns when rollback
    affects later changes.
-   **UI and state rollback:** For UI, the overlay can "time‑travel" to
    show previous states. Developers can restore a UI element to a prior
    state while preserving unrelated changes.
-   **Migration and dependency rollback:** The system tracks database
    migrations and dependency updates; rollback operations revert to
    previous versions, with warnings about data loss or compatibility.
-   **Alternative solution comparison:** The system allows side‑by‑side
    comparison of different agent solutions. Humans can merge the best
    parts and discard the rest.

## 9 Observability for AI Coding Agents

Observability involves capturing structured telemetry from agents to
monitor, analyse and debug their behaviour in real time. Langfuse's blog
notes that the industry is converging on **OpenTelemetry (OTEL)** as a
standard for collecting agent telemetry data and that many frameworks
emit traces via
OTEL[\[26\]](https://langfuse.com/blog/2024-07-ai-agent-observability-with-langfuse#:~:text=Industry%20Trends%20in%20Agent%20Observability).
OTEL defines generative AI attributes such as `gen_ai.agent.id`,
`gen_ai.agent.name` and conversation
IDs[\[27\]](https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/#:~:text=Attributes%3A).

### 9.1 Span‑based tracing

Agents produce nested spans representing tasks, subtasks, tool calls and
test runs. Each span includes:

-   **Attributes:** `agent_id`, `task_id`, `tool_name`, `prompt_name`,
    `input_size`, `output_size`, latency, token count, cost,
    success/failure status, etc. The OTEL Gen AI spec defines fields for
    input messages, output messages, request temperature, top‑p, top‑k
    and stop
    sequences[\[28\]](https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/).
-   **Events:** Start/stop events, error events (exceptions), warnings
    (e.g., prompt injection detection), retrieval events (documents
    returned)[\[29\]](https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/#:~:text=value%20is%20measured%20from%20when,87).
-   **Logs:** Structured logs capturing reasoning summaries, environment
    variables, memory reads/writes and safety constraint checks.

Traces from multiple agents are combined into a **causal DAG** by
propagating correlation IDs and parent span
IDs[\[30\]](https://www.augmentcode.com/guides/debug-parallel-ai-agents#:~:text=Pattern%204%3A%20Causal%20Tracing%20with,Distributed%20Trace%20Context).
A cross‑agent timeline view (Section 5) displays spans as horizontal
bars aligned by time; overlapping spans show concurrency. Langfuse
acknowledges that no mainstream observability tool yet visualises
concurrent agents as parallel
tracks[\[17\]](https://www.augmentcode.com/guides/debug-parallel-ai-agents#:~:text=The%20Observability%20Gap%3A%20No%20Mainstream,Agent%20Visualization),
underscoring the need for new visualisations.

### 9.2 Metrics and dashboards

Observability dashboards aggregate metrics per agent and task: latency,
throughput, token counts, cost, error rates, success rates, ratio of
tool calls, and coverage of tests. They also track error budgets for
agent‑generated changes: e.g., number of hidden regressions, failed
merges, or flakiness incidents per release. Real‑time cost tracking is
crucial because agent workflows can incur unpredictable
costs[\[31\]](https://langfuse.com/blog/2024-07-ai-agent-observability-with-langfuse#:~:text=LLMs%20are%20stochastic%20by%20nature%2C,advantage%20of%20using%20agentic%20workflows).

### 9.3 Token and memory audit

Tools should audit which memories were read and written, which files
were included in context, and which prompts or system constraints were
used. This ensures that prompt injections or stale memories are
detected. Logging memory operations also allows analysis of context
drift and summarisation distortions over time.

### 9.4 Security and policy enforcement

Observability spans should include security attributes: permission
checks, access to sensitive data, encryption use, and secrets redaction.
The system should detect prompts containing secrets or requests to
unsafe tools. Trace analysis can flag suspicious patterns such as
repeated attempts to access restricted resources.

## 10 Human Review and Code Review UX

Human oversight remains critical. AI‑generated changes should appear in
the review interface with rich context to enable informed decisions.

### 10.1 Review summaries and evidence cards

-   **Agent‑authored summaries:** Each agent provides a human‑readable
    summary of its changes, reasons and evidence. However, summaries can
    be misleading; therefore, the system attaches evidence links (diffs,
    tests, trace spans) to each claim.
-   **Intent grouping:** Changes are grouped by intent (see Section 7).
    Each group shows the agent, risk score, confidence score and a
    summary of the impacted functionality.
-   **Risk and confidence badges:** Visual indicators show high‑risk
    changes (e.g., touching authentication, database schema) or low
    confidence changes (due to hallucinated reasoning). Reviewers can
    filter by risk or agent.
-   **Evidence cards:** Attach test evidence (screenshots, trace
    snapshots), performance metrics, accessibility diffs and security
    analysis to each file. For example, a card might show that the
    Playwright test covering a modified component still passes, along
    with before/after snapshots.
-   **Reviewer suggestions:** The system suggests questions for
    reviewers (e.g., "Verify that error handling was not removed") based
    on the type of change.
-   **Review filters:** The interface lets reviewers filter by agent,
    task, file type, UI region, test coverage status, and confidence
    level. This prevents information overload.

### 10.2 Preventing summarisation bias

Agent‑generated summaries should not hide important details or oversell
success. To counter this, the UI emphasises raw evidence and highlights
unsupported claims. Confidence badges (see Section 13) reflect the
agent's certainty and evidence quality. Human reviewers can view the
full reasoning journal if needed.

## 11 Debuggable Prompt, Memory and Context Management

Prompt and context management significantly influence agent behaviour.
The system should expose:

-   **Prompt versions:** Record the sequence of prompts (system, user,
    tool instructions) provided to each agent. List which instructions
    were used or ignored. Expose system constraints and safety policies
    applied.
-   **Context windows:** Show which files, documentation and past
    interactions were included in context. Provide reasons for
    inclusion/exclusion and highlight stale or hallucinated information.
-   **Memory operations:** Log memory reads and writes: what information
    was retrieved, summarised or stored. Show how context changed across
    steps and across agents.
-   **Summarisation fidelity:** Reveal how summarisation compressed or
    distorted context. Provide metrics on summarisation loss and allow
    humans to expand summarised content.
-   **Evidence citations:** Encourage agents to cite sources in their
    reasoning, linking to files, lines, docs or API responses. This
    internal citation habit aids auditability.

## 12 Conflict Detection and Resolution

### 12.1 Conflict types

-   **File edit conflicts:** Two agents edit the same lines or
    semantically coupled lines. AST diffing is used to detect conflicts
    beyond textual overlaps.
-   **Semantic conflicts:** One agent changes a function signature while
    another updates call sites inconsistently. Type‑aware diffs and API
    contract diffs can detect these.
-   **UI conflicts:** Agents modify the same component layout or style
    differently. Visual diff overlays show overlapping modifications.
-   **Test conflicts:** Agents add tests with contradictory assertions
    or remove tests without consensus.
-   **Architecture conflicts:** Agents propose incompatible design
    patterns or frameworks.
-   **Dependency conflicts:** Agents upgrade different versions of the
    same dependency.
-   **Security/performance conflicts:** One agent removes error handling
    for performance, while another adds security checks.
-   **Prompt/memory conflicts:** Conflicting instructions in prompts or
    inconsistent memory states.

### 12.2 Detection and display

-   **Real‑time conflict detection:** As changes are proposed, the
    system performs semantic diffing and triggers conflict alarms.
    Conflicts are shown in overlays and the review interface.
-   **Conflict maps:** Visualise conflicts as graphs with nodes
    representing agents and resources (files, components, tests) and
    edges representing conflict relationships. Edge colours denote
    conflict severity.
-   **Resolution mechanisms:** Agents can attempt automated merges using
    CRDTs or patch stacks. If multiple solutions exist, the system
    prompts a vote among agents or escalates to a human. Human reviewers
    can select or merge parts of each proposed solution.
-   **Assumption tracking:** The ledger tracks assumptions made by
    agents. When a conflict arises, the system shows which assumptions
    differ and invites resolution.

## 13 Risk, Confidence, Uncertainty and Verification

### 13.1 Confidence metrics

Agents should estimate confidence per change, file, test, UI element and
generated explanation. Confidence may derive from model log
probabilities, presence of supporting evidence, and test coverage. For
example, changes with passing tests and strong evidence have high
confidence; hallucinated code with little evidence has low confidence.

### 13.2 Risk scoring

Risk scoring assesses the blast radius of a change. High‑risk changes
touch critical paths (authentication, payments, database schema),
security‑sensitive functions, third‑party dependencies or migrations.
Lack of tests or low confidence increases risk. A risk heatmap overlays
the codebase to show hotspots.

### 13.3 Verification status

Each claim or change is tagged with a verification status: `Untested`,
`Tested–Pass`, `Tested–Fail`, `Benchmarked`, `Human‑Approved`,
`Assumed`, `Unsupported`. The code review UI displays these statuses.
Unsupported claims trigger reviewer warnings.

### 13.4 Communicating uncertainty

Confidence and risk should not create false trust. Visual indicators
(e.g., dashed outlines or opacity) convey uncertainty. Summaries should
explicitly state the level of evidence, similar to scientific reporting
(e.g., "Likely," "Uncertain"). This encourages critical human oversight.

## 14 Accessibility, Security, Privacy and Compliance Debugging

AI‑generated changes can introduce hidden regressions beyond visual
differences. The system should perform specialised diffs and analyses:

-   **Accessibility tree diffs:** Compare the accessibility tree (roles,
    labels, states) before and after changes. Highlight altered ARIA
    attributes, focus orders and keyboard navigation flows. Present
    diffs in an accessibility panel.
-   **Colour contrast and layout diffs:** Measure colour contrast ratios
    and spacing. Flag regressions in accessible design.
-   **Security taint tracking:** Perform static taint analysis to detect
    injection risks or insecure data flows. Highlight permission
    boundary diffs and authentication/authorisation path changes. When
    dependencies are updated, check for known vulnerabilities.
-   **Privacy‑sensitive data flow diffs:** Trace flows of personally
    identifiable information (PII). Flag new telemetry events, analytics
    calls or cookie changes. Provide audit trails for compliance and
    data retention changes.
-   **Secret leakage detection:** Scan prompts, code and memory for
    secrets. Observability logs should not capture sensitive
    information; redaction is enforced.

## 15 Product Design: An Ideal Debuggable Multi‑Agent Coding Environment

### 15.1 Information architecture and key screens

An ideal system integrates multiple views into a cohesive product:

1.  **Code Editor:** A familiar IDE (VS Code, WebStorm) augmented with
    agent overlays. Code diffing is semantic and grouped by intent.
    Hovering over a line shows the agent, task and reasoning.
2.  **Browser Preview:** Displays the running application with
    colour‑coded overlays and a toolbar to toggle provenance layers,
    visual diffs, accessibility highlights and coverage maps.
3.  **Visual Change Overlay:** On top of the preview, this layer
    highlights modified UI elements, with filters by agent and change
    type.
4.  **Provenance Layer:** A hidden layer toggled by a keyboard shortcut
    reveals agent IDs, timestamps, and reasoning for every DOM node and
    component.
5.  **State Inspector:** A panel showing the current state JSON for each
    agent and the diff from previous snapshots. Users can search, sort
    and compare states.
6.  **Agent Timeline:** A horizontal timeline with swimlanes for each
    agent. Spans depict tasks, tool calls, messages, test runs and
    reasoning steps. Clicking a span opens the state snapshot and
    reasoning. Filters by agent, tool, task and error make navigation
    manageable.
7.  **Task Graph:** Displays the hierarchy of tasks and subtasks. Nodes
    show status (in progress, succeeded, failed, rolled back). Edges
    show dependencies and handoffs.
8.  **Change Provenance Ledger:** A ledger view listing all change
    entries. Users can query, filter and drill down into specific
    entries. The ledger is integrated with the diff viewer and tests.
9.  **Semantic Diff Viewer:** Shows grouped diffs with AST‑level
    details, code and UI diffs side by side. Comments and review notes
    attach to diff sections.
10. **Playwright Visual Test Viewer:** Embeds the Playwright trace
    viewer to show test artefacts. Tests are mapped to changed
    components. Coverage overlays appear in the preview.
11. **Rollback & Replay Console:** Lists available checkpoints and
    branches. Users can replay runs using recorded traces or create new
    branches from checkpoints.
12. **Risk Dashboard:** Shows risk and confidence heatmaps across the
    codebase, UI and tasks. Lists high‑risk changes requiring immediate
    attention.
13. **Human Review Workspace:** A central place where reviewers see
    summaries, diffs, evidence cards, test results, risk indicators and
    can approve or reject changes. Comments feed back into the agent
    system.
14. **Conflict‑Resolution View:** Presents conflicting changes with
    side‑by‑side proposals and reasoning. Allows merging and final
    decision logging.
15. **Observability Trace Explorer:** Visualises distributed traces with
    cross‑agent timelines, spans, logs and metrics. Enables filtering by
    latency, error, cost or agent.
16. **Memory & Context Inspector:** Shows prompts, retrieved memories,
    context windows, summarisation logs and memory read/write
    operations. Helps detect context drift and hallucinations.
17. **Deployment Readiness Report:** Summarises readiness for
    deployment: passed tests, risk level, coverage, outstanding
    conflicts, required human approvals and compliance status.

### 15.2 User flows

1.  **Investigate a failing test:** The developer navigates to the risk
    dashboard and sees a failing test. Clicking the failure opens the
    Playwright trace with before/after snapshots and highlights the
    component modified by Agent B. The ledger shows that Agent B changed
    the corresponding file due to a bug report. The state inspector
    reveals that the agent misread the API response. The developer
    rewinds to before the agent's decision, edits the prompt and
    replays; the test passes.
2.  **Understand a visual change:** In the browser preview, the
    developer toggles the provenance layer and sees that the header
    colour changed. Hovering reveals the responsible Agent C, the task
    "rebrand colours," the commit ID and the reasoning summary. A
    before/after screenshot appears in the side panel. The semantic diff
    viewer shows the CSS variable change grouped under "Copy and style
    changes."
3.  **Review a pull request:** The reviewer opens the human review
    workspace. Changes are grouped by intent: bug fixes, refactors and
    new features. Each group lists affected files, tests, risk levels
    and confidence scores. The reviewer filters to high‑risk changes
    touching authentication. They click into the diff, see the agent's
    reasoning, run the Playwright traces to verify UI behaviour, inspect
    memory usage, and then approve or request changes.

## 16 Concrete Feature Inventory

The table below catalogues **80+ debuggability features**, grouped by
category. Implementation difficulty is qualitatively estimated on a 1--5
scale (1 = straightforward, 5 = research‑grade). Failure modes describe
how features might mislead or fail.

  ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  Category           Feature name                         Problem solved                                                                                                                                                                     How it works                                                                                                                                                                          Data required     UI location     Users benefited        Difficulty   Impact   Failure modes           Example scenario
  ------------------ ------------------------------------ ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ----------------- --------------- ---------------------- ------------ -------- ----------------------- -----------------
  **Visual           Agent colour overlays                Identify which agent modified which UI element                                                                                                                                     Each agent is assigned a colour; modified elements outlined accordingly                                                                                                               Mapping between   Browser         Developers, reviewers, 2            High     Colour overload;        A reviewer sees
  explainability**                                                                                                                                                                                                                                                                                                                                                                                                                 UI nodes and      preview, design designers                                    mis‑mapping if DOM      that Agent A
                                                                                                                                                                                                                                                                                                                                                                                                                                   agent‑modified    canvas                                                       changes dynamically     modified a button
                                                                                                                                                                                                                                                                                                                                                                                                                                   diffs                                                                                                  and Agent B
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          changed its
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          tooltip

                     Hover annotations                    Show who, when, why for each element                                                                                                                                               Tooltips display agent ID, timestamp, task, related files/tests and reasoning summary when hovering                                                                                   Provenance        Browser preview Reviewers, QA          2            High     Annotation clutter;     Hovering over a
                                                                                                                                                                                                                                                                                                                                                                                                                                   metadata from                                                                  outdated metadata       table row reveals
                                                                                                                                                                                                                                                                                                                                                                                                                                   ledger                                                                                                 it was added by a
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          data‑import agent
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          responding to a
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          CSV upload

                     Visual diff maps                     Visualise before‑and‑after UI differences                                                                                                                                          Compute pixel and semantic diffs; highlight layout, copy, colour and spacing changes                                                                                                  Screenshots and   Diff viewer,    Designers, testers     3            High     False positives due to  After editing CSS
                                                                                                                                                                                                                                                                                                                                                                                                                                   DOM snapshots     browser overlay                                              dynamic content         variables, the
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          diff highlights
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          only the
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          rebranded colours
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          without noise

                     Conflict overlays                    Detect overlapping changes                                                                                                                                                         Overlay shows multi‑coloured regions where multiple agents modified the same element; click to resolve                                                                                Change provenance Browser preview Reviewers, agents      3            Medium   Overlaps may be benign; Two agents modify
                                                                                                                                                                                                                                                                                                                                                                                                                                   ledger                                                                         may overwhelm if many   the navigation
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  agents                  menu; conflict
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          overlay shows
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          conflicting
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          classes

                     Timeline playback                    Replay UI evolution across agent steps                                                                                                                                             Sequence of UI snapshots aligned with timeline; slider to scrub through states                                                                                                        State snapshots,  Browser preview Developers, testers    3            Medium   Large storage for       Developer scrubs
                                                                                                                                                                                                                                                                                                                                                                                                                                   screenshots                                                                    snapshots; may miss     timeline to see
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  intermediate states     when a layout
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          shift was
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          introduced

                     Heatmaps                             Visualise agent effort distribution                                                                                                                                                Heatmaps overlay intensity where agents spent time or changes                                                                                                                         Interaction logs, Browser preview Project managers       2            Low      Interpretations may     Heatmap shows
                                                                                                                                                                                                                                                                                                                                                                                                                                   diff counts                                                                    vary; bias if tasks     that Agent D
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  vary by complexity      spent most time
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          on checkout pages

  **State            Canonical state JSON                 Capture hidden agent state                                                                                                                                                         Structured JSON includes identity, inputs, outputs, reasoning, environment                                                                                                            Instrumentation   State inspector Developers, auditors   3            High     Information overload;   Auditor inspects
  representation**                                                                                                                                                                                                                                                                                                                                                                                                                 logs                                                                           privacy concerns        state to see
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          which files were
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          read before a bug
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          fix

                     State timeline and diffing           Compare reasoning/state across steps                                                                                                                                               Compute diffs across successive state JSONs; highlight changed fields                                                                                                                 Sequential        State           Developers             4            High     Complex diff            Developer
                                                                                                                                                                                                                                                                                                                                                                                                                                   snapshots         inspector,                                                   visualisation; may miss compares
                                                                                                                                                                                                                                                                                                                                                                                                                                                     ledger                                                       semantic equivalence    hypotheses before
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          and after reading
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          a file

                     Graph representation                 Visualise tasks and dependencies                                                                                                                                                   Use DAG to represent states and transitions; interactive graph viewer                                                                                                                 Ledger and state  Task graph view Developers, planners   4            Medium   Graph may become        Graph shows that
                                                                                                                                                                                                                                                                                                                                                                                                                                   snapshots                                                                      cluttered; layout       two subtasks
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  complexity              depend on the
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          same database
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          migration

                     Agent journals                       Provide human‑readable reasoning summaries                                                                                                                                         Agent summarises its reasoning and cites evidence; stored in ledger                                                                                                                   Reasoning logs,   Review UI       Reviewers, auditors    2            Medium   Summaries may omit      Reviewer reads
                                                                                                                                                                                                                                                                                                                                                                                                                                   citations                                                                      critical details;       the journal to
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  hallucinations          understand why a
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          function was
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          refactored

  **Provenance &     Change provenance ledger             Record all agent actions with causal links                                                                                                                                         Append entries with agent ID, task ID, inputs, outputs, diffs, reasoning, confidence and risk; maintain hash chain                                                                    Instrumentation   Ledger view,    Auditors, reviewers    4            High     Ledger may be tampered  Auditor queries
  ownership**                                                                                                                                                                                                                                                                                                                                                                                                                      logs, git         diff viewer                                                  if not secured; high    the ledger to
                                                                                                                                                                                                                                                                                                                                                                                                                                   metadata                                                                       storage                 find all changes
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          triggered by a
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          failing test

                     Line‑level attribution               Identify agent responsible for each code line                                                                                                                                      Extend git blame with agent metadata; annotate diff lines                                                                                                                             Commit metadata,  Code editor,    Developers, reviewers  2            Medium   Renamed/moved code may  Reviewer sees
                                                                                                                                                                                                                                                                                                                                                                                                                                   AST diffs         diff viewer                                                  break mapping           that a line was
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          originally
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          generated by
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          Agent E

                     Component‑level attribution          Track agent ownership of UI components                                                                                                                                             Map component IDs to agents; update on modifications                                                                                                                                  Component         Browser         Designers, testers     3            Medium   Components may be       Designer sees
                                                                                                                                                                                                                                                                                                                                                                                                                                   mapping, ledger   overlay, design                                              reused; mapping may     that the modal
                                                                                                                                                                                                                                                                                                                                                                                                                                                     tool                                                         break                   component was
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          last touched by
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          Agent F

                     Decision‑level attribution           Trace decisions across workflows                                                                                                                                                   Create decision nodes in ledger with reasons and outcomes                                                                                                                             State snapshots,  Timeline view,  Managers               4            Medium   Capturing reasoning can Manager queries
                                                                                                                                                                                                                                                                                                                                                                                                                                   prompts           ledger                                                       be heavy; privacy       why the system
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  concerns                chose to refactor
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          rather than patch

  **Communication &  Conversation timeline                Visualise multi‑agent conversation                                                                                                                                                 Gantt‑style timeline with swimlanes per agent showing messages, tool calls and                                                                                                        Message logs,     Collaboration   Developers             4            High     Large conversations may Developer finds
  collaboration**                                                                                                                                                                                                                            tasks[\[17\]](https://www.augmentcode.com/guides/debug-parallel-ai-agents#:~:text=The%20Observability%20Gap%3A%20No%20Mainstream,Agent%20Visualization)                               tool calls        view                                                         be overwhelming         the moment when
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          two agents
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          miscommunicated

                     Summarised messages                  Reduce cognitive load                                                                                                                                                              Summarise long messages into bullet points with links to full content                                                                                                                 Chat logs,        Conversation    Reviewers              2            Medium   Summaries may miss      Reviewer quickly
                                                                                                                                                                                                                                                                                                                                                                                                                                   summarisation     view                                                         nuance                  skims agent
                                                                                                                                                                                                                                                                                                                                                                                                                                   model                                                                                                  dialogues

                     Task handoff records                 Clarify delegation                                                                                                                                                                 Record handoffs with subtask description, arguments and expected outputs                                                                                                              Ledger, message   Timeline, task  Developers             3            Medium   Incomplete handoffs     Developer sees
                                                                                                                                                                                                                                                                                                                                                                                                                                   logs              graph                                                        hinder tracing          that the coder
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          agent delegated
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          test writing to
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          the tester

                     Disagreement tracking                Detect conflicts in conversation                                                                                                                                                   Analyse messages and decisions to identify contradictions; highlight unresolved issues                                                                                                Message logs,     Conversation    Managers               4            Medium   Natural language        Agents disagree
                                                                                                                                                                                                                                                                                                                                                                                                                                   state diffs       view                                                         ambiguity; false        on API endpoint;
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  positives               the system flags
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          the disagreement

                     Critic/reviewer agents               Provide independent evaluation                                                                                                                                                     Dedicated agents evaluate outputs and provide critiques                                                                                                                               Outputs,          Review UI       Developers, quality    3            Medium   Critic may miss subtle  Critic agent
                                                                                                                                                                                                                                                                                                                                                                                                                                   evaluation                        teams                                        issues; misalign with   notes that error
                                                                                                                                                                                                                                                                                                                                                                                                                                   prompts                                                                        human preferences       handling is
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          missing in a
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          patch

                     Dependency graphs                    Prevent deadlocks and duplicate work                                                                                                                                               Represent subtasks and dependencies; detect cycles                                                                                                                                    Task assignments, Task graph      Planners,              4            Medium   Graph complexity;       Graph shows a
                                                                                                                                                                                                                                                                                                                                                                                                                                   state                             orchestrators                                dynamic dependencies    cycle between
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          tasks A and B

                     Evidence quality scoring             Calibrate trust                                                                                                                                                                    Score evidence sources by reliability and recency; display scores                                                                                                                     Document          Review UI       Reviewers, auditors    3            Medium   Subjective scoring;     Low‑quality
                                                                                                                                                                                                                                                                                                                                                                                                                                   metadata,                                                                      might mislead           evidence triggers
                                                                                                                                                                                                                                                                                                                                                                                                                                   retrieval logs                                                                                         extra human
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          review

                     Human intervention tools             Enable interactive debugging                                                                                                                                                       Allow humans to edit messages, prompts or state and replay                                                                                                                            Trace logs,       Debug console   Developers             4            High     Risk of unintentional   Developer
                                                                                                                                                                                                                                                                                                                                                                                                                                   prompts                                                                        side‑effects            corrects a prompt
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          and reruns the
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          agent

  **Testing &        Playwright trace attachment          Record and display test artefacts                                                                                                                                                  Capture DOM snapshots, screenshots, network logs and console                                                                                                                          Test runs, trace  Test viewer     Testers, reviewers     2            High     Large trace files;      Reviewer watches
  coverage**                                                                                                                                                                                                                                 logs[\[13\]](https://www.bigbinary.com/blog/how-to-analyze-playwright-traces#:~:text=What%20are%20Playwright%20traces%3F); attach to ledger                                           files                                                                          privacy of network logs a test run to
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          debug a failing
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          click

                     UI coverage overlay                  Highlight tested vs. untested areas                                                                                                                                                Map test locators to UI regions; overlay coverage colours                                                                                                                             Test metadata,    Browser preview Testers, QA            3            Medium   Locators may change;    Overlay shows
                                                                                                                                                                                                                                                                                                                                                                                                                                   locator mapping                                                                dynamic elements        that the new
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          dropdown has no
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          tests

                     Test mapping to agent actions        Connect tests to code changes                                                                                                                                                      Link test suites to changed files and agents who modified them                                                                                                                        Ledger, test      Review UI       Reviewers              3            Medium   Complex mapping if      Reviewer sees
                                                                                                                                                                                                                                                                                                                                                                                                                                   metadata                                                                       tests are generic       that Agent G
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          added a test for
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          the new API but
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          not for the UI

                     Visual flakiness analysis            Detect flaky tests                                                                                                                                                                 Display pass/fail histograms and runtime metrics per test                                                                                                                             Test run history  Test viewer     QA                     3            Medium   Flakiness may be        Test passes
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  environment‑dependent   locally but fails
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          in CI; flakiness
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          analysis reveals
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          network latency

                     User‑journey graphs                  Visualise end‑to‑end tests                                                                                                                                                         Represent flows through the application; overlay agent changes                                                                                                                        Test definitions, Coverage viewer Product managers       4            Medium   Large flows may be      Journey graph
                                                                                                                                                                                                                                                                                                                                                                                                                                   coverage                                                                       complex                 shows that
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          checkout flow
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          touches a
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          modified module

                     Natural‑language test explanations   Make tests readable                                                                                                                                                                Generate plain‑English descriptions of what each test asserts                                                                                                                         Test code, code   Review UI       Reviewers,             2            Medium   Generated summaries may Reviewer reads an
                                                                                                                                                                                                                                                                                                                                                                                                                                   analysis                          non‑technical                                be inaccurate           explanation of a
                                                                                                                                                                                                                                                                                                                                                                                                                                                                     stakeholders                                                         test verifying
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          discount logic

  **Semantic         AST diffing                          Identify meaningful code                                                                                                                                                           Parse code into ASTs and compare syntax nodes; group by function/class                                                                                                                Code snapshots    Diff viewer     Developers, reviewers  4            High     AST parsers may lag     Diff shows that a
  diffing**                                               changes[\[23\]](https://baz.co/resources/why-your-code-gen-ai-doesnt-understand-diffs#:~:text=Where%20Git%20diffing%20focuses%20on,and%20structure%20between%20those%20elements)                                                                                                                                                                                                                                                                        behind language         function body
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  features                changed without
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          noise from
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          formatting

                     Type‑aware diff                      Detect API changes                                                                                                                                                                 Use type checkers to compare function signatures and class hierarchies                                                                                                                Type metadata,    Diff viewer     API owners             4            High     Type systems vary       Type diff reveals
                                                                                                                                                                                                                                                                                                                                                                                                                                   AST                                                                            across languages        a missing
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          parameter in an
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          API

                     Data‑flow/control‑flow diff          Understand runtime impact                                                                                                                                                          Compute control‑flow graphs and data‑flow relations; highlight changes                                                                                                                Program analysis  Diff viewer     Developers             5            High     Computationally         Data‑flow diff
                                                                                                                                                                                                                                                                                                                                                                                                                                   results                                                                        expensive; hard to      shows that error
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  visualise               handling is
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          bypassed

                     API contract diff                    Detect breaking API changes                                                                                                                                                        Compare OpenAPI/GraphQL specs; highlight removed endpoints or fields                                                                                                                  API schemas       Diff viewer     Backend/Frontend teams 3            Medium   Versions may not be     Diff warns that
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  available; may ignore   the `price` field
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  semantics               type changed from
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          number to string

                     Dependency graph diff                Track dependency changes                                                                                                                                                           Compare dependency trees; show added/removed/updated packages                                                                                                                         Package manifests Diff viewer     Security teams         2            Medium   Indirect dependencies   Diff shows that a
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  may hide                new library
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  vulnerabilities         introduces a
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          vulnerable
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          transitive
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          dependency

                     Schema diff                          Compare database schemas                                                                                                                                                           Diff migration files and database introspection; highlight added tables, columns, constraints                                                                                         Migrations,       DB viewer       DBAs                   3            Medium   Schema may drift from   Diff reveals that
                                                                                                                                                                                                                                                                                                                                                                                                                                   schema snapshots                                                               migrations              a column type
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          change might
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          cause downtime

                     Component tree diff                  Track UI structure changes                                                                                                                                                         Compare component hierarchies; highlight added/removed components                                                                                                                     Component mapping Diff viewer,    Front‑end developers   4            Medium   Component names may     Diff shows that a
                                                                                                                                                                                                                                                                                                                                                                                                                                                     design tool                                                  change                  legacy `<Form>`
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          was replaced by
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          `<FormWizard>`

                     Prompt diff                          Track prompt evolution                                                                                                                                                             Compare versions of prompts; highlight added/removed instructions/examples                                                                                                            Prompt history    Prompt          Prompt engineers       2            Medium   Diff semantics are      Diff shows that
                                                                                                                                                                                                                                                                                                                                                                                                                                                     inspector                                                    subjective              safety
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          instructions were
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          removed

                     Performance/security/accessibility   Detect non‑functional changes                                                                                                                                                      Compare telemetry (latency, memory, CPU), security taint flows and accessibility metrics                                                                                              Telemetry,        Risk dashboard  Performance/security   4            Medium   Metrics may be noisy;   Diff shows
                     diff                                                                                                                                                                                                                                                                                                                                                                                                          security scan,                    teams                                        correlation vs.         latency increased
                                                                                                                                                                                                                                                                                                                                                                                                                                   accessibility                                                                  causation               after a refactor
                                                                                                                                                                                                                                                                                                                                                                                                                                   analysis                                                                                               

  **Replay &         Deterministic replay                 Reproduce agent runs[\[16\]](https://www.augmentcode.com/guides/debug-parallel-ai-agents#:~:text=Pattern%206%3A%20Deterministic%20Replay)                                          Record all prompts, tool calls, responses and state; replay by substituting recorded outputs                                                                                          Trace logs        Debug console   Developers             4            High     Storage overhead;       Developer replays
  rollback**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      non‑deterministic       a failing run
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  external services       offline

                     Checkpointing                        Save state snapshots                                                                                                                                                               Create checkpoints after each sub‑goal; store file system, DB, state JSON                                                                                                             State snapshots   Rollback        Developers             3            Medium   Large snapshot sizes;   Developer
                                                                                                                                                                                                                                                                                                                                                                                                                                                     console                                                      snapshot frequency      restores state
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          before a harmful
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          migration

                     Branch‑per‑agent                     Isolate parallel work[\[10\]](https://www.augmentcode.com/guides/debug-parallel-ai-agents#:~:text=Pattern%202%3A%20Isolated%20Git%20Worktrees,for%20Parallel%20Agents)             Use git worktrees/branches per agent; later merge via semantic diffs                                                                                                                  Git repo,         Version control Developers             3            High     Merge conflicts;        Each agent works
                                                                                                                                                                                                                                                                                                                                                                                                                                   worktrees                                                                      dependency duplication  in a separate
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          branch and merges
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          after tests pass

                     Sandbox‑per‑agent                    Execute code safely[\[25\]](https://www.augmentcode.com/guides/debug-parallel-ai-agents#:~:text=system%20state%20beyond%20their%20intended,access%20to%20the%20control%20plane)    Run agents in containerised sandboxes with scoped credentials and allowed files                                                                                                       Docker,           Execution       DevOps                 4            High     Container overhead      A misbehaving
                                                                                                                                                                                                                                                                                                                                                                                                                                   credentials       engine                                                                               agent cannot
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          corrupt the main
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          environment

                     Causal rollback                      Undo changes by cause                                                                                                                                                              Use provenance ledger to remove effects and dependent changes                                                                                                                         Ledger, state     Rollback        Developers             4            High     Complex dependency      Rollback reverts
                                                                                                                                                                                                                                                                                                                                                                                                                                   snapshots         console                                                      resolution              both the bug fix
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          and subsequent
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          tests relying on
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          it

                     Side‑by‑side solution comparison     Compare alternative agent outputs                                                                                                                                                  Show two or more branches/diffs side by side; allow selective merging                                                                                                                 Branches, diffs   Review UI       Reviewers              3            Medium   Many alternatives may   Reviewer merges
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  be overwhelming         the best UI
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          design from two
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          agents

  **Observability &  Distributed tracing                  Collect traces across agents                                                                                                                                                       Instrument code to emit spans with agent IDs, tool calls, latencies, costs[\[15\]](https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/#:~:text=Attributes%3A)     Instrumentation   Trace explorer  Observability teams    3            High     Performance overhead;   Trace shows a
  metrics**                                                                                                                                                                                                                                                                                                                                                                                                                        hooks                                                                          privacy of prompts      latency spike due
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          to network call

                     Cost and resource tracking           Monitor token usage and costs                                                                                                                                                      Include token counts, model costs, API costs in                                                                                                                                       Instrumentation   Metrics         Finance, DevOps        2            Medium   Complex cost allocation Dashboard shows a
                                                                                                                                                                                                                                             spans[\[31\]](https://langfuse.com/blog/2024-07-ai-agent-observability-with-langfuse#:~:text=LLMs%20are%20stochastic%20by%20nature%2C,advantage%20of%20using%20agentic%20workflows)   logs, billing     dashboard                                                    across tasks            task costing \$20
                                                                                                                                                                                                                                                                                                                                                                                                                                   data                                                                                                   due to repeated
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          model calls

                     Error budgets                        Define acceptable failure rates                                                                                                                                                    Track number of regressions, flakiness incidents, failed merges; compare to budget                                                                                                    Test results,     Risk dashboard  Management             3            Medium   Budgets may be          Exceeding budget
                                                                                                                                                                                                                                                                                                                                                                                                                                   merge logs                                                                     arbitrary; unrealistic  triggers rollback
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  expectations            or human
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          intervention

                     Token/memory audit                   Track context usage                                                                                                                                                                Log which memories/files were read or written and which prompts were used                                                                                                             Memory logs       Memory          Security, auditors     3            Medium   Logging sensitive data; Auditor finds
                                                                                                                                                                                                                                                                                                                                                                                                                                                     inspector                                                    storage overhead        that secret keys
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          were loaded into
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          context

                     Prompt injection detection           Prevent malicious prompts                                                                                                                                                          Scan prompts and inputs for injection patterns; enforce guardrails                                                                                                                    Prompt text       Security logs   Security teams         4            Medium   False positives;        System blocks a
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  evolving threats        malicious prompt
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          that tries to
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          exfiltrate data

  **Review &         Agent‑authored summaries with        Summarise changes                                                                                                                                                                  Agents provide human‑readable summaries with citations and links to tests                                                                                                             Ledger entries    Review          Reviewers              2            Medium   Summaries may omit      Reviewer sees
  governance**       evidence                                                                                                                                                                                                                                                                                                                                                                                                                        workspace                                                    important details       summary of test
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          additions with
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          links to
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          screenshots

                     Risk & confidence badges             Communicate uncertainty                                                                                                                                                            Visual badges indicate risk level (red/orange/green) and confidence (high/medium/low)                                                                                                 Risk model,       Review UI       Reviewers              2            Medium   Badge thresholds may be A high‑risk,
                                                                                                                                                                                                                                                                                                                                                                                                                                   confidence scores                                                              subjective              low‑confidence
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          change triggers
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          deeper review

                     Evidence cards                       Attach test, performance and accessibility evidence                                                                                                                                Cards show before/after snapshots, metrics, accessibility diffs, flakiness stats                                                                                                      Test logs,        Review          Reviewers, QA          3            High     Evidence may be         Evidence card
                                                                                                                                                                                                                                                                                                                                                                                                                                   telemetry         workspace                                                    voluminous; selective   shows that the
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  display needed          new modal passes
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          accessibility
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          checks

                     Reviewer checklists                  Suggest review focus areas                                                                                                                                                         Based on change types, generate a checklist (security, error handling, accessibility)                                                                                                 Risk model,       Review UI       Reviewers              2            Medium   Checklist fatigue; may  Checklist prompts
                                                                                                                                                                                                                                                                                                                                                                                                                                   heuristics                                                                     miss context            reviewer to check
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          translation keys

                     Review filters                       Focus on relevant changes                                                                                                                                                          Filter diffs by agent, task, risk, file type, UI region, test coverage and confidence                                                                                                 Ledger metadata   Review          Reviewers              3            High     Complex filter UI       Reviewer filters
                                                                                                                                                                                                                                                                                                                                                                                                                                                     workspace                                                                            to only high‑risk
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          changes touching
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          database

                     Provenance badges                    Show agent identity                                                                                                                                                                Badges indicate which agent authored each file or line                                                                                                                                Ledger metadata   Code editor,    Reviewers, auditors    2            Medium   Visual clutter          Badge next to
                                                                                                                                                                                                                                                                                                                                                                                                                                                     diff viewer                                                                          function shows it
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          was generated by
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          an LLM

                     Assumption warnings                  Highlight unverified claims                                                                                                                                                        Highlight parts of reasoning or code that rely on unverified assumptions                                                                                                              Reasoning logs,   Review UI       Reviewers              3            Medium   False positives;        Warning shows
                                                                                                                                                                                                                                                                                                                                                                                                                                   evidence                                                                       uncertain               that the
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  classification          algorithm assumes
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          sorted input

                     Human approval gates                 Require manual approval for high‑risk changes                                                                                                                                      Block merging until human reviewer approves                                                                                                                                           Risk scores,      CI/CD pipeline  Compliance, management 2            Medium   Slower deployment; risk High‑risk schema
                                                                                                                                                                                                                                                                                                                                                                                                                                   policy                                                                         of override             change awaits DBA
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          approval

  **Prompt & memory  Prompt versioning                    Track prompt evolution                                                                                                                                                             Store versions of prompts and diff them                                                                                                                                               Prompt history    Prompt          Prompt engineers       2            Medium   Many versions; diff     Engineer sees
  debugging**                                                                                                                                                                                                                                                                                                                                                                                                                                        inspector                                                    semantics               that safety
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          instructions were
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          removed in a
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          prompt revision

                     Context window visualisation         Show files/docs included in context                                                                                                                                                Visual lists or graphs show included files, order, and sizes                                                                                                                          Context logs      Memory          Developers             2            Medium   Large contexts may be   Developer
                                                                                                                                                                                                                                                                                                                                                                                                                                                     inspector                                                    cluttered               realises a
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          critical file was
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          omitted

                     Memory read/write logs               Audit memory usage                                                                                                                                                                 Record memory operations; attach to agents and tasks                                                                                                                                  Memory logs       Memory          Security teams         2            Medium   Privacy concerns        Log shows agent
                                                                                                                                                                                                                                                                                                                                                                                                                                                     inspector                                                                            loaded outdated
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          research notes

                     Summarisation audit                  Analyse summarisation quality                                                                                                                                                      Compare original documents to summaries; highlight dropped details                                                                                                                    Summaries,        Memory          Prompt engineers       4            Medium   Hard to quantify        Audit shows that
                                                                                                                                                                                                                                                                                                                                                                                                                                   original docs     inspector                                                    summarisation quality   summary omitted
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          security
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          recommendations

  **Conflict         Conflict map                         Visualise conflicting changes                                                                                                                                                      Graph where nodes are agents/resources and edges indicate conflicts                                                                                                                   Ledger, diff      Conflict view   Reviewers              3            Medium   Graph complexity; may   Conflict map
  resolution**                                                                                                                                                                                                                                                                                                                                                                                                                     analysis                                                                       be unclear              shows tests
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          removed by one
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          agent and added
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          by another

                     Automatic merge suggestions          Propose resolution strategies                                                                                                                                                      Use CRDTs or heuristics to suggest merges; ask agents or humans to approve                                                                                                            Diffs, state      Conflict view   Developers             4            Medium   Suggestions may be      System suggests
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  incorrect               merging two style
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          changes into one

                     Assumption tracking                  Compare assumptions across agents                                                                                                                                                  Record assumptions; detect contradictory ones; prompt resolution                                                                                                                      Reasoning logs    Conflict view,  Planners               3            Medium   Hard to extract         Agents assume
                                                                                                                                                                                                                                                                                                                                                                                                                                                     task graph                                                   assumptions; false      different date
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  positives               formats; system
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          flags conflict

  **Risk &           Blast radius analysis                Estimate impact of changes                                                                                                                                                         Analyse dependency graph to compute reachable nodes (functions, components) from a change                                                                                             Code graph        Risk dashboard  Managers               4            Medium   Graph analysis          Blast radius
  uncertainty**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   complexity              shows that a
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          helper function
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          touches payment
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          processing

                     Risk heatmaps                        Visualise risk distribution                                                                                                                                                        Colour‑code files/components by risk score                                                                                                                                            Risk model        Risk dashboard  Reviewers, managers    3            Medium   May mislead if risk     Heatmap shows
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  model is wrong          that
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          authentication
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          files are high
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          risk

                     Verification status tags             Track testing and review status                                                                                                                                                    Assign tags like Untested, Tested‑Pass, Human‑Approved to each change                                                                                                                 Test results,     Review          Reviewers              2            Medium   Tag accuracy; stale     Tag shows that a
                                                                                                                                                                                                                                                                                                                                                                                                                                   review logs       workspace                                                    status                  function is
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          Untested,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          prompting
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          additional tests

                     Uncertainty badges                   Communicate low confidence                                                                                                                                                         Attach icons or colours to low‑confidence changes                                                                                                                                     Confidence model  Review UI       Reviewers              2            Medium   Overuse may reduce      Low‑confidence
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  trust                   badge on a new
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          algorithm invites
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          deeper review

  **Accessibility,   Accessibility diff panel             Compare accessibility trees                                                                                                                                                        Show before/after diffs of roles, labels, focus order, etc.                                                                                                                           Accessibility     Diff viewer     Accessibility experts  4            Medium   Complex representation; Panel shows that
  security &                                                                                                                                                                                                                                                                                                                                                                                                                       snapshots                                                                      false positives         an ARIA label was
  compliance**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            removed

                     Keyboard navigation trace            Replay navigation sequences                                                                                                                                                        Capture keyboard interactions; highlight focus traps                                                                                                                                  Browser           Accessibility   QA                     3            Medium   Hard to simulate all    Trace reveals
                                                                                                                                                                                                                                                                                                                                                                                                                                   automation logs   view                                                         states                  that a modal
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          traps focus
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          incorrectly

                     Security taint diff                  Track data flows                                                                                                                                                                   Perform taint analysis to detect insecure flows; diff before/after                                                                                                                    Static analysis   Risk dashboard  Security teams         5            High     Analysis may be         Diff shows that
                                                                                                                                                                                                                                                                                                                                                                                                                                   results                                                                        imprecise; false        unsanitised input
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  positives               flows to DB

                     Permission boundary diff             Compare authorisation logic                                                                                                                                                        Detect changes in access control policies or routes                                                                                                                                   Auth config, code Risk dashboard  Security teams         3            Medium   Complex policies;       Diff shows that
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  dynamic auth            admin route
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          became public

                     PII flow diff                        Detect privacy regressions                                                                                                                                                         Analyse data flows of PII; diff across versions                                                                                                                                       Data flow         Privacy panel   Compliance teams       4            High     Hard to detect implicit Diff shows that
                                                                                                                                                                                                                                                                                                                                                                                                                                   analysis                                                                       PII flows               email addresses
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          are now logged

                     Audit trails                         Record compliance‑relevant events                                                                                                                                                  Log data retention changes, cookie updates, analytics calls, etc.                                                                                                                     Logs, ledger      Audit view      Auditors               2            Medium   Large logs; privacy     Auditor sees when
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  concerns                telemetry was
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          changed to
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          include user IDs
  ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

## 17 Evaluation Framework

To assess whether debuggability features improve outcomes, design
controlled experiments and field studies. Key metrics include:

-   **Time to understand a change:** Measure how long reviewers take to
    understand why a change was made and what it affects. Compare
    baseline tools (raw diffs) to the proposed system.
-   **Time to identify regression cause:** When presented with a failing
    test, measure the time taken to identify the responsible agent and
    change.
-   **Time to safely approve a pull request:** Record the end‑to‑end
    review time, including reading summaries, inspecting evidence and
    running tests.
-   **Hidden regressions caught:** Count the number of regressions
    detected by testers that were not caught by baseline tools.
-   **Unsupported agent claims caught:** Count claims that lacked
    evidence and were flagged by the system.
-   **Trust calibration:** Use surveys to measure whether reviewers'
    confidence matches the actual reliability of changes.
    Over‑confidence indicates false trust; under‑confidence indicates
    friction.
-   **Reduction in duplicated agent work:** Track duplicate code or
    tasks across agents; the system should reduce duplicates by conflict
    detection and heatmaps.
-   **Failed merges and conflicts:** Monitor the number of merge
    conflicts or rollbacks required.
-   **Flaky tests:** Compare flakiness rates before and after improved
    testing and coverage overlays.
-   **Rollback speed:** Measure how quickly developers can rollback to a
    previous state and resume work.
-   **Coverage of changed behaviours:** Evaluate test coverage before
    and after using the system; improved coverage should correlate with
    fewer regressions.
-   **Attribution accuracy:** Validate that the system correctly
    attributes changes and decisions to agents by cross‑checking with
    ground truth.
-   **User satisfaction and cognitive load:** Use NASA‑TLX or similar
    surveys to measure perceived workload when using the system.

### Benchmark tasks

Create benchmark tasks that mirror real‑world agent coding scenarios:
refactoring code, adding features, fixing bugs and writing tests. For
each task, prepare ground‑truth provenance data and intentional bugs.
Compare teams using the new system vs. baseline. Evaluate metrics listed
above. Additionally, replicate the AGDebugger study by letting
participants debug multi‑agent workflows and measure their ability to
steer agents and discover
errors[\[18\]](https://arxiv.org/pdf/2503.02068).

## 18 Implementation Architecture

### 18.1 Minimum viable implementation (MVP)

1.  **Instrumentation & logging:** Instrument agent frameworks (e.g.,
    LangGraph, CrewAI, AutoGen) with middleware that emits structured
    logs containing agent IDs, task IDs, prompts, responses, tool calls,
    file reads/writes and state snapshots. Use OpenTelemetry for trace
    propagation and generative AI
    attributes[\[27\]](https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/#:~:text=Attributes%3A).
2.  **State & ledger storage:** Store snapshots and ledger entries in a
    document store (e.g., MongoDB) and event store (e.g., Kafka). Git
    worktrees provide
    isolation[\[10\]](https://www.augmentcode.com/guides/debug-parallel-ai-agents#:~:text=Pattern%202%3A%20Isolated%20Git%20Worktrees,for%20Parallel%20Agents);
    commit metadata includes agent IDs.
3.  **Visual overlay server:** Build a web overlay that runs in the
    development server. It fetches provenance metadata via a WebSocket
    and overlays highlights on the DOM. A VS Code extension displays
    diff overlays and state inspector.
4.  **Test integration:** Integrate Playwright tracing by adding
    `context.tracing.start/stop` around test runs. Store `.zip` trace
    files and display them with the Playwright trace viewer in the
    UI[\[13\]](https://www.bigbinary.com/blog/how-to-analyze-playwright-traces#:~:text=What%20are%20Playwright%20traces%3F).
5.  **Semantic diffing:** Use existing AST diff tools (e.g., Difftastic
    with Tree‑sitter) to compute diffs. Group diffs by heuristics (e.g.,
    file type, function names) and annotate with agent metadata.
6.  **Simple dashboard:** Build dashboards for the ledger, timeline and
    diff viewer using React and D3.js. Provide filters and search.
7.  **CI integration:** Add pre‑merge checks that compute risk scores,
    run tests, attach traces and block merges requiring human approval.

### 18.2 Advanced architecture

1.  **Event‑driven architecture:** Agents emit events to a message bus
    (Kafka) with topics per agent or task. A stream processor enriches
    events with context (e.g., linking to code lines) and writes to the
    ledger database.
2.  **Graph database:** Use Neo4j or JanusGraph to store the causal DAG
    of states, tasks and ledger entries. Queries traverse this graph for
    provenance and dependency analysis.
3.  **Snapshot storage and compression:** Use incremental snapshotting
    (copy‑on‑write) with deduplication to minimise storage. Snapshots
    can be stored in object storage (S3) with metadata in the database.
4.  **Real‑time overlay:** The browser overlay uses WebAssembly to diff
    DOM trees and compute pixel diffs on the client. It fetches
    provenance metadata asynchronously, using caching and throttling to
    avoid slowdown.
5.  **Context management engine:** Manage memory retrieval,
    summarisation and context windows. Use a vector store (e.g.,
    Pinecone) to store embeddings. The engine logs retrieval events with
    provenance data.
6.  **Security & privacy layer:** Integrate secret scanning and taint
    analysis pipelines. Use encryption at rest and in transit, with
    fine‑grained access controls. Redact sensitive content in logs.
7.  **AI evaluation and summarisation:** Deploy evaluation models
    (critics) and summarisation models to produce human‑readable
    summaries, risk and confidence estimates. Use retrieval‑augmented
    generation to ground agent reasoning in evidence.
8.  **Scalable UI:** Build a micro‑frontend architecture where each view
    (timeline, diff, test viewer) is a separate module. Use
    virtualization to render large lists efficiently.
9.  **Extensibility:** Provide plugin APIs for custom diff types (e.g.,
    shader diffs for games), domain‑specific tests and third‑party
    observability backends.

## 19 Current Landscape

Several tools and frameworks offer partial solutions:

-   **AI coding assistants:** Tools like GitHub Copilot, Anthropic
    Claude Code, Cursor, Devin and others help write and refactor code.
    They typically operate in single‑agent mode and lack deep debugging
    and provenance features. Some, like Cursor, introduce parallel
    agents with isolated
    branches[\[10\]](https://www.augmentcode.com/guides/debug-parallel-ai-agents#:~:text=Pattern%202%3A%20Isolated%20Git%20Worktrees,for%20Parallel%20Agents)
    but still rely on textual diffs for review.
-   **Multi‑agent frameworks:** AutoGen, LangGraph, CrewAI and Google
    ADK orchestrate multiple agents with role separation (planner,
    coder, critic). They provide high‑level traces but limited
    interactive debugging. AGDebugger adds interactive message resetting
    and timeline
    visualisation[\[7\]](https://arxiv.org/pdf/2503.02068#:~:text=Abstract%20Fully%20autonomous%20teams%20of,3%20Mar%202025)
    but focuses on conversation rather than code diffs and UI.
-   **Observability tools:** LangSmith, Langfuse, Arize Phoenix,
    Helicone and Braintrust provide tracing, logging and evaluation for
    LLM applications. LangSmith emphasises tracing runs and threads,
    with nested runs representing tool calls and LLM
    calls[\[32\]](https://www.langchain.com/blog/debugging-deep-agents-with-langsmith#:~:text=How%20Deep%20Agents%20are%20different,than%20simpler%20LLM%20applications).
    Langfuse collects traces via OTEL and focuses on metrics like
    latency, cost and error
    rates[\[33\]](https://langfuse.com/blog/2024-07-ai-agent-observability-with-langfuse#:~:text=What%20is%20AI%20Agent%20Observability%3F).
    However, these tools lack visual overlays, code attribution and UI
    diffing features.
-   **Visual testing platforms:** Playwright, Cypress and Percy\'s
    snapshot testing capture UI state and visual differences.
    Playwright's Trace Viewer provides DOM snapshots, screenshots,
    network logs and console
    logs[\[13\]](https://www.bigbinary.com/blog/how-to-analyze-playwright-traces#:~:text=What%20are%20Playwright%20traces%3F)[\[19\]](https://www.bigbinary.com/blog/how-to-analyze-playwright-traces#:~:text=1).
    Tools like NeetoPlaydash build dashboards for Playwright traces, but
    they are not integrated with agent provenance.
-   **Semantic diff tools:** Difftastic uses Tree‑sitter to produce AST
    diffs, while Baz builds an AST‑based code reviewer that reduces
    noise and detects meaningful
    changes[\[34\]](https://baz.co/resources/why-your-code-gen-ai-doesnt-understand-diffs#:~:text=Where%20Git%20diffing%20focuses%20on,and%20structure%20between%20those%20elements).
    GitHub's semantic diff for languages like TypeScript is improving,
    but mainstream code review remains line‑based. Tools rarely connect
    semantic diffs to agent reasoning.
-   **Version control and branching:** Git worktrees and branch
    isolation are used by Cursor's parallel agents
    feature[\[10\]](https://www.augmentcode.com/guides/debug-parallel-ai-agents#:~:text=Pattern%202%3A%20Isolated%20Git%20Worktrees,for%20Parallel%20Agents).
    However, merging multiple agent branches remains manual, and there
    is no provenance ledger.
-   **Multi‑agent provenance research:** Chang & Echizen propose
    symbolic chronicles for tracking multi‑agent contributions within
    generated
    content[\[11\]](https://arxiv.org/pdf/2504.12612v2#:~:text=ative%20chain%2C%20content%20undergoes%20successive,content%20in%20the%20very%20act).
    Their approach is a post‑hoc attribution, not integrated with code
    or UI changes. The field lacks end‑to‑end provenance systems for
    AI‑generated code.
-   **Human--computer interaction research:** The AGDebugger study
    demonstrates the value of interactive message editing and timeline
    visualisation for debugging multi‑agent
    systems[\[7\]](https://arxiv.org/pdf/2503.02068#:~:text=Abstract%20Fully%20autonomous%20teams%20of,3%20Mar%202025).
    It also shows that users rely more on editing messages than changing
    agent
    configurations[\[35\]](https://arxiv.org/pdf/2503.02068#:~:text=Although%20AGDebugger%20allows%20users%20to,over%20a%20longer%20debugging%20period).
    However, AGDebugger does not handle code, UI or test provenance.

**Gaps:** Existing tools do not provide unified provenance across code,
UI, tests and prompts; they lack semantic diff grouping; they have
limited conflict detection and risk scoring; and they rarely support
deterministic replay or rollback. Visual overlays connecting UI changes
to agent actions are largely absent. There is also no standard state
JSON or ledger format.

## 20 Final Recommendations and Roadmap

### 20.1 Priorities

**Must‑have:**

1.  **Structured logging and trace propagation:** Without agent IDs,
    correlation IDs and timestamps, debugging is
    impossible[\[8\]](https://www.augmentcode.com/guides/debug-parallel-ai-agents#:~:text=Parallel%20agent%20debugging%20becomes%20tractable,shared%20state%20reads%20and%20writes).
    Implement structured logging before deploying agents.
2.  **Isolated workspaces and sandboxing:** Use git worktrees or
    containerised sandboxes for each agent to avoid silent state
    overwrites[\[9\]](https://www.augmentcode.com/guides/debug-parallel-ai-agents#:~:text=Silent%20state%20overwrites%20occur%20when,Missing%20data)[\[10\]](https://www.augmentcode.com/guides/debug-parallel-ai-agents#:~:text=Pattern%202%3A%20Isolated%20Git%20Worktrees,for%20Parallel%20Agents).
3.  **Change provenance ledger and state snapshots:** Capture all agent
    actions, inputs, outputs and reasoning in a ledger with causal
    links. Store state JSON snapshots for inspection.
4.  **Visual overlays and diffing:** Provide colour‑coded UI overlays,
    before/after screenshots and semantic diffs to connect code changes
    to UI behaviour. Include Playwright trace integration for
    tests[\[13\]](https://www.bigbinary.com/blog/how-to-analyze-playwright-traces#:~:text=What%20are%20Playwright%20traces%3F).
5.  **Agent timeline and conversation view:** Show parallel agent runs
    in a timeline with swimlanes and summarised messages. Support
    interactive message editing and counterfactual testing, inspired by
    AGDebugger[\[18\]](https://arxiv.org/pdf/2503.02068).
6.  **Risk and confidence indicators:** Implement risk scoring based on
    change impact and confidence estimation to guide reviewers.
7.  **Human review interface:** Build a review workspace that groups
    changes by intent, shows evidence cards, and allows filtering by
    agent, risk and coverage.

**Should‑have:**

1.  **Semantic diffing and intent grouping:** Use AST diffing and type
    analysis to group changes by intent and reduce
    noise[\[34\]](https://baz.co/resources/why-your-code-gen-ai-doesnt-understand-diffs#:~:text=Where%20Git%20diffing%20focuses%20on,and%20structure%20between%20those%20elements).
2.  **Conflict detection and resolution tools:** Provide real‑time
    conflict detection across files, UI and tests with visual conflict
    maps. Offer automatic merge suggestions and assumption tracking.
3.  **Observability dashboards:** Integrate OTEL traces with dashboards
    showing latency, cost and error
    budgets[\[31\]](https://langfuse.com/blog/2024-07-ai-agent-observability-with-langfuse#:~:text=LLMs%20are%20stochastic%20by%20nature%2C,advantage%20of%20using%20agentic%20workflows).
4.  **State and memory inspection:** Expose prompt versions, context
    windows, and memory operations. Provide summarisation audits to
    detect dropped context.
5.  **Accessibility, security and compliance panels:** Diff
    accessibility trees, perform taint analysis, and track PII flows.
    Provide audit trails for compliance.
6.  **Deterministic replay and rollback:** Record runs for deterministic
    replay[\[16\]](https://www.augmentcode.com/guides/debug-parallel-ai-agents#:~:text=Pattern%206%3A%20Deterministic%20Replay),
    provide checkpointing and branch per agent. Support time‑travel
    debugging and causal rollback.

**Advanced:**

1.  **Machine‑learning‑based risk prediction:** Train models on
    historical agent runs to predict risk and confidence more
    accurately.
2.  **Automated evaluation and summarisation:** Use critic agents and
    evaluation models to automatically rate agent outputs and summarise
    reasoning.
3.  **Causal dependency maps and task graphs:** Visualise causal
    relationships between tasks, states and changes. Use graph
    algorithms to detect deadlocks and hidden couplings.
4.  **Real‑time pixel and DOM diffing:** Use WebAssembly for efficient
    in‑browser diffing and overlay rendering.
5.  **Plugin ecosystem:** Allow domain‑specific plugins for diff types,
    visualisations and tests.
6.  **Cryptographic provenance:** Use digital signatures and blockchain
    or Merkle trees to ensure the immutability of the provenance ledger.

**Experimental:**

1.  **Symbolic chronicle embedding:** Embed signed provenance
    information within the generated code or content
    itself[\[11\]](https://arxiv.org/pdf/2504.12612v2#:~:text=ative%20chain%2C%20content%20undergoes%20successive,content%20in%20the%20very%20act).
2.  **Self‑healing agents:** Agents detect their own conflicts and
    propose rollbacks or alternate solutions.
3.  **Collective agent conscience:** Shared memory of assumptions and
    beliefs across agents; conflict resolution becomes social
    negotiation.
4.  **Adaptive interface complexity:** The UI hides or reveals details
    based on user workload and expertise.

### 20.2 Roadmap

**First 30 days:**

-   Instrument agent frameworks with structured logging and OTEL traces.
-   Implement isolated worktrees and sandbox per agent.
-   Build a minimal ledger storing agent actions, file diffs and
    reasoning summaries.
-   Integrate Playwright tracing in the CI pipeline and attach traces to
    test runs.
-   Develop a simple review interface showing grouped diffs and agent
    attribution.

**First 90 days:**

-   Add visual overlays to the browser preview and code editor with
    agent colour mapping.
-   Build the agent timeline view and conversation summariser.
    Incorporate interactive message editing and replay.
-   Implement risk scoring based on file type, dependency changes and
    test coverage.
-   Add AST diffing and intent grouping to the diff viewer. Provide
    basic conflict detection.
-   Launch dashboards for metrics (latency, cost, error budget) and
    simple risk heatmaps.

**First 6 months:**

-   Expand the ledger to store state JSON snapshots and prompts. Provide
    state diffing and memory inspection.
-   Integrate accessibility, performance and security diffs. Add
    evidence cards and review checklists.
-   Implement rollback and branching UI with deterministic replay and
    checkpoint management.
-   Enhance conflict resolution with assumption tracking and automatic
    merge suggestions.
-   Add plugin API for custom diff types and domain‑specific tests.

**First 12 months:**

-   Add graph database backend for causal dependencies and task graphs.
    Provide interactive graph visualisation.
-   Implement machine‑learning models for risk prediction and
    summarisation. Evaluate performance using metrics described in
    Section 17.
-   Integrate cryptographic signatures into the provenance ledger.
    Explore embedding symbolic chronicles into code.
-   Develop advanced user‑journey visualisations and flakiness analysis.
    Provide comprehensive compliance and privacy dashboards.
-   Iterate on the UI with user feedback; support large teams and
    enterprise‑grade deployments.

## Conclusion

Debugging multi‑agent AI coding systems is fundamentally harder than
debugging traditional code due to non‑deterministic behaviour,
concurrent state access, invisible reasoning and emergent interactions.
Current tools provide only partial visibility. By combining structured
logging, provenance ledgers, state snapshots, semantic diffs, visual
overlays, play‑back capabilities, comprehensive testing artefacts and
observability tracing, developers can gain the insight needed to trust,
govern and improve AI‑generated code. The proposed feature catalogue and
product design provide a roadmap for building robust, debuggable
multi‑agent coding platforms that empower developers rather than obscure
their work.

------------------------------------------------------------------------

[\[1\]](https://www.augmentcode.com/guides/debug-parallel-ai-agents#:~:text=Why%20Parallel%20Agents%20Break%20Every,Standard%20Debugging%20Tool)
[\[2\]](https://www.augmentcode.com/guides/debug-parallel-ai-agents#:~:text=Why%20Parallel%20Agents%20Break%20Every,Standard%20Debugging%20Tool)
[\[3\]](https://www.augmentcode.com/guides/debug-parallel-ai-agents#:~:text=Each%20failure%20mode%20exists%20to,failures%20on%20every%20parallel%20run)
[\[4\]](https://www.augmentcode.com/guides/debug-parallel-ai-agents#:~:text=%22multi,lies%20in%20the%20interaction%20structure)
[\[5\]](https://www.augmentcode.com/guides/debug-parallel-ai-agents#:~:text=Cascading%20hallucinations%20compound%20across%20agent,recognizable%20relationship%20to%20its%20origin)
[\[6\]](https://www.augmentcode.com/guides/debug-parallel-ai-agents#:~:text=Feedback%20loops%20emerge%20when%20one,proxy%20for%20semantic%20loop%20detection)
[\[8\]](https://www.augmentcode.com/guides/debug-parallel-ai-agents#:~:text=Parallel%20agent%20debugging%20becomes%20tractable,shared%20state%20reads%20and%20writes)
[\[9\]](https://www.augmentcode.com/guides/debug-parallel-ai-agents#:~:text=Silent%20state%20overwrites%20occur%20when,Missing%20data)
[\[10\]](https://www.augmentcode.com/guides/debug-parallel-ai-agents#:~:text=Pattern%202%3A%20Isolated%20Git%20Worktrees,for%20Parallel%20Agents)
[\[16\]](https://www.augmentcode.com/guides/debug-parallel-ai-agents#:~:text=Pattern%206%3A%20Deterministic%20Replay)
[\[17\]](https://www.augmentcode.com/guides/debug-parallel-ai-agents#:~:text=The%20Observability%20Gap%3A%20No%20Mainstream,Agent%20Visualization)
[\[25\]](https://www.augmentcode.com/guides/debug-parallel-ai-agents#:~:text=system%20state%20beyond%20their%20intended,access%20to%20the%20control%20plane)
[\[30\]](https://www.augmentcode.com/guides/debug-parallel-ai-agents#:~:text=Pattern%204%3A%20Causal%20Tracing%20with,Distributed%20Trace%20Context)
How to Debug Parallel AI Agents Without Going Insane \| Augment Code

<https://www.augmentcode.com/guides/debug-parallel-ai-agents>

[\[7\]](https://arxiv.org/pdf/2503.02068#:~:text=Abstract%20Fully%20autonomous%20teams%20of,3%20Mar%202025)
[\[18\]](https://arxiv.org/pdf/2503.02068)
[\[35\]](https://arxiv.org/pdf/2503.02068#:~:text=Although%20AGDebugger%20allows%20users%20to,over%20a%20longer%20debugging%20period)
2503.02068

<https://arxiv.org/pdf/2503.02068>

[\[11\]](https://arxiv.org/pdf/2504.12612v2#:~:text=ative%20chain%2C%20content%20undergoes%20successive,content%20in%20the%20very%20act)
[\[12\]](https://arxiv.org/pdf/2504.12612v2#:~:text=agent%20systems%20may%20undergo%20complete,discernible%20trace%20of%20prior%20contributions)
Chronology of Multi-Agent Interactions for Provenance of Evolving
Information

<https://arxiv.org/pdf/2504.12612v2>

[\[13\]](https://www.bigbinary.com/blog/how-to-analyze-playwright-traces#:~:text=What%20are%20Playwright%20traces%3F)
[\[14\]](https://www.bigbinary.com/blog/how-to-analyze-playwright-traces#:~:text=%23%20Snapshots%3A%20Time)
[\[19\]](https://www.bigbinary.com/blog/how-to-analyze-playwright-traces#:~:text=1)
[\[20\]](https://www.bigbinary.com/blog/how-to-analyze-playwright-traces#:~:text=3)
[\[21\]](https://www.bigbinary.com/blog/how-to-analyze-playwright-traces#:~:text=%23%20Snapshots%3A%20Time)
How to analyze Playwright traces \| BigBinary Blog

<https://www.bigbinary.com/blog/how-to-analyze-playwright-traces>

[\[15\]](https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/#:~:text=Attributes%3A)
[\[27\]](https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/#:~:text=Attributes%3A)
[\[28\]](https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/)
[\[29\]](https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/#:~:text=value%20is%20measured%20from%20when,87)
Gen AI \| OpenTelemetry

<https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/>

[\[22\]](https://baz.co/resources/why-your-code-gen-ai-doesnt-understand-diffs#:~:text=Git%20diffs%20are%20usually%20what,track%20dependencies%20and%20reconstruct%20intent)
[\[23\]](https://baz.co/resources/why-your-code-gen-ai-doesnt-understand-diffs#:~:text=Where%20Git%20diffing%20focuses%20on,and%20structure%20between%20those%20elements)
[\[24\]](https://baz.co/resources/why-your-code-gen-ai-doesnt-understand-diffs#:~:text=Key%20Benefits%20of%20AST%20Diffing)
[\[34\]](https://baz.co/resources/why-your-code-gen-ai-doesnt-understand-diffs#:~:text=Where%20Git%20diffing%20focuses%20on,and%20structure%20between%20those%20elements)
Why Your Code Gen AI Doesn't Understand Diffs

<https://baz.co/resources/why-your-code-gen-ai-doesnt-understand-diffs>

[\[26\]](https://langfuse.com/blog/2024-07-ai-agent-observability-with-langfuse#:~:text=Industry%20Trends%20in%20Agent%20Observability)
[\[31\]](https://langfuse.com/blog/2024-07-ai-agent-observability-with-langfuse#:~:text=LLMs%20are%20stochastic%20by%20nature%2C,advantage%20of%20using%20agentic%20workflows)
[\[33\]](https://langfuse.com/blog/2024-07-ai-agent-observability-with-langfuse#:~:text=What%20is%20AI%20Agent%20Observability%3F)
AI Agent Observability, Tracing & Evaluation with Langfuse - Langfuse

<https://langfuse.com/blog/2024-07-ai-agent-observability-with-langfuse>

[\[32\]](https://www.langchain.com/blog/debugging-deep-agents-with-langsmith#:~:text=How%20Deep%20Agents%20are%20different,than%20simpler%20LLM%20applications)
Debugging Deep Agents with LangSmith

<https://www.langchain.com/blog/debugging-deep-agents-with-langsmith>
