# Modular Decomposition Framework
> Universal decision system for autonomous agents — when to split, watch, or keep unified

---

## 1. Diagnose — Current System Shape

### Questions to answer before any split decision

| # | Question | What to capture |
|---|----------|-----------------|
| 1 | What are the main responsibilities and behaviours? | List every distinct thing this module does. If the list has more than 3 items, note which are primary vs incidental. |
| 2 | Who owns what state? | Identify every piece of mutable data. Find its owner. Flag any state shared across boundaries without an explicit owner. |
| 3 | What are the external integrations and internal dependencies? | List external systems, internal imports, and shared utilities. Measure depth: can A change without touching B? |
| 4 | Where are the test boundaries today? | Which tests are fast (unit), which are slow (integration), and which parts cannot be tested without running everything? |
| 5 | What are the failure modes? | When this area breaks, what else breaks? Can failures be localised or do they cascade? |
| 6 | What is the feedback time today? | Measure: time from code change to test result, from commit to deploy. Note which tests are the bottleneck. |

---

### Modularity pressure signals

Check every signal that applies to the area under review.

- [ ] **Multiple reasons to change.** This area changes when product features change AND when infrastructure changes AND when performance changes.
- [ ] **Ownership is unclear.** Two or more people disagree on who should change this file.
- [ ] **Repeated concept.** This pattern appears in 3 or more places with no stable abstraction.
- [ ] **Test coupling.** A feature cannot be tested without running large unrelated parts of the system.
- [ ] **Unrelated breakage.** Changes in this area repeatedly break things that have nothing to do with it.
- [ ] **Different change rhythms.** Two parts of this module change at different speeds for different reasons.
- [ ] **Overloaded files.** Files exceed 300 lines or agents cannot hold the full context in mind.
- [ ] **Development waits.** One area slows down other areas because of shared resources, locks, or long integration tests.
- [ ] **Shared mutable state misuse.** Global or shared state is mutated without clear ownership.
- [ ] **Different runtime needs.** Part of the system needs different security, scaling, or deployment cadence.

---

### Split candidate criteria

All of these should be true before extraction.

- [ ] Single clear responsibility — describable in one sentence
- [ ] Stable input and output contract — the interface won't change next sprint
- [ ] Own data or state boundary — does not share mutable state without explicit ownership
- [ ] Own testable behaviour — tests can run locally without the rest of the system
- [ ] Low need for shared mutable state
- [ ] High internal cohesion — everything inside belongs together
- [ ] Manageable external dependencies — not wired to everything
- [ ] Reason to evolve independently from the rest
- [ ] Measurable reduction in feedback time, debug time, or cognitive load after splitting

---

## 2. Decide — When to Split and When Not to

### Split when these triggers appear

1. **Multiple reasons to change.** A component changes for more than one distinct reason (domain logic AND infrastructure AND performance).
2. **Beyond agent comprehension.** A single agent cannot reliably understand and modify the component without missing context.
3. **Untestable in isolation.** A feature cannot be validated without running large unrelated parts of the system.
4. **Development wait caused here.** Long integration tests, slow builds, shared resources, or unclear ownership block other work.
5. **Unrelated breakage.** Changes in one area repeatedly break unrelated areas. Defects cannot be localised.
6. **Different change speeds.** Two parts change at different rates for different reasons.
7. **Different runtime or security model.** Different testing strategy, runtime environment, security model, scaling model, or deployment cadence needed.
8. **Coordination cost exceeds interface cost.** The cost of keeping things together is higher than the cost of defining and maintaining an explicit interface.
9. **Pattern repeated 3+ times with stable abstraction.** A repeated pattern has appeared at least three times and has a clear, stable abstraction available.
10. **Contract is expressible simply.** The module boundary can be described as a simple, stable contract.
11. **Total feedback time reduces.** The split will reduce total system feedback time — not only improve aesthetic architecture.

---

### Do not split when these are true

1. **Domain is still unclear.** If you can't define what belongs inside and what belongs outside, the boundary is not ready.
2. **Interface would be speculative.** If the contract would be guessed rather than observed from actual usage, wait.
3. **Heavy shared mutable state.** If the module depends heavily on shared mutable state it cannot own, splitting hides the coupling without removing it.
4. **Would create many tiny modules.** If the result is many small modules with high coordination overhead, the system becomes harder, not easier.
5. **Would hide coupling.** If the split moves coupling behind an interface without removing it, complexity increases invisibly.
6. **Tests would become more complex.** If the new module requires more mocking, more setup, or more integration work to test, the split is wrong.
7. **Reason is file size or aesthetics.** Never split for line count, folder cleanliness, or architectural fashion. Only for operational benefit.
8. **No independent lifecycle.** If the module cannot change, deploy, or fail independently, it is not a real cell.
9. **No repeated pressure yet.** If the system has not shown repeated, observable pressure at this boundary, wait for more evidence.

---

### Decision outcomes

| Decision | Meaning | Signal |
|----------|---------|--------|
| **Keep unified** | No split. Stay as one module. | No repeated pressure. Domain unclear. Tests fast already. |
| **Watch zone** | Mark the boundary. Monitor friction signals. | One or two signals present. Pattern not yet repeated 3×. |
| **Extract internal module** | Separate directory/file group. No service boundary. | Clear responsibility. Local tests possible. Still shares deploy. |
| **Extract package / library** | Versioned API boundary. Can be published and shared. | Stable interface. Consumed by 2+ modules. Wants independent versioning. |
| **Extract service** | Runtime and deploy boundary. Separate process. | Different scaling, security, or runtime model required. |
| **Extract agent role** | Dedicated agent, CI/CD pipeline, and lifecycle. | Different development rhythm. Own monitoring. Own team or agent. |
| **Merge / repair** | Simplify or dissolve a failed boundary. | Interface keeps changing. Module too small. Coupling re-grew. |

---

## 3. Design — Initial Rules and Agent Protocol

### Initial design rules

Apply these from the start of every module.

1. **Separate capabilities by responsibility, not by technical layer alone.** Group what changes together, not what looks similar structurally.
2. **Keep data ownership explicit.** Every piece of mutable state has one declared owner. No implicit shared state.
3. **Keep side effects isolated.** Network calls, file writes, and external mutations happen at the edges, not inside domain logic.
4. **Keep interfaces small and stable.** Less surface area = less coupling. If an interface needs many methods, the boundary is wrong.
5. **Keep orchestration separate from execution.** The thing that coordinates work should not do the work. Coordinators are easy to replace; workers are not.
6. **Keep domain logic separate from transport, storage, UI, prompts, and external APIs.** Domain logic must be testable without running infrastructure.
7. **Make every major capability testable through a local contract.** If you cannot test it locally, it cannot be a healthy cell.
8. **Design each feature with a future cell boundary in mind.** Even if it stays unified, name the boundary clearly in comments and structure the code to respect it.
9. **Track coupling, build time, test time, change frequency from the start.** You cannot make data-driven split decisions without historical measurements.
10. **Avoid shared global state unless explicitly owned and controlled.**
11. **Prefer clear contracts over implicit knowledge.**
12. **Prefer simple modules that can be split later over premature distributed architecture.**

---

### Agent decision protocol

Run before implementing any feature.

**Step 0 — occurrence count.** Is this the first, second, or third+ time this pattern appears?

| Occurrence | Default action |
|-----------|----------------|
| 1st | Add to existing module. Note any signals. |
| 2nd | Mark as watch zone. Document signals. |
| 3rd+ | Score the module. Evaluate for extraction. |

**Step 1 — answer each question:**

- [ ] Does this change belong to an existing responsibility? *(If no: a new responsibility is being created — mark the boundary now.)*
- [ ] Does it increase coupling to other modules? *(If yes: new coupling without justification is a warning sign.)*
- [ ] Does it introduce a new data owner? *(If yes: make ownership explicit immediately.)*
- [ ] Does it require a different test strategy? *(If yes: different test strategy = different operational concern — add to watch zone.)*
- [ ] Does it make feedback slower? *(If yes: strong signal to isolate this concern.)*
- [ ] Does it make the current module harder to reason about? *(If yes: cognitive load accumulates — measure it.)*
- [ ] Would a local module contract make this change safer?
- [ ] Can the feature be tested independently after this change?

**Step 2 — interpret the result:**

- 0 concerns on 1st occurrence → proceed, no action needed.
- 1–2 concerns on 1st occurrence → proceed, add a `WATCH-ZONE` comment at the boundary.
- 3+ concerns on 1st occurrence → proceed, but create a named boundary immediately and score the module.
- Any concerns on 2nd occurrence → mark as watch zone, define a draft contract.
- 3rd occurrence with 3+ concerns → strong split signal; proceed to Score section, then Execute.

**The agent must not split immediately on first occurrence** unless there is strong evidence of independent lifecycle, security isolation, runtime isolation, or testing isolation.

---

## 4. Score — 12-Factor Scoring Model

Rate each factor from 0 to 5. Total out of 60.

| Factor | 0 | 5 |
|--------|---|---|
| Internal cohesion | Mixed, unclear responsibility | Single clear responsibility; everything belongs together |
| External decoupling | Wired into everything | Already well decoupled from surrounding modules |
| Change frequency | Rarely changes independently | Changes very frequently and independently from neighbours |
| Independent testability | Impossible without full system | Fully testable in isolation |
| Feedback-time gain | No improvement expected | Splitting would dramatically cut test and build wait time |
| Interface stability | Interface changes weekly | Stable, obvious interface already exists or is easily defined |
| State ownership | Shared mutable state everywhere | Clearly owns its state; no shared mutable state required |
| Failure isolation | Failures cascade everywhere | Failures would be well contained and easily localised after split |
| Cognitive relief | No improvement expected | Splitting would dramatically reduce cost to understand and change |
| Runtime independence | Cannot run independently | Can run, scale, and deploy completely independently |
| Boundary clarity | Vague, speculative boundary | Boundary is crystal clear; low risk of premature abstraction |
| Migration ease | Extremely risky to extract | Easy to extract safely with minimal refactoring risk |

### Score thresholds

| Score | Decision |
|-------|----------|
| 0–9 | **Keep unified.** No sufficient evidence. Monitor for signals. |
| 10–19 | **Watch zone.** Document signals present. Review after next 3 changes. |
| 20–29 | **Extract internal module.** Reorganise into dedicated directory. Define explicit API. Add unit tests. |
| 30–39 | **Extract package / library.** Define stable API contract. Create separate package. Add contract tests. |
| 40–49 | **Extract service.** Define service contract. Deploy independently. Add monitoring and circuit breakers. |
| 50–60 | **Extract agent role / plugin.** Define plugin contract or agent role spec. Establish independent CI/CD. |

> A score of 50+ on even one dimension does not justify extraction. The score must be consistently distributed across multiple factors. A single-factor spike is a warning sign, not a mandate.

---

## 5. Lifecycle — Cell Stages

Every module is a living cell. Its health is determined by cohesion, ownership, testability, and coupling.

**Healthy path:** Seed → Watch Zone → Budding Cell → Independent Cell → Specialised Cell

**Disease path:** Any healthy cell → Diseased Cell → Merge or Repair → Seed or Independent Cell

---

### Stage 1 — Seed

**State:** Behaviour appears once. Lives entirely inside the parent module.

**Characteristics:**
- No independent tests yet
- No named boundary
- First occurrence of a new pattern
- Part of a larger concern

**Transition:** → Watch Zone, if the pattern repeats or causes friction

**Signs you are here:** A new function, class, or file that handles one new concern.

---

### Stage 2 — Watch Zone

**State:** Behaviour appears again or causes friction. Boundary not yet stable enough to extract.

**Characteristics:**
- Marked with a TODO or WATCH-ZONE comment
- Pattern appearing 2nd or 3rd time
- Tests starting to feel slow because of this area
- Ownership becoming unclear

**Transition:** → Budding Cell, when boundary is clear and cohesion confirmed

**Signs you are here:** Repeated pressure, test slowdowns, or ownership confusion.

---

### Stage 3 — Budding Cell

**State:** Clear responsibility identified. Local tests exist. Draft contract written. Ready for careful extraction.

**Characteristics:**
- Single clear responsibility defined
- Local unit tests exist or planned
- Draft public contract written
- Limited shared mutable state
- Strong extraction candidate

**Transition:** → Independent Cell, after safe extraction and contract stabilisation

**Signs you are here:** You can describe what it does in one sentence. Tests run fast locally.

---

### Stage 4 — Independent Cell

**State:** Stable ownership, tests, interface, documentation, and limited coupling.

**Characteristics:**
- Explicit public API
- Local fast tests passing
- Contract tests with neighbours
- Clear owner (person or agent)
- Internal changes do not break neighbours

**Transition:** → Specialised Cell, if different runtime, security, or deployment needs emerge

**Signs you are here:** Changes here don't require coordination with unrelated modules.

---

### Stage 5 — Specialised Cell

**State:** Own development rhythm, agent role, performance profile, security model, or deployment path.

**Characteristics:**
- Independent CI/CD pipeline
- Own monitoring and alerting
- Can scale independently of others
- Different security or runtime model
- Dedicated agent or team owner

**Transition:** → Diseased Cell if coupling grows back; remains healthy if guarded

**Signs you are here:** It deploys on its own schedule. Its tests never block other modules.

---

### Stage 6 — Diseased Cell

**State:** Excessive coupling, unclear ownership, duplicated logic, slow tests, or frequent breakages.

**Characteristics:**
- Interface keeps changing
- Changes here require parent module changes
- Tests are slow or fragile
- Multiple agents disagree on ownership
- Logic is duplicated elsewhere

**Transition:** → Merge / Repair (to fix boundary or dissolve it)

**Signs you are here:** Every PR touches this file. Bugs here appear as bugs everywhere.

---

### Stage 7 — Merge / Repair

**State:** The cell is simplified, merged back into the parent, or given a cleaner boundary and restarted.

**Characteristics:**
- Boundary redefined or removed
- Coupling made explicit and reduced
- Logic consolidated or removed
- Tests restructured for speed
- Ownership reassigned and documented

**Transition:** → Seed (if merged back) or → Independent Cell (if boundary repaired)

**Signs you are here:** The reason for the boundary could not be maintained. Simpler is better.

---

## 6. Execute — Safe Refactoring Plan

### Steps — execute in order, never skip

1. **Preserve behaviour first.** Do not change behaviour and structure at the same time. Refactoring and feature changes are separate commits.
2. **Add characterisation tests before moving code.** These tests capture current behaviour, not desired behaviour. They protect you during the move.
3. **Define the public contract before extraction.** Write the interface first. Make it minimal. No internal types in the public API.
4. **Move one responsibility at a time.** Do not extract multiple concerns in one commit. Each move should be independently reviewable and reversible.
5. **Keep old and new paths temporarily if needed.** Feature flags or adapter layers let you validate the new path before removing the old one.
6. **Use adapters to reduce migration risk.** An adapter wraps the old interface and delegates to the new one. Remove the adapter after full migration.
7. **Eliminate shared mutable state or make ownership explicit.** Shared state that survives extraction will re-create the coupling you just tried to remove.
8. **Add local fast tests for the new module.** These tests should run in under 2 seconds without external dependencies.
9. **Add contract tests between modules.** Contract tests verify that the interface behaves as both sides expect, without running the full system.
10. **Add integration tests only for critical cross-module behaviour.** Keep these few. They are expensive. They should test collaboration, not implementation.
11. **Measure feedback time before and after.** If feedback time did not improve, the split did not achieve its goal. Consider reverting.
12. **Remove dead code, update documentation, and set rollback criteria.** Define rollback conditions: if X conditions are met within Y days, merge back.

---

### Independence readiness checklist

A module can be developed independently only when all of these are true.

- [ ] Contract is explicit — inputs and outputs are defined and documented
- [ ] Inputs and outputs are stable enough — won't change next sprint
- [ ] Tests run locally without the whole system
- [ ] Dependencies are injected or mocked cleanly
- [ ] Module owns or clearly accesses its data
- [ ] Failure modes are known and documented
- [ ] Responsibility is clear — describable in one sentence
- [ ] Can change internally without requiring unrelated modules to change
- [ ] Has an owner agent or role
- [ ] Has acceptance criteria independent of the full system
- [ ] Integration with the rest of the system is verified through contract tests

---

### Feedback-time strategy

| Layer | What it tests | Rule |
|-------|--------------|------|
| Unit | Internal cell behaviour | Many. Fast. Run on every change. |
| Contract | Cell boundary expectations | One per boundary. Run on change to either side. |
| Integration | Essential collaboration only | Few. Run on merge, not every commit. |
| End-to-end | Core user journeys | Very few. Run on release. Never block a small fix. |

The system should know which tests to run based on which cell changed. Every new cell should reduce unnecessary waiting — not add more of it.

---

## 7. Report — Success, Failure, and Monitoring

### Success criteria

A split has succeeded only when all of these are true.

- [ ] The new module has a clearer responsibility than before
- [ ] Tests for that responsibility are faster or easier to run
- [ ] Fewer unrelated files change together
- [ ] The interface is smaller than the previous implicit dependency surface
- [ ] The system is easier to reason about overall
- [ ] Waiting time is reduced for developers and agents
- [ ] Defects are easier to localise to a specific module
- [ ] The module can evolve without unnecessary coordination
- [ ] Total complexity of the system did not increase without benefit

---

### Failure criteria

A split has failed if any of these are true — consider merging back.

- [ ] **Constant parent coupling.** The new module constantly needs changes in the parent module.
- [ ] **Unstable interface.** The contract between modules keeps changing.
- [ ] **Slower or more fragile tests.** Testing is now harder than before.
- [ ] **Unclear data ownership.** Nobody agrees on who owns what state.
- [ ] **Agent confusion.** Agents disagree on where changes belong.
- [ ] **Too small to justify.** The boundary adds overhead with no visible benefit.
- [ ] **Duplicated logic.** The same logic now exists in two places.
- [ ] **More integration work.** The same feature now requires more cross-module coordination.
- [ ] **Only moved code.** The split reorganised files but did not reduce coupling.

---

### Monitoring signals

| Signal | Healthy | Warning | Diseased |
|--------|---------|---------|---------|
| Files changed per PR | Mostly in one module | Occasional cross-boundary | Always cross-boundary |
| Test run time | Faster than before split | Similar to before | Slower than before |
| Interface change frequency | Stable for >4 weeks | Changes monthly | Changes weekly |
| Bug localisation | Clear module blame | Occasional ambiguity | Cannot tell which module |
| Agent comprehension | One agent owns it confidently | Requires checking context | No single agent understands it |
| Integration test failures | Rare and explainable | Occasional flakes | Frequent, unclear cause |

---

### Final recommendation template

```
Decision:
  [ Keep unified | Watch zone | Extract internal | Extract package |
    Extract service | Extract agent role | Merge back ]

Evidence:
  - [ Signal 1 observed ]
  - [ Signal 2 observed ]
  - [ Pattern appeared N times ]

Module boundary:
  Responsibility : [ One sentence ]
  Inputs         : [ List ]
  Outputs        : [ List ]
  State owned    : [ List ]
  State NOT owned: [ List ]

First refactoring step:
  [ One concrete, reversible action ]

Tests before refactor:
  - [ Characterisation test 1 ]
  - [ Characterisation test 2 ]

Tests after refactor:
  - [ Unit test for new module ]
  - [ Contract test at boundary ]
  - [ Integration test for critical path ]

Metrics to compare:
  Feedback time before: __s  →  after: __s
  Files per PR before : __   →  after: __
  Test run time before: __s  →  after: __s

Agent instruction update:
  Changes to [module name] belong to [owner].
  Do not modify [internals] from outside this boundary.
  Use only [public interface] to interact with this module.
  If unsure, ask: does this change fit the responsibility: [sentence]?

Rollback criteria:
  If [interface changes more than N times] or [test time increases >X%]
  within [Y days], merge back and re-evaluate from watch zone.
```

---

## Operating Rules

These rules apply to every decision in this framework.

- Do not split for elegance alone.
- Do not create speculative abstractions.
- Do not hide coupling behind interfaces.
- Do not create modules that cannot be tested independently.
- Do not create modules without clear ownership.
- Do not make the system slower to validate.
- Prefer small reversible refactors over large irreversible rewrites.
- Prefer evidence over architectural opinion.
- Prefer working software over perfect structure.
- Prefer living-cell modularity: clear boundary, internal autonomy, controlled communication, independent health, and useful specialisation.

> A split is a means to reduce friction, not an architectural achievement. If the friction is not measurably reduced, the split has not succeeded.
