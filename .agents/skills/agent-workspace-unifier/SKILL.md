---
name: agent-workspace-unifier
description: Unify repository agent instructions and portable skills across Codex and Claude Code. Use when setting up or migrating a project to use AGENTS.md as the canonical shared instruction file, CLAUDE.md as a thin Claude adapter, .agents/skills as the shared skill source, and .claude/skills symlinks for Claude Code compatibility.
---

# Agent Workspace Unifier

Use this skill to standardize agent-facing project structure across Codex and Claude Code without duplicating instructions or skills.

## Target Layout

```text
AGENTS.md                         # canonical shared project instructions
CLAUDE.md                         # thin Claude adapter importing AGENTS.md
.agents/
  README.md                       # shared asset policy
  hooks/README.md                 # shared hook policy
  templates/README.md             # shared template policy
  skills/<skill-name>/SKILL.md    # portable shared skills
.claude/
  skills/<skill-name> -> ../../.agents/skills/<skill-name>
  skills/<claude-only>/SKILL.md   # Claude-only workflows when needed
```

## Decision Rule

Prefer a skill when the workflow is repeated across projects or needs scripts, references, or validation. Prefer a boilerplate snippet only for one-off text that will not be maintained.

For this unification workflow, use the skill plus bundled script. The script supplies the boilerplate safely and repeatably.

## Workflow

1. Inspect the repository for `AGENTS.md`, `AGENT.md`, `CLAUDE.md`, `.agents/`, and `.claude/skills/`.
2. Run the bundled script in dry-run mode first:

   ```bash
   python .agents/skills/agent-workspace-unifier/scripts/unify_agent_workspace.py --repo .
   ```

3. Review the planned actions. The script should not modify files without `--apply`.
4. Apply the standard structure:

   ```bash
   python .agents/skills/agent-workspace-unifier/scripts/unify_agent_workspace.py --repo . --apply --force-claude --retire-agent-md
   ```

5. If the project has portable skills, keep their source in `.agents/skills/<name>` and let the script create `.claude/skills/<name>` symlinks.
6. Keep Claude-only workflows as real directories under `.claude/skills/`.
7. Never move personal settings such as `.claude/settings.local.json` into shared files.

## Script Behavior

The script:

- Creates `.agents/README.md`, `.agents/hooks/README.md`, `.agents/templates/README.md`, and `.agents/skills/`.
- Creates `AGENTS.md` if missing, optionally seeding it from existing `CLAUDE.md` or `AGENT.md`.
- Inserts shared ownership and skill policy sections into `AGENTS.md` when absent.
- Writes `CLAUDE.md` as a thin adapter when `--force-claude` is supplied, backing up existing content first.
- Retires legacy `AGENT.md` with a backup when `--retire-agent-md` is supplied.
- Symlinks portable `.agents/skills/*` into `.claude/skills/*`.
- Leaves `.claude/settings.local.json` and other personal settings untouched.

Read `references/policy.md` for the rationale and edge cases before changing the policy.
