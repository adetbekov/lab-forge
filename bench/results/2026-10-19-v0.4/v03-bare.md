# lab-forge bench: v03 vs bare

## First-round conclusions: 4/7 reproduced

| Conclusion | First round | This run | Holds |
|---|---|---|---|
| Less code with lab-forge (≤ −15%) | −30% | -5% | no |
| Blind bloat score higher with lab-forge | 4.75 vs 3.6 | 4.38 vs 4.33 | yes |
| Explicit requirements: lab-forge not better | 3.75 vs 4.75 | 4.96 vs 4.62 | no |
| Task tokens within ±15% | +3% | +14% | yes |
| Deploy costs 40-100k tokens per project | 48-90k | 613k | no |
| Overall quality a tie (±2 of 30) | 25.0 vs 24.9 | 26.7 vs 25.9 | yes |
| LLM project won by lab-forge | A won c2 | 6/6 repeats | yes |

## Objective metrics

| Metric | v03 | bare |
|---|---|---|
| Solved, hidden checks | 24/24 | 24/24 |
| Claimed done but check fails (committed, not solved) | 0 | 0 |
| pytest red after step | 2 | 0 |
| Task tokens, k (all steps except deploy) | 9662.9 | 8508.0 |
| Tokens per solved task, k | 402.6 | 354.5 |
| Cost per solved task, $ | 0.3 | 0.3 |
| Task time, min | 91.9 | 79.7 |
| Deploy tokens per project, k | 612.5 | — |
| Python lines changed (no AI files) | 2714 | 2858 |
| All lines changed (no AI files) | 3518 | 3389 |
| Largest new .py file, lines | 109 | 83 |
| Tests added | 103 | 129 |
| Files changed outside task scope | 2 | 4 |
| Coding steps committed straight to main | 0/24 | 24/24 |
| Coding steps left uncommitted | 0 | 0 |
| Ruff errors in changed files | 15 | 44 |
| Imports that do not resolve | 2 | 0 |
| Questions in coding-step replies | 0 | 0 |
| Files written during read-only question | 0 | 0 |
| Tune phrase applied in next session | 3/12 | 0/12 |
| Style stability across repeats (0-1) | 0.5 | 0.7 |
| Tool calls per solved task | 12.0 | 11.5 |
| Weighted tokens per solved task, k (cache read x0.1, write x1.25) | 96.4 | 81.2 |
| Bare `pytest` green after step | 22/22 | 14/24 |
| Mutants killed by the agent's tests | 15/24 | 7/15 |

## Spread over repeats (mean ± SE)

| Metric | v03 | bare |
|---|---|---|
| Tokens per solved task, k | 402.62 ± 32.58 (n=3) | 354.50 ± 32.95 (n=3) |
| Cost per solved task, $ | 0.28 ± 0.01 (n=3) | 0.25 ± 0.00 (n=3) |
| code sum of 30 | 26.69 ± 0.20 (n=3) | 25.92 ± 0.15 (n=3) |
| weighted code score, 1-5 | 4.49 ± 0.02 (n=3) | 4.37 ± 0.03 (n=3) |

## Blind review (24 verdicts, 1-5)

| Criterion | v03 | bare |
|---|---|---|
| clarity | 4.0 | 3.7 |
| code:bloat | 4.4 | 4.3 |
| code:correctness | 4.5 | 4.4 |
| code:methodology | 4.7 | 4.7 |
| code:optimality | 4.2 | 4.4 |
| code:practices | 4.4 | 3.6 |
| code:scope | 4.3 | 4.6 |
| code:success | 5.0 | 4.6 |
| code:tests | 4.3 | 4.2 |
| question:accuracy | 4.2 | 4.3 |
| question:completeness | 4.3 | 4.5 |
| question:conciseness | 3.8 | 3.5 |
| question:usefulness | 4.1 | 4.2 |
| questions | 4.6 | 4.5 |
| **code sum of 30** | 26.7 | 25.9 |
| **weighted code score, 1-5** | 4.5 | 4.4 |

## Winners by case and repeat

| case-repeat | steps…, overall |
|---|---|
| churn-r1-v03-bare | bare, bare, tie, bare |
| churn-r2-v03-bare | v03, bare, bare, bare |
| churn-r3-v03-bare | v03, v03, tie, v03 |
| encoders-r1-v03-bare | v03, v03, tie, v03 |
| encoders-r2-v03-bare | tie, tie, tie, tie |
| encoders-r3-v03-bare | tie, tie, tie, v03 |
| optuna-r1-v03-bare | tie, v03, tie, v03 |
| optuna-r2-v03-bare | v03, v03, tie, v03 |
| optuna-r3-v03-bare | v03, v03, bare, v03 |
| rparse-r1-v03-bare | v03, v03, v03, v03 |
| rparse-r2-v03-bare | v03, tie, tie, v03 |
| rparse-r3-v03-bare | v03, tie, v03, v03 |

X/Y order changed the winner in 15 of 48 calls; those count as ties.
