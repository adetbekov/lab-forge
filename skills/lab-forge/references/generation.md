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
| Profile repo block, copied verbatim into the repo `AGENTS.md` | `references/profiles/*.md` | yes, seed too |
| Minimal `pyproject.toml` with the pytest `pythonpath` | section 3 | new Python project |
| `CLAUDE.md` with the single line `@AGENTS.md` | - | if Claude Code is used |
| Pointers for other agents present | `pointer.md` | if 2+ agents |
| Skill `task-intake` - size the task, decompose, plan for L | `skill-task-intake.md` | yes |
| Skill `self-review` - anti-slop check of own diff, M and bigger | `skill-self-review.md` | yes |
| Skill `grill` - ask only what changes the result, as real options | `skill-grill.md` | yes |
| Skill `experiment` - hypothesis -> baseline -> measure -> promote | `skill-experiment.md` | DS/ML/agents projects |
| Skill `pr-description` | `skill-pr-description.md` | if PRs are used |
| Skill `wiki-page` | `skill-wiki-page.md` | if a wiki channel exists |
| Commands `/intake /review /pr /wiki /deck` | `command.md` | if the agent supports commands |
| Scoped rule for exploration vs production paths | inside `rules.md` or a scoped file | if notebooks exist |
| Bundled skills from the style pack | copied as-is to the user skills folder | once per machine; into the repo only on request |
| `.lab-forge/state.md` | `state.md` | yes |

Anything else (ADR folder, changelog, status page, roadmap, onboarding doc) is
offered only when the audit shows the need and the user says yes.

## 2. Budgets

| File | Max lines |
|---|---|
| Repo `AGENTS.md`, profile block included (managed global copy not counted) | 60 |
| Global core (`core.md`) | 30 |
| Global core + repo template (`rules.md`) | 60 |
| Global `AGENTS.md` (core + defaults) + `overrides.md` | 80 |
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
- The profile's `## Repo block` goes in as is, markers included, in place of
  `{{profile_block}}`. Never shorten or reword it: a paraphrase drops the rule
  that matters (v0.3 turned "own split per fitted step" into "nothing chosen on
  test"). `verify_setup.py` fails on any change. Project invariants follow it.
- Numbered, imperative, one line per rule where possible, with the reason when
  it is not obvious. The agent follows rules better when it knows why.
- Every pain point from the interview becomes a concrete rule, phrased as what
  to do instead ("reuse helpers in `utils/io.py`; do not write new readers").
- Commands to run (tests, lint, pipeline) are copied from the project's real
  Makefile, pyproject, dvc.yaml or README, or from what the user stated. Never
  invent a command, and never add a rule that breaks a stated one.
- New project: prescribe no package layout. If you must, it has to let stated
  commands run from the root with no install step (`pkg/` at the root, not
  `src/pkg/`, unless an editable install is part of setup).
- A new Python project gets a minimal `pyproject.toml`: name, deps and
  `[tool.pytest.ini_options]` `pythonpath = ["."]`. It is setup, not layout.
  The phase 6 dry run includes a bare `pytest`.
- Config format: only what the env reads today (`detect_env.py` reports the
  importable parsers). TOML via `tomllib` on 3.11+, else JSON; YAML only with
  PyYAML installed. The file extension matches the content.
- Run artifacts: the rules name one committed baseline file and one git-ignored
  runs folder, and the generated `.gitignore` entry exists.
- AI co-author trailer: copy the policy the harness or environment imposes
  (system prompt, existing commit trailers, CONTRIBUTING). None found -> the
  style pack default. Record it in `.lab-forge/state.md`; tune changes it.

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
text, that each skill has name and description, and that the profile block
matches `references/profiles/` byte for byte (sha). `verify_setup.py --engine`
checks the engine itself: core ≤ 30 lines, core + repo template ≤ 60. Fix every failure, then do
the dry run described in SKILL.md phase 6.

## 8. Global layer and harness adapters

`scripts/install_global.py install --harness <list>` writes `~/.lab-forge/`
(`core.md`, `defaults.md`, `AGENTS.md` = both, `overrides.md`, `tune.py`,
`hooks/guard.py`, `state.md` with `- Version:`) and one managed block
`<!-- lab-forge:begin core v=… sha=… -->` per harness. It never touches text
outside its markers, and a rerun keeps the canary. A file or block the user
edited is merged with `git merge-file` on the last render kept in
`~/.lab-forge/base/`; a conflict leaves it as is and writes `<file>.rej`. Changed
files are backed up to `~/.lab-forge/backup/<time>/` first. `uninstall` removes
the blocks, hooks and skill links. Older installs go through `scripts/upgrade.py`.

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

Decision hooks, opt-in, off by default, with the user's own endpoint and key:
`install --decide hosted|local|custom [--decide-url URL] [--decide-model NAME] [--decide-key-env VAR]` writes
`~/.lab-forge/decide.json` and adds `guard.py decide stop` (Stop: blocks an unverified "done" once,
"not verified: <what is missing>") and `guard.py decide skill` (UserPromptSubmit: "load skill X" at
confidence ≥ 0.7, over project, user and enabled plugin skills) for Claude Code and Codex, next to any other Stop
hook. **Whatever backend is set gets each prompt, task and final reply; the install prints the host.**

| backend | default url / model | key |
|---|---|---|
| `hosted` | api.liquid.ai, `d1-ultra` | `$LIQUID_AI_API_KEY` |
| `local` | `http://localhost:11434/v1/systemone`, `d1-omni:600m` | none |
| `custom` | your `--decide-url` and `--decide-model` (required) | `$VAR` from `--decide-key-env`, optional |

Any provider works as `custom` if it takes the `/v1/systemone` body (`model`, `state`, `questions` → `answers`);
another API shape needs a proxy that speaks it. The key never goes on the command line or into chat: the user
exports the variable where the agent starts, or writes it to `~/.lab-forge/decide.key` (chmod 600), which is read
when the variable is unset. Without a key the hooks stay silent; the install says which key is missing. Timeout
1.5 s; any error does nothing. `--decide off` removes the hooks. Local d1-omni-600M cannot judge `stop` or `skill`
(JEB-1889 eval), so use it only for plumbing tests.

Smoke test after install: `scripts/smoke.py`. Each harness CLI found on PATH
answers `lab-forge ping` with the global and repo canaries, and Claude Code and
Codex must not land a commit on `main`. IDE-only harnesses print the same check
to do by hand. Record what passed in `.lab-forge/state.md`.
