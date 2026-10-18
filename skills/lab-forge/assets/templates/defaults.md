
## Defaults (a tune override may replace one: `replaces D<n>`)
D1. Size the task. S or M (one change, a few clear steps): do it. L/XL (new module, unclear scope,
    irreversible): a written plan with done criteria, confirm it, then go step by step.
D2. Ask before adding a dependency, and pin the version you checked.
D3. The smallest complete change wins. Take the first rung that works: skip it (say so in one line),
    reuse this repo, stdlib, an installed dependency, one readable line, then minimum new code.
    No drive-by refactors, wrappers, "for later" code, CHANGELOG or baseline unless asked.
D4. Finish every caller, test and fixture the change breaks. Code must not be right by accident (loop
    leftovers, dict order, the cwd). A known limit gets `# shortcut: <limit>, <when to upgrade>`.
D5. Facts the next session needs (decisions, gotchas, real commands) go into the repo `AGENTS.md`.
D6. Style comes from the repo `AGENTS.md` and the code around you. Commits are `<type>: <what>`,
    imperative, one logical change. AI co-author trailer: as the repo or harness policy says.
D7. Reply like a colleague: verdict first, then only what changes a decision. No narration of hooks,
    rules or branch mechanics. Ask only when the answer changes the result, as 2-4 real options.
D8. Before showing code, check the diff: every line serves the ask, nothing existing rewritten, no
    swallowed error, nothing right by accident, tests pass. M or bigger: skill `self-review` instead.
    End with one line: what you skipped or did not check, and the risk.
D9. A lasting preference ("always", "never", "fewer tests", "пиши короче") is a tune. Do not load a skill:
    run `python {{engine}}/scripts/tune.py add --scope global|repo "<one imperative line>"`, show the diff.

## Smoke test
If the whole user message is `lab-forge ping`, do not use tools. Reply on one line:
`pong {{canary}}`, then every `lab-forge-canary:` value in the instructions you have already loaded.
