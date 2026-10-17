# lab-forge v1 architecture

Status: design. Built from the stage 1 research and the v0.1 A/B round.
Every component lands in `main` only after it wins its A/B on `bench/`.

## Conclusions that shape the design

1. **Less always-on context.** Context files written by an LLM lowered success in
   5 of 8 setups and cost 20-23% more (arXiv:2602.11988). Files written by people
   gave +2.4 pp, p=0.21, so no significant gain either. Keep always-on text small
   and project-specific, and load the rest only when needed.
2. **Ceremony follows task size.** Spec tools that write 16 acceptance criteria
   for a one-line bug are the failure we avoid. Triage decides how much process a
   task gets.
3. **Portability lives in `AGENTS.md` and `SKILL.md`.** All five harnesses read
   both. Hooks are per-harness and partly preview, so a hook is only a bonus. It
   is never the only line of defence.
4. **A tool check beats a sentence.** If a guard can catch a pain, the rule is
   one line and the guard does the work.

## Layers

| Layer | Lives in | Holds | Changes when |
|---|---|---|---|
| Engine | `skills/lab-forge/` (this repo) | deploy, audit, tune, verify | lab-forge release |
| Global | `~/.lab-forge/` | principles, shared skills, routing agents, user overrides | install, `tune` (global) |
| Repo | project root | project facts, commands, pointers, project skills | deploy, `tune` (repo) |
| Session | the chat | one-off asks | never stored unless the user says so |

**Global, one source.** `~/.lab-forge/` holds `AGENTS.md` (≤60 lines),
`overrides.md` (≤20 lines), `skills/`, `agents/`, `hooks/guard.py`. Each
harness gets a thin adapter that points at it. On Windows a symlink is a copy
plus a checksum in `state.md`, and `verify_setup.py` reports drift.

**Repo, thin.** `AGENTS.md` (≤60 lines) has only facts the agent cannot guess:
real commands, paths, invariants, domain words. `CLAUDE.md` is one line,
`@AGENTS.md`. `.lab-forge/state.md` records ownership. `docs/wiki/` is
optional and read on demand.

### Where each harness reads it

✓ = confirmed by docs, ~ = community only. `scripts/smoke.py` turns a ~ into ✓ per machine;
results so far are in the open items.

| Harness | Global rules | Global skills | Repo rules | Subagents | Hooks |
|---|---|---|---|---|---|
| Claude Code | `~/.claude/CLAUDE.md` = `@~/.lab-forge/AGENTS.md` ✓ | `~/.claude/skills` → link ✓ | `CLAUDE.md` = `@AGENTS.md` ✓ | `~/.claude/agents/*.md` ✓ | `settings.json` Stop, PreToolUse ✓ |
| Codex | `~/.codex/AGENTS.md` → link ✓ | `~/.agents/skills` ✓ | `AGENTS.md` ✓ | `~/.codex/agents/*.toml` ✓ | `.codex/hooks.json` (trust) ✓ |
| Copilot VS Code | user instructions folder ~ | `~/.copilot/skills` ~ | `AGENTS.md`, `.github/copilot-instructions.md` pointer ✓ | `.github/agents/*.agent.md` ✓ | `.github/hooks/*.json` preview |
| Cursor | User Rules (UI, not a file) ~ | `~/.cursor/skills` ~ | `AGENTS.md` ✓ | `.cursor/agents` ✓ (model may be ignored) | `.cursor/hooks.json` ✓ |
| Antigravity | `~/.gemini/GEMINI.md` → link ~ | `~/.gemini/antigravity/skills` ~ | `AGENTS.md` ✓ | `.agents/agents/*.md` ✓ | `.agents/hooks.json` (IDE ~) |

Fallback when a global file is not read: the repo `AGENTS.md` gets a generated
`## Principles` block copied from global and marked as owned. `verify_setup.py`
keeps it in sync. Commands are always skills, because Antigravity drops workflows
on 2026-10-19.

## Components

| ID | Component | Kind | Always-on cost | Stage 3 issue |
|---|---|---|---|---|
| C1 | Principles: global `AGENTS.md` | rule | ≤60 lines | JEB-1879 |
| C2 | `triage`: quick / build / deep | skill + rule line | 1 line + description | JEB-1880 |
| C3 | Scope guard: branch, file allowlist, simplicity gate | hook + rule | 0 (hook) | JEB-1879 |
| C4 | `grill`: questions with real options | skill | description | JEB-1881 |
| C5 | Verifier: proof before "done" | subagent + Stop hook | 0 | JEB-1880 |
| C6 | Fresh docs: version pin, import check, docs lookup | guard + rule | 1 line | JEB-1879 |
| C7 | Memory: `docs/wiki/` + `handoff` | skill | description | JEB-1882 |
| C8 | Routing agents `quick` / `build` / `deep` | subagents | 0 | JEB-1880 |
| C9 | `tune` | engine mode | 0 | JEB-1881 |
| C10 | `self-review`: anti-slop check of own diff | skill | description | JEB-1878 |

`guard.py` is one stdlib script with subcommands (`branch`, `scope`, `imports`,
`stop`). Per-harness hook files are 3-line wrappers. If hooks are missing, the
same checks run from C5 and from `self-review`.

## Pain → mechanism → check → benchmark metric

"Tool check" means a machine can verify it without an LLM judge.

| # | Pain | Mechanism | Tool check | Bench metric |
|---|---|---|---|---|
| 1 | Too much code | C10 simplicity gate, C2 size budget per tier | `guard.py scope` diff LOC vs tier budget | diff LOC; blind bloat score |
| 2 | Touches code outside the task | C3 plan lists files, "what does not change" | `guard.py scope` files ⊄ plan | files out of scope |
| 3 | Works on `main` | C3 PreToolUse: no edits on default branch | `guard.py branch` exit 1 | commits to main = 0 |
| 4 | Extra tests and edge cases | C1 rule: tests only for acceptance criteria | test count / AC from diff | tests per AC |
| 5 | Wastes tokens, slow | C2 + C8 tier picks effort, budgets below | session token log | tokens and wall time per solved task |
| 6 | Stale docs in its head | C6 rule: look up the installed version first | `guard.py imports` vs installed metadata | API errors on new versions |
| 7 | Does what nobody asked | C2 build/deep need a confirmed plan; C3 | plan present before first edit | extra features found in review |
| 8 | Does not ask when the user knows more | C4 asks when the answer changes the result | question log | hidden-fact cases with a question |
| 9 | Huge scripts instead of reusable OOP | C1 reuse rule, C10 duplicate scan | duplicate class/function scan, file size | duplicates, max new file LOC |
| 10 | Fake or outdated tech | C6 pin and check existence | import resolves, package on index | non-existent imports = 0 |
| 11 | Robotic, no conclusions | C1 "conclusion first", C5 rejects bare "Done!" | first line of final message is a verdict | blind clarity score |
| 12 | Solves at once, tech debt grows | C2 deep = brainstorm → plan → execute | plan file present for deep | debt found after N iterations |
| 13 | Forgets between sessions | C7 handoff note + wiki, C9 stored overrides | handoff file updated at Stop | questions repeated in session 2 |
| 14 | One strong model for all | C8 fixed `model`/`effort` per tier, escalate once on FAIL | tier logged per task | cost per solved task, escalation rate |
| 15 | Rushes | C5 Iron Law: fresh test output before "done" | Stop hook runs project test command | false "done" rate |
| 16 | Misses the big picture | C2 build/deep start with a project map | map step present in transcript | integration errors |
| 17 | No doubt, no curiosity | C1 statuses `DONE_WITH_CONCERNS`, `NEEDS_CONTEXT` | status token in final message | concerns raised / planted issues |
| 18 | Style differs every time | C1 + repo glossary, one style source | rule lint: no duplicate rule text | style variance across repeats |
| 19 | Tuning in one phrase | C9 below | override line in diff after one phrase | tune cases applied from first phrase |

## Tune mode

1. **Trigger.** Automatic. Lasting intent ("always", "stop doing", "from now on",
   "fewer tests") is applied as tune with no question; `tune:` forces it.
2. **Scope.** If the user names a scope, use it. Otherwise: repo facts go to repo,
   behaviour and style go to global. A request for this session only is never
   stored.
3. **Write.** Add one imperative line. Global lines go to `~/.lab-forge/overrides.md`.
   Repo lines go to `## Overrides` in the repo `AGENTS.md`. If a new line
   contradicts an older one, replace the old line. Do not append both.
4. **Report.** Write first, then show the diff in ≤3 lines; `undo` reverts it.
   Log one line in `state.md`.
5. **Escalate.** If the bench shows an override is ignored, follow the order in
   `references/tune.md`: move it up, make it concrete, dedupe, check that the
   file is read, then offer a guard.

Precedence, highest first: explicit request in this session > repo overrides >
global overrides > repo facts > global principles. The v0.1 defect "generated
rule beat the user's explicit ask" is fixed by this order.

## Budgets

| Item | Lines | Tokens (≈ chars/4) |
|---|---|---|
| Global `AGENTS.md` + `overrides.md` | ≤80 | ≤1.5k |
| Repo `AGENTS.md` | ≤60 | ≤1k |
| Skill descriptions listed at start (≤10 skills) | 1 each | ≤1k |
| **Always-on total before the first task** | ≤150 | **≤3.5k** |
| A `SKILL.md` body, on demand | ≤120 | ≤2k |
| Hook failure message | ≤5 | ≤150 |
| quick-tier task overhead from lab-forge | — | ≤5k |

For comparison: superpowers starts at ~22k tokens (blog figure, unverified).
`verify_setup.py` enforces the line budgets, and the bench enforces the token
budgets. Any component that adds always-on text must pay for it with a metric
win.

## Out of v1

- Mandatory TDD: it conflicts with pain 4 and with exploratory ML work.
- Full spec-kit or Kiro ceremony. We keep only "what does not change" and
  `[NEEDS CLARIFICATION]`.
- Graph memory or MCP memory, until the JEB-1882 spike shows an A/B win.

## Open items

- Smoke (`scripts/smoke.py`), 2026-10-18: Claude Code ✓ (global and repo rules, guard hook
  blocks a commit on `main` even when asked). Gemini CLI loads `~/.gemini/GEMINI.md` ✓ and
  repo `AGENTS.md` only with `context.fileName` (set by the installer). Codex, Copilot,
  Cursor and Antigravity IDE still need a run on a logged-in machine.
- Model Routing Playbook (@donimas) not found. C8 rests on Claude and Codex docs
  and superpowers SDD.
