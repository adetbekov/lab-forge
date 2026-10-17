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

1. **Detect before asking.** Every question the filesystem can answer is not asked.
   Ask only when the answer changes the result, as a real choice of 2-4 options
   (`references/interview.md`). Otherwise decide and state the assumption.
2. **Ceremony scales with the task.** Generated rules must let a small task be
   just done. Plans, specs, ADRs appear only for big or irreversible work.
3. **Markdown diet.** Every generated file has a line budget
   (`references/generation.md`). Link, never repeat. No document "just in case".
4. **One source of truth.** How to work lives once per machine in
   `~/.lab-forge/AGENTS.md`; the repo `AGENTS.md` holds only project facts.
   Every other entry point is an import, a managed copy or a pointer of at
   most 5 lines. Two hand-kept rule files = drift = bug.
5. **Rules enforced by tools beat rules in prose** - but only at the level the
   user is allowed to touch (levels 0-3, `references/environment.md`).
6. **Style from the pack, facts from the project.** Principles come from
   `style-pack/principles.md`; tools, commands, domain come from what is detected.
   Never import code or structure from the pack's origin projects.
7. **Skeleton before content.** Show the file list and the rules outline, get a
   yes, then write. After approval, edits are surgical.
8. **Ask first, degrade after.** Missing network, permissions or tools: stop and
   ask once, then use the fallback and say what was skipped.
9. **Bundled skills are installed as-is.** Copy the folder, restore the
   `SKILL.md` name, never rewrite the content.
10. **Leave a trail.** Record what was deployed in `.lab-forge/state.md` so tune mode
    knows what it owns and what the user wrote by hand.

## Modes

- **Deploy** - no `.lab-forge/state.md` found. Run phases 0-6.
- **Tune** - state file exists, the user asks to change the setup, or a phrase
  sets lasting behaviour ("always", "fewer tests", "пиши короче"). Read
  `references/tune.md`, apply without asking, and skip the rest.
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
user declines it.

**Phase 1 - Onboarding audit.** Run `scripts/audit_repo.py <project>` for each
project the user points at, then read `references/audit.md` and review by hand
what scripts cannot judge (code style, decomposition, experiment hygiene).
Output the short report from `assets/templates/audit-report.md`: problem ->
why it hurts -> proposed fix -> level needed. The user picks what to fix.

**Phase 2 - Interview.** Protocol in `references/interview.md`. Cover only open
branches: domain profile, stack, company restrictions, delivery channels (PR,
wiki, slides), language of docs and commits. No user available -> batch mode:
decide from evidence, list assumptions at the top of the skeleton.

**Phase 3 - Skeleton.** Pick the domain profile (`references/profiles/`), merge
with `style-pack/principles.md`, and present: file list with target paths and
budgets, the rules outline (invariants, task-size ladder, prohibitions), skills
and commands to create, bundled skills to install. Get explicit confirmation.

**Phase 4 - Generate.** Follow `references/generation.md` and the templates in
`assets/templates/`. Write the canonical file first, then pointers, skills,
commands, then guards if the level allows. Adapt every template to the detected
stack; delete sections that do not apply rather than leaving placeholders. If
Cursor or Copilot in VS Code is used, run `scripts/install_global.py repo <project>`:
they have no global rules file.

**Phase 5 - Install bundled skills.** Copy each folder from
`style-pack/bundled-skills/` into the skills directory the agent reads (see
`references/environment.md`) and rename `SKILL.md.bundle` back to `SKILL.md`
(the suffix only keeps them from loading as part of lab-forge). Do not edit
content. If a bundled skill needs network the machine lacks, keep it - these
skills carry their own fallbacks.

**Phase 6 - Verify and record.** Run the checks in `references/generation.md`
(budgets, links resolve, no duplicated rules, triggers present), then
`scripts/smoke.py` to prove each harness loads the rules. Do one dry run:
pick a small real task, show how the new rules route it. Write `.lab-forge/state.md`
from its template. Finish with a 5-line summary: what was created, where, how to
tune.

## What never to do

- Rewrite or delete user-written rule files. Merge into the canonical file with
  the user's consent, then turn the old file into a pointer.
- Generate ADR machinery, changelogs, roadmaps or status docs by default.
  Offer them only when the audit shows a real need.
- Add CI, hooks or dependencies at a level the user did not confirm.
- Put secrets, internal URLs or personal data into generated files.
