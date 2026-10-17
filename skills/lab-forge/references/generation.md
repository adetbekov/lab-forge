# Generation

## Contents
1. Default artifact set
2. Budgets
3. Writing the canonical rules file
4. Writing skills
5. Commands
6. Guards (level 2-3)
7. Verification

## 1. Default artifact set

Create only what the skeleton approved. Default for a DS/ML engineer:

| Artifact | Template | Always? |
|---|---|---|
| Canonical rules file | `rules.md` | yes |
| Pointers for other agents present | `pointer.md` | if 2+ agents |
| Skill `task-intake` - size the task, decompose, plan for L | `skill-task-intake.md` | yes |
| Skill `self-review` - anti-slop check of own diff | `skill-self-review.md` | yes |
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
| Canonical rules | 100 |
| Pointer | 5 |
| Generated skill SKILL.md | 120 |
| Command | 10 |
| Plan file for an L task (written at work time) | 60 |
| `.lab-forge/state.md` | 60 |

Over budget -> cut or move detail into a skill; never shrink by removing the
"why" of a rule that is not obvious.

## 3. Writing the canonical rules file

- Numbered, imperative, one line per rule where possible, with the reason when
  it is not obvious. The agent follows rules better when it knows why.
- Order: read-first links -> invariants (from restrictions and the audit) ->
  task ladder -> workflow for M/L -> anti-slop -> languages -> delivery ->
  skills table.
- Merge the style pack with the project: the pack gives the ladder and the
  anti-slop list; the project gives commands, paths, tools, invariants.
- Every pain point from the interview becomes a concrete rule, phrased as what
  to do instead ("reuse helpers in `utils/io.py`; do not write new readers").
- Commands to run (tests, lint, pipeline) are copied from the project's real
  Makefile, pyproject, dvc.yaml or README, or from what the user stated. Never
  invent a command, and never add a rule that breaks a stated one.
- New project: prescribe no package layout. If you must, it has to let stated
  commands run from the root with no install step (`pkg/` at the root, not
  `src/pkg/`, unless an editable install is part of setup).
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
text, and that each skill has name and description. Fix every failure, then do
the dry run described in SKILL.md phase 6.
