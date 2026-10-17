# lab-forge bench: a vs b

## First-round conclusions: 4/6 reproduced

| Conclusion | First round | This run | Holds |
|---|---|---|---|
| Less code with lab-forge (≤ −15%) | −30% | +0% | no |
| Blind bloat score higher with lab-forge | 4.75 vs 3.6 | 4.62 vs 4.50 | yes |
| Explicit requirements: lab-forge not better | 3.75 vs 4.75 | 5 vs 4.25 | no |
| Task tokens within ±15% | +3% | +3% | yes |
| Deploy costs 40-100k tokens per project | 48-90k | 99k | yes |
| Overall quality a tie (±2 of 30) | 25.0 vs 24.9 | 28.0 vs 26.8 | yes |
| LLM project won by lab-forge | A won c2 | 0/0 repeats | — |

## Objective metrics

| Metric | a | b |
|---|---|---|
| Solved, hidden checks | 6/8 | 8/8 |
| Claimed done but check fails (committed, not solved) | 2 | 0 |
| pytest red after step | 0 | 0 |
| Task tokens, k (all steps except deploy) | 881.4 | 856.3 |
| Tokens per solved task, k | 146.9 | 107.0 |
| Cost per solved task, $ | — | — |
| Task time, min | 66.2 | 76.5 |
| Deploy tokens per project, k | 98.7 | 82.1 |
| Python lines changed (no AI files) | 825 | 821 |
| All lines changed (no AI files) | 1038 | 980 |
| Largest new .py file, lines | 100 | 104 |
| Tests added | 20 | 20 |
| Files changed outside task scope | 4 | 4 |
| Coding steps committed straight to main | 0/8 | 6/8 |
| Coding steps left uncommitted | 0 | 0 |
| Ruff errors in changed files | 0 | 0 |
| Imports that do not resolve | 0 | 0 |
| Questions in coding-step replies | 0 | 0 |
| Files written during read-only question | 0 | 0 |
| Tune phrase applied in next session | 4/4 | 4/4 |
| Style stability across repeats (0-1) | 0.6 | 0.5 |

## Blind review (4 verdicts, 1-5)

| Criterion | a | b |
|---|---|---|
| clarity | 4.2 | 4 |
| code:bloat | 4.6 | 4.5 |
| code:correctness | 5 | 4.5 |
| code:optimality | 4.6 | 4.5 |
| code:practices | 4.2 | 4.5 |
| code:scope | 4.5 | 4.5 |
| code:success | 5 | 4.2 |
| question:accuracy | 4.8 | 4.8 |
| question:completeness | 5 | 4.5 |
| question:conciseness | 3.8 | 4.5 |
| question:usefulness | 4.8 | 4.8 |
| questions | 5 | 4.2 |
| **code sum of 30** | 28.0 | 26.8 |

## Winners by case and repeat

| case-repeat | steps…, overall |
|---|---|
| churn-r1 | a, tie, b, a |
| churn-r2 | a, a, b, a |
| encoders-r1 | b, tie, tie, b |
| encoders-r2 | b, a, a, a |
