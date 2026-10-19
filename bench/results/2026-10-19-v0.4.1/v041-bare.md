# lab-forge bench: v041 vs bare

## First-round conclusions: 4/7 reproduced

| Conclusion | First round | This run | Holds |
|---|---|---|---|
| Less code with lab-forge (≤ −15%) | −30% | -10% | no |
| Blind bloat score higher with lab-forge | 4.75 vs 3.6 | 4.46 vs 4.19 | yes |
| Explicit requirements: lab-forge not better | 3.75 vs 4.75 | 4.92 vs 4.56 | no |
| Task tokens within ±15% | +3% | +5% | yes |
| Deploy costs 40-100k tokens per project | 48-90k | 797k | no |
| Overall quality a tie (±2 of 30) | 25.0 vs 24.9 | 27.1 vs 25.7 | yes |
| LLM project won by lab-forge | A won c2 | 6/6 repeats | yes |

## Objective metrics

| Metric | v041 | bare |
|---|---|---|
| Solved, hidden checks | 24/24 | 24/24 |
| Claimed done but check fails (committed, not solved) | 0 | 0 |
| pytest red after step | 1 | 0 |
| Task tokens, k (all steps except deploy) | 10174.0 | 9681.2 |
| Tokens per solved task, k | 423.9 | 403.4 |
| Cost per solved task, $ | 0.3 | 0.3 |
| Task time, min | 52.8 | 79.7 |
| Deploy tokens per project, k | 796.7 | — |
| Python lines changed (no AI files) | 2583 | 2858 |
| All lines changed (no AI files) | 3105 | 3389 |
| Largest new .py file, lines | 132 | 83 |
| Tests added | 93 | 129 |
| Files changed outside task scope | 2 | 4 |
| Coding steps committed straight to main | 0/24 | 24/24 |
| Coding steps left uncommitted | 0 | 0 |
| Ruff errors in changed files | 15 | 44 |
| Imports that do not resolve | 0 | 0 |
| Questions in coding-step replies | 0 | 0 |
| Files written during read-only question | 0 | 0 |
| Tune phrase applied in next session | 4/12 | 0/12 |
| Style stability across repeats (0-1) | 0.6 | 0.7 |
| Tool calls per solved task | 12.4 | 12.9 |
| Weighted tokens per solved task, k (cache read x0.1, write x1.25) | 100.5 | 90.1 |
| Bare `pytest` green after step | 23/23 | 14/24 |
| Mutants killed by the agent's tests | 16/24 | 7/15 |

## Spread over repeats (mean ± SE)

| Metric | v041 | bare |
|---|---|---|
| Tokens per solved task, k | 423.92 ± 5.34 (n=3) | 403.38 ± 7.13 (n=3) |
| Cost per solved task, $ | 0.29 ± 0.01 (n=3) | 0.25 ± 0.00 (n=3) |
| code sum of 30 | 27.06 ± 0.12 (n=3) | 25.73 ± 0.59 (n=3) |
| weighted code score, 1-5 | 4.55 ± 0.04 (n=3) | 4.28 ± 0.04 (n=3) |

## Blind review (24 verdicts, 1-5)

| Criterion | v041 | bare |
|---|---|---|
| clarity | 3.8 | 3.7 |
| code:bloat | 4.5 | 4.2 |
| code:correctness | 4.6 | 4.4 |
| code:methodology | 4.8 | 4.6 |
| code:optimality | 4.4 | 4.2 |
| code:practices | 4.4 | 3.8 |
| code:scope | 4.3 | 4.6 |
| code:success | 4.9 | 4.6 |
| code:tests | 4.4 | 3.9 |
| question:accuracy | 4.4 | 4.3 |
| question:completeness | 4.5 | 4.5 |
| question:conciseness | 3.8 | 3.8 |
| question:usefulness | 4.3 | 4 |
| questions | 4.6 | 4.5 |
| **code sum of 30** | 27.1 | 25.7 |
| **weighted code score, 1-5** | 4.6 | 4.3 |

## Winners by case and repeat

| case-repeat | steps…, overall |
|---|---|
| churn-r1-v041-bare | bare, bare, v041, bare |
| churn-r2-v041-bare | v041, v041, bare, v041 |
| churn-r3-v041-bare | v041, v041, tie, v041 |
| encoders-r1-v041-bare | v041, v041, tie, v041 |
| encoders-r2-v041-bare | v041, v041, tie, v041 |
| encoders-r3-v041-bare | tie, tie, v041, v041 |
| optuna-r1-v041-bare | bare, tie, bare, bare |
| optuna-r2-v041-bare | tie, v041, v041, v041 |
| optuna-r3-v041-bare | v041, v041, v041, v041 |
| rparse-r1-v041-bare | v041, v041, tie, v041 |
| rparse-r2-v041-bare | v041, v041, bare, v041 |
| rparse-r3-v041-bare | v041, v041, v041, v041 |

X/Y order changed the winner in 5 of 48 calls; those count as ties.
