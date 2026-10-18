# lab-forge bench: v02 vs bare

## First-round conclusions: 5/7 reproduced

| Conclusion | First round | This run | Holds |
|---|---|---|---|
| Less code with lab-forge (≤ −15%) | −30% | -55% | yes |
| Blind bloat score higher with lab-forge | 4.75 vs 3.6 | 5 vs 3.38 | yes |
| Explicit requirements: lab-forge not better | 3.75 vs 4.75 | 5 vs 5 | yes |
| Task tokens within ±15% | +3% | +24% | no |
| Deploy costs 40-100k tokens per project | 48-90k | 90k | yes |
| Overall quality a tie (±2 of 30) | 25.0 vs 24.9 | 28.0 vs 25.5 | no |
| LLM project won by lab-forge | A won c2 | 1/1 repeats | yes |

## Objective metrics

| Metric | v02 | bare |
|---|---|---|
| Solved, hidden checks | 8/8 | 8/8 |
| Claimed done but check fails (committed, not solved) | 0 | 0 |
| pytest red after step | 0 | 0 |
| Task tokens, k (all steps except deploy) | 839.1 | 675.5 |
| Tokens per solved task, k | 104.9 | 84.4 |
| Cost per solved task, $ | — | — |
| Task time, min | 49.8 | 54.5 |
| Deploy tokens per project, k | 90.2 | — |
| Python lines changed (no AI files) | 923 | 2048 |
| All lines changed (no AI files) | 1071 | 2373 |
| Largest new .py file, lines | 105 | 194 |
| Tests added | 23 | 74 |
| Files changed outside task scope | 2 | 2 |
| Coding steps committed straight to main | 0/8 | 8/8 |
| Coding steps left uncommitted | 0 | 0 |
| Ruff errors in changed files | 0 | 0 |
| Imports that do not resolve | 0 | 0 |
| Questions in coding-step replies | 0 | 0 |
| Files written during read-only question | 0 | 0 |
| Tune phrase applied in next session | 4/4 | 4/4 |
| Style stability across repeats (0-1) | — | — |

## Blind review (4 verdicts, 1-5)

| Criterion | v02 | bare |
|---|---|---|
| clarity | 4.2 | 4.2 |
| code:bloat | 5 | 3.4 |
| code:correctness | 4.5 | 4.6 |
| code:optimality | 4.9 | 3.8 |
| code:practices | 4.1 | 4.4 |
| code:scope | 4.5 | 4.4 |
| code:success | 5 | 5 |
| question:accuracy | 4.2 | 5 |
| question:completeness | 4.2 | 4.8 |
| question:conciseness | 3.8 | 4 |
| question:usefulness | 4 | 4.8 |
| questions | 5 | 5 |
| **code sum of 30** | 28.0 | 25.5 |

## Winners by case and repeat

| case-repeat | steps…, overall |
|---|---|
| churn-r1-v02-bare | bare, bare, bare, bare |
| encoders-r1-v02-bare | v02, v02, bare, v02 |
| optuna-r1-v02-bare | v02, bare, v02, v02 |
| rparse-r1-v02-bare | v02, v02, bare, v02 |
