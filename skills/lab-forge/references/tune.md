# Tune mode

The user changes the deployed setup with one short phrase. Apply it at once,
then show what changed.

## 1. Detect
A phrase is a tune when it sets lasting behaviour: "always", "never", "stop
doing", "from now on", "fewer tests", "пиши короче", "больше не". `tune:` forces
it. A one-off ask about the current task ("make this function shorter") is not
a tune. If a phrase could be either, apply it to this task only and add one
line: "say `tune:` to keep it". Never ask.

## 2. Scope
- The user named one ("in this repo", "everywhere"): use it.
- Repo facts (paths, commands, data, domain words) go to `repo`.
- Behaviour and style go to `global`.
- "Only now" or "this session" is never stored.
- Level 0 (`environment.md` section 3), or the repo is on its default branch
  (the guard forbids edits there): nothing goes into the repo. `tune.py`
  stores repo lines in global overrides with a `[<repo>]` prefix.

## 3. Write one line
Turn the phrase into one imperative line with a concrete action:
"меньше тестов" becomes "Tests: only for acceptance criteria; no edge-case tests
unless asked." If an older override says the opposite, replace it. Never keep
both. Then run:

```
python scripts/tune.py add --scope global|repo "<line>" [--replace "<old line>"] --repo <project root>
```

It writes `~/.lab-forge/overrides.md` (global) or `## Overrides` in the repo
`AGENTS.md` (repo), logs to `state.md` and prints the diff.

## 4. Report
Reply with the diff only (3 lines max) and `undo` as the way back. Then follow the
new line from the next action on, in the same session. `undo` runs
`python scripts/tune.py undo --repo <project root>`.

## 5. Larger changes
- **New skill or command**: create it from templates and add one row to the skills table.
- **New project**: run deploy phases 0-1 for it only, and reuse the pack and answers.
- **Pack update**: re-merge only the affected sections.
Show the diff before writing, then run `scripts/verify_setup.py`.

## When the agent ignores an override
Fix the first cause found:
1. It is buried: move it up and make it one line with the reason.
2. It is vague: replace it with the concrete action.
3. Two files disagree: delete the duplicate.
4. The file is not read by this harness: re-run the test in `environment.md` section 5.
5. It needs enforcement: offer a guard, if the level allows.

## Drift check
When the user asks "is my setup still fine", compare state with disk. Report
hand edits (they win), budgets over the limit, broken links, and dead skills.
