# lab-forge bench: v03 vs bare

## First-round conclusions: 5/7 reproduced

| Conclusion | First round | This run | Holds |
|---|---|---|---|
| Less code with lab-forge (≤ −15%) | −30% | -55% | yes |
| Blind bloat score higher with lab-forge | 4.75 vs 3.6 | 5 vs 3.25 | yes |
| Explicit requirements: lab-forge not better | 3.75 vs 4.75 | 4.88 vs 5 | yes |
| Task tokens within ±15% | +3% | +26% | no |
| Deploy costs 40-100k tokens per project | 48-90k | 91k | yes |
| Overall quality a tie (±2 of 30) | 25.0 vs 24.9 | 28.1 vs 25.2 | no |
| LLM project won by lab-forge | A won c2 | 1/1 repeats | yes |

## Objective metrics

| Metric | v03 | bare |
|---|---|---|
| Solved, hidden checks | 8/8 | 8/8 |
| Claimed done but check fails (committed, not solved) | 0 | 0 |
| pytest red after step | 1 | 0 |
| Task tokens, k (all steps except deploy) | 852.3 | 675.5 |
| Tokens per solved task, k | 106.5 | 84.4 |
| Cost per solved task, $ | — | — |
| Task time, min | 40.2 | 54.5 |
| Deploy tokens per project, k | 91.0 | — |
| Python lines changed (no AI files) | 922 | 2048 |
| All lines changed (no AI files) | 1029 | 2373 |
| Largest new .py file, lines | 108 | 194 |
| Tests added | 23 | 74 |
| Files changed outside task scope | 0 | 2 |
| Coding steps committed straight to main | 0/8 | 8/8 |
| Coding steps left uncommitted | 0 | 0 |
| Ruff errors in changed files | 0 | 0 |
| Imports that do not resolve | 0 | 0 |
| Questions in coding-step replies | 0 | 0 |
| Files written during read-only question | 0 | 0 |
| Tune phrase applied in next session | 4/4 | 4/4 |
| Style stability across repeats (0-1) | — | — |

## Blind review (4 verdicts, 1-5)

| Criterion | v03 | bare |
|---|---|---|
| clarity | 4 | 3.8 |
| code:bloat | 5 | 3.2 |
| code:correctness | 4.4 | 4.6 |
| code:optimality | 5 | 4 |
| code:practices | 4.2 | 4.2 |
| code:scope | 4.6 | 4.1 |
| code:success | 4.9 | 5 |
| question:accuracy | 4.8 | 5 |
| question:completeness | 4.8 | 5 |
| question:conciseness | 4 | 3.8 |
| question:usefulness | 4.8 | 5 |
| questions | 5 | 5 |
| **code sum of 30** | 28.1 | 25.2 |

## Winners by case and repeat

| case-repeat | steps…, overall |
|---|---|
| churn-r1-v03-bare | bare, bare, tie, bare |
| encoders-r1-v03-bare | v03, v03, bare, v03 |
| optuna-r1-v03-bare | v03, v03, v03, v03 |
| rparse-r1-v03-bare | v03, bare, tie, v03 |
