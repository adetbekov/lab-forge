# lab-forge bench: v03 vs pony

## First-round conclusions: 4/7 reproduced

| Conclusion | First round | This run | Holds |
|---|---|---|---|
| Less code with lab-forge (≤ −15%) | −30% | +19% | no |
| Blind bloat score higher with lab-forge | 4.75 vs 3.6 | 4.25 vs 5 | no |
| Explicit requirements: lab-forge not better | 3.75 vs 4.75 | 5 vs 5 | yes |
| Task tokens within ±15% | +3% | +37% | no |
| Deploy costs 40-100k tokens per project | 48-90k | 91k | yes |
| Overall quality a tie (±2 of 30) | 25.0 vs 24.9 | 27.5 vs 28.2 | yes |
| LLM project won by lab-forge | A won c2 | 1/1 repeats | yes |

## Objective metrics

| Metric | v03 | pony |
|---|---|---|
| Solved, hidden checks | 8/8 | 8/8 |
| Claimed done but check fails (committed, not solved) | 0 | 0 |
| pytest red after step | 1 | 0 |
| Task tokens, k (all steps except deploy) | 852.3 | 620.0 |
| Tokens per solved task, k | 106.5 | 77.5 |
| Cost per solved task, $ | — | — |
| Task time, min | 40.2 | 35.2 |
| Deploy tokens per project, k | 91.0 | — |
| Python lines changed (no AI files) | 922 | 775 |
| All lines changed (no AI files) | 1029 | 793 |
| Largest new .py file, lines | 108 | 110 |
| Tests added | 23 | 23 |
| Files changed outside task scope | 0 | 0 |
| Coding steps committed straight to main | 0/8 | 8/8 |
| Coding steps left uncommitted | 0 | 0 |
| Ruff errors in changed files | 0 | 0 |
| Imports that do not resolve | 0 | 0 |
| Questions in coding-step replies | 0 | 0 |
| Files written during read-only question | 0 | 0 |
| Tune phrase applied in next session | 4/4 | 3/4 |
| Style stability across repeats (0-1) | — | — |

## Blind review (4 verdicts, 1-5)

| Criterion | v03 | pony |
|---|---|---|
| clarity | 4.5 | 4.2 |
| code:bloat | 4.2 | 5 |
| code:correctness | 4.6 | 4.4 |
| code:optimality | 4.5 | 4.9 |
| code:practices | 4.8 | 4.1 |
| code:scope | 4.4 | 4.9 |
| code:success | 5 | 5 |
| question:accuracy | 4.8 | 4.5 |
| question:completeness | 5 | 4.5 |
| question:conciseness | 4 | 4.2 |
| question:usefulness | 4.8 | 4.8 |
| questions | 5 | 5 |
| **code sum of 30** | 27.5 | 28.2 |

## Winners by case and repeat

| case-repeat | steps…, overall |
|---|---|
| churn-r1-v03-pony | v03, tie, tie, v03 |
| encoders-r1-v03-pony | v03, v03, pony, v03 |
| optuna-r1-v03-pony | tie, v03, v03, v03 |
| rparse-r1-v03-pony | v03, v03, v03, v03 |
