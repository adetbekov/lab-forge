---
name: lab-forge
description: Deploys and maintains an AI working environment for a data scientist or ML/AI engineer inside any IDE agent (GitHub Copilot, Claude Code, Cursor, Codex, corporate wrappers). Onboards on the machine, audits existing projects, finds problems and proposes fixes, interviews only for what it could not detect, then generates one canonical rules file plus thin pointers, skills, prompt commands and optional guards in the author's style, and installs bundled skills as-is. Use this skill whenever the user wants to set up, bootstrap, onboard, standardize, audit or fix their AI coding setup, instructions, skills, commands or agents; complains that the agent writes slop, too much code or not in their style; moves to a new machine, VDI or project; or says "lab-forge", "tune lab-forge", "forge", "разверни систему", "настрой агента под меня". Also use it to adjust an already deployed setup (tune mode), including one-phrase preferences like "always ...", "never ...", "fewer tests", "пиши короче", "tune: ...".
---

# lab-forge - AI work environment for DS/ML engineers

lab-forge is an engine plus a style pack. The engine is universal: onboard, audit,
interview, generate, tune. The style pack (`style-pack/`) holds the author's
principles and ready skills; swap the pack and the engine serves someone else.
Company specifics (tools, restrictions, network) are never baked in - they come
from the environment and from the user at run time.

It runs once to deploy, then the generated system lives on its own. Later runs
are tune mode: surgical edits, never a rebuild.

## Fixed principles

1. **The user's explicit request wins.** A command, path, format or behaviour the
   user named beats every generated rule and every style-pack default. Never
   generate a rule that a stated requirement would contradict (a layout that
   breaks the stated run command, a config format the env cannot read).
2. **Detect before asking.** Every question the filesystem can answer is not asked.
   Ask only when the answer changes the result, as a real choice of 2-4 options
   (`references/interview.md`). Otherwise decide and state the assumption.
3. **Ceremony scales with the task.** Generated rules must let a small task be
   just done. Plans, specs, ADRs appear only for big or irreversible work.
4. **Markdown diet.** Every generated file has a line budget
   (`references/generation.md`). Link, never repeat. No document "just in case".
5. **One source of truth.** How to work lives once per machine in
   `~/.lab-forge/AGENTS.md` (core plus defaults); the repo `AGENTS.md` holds
   project facts and the profile block, copied verbatim.
   Every other entry point is an import, a managed copy or a pointer of at
   most 5 lines. Two hand-kept rule files = drift = bug.
6. **Rules enforced by tools beat rules in prose** - but only at the level the
   user is allowed to touch (levels 0-3, `references/environment.md`).
7. **Style from the pack, facts from the project.** Principles come from
   `style-pack/principles.md`; tools, commands, domain come from what is detected.
   Never import code or structure from the pack's origin projects.
8. **Skeleton before content.** Show the file list and the rules outline, get a
   yes, then write. After approval, edits are surgical.
9. **Ask first, degrade after.** Missing network, permissions or tools: stop and
   ask once, then use the fallback and say what was skipped. In batch mode (no
   user) there is no "ask": decide, do it, report the assumption. An explicit
   requirement is never deferred.
10. **Bundled skills are installed as-is, once, at user level.** They go to the
    user skills folder shared by all repos, never into a repo unless asked.
11. **Leave a trail.** Record what was deployed in `.lab-forge/state.md` so tune mode
    knows what it owns and what the user wrote by hand.

## Modes

- **Seed** - the project is empty or has no code yet. Phase 0, then write the repo
  `AGENTS.md` from `rules.md` with only the facts that exist (stated commands,
  languages) and the profile's repo block copied verbatim, a minimal
  `pyproject.toml` for Python (`references/generation.md` section 3), and the
  skills `self-review` and `grill`. No audit, no layout, no params file, no
  bundles: the first real task decides structure. Then phase 6. Upgrade to
  deploy later on request.
- **Deploy** - no `.lab-forge/state.md` found and the project has code. Run phases 0-6.
- **Upgrade** - `.lab-forge/state.md` or `~/.lab-forge/state.md` exists and its
  `- Version:` is older than the engine's (`VERSION` in `scripts/install_global.py`)
  or missing (v0.1-v0.3). Run `scripts/upgrade.py --repo <project>`: a dry run that
  prints the diff. Show it, apply with `--apply` after a yes (it backs up first),
  report any `.rej` conflict as is, then continue with what the user asked.
- **Tune** - state file exists and is current, the user asks to change the setup, or a phrase
  sets lasting behaviour ("always", "fewer tests", "пиши короче"). One line:
  run `scripts/tune.py add` at once (global rule D9), without reading further.
  Read `references/tune.md` only for a new skill, project or pack update.
- **Audit only** - user wants a review without changes. Phases 0-1, report, stop.

## Deploy workflow

**Phase 0 - Environment.** Run `scripts/detect_env.py <root>` (stdlib only,
works on Windows). Read `references/environment.md` to interpret it: which agent
and which folders it reads, OS, git host, network, and the ownership level (0-3)
for each project. Confirm the level with the user; never assume write rights.
If `~/.lab-forge/state.md` is missing, install the global layer once for the
harnesses in use: `scripts/install_global.py install --harness <list>`
(`references/generation.md` section 8). It writes only user-level files, so
repo level 0 does not block it; skip the guard hook with `--no-hooks` if the
user declines it. The install prints a one-line offer of the decision hooks (`--decide`); repeat it to the user,
and offer it again when they complain the agent claims "done" too early or skips the right skill. Enable it only on
request, with their endpoint and model; they add the key themselves (env var or `~/.lab-forge/decide.key`), never
in chat. Say where the data goes: the install prints the host.

**Phase 1 - Onboarding audit.** Run `scripts/audit_repo.py <project>` for each
project the user points at, then read `references/audit.md` and review by hand
what scripts cannot judge (code style, decomposition, experiment hygiene).
Output the short report from `assets/templates/audit-report.md`: problem ->
why it hurts -> proposed fix -> level needed. The user picks what to fix.

**Phase 2 - Interview.** Protocol in `references/interview.md`. Cover only open
branches: domain profile, stack, company restrictions, delivery channels (PR,
wiki, slides), language of docs and commits. No user available -> batch mode:
decide from evidence, list assumptions at the top of the skeleton.

**Phase 3 - Skeleton.** Pick the domain profile (`references/profiles/`): its
repo block goes into the repo `AGENTS.md` verbatim, never paraphrased. Merge the
rest with `style-pack/principles.md`, and present: file list with target paths and
budgets, the rules outline (invariants, task-size ladder, prohibitions), skills
and commands to create, bundled skills to install. Get explicit confirmation.

**Phase 4 - Generate.** Follow `references/generation.md` and the templates in
`assets/templates/`. Write the canonical file first, then pointers, skills,
commands, then guards if the level allows. Adapt every template to the detected
stack; delete sections that do not apply rather than leaving placeholders. If
Cursor or Copilot in VS Code is used, run `scripts/install_global.py repo <project>`:
they have no global rules file.

**Phase 5 - Install bundled skills.** Skip if the user skills folder
(`references/environment.md` section 1, for example `~/.claude/skills/`) already
has them: they are installed once per machine. Otherwise copy each folder from
`style-pack/bundled-skills/` there and rename `SKILL.md.bundle` back to
`SKILL.md` (the suffix only keeps them from loading as part of lab-forge). Do
not edit content. Into a repo only when the user asks.

**Phase 6 - Verify and record.** Run the checks in `references/generation.md`
(budgets, links resolve, no duplicated rules, profile block sha), then
`scripts/smoke.py` to prove each harness loads the rules. Dry run: run every command the user stated (entry point, tests, lint)
from the project root exactly as written - no install step, no `PYTHONPATH` - plus a bare `pytest`.
A failure is a setup bug: fix the rules, not the command. No code yet (seed):
put those commands into the rules as invariants ("must run from the root as
written"). Write `.lab-forge/state.md`
from its template. Finish with a 5-line summary: what was created, where, how to
tune.

## What never to do

- Rewrite or delete user-written rule files. Merge into the canonical file with
  the user's consent, then turn the old file into a pointer.
- Generate ADR machinery, changelogs, roadmaps or status docs by default.
  Offer them only when the audit shows a real need.
- Add CI, hooks or dependencies at a level the user did not confirm.
- Put secrets, internal URLs or personal data into generated files.
