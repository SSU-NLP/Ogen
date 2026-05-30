# Shared Agent Assets

This directory is the shared home for agent-facing assets that should work across Claude Code, Codex, Gemini CLI, Cursor, GitHub Copilot agents, and similar tools.

Use `AGENTS.md` for instructions. Use this directory for reusable files that tool-specific adapters can point at.

## Layout

- `skills/` - portable Agent Skills intended to be shared across tools.
- `hooks/` - reusable hook scripts and hook policy notes.
- `templates/` - shared prompt, report, or config templates when needed.

## Adapter Rule

Each agent should keep its native config file in the location that tool expects, then delegate shared behavior here.

Examples:

- Codex: repo skills are read directly from `.agents/skills/*/SKILL.md`.
- Claude Code: shared project skills should be symlinked from `.claude/skills/<name>` to `.agents/skills/<name>`.
- Claude Code: `.claude/settings.json` or `.claude/settings.local.json` can call `.agents/hooks/*`.
- Codex: `.codex/hooks.json` or `.codex/config.toml` can call `.agents/hooks/*`.
- Gemini CLI: `.gemini/settings.json` can call `.agents/hooks/*`.
- Cursor: `.cursor/hooks.json` can call `.agents/hooks/*`.
- GitHub Copilot agents: `.github/hooks/*.json` can call `.agents/hooks/*`.

Do not duplicate shared hook logic inside tool-specific directories.
Do not duplicate shared skill logic inside tool-specific skill directories.
