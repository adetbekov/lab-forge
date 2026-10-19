# Working rules (lab-forge, global)

For every repo; the repo `AGENTS.md` adds facts. An explicit task requirement (command, path, format)
beats any rule: follow it, name the rule set aside. Core rules (C) always hold; profile and local
rules may tighten them, never relax them.

## Core
C1. Never change files on the default branch (`main`, `master`): first `git switch -c <type>/<slug>`,
    type feat, fix, docs, chore or exp. A guard hook enforces it.
C2. Do only what was asked; touch no file the task does not need (if it needs one, say why). An idea
    outside the ask is one line at the end.
C3. These rules and the repo `AGENTS.md` are loaded: do not reopen them. `.lab-forge/state.md` is
    for tune and upgrade only.
C4. Never invent a package, flag or function: check the installed version and its source. Cite
    `file:line` only for lines read this session, after your last edit.
C5. Sound method is part of "complete"; D3 never trims it. Every fitted step (preprocessing,
    calibration, threshold, tuning, early stopping) uses rows no earlier step was fitted on, or CV
    inside the training rows. If the ask allows a weaker method, do the sound one and say so.
C6. Test acceptance criteria through real interfaces; each test fails when the behaviour it names
    breaks (assert the effect, not an echo of input or config). A helper you write (split,
    threshold, metric) gets one hand-computed case. No edge-case matrices unless asked.
C7. Before "done", run the task's entry point and check its output has every file, key, field and
    metric the task names, spelled as the task spells them. On failure stop and say so: no silent
    fallback, no swallowed error, no cut validation of untrusted input. A defect that breaks an
    explicit requirement is fixed now.
C8. README: what it is, how to run it. Docstring: the contract and why, 1-2 lines. Comment: only a
    non-obvious why. No bold, emoji or recap. A changed command, path or behaviour updates its docs.
