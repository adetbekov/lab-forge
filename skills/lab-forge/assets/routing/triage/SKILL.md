---
name: triage
description: Routes every task before work starts - picks the tier quick, build or deep, hands the task to that subagent, then has verifier prove it. Use at the start of any task that changes code or needs more than a quick lookup.
---

# triage

## 1. Pick the tier
A lasting preference ("from now on", "always", "never") is not a task. Store it now with
lab-forge tune (or the project's local rules file if lab-forge is not deployed), then reply.

Read the last 20 lines of `~/.lab-forge/routing.md`. If a past miss matches this kind of
task, start one tier higher.

| Tier | Task ladder | Looks like |
|---|---|---|
| `quick` | S | question, one clear change in 1-2 files, rename, config |
| `build` | M | a feature or fix over several files in known code, clear criteria |
| `deep` | L, XL | new project or module, design choice, cross-module, unknown cause |

Between two tiers, pick the lower one: one escalation costs less than overkill on every task.

## 2. Delegate
Hand the task to the tier's subagent verbatim, plus what you already know (files,
constraints, what must not change). Do not redo its work.

## 3. Verify
If code changed, give `verifier` the task and the worker's report.
- `PASS`: reply to the user with the result.
- `FAIL` or `ESCALATE`: run the task once more, one tier up (`quick` -> `build` -> `deep`),
  with the evidence. A second failure goes to the user as `DONE_WITH_CONCERNS` with
  the evidence. Never loop.

## 4. Log the miss
Each escalation adds one line to `~/.lab-forge/routing.md`, keep the last 50:
`- <YYYY-MM-DD> quick->build: <kind of task, 6 words> - <what failed>`

No subagents in this harness: do the work yourself at the tier's depth and say the tier
in the first line.
