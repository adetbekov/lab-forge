# lab-forge bench: decide vs main

## First-round conclusions: 4/7 reproduced

| Conclusion | First round | This run | Holds |
|---|---|---|---|
| Less code with lab-forge (≤ −15%) | −30% | -7% | no |
| Blind bloat score higher with lab-forge | 4.75 vs 3.6 | 4.38 vs 4 | yes |
| Explicit requirements: lab-forge not better | 3.75 vs 4.75 | 4.69 vs 4.81 | yes |
| Task tokens within ±15% | +3% | -1% | yes |
| Deploy costs 40-100k tokens per project | 48-90k | 732k | no |
| Overall quality a tie (±2 of 30) | 25.0 vs 24.9 | 26.1 vs 24.9 | yes |
| LLM project won by lab-forge | A won c2 | 1/2 repeats | no |

## Objective metrics

| Metric | decide | main |
|---|---|---|
| Solved, hidden checks | 16/16 | 16/16 |
| Claimed done but check fails (committed, not solved) | 0 | 0 |
| pytest red after step | 0 | 1 |
| Task tokens, k (all steps except deploy) | 6897.4 | 6939.0 |
| Tokens per solved task, k | 431.1 | 433.7 |
| Cost per solved task, $ | 0.3 | 0.3 |
| Task time, min | 42.1 | 49.3 |
| Deploy tokens per project, k | 732.1 | 673.9 |
| Python lines changed (no AI files) | 1767 | 1896 |
| All lines changed (no AI files) | 2291 | 2493 |
| Largest new .py file, lines | 100 | 109 |
| Tests added | 70 | 64 |
| Files changed outside task scope | 2 | 4 |
| Coding steps committed straight to main | 0/16 | 0/16 |
| Coding steps left uncommitted | 0 | 0 |
| Ruff errors in changed files | 11 | 4 |
| Imports that do not resolve | 0 | 0 |
| Questions in coding-step replies | 0 | 0 |
| Files written during read-only question | 0 | 0 |
| Tune phrase applied in next session | 6/8 | 7/8 |
| Style stability across repeats (0-1) | 0.5 | 0.6 |

## Blind review (8 verdicts, 1-5)

| Criterion | decide | main |
|---|---|---|
| clarity | 3.9 | 4 |
| code:bloat | 4.4 | 4 |
| code:correctness | 4.2 | 4.2 |
| code:optimality | 4.2 | 3.9 |
| code:practices | 4.2 | 4 |
| code:scope | 4.4 | 4 |
| code:success | 4.7 | 4.8 |
| question:accuracy | 4.1 | 4.4 |
| question:completeness | 4.6 | 4.4 |
| question:conciseness | 3.8 | 4 |
| question:usefulness | 4.2 | 4.2 |
| questions | 4.8 | 4.8 |
| **code sum of 30** | 26.1 | 24.9 |

## Winners by case and repeat

| case-repeat | steps…, overall |
|---|---|
| churn-r1 | decide, tie, main, decide |
| churn-r2 | tie, decide, main, decide |
| encoders-r1 | main, tie, main, main |
| encoders-r2 | decide, decide, tie, decide |
| optuna-r1 | main, tie, decide, decide |
| optuna-r2 | tie, decide, main, tie |
| rparse-r1 | decide, decide, decide, decide |
| rparse-r2 | main, main, main, main |
