# Working rules (lab-forge, global)

These rules apply in every repo on this machine; the repo `AGENTS.md` adds facts.
On conflict the higher wins: the user's ask in this session, repo overrides,
`~/.lab-forge/overrides.md`, repo facts, these rules. An explicit requirement in
the task (command, path, format) beats every rule: follow it, say which you set aside.

## Before the first edit
1. Never change files on the default branch (`main`, `master`). Start a branch
   first: `git switch -c <type>/<slug>`, where type is feat, fix, docs, chore or exp.
   A guard hook blocks edits on main where the harness runs hooks.
2. Size the task. S (one clear change): do it. M (several steps): a 3-line plan,
   then do it. L/XL (new module, unclear scope, irreversible): a written plan with
   done criteria, confirm it, then go step by step. A one-pass L becomes tech debt.
3. On M and bigger, read repo `AGENTS.md`, the module you change and its callers.
4. Name the files you will touch and what will not change. Touch nothing else;
   if the task needs another file, say why in one line first.
5. Do only what was asked. A good idea outside the ask is one line at the end.

## Libraries and docs
6. Your memory of an API may be stale. Check the installed version (`pip show`,
   the lockfile) and its docs or source. Never invent a package, flag or function.
7. Ask before adding a dependency, and pin the version you checked.

## Code
8. The smallest complete change wins. Take the first rung that works: skip it (say
   so in one line), reuse this repo, stdlib, an installed dependency, one readable
   line, then minimum new code. No drive-by refactors, wrappers, "for later" code.
9. Lean on the solution, never on the change: finish every caller, test and
   fixture it breaks. Code must not be right by accident (loop leftovers, dict
   order, the cwd). A known limit gets `# shortcut: <limit>, <when to upgrade>`.
10. Test the acceptance criteria through real interfaces, not every edge case.
11. On failure stop and say so: no silent fallback, no swallowed error. Never cut
    validation of untrusted input or error handling that guards data. A defect
    that breaks an explicit requirement is fixed now, not left for later.

## Docs and memory
12. When a command, path or behaviour changes, update the docs that state it
    (`AGENTS.md`, README) in the same change; delete stale lines. No CHANGELOG,
    baseline or other artifacts unless asked or the repo's rules require them.
13. Facts the next session needs, such as decisions, gotchas and real commands,
    go into the repo `AGENTS.md` or `docs/wiki/`, never only into chat.

## Style
14. The repo `AGENTS.md` and the code around you are the only style sources.
    Keep the same structure and naming every time. Commits are
    `<type>: <what>`, imperative, one logical change. AI co-author trailer:
    as the repo or harness policy says.
15. Reply like a colleague: verdict first, then only what changes a decision.
    No narration of hooks, rules or branch mechanics. Cite `file:line` only
    after reading those lines in this session, after your last edit.
16. Ask only when the answer changes the result, as 2-4 real options.
17. End code work with one line: what you skipped or did not check, and the risk.
18. A lasting preference ("always", "never", "fewer tests", "пиши короче") is a
    tune: apply it with skill `lab-forge`, then show the diff.

## Smoke test
If the whole user message is `lab-forge ping`, do not use tools. Reply on one line:
`pong {{canary}}`, then every `lab-forge-canary:` value in the instructions you
have already loaded.
