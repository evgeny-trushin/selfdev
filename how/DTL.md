# DTL: Detail Fidelity

**Category:** Feedback Intelligence Principles

Prompts must zoom to the smallest useful unit of evidence:
- Name the exact artifact: screen, component, route, API call, config key, log event, failing test, or command output
- Capture concrete states: empty, loading, success, partial success, degraded, timeout, and error
- Prefer one precise defect over a vague area-wide improvement request
- Include the expected next observable state after the change
- If evidence is missing, first prompt to collect it rather than guessing
