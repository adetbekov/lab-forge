# lab-forge bench: pony vs v02

## First-round conclusions: 4/7 reproduced

| Conclusion | First round | This run | Holds |
|---|---|---|---|
| Less code with lab-forge (≤ −15%) | −30% | -16% | yes |
| Blind bloat score higher with lab-forge | 4.75 vs 3.6 | 5 vs 4.38 | yes |
| Explicit requirements: lab-forge not better | 3.75 vs 4.75 | 4.88 vs 5 | yes |
| Task tokens within ±15% | +3% | -26% | no |
| Deploy costs 40-100k tokens per project | 48-90k | —k | no |
| Overall quality a tie (±2 of 30) | 25.0 vs 24.9 | 27.8 vs 28.1 | yes |
| LLM project won by lab-forge | A won c2 | 0/1 repeats | no |

## Objective metrics

| Metric | pony | v02 |
|---|---|---|
| Solved, hidden checks | 8/8 | 8/8 |
| Claimed done but check fails (committed, not solved) | 0 | 0 |
| pytest red after step | 0 | 0 |
| Task tokens, k (all steps except deploy) | 620.0 | 839.1 |
| Tokens per solved task, k | 77.5 | 104.9 |
| Cost per solved task, $ | — | — |
| Task time, min | 35.2 | 49.8 |
| Deploy tokens per project, k | — | 90.2 |
| Python lines changed (no AI files) | 775 | 923 |
| All lines changed (no AI files) | 793 | 1071 |
| Largest new .py file, lines | 110 | 105 |
| Tests added | 23 | 23 |
| Files changed outside task scope | 0 | 2 |
| Coding steps committed straight to main | 8/8 | 0/8 |
| Coding steps left uncommitted | 0 | 0 |
| Ruff errors in changed files | 0 | 0 |
| Imports that do not resolve | 0 | 0 |
| Questions in coding-step replies | 0 | 0 |
| Files written during read-only question | 0 | 0 |
| Tune phrase applied in next session | 3/4 | 4/4 |
| Style stability across repeats (0-1) | — | — |

## Blind review (4 verdicts, 1-5)

| Criterion | pony | v02 |
|---|---|---|
| clarity | 4 | 3.8 |
| code:bloat | 5 | 4.4 |
| code:correctness | 4.4 | 4.8 |
| code:optimality | 4.6 | 4.8 |
| code:practices | 3.9 | 4.9 |
| code:scope | 5 | 4.4 |
| code:success | 4.9 | 5 |
| question:accuracy | 4.2 | 4 |
| question:completeness | 4.8 | 5 |
| question:conciseness | 4.5 | 3.5 |
| question:usefulness | 4.8 | 4.5 |
| questions | 5 | 5 |
| **code sum of 30** | 27.8 | 28.1 |

## Winners by case and repeat

| case-repeat | steps…, overall |
|---|---|
| churn-r1-pony-v02 | tie, v02, pony, v02 |
| encoders-r1-pony-v02 | pony, pony, v02, pony |
| optuna-r1-pony-v02 | tie, v02, v02, v02 |
| rparse-r1-pony-v02 | v02, v02, pony, v02 |
