# lab-forge bench: fixed vs routed

## First-round conclusions: 5/7 reproduced

| Conclusion | First round | This run | Holds |
|---|---|---|---|
| Less code with lab-forge (≤ −15%) | −30% | -18% | yes |
| Blind bloat score higher with lab-forge | 4.75 vs 3.6 | 4.50 vs 3.88 | yes |
| Explicit requirements: lab-forge not better | 3.75 vs 4.75 | 4.88 vs 4.88 | yes |
| Task tokens within ±15% | +3% | -41% | no |
| Deploy costs 40-100k tokens per project | 48-90k | 50k | yes |
| Overall quality a tie (±2 of 30) | 25.0 vs 24.9 | 26.9 vs 27.0 | yes |
| LLM project won by lab-forge | A won c2 | 0/1 repeats | no |

## Objective metrics

| Metric | fixed | routed |
|---|---|---|
| Solved, hidden checks | 8/8 | 6/8 |
| Claimed done but check fails (committed, not solved) | 0 | 2 |
| pytest red after step | 0 | 0 |
| Task tokens, k (all steps except deploy) | 740.7 | 1251.6 |
| Tokens per solved task, k | 92.6 | 208.6 |
| Cost per solved task, $ | — | — |
| Task time, min | 0.0 | 0.0 |
| Deploy tokens per project, k | 49.8 | 49.8 |
| Python lines changed (no AI files) | 1441 | 1750 |
| All lines changed (no AI files) | 2026 | 2371 |
| Largest new .py file, lines | 84 | 110 |
| Tests added | 40 | 68 |
| Files changed outside task scope | 0 | 0 |
| Coding steps committed straight to main | 8/8 | 8/8 |
| Coding steps left uncommitted | 0 | 0 |
| Ruff errors in changed files | 0 | 0 |
| Questions in coding-step replies | 0 | 0 |
| Files written during read-only question | 0 | 0 |
| Tune phrase applied in next session | 4/4 | 4/4 |
| Style stability across repeats (0-1) | — | — |

## Blind review (4 verdicts, 1-5)

| Criterion | fixed | routed |
|---|---|---|
| clarity | 4 | 4 |
| code:bloat | 4.5 | 3.9 |
| code:correctness | 4.2 | 4.8 |
| code:optimality | 4.5 | 4.2 |
| code:practices | 4.2 | 4.5 |
| code:scope | 4.5 | 4.8 |
| code:success | 4.9 | 4.9 |
| question:accuracy | 5 | 5 |
| question:completeness | 4.8 | 5 |
| question:conciseness | 4.2 | 4 |
| question:usefulness | 4.8 | 5 |
| questions | 4.8 | 4.8 |
| **code sum of 30** | 26.9 | 27.0 |

## Winners by case and repeat

| case-repeat | steps…, overall |
|---|---|
| churn-r1 | routed, fixed, tie, fixed |
| encoders-r1 | tie, fixed, tie, fixed |
| optuna-r1 | routed, fixed, routed, routed |
| rparse-r1 | routed, routed, tie, routed |
