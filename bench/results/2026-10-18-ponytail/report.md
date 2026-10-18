# Ponytail vs lab-forge v0.2 vs bare (JEB-1895), 2026-10-18

**Verdict: keep lab-forge; do not switch to ponytail.** Ponytail alone is the leanest and
cheapest arm and ties lab-forge on the blind code sum (27.7 vs 28.1 of 30), but it loses
3 of 4 head-to-head cases to lab-forge. Both beat the bare agent by about 2.5 points. Its
weak spot is engineering practice (3.8 vs 4.5): fragile shortcuts and thin tests. It does
nothing about pain 3 (8/8 coding steps on `main`) and lost one tune. Worth borrowing:
the "laziness ladder" and the closing "what I skipped" line. That is a candidate for the
next A/B, not a change in this round.

## Arms

| Arm | What runs | Deploy step |
|---|---|---|
| `v02` | `skills/lab-forge` on `main` (`7a02f01`): global layer, guard hook, repo `AGENTS.md` | P0, ~90k tokens per project |
| `pony` | [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) `v5.3.2` (`16352ac`) as a Claude Code plugin: the real `hooks/ponytail-activate.js` SessionStart output (rules, `full` level, plus its codebase map) injected into every session, its 6 skills in `HOME/.claude/skills` | none |
| `bare` | no setup | none |

## Result

| | v02 | pony | bare |
|---|---|---|---|
| Hidden checks solved | 8/8 | 8/8 | 8/8 |
| Task tokens, k (no deploy) | 839 | **620** | 676 |
| Deploy tokens, k (4 projects) | 361 | 0 | 0 |
| Task time, min | 49.8 | **35.2** | 54.5 |
| All lines changed | 1071 | **793** | 2373 |
| Tests added | 23 | 23 | 74 |
| Files outside task scope | 2 | **0** | 2 |
| Coding steps committed to `main` | **0/8** | 8/8 | 8/8 |
| Tune applied next session | 4/4 | 3/4 | 4/4 |
| Blind code sum of 30 (all verdicts) | **28.1** | 27.7 | 25.4 |
| Blind practices | 4.5 | 3.8 | 4.6 |
| Blind bloat | 4.7 | **5.0** | 3.1 |
| Blind scope | 4.4 | **5.0** | 4.2 |

Head to head (overall winner per case, blind):

| Pair | churn | encoders | optuna | rparse | Score | Code sum |
|---|---|---|---|---|---|---|
| pony vs v02 | v02 | pony | v02 | v02 | 1:3 | 27.8 vs 28.1 |
| pony vs bare | bare | pony | pony | bare | 2:2 | 27.6 vs 25.2 |
| v02 vs bare | bare | v02 | v02 | v02 | 3:1 | 28.0 vs 25.5 |

Details: [`pony-v02.md`](pony-v02.md), [`pony-bare.md`](pony-bare.md), [`v02-bare.md`](v02-bare.md),
[`all-arms.md`](all-arms.md), verdicts in `verdicts/<pair>/`.

## Why

1. **Ponytail does what it promises on size.** It wrote 26% fewer lines than v02 and 67% fewer
   than bare, with no edits outside the task (v02 and bare both added unrequested CHANGELOG
   entries in `encoders`). It used 26% fewer task tokens than v02 and needs no deploy.
2. **It loses where the lean path cuts a corner.** In each case the reviewers named one concrete problem:
   - churn: the F1 threshold uses the leftover loop variable `pipe`, so it is correct only
     because gradient boosting is last in the dict;
   - optuna: the warning test mocks `_logger.warning` instead of the repo's `caplog`
     pattern, and the negative test cannot fail;
   - rparse: almost no reply validation, and the eval aborts on the first bad receipt.
   v02 got the same "lean" scores (bloat 4.7, optimality 4.8) without these defects. Its
   repo `AGENTS.md` invariants and `self-review` skill seem to be what catches them.
3. **It covers one pain of the 19.** Ponytail is a coding-style rule set. Branch guard, tune
   with undo, project facts across sessions and audit are out of its scope. In one tune
   session (optuna) the "smallest change" rule led the agent to keep "from now on" for
   the current session only, so P3 came back in English.
4. **v02 costs more tokens than in the first v0.2 run** (+24% vs bare here, −8% on
   2026-10-18-v0.2-vs-bare). The global layer is new since then, and in agent-driven mode
   every guard-hook call is a simulated shell command. Recheck this in headless mode before
   reading it as a regression.

## Setup

- Bench on `main` (`7a02f01`) plus this round's driver change: an arm value `plugin:DIR`
  loads a Claude Code plugin (headless: `--plugin-dir`; agent mode: the plugin's SessionStart
  output goes into the prompt, and its skills go to `HOME/.claude/skills`). No P0 for such arms.
  `pack` and `report` take `--pair A,B` for 3+ arms.
- Cases `churn`, `encoders`, `optuna`, `rparse`, 1 repeat, seed 1877, all three arms fresh
  (the v0.2-vs-bare workspaces were gone). Agent-driven mode: 52 sessions, a fresh Opus
  subagent per step. 12 blind verdicts, every pair of arms on every case, judged by Opus.
- Only the ponytail statusline nudge was cut from the hook output. Ponytail's other hooks
  (UserPromptSubmit mode tracker, SubagentStart, task-board ledger) only handle `/ponytail`
  commands, subagents and stats, so they were not simulated.

## Limitations

- One repeat. Differences of one case are noise; the 2.5-point gap to bare is the only firm result.
- Reviewers and agents are the same model family. Replies that cite `AGENTS.md` or "ponytail
  mode" partly reveal the arm to the reviewer.
- v02 vs pony P3 accuracy (4.1 vs 4.2) is dragged down by rparse answers that cite lines past
  the end of `eval.py`, which also happened in the model-mix round. That is a separate defect.
- Not tested: ponytail stacked on top of lab-forge, the `lite`/`ultra` levels, other harnesses.
