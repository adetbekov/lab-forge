# lab-forge bench: v02 vs pony vs bare

## Objective metrics

| Metric | v02 | pony | bare |
|---|---|---|---|
| Solved, hidden checks | 8/8 | 8/8 | 8/8 |
| Claimed done but check fails (committed, not solved) | 0 | 0 | 0 |
| pytest red after step | 0 | 0 | 0 |
| Task tokens, k (all steps except deploy) | 839.1 | 620.0 | 675.5 |
| Tokens per solved task, k | 104.9 | 77.5 | 84.4 |
| Cost per solved task, $ | — | — | — |
| Task time, min | 49.8 | 35.2 | 54.5 |
| Deploy tokens per project, k | 90.2 | — | — |
| Python lines changed (no AI files) | 923 | 775 | 2048 |
| All lines changed (no AI files) | 1071 | 793 | 2373 |
| Largest new .py file, lines | 105 | 110 | 194 |
| Tests added | 23 | 23 | 74 |
| Files changed outside task scope | 2 | 0 | 2 |
| Coding steps committed straight to main | 0/8 | 8/8 | 8/8 |
| Coding steps left uncommitted | 0 | 0 | 0 |
| Ruff errors in changed files | 0 | 0 | 0 |
| Imports that do not resolve | 0 | 0 | 0 |
| Questions in coding-step replies | 0 | 0 | 0 |
| Files written during read-only question | 0 | 0 | 0 |
| Tune phrase applied in next session | 4/4 | 3/4 | 4/4 |
| Style stability across repeats (0-1) | — | — | — |

## Blind review (12 verdicts, 1-5)

| Criterion | v02 | pony | bare |
|---|---|---|---|
| clarity | 4 | 4.1 | 4 |
| code:bloat | 4.7 | 5 | 3.1 |
| code:correctness | 4.6 | 4.4 | 4.6 |
| code:optimality | 4.8 | 4.6 | 3.8 |
| code:practices | 4.5 | 3.8 | 4.6 |
| code:scope | 4.4 | 5 | 4.2 |
| code:success | 5 | 4.9 | 5 |
| question:accuracy | 4.1 | 4.2 | 5 |
| question:completeness | 4.6 | 4.4 | 4.9 |
| question:conciseness | 3.6 | 4.4 | 3.9 |
| question:usefulness | 4.2 | 4.6 | 4.8 |
| questions | 5 | 5 | 5 |
| **code sum of 30** | 28.1 | 27.7 | 25.4 |

## Winners by case and repeat

| case-repeat | steps…, overall |
|---|---|
| churn-r1-pony-bare | tie, bare, tie, bare |
| churn-r1-pony-v02 | tie, v02, pony, v02 |
| churn-r1-v02-bare | bare, bare, bare, bare |
| encoders-r1-pony-bare | pony, tie, bare, pony |
| encoders-r1-pony-v02 | pony, pony, v02, pony |
| encoders-r1-v02-bare | v02, v02, bare, v02 |
| optuna-r1-pony-bare | pony, pony, bare, pony |
| optuna-r1-pony-v02 | tie, v02, v02, v02 |
| optuna-r1-v02-bare | v02, bare, v02, v02 |
| rparse-r1-pony-bare | pony, bare, bare, bare |
| rparse-r1-pony-v02 | v02, v02, pony, v02 |
| rparse-r1-v02-bare | v02, v02, bare, v02 |
