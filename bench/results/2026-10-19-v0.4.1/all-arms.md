# lab-forge bench: v041 vs v04 vs v03 vs bare

## Objective metrics

| Metric | v041 | v04 | v03 | bare |
|---|---|---|---|---|
| Solved, hidden checks | 24/24 | 21/24 | 24/24 | 24/24 |
| Claimed done but check fails (committed, not solved) | 0 | 3 | 0 | 0 |
| pytest red after step | 1 | 0 | 2 | 0 |
| Task tokens, k (all steps except deploy) | 10174.0 | 11041.7 | 10017.6 | 9681.2 |
| Tokens per solved task, k | 423.9 | 525.8 | 417.4 | 403.4 |
| Cost per solved task, $ | 0.3 | 0.3 | 0.3 | 0.3 |
| Task time, min | 52.8 | 125.8 | 91.9 | 79.7 |
| Deploy tokens per project, k | 796.7 | 762.7 | 670.9 | — |
| Python lines changed (no AI files) | 2583 | 2541 | 2714 | 2858 |
| All lines changed (no AI files) | 3105 | 3289 | 3518 | 3389 |
| Largest new .py file, lines | 132 | 115 | 109 | 83 |
| Tests added | 93 | 99 | 103 | 129 |
| Files changed outside task scope | 2 | 2 | 2 | 4 |
| Coding steps committed straight to main | 0/24 | 0/24 | 0/24 | 24/24 |
| Coding steps left uncommitted | 0 | 0 | 0 | 0 |
| Ruff errors in changed files | 15 | 27 | 15 | 44 |
| Imports that do not resolve | 0 | 0 | 2 | 0 |
| Questions in coding-step replies | 0 | 0 | 0 | 0 |
| Files written during read-only question | 0 | 0 | 0 | 0 |
| Tune phrase applied in next session | 4/12 | 5/12 | 3/12 | 0/12 |
| Style stability across repeats (0-1) | 0.6 | 0.4 | 0.5 | 0.7 |
| Tool calls per solved task | 12.4 | 14.8 | 12.4 | 12.9 |
| Weighted tokens per solved task, k (cache read x0.1, write x1.25) | 100.5 | 121.0 | 99.5 | 90.1 |
| Bare `pytest` green after step | 23/23 | 24/24 | 22/22 | 14/24 |
| Mutants killed by the agent's tests | 16/24 | 18/24 | 15/24 | 7/15 |

## Spread over repeats (mean ± SE)

| Metric | v041 | v04 | v03 | bare |
|---|---|---|---|---|
| Tokens per solved task, k | 423.92 ± 5.34 (n=3) | 537.43 ± 72.66 (n=3) | 417.40 ± 22.97 (n=3) | 403.38 ± 7.13 (n=3) |
| Cost per solved task, $ | 0.29 ± 0.01 (n=3) | 0.35 ± 0.03 (n=3) | 0.28 ± 0.01 (n=3) | 0.25 ± 0.00 (n=3) |
| code sum of 30 | 27.26 ± 0.08 (n=3) | 27.27 ± 0.70 (n=3) | 0.00 ± 0.00 (n=3) | 25.73 ± 0.59 (n=3) |
| weighted code score, 1-5 | 4.58 ± 0.03 (n=3) | 4.56 ± 0.11 (n=3) | — | 4.28 ± 0.04 (n=3) |

## Blind review (48 verdicts, 1-5)

| Criterion | v041 | v04 | v03 | bare |
|---|---|---|---|---|
| clarity | 3.8 | 4.0 | — | 3.7 |
| code:bloat | 4.5 | 4.6 | — | 4.2 |
| code:correctness | 4.6 | 4.7 | — | 4.4 |
| code:methodology | 4.8 | 4.8 | — | 4.6 |
| code:optimality | 4.4 | 4.5 | — | 4.2 |
| code:practices | 4.3 | 4.1 | — | 3.8 |
| code:scope | 4.4 | 4.6 | — | 4.6 |
| code:success | 4.9 | 4.9 | — | 4.6 |
| code:tests | 4.4 | 4.3 | — | 3.9 |
| question:accuracy | 4.3 | 4.5 | — | 4.3 |
| question:completeness | 4.4 | 4.5 | — | 4.5 |
| question:conciseness | 3.8 | 3.9 | — | 3.8 |
| question:usefulness | 4.2 | 4.2 | — | 4 |
| questions | 4.6 | 4.6 | — | 4.5 |
| **code sum of 30** | 27.3 | 27.3 | 0 | 25.7 |
| **weighted code score, 1-5** | 4.6 | 4.6 | — | 4.3 |

## Winners by case and repeat

| case-repeat | steps…, overall |
|---|---|
| churn-r1-v041-bare | bare, bare, v041, bare |
| churn-r1-v041-v04 | tie, v041, v04, tie |
| churn-r2-v041-bare | v041, v041, bare, v041 |
| churn-r2-v041-v04 | tie, v04, tie, v04 |
| churn-r3-v041-bare | v041, v041, tie, v041 |
| churn-r3-v041-v04 | tie, v041, tie, v041 |
| encoders-r1-v041-bare | v041, v041, tie, v041 |
| encoders-r1-v041-v04 | v041, v041, v04, v041 |
| encoders-r2-v041-bare | v041, v041, tie, v041 |
| encoders-r2-v041-v04 | v04, tie, tie, v04 |
| encoders-r3-v041-bare | tie, tie, v041, v041 |
| encoders-r3-v041-v04 | tie, v041, v04, tie |
| optuna-r1-v041-bare | bare, tie, bare, bare |
| optuna-r1-v041-v04 | tie, v04, tie, v04 |
| optuna-r2-v041-bare | tie, v041, v041, v041 |
| optuna-r2-v041-v04 | tie, tie, tie, v041 |
| optuna-r3-v041-bare | v041, v041, v041, v041 |
| optuna-r3-v041-v04 | v041, tie, v041, v041 |
| rparse-r1-v041-bare | v041, v041, tie, v041 |
| rparse-r1-v041-v04 | v041, v041, tie, v041 |
| rparse-r2-v041-bare | v041, v041, bare, v041 |
| rparse-r2-v041-v04 | tie, v04, v04, v04 |
| rparse-r3-v041-bare | v041, v041, v041, v041 |
| rparse-r3-v041-v04 | tie, v041, tie, v041 |

X/Y order changed the winner in 23 of 96 calls; those count as ties.
