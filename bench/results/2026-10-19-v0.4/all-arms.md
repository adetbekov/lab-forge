# lab-forge bench: v04 vs v03 vs bare

## Objective metrics

| Metric | v04 | v03 | bare |
|---|---|---|---|
| Solved, hidden checks | 21/24 | 24/24 | 24/24 |
| Claimed done but check fails (committed, not solved) | 3 | 0 | 0 |
| pytest red after step | 0 | 2 | 0 |
| Task tokens, k (all steps except deploy) | 11041.7 | 9662.9 | 8508.0 |
| Tokens per solved task, k | 525.8 | 402.6 | 354.5 |
| Cost per solved task, $ | 0.3 | 0.3 | 0.3 |
| Task time, min | 125.8 | 91.9 | 79.7 |
| Deploy tokens per project, k | 689.3 | 612.5 | — |
| Python lines changed (no AI files) | 2541 | 2714 | 2858 |
| All lines changed (no AI files) | 3289 | 3518 | 3389 |
| Largest new .py file, lines | 115 | 109 | 83 |
| Tests added | 99 | 103 | 129 |
| Files changed outside task scope | 2 | 2 | 4 |
| Coding steps committed straight to main | 0/24 | 0/24 | 24/24 |
| Coding steps left uncommitted | 0 | 0 | 0 |
| Ruff errors in changed files | 27 | 15 | 44 |
| Imports that do not resolve | 0 | 2 | 0 |
| Questions in coding-step replies | 0 | 0 | 0 |
| Files written during read-only question | 0 | 0 | 0 |
| Tune phrase applied in next session | 5/12 | 3/12 | 0/12 |
| Style stability across repeats (0-1) | 0.4 | 0.5 | 0.7 |
| Tool calls per solved task | 14.8 | 12.0 | 11.5 |
| Weighted tokens per solved task, k (cache read x0.1, write x1.25) | 121.0 | 96.4 | 81.2 |
| Bare `pytest` green after step | 24/24 | 22/22 | 14/24 |
| Mutants killed by the agent's tests | 18/24 | 15/24 | 7/15 |

## Spread over repeats (mean ± SE)

| Metric | v04 | v03 | bare |
|---|---|---|---|
| Tokens per solved task, k | 537.43 ± 72.66 (n=3) | 402.62 ± 32.58 (n=3) | 354.50 ± 32.95 (n=3) |
| Cost per solved task, $ | 0.35 ± 0.03 (n=3) | 0.28 ± 0.01 (n=3) | 0.25 ± 0.00 (n=3) |
| code sum of 30 | 27.30 ± 0.50 (n=3) | 26.65 ± 0.18 (n=3) | 25.66 ± 0.16 (n=3) |
| weighted code score, 1-5 | 4.59 ± 0.05 (n=3) | 4.47 ± 0.01 (n=3) | 4.34 ± 0.01 (n=3) |

## Blind review (72 verdicts, 1-5)

| Criterion | v04 | v03 | bare |
|---|---|---|---|
| clarity | 4.1 | 4.0 | 3.7 |
| code:bloat | 4.5 | 4.3 | 4.2 |
| code:correctness | 4.6 | 4.5 | 4.4 |
| code:methodology | 4.9 | 4.7 | 4.7 |
| code:optimality | 4.5 | 4.2 | 4.2 |
| code:practices | 4.3 | 4.3 | 3.7 |
| code:scope | 4.4 | 4.4 | 4.5 |
| code:success | 4.9 | 5.0 | 4.6 |
| code:tests | 4.4 | 4.2 | 4.1 |
| question:accuracy | 4.5 | 4.1 | 4.3 |
| question:completeness | 4.4 | 4.3 | 4.4 |
| question:conciseness | 3.8 | 3.8 | 3.6 |
| question:usefulness | 4.4 | 4.0 | 4.2 |
| questions | 4.7 | 4.6 | 4.5 |
| **code sum of 30** | 27.3 | 26.6 | 25.7 |
| **weighted code score, 1-5** | 4.6 | 4.5 | 4.3 |

## Winners by case and repeat

| case-repeat | steps…, overall |
|---|---|
| churn-r1-v03-bare | bare, bare, tie, bare |
| churn-r1-v04-bare | tie, tie, v04, tie |
| churn-r1-v04-v03 | v04, tie, v04, v04 |
| churn-r2-v03-bare | v03, bare, bare, bare |
| churn-r2-v04-bare | v04, v04, bare, v04 |
| churn-r2-v04-v03 | tie, v04, v04, v04 |
| churn-r3-v03-bare | v03, v03, tie, v03 |
| churn-r3-v04-bare | v04, v04, bare, v04 |
| churn-r3-v04-v03 | tie, v04, tie, v04 |
| encoders-r1-v03-bare | v03, v03, tie, v03 |
| encoders-r1-v04-bare | v04, tie, v04, v04 |
| encoders-r1-v04-v03 | tie, tie, v04, v04 |
| encoders-r2-v03-bare | tie, tie, tie, tie |
| encoders-r2-v04-bare | v04, v04, tie, v04 |
| encoders-r2-v04-v03 | v04, tie, v04, v04 |
| encoders-r3-v03-bare | tie, tie, tie, v03 |
| encoders-r3-v04-bare | tie, tie, tie, v04 |
| encoders-r3-v04-v03 | tie, v04, v04, v04 |
| optuna-r1-v03-bare | tie, v03, tie, v03 |
| optuna-r1-v04-bare | tie, v04, tie, v04 |
| optuna-r1-v04-v03 | v03, v03, tie, v03 |
| optuna-r2-v03-bare | v03, v03, tie, v03 |
| optuna-r2-v04-bare | bare, v04, tie, tie |
| optuna-r2-v04-v03 | tie, v04, tie, v04 |
| optuna-r3-v03-bare | v03, v03, bare, v03 |
| optuna-r3-v04-bare | tie, v04, bare, tie |
| optuna-r3-v04-v03 | v03, v04, v03, v03 |
| rparse-r1-v03-bare | v03, v03, v03, v03 |
| rparse-r1-v04-bare | v04, v04, tie, v04 |
| rparse-r1-v04-v03 | tie, v03, v03, v03 |
| rparse-r2-v03-bare | v03, tie, tie, v03 |
| rparse-r2-v04-bare | v04, v04, v04, v04 |
| rparse-r2-v04-v03 | tie, v04, v04, v04 |
| rparse-r3-v03-bare | v03, tie, v03, v03 |
| rparse-r3-v04-bare | v04, v04, v04, v04 |
| rparse-r3-v04-v03 | tie, tie, tie, tie |

X/Y order changed the winner in 41 of 144 calls; those count as ties.
