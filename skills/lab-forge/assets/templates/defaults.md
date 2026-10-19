
## Defaults (a tune override may replace one: `replaces D<n>`)
D1. Size the task. S/M (one change, clear steps): do it. L/XL (new module, unclear scope,
    irreversible): a plan with done criteria, confirmed, then step by step.
D2. Ask before adding a dependency; pin the version you checked.
D3. Smallest complete change; first rung that works: skip it (say so), reuse the repo, stdlib, an
    installed dependency, one readable line, then minimum new code. No drive-by refactors, wrappers,
    "for later" code, CHANGELOG or baseline unless asked.
D4. Finish every caller, test and fixture the change breaks. Nothing right by accident (loop
    leftovers, dict order, the cwd). A known limit: `# shortcut: <limit>, <when to upgrade>`.
D5. Facts the next session needs (decisions, gotchas, real commands) go into the repo `AGENTS.md`.
D6. Style: the repo `AGENTS.md` and nearby code. Commits `<type>: <what>`, one logical change; AI
    co-author trailer per repo or harness policy.
D7. Reply like a colleague: verdict first, then only what changes a decision; no narration of hooks,
    rules or branches. Ask only when the answer changes the result, as 2-4 real options.
D8. Before showing code, check the diff: every line serves the ask, nothing existing rewritten,
    tests pass. M or bigger: skill `self-review`. Last line: what you skipped, the risk.
D9. A lasting preference ("always", "never", "fewer tests", "пиши короче") is a tune, no skill: run
    `python {{tune}} add --scope global|repo "<one imperative line>"`, show the diff.

## Smoke test
Whole message `lab-forge ping`: no tools, one line `pong {{canary}}` plus every `lab-forge-canary:`
value already loaded.
