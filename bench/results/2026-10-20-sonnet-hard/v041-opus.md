# lab-forge bench: v041 vs opus

## First-round conclusions: 4/6 reproduced

| Conclusion | First round | This run | Holds |
|---|---|---|---|
| Less code with lab-forge (≤ −15%) | −30% | -59% | yes |
| Blind bloat score higher with lab-forge | 4.75 vs 3.6 | 5 vs 3.12 | yes |
| Explicit requirements: lab-forge not better | 3.75 vs 4.75 | 4.12 vs 5 | yes |
| Task tokens within ±15% | +3% | -29% | no |
| Deploy costs 40-100k tokens per project | 48-90k | 643k | no |
| Overall quality a tie (±2 of 30) | 25.0 vs 24.9 | 25.1 vs 25.2 | yes |
| LLM project won by lab-forge | A won c2 | 0/0 repeats | — |

## Objective metrics

| Metric | v041 | opus |
|---|---|---|
| Solved, hidden checks | 4/4 | 4/4 |
| Claimed done but check fails (committed, not solved) | 0 | 0 |
| pytest red after step | 0 | 0 |
| Task tokens, k (all steps except deploy) | 1761.3 | 2482.5 |
| Tokens per solved task, k | 440.3 | 620.6 |
| Cost per solved task, $ | 0.3 | 0.9 |
| Task time, min | 14.5 | 14.4 |
| Deploy tokens per project, k | 643.0 | — |
| Python lines changed (no AI files) | 624 | 1521 |
| All lines changed (no AI files) | 744 | 1760 |
| Largest new .py file, lines | 79 | 131 |
| Tests added | 23 | 49 |
| Files changed outside task scope | 0 | 0 |
| Coding steps committed straight to main | 0/4 | 0/4 |
| Coding steps left uncommitted | 0 | 0 |
| Ruff errors in changed files | 0 | 0 |
| Imports that do not resolve | 0 | 0 |
| Questions in coding-step replies | 0 | 0 |
| Files written during read-only question | 0 | 0 |
| Tune phrase applied in next session | 0/2 | 2/2 |
| Style stability across repeats (0-1) | — | — |
| Tool calls per solved task | 12.0 | 17.5 |
| Weighted tokens per solved task, k (cache read x0.1, write x1.25) | 106.2 | 142.6 |
| Bare `pytest` green after step | 4/4 | 4/4 |
| Mutants killed by the agent's tests | 9/9 | 7/9 |

## Spread over repeats (mean ± SE)

| Metric | v041 | opus |
|---|---|---|
| Tokens per solved task, k | 440.32 (n=1) | 620.63 (n=1) |
| Cost per solved task, $ | 0.32 (n=1) | 0.93 (n=1) |
| code sum of 30 | 25.12 (n=1) | 25.25 (n=1) |
| weighted code score, 1-5 | 4.05 (n=1) | 4.57 (n=1) |

## Blind review (4 verdicts, 1-5)

| Criterion | v041 | opus |
|---|---|---|
| clarity | 4 | 4 |
| code:bloat | 5 | 3.1 |
| code:correctness | 3.9 | 4.9 |
| code:methodology | 4.5 | 4.8 |
| code:optimality | 4.2 | 3.9 |
| code:practices | 3.9 | 4.8 |
| code:scope | 4 | 3.6 |
| code:success | 4.1 | 5 |
| code:tests | 3.5 | 4.9 |
| question:accuracy | 3.5 | 5 |
| question:completeness | 3.2 | 5 |
| question:conciseness | 4.5 | 3.2 |
| question:usefulness | 3.5 | 5 |
| questions | 4.2 | 5 |
| **code sum of 30** | 25.1 | 25.2 |
| **weighted code score, 1-5** | 4.0 | 4.6 |

## Winners by case and repeat

| case-repeat | steps…, overall |
|---|---|
| forecast-r1-v041-opus | opus, opus, opus, opus |
| fraud-r1-v041-opus | tie, opus, opus, opus |

X/Y order changed the winner in 1 of 8 calls; those count as ties.
