# Shared Hooks

Put reusable hook scripts in this directory. Tool-specific configs should call these scripts instead of embedding policy directly.

Current policy:

- Keep hooks idempotent.
- Read event payloads from stdin when the calling tool provides them.
- Exit `0` to allow the action.
- Exit non-zero only for clear policy violations or broken validation.
- Print concise, actionable messages to stderr.

Suggested names:

- `pre_tool_use.*` for shell or tool guardrails.
- `post_tool_use.*` for validation after edits or commands.
- `stop.*` for final session checks.

No hooks are enabled by default in this repository yet. Add the tool-specific adapter file only when there is a concrete policy to enforce.
