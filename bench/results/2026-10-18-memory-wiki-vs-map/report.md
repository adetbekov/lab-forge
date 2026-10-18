# lab-forge bench: wiki vs map

## First-round conclusions: 4/6 reproduced

| Conclusion | First round | This run | Holds |
|---|---|---|---|
| Less code with lab-forge (≤ −15%) | −30% | +9% | no |
| Blind bloat score higher with lab-forge | 4.75 vs 3.6 | 4.75 vs 5 | no |
| Explicit requirements: lab-forge not better | 3.75 vs 4.75 | 5 vs 5 | yes |
| Task tokens within ±15% | +3% | -6% | yes |
| Deploy costs 40-100k tokens per project | 48-90k | 61k | yes |
| Overall quality a tie (±2 of 30) | 25.0 vs 24.9 | 29.5 vs 29.2 | yes |
| LLM project won by lab-forge | A won c2 | 0/0 repeats | — |

## Objective metrics

| Metric | wiki | map |
|---|---|---|
| Solved, hidden checks | 4/4 | 4/4 |
| Claimed done but check fails (committed, not solved) | 0 | 0 |
| pytest red after step | 1 | 0 |
| Task tokens, k (all steps except deploy) | 390.7 | 414.9 |
| Tokens per solved task, k | 97.7 | 103.7 |
| Cost per solved task, $ | — | — |
| Task time, min | 16.2 | 12.7 |
| Deploy tokens per project, k | 61.3 | 61.3 |
| Python lines changed (no AI files) | 284 | 261 |
| All lines changed (no AI files) | 284 | 261 |
| Largest new .py file, lines | 57 | 59 |
| Tests added | 11 | 10 |
| Files changed outside task scope | 0 | 0 |
| Coding steps committed straight to main | 0/4 | 0/4 |
| Coding steps left uncommitted | 0 | 0 |
| Ruff errors in changed files | 0 | 0 |
| Imports that do not resolve | 0 | 0 |
| Questions in coding-step replies | 0 | 0 |
| Files written during read-only question | 0 | 0 |
| Tune phrase applied in next session | 2/2 | 2/2 |
| Style stability across repeats (0-1) | 0.6 | 0.1 |

## Blind review (2 verdicts, 1-5)

| Criterion | wiki | map |
|---|---|---|
| clarity | 4.5 | 4 |
| code:bloat | 4.8 | 5 |
| code:correctness | 4.8 | 4.8 |
| code:optimality | 5 | 5 |
| code:practices | 5 | 4.5 |
| code:scope | 5 | 5 |
| code:success | 5 | 5 |
| question:accuracy | 5 | 5 |
| question:completeness | 4.5 | 5 |
| question:conciseness | 4 | 4 |
| question:usefulness | 4.5 | 5 |
| questions | 5 | 5 |
| **code sum of 30** | 29.5 | 29.2 |

## Winners by case and repeat

| case-repeat | steps…, overall |
|---|---|
| optuna-r1 | tie, wiki, tie, wiki |
| optuna-r2 | tie, map, map, map |
