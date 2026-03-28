# NSF: Next-State Feedback

**Category:** Feedback Intelligence Principles

Treat what happens after each action as a learning signal:
- **Evaluative signals**: pass/fail tests, HTTP status, user correction, UI breakage, stderr, deploy health, and lint output
- **Directive signals**: stack traces, screenshots, diff output, logs, schema mismatches, and user instructions that suggest what should change
- Every high-priority prompt should connect a current issue to the next observable signal that will prove it is fixed
- Prefer prompts that turn raw feedback into a specific corrective action
- If an action produced no observable state change, treat it as a potential no-op and investigate
