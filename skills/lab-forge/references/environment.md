# Environment - agents, folders, ownership levels

## Contents
1. Which agent reads what
2. Choosing the canonical file
3. Ownership levels 0-3
4. Network and tools
5. Corporate wrappers and unknown agents

## 1. Which agent reads what

`scripts/detect_env.py` lists what exists. Folder conventions change between
versions, so treat this table as a starting point and confirm by checking the
agent's own settings or docs on the machine when in doubt.

| Agent | Always-on rules | Scoped rules | Skills | Commands | Agents/personas |
|---|---|---|---|---|---|
| GitHub Copilot (VS Code) | `.github/copilot-instructions.md`, `AGENTS.md` | `.github/instructions/*.instructions.md` (`applyTo:` glob) | `.github/skills/`, `.claude/skills/`, `.agents/skills/` | `.github/prompts/*.prompt.md` | `.github/agents/*.agent.md` |
| Claude Code | `CLAUDE.md` (root and subfolders) | subfolder `CLAUDE.md` | `.claude/skills/` | `.claude/commands/*.md` | `.claude/agents/*.md` |
| Cursor | `.cursor/rules/*.mdc` (`alwaysApply: true`) | `.mdc` with globs | `.cursor/skills/` | - | - |
| Codex / generic | `AGENTS.md` | subfolder `AGENTS.md` | `.agents/skills/` | - | - |

User level (applies to all projects, needs no repo rights): `~/.copilot/`,
`~/.claude/` (`CLAUDE.md`, `skills/`, `commands/`), VS Code user prompts folder.
On Windows `~` is `%USERPROFILE%`.

## 2. Choosing the canonical file

- Several agents in use -> canonical `AGENTS.md`; `CLAUDE.md`,
  `.github/copilot-instructions.md`, `.cursor/rules/main.mdc` become pointers.
- Only Claude Code -> canonical `CLAUDE.md`.
- Only Copilot and it ignores `AGENTS.md` in this setup -> canonical
  `.github/copilot-instructions.md`.
- Skills folder: prefer the one every present agent reads (`.claude/skills/` is
  read by both Claude Code and Copilot). Never keep two copies of a skill.

Pointer template: `assets/templates/pointer.md`.

## 3. Ownership levels

Decide per project, confirm with the user.

| Level | When | lab-forge may write |
|---|---|---|
| 0 - personal | not your repo, or team would not accept AI files | user-level folders only; nothing in the repo |
| 1 - repo files | you can commit docs/config | canonical rules, pointers, skills, commands |
| 2 - local guards | you control dev tooling | + pre-commit hooks, lint config |
| 3 - pipeline | you own the repo's CI | + CI jobs for the same checks |

Level 0 still gets a full setup: the rules and skills live in the user folder
and mention which repo patterns to follow. Signals: an existing
`CODEOWNERS` without the user, protected branches, a big team, a vendor repo ->
suggest level 0 or 1.

## 4. Network and tools

`detect_env.py` reports python, git, pre-commit, dvc, and whether a few hosts
answer. If a generated step needs something missing, ask once ("pre-commit is
not installed and PyPI is unreachable - install from an internal mirror, or skip
guards?"), then degrade and note it in `.lab-forge/state.md`.

## 5. Corporate wrappers and unknown agents

Company builds of Copilot or Claude (for example through a cloud model gateway)
may read only part of the folders above. Do not guess:

1. Write a one-line test rule into the candidate always-on file (for example
   "End every answer with the word FORGE-OK").
2. Ask the user to send one message in each agent tab and report which ones
   obeyed.
3. Keep only the files that work, remove the test line.

Record the result in `.lab-forge/state.md` so tune mode does not repeat it.
