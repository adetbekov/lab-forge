# lab-forge bench: v02 vs pony vs bare vs v03

## Objective metrics

| Metric | v02 | pony | bare | v03 |
|---|---|---|---|---|
| Solved, hidden checks | 8/8 | 8/8 | 8/8 | 8/8 |
| Claimed done but check fails (committed, not solved) | 0 | 0 | 0 | 0 |
| pytest red after step | 0 | 0 | 0 | 1 |
| Task tokens, k (all steps except deploy) | 839.1 | 620.0 | 675.5 | 852.3 |
| Tokens per solved task, k | 104.9 | 77.5 | 84.4 | 106.5 |
| Cost per solved task, $ | — | — | — | — |
| Task time, min | 49.8 | 35.2 | 54.5 | 40.2 |
| Deploy tokens per project, k | 90.2 | — | — | 91.0 |
| Python lines changed (no AI files) | 923 | 775 | 2048 | 922 |
| All lines changed (no AI files) | 1071 | 793 | 2373 | 1029 |
| Largest new .py file, lines | 105 | 110 | 194 | 108 |
| Tests added | 23 | 23 | 74 | 23 |
| Files changed outside task scope | 2 | 0 | 2 | 0 |
| Coding steps committed straight to main | 0/8 | 8/8 | 8/8 | 0/8 |
| Coding steps left uncommitted | 0 | 0 | 0 | 0 |
| Ruff errors in changed files | 0 | 0 | 0 | 0 |
| Imports that do not resolve | 0 | 0 | 0 | 0 |
| Questions in coding-step replies | 0 | 0 | 0 | 0 |
| Files written during read-only question | 0 | 0 | 0 | 0 |
| Tune phrase applied in next session | 4/4 | 3/4 | 4/4 | 4/4 |
| Style stability across repeats (0-1) | — | — | — | — |

## Blind review (24 verdicts, 1-5)

| Criterion | v02 | pony | bare | v03 |
|---|---|---|---|---|
| clarity | 4 | 4.2 | 3.9 | 4.2 |
| code:bloat | 4.7 | 5 | 3.2 | 4.6 |
| code:correctness | 4.7 | 4.4 | 4.6 | 4.5 |
| code:optimality | 4.8 | 4.7 | 3.9 | 4.7 |
| code:practices | 4.5 | 3.9 | 4.5 | 4.5 |
| code:scope | 4.5 | 5.0 | 4.2 | 4.5 |
| code:success | 5 | 5.0 | 5 | 5.0 |
| question:accuracy | 4.2 | 4.3 | 5 | 4.8 |
| question:completeness | 4.7 | 4.4 | 4.9 | 4.8 |
| question:conciseness | 3.8 | 4.3 | 3.8 | 4.1 |
| question:usefulness | 4.3 | 4.7 | 4.8 | 4.8 |
| questions | 5 | 5 | 5 | 5 |
| **code sum of 30** | 28.1 | 27.9 | 25.3 | 27.8 |

## Winners by case and repeat

| case-repeat | steps…, overall |
|---|---|
| churn-r1-pony-bare | tie, bare, tie, bare |
| churn-r1-pony-v02 | tie, v02, pony, v02 |
| churn-r1-v02-bare | bare, bare, bare, bare |
| churn-r1-v03-bare | bare, bare, tie, bare |
| churn-r1-v03-pony | v03, tie, tie, v03 |
| churn-r1-v03-v02 | tie, v02, tie, v02 |
| encoders-r1-pony-bare | pony, tie, bare, pony |
| encoders-r1-pony-v02 | pony, pony, v02, pony |
| encoders-r1-v02-bare | v02, v02, bare, v02 |
| encoders-r1-v03-bare | v03, v03, bare, v03 |
| encoders-r1-v03-pony | v03, v03, pony, v03 |
| encoders-r1-v03-v02 | v03, tie, v02, v03 |
| optuna-r1-pony-bare | pony, pony, bare, pony |
| optuna-r1-pony-v02 | tie, v02, v02, v02 |
| optuna-r1-v02-bare | v02, bare, v02, v02 |
| optuna-r1-v03-bare | v03, v03, v03, v03 |
| optuna-r1-v03-pony | tie, v03, v03, v03 |
| optuna-r1-v03-v02 | tie, v03, tie, v03 |
| rparse-r1-pony-bare | pony, bare, bare, bare |
| rparse-r1-pony-v02 | v02, v02, pony, v02 |
| rparse-r1-v02-bare | v02, v02, bare, v02 |
| rparse-r1-v03-bare | v03, bare, tie, v03 |
| rparse-r1-v03-pony | v03, v03, v03, v03 |
| rparse-r1-v03-v02 | tie, v02, v03, v03 |
