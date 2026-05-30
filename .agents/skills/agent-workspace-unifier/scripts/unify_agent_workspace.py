#!/usr/bin/env python3
"""Unify agent-facing project layout for Codex and Claude Code."""

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path


AGENTS_HEADER = """## Agent Instruction Ownership

`AGENTS.md` is the canonical source for shared agent instructions in this repository. Keep repository-wide rules, commands, architecture notes, and shared safety expectations here.

Tool-specific files should be thin adapters:

- `CLAUDE.md` imports this file for Claude Code and should only contain Claude-specific routing or exceptions.
- `.claude/` is reserved for Claude Code settings, skills, commands, hooks, and local permissions.
- `.agents/` stores shared agent assets such as reusable skills, hook scripts, templates, and cross-tool notes.
- If another agent needs hooks or settings, keep its native config file minimal and call scripts from `.agents/hooks/` instead of duplicating policy.
"""

SHARED_SKILLS = """## Shared Skills

Portable agent skills live in `.agents/skills/<skill-name>/SKILL.md`. Codex reads this location directly. Claude Code project skills should point to shared skills from `.claude/skills/<skill-name>` with a symlink when the workflow is meant to be identical across agents.

Do not edit a symlinked `.claude/skills/<skill-name>` as if it were the source; edit the matching `.agents/skills/<skill-name>` directory instead. Claude-only skills may remain as real directories under `.claude/skills/`.
"""

CLAUDE_SHIM = """@AGENTS.md
@.agents/README.md

# Claude Code Adapter

This file intentionally stays thin. Shared project instructions live in `AGENTS.md`; shared cross-agent assets live under `.agents/`.

Claude-specific settings, permissions, skills, commands, and hooks may remain under `.claude/`, but they should call or reference `.agents/` assets when the behavior is meant to be shared with other agents.
"""

AGENTS_README = """# Shared Agent Assets

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

Do not duplicate shared hook or skill logic inside tool-specific directories.
"""

HOOKS_README = """# Shared Hooks

Put reusable hook scripts in this directory. Tool-specific configs should call these scripts instead of embedding policy directly.

No hooks are enabled by default. Add tool-specific adapter files only when there is a concrete policy to enforce.
"""

TEMPLATES_README = """# Shared Templates

Put cross-agent prompt, report, or config templates here when they are useful across more than one tool.
"""

MIN_AGENTS = f"""# Repository Guidelines

{AGENTS_HEADER}

{SHARED_SKILLS}
"""


class Plan:
    def __init__(self, apply: bool):
        self.apply = apply
        self.actions: list[str] = []

    def note(self, message: str) -> None:
        self.actions.append(message)
        print(message)


def backup_path(path: Path) -> Path:
    base = path.with_name(path.name + ".pre-agent-unifier.bak")
    if not base.exists():
        return base
    idx = 2
    while True:
        candidate = path.with_name(path.name + f".pre-agent-unifier.{idx}.bak")
        if not candidate.exists():
            return candidate
        idx += 1


def write_text(path: Path, content: str, plan: Plan) -> None:
    if path.exists() and path.read_text(encoding="utf-8") == content:
        plan.note(f"ok: {path}")
        return
    plan.note(f"write: {path}")
    if plan.apply:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def ensure_dir(path: Path, plan: Plan) -> None:
    if path.is_dir():
        plan.note(f"ok: {path}/")
        return
    plan.note(f"mkdir: {path}/")
    if plan.apply:
        path.mkdir(parents=True, exist_ok=True)


def seed_agents_from_legacy(repo: Path) -> str:
    for name in ("AGENT.md", "CLAUDE.md"):
        p = repo / name
        if p.exists() and not p.is_symlink():
            text = p.read_text(encoding="utf-8").strip()
            if text:
                return f"{MIN_AGENTS}\n\n## Migrated Notes From `{name}`\n\n{text}\n"
    return MIN_AGENTS


def ensure_agents_md(repo: Path, plan: Plan) -> None:
    path = repo / "AGENTS.md"
    if not path.exists():
        write_text(path, seed_agents_from_legacy(repo), plan)
        return

    text = path.read_text(encoding="utf-8")
    changed = False
    if "## Agent Instruction Ownership" not in text:
        insert = AGENTS_HEADER.strip() + "\n\n"
        if text.startswith("# "):
            first_newline = text.find("\n")
            text = text[: first_newline + 1] + "\n" + insert + text[first_newline + 1 :]
        else:
            text = "# Repository Guidelines\n\n" + insert + text
        changed = True
    if "## Shared Skills" not in text:
        marker = "## Project Structure"
        if marker in text:
            text = text.replace(marker, SHARED_SKILLS.strip() + "\n\n" + marker, 1)
        else:
            text = text.rstrip() + "\n\n" + SHARED_SKILLS
        changed = True

    if changed:
        plan.note(f"update: {path}")
        if plan.apply:
            path.write_text(text, encoding="utf-8")
    else:
        plan.note(f"ok: {path}")


def ensure_claude_md(repo: Path, plan: Plan, force: bool) -> None:
    path = repo / "CLAUDE.md"
    if path.exists() and path.read_text(encoding="utf-8") == CLAUDE_SHIM:
        plan.note(f"ok: {path}")
        return
    if path.exists() and not force:
        plan.note(f"warn: {path} exists; pass --force-claude to replace with adapter")
        return
    if path.exists() and force:
        b = backup_path(path)
        plan.note(f"backup: {path} -> {b}")
        if plan.apply:
            shutil.copy2(path, b)
    write_text(path, CLAUDE_SHIM, plan)


def retire_agent_md(repo: Path, plan: Plan, retire: bool) -> None:
    path = repo / "AGENT.md"
    if not path.exists():
        return
    if not retire:
        plan.note(f"warn: legacy {path} exists; pass --retire-agent-md to back it up and remove it")
        return
    b = backup_path(path)
    plan.note(f"retire: {path} -> {b}")
    if plan.apply:
        shutil.move(str(path), str(b))


def relative_symlink_target(link: Path, target: Path) -> str:
    return os.path.relpath(target, start=link.parent)


def sync_claude_skill_links(repo: Path, plan: Plan) -> None:
    shared = repo / ".agents" / "skills"
    claude = repo / ".claude" / "skills"
    ensure_dir(claude, plan)
    if not shared.is_dir():
        return

    for skill in sorted(shared.iterdir()):
        if not skill.is_dir() or not (skill / "SKILL.md").exists():
            continue
        link = claude / skill.name
        rel = relative_symlink_target(link, skill)
        if link.is_symlink():
            current = os.readlink(link)
            if current == rel:
                plan.note(f"ok: {link} -> {rel}")
            else:
                plan.note(f"update symlink: {link} -> {rel}")
                if plan.apply:
                    link.unlink()
                    link.symlink_to(rel)
            continue
        if link.exists():
            plan.note(f"skip: {link} exists as a real file/directory; leave as tool-specific")
            continue
        plan.note(f"symlink: {link} -> {rel}")
        if plan.apply:
            link.symlink_to(rel)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="Repository root to update")
    parser.add_argument("--apply", action="store_true", help="Write changes. Default is dry-run.")
    parser.add_argument("--force-claude", action="store_true", help="Replace CLAUDE.md with the thin adapter after backing it up")
    parser.add_argument("--retire-agent-md", action="store_true", help="Back up and remove legacy AGENT.md")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    if not repo.exists():
        raise SystemExit(f"Repository path does not exist: {repo}")

    plan = Plan(apply=args.apply)
    mode = "apply" if args.apply else "dry-run"
    plan.note(f"mode: {mode}")
    plan.note(f"repo: {repo}")

    ensure_dir(repo / ".agents", plan)
    ensure_dir(repo / ".agents" / "skills", plan)
    ensure_dir(repo / ".agents" / "hooks", plan)
    ensure_dir(repo / ".agents" / "templates", plan)
    write_text(repo / ".agents" / "README.md", AGENTS_README, plan)
    write_text(repo / ".agents" / "hooks" / "README.md", HOOKS_README, plan)
    write_text(repo / ".agents" / "templates" / "README.md", TEMPLATES_README, plan)

    ensure_agents_md(repo, plan)
    ensure_claude_md(repo, plan, force=args.force_claude)
    retire_agent_md(repo, plan, retire=args.retire_agent_md)
    sync_claude_skill_links(repo, plan)

    if not args.apply:
        plan.note("dry-run only: re-run with --apply to modify files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
