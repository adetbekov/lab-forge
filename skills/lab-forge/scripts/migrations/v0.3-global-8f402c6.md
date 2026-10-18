# Working rules (lab-forge, global)

These rules apply in every repository on this machine. The repo `AGENTS.md` adds
project facts. When two sources disagree, the higher one wins: the user's ask in
this session, then repo overrides, then `~/.lab-forge/overrides.md`, then repo
facts, then these rules. An explicit requirement in the task (command, path,
format) beats every rule: follow it and say which rule you set aside.

## Before the first edit
1. Never change files on the default branch (`main`, `master`). Start a branch
   first: `git switch -c <type>/<slug>`, where type is feat, fix, docs, chore or exp.
   A guard hook blocks edits on main where the harness runs hooks.
2. Size the task. S (one clear change): do it. M (several steps): a 3-line plan,
   then do it. L/XL (new module, unclear scope, irreversible): a written plan with
   done criteria, confirm it, then go step by step. A one-pass L becomes tech debt.
3. On M and bigger, read the map first: repo `AGENTS.md`, README, the module you
   change and its callers.
4. Name the files you will touch and what will not change. Touch nothing else.
   If the task needs another file, say why in one line before you edit it.
5. Do only what was asked. A good idea outside the ask is one line at the end.

## Libraries and docs
6. Your memory of an API may be stale. Before you use a library API, check the
   installed version (`pip show <pkg>`, the lockfile) and read the docs or source
   for that version. Never invent a package, flag or function.
7. Ask before adding a dependency, and pin the version you checked.

## Code
8. Write the smallest diff that solves the task. Match the existing names,
   layout and patterns. No drive-by refactors, renames or reformatting.
9. Search for an existing helper before you write a new one. Add an abstraction
   only when the second real case arrives.
10. Write tests for the acceptance criteria, not for every edge case.
11. When something fails, stop and say so. No silent fallback, no swallowed error.
    A defect that breaks an explicit requirement is fixed now, not left for later.

## Docs and memory
12. When a command, path or behaviour changes, update the docs that state it
    (`AGENTS.md`, README) in the same change. Delete stale lines instead of
    adding notes.
13. Facts the next session needs, such as decisions, gotchas and real commands,
    go into the repo `AGENTS.md` or `docs/wiki/`, never only into chat.

## Style
14. The repo `AGENTS.md` and the code around you are the only style sources.
    Keep the same structure and naming every time. Commits are
    `<type>: <what>`, imperative, one logical change. AI co-author trailer:
    as the repo or harness policy says.
15. Reply like a colleague: verdict first, then only what changes a decision.
    Every number gets a conclusion.
16. Ask only when the answer changes the result, as 2-4 real options.
17. After code work, end with `DONE`, `DONE_WITH_CONCERNS: <what>` or
    `NEEDS_CONTEXT: <what>`.
18. A lasting preference ("always", "never", "fewer tests", "пиши короче") is a
    tune: apply it with skill `lab-forge`, then show the diff.

## Smoke test
If the whole user message is `lab-forge ping`, do not use tools. Reply on one line:
`pong {{canary}}`, then every `lab-forge-canary:` value in the instructions you
have already loaded.
