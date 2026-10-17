# lab-forge bench: a vs b

## First-round conclusions: 1/6 reproduced

| Conclusion | First round | This run | Holds |
|---|---|---|---|
| Less code with lab-forge (≤ −15%) | −30% | +15% | no |
| Blind bloat score higher with lab-forge | 4.75 vs 3.6 | 4.25 vs 4.25 | no |
| Explicit requirements: lab-forge not better | 3.75 vs 4.75 | 5 vs 4.75 | no |
| Task tokens within ±15% | +3% | +53% | no |
| Deploy costs 40-100k tokens per project | 48-90k | 867k | no |
| Overall quality a tie (±2 of 30) | 25.0 vs 24.9 | 27.5 vs 26.5 | yes |
| LLM project won by lab-forge | A won c2 | 0/0 repeats | — |

## Objective metrics

| Metric | a | b |
|---|---|---|
| Solved, hidden checks | 4/4 | 2/4 |
| Claimed done but check fails (committed, not solved) | 0 | 2 |
| pytest red after step | 0 | 0 |
| Task tokens, k (all steps except deploy) | 2840.8 | 1857.7 |
| Tokens per solved task, k | 710.2 | 928.9 |
| Cost per solved task, $ | 0.9 | 1.4 |
| Task time, min | 12.6 | 8.2 |
| Deploy tokens per project, k | 867.5 | 636.2 |
| Python lines changed (no AI files) | 778 | 674 |
| All lines changed (no AI files) | 1456 | 841 |
| Largest new .py file, lines | 98 | 100 |
| Tests added | 14 | 9 |
| Files changed outside task scope | 0 | 0 |
| Coding steps committed straight to main | 0/4 | 4/4 |
| Coding steps left uncommitted | 0 | 0 |
| Ruff errors in changed files | 0 | 0 |
| Imports that do not resolve | 0 | 0 |
| Questions in coding-step replies | 0 | 0 |
| Files written during read-only question | 0 | 0 |
| Tune phrase applied in next session | 2/2 | 2/2 |
| Style stability across repeats (0-1) | 0.2 | 0.4 |

## Blind review (2 verdicts, 1-5)

| Criterion | a | b |
|---|---|---|
| clarity | 4.5 | 4.5 |
| code:bloat | 4.2 | 4.2 |
| code:correctness | 5 | 4.2 |
| code:optimality | 4.8 | 4.2 |
| code:practices | 4.5 | 4.5 |
| code:scope | 4 | 4.5 |
| code:success | 5 | 4.8 |
| question:accuracy | 5 | 4 |
| question:completeness | 5 | 5 |
| question:conciseness | 4 | 4 |
| question:usefulness | 5 | 4.5 |
| questions | 5 | 5 |
| **code sum of 30** | 27.5 | 26.5 |

## Winners by case and repeat

| case-repeat | steps…, overall |
|---|---|
| churn-r1 | tie, a, a, a |
| churn-r2 | b, a, tie, a |
