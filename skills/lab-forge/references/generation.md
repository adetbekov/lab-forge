# Generation

## Contents
1. Default artifact set
2. Budgets
3. Writing the canonical rules file
4. Writing skills
5. Commands
6. Guards (level 2-3)
7. Verification
8. Global layer and harness adapters

## 1. Default artifact set

Two layers. The global layer holds how to work and is installed once per
machine by `scripts/install_global.py install` (section 8). The repo holds only
facts the agent cannot guess. Create only what the skeleton approved. Default
for a DS/ML engineer:

| Artifact | Template | Always? |
|---|---|---|
| Repo `AGENTS.md`: commands, map, invariants, words | `rules.md` | yes |
| `CLAUDE.md` with the single line `@AGENTS.md` | - | if Claude Code is used |
| Pointers for other agents present | `pointer.md` | if 2+ agents |
| Skill `task-intake` - size the task, decompose, plan for L | `skill-task-intake.md` | yes |
| Skill `self-review` - anti-slop check of own diff | `skill-self-review.md` | yes |
| Skill `grill` - ask only what changes the result, as real options | `skill-grill.md` | yes |
| Skill `experiment` - hypothesis -> baseline -> measure -> promote | `skill-experiment.md` | DS/ML/agents projects |
| Skill `pr-description` | `skill-pr-description.md` | if PRs are used |
| Skill `wiki-page` | `skill-wiki-page.md` | if a wiki channel exists |
| Commands `/intake /review /pr /wiki /deck` | `command.md` | if the agent supports commands |
| Scoped rule for exploration vs production paths | inside `rules.md` or a scoped file | if notebooks exist |
| Bundled skills from the style pack | copied as-is | yes |
| `.lab-forge/state.md` | `state.md` | yes |

Anything else (ADR folder, changelog, status page, roadmap, onboarding doc) is
offered only when the audit shows the need and the user says yes.

## 2. Budgets

| File | Max lines |
|---|---|
| Repo `AGENTS.md` (managed global copy not counted) | 60 |
| Global `AGENTS.md` + `overrides.md` | 80 |
| Pointer | 5 |
| Generated skill SKILL.md | 120 |
| Command | 10 |
| Plan file for an L task (written at work time) | 60 |
| `.lab-forge/state.md` | 60 |

Over budget -> cut or move detail into a skill; never shrink by removing the
"why" of a rule that is not obvious.

## 3. Writing the repo rules file

- Facts only: commands, paths, invariants, domain words. Anything about how to
  work (branches, scope, task size, style, replies) is in the global layer;
  writing it again here is drift.
- Numbered, imperative, one line per rule where possible, with the reason when
  it is not obvious. The agent follows rules better when it knows why.
- Every pain point from the interview becomes a concrete rule, phrased as what
  to do instead ("reuse helpers in `utils/io.py`; do not write new readers").
- Commands to run (tests, lint, pipeline) are copied from the project's real
  Makefile, pyproject, dvc.yaml or README. Never invent a command.

## 4. Writing skills

- Frontmatter `description` carries all triggers: what it does and when to use
  it, with the words the user actually says. Make it a little pushy - agents
  under-trigger skills.
- Body: short steps, output format, one example if the format is strict. Link to
  the rules file instead of repeating rules.
- Skills adapt to the project: replace template placeholders with real paths and
  tools, delete sections that do not apply.

## 5. Commands

Thin wrappers that invoke a skill, so the user has a manual lever when automatic
triggering misses. They never contain logic of their own.

## 6. Guards (level 2-3)

Minimum set matching the stack; do not add tools the project does not use.
- Formatter and linter already used by the project, or the project's language
  default if none (ask).
- Secret scan and large-file check.
- Optional custom check derived from an invariant (for example: no notebook
  cells in the production package). Keep each custom hook under 30 lines and
  give it a clear failure message.
Level 3: one CI job that runs the same checks. Nothing more without asking.

## 7. Verification

Run `scripts/verify_setup.py <project>` after generating. It checks budgets,
that relative links resolve, that no two rule files carry the same full rule
text, and that each skill has name and description. Fix every failure, then do
the dry run described in SKILL.md phase 6.

## 8. Global layer and harness adapters

`scripts/install_global.py install --harness <list>` writes `~/.lab-forge/`
(`AGENTS.md` from `assets/templates/global-agents.md`, `overrides.md`,
`hooks/guard.py`, `state.md`) and one managed block per harness. It never
touches text outside its `<!-- lab-forge:begin/end -->` markers, and a rerun
keeps the canary.

| Harness | Global file | How | Guard hook |
|---|---|---|---|
| Claude Code | `~/.claude/CLAUDE.md` | `@` import | `~/.claude/settings.json` PreToolUse |
| Codex | `$CODEX_HOME/AGENTS.md` | copy | `$CODEX_HOME/hooks.json` PreToolUse |
| Copilot CLI | `~/.copilot/copilot-instructions.md` | copy | - |
| Antigravity, Gemini CLI | `~/.gemini/GEMINI.md`, plus `context.fileName` so repo `AGENTS.md` is read | copy | - |
| Cursor, Copilot in VS Code | none (User Rules live in the UI) | `install_global.py repo <dir>` copies the block into the repo `AGENTS.md` | - |

Copies follow `overrides.md`: `tune.py` runs `sync` after a global tune.
`install_global.py check` reports drift. Without a hook, the same checks run by
hand: `guard.py branch`, `guard.py scope` (globs in `.lab-forge/scope`),
`guard.py imports` (unresolved imports, installed versions to read docs for).

Smoke test after install: `scripts/smoke.py`. Each harness CLI found on PATH
answers `lab-forge ping` with the global and repo canaries, and Claude Code and
Codex must not land a commit on `main`. IDE-only harnesses print the same check
to do by hand. Record what passed in `.lab-forge/state.md`.
