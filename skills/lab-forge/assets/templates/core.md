# Working rules (lab-forge, global)

These rules apply in every repo on this machine; the repo `AGENTS.md` adds facts. An explicit requirement
in the task (command, path, format) beats every rule: follow it, say which rule you set aside. Otherwise
core rules (C) always hold; profile and local rules may add or tighten them, never relax them.

## Core
C1. Never change files on the default branch (`main`, `master`). Start a branch first:
    `git switch -c <type>/<slug>`, type feat, fix, docs, chore or exp. A guard hook enforces it.
C2. Do only what was asked; touch no file the task does not need. An idea outside the ask is one line
    at the end. If the task needs another file, say why in one line first.
C3. These rules and the repo `AGENTS.md` are already in context: do not open them again. Read
    `.lab-forge/state.md` only to tune or upgrade.
C4. Never invent a package, flag or function: check the installed version and its docs or source.
    Cite `file:line` only after reading those lines in this session, after your last edit.
C5. Sound method is part of "complete"; D3 never trims it. Every fitted step (preprocessing,
    calibration, threshold, tuning, early stopping) uses rows no earlier step was fitted on, or CV
    inside the training rows. If the ask allows a weaker method, do the sound one and say so in one line.
C6. Test the acceptance criteria through real interfaces. Each test must fail when the behaviour it
    names breaks: assert the effect, never an echo of the input or config. A helper you write (split,
    threshold, metric) gets one hand-computed case. No edge-case matrices unless asked.
C7. On failure stop and say so: no silent fallback, no swallowed error, no unchecked "done". Never cut
    validation of untrusted input or error handling that guards data. A defect that breaks an explicit
    requirement is fixed now, not left for later.
C8. README: what it is and how to run it. Docstring: the contract and why, 1-2 lines. Comment: only a
    non-obvious why. No "This module provides", no bold, no emoji, no summary of what you just did.
    When a command, path or behaviour changes, update the docs that state it in the same change.
