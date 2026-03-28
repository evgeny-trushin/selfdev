# CSV: Client-Service Contract Integrity

**Category:** Integration Principles

Features must hold across the client-service boundary:
- Verify request and response shapes, status codes, error handling, retries, auth, caching, and idempotency
- Validate that frontend assumptions match backend contracts, migrations, and persistence behavior
- Prefer prompts that name the route, function, DTO or schema, and failure mode
- For bugs with user-visible symptoms, inspect both caller and callee before deciding scope
- A flow is only "done" when both client behavior and service behavior agree
