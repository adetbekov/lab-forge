# lab-forge bench: v04 vs bare

## First-round conclusions: 3/7 reproduced

| Conclusion | First round | This run | Holds |
|---|---|---|---|
| Less code with lab-forge (≤ −15%) | −30% | -11% | no |
| Blind bloat score higher with lab-forge | 4.75 vs 3.6 | 4.50 vs 4.10 | yes |
| Explicit requirements: lab-forge not better | 3.75 vs 4.75 | 4.94 vs 4.60 | no |
| Task tokens within ±15% | +3% | +30% | no |
| Deploy costs 40-100k tokens per project | 48-90k | 689k | no |
| Overall quality a tie (±2 of 30) | 25.0 vs 24.9 | 27.2 vs 25.4 | yes |
| LLM project won by lab-forge | A won c2 | 6/6 repeats | yes |

## Objective metrics

| Metric | v04 | bare |
|---|---|---|
| Solved, hidden checks | 21/24 | 24/24 |
| Claimed done but check fails (committed, not solved) | 3 | 0 |
| pytest red after step | 0 | 0 |
| Task tokens, k (all steps except deploy) | 11041.7 | 8508.0 |
| Tokens per solved task, k | 525.8 | 354.5 |
| Cost per solved task, $ | 0.3 | 0.3 |
| Task time, min | 125.8 | 79.7 |
| Deploy tokens per project, k | 689.3 | — |
| Python lines changed (no AI files) | 2541 | 2858 |
| All lines changed (no AI files) | 3289 | 3389 |
| Largest new .py file, lines | 115 | 83 |
| Tests added | 99 | 129 |
| Files changed outside task scope | 2 | 4 |
| Coding steps committed straight to main | 0/24 | 24/24 |
| Coding steps left uncommitted | 0 | 0 |
| Ruff errors in changed files | 27 | 44 |
| Imports that do not resolve | 0 | 0 |
| Questions in coding-step replies | 0 | 0 |
| Files written during read-only question | 0 | 0 |
| Tune phrase applied in next session | 5/12 | 0/12 |
| Style stability across repeats (0-1) | 0.4 | 0.7 |
| Tool calls per solved task | 14.8 | 11.5 |
| Weighted tokens per solved task, k (cache read x0.1, write x1.25) | 121.0 | 81.2 |
| Bare `pytest` green after step | 24/24 | 14/24 |
| Mutants killed by the agent's tests | 18/24 | 7/15 |

## Spread over repeats (mean ± SE)

| Metric | v04 | bare |
|---|---|---|
| Tokens per solved task, k | 537.43 ± 72.66 (n=3) | 354.50 ± 32.95 (n=3) |
| Cost per solved task, $ | 0.35 ± 0.03 (n=3) | 0.25 ± 0.00 (n=3) |
| code sum of 30 | 27.17 ± 0.56 (n=3) | 25.40 ± 0.18 (n=3) |
| weighted code score, 1-5 | 4.58 ± 0.06 (n=3) | 4.32 ± 0.03 (n=3) |

## Blind review (24 verdicts, 1-5)

| Criterion | v04 | bare |
|---|---|---|
| clarity | 4.1 | 3.7 |
| code:bloat | 4.5 | 4.1 |
| code:correctness | 4.5 | 4.4 |
| code:methodology | 4.9 | 4.7 |
| code:optimality | 4.4 | 4.1 |
| code:practices | 4.4 | 3.7 |
| code:scope | 4.3 | 4.5 |
| code:success | 4.9 | 4.6 |
| code:tests | 4.4 | 4.1 |
| question:accuracy | 4.5 | 4.4 |
| question:completeness | 4.3 | 4.4 |
| question:conciseness | 3.8 | 3.7 |
| question:usefulness | 4.4 | 4.2 |
| questions | 4.5 | 4.5 |
| **code sum of 30** | 27.2 | 25.4 |
| **weighted code score, 1-5** | 4.6 | 4.3 |

## Winners by case and repeat

| case-repeat | steps…, overall |
|---|---|
| churn-r1-v04-bare | tie, tie, v04, tie |
| churn-r2-v04-bare | v04, v04, bare, v04 |
| churn-r3-v04-bare | v04, v04, bare, v04 |
| encoders-r1-v04-bare | v04, tie, v04, v04 |
| encoders-r2-v04-bare | v04, v04, tie, v04 |
| encoders-r3-v04-bare | tie, tie, tie, v04 |
| optuna-r1-v04-bare | tie, v04, tie, v04 |
| optuna-r2-v04-bare | bare, v04, tie, tie |
| optuna-r3-v04-bare | tie, v04, bare, tie |
| rparse-r1-v04-bare | v04, v04, tie, v04 |
| rparse-r2-v04-bare | v04, v04, v04, v04 |
| rparse-r3-v04-bare | v04, v04, v04, v04 |

X/Y order changed the winner in 12 of 48 calls; those count as ties.
