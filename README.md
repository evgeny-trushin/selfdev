# Self-Development Organism

An AI-powered code evolution system. It scans your project, generates precise development prompts (what to build, fix, test, document), and tracks progress through sequential increments — so any AI agent can evolve your codebase on autopilot.

## Table of Contents

1. [What's New: VS Code Agents](#whats-new-vs-code-agents)
2. [Use Cases](#use-cases)
3. [Why Selfdev](#why-selfdev)
4. [How to Use](#how-to-use)
5. [How It Works](#how-it-works)

---

## What's New: VS Code Agents

Selfdev now ships with four specialized [VS Code agents](https://github.com/evgeny-trushin/selfdev/blob/main/.github/agents/) in `.github/agents/`. Each agent has a dedicated role in the development lifecycle — pick the right one for the task at hand.

![VS Code Agents panel showing selfdev agents](https://selfdev.trushin.vip/img/visual-studio-code-agents.webp)

| Agent | Role |
|-------|------|
| **[know-agent](https://github.com/evgeny-trushin/selfdev/blob/main/.github/agents/know-agent.md)** | Knowledge analyst. Scans `principles/`, cross-references with `requirements/` and source code, validates consistency, and produces a structured quality report — preparing the ground for selfdev-agent. |
| **[selfdev-agent](https://github.com/evgeny-trushin/selfdev/blob/main/.github/agents/selfdev-agent.md)** | End-to-end development agent. Combines plan-agent analysis with do-agent execution in a continuous loop: creates the requirement, implements each increment, runs tests, commits, pushes, and repeats until all increments ship. |
| **[plan-agent](https://github.com/evgeny-trushin/selfdev/blob/main/.github/agents/plan-agent.md)** *(sub-agent)* | Planning and analysis sub-agent of selfdev-agent. Clarifies the task, reviews git history for patterns, analyses the codebase, and creates a detailed execution plan as a new `requirements/` increment with acceptance criteria. |
| **[do-agent](https://github.com/evgeny-trushin/selfdev/blob/main/.github/agents/do-agent.md)** *(sub-agent)* | Strict execution sub-agent of selfdev-agent. Picks up the current `_todo_` increment and implements it **exactly** as specified — no deviations, no scope creep. Runs tests, commits with traceability, and halts on any ambiguity for approval. |

---

## Use Cases

### AWS SA Pro Quiz Trainer

[![AWS SA Pro Quiz Trainer](https://selfdev.trushin.vip/img/aws-cert-1.webp)](https://aws-cert.trushin.vip/)
[![AWS SA Pro Quiz Trainer - Progress Tracking](https://selfdev.trushin.vip/img/aws-cert-2.webp)](https://aws-cert.trushin.vip/)
[![AWS SA Pro Quiz Trainer - Interactive Mind Map](https://selfdev.trushin.vip/img/aws-cert-3.webp)](https://aws-cert.trushin.vip/)
[![AWS SA Pro Quiz Trainer - Flashcards and Quiz](https://selfdev.trushin.vip/img/aws-cert-4.webp)](https://aws-cert.trushin.vip/)

**100% Free & No Registration.** A comprehensive study application featuring Smart Quizzes with Bayesian Adaptive Engine, Interactive Mind Map with unseen/weak-area filters, Spaced-Repetition Flashcards (SM-2), Service Mastery Heatmaps with completion projection, near-miss scoring, detailed per-option feedback, and built-in progression limits for optimal retention.

🔗 **[aws-cert.trushin.vip](https://aws-cert.trushin.vip/)**

### System Design Quiz Trainer

[![System Design Quiz Trainer](https://selfdev.trushin.vip/img/system-design-1.webp)](https://system-design.trushin.vip/)
[![System Design Quiz Trainer - Interactive Mind Map](https://selfdev.trushin.vip/img/system-design-2.webp)](https://system-design.trushin.vip/)
[![System Design Quiz Trainer - Quiz Explanations](https://selfdev.trushin.vip/img/system-design-3.webp)](https://system-design.trushin.vip/)

**100% Free & No Registration.** A comprehensive study application focused on **Privacy-First** learning (Data Stays Local). Highlights include Adaptive Smart Quizzes, Spaced Repetition Flashcards, an Interactive Mind Map with topic filtering, and detailed Explanations with Architectural Diagrams for deeper comprehension.

🔗 **[system-design.trushin.vip](https://system-design.trushin.vip/)**

### More Projects

| Project | Description |
|---------|-------------|
| **[trushin.vip](https://trushin.vip/)** | Portfolio website, 100% created by selfdev logic. |
| **[cloud-agents.trushin.vip](https://cloud-agents.trushin.vip/)** | The how-to guide on Cloud Agents. |
| **[selfdev.trushin.vip](https://selfdev.trushin.vip/)** | Selfdev project website, developed by selfdev logic. |

---

## Why Selfdev

- **Zero config** — drop the `selfdev/` folder into any project and run. No dependencies beyond Python 3.8+.
- **Increment-driven development** — requirements are split into small, sequential increments (`requirements/increment_XXXX_todo_*.md`). The system shows one at a time, with acceptance criteria and injected principles, so you (or an AI agent) always know exactly what to do next.
- **Multi-perspective analysis** — five built-in perspectives (User, Test, System, Analytics, Debug) score your codebase fitness from 0.0 to 1.0 and generate prioritized prompts.
- **Works with any AI agent** — GitHub Copilot, Claude, ChatGPT, Gemini, Cursor — just paste the one-liner prompt below and the agent does the rest.
- **Evolutionary tracking** — every completed increment advances a generation. Fitness history is persisted in `organism_state.json` so you can see progress over time.

---

## How to Use

### One-liner for AI agents (copy-paste)

> Clone https://github.com/evgeny-trushin/selfdev to a temp dir, copy its `selfdev/`, `requirements/`, and `principles/` folders into my project root, then run `./selfdev/develop.sh`. Read the generated prompt, implement it, commit, and run `./selfdev/develop.sh` again. Repeat until all increments are completed.

Requirements: **Python 3.8+** (no pip packages needed).

### Manual workflow

```
┌─────────────────────────────────────────────┐
│  ./selfdev/develop.sh                       │
│  ↓                                          │
│  Read the prompt (increment + principles)   │
│  ↓                                          │
│  Implement the requirement                  │
│  ↓                                          │
│  git add -A && git commit && git push       │
│  ↓                                          │
│  ./selfdev/develop.sh        ← loop back    │
│  (verifies done → shows next increment)     │
└─────────────────────────────────────────────┘
```

### CLI reference

```bash
./selfdev/develop.sh              # Show current increment (default)
./selfdev/develop.sh --advance    # Mark current done, show next
./selfdev/develop.sh --state      # Print organism state & fitness

# Run specific perspectives
./selfdev/develop.sh --user       # Documentation, UX, features
./selfdev/develop.sh --test       # Coverage, missing tests
./selfdev/develop.sh --system     # Complexity, coupling, architecture
./selfdev/develop.sh --analytics  # Trends, patterns over time
./selfdev/develop.sh --debug      # TODOs, FIXMEs, bugs

./selfdev/develop.sh --all        # Run all five perspectives
./selfdev/develop.sh --selfdev    # Analyze selfdev itself
./selfdev/develop.sh --root DIR   # Analyze a different directory
```

---

## How It Works

### Increment-driven loop

The core idea: **requirements are pre-split into numbered increments** stored in `requirements/`. Each increment file contains a description, acceptance criteria, and links to applicable principles.

```
requirements/
  increment_0001_todo_multi_perspective_validation.md
  increment_0002_todo_state_aware_prompts.md
  increment_0003_todo_evolutionary_tracking.md
  ...
  increment_0013_todo_acceptance_criteria.md
```

When you run `./selfdev/develop.sh`:

1. **Find** the lowest-numbered `_todo_` increment file.
2. **Resolve** all referenced principles from `principles/` and inject their full text into the prompt.
3. **Output** a complete, self-contained prompt: requirement + acceptance criteria + principles + suggested commit message.
4. You (or your AI agent) implement it and commit.
5. On the next run, the system detects the commit, **renames** `_todo_` → `_done_`, advances the generation, and shows the next increment.

### Prompt generation

Each prompt includes:
- **Increment number & title** — e.g. `INCREMENT 0005: Prompt Output Format`
- **Requirement description** — what to build
- **Acceptance criteria** — checklist to verify completion
- **Injected principles** — full text of referenced principles (lateral thinking, biological development, etc.)
- **Workflow instructions** — exact git commands and commit message

### Multi-perspective analysis

When run with `--all` or specific perspective flags, the system analyzes your codebase and produces **fitness scores** (0.0–1.0) plus prioritized prompts:

| Perspective | Analyzes |
|-------------|----------|
| **User** | README quality, docs, feature completeness |
| **Test** | Test coverage ratio, missing test files |
| **System** | McCabe complexity, file size, coupling |
| **Analytics** | Commit trends, fitness history, patterns |
| **Debug** | TODOs, FIXMEs, syntax errors, uncommitted changes |

### Project structure

```
your-project/
├── organism_state.json     # Evolutionary state (auto-managed)
├── principles/             # Development principles (P1, B1, G1, etc.)
├── requirements/           # Increment files (todo ↔ done lifecycle)
└── selfdev/
    ├── develop.sh          # Entry point (bash)
    ├── organism.py         # Orchestrator
    ├── models.py           # Data models & constants
    ├── analyzers.py        # Code & git analysis
    ├── perspectives.py     # Test & system perspectives
    ├── user_perspective.py # User perspective
    ├── diagnostics.py      # Analytics & debug perspectives
    ├── formatters.py       # Output formatting
    └── increment_tracker.py# Increment lifecycle management
```

---

## Prompt Examples

### Bootstrap any project

> "Clone https://github.com/evgeny-trushin/selfdev to a temp dir, copy its `selfdev/` subfolder into my project root, then using my project data create `principles/` and `requirements/` directories with project-specific content. Run `./selfdev/develop.sh` to verify."

### Daily development loop

> "Run `./selfdev/develop.sh`, implement the prompt, commit, and repeat until all increments are done."

### Pre-PR quality gate

> "Run `./selfdev/develop.sh --test --debug --system`, fix all CRITICAL and HIGH issues, then show before/after fitness scores."

### Technical debt sprint

> "Run `./selfdev/develop.sh --system`, implement all refactoring prompts — split large files, reduce complexity below 10, extract duplicated logic."

### Test coverage push

> "Run `./selfdev/develop.sh --test`, generate unit tests for every untested source file it flags. Target 80% coverage."

### Documentation catch-up

> "Run `./selfdev/develop.sh --user`, implement every prompt — add missing README sections, docstrings, usage examples, and CHANGELOG."

### Multi-generation sprint

> "Run 3 generations: for each, run `./selfdev/develop.sh`, implement all HIGH-priority prompts, verify tests pass, then `./selfdev/develop.sh --advance`. Show fitness progression."

### CI/CD integration

```yaml
# .github/workflows/selfdev.yml
name: Selfdev Check
on: [pull_request]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: ./selfdev/develop.sh --test --system --debug
```

### Monorepo / data science / IaC

Adapt perspectives for your domain — the system is extensible. Add custom perspectives by subclassing `PerspectiveAnalyzer` in [selfdev/organism.py](selfdev/organism.py).
