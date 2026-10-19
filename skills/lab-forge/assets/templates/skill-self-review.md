---
name: self-review
description: Checks your own diff for slop before showing it: extra code, needless abstractions, swallowed errors, style drift, unrequested changes. Use before presenting an M or bigger change or a PR, and when the user says "review", "too much code", "simplify" or "that's slop".
---

# self-review

Read the diff as a strict senior reviewer who has to maintain it. For each item,
fix it, do not just report it.

1. **Scope** - every changed line serves the task. Revert drive-by edits,
   renames, reformatting.
2. **Size** - could this be fewer lines by reusing what exists? Search the repo
   for an existing helper before keeping a new one.
3. **Abstraction** - new base class, factory, config option or wrapper with a
   single user? Inline it.
4. **Errors** - no bare/swallowed exceptions, no silent defaults, no retries or
   sleeps hiding a problem.
5. **By accident** - code that works only because of loop leftovers, dict order,
   the cwd or the test data. Make it explicit or mark `# shortcut: <limit>`.
6. **Style** - names, structure, logging and docstrings match the neighbours
   and {{canonical_path}}.
7. **Config** - no new hard-coded thresholds, paths or dates; they go to {{params_file}}.
8. **Tests bite** - each new test fails if the behaviour it names breaks (assert the effect,
   not an echo of config); tests/lint pass: {{test_command}}; DS change has its metric.
9. **Docs** - README, docstrings and comments carry none of these signs of AI text:
   inflated significance ("pivotal", "serves as"), "not just X but Y", bold for emphasis,
   bullet lists with bold headers, emoji, a closing summary of what was done.

Report to the user in at most 5 lines: what was trimmed and what remains risky.
