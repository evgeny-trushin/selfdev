# OBS: Observability First

**Category:** Observability Principles

If a feature cannot be understood in production, it is incomplete:
- Add structured logs with stable field names and actionable context
- Preserve traceability across UI, client, service, and infrastructure using request IDs or correlation IDs where relevant
- Capture metrics for success, failure, latency, and retry behavior
- Logs should be high-signal, privacy-aware, and easy to connect to a user or system journey
- Prefer prompts that specify which event, metric, or trace should exist after the change
