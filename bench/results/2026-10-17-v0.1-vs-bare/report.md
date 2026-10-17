# lab-forge bench: lab vs bare

## First-round conclusions: 5/7 reproduced

| Conclusion | First round | This run | Holds |
|---|---|---|---|
| Less code with lab-forge (≤ −15%) | −30% | -40% | yes |
| Blind bloat score higher with lab-forge | 4.75 vs 3.6 | 4.62 vs 3.38 | yes |
| Explicit requirements: lab-forge not better | 3.75 vs 4.75 | 4.50 vs 5 | yes |
| Task tokens within ±15% | +3% | +10% | yes |
| Deploy costs 40-100k tokens per project | 48-90k | 77k | yes |
| Overall quality a tie (±2 of 30) | 25.0 vs 24.9 | 26.9 vs 24.9 | no |
| LLM project won by lab-forge | A won c2 | 1/2 repeats | no |

## Objective metrics

| Metric | lab | bare |
|---|---|---|
| Solved, hidden checks | 14/16 | 16/16 |
| Claimed done but check fails (committed, not solved) | 2 | 0 |
| pytest red after step | 1 | 0 |
| Task tokens, k (all steps except deploy) | 1592.0 | 1447.2 |
| Tokens per solved task, k | 113.7 | 90.4 |
| Cost per solved task, $ | — | — |
| Task time, min | 86.4 | 119.0 |
| Deploy tokens per project, k | 77.4 | — |
| Python lines changed (no AI files) | 3259 | 5443 |
| All lines changed (no AI files) | 4634 | 6078 |
| Largest new .py file, lines | 196 | 188 |
| Tests added | 109 | 217 |
| Files changed outside task scope | 5 | 4 |
| Coding steps committed straight to main | 16/16 | 16/16 |
| Coding steps left uncommitted | 0 | 0 |
| Ruff errors in changed files | 0 | 0 |
| Questions in coding-step replies | 0 | 0 |
| Files written during read-only question | 0 | 0 |
| Tune phrase applied in next session | 8/8 | 8/8 |
| Style stability across repeats (0-1) | 0.4 | 0.7 |

## Blind review (8 verdicts, 1-5)

| Criterion | lab | bare |
|---|---|---|
| clarity | 3.6 | 4.1 |
| code:bloat | 4.6 | 3.4 |
| code:correctness | 4.3 | 4.4 |
| code:optimality | 4.6 | 3.9 |
| code:practices | 4.5 | 4.1 |
| code:scope | 4.4 | 4.1 |
| code:success | 4.5 | 5 |
| question:accuracy | 4.8 | 4.6 |
| question:completeness | 4.6 | 5 |
| question:conciseness | 3.6 | 3.8 |
| question:usefulness | 4.6 | 4.6 |
| questions | 4.4 | 4.9 |
| **code sum of 30** | 26.9 | 24.9 |

## Winners by case and repeat

| case-repeat | steps…, overall |
|---|---|
| churn-r1 | bare, bare, bare, bare |
| churn-r2 | tie, lab, lab, lab |
| encoders-r1 | lab, tie, tie, lab |
| encoders-r2 | lab, lab, lab, lab |
| optuna-r1 | bare, lab, lab, bare |
| optuna-r2 | bare, lab, bare, bare |
| rparse-r1 | lab, lab, tie, lab |
| rparse-r2 | bare, lab, bare, bare |

## Run notes

- **Setup.** `lab` = `skills/lab-forge` v0.1 (commit `b54d002`), `bare` = no skill. 4 cases x 2 arms x 2 repeats, 72 agent sessions plus 8 blind verdicts. Driver: agent mode (fresh subagent per step, same model in both arms), because headless `claude -p` was not authenticated on the runner. Raw rows: `runs.tsv`; verdicts and the X/Y key: `verdicts/`.
- **Cost.** 3.66M subagent tokens for the 72 sessions (deploy 0.62M of it) plus 0.54M for the verdicts, 235 session-minutes summed (up to 16 sessions ran in parallel). Tokens are the harness `subagent_tokens` figure, not billing.
- **What reproduced.** lab-forge writes much less code (−40% Python lines, half the tests) and wins the blind bloat score by over 1 point. It is still worse on explicit requirements: the same `src/` layout defect broke `python -m churn.train` in one churn repeat (P1 and P2), exactly as in the first round. Task tokens are close (+10%), and a deploy costs 77k tokens per project.
- **What did not.** On the open fixtures lab-forge's blind sum is about 2 points ahead (26.9 vs 24.9 of 30) rather than a tie. The LLM case split 1:1 between repeats instead of a clean lab-forge win. Repeats disagree often (churn r1: bare wins every step; r2: lab wins P2, P3 and overall), so single runs are noise; read the patterns.
- **New signals.** Both arms commit straight to `main` in 16/16 coding steps (pain 3 is untouched by v0.1). Neither asks questions in batch mode. The tune phrase stuck in the next session in 8/8 for both arms, so this case is too easy to separate them. lab-forge's style is less stable across repeats (0.4 vs 0.7): its generated rules differ per deploy (`src/` vs flat layout, TOML vs JSON params).
- **Deviations.** Three sessions were cut by a provider rate limit mid-step. Their workspaces were reset to the previous step's commit and the step was rerun. One rerun saw leftover git-ignored scratch files from the cut session and said it did not use them. Two hidden checks had bugs (message wording, missing `.git` in the check copy). They were fixed and all steps were rechecked with `bench.py recheck`.
- **Limitations.** Reviewers are the same model family. Replies can mention rule files, so blinding is partial. Agent mode simulates session start from a prompt; the `claude` driver is the faithful one and was only tested with a stub here.
