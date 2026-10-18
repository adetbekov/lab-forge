# lab-forge bench: pony vs bare

## First-round conclusions: 4/7 reproduced

| Conclusion | First round | This run | Holds |
|---|---|---|---|
| Less code with lab-forge (≤ −15%) | −30% | -62% | yes |
| Blind bloat score higher with lab-forge | 4.75 vs 3.6 | 5 vs 2.88 | yes |
| Explicit requirements: lab-forge not better | 3.75 vs 4.75 | 5 vs 5 | yes |
| Task tokens within ±15% | +3% | -8% | yes |
| Deploy costs 40-100k tokens per project | 48-90k | —k | no |
| Overall quality a tie (±2 of 30) | 25.0 vs 24.9 | 27.6 vs 25.2 | no |
| LLM project won by lab-forge | A won c2 | 0/1 repeats | no |

## Objective metrics

| Metric | pony | bare |
|---|---|---|
| Solved, hidden checks | 8/8 | 8/8 |
| Claimed done but check fails (committed, not solved) | 0 | 0 |
| pytest red after step | 0 | 0 |
| Task tokens, k (all steps except deploy) | 620.0 | 675.5 |
| Tokens per solved task, k | 77.5 | 84.4 |
| Cost per solved task, $ | — | — |
| Task time, min | 35.2 | 54.5 |
| Deploy tokens per project, k | — | — |
| Python lines changed (no AI files) | 775 | 2048 |
| All lines changed (no AI files) | 793 | 2373 |
| Largest new .py file, lines | 110 | 194 |
| Tests added | 23 | 74 |
| Files changed outside task scope | 0 | 2 |
| Coding steps committed straight to main | 8/8 | 8/8 |
| Coding steps left uncommitted | 0 | 0 |
| Ruff errors in changed files | 0 | 0 |
| Imports that do not resolve | 0 | 0 |
| Questions in coding-step replies | 0 | 0 |
| Files written during read-only question | 0 | 0 |
| Tune phrase applied in next session | 3/4 | 4/4 |
| Style stability across repeats (0-1) | — | — |

## Blind review (4 verdicts, 1-5)

| Criterion | pony | bare |
|---|---|---|
| clarity | 4.2 | 3.8 |
| code:bloat | 5 | 2.9 |
| code:correctness | 4.4 | 4.6 |
| code:optimality | 4.6 | 3.9 |
| code:practices | 3.6 | 4.9 |
| code:scope | 5 | 4 |
| code:success | 5 | 5 |
| question:accuracy | 4.2 | 5 |
| question:completeness | 4 | 5 |
| question:conciseness | 4.2 | 3.8 |
| question:usefulness | 4.5 | 4.8 |
| questions | 5 | 5 |
| **code sum of 30** | 27.6 | 25.2 |

## Winners by case and repeat

| case-repeat | steps…, overall |
|---|---|
| churn-r1-pony-bare | tie, bare, tie, bare |
| encoders-r1-pony-bare | pony, tie, bare, pony |
| optuna-r1-pony-bare | pony, pony, bare, pony |
| rparse-r1-pony-bare | pony, bare, bare, bare |
