# CLN: Plain Text Output

**Category:** Output Principles

- **No ANSI colors**: Console output must never contain escape codes or color sequences
- **Plain text only**: All prompts, banners, and messages use plain UTF-8 text
- **Copy-paste friendly**: Output is directly usable in any context (logs, pipes, LLM prompts)
- **No `--no-color` flag needed**: Plain output is the default and only mode
- **Rationale**: Colored output breaks when piped, logged, or consumed by other tools; plain text is universally compatible
