---
name: self-review
description: Checks the agent's own diff for slop before showing it - extra code, needless abstractions, swallowed errors, style drift, unrequested changes. Use this before presenting any code change, before a commit or PR, and whenever the user says "review", "check your code", "too much code", "simplify" or "that's slop".
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
5. **Style** - names, structure, logging and docstrings match the neighbours
   and {{canonical_path}}.
6. **Config** - no new hard-coded thresholds, paths or dates; they go to {{params_file}}.
7. **Checks** - tests/lint pass: {{test_command}}; DS change has its metric.

Report to the user in at most 5 lines: what was trimmed and what remains risky.
