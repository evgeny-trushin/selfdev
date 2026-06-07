# System Architecture and Modularisation Analysis

## Overview of the Current System

### Repository contents

The repository under analysis contains two primary JavaScript files and
two small Python utilities:

-   `answer.js` -- a script that uses the `pptxgenjs` library to
    assemble a PowerPoint presentation. It defines constants for slide
    dimensions, font sizes, colours and margins and provides helper
    functions to calculate text box heights and image sizing. The script
    then constructs a slide deck using these helpers. At the top of the
    file, constants such as `SLIDE_HEIGHT`, `SLIDE_WIDTH`, `FONT_SIZE`
    and helper functions like `calcTextBoxHeight`, `getImageDimensions`
    and `imageSizingCrop` are defined. Towards the bottom, an
    asynchronous IIFE creates a `pptxgen` instance and builds slides.

-   `slides_template.js` -- a much larger file that provides examples of
    different slide layouts (charts, image grids, key‑point lists,
    timelines, bubble graphs, etc.) for a 16×9 presentation. It repeats
    the same constants and helper functions found in `answer.js` and
    implements a series of slide construction blocks for each layout.
    The duplication of these constants and helpers indicates that the
    system has not yet extracted shared functionality into a reusable
    module.

-   `create_montage.py` -- a small Python script that takes a set of PNG
    images and composes them into a montage image. It opens each input
    image, arranges them in a grid, optionally rescales the result and
    writes the combined image to disk. The script serves as a tooling
    aid for generating composite images but does not interact with the
    JavaScript codebase.

-   `pptx_to_img.py` -- a utility that converts a PPTX file into a set
    of PNG images using LibreOffice and `pdf2image`, checks whether
    slide content overflows the canvas and warns about problems. Again,
    it is a stand‑alone tool with no direct coupling to the Node
    scripts.

The remainder of the repository contains a large `node_modules`
directory, which is standard for a Node project, and static assets such
as `placeholder_light_gray_block.png`. There are no unit tests,
integration tests or continuous integration scripts; execution is manual
via `node answer.js` or the Python scripts.

### Natural responsibilities and behaviours

The system's primary purpose is to generate visually pleasing slide
decks using JavaScript. The natural responsibilities can be grouped as
follows:

-   **Presentation configuration** -- definitions of slide dimensions,
    margins, font sizes, colour palettes and bullet indentation. These
    constants appear at the top of both `answer.js` and
    `slides_template.js` and are used to control layout.

-   **Image utilities** -- helper functions such as
    `getImageDimensions`, `imageSizingContain`, `imageSizingCrop` and an
    image info cache. These functions read image dimensions using
    `image-size` and compute resizing/cropping parameters. Both
    JavaScript files define identical implementations.

-   **Text helpers** -- the function `calcTextBoxHeight` calculates the
    height of a text box based on font size, leading and padding.
    Another helper, `addSlideTitle`, adds a title to a slide with
    consistent positioning.

-   **Slide construction** -- the asynchronous IIFE in each file sets up
    the PPTX layout, adds slides and populates them with images, text
    and charts. `slides_template.js` includes several slide types for
    reference, while `answer.js` is a skeleton for the user to fill in.

-   **Supporting tooling** -- the Python scripts manage image montages
    and convert PPTX files to images with overflow detection. Their
    behaviour is isolated and they form separate tools.

### Data flow and state ownership

-   **Data input** -- the scripts read local image files
    (`placeholder_light_gray_block.png` and any additional images the
    user includes) and optional data for charts. There is no central
    data store; all data are passed via local variables.

-   **State ownership** -- each script owns its own internal state. The
    image sizing cache is a `Map` within each file, meaning duplicate
    caches exist when both scripts are loaded. Slides are built through
    the `pptxgenjs` API, which manages its own internal state.

-   **External integrations** -- dependencies include `pptxgenjs` for
    PPTX creation, `@fortawesome` for icons and `image-size` for
    dimension detection. The Python scripts call `soffice` and
    `pdf2image` but are independent.

### Current boundaries and deployment characteristics

The JavaScript files are run as Node scripts; there is no concept of a
deployed service. The Python tools may be executed separately. There are
no clearly defined module boundaries; duplication of constants and
helpers suggests that the authors intended to reuse functionality but
have not structured it into modules.

### Failure modes and bottlenecks

Because the system is small, failure modes are simple: incorrect sizing
or positioning of images, poor alignment or overflow of slide content,
and errors from missing assets. The lack of tests and duplication
increases the risk of subtle bugs when edits are made. Running the
scripts requires Node and Python, and manual conversion of slides to
images can slow feedback.

## Evidence of Emerging Modularity

Although the codebase is small, there are signs that the system is
"trying" to become modular:

-   **Repeated constants and helper functions** -- both `answer.js` and
    `slides_template.js` define the same constants and helper functions
    (`SLIDE_HEIGHT`, `FONT_SIZE`, `calcTextBoxHeight`,
    `imageSizingContain`, `imageSizingCrop`, `addSlideTitle`, etc.).
    This duplication implies an intent to share configuration and
    utility code across different scripts.

-   **Implicit separation of concerns** -- one script contains slide
    templates and the other acts as the entry point for generating a
    specific presentation. This separation suggests the possibility of
    isolating reusable slide layouts from presentation‑specific content.

-   **Supporting tooling in separate languages** -- Python utilities for
    montage creation and PPTX conversion live alongside the JavaScript
    code. Their isolation is natural because they serve distinct
    purposes.

## Split Candidates and Their Characteristics

To identify potential module boundaries (cells), we evaluate each
candidate according to cohesion, coupling, data ownership, testability,
and reasons to evolve independently. A table summarises the analysis:

  -----------------------------------------------------------------------------------------------------------------------
  Candidate module     Responsibility        Evidence of cohesion    External         Pros for         Cons /
                                                                     dependencies     extraction       uncertainties
  -------------------- --------------------- ----------------------- ---------------- ---------------- ------------------
  **Presentation       Holds constants for   The same constants      Depends only on  Encourages       Must remain
  configuration**      slide size, margins,  appear in both          Node's `path`    consistency      stable; premature
  (`config.js`)        font sizes and        JavaScript files,       and standard     across scripts;  extraction if the
                       colours.              indicating a single     types.           reduces          presentation style
                                             source of truth would                    duplication;     is still evolving.
                                             be beneficial.                           easy to test by  
                                                                                      asserting        
                                                                                      values.          

  **Image utilities**  Functions to read     Functions               Depends on       Reuse avoids     Slight overhead of
  (`imageUtils.js`)    image sizes and       `getImageDimensions`,   `image-size` and duplicating code import; need to
                       compute resize/crop   `imageSizingContain`    `fs`.            and caches; easy handle cache
                       parameters, including and `imageSizingCrop`                    to unit test by  invalidation if
                       a cache.              are identical in both                    mocking          used in
                                             files; they form a                       `image-size`.    long‑running
                                             coherent unit.                                            processes.

  **Text and layout    Helpers like          These functions         Depends on       Centralises      The interface may
  helpers**            `calcTextBoxHeight`   logically belong        `pptxgenjs`      layout logic;    be speculative
  (`layoutUtils.js`)   and `addSlideTitle`.  together because they   types.           simplifies slide until multiple
                                             compute layout metrics                   construction     slide types are
                                             and add text to slides.                  scripts.         implemented.

  **Slide templates**  Each slide type       `slides_template.js`    Relies on        Encapsulates     Requires careful
  (`templates/`)       implemented as a      contains multiple slide `pptxgenjs`,     complex slide    contract design
                       function returning a  examples that could be  `imageUtils`,    layouts; allows  (inputs/outputs)
                       configured slide.     split into separate     `layoutUtils`    independent      and may be
                                             functions or files.     and              evolution and    premature if only
                                                                     configuration.   testing of each  a few slides are
                                                                                      template.        needed.

  **Montage and        Python scripts remain They already operate    None (already    No changes       --
  conversion tools**   as separate           independently and have  extracted).      required; they   
                       command‑line tools.   their own dependencies                   can be treated   
                                             (`PIL`, `pdf2image`).                    as separate      
                                                                                      modules or       
                                                                                      micro‑services   
                                                                                      if needed.       
  -----------------------------------------------------------------------------------------------------------------------

These candidates have clear responsibilities and can be given stable
input and output contracts. They own their own state (e.g., the image
cache) and depend on a small set of libraries. They can be unit tested
independently. Extracting them would reduce duplication and cognitive
load but should wait until there is evidence of repeated change
pressure.

## Decision Framework: When to Split

Drawing on industry guidance and domain‑driven design principles, we
create a decision framework to decide when to split a module into an
independent cell.

### Evidence‑based triggers

-   **Multiple reasons to change** -- if a component serves several
    responsibilities (e.g., configuration constants and slide
    construction) or needs to change for unrelated reasons, consider
    splitting. Strong module boundaries help teams change parts of the
    system without understanding
    everything[\[1\]](https://martinfowler.com/articles/microservice-trade-offs.html#:~:text=Strong%20Module%20Boundaries%20).

-   **Repeated change pressure** -- when code must be edited in multiple
    places to update the same behaviour (e.g., changing the slide
    dimensions in two files), extraction reduces duplicated effort.

-   **Independent lifecycles** -- if part of the system evolves at a
    different rate or requires a different testing strategy (e.g., slide
    templates reused across projects versus project‑specific scripts),
    isolation makes sense.

-   **Coupling through shared state** -- modules should own their data;
    direct access to another module's internals causes coupling and
    fragility. In a modular monolith, data should be accessed only
    through public
    interfaces[\[2\]](https://binaryigor.com/modular-monolith-and-microservices-data.html#:~:text=,but%20only%20eventually%2C%20not%20immediately)[\[3\]](https://binaryigor.com/modular-monolith-and-microservices-data.html#:~:text=Mainly%20because%20of%20Coupling%3A%20the,database%20completely%2C%20from%20Postgres%20to).

-   **Feedback‑time reduction** -- splitting should reduce wait time for
    tests or builds. For example, unit tests for image sizing utilities
    should not require executing the entire slide generation script.

-   **Organisational boundaries** -- if different teams own different
    parts of the code, separation can reflect Conway's
    law[\[4\]](https://martinfowler.com/articles/microservice-trade-offs.html#:~:text=Advocates%20of%20microservices%20are%20quick,that%20kind%20of%20communication%20pattern).

### Caution against premature splitting

-   **Unclear domain** -- if the responsibilities are still evolving,
    keep code together to avoid speculative interfaces. Microservices
    advocates warn that premature distribution introduces complexity
    without
    benefit[\[5\]](https://martinfowler.com/articles/microservice-trade-offs.html#:~:text=%E2%80%A6but%20come%20with%20costs).

-   **Speculative abstractions** -- extracting modules based on a single
    use case often leads to unnecessary layers and brittle interfaces.

-   **Shared mutable state** -- if a potential module must share a large
    portion of its state with others, splitting will introduce expensive
    synchronisation. DDD recommends that each module owns its data and
    that outside modules access it only through well‑defined
    interfaces[\[2\]](https://binaryigor.com/modular-monolith-and-microservices-data.html#:~:text=,but%20only%20eventually%2C%20not%20immediately).

-   **Tiny modules** -- splitting into many small modules can increase
    coordination costs and make the system harder to reason about. It is
    better to start with a modular monolith and only split when the
    benefits outweigh the costs.

### Scoring model

To decide whether to keep unified, mark as a watch zone or extract a
module, we assign each candidate a score from 0 (low) to 5 (high) along
several factors. Higher scores in the positive factors (cohesion,
testability, interface stability, feedback‑time reduction, cognitive
load reduction, independent evolution) and lower scores in the negative
factors (coupling, premature abstraction, migration difficulty) favour
extraction. For each candidate, evaluate:

1.  **Cohesion** -- does the code have a single responsibility?
2.  **Coupling** -- how strongly does it depend on other parts of the
    system?
3.  **Change frequency** -- how often does it change relative to the
    rest of the code?
4.  **Independent testability** -- can it be tested in isolation?
5.  **Feedback‑time reduction** -- will extraction speed up local tests
    or builds?
6.  **Interface stability** -- how stable is the contract likely to be?
7.  **State ownership clarity** -- does it own its data?
8.  **Failure isolation benefit** -- will isolating reduce blast radius
    of bugs?
9.  **Cognitive load reduction** -- does splitting help developers
    understand the system?
10. **Deployment/runtime independence** -- does it require a different
    runtime or scaling model?
11. **Risk of premature abstraction** -- is there evidence of repeated
    patterns?
12. **Migration difficulty** -- how hard is it to extract without
    breaking existing behaviour?

Aggregate the scores to classify decisions:

-   **Keep unified (0--20)** -- the benefit of splitting is low; monitor
    but do not extract.
-   **Mark as watch zone (21--30)** -- potential to split; track change
    frequency and coupling.
-   **Extract internal module (31--40)** -- create a new file or package
    within the monolith.
-   **Extract service/agent (41+)** -- consider a separate process or
    agent role when independent deployment, security or scaling is
    required.
-   **Merge back** -- if a previous extraction fails (e.g., interface
    changes frequently, tests become slower), bring the code back into
    the parent module.

## Cell Lifecycle Model

We model each candidate's evolution as a living cell:

1.  **Seed** -- a behaviour appears once inside the parent module; no
    immediate split.
2.  **Watch zone** -- the behaviour reappears or causes friction; note
    the boundary but delay extraction.
3.  **Budding cell** -- the behaviour has a clear responsibility, local
    tests and a draft contract. Start refactoring into a separate file
    or package; treat the old and new code paths concurrently.
4.  **Independent cell** -- the module has stable ownership, contract
    tests and limited coupling. It can be developed by a team in
    isolation.
5.  **Specialised cell** -- the module has its own development cadence,
    performance profile or deployment path (e.g., a service). It may
    require its own runtime (e.g., Python vs Node).
6.  **Diseased cell** -- if coupling increases or the interface is
    unstable, causing frequent breakages, treat it as diseased. Either
    repair the boundary or merge back.
7.  **Merge or repair** -- if a split fails to deliver benefits (tests
    slower, cognitive load higher), bring the code back or redefine the
    boundary.

## Designing for Future Splitting

### Principles from the start

-   **Separate by responsibility** -- group code by what it does, not by
    technical layer. A configuration file should not be mixed with slide
    construction logic.
-   **Explicit data ownership** -- each module owns its data and exposes
    it through explicit interfaces. Direct access to another module's
    state is
    discouraged[\[2\]](https://binaryigor.com/modular-monolith-and-microservices-data.html#:~:text=,but%20only%20eventually%2C%20not%20immediately).
-   **Isolate side effects** -- reading files, writing slides or calling
    external programs should be wrapped in small functions; the bulk of
    the logic remains pure and testable.
-   **Small, stable interfaces** -- modules should communicate through
    small, clear contracts. DDD's notion of bounded contexts emphasises
    explicit mapping between contexts when
    needed[\[6\]](https://martinfowler.com/bliki/BoundedContext.html#:~:text=Bounded%20Context%20is%20a%20central,being%20explicit%20about%20their%20interrelationships).
-   **Separate orchestration from execution** -- for example, a
    high‑level `generatePresentation()` function orchestrates the
    creation of slides but delegates details to template functions.
-   **Keep domain logic separate from transport and tooling** -- avoid
    mixing slide templates with file IO or CLI parsing.
-   **Local contracts for testing** -- each major capability should have
    a way to run tests without starting the entire system (e.g., unit
    tests for `imageUtils` and `layoutUtils`).
-   **Monitor coupling and feedback time** -- track metrics like build
    time and test duration; if these grow disproportionately when
    editing certain files, consider extraction.
-   **Prefer reversible refactors** -- early extractions should be small
    and reversible; avoid large rewrites until there is clear evidence.

### Agent decision protocol

Before implementing a feature, an autonomous agent should ask:

1.  Does this change belong to an existing responsibility? If so, modify
    the existing module.
2.  Does it introduce a new responsibility? If yes, consider a watch
    zone.
3.  Will it increase coupling between modules? If so, look for ways to
    reduce coupling or mark as a watch zone.
4.  Does it introduce a new data owner? If yes, plan for an interface to
    control access.
5.  Does it require a different test strategy (e.g., asynchronous code,
    heavy IO)? Consider separating it.
6.  Will it slow down feedback (build or test time)? Avoid placing it in
    a core module.
7.  Does it make the current module harder to reason about? Avoid
    lumping unrelated concerns together.
8.  Is this the first, second or third time this pattern appears? Only
    split on the third appearance unless there are strong reasons
    (security isolation, runtime constraints).
9.  Would a local module contract make the change safer? If yes, start
    designing the contract.
10. Can the feature be tested independently after splitting? If not,
    keep unified until it can.

## Refactoring Strategy

When the scoring model indicates extraction, follow these rules:

1.  **Preserve behaviour first** -- add characterisation tests to
    capture current behaviour.
2.  **Define the public contract** -- determine function signatures and
    expected inputs/outputs.
3.  **Move one responsibility at a time** -- avoid refactoring multiple
    concerns simultaneously.
4.  **Keep old and new paths temporarily** -- run both implementations
    side by side if necessary; compare outputs.
5.  **Use adapters** -- if new interfaces differ, provide adapters to
    maintain backward compatibility.
6.  **Eliminate shared mutable state** -- copy or encapsulate data;
    avoid global variables.
7.  **Add local tests** -- new module should have its own unit tests;
    parent module should have contract tests for integration.
8.  **Add integration tests only for cross‑module behaviour** -- avoid
    unnecessary end‑to‑end tests that slow feedback.
9.  **Measure feedback time before and after** -- extraction should
    reduce build/test time; if not, reconsider.
10. **Remove dead code** -- delete old paths when the new module is
    stable.
11. **Update documentation and agent instructions** -- describe new
    boundaries and responsibilities.
12. **Define rollback criteria** -- know when to revert if extraction
    causes problems.

## Feedback‑Time Strategy

To optimise learning loops:

-   **Unit tests validate internal behaviour** of each module (e.g.,
    `imageUtils`, `layoutUtils`). They run quickly and do not invoke
    file IO.
-   **Contract tests validate module boundaries** -- ensure that
    `generateSlide()` functions accept and return the correct shapes.
-   **Integration tests validate critical collaborations** -- for
    example, test that a slide created by
    `template.generateChartSlide()` appears correctly in the final PPTX.
-   **End‑to‑end tests are few and reserved for core user journeys** --
    for example, generating an entire deck and checking that it opens in
    PowerPoint without overflow.
-   **Select tests based on changed cells** -- if editing only
    `layoutUtils`, run its unit tests and contract tests; avoid running
    the entire presentation generation test suite.
-   **Ensure new cells reduce waiting time** -- if splitting leads to
    more integration tests and slower feedback, it may not be justified.

## Architecture Outputs

### Responsibility and dependency maps

-   **Responsibility map** -- identifies five main responsibilities:
    presentation configuration, image utilities, layout/text helpers,
    slide templates, and tooling. Each responsibility is currently
    co‑located in the JavaScript files but can be separated.

-   **Dependency map** -- `answer.js` and `slides_template.js` depend on
    `pptxgenjs`, `image-size` and `@fortawesome` for icons. Proposed
    modules would depend on `config` for constants, `imageUtils` for
    sizing, and `layoutUtils` for text layout. The Python scripts are
    independent.

-   **Data ownership map** -- the only mutable state is the image info
    cache, which should belong to `imageUtils`; other modules should not
    access it directly.

-   **Test boundary map** -- unit tests for utilities; contract tests
    between templates and configuration; integration tests between
    JavaScript modules and PPTX generation; no tests currently exist,
    which is a risk.

### Feedback‑time bottlenecks

Currently there are no automated tests, so feedback depends on manually
running the scripts and visually inspecting the resulting PPTX or
images. This is slow and subjective. Splitting into testable modules
would enable fast unit tests and reduce iteration time.

### Watch zones and split candidates

-   **Presentation configuration and image utilities** -- currently
    duplicated across files. Mark as watch zones because they have high
    cohesion and could be extracted into modules. If the project grows
    or the constants need to be updated frequently, extraction should
    occur.

-   **Slide templates** -- multiple layouts exist in
    `slides_template.js`. If new presentations require reusing these
    layouts, extract them into separate functions or files. Each
    template should have a clear interface (inputs such as chart data or
    images) and return a configured slide. Track how often new layouts
    are added or modified; extraction should happen when duplication or
    coupling becomes evident.

-   **Layout helpers** -- `calcTextBoxHeight` and `addSlideTitle` form a
    cohesive unit. Monitor for repeated use across different files;
    extraction reduces duplication.

-   **Python tooling** -- already independent; no action needed.

### No‑split candidates

-   **Single‑use constants** -- if certain values are used only once
    (e.g., a unique colour for a specific slide), keep them local.

-   **One‑off slides** -- if a slide type will not be reused, do not
    extract it prematurely; leave it in the presentation script.

### Recommended first refactor

1.  **Extract configuration and utilities** -- create a `config.js`
    containing constants for slide size, fonts, colours and margins;
    create an `imageUtils.js` with `getImageDimensions`,
    `imageSizingContain` and `imageSizingCrop`; and create a
    `layoutUtils.js` with `calcTextBoxHeight` and `addSlideTitle`.
    Adjust `answer.js` and `slides_template.js` to import these modules.
    This extraction addresses the duplication clearly evidenced in the
    code.
2.  **Add unit tests** for these modules to ensure correctness (e.g.,
    verifying that `calcTextBoxHeight` returns expected values for
    various font sizes; verifying that `imageSizingCrop` preserves
    aspect ratios). Use a testing framework like Jest.
3.  **Mark slide templates as a watch zone** -- if `slides_template.js`
    continues to grow or is reused across different projects, plan to
    extract each slide type into its own module.

### Recommended future refactors

-   **Template library** -- once multiple presentations reuse slide
    layouts, create a `templates/` folder with functions such as
    `createTitleSlide(config, utils)`,
    `createChartSlide(data, config, utils)`, etc. Each function accepts
    data and returns a configured slide. Add contract tests for each
    template.

-   **Plugin architecture** -- if external developers need to add new
    slide types or themes, design a plugin system where templates are
    registered. Each plugin would declare its inputs, version and
    compatibility.

-   **Automated tooling** -- wrap the Python scripts into npm tasks or
    integrate them into CI to automatically generate previews and detect
    overflow. Consider converting `create_montage.py` into a Node script
    if consistent tooling is desired.

### Risks of splitting

-   **Interface churn** -- if the configuration constants or helpers
    change frequently, extracted modules may need constant updates;
    monitor change frequency before extraction.

-   **Test overhead** -- adding unit and contract tests requires initial
    investment; poorly designed tests may slow feedback.

-   **Developer confusion** -- introducing too many small modules may
    increase cognitive load; ensure documentation is clear.

### Risks of not splitting

-   **Duplication and inconsistency** -- as seen in the repeated
    constants and helpers, changes may be applied to one file and
    forgotten in the other.

-   **Growing complexity** -- if slide templates proliferate, a single
    script may become difficult to navigate.

-   **Lack of tests** -- without modularisation, it is harder to write
    unit tests; errors may go unnoticed until a full presentation is
    rendered.

## Success and Failure Criteria

### Success

An extraction is successful when:

-   The new module has a clear responsibility and stable contract.
-   Unit tests for that module run faster than end‑to‑end tests.
-   Fewer unrelated files need to be modified together.
-   The interface surface area is smaller than the implicit dependency
    it replaced.
-   Developers report reduced cognitive load and faster feedback.
-   Changes to the module do not require changes elsewhere unless the
    contract changes.
-   The total complexity of the system does not increase without
    benefit.

### Failure

An extraction has failed if:

-   The new module requires frequent changes in the parent module; the
    interface is unstable.
-   Tests become slower or more fragile.
-   Data ownership remains unclear.
-   Developers are unsure where to add new features; confusion
    increases.
-   The module is too small to justify its existence.
-   Code duplication increases because the split did not remove
    coupling.

## Final Recommendations

1.  **Keep unified but mark as watch zones** -- For now, maintain a
    single repository and do not distribute functionality across
    services. Extract configuration and helper utilities into separate
    files within the same package; this will reduce duplication and
    facilitate testing. Mark the slide templates as watch zones.

2.  **Gather evidence** -- Start tracking change frequency of constants,
    utilities and slide templates. If the same pattern appears three
    times or more, consider extraction.

3.  **Implement the first refactor** -- Create `config.js`,
    `imageUtils.js` and `layoutUtils.js` modules. Add unit tests for
    each. Refactor `answer.js` and `slides_template.js` to import these
    modules. This change has low migration risk and high cohesion.

4.  **Do not extract services yet** -- The system is small; there is no
    need for independent deployment. Focus on creating a modular
    monolith with clear cell boundaries. Microservices introduce
    distribution costs such as latency, eventual consistency and
    operational
    complexity[\[5\]](https://martinfowler.com/articles/microservice-trade-offs.html#:~:text=%E2%80%A6but%20come%20with%20costs)[\[7\]](https://martinfowler.com/articles/microservice-trade-offs.html#:~:text=Distribution%20).

5.  **Design with bounded contexts in mind** -- As the system grows or
    new domains emerge (e.g., dynamic charts, data retrieval), identify
    bounded contexts and design explicit context maps. DDD teaches that
    large domains should be divided into bounded contexts with explicit
    relationships[\[6\]](https://martinfowler.com/bliki/BoundedContext.html#:~:text=Bounded%20Context%20is%20a%20central,being%20explicit%20about%20their%20interrelationships).

6.  **Empower autonomous agents** -- Use the decision protocol outlined
    above. Agents should treat potential split points as watch zones;
    only on repeated change pressure or clear differences in lifecycle
    should they extract. Align module boundaries with data ownership,
    domain concepts and team responsibilities.

Following these recommendations will allow the system to evolve
organically. It will remain simple when small but be prepared to grow
into a healthier modular structure when complexity demands it.

------------------------------------------------------------------------

[\[1\]](https://martinfowler.com/articles/microservice-trade-offs.html#:~:text=Strong%20Module%20Boundaries%20)
[\[4\]](https://martinfowler.com/articles/microservice-trade-offs.html#:~:text=Advocates%20of%20microservices%20are%20quick,that%20kind%20of%20communication%20pattern)
[\[5\]](https://martinfowler.com/articles/microservice-trade-offs.html#:~:text=%E2%80%A6but%20come%20with%20costs)
[\[7\]](https://martinfowler.com/articles/microservice-trade-offs.html#:~:text=Distribution%20)
Microservice Trade-Offs

<https://martinfowler.com/articles/microservice-trade-offs.html>

[\[2\]](https://binaryigor.com/modular-monolith-and-microservices-data.html#:~:text=,but%20only%20eventually%2C%20not%20immediately)
[\[3\]](https://binaryigor.com/modular-monolith-and-microservices-data.html#:~:text=Mainly%20because%20of%20Coupling%3A%20the,database%20completely%2C%20from%20Postgres%20to)
Modular Monolith and Microservices: Data ownership, boundaries,
consistency and synchronization

<https://binaryigor.com/modular-monolith-and-microservices-data.html>

[\[6\]](https://martinfowler.com/bliki/BoundedContext.html#:~:text=Bounded%20Context%20is%20a%20central,being%20explicit%20about%20their%20interrelationships)
Bounded Context

<https://martinfowler.com/bliki/BoundedContext.html>
