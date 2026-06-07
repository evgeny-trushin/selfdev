# Living Cell Modularity Assessment of noVNC

## Scope and evidence

I could only analyze the actual repository that was accessible in the workspace during this session: `/opt/novnc`, at commit `7fcf9dc`, which is tagged `noVNC 1.5.0` in the local Git history. I inspected the source tree, docs, tests, build scripts, packaging files, and commit history directly.

That means this report is evidence-based for **noVNC** specifically, not for some other repository that might have been intended. I did **not** have access to production runtime logs, issue tracker discussions, or user-provided project documents beyond what was present in the repo. I also did not succeed in establishing a fully installed dependency environment, so I could not produce trustworthy measured timings for `npm test`, browser-matrix runtime, or flake rate. Those remain unknown and should be collected before judging whether a split actually improves feedback time.

The architectural stance in this report is deliberately conservative. The literature is consistent on the core rule: modernize and separate incrementally, introduce seams where pressure is real, and avoid speculative distributed boundaries. Fowler’s “Strangler Fig” guidance emphasizes introducing seams and moving behavior gradually instead of betting on a big-bang replacement, while Microsoft and AWS both describe incremental modernization and reversible branch-by-abstraction as lower-risk approaches. The “sliceable monolith” research makes the same monolith-first point from another angle: keep the simplicity of a single codebase until separation yields measurable benefit. citeturn28view0turn26view2turn26view3turn24view0

## Current system map

### Natural shape of the organism

Direct repository inspection shows that noVNC is already a **modular monolith**, not an undifferentiated blob. Its natural shape is:

```text
Browser user
  -> vnc.html / vnc_lite.html
      -> app/ui.js
          -> app/webutil.js       (settings/config persistence)
          -> app/localization.js  (translations)
          -> core/rfb.js          (session orchestrator)
              -> core/websock.js          (wire transport)
              -> core/display.js          (canvas rendering)
              -> core/input/*             (keyboard/gesture/key mapping)
              -> core/decoders/*          (encoding-specific decode cells)
              -> core/inflator.js
              -> core/deflator.js
              -> core/crypto/* + core/ra2.js
              -> browser APIs             (ResizeObserver, Fullscreen, crypto, audio)
          -> DOM in vnc.html
          -> CSS in app/styles/*
Build/publish
  -> utils/convert.js -> lib/
Deploy/proxy
  -> utils/novnc_proxy
  -> snap/snapcraft.yaml
```

The **external public library boundary** is intentionally narrow. The formal API docs describe a single `RFB` object as the client API, and the code backs that up by exporting one `RFB` class that orchestrates transport, rendering, input, security, and decoders. In the accessible source, `RFB` imports display, compression, input, transport, security, and eight decoder modules; that is a clear sign that it is the central session coordinator rather than a leaf utility. citeturn15view0turn16view2turn16view3turn17view0

The **application boundary** is also clear. `UI.start()` initializes settings, translation, fullscreen support, version fetching, multiple handler groups, keyboard bootstrap, visual state, and autoconnect behavior, which means `app/ui.js` is the top-level app-shell orchestrator for the browser application. Later sections of the same file also handle settings panels, power and clipboard panels, connection lifecycle, reconnect flow, verification dialogs, virtual keyboard behavior, extra keys, compression/quality/view state, and status messages. citeturn15view1turn16view0turn17view1

### Responsibility map

From direct inspection, the current responsibilities are best described by **capability**, not by technical layer alone:

| Cell or region | Current responsibility | Health status |
|---|---|---|
| `app/ui.js` | Browser app shell, DOM event wiring, connection flow, settings sync, dialogs, keyboard helpers, status updates | Stressed |
| `app/webutil.js` | Query/hash config, settings persistence, logging setup | Healthy |
| `app/localization.js` | Language selection and DOM translation | Healthy |
| `core/rfb.js` | RFB session lifecycle, state machine, protocol negotiation, event bridge, resize/input/cursor coordination | Stressed but functional |
| `core/display.js` | Canvas rendering and viewport handling | Healthy |
| `core/websock.js` | WebSocket queueing and framed I/O helpers | Healthy |
| `core/decoders/*` | Encoding-specific framebuffer decode logic | Healthy |
| `core/input/*` | Keyboard, gesture, keysym, and browser input translation | Healthy |
| `core/crypto/*`, `core/ra2.js` | Low-level crypto primitives and RSA-AES auth state | Mostly healthy |
| `utils/convert.js` | Build-time transpilation from source modules to `lib/` | Healthy |
| `utils/novnc_proxy` | Local web server + WebSocket proxy bootstrap around websockify | Healthy |
| `tests/test.rfb.js` | Broad verification envelope around the giant `RFB` orchestration surface | Diseased test boundary |

### Dependency map and data ownership map

The dependency shape is asymmetric and healthy in several places. `app/` depends on `core/`. `tests/` mostly depend on `core/`, with only a small amount of direct `app/` testing. That fits the product’s real architecture: the protocol/session core is the engine; the app shell is a thin but currently overgrown presenter layer.

State ownership is split across four main owners:

The first state owner is **`WebUtil`**, which owns configuration state and persistence via `localStorage` or `chrome.storage`. The second is **`UI`**, which owns browser-app transient state such as `connected`, `desktopName`, reconnect timers, control-bar drag state, and virtual keyboard helper state. The third is **`RFB`**, which owns protocol/session state such as connection state, init state, credentials, server capabilities, framebuffer dimensions, cursor state, decoder state, and socket/display/input object lifecycles. The fourth is the **remote VNC server**, which remains the real owner of the desktop contents, protocol capabilities, authentication requirements, desktop name, and clipboard updates.

This ownership split is important: the repo does **not** have a global mutable singleton across the whole system. It has a few distinct owners. That is a good sign. The problem is narrower: `app/ui.js` owns too many **different kinds** of transient state at the same time.

### Test boundary map, deployment boundary map, and failure modes

Direct inspection found **22 automated `tests/test.*.js` files** with about **590 `it(...)` test cases** total. That is not a weak test suite overall. The weakness is **where the boundary is drawn**. `core/rfb.js` has a massive companion test file:

- `tests/test.rfb.js`: **5217 LOC**
- about **84 `describe(...)` blocks**
- about **277 `it(...)` cases**

That one file covers constructor behavior, connect/disconnect, clipping, scaling, resize, protocol initialization, many auth schemes, framebuffer handling, cursor handling, clipboard flows, input events, gestures, WebSocket events, and message encoders. This is evidence that `RFB`’s verification boundary is too broad for comfortable independent change.

By contrast, the application shell has almost no direct automated boundary. There are tests for `app/localization.js` and `app/webutil.js`, but there is **no dedicated automated test file for `app/ui.js`**. There is also a manual playback harness (`tests/playback.js`, `tests/playback-ui.js`), but Karma is configured to load only `tests/test.*.js`, so that harness is not part of the default automated suite.

The deployment shape is simple and healthy. The repo supports:

- static application deployment via `vnc.html`, `app/`, `core/`, and `vendor/`
- library publishing through `utils/convert.js` into `lib/`
- optional local proxy/development runtime via `utils/novnc_proxy`
- snap packaging that bundles the key runtime pieces

The main operational failure modes visible in the code are also coherent. The UI warns on insecure contexts and degrades gracefully if it cannot fetch `package.json` for version display. `RFB` has explicit failure handling that transitions to disconnecting/disconnected on protocol failure, bad states, or decode errors. The proxy script fails fast if ports or required files are missing. The embedding docs also call out an HTTP cache-control hazard during upgrades. citeturn15view1turn16view2turn20view0

## Existing cells and pressure points

### Where the system is already trying to become modular

The codebase is already telling you where the organism wants to separate:

The **decoder family** is the clearest existing cell colony. Each encoding has its own module under `core/decoders/`, with matching focused tests. This is a healthy cell pattern: clear responsibility, stable contract, and local verification.

The **utility/support cells** are also healthy. `app/webutil.js` has a clear settings/persistence boundary. `app/localization.js` has a distinct translation boundary. `core/display.js` is a rendering cell. `core/websock.js` is a transport cell. `core/input/*` is a distinct input-transformation area.

The **tooling boundary** is also healthy. `utils/convert.js`, `utils/novnc_proxy`, and `snap/snapcraft.yaml` are operationally separate enough already. They do not need more architectural surgery.

This means the repo already behaves like a **sliceable monolith** in the research sense: one codebase, one local execution model, but with meaningful internal seams. That is a strength worth preserving. citeturn24view0turn24view1

### Watch zones and stressed cells

The first diseased cell is **`app/ui.js`**.

Direct inspection found:

- **1778 LOC** in `app/ui.js`
- **76.9%** of all JavaScript LOC under `app/`
- **129** `getElementById(...)` calls touching **45** unique DOM IDs
- **66** `addEventListener(...)` registrations
- **71** references to `UI.rfb`
- no dedicated automated test file for the module

Historically, it is also the most changed current source file in the repo, with **258 historical commits** touching it. It co-changed with:

- `core/rfb.js` **56** times
- `vnc.html` **51** times
- `app/styles/base.css` **42** times

That is exactly the signature of a cell that is doing too much: visual state, DOM mechanics, session orchestration, persistent setting synchronization, and mobile input work all change through one membrane.

The second stressed cell is **`core/rfb.js`**.

Direct inspection found:

- **3249 LOC**
- about **31%** of all JavaScript LOC under `core/`
- **27 imports**
- roughly **15** `_negotiate*` methods
- roughly **25** `_handle*` methods

The accessible source shows it directly mixes connection lifecycle, protocol negotiation, multiple auth schemes, message pumping, clipboard handling, cursor handling, resize logic, input handling, framebuffer update management, and low-level message construction. That is not proof that the file must be split today, but it is strong evidence that the file is an orchestration hotspot. citeturn15view0turn16view2turn16view3turn17view0

The third stressed boundary is **feedback-time health**, not code structure alone.

Direct inspection found that:

- dev dependencies are mostly declared as `"latest"`
- CI workflows run `npm update`
- the default test command is one broad Karma run
- the GitHub Actions test workflow fans out across multiple browsers and operating systems

That means the feedback loop is likely both **broad** and **non-hermetic**. Even without measured timing, that is a meaningful risk: the repo currently lacks a precise cell-to-test routing mechanism, and build validation can drift with ecosystem dependency changes.

### Current feedback-time bottlenecks

For this repo, the main delays are not “needs more microservices.” They are:

- a giant browser-UI orchestrator without local targeted tests
- a giant `RFB` verification envelope in one file
- no default changed-cell test selection
- unpinned validation inputs in CI

Thoughtworks’ practical test-pyramid guidance argues for different test granularities, lots of small fast tests, and only a few high-level tests, precisely because that keeps refactoring safe and feedback fast. This repo’s core tests are strong, but its app-shell boundary does not yet follow that shape. citeturn25view0turn25view1

## Split decisions and scoring

### Decision model

I recommend a simple scoring model for autonomous agents.

For the first ten factors, **higher means “more evidence that a boundary is real or useful.”**  
For the last two, **higher means “more reason to wait.”**

- **Cohesion**: 0 diffuse, 5 single clear responsibility
- **Coupling**: 0 low entanglement, 5 severe entanglement burden in current shape
- **Change**: 0 rare, 5 frequent
- **Test**: 0 cannot test independently, 5 easily testable locally
- **Feedback**: 0 negligible gain, 5 large expected feedback-time reduction
- **API**: 0 speculative interface, 5 stable/simple contract
- **State**: 0 unclear ownership, 5 clear state ownership
- **Isolation**: 0 no failure-isolation gain, 5 large gain
- **Cognitive**: 0 little relief, 5 large reasoning simplification
- **Runtime**: 0 same runtime/deploy model, 5 clearly different runtime or deployment needs
- **Premature risk**: 0 low, 5 high
- **Migration difficulty**: 0 trivial, 5 very hard

A practical readiness score is:

**Readiness = Cohesion + Coupling + Change + Test + Feedback + API + State + Isolation + Cognitive + Runtime − Premature risk − Migration difficulty**

This is a decision aid, not a replacement for judgment. Metric-based evaluation is useful precisely because it reduces subjective boundary decisions, but it still needs evidence and context. citeturn24view1

Use these thresholds:

- **Keep unified**: score below 18, or interface/state are still unclear
- **Watch zone**: score 18–24, or one hard blocker remains
- **Extract internal module**: score 25+, with `API >= 3`, `State >= 3`, `Premature risk <= 3`, `Migration difficulty <= 3`
- **Extract package/library**: internal-module threshold plus real reuse beyond the repo, or an independently versioned consumer contract
- **Extract service**: package threshold plus independent data ownership, runtime/security/deploy needs, and low shared mutable state
- **Merge back**: after extraction, if parent and child still change together most of the time, the contract churns repeatedly, or tests become slower/more fragile

### Candidate scores

The table below is repo-specific and based on direct inspection. The **Feedback** column is inferred, not measured, because runtime timings were not available.

| Candidate boundary | Coh | Coup | Chg | Test | Fbk | API | State | Iso | Cog | Run | Prem | Mig | Readiness | Decision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `app/session-controller.js` from `app/ui.js` | 4 | 4 | 3 | 4 | 4 | 4 | 4 | 3 | 4 | 1 | 2 | 2 | 29 | **Extract internal module now, but only inside the monolith** |
| `app/settings-presenter.js` from `app/ui.js` | 3 | 3 | 2 | 4 | 3 | 3 | 4 | 2 | 3 | 0 | 2 | 2 | 21 | **Watch zone** |
| `app/controlbar-touch-input.js` from `app/ui.js` | 2 | 4 | 2 | 2 | 2 | 2 | 2 | 2 | 3 | 0 | 3 | 3 | 13 | **Keep unified for now** |
| `core/rfb-auth-negotiation.js` from `core/rfb.js` | 4 | 4 | 4 | 3 | 3 | 2 | 2 | 3 | 5 | 0 | 3 | 4 | 23 | **Watch zone** |
| `core/rfb-messages.js` from the `RFB.messages` block | 5 | 1 | 1 | 5 | 1 | 5 | 5 | 1 | 1 | 0 | 4 | 1 | 19 | **Keep unified** |
| Separate package or service for app/core split | 2 | 5 | 1 | 1 | 1 | 1 | 1 | 3 | 1 | 2 | 5 | 5 | 8 | **Do not split** |

### Why these decisions are correct for this repo

The only boundary that is both **real** and **useful right now** is the session-lifecycle seam inside `app/ui.js`. The file already contains a logically distinct cluster: connect, disconnect, reconnect, credential prompts, server verification, desktop naming, and RFB event wiring. Those behaviors are conceptually stable, and they can be tested with an injected fake `RFB` far more easily than the current DOM-heavy whole-file approach. The source itself shows that this single file already couples DOM actions, settings, and session orchestration, while the connect flow wires a large set of RFB events and options in one place. citeturn16view0turn17view1

The `core/rfb.js` authentication and negotiation region is **not** ready for extraction yet. It has repeated patterns, and it is clearly a watch zone, but the boundary still shares too much mutable state with the main protocol machine: socket queue state, `_rfbInitState`, credentials, async resume behavior, capability flags, and event dispatch. AWS’s branch-by-abstraction guidance is relevant here: if the code is deep inside the stack and highly entangled, reversible abstraction is safer than immediate hard separation. That describes `RFB` auth well. citeturn26view3turn16view3

A service or package split would be premature. AWS explicitly notes that a monolith can remain a valid choice when responsibilities are not yet clearly defined enough, and that decomposition should be driven by real tight-coupling, reliability, or scaling pressure. This repo is a browser library and application with one dominant runtime. It does **not** show evidence of separate runtime, security, scaling, or deployment cadences between app and core that would justify service extraction. citeturn26view0turn26view1

The strongest “no-split” area is also the healthiest: the decoders, display, input, transport, localization, and settings helpers are already behaving like healthy cells. Splitting them further would mostly serve aesthetics, not feedback time.

## Refactoring and test strategy

### Recommended first refactor

The first safe architectural move is **not** a package split and **not** a service split.

It is this:

**Create an internal `app/session-controller.js` seam inside the existing monolith, and move only the session lifecycle responsibility into it.**

That means:

- keep `vnc.html` as the app page
- keep `app/ui.js` as the DOM presenter
- keep `core/rfb.js` as the only public session core
- move connect/disconnect/reconnect/event-wiring/session state into a local internal module
- inject `RFB` as a dependency for tests
- publish controller events back to the UI instead of having the controller manipulate the DOM directly

This is the right first split because it is the first point where specialization becomes cheaper and safer than further accretion inside `app/ui.js`. It is also reversible, which matters. Fowler’s modernization guidance stresses incremental seams, and AWS’s branch-by-abstraction pattern explicitly recommends an abstraction layer that allows old and new flows to coexist until the seam is proven. citeturn28view0turn26view3

### Exact boundary to create

`app/session-controller.js` should own:

- RFB instance creation and teardown
- connect/disconnect/reconnect/cancel-reconnect flow
- session state snapshot
- mapping connection/session preferences into RFB options
- RFB event subscriptions and translation into app-level events
- reconnect timer state
- credentials submission and server approval commands

`app/ui.js` should keep owning:

- DOM querying and DOM mutation
- panels, control bar, and visual state classes
- settings form controls
- clipboard text area rendering
- power/settings/extra keys panel open/close behavior
- touch keyboard DOM behavior
- fullscreen button behavior
- audio bell playback

That is a clean cell boundary because it separates **orchestration of a remote session** from **presentation of browser UI**.

### Public contract for the new cell

A practical contract for the first extraction is:

```ts
export type SessionConfig = {
  host: string;
  port?: string | number;
  path: string;
  encrypt: boolean;
  shared: boolean;
  repeaterID?: string;
  password?: string;
  quality: number;
  compression: number;
  showDotCursor: boolean;
  resizeMode: 'off' | 'scale' | 'remote';
  viewOnly: boolean;
};

export type SessionEvent =
  | { type: 'state'; state: 'connecting' | 'connected' | 'disconnecting' | 'disconnected' | 'reconnecting' }
  | { type: 'status'; level: 'normal' | 'warning' | 'error'; message: string }
  | { type: 'desktopname'; name: string }
  | { type: 'clipboard'; text: string }
  | { type: 'capabilities'; power: boolean }
  | { type: 'credentialsrequired'; fields: Array<'username' | 'password'> }
  | { type: 'serververification'; verificationType: string; fingerprint?: string }
  | { type: 'securityfailure'; reason?: string };

export interface SessionController {
  connect(target: HTMLElement, config: SessionConfig): void;
  disconnect(): void;
  approveServer(): void;
  rejectServer(): void;
  sendCredentials(creds: { username?: string; password?: string }): void;
  applyPreferences(config: Pick<SessionConfig, 'quality' | 'compression' | 'showDotCursor' | 'resizeMode' | 'viewOnly'>): void;
  getSnapshot(): {
    connected: boolean;
    desktopName: string;
    reconnectPending: boolean;
  };
  subscribe(listener: (event: SessionEvent) => void): () => void;
  dispose(): void;
}
```

This boundary is intentionally small. It keeps the DOM out, keeps `RFB` in one place, and gives the UI a stable event stream.

### Tests that must exist before the refactor

Before moving code, add characterization tests around the behavior that currently lives in `app/ui.js`:

- connection URL construction from host/port/path/encrypt
- initial RFB option mapping for shared, repeater ID, quality, compression, show-dot cursor, resize mode, and view-only
- reconnect timer scheduling and cancellation
- connect/disconnect visual-state transitions
- credential-required flow and verification-approval flow
- desktop-name and clipboard event handling
- the error path when `RFB` construction fails

These should be **new targeted tests**, not additions to `tests/test.rfb.js`.

### Tests that must exist after the refactor

After extraction, the test pyramid for this repo should look healthier:

- **Unit tests** for `app/session-controller.js` with a fake `RFB` constructor and fake timers
- **Contract tests** between `app/ui.js` and `app/session-controller.js`, verifying that UI commands call controller methods and that controller events produce the right UI updates
- **Existing core tests** for `core/rfb.js`, `core/websock.js`, display, input, and decoders remain in place
- **One or two browser integration smoke tests** for `vnc.html` only, reserved for critical user journeys

That matches the practical test-pyramid guidance: different test granularities, many fast local tests, and far fewer high-level ones. citeturn25view0turn25view1

### Feedback-time strategy for this repo

The test strategy should be cell-aware:

- changes in `core/decoders/*` should run the matching decoder tests plus one narrow `RFB` collaboration test
- changes in `core/websock.js` should run `test.websock.js` plus only relevant `RFB` collaboration tests
- changes in `app/session-controller.js` should run `test.session-controller.js` and contract tests with the UI
- the full Karma/browser matrix should remain, but it should stop being the default answer for every small refactor

To make this real, the repo needs a changed-cell test selector. Right now the default Karma setup is broad. That broad suite remains valuable as a safety net, but it should not be the only learning loop.

### Prerequisite health fix before measuring the split

Before comparing before/after feedback time, stabilize the build inputs:

- stop relying on `latest` for all dev dependencies
- add a lockfile
- switch CI from `npm update` to a reproducible install step
- record baseline timings for full test, targeted test, and lint

Without that, you will not know whether a faster or slower result came from the refactor or from dependency drift.

## Agent protocol, cell lifecycle, and success signals

### Cell lifecycle for this repo

In noVNC, the current lifecycle map looks like this:

- **Seed**: new UI options, new pseudo-encodings, or rare auth variants that appear once
- **Watch zone**: `app/ui.js` session block, `app/ui.js` settings block, `core/rfb.js` auth/negotiation block
- **Budding cell**: `app/session-controller.js` immediately after extraction, once it has local tests and a draft contract
- **Independent cell**: `app/webutil.js`, `app/localization.js`, `core/display.js`, `core/websock.js`, `core/decoders/*`, and later the session controller if stable
- **Specialized cell**: none yet at the package/service level
- **Diseased cell**: `app/ui.js` in its current form; `tests/test.rfb.js` as an overgrown verification cell
- **Merge or repair**: if the extracted session controller still forces frequent concurrent edits in `app/ui.js`, churns its contract, or makes tests slower, merge it back or reduce its surface

### Agent decision protocol

For autonomous AI agents working in this repo, the protocol should be:

When starting a change, first classify it into one of these responsibilities: **UI presenter**, **session lifecycle**, **RFB protocol core**, **decoder**, **transport**, **input**, **settings/persistence**, **localization**, or **tooling**.

If the change is about connect/disconnect, reconnect, credentials, server approval, desktop naming, or mapping settings into RFB behavior, route it to the **session lifecycle watch zone** first. Do not add more of that logic into general panel/control-bar code.

If the change is about a specific encoding, keep it inside the existing decoder cell unless three independent encodings now share the same abstraction.

If the change introduces a new auth/security variant, mark the `core/rfb.js` auth region as touched. Do **not** immediately extract it unless there is repeated pressure.

Before splitting anything, compute the score. Split only if:

- the score says **Extract internal module**
- there is at least one hard trigger
- the interface is simple enough to state in a contract
- local tests can be created for that boundary
- shared mutable state can be reduced or made explicit

Hard triggers for this repo should be:

| Watch zone | Split trigger | Merge-back trigger |
|---|---|---|
| `app/ui.js` session lifecycle | Next feature touches session flow and requires edits to both DOM presenter code and RFB wiring, or the zone sees 3 similar changes in a row | Controller contract changes more than 3 times in 5 related changes, or parent and child still change together in most session PRs |
| `app/ui.js` settings sync | 3 setting-related changes in a row touch both form wiring and persistence behavior | Added module mostly proxies DOM calls without reducing touched files or tests |
| `core/rfb.js` auth/negotiation | Third new auth/security enhancement after extraction watch begins, or auth tests start dominating unrelated `RFB` changes | Extracted auth module still depends on broad shared mutable `RFB` internals and changes alongside core on most commits |
| `app/ui.js` controlbar/touch input | Repeated mobile/input work shows a stable independent event model and local tests become practical | Boundary remains DOM-fragile and mostly aesthetic |

### Success criteria and failure criteria for the first split

The first split succeeds only if all of these become true:

- `app/session-controller.js` has a clearer responsibility than the removed code in `app/ui.js`
- there is at least one fast local test file for session behavior
- session-related changes stop forcing unrelated edits to panel or touch-keyboard code
- `app/ui.js` becomes materially smaller and easier to scan
- the controller contract stays stable through several changes
- targeted test execution becomes possible without the full browser matrix
- defects in connect/reconnect/credentials can be localized to one module faster

The first split has failed if:

- controller and UI still change together for nearly every session feature
- the controller contract churns repeatedly
- tests become slower or more brittle
- state ownership becomes more confusing than before
- the split mostly moves code without reducing touched files or reasoning burden

### Monitoring signals

Use these signals to judge whether the organism got healthier:

| Signal | Baseline from direct inspection | Success target |
|---|---|---|
| Dedicated automated tests for session flow | none | at least one targeted local session test file |
| `app/ui.js` LOC | 1778 | below 1300 after extraction |
| `app/ui.js` share of app JS LOC | 76.9% | below 60% |
| Unique DOM IDs referenced by session code | embedded in `app/ui.js` | session module references zero DOM IDs directly |
| Session feature touched-files pattern | historically co-changes with `core/rfb.js` and `vnc.html` are common | most session changes confined to controller + its tests |
| Full-suite timing | unknown | measure before/after; targeted session suite should be a small fraction of full suite |
| Contract churn | not applicable yet | no more than one breaking revision across first three feature iterations |

## Final recommendation

The clear overall decision for this repo is:

**Keep the system unified as a deployable modular monolith. Do not extract packages, services, or extra agent roles now.**

The clear boundary-level decision is:

**Split exactly one internal cell now: extract a `session-controller` from `app/ui.js`, and do it by branch-by-abstraction inside the same repo and runtime.**

That recommendation is based on direct repository evidence:

- `app/ui.js` is the dominant app-layer file and mixes too many responsibilities
- it lacks direct automated tests
- it historically co-changes with both the session core and the app page
- its session-lifecycle boundary is stable enough to express as a contract
- moving that boundary inward should reduce cognitive load and make local testing possible

The evidence does **not** support a bigger split right now:

- the decoder, display, input, transport, localization, and settings cells are already reasonably healthy
- `core/rfb.js` is stressed, but its auth/negotiation region still shares too much protocol state for a clean extraction today
- there is no evidence of separate runtime, deployment cadence, data ownership, or security isolation that would justify a package or service boundary
- AWS guidance explicitly warns that a monolith can remain the right choice when responsibilities are not yet clearly enough defined, and recommends decomposition where real coupling and maintainability pressure justify it; Fowler and Microsoft both favor incremental seam creation over speculative architectural leaps. citeturn26view0turn26view1turn28view0turn26view2

So the practical architecture output for an autonomous development system is:

- **Overall**: keep unified
- **Immediate**: extract internal `app/session-controller.js`
- **Watch**: UI settings sync, UI touch/controlbar behavior, `core/rfb.js` auth/negotiation
- **No-split**: decoders, display, websock, localization, webutil, `RFB.messages`, package/service boundary
- **Prerequisite**: stabilize CI inputs and add targeted tests before claiming feedback-time improvement

That is the point where specialization is cheaper, safer, and faster than continued accretion—**but only for the session seam inside the app shell, not for the whole system**.