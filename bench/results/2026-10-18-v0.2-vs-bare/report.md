# lab-forge bench: v02 vs bare

## First-round conclusions: 5/7 reproduced

| Conclusion | First round | This run | Holds |
|---|---|---|---|
| Less code with lab-forge (≤ −15%) | −30% | -56% | yes |
| Blind bloat score higher with lab-forge | 4.75 vs 3.6 | 5 vs 3 | yes |
| Explicit requirements: lab-forge not better | 3.75 vs 4.75 | 4.94 vs 5 | yes |
| Task tokens within ±15% | +3% | -8% | yes |
| Deploy costs 40-100k tokens per project | 48-90k | 65k | yes |
| Overall quality a tie (±2 of 30) | 25.0 vs 24.9 | 28.4 vs 25.0 | no |
| LLM project won by lab-forge | A won c2 | 1/2 repeats | no |

## Objective metrics

| Metric | v02 | bare |
|---|---|---|
| Solved, hidden checks | 16/16 | 16/16 |
| Claimed done but check fails (committed, not solved) | 0 | 0 |
| pytest red after step | 0 | 0 |
| Task tokens, k (all steps except deploy) | 1325.5 | 1447.2 |
| Tokens per solved task, k | 82.8 | 90.4 |
| Cost per solved task, $ | — | — |
| Task time, min | 58.0 | 119.0 |
| Deploy tokens per project, k | 65.2 | — |
| Python lines changed (no AI files) | 2406 | 5443 |
| All lines changed (no AI files) | 3009 | 6078 |
| Largest new .py file, lines | 134 | 188 |
| Tests added | 71 | 217 |
| Files changed outside task scope | 4 | 4 |
| Coding steps committed straight to main | 16/16 | 16/16 |
| Coding steps left uncommitted | 0 | 0 |
| Ruff errors in changed files | 0 | 0 |
| Questions in coding-step replies | 0 | 0 |
| Files written during read-only question | 0 | 0 |
| Tune phrase applied in next session | 8/8 | 8/8 |
| Style stability across repeats (0-1) | 0.6 | 0.7 |

## Blind review (8 verdicts, 1-5)

| Criterion | v02 | bare |
|---|---|---|
| clarity | 4.1 | 4 |
| code:bloat | 5 | 3 |
| code:correctness | 4.4 | 4.7 |
| code:optimality | 5 | 3.8 |
| code:practices | 4.2 | 4.4 |
| code:scope | 4.8 | 4.1 |
| code:success | 4.9 | 5 |
| question:accuracy | 5 | 4.6 |
| question:completeness | 4.9 | 5 |
| question:conciseness | 4 | 3.2 |
| question:usefulness | 4.9 | 4.9 |
| questions | 5 | 4.9 |
| **code sum of 30** | 28.4 | 25.0 |

## Winners by case and repeat

| case-repeat | steps…, overall |
|---|---|
| churn-r1 | v02, v02, tie, v02 |
| churn-r2 | bare, v02, v02, v02 |
| encoders-r1 | tie, bare, tie, bare |
| encoders-r2 | v02, v02, v02, v02 |
| optuna-r1 | tie, v02, v02, v02 |
| optuna-r2 | v02, v02, v02, v02 |
| rparse-r1 | bare, bare, tie, bare |
| rparse-r2 | v02, bare, tie, v02 |

## Run notes

- **Setup.** `v02` = `skills/lab-forge` after the JEB-1878 fixes (explicit request wins, no deferral in batch mode, bundles at user level, config format from installed parsers, baseline-only commits, configurable co-author trailer, seed mode). `bare` = the bare arm of [`2026-10-17-v0.1-vs-bare`](../2026-10-17-v0.1-vs-bare/report.md), reused as is: same seed, fixtures, prompts and model, so only the 40 `v02` sessions ran. Driver: agent mode, a fresh subagent per step. 8 new blind verdicts against the same bare workspaces.
- **Against v0.1** (same cases, same bare arm): hidden checks 16/16 vs 14/16; Python lines 2406 vs 3259 (−26%); tests added 71 vs 109; task tokens 1.33M vs 1.59M; deploy 65k vs 77k per project; AI-setup lines per repo 132-143 (seed) and 293-305 (deploy) vs ~1070-1160; blind code sum 28.4 vs 26.9; style stability 0.6 vs 0.4.
- **What the fixes did.** Seed mode prescribes no layout, so both churn repeats run `python -m churn.train` from the root (v0.1 broke it in one repeat). Configs are TOML via `tomllib`, never "YAML written as JSON". Per-run outputs are git-ignored and only a baseline is committed in all four new-project runs. No star-deck in any repo, so no ruff exclusions were needed.
- **Where bare still wins.** Blind success 4.94 vs 5: one churn P1 lacked a pytest config, so plain `pytest` (not `python -m pytest`) failed; the hidden check passed. Correctness 4.4 vs 4.7: the lean v02 code sometimes skips robustness bare adds (rparse-r1: an eval that aborts on one unparseable receipt). rparse split 1:1 again.
- **Not fixed by this round.** Commits straight to `main` 16/16 in both arms (pain 3, JEB-1879/1880 scope). `tune.py` writes repo overrides to `AGENTS.md` even when `CLAUDE.md` is canonical; every tune session fell back to a manual edit of `## Overrides`.
- **Limitations.** One more repeat-pair; differences of one point in one case are noise. The bare arm ran a day earlier. Reviewers are the same model family. A subagent's harness attribution policy leaked into one seed deploy's co-author rule.
