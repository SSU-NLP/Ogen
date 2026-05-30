# Agent Workspace Unification Policy

## Purpose

Use one canonical instruction file and one canonical portable skill source. Tool-specific files should be adapters, not parallel sources of truth.

## Canonical Files

- `AGENTS.md` owns shared repository instructions.
- `.agents/skills/<name>/SKILL.md` owns portable workflows that both Codex and Claude Code should use.
- `.agents/hooks/` owns shared hook scripts and hook policy.
- `.agents/templates/` owns reusable prompt, report, or config templates.

## Tool Adapters

- `CLAUDE.md` imports `AGENTS.md` and may import `.agents/README.md`.
- `.claude/skills/<name>` should symlink to `.agents/skills/<name>` for shared skills.
- Real directories under `.claude/skills/` are reserved for Claude-only workflows.

## Migration Rules

- Preserve user content by backing up any replaced file with `.pre-agent-unifier.bak` or a numbered variant.
- Do not delete `.claude/settings.local.json`.
- Do not overwrite a real `.claude/skills/<name>` directory unless the user explicitly decides to make that workflow shared.
- Do not assume every `SKILL.md` is portable. Claude-specific instructions such as Claude-only hooks, settings, or slash-command behavior should remain Claude-only.

## Token Budget

The adapter pattern keeps token cost low:

- `AGENTS.md` is always-on shared context.
- Skill metadata (`name` and `description`) is listed up front.
- Full skill bodies load only when a skill triggers.

Keep shared skill descriptions precise and short. Move long examples or policy detail into `references/`.
