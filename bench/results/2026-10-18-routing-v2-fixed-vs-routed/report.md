# lab-forge bench: fixed vs routed

## First-round conclusions: 1/3 reproduced

| Conclusion | First round | This run | Holds |
|---|---|---|---|
| Less code with lab-forge (≤ −15%) | −30% | -6% | no |
| Blind bloat score higher with lab-forge | 4.75 vs 3.6 | — vs — | — |
| Explicit requirements: lab-forge not better | 3.75 vs 4.75 | — vs — | — |
| Task tokens within ±15% | +3% | -33% | no |
| Deploy costs 40-100k tokens per project | 48-90k | 57k | yes |
| Overall quality a tie (±2 of 30) | 25.0 vs 24.9 | 0.0 vs 0.0 | — |
| LLM project won by lab-forge | A won c2 | 0/0 repeats | — |

## Objective metrics

| Metric | fixed | routed |
|---|---|---|
| Solved, hidden checks | 16/16 | 16/16 |
| Claimed done but check fails (committed, not solved) | 0 | 0 |
| pytest red after step | 0 | 0 |
| Task tokens, k (all steps except deploy) | 939.4 | 1397.3 |
| Tokens per solved task, k | 58.7 | 87.3 |
| Cost per solved task, $ | — | — |
| Task time, min | 0.0 | 0.0 |
| Deploy tokens per project, k | 57.1 | 57.1 |
| Python lines changed (no AI files) | 2056 | 2191 |
| All lines changed (no AI files) | 2502 | 2571 |
| Largest new .py file, lines | 136 | 151 |
| Tests added | 52 | 71 |
| Files changed outside task scope | 4 | 4 |
| Coding steps committed straight to main | 0/16 | 0/16 |
| Coding steps left uncommitted | 0 | 0 |
| Ruff errors in changed files | 0 | 0 |
| Imports that do not resolve | 0 | 3 |
| Questions in coding-step replies | 0 | 0 |
| Files written during read-only question | 0 | 0 |
| Tune phrase applied in next session | 0/0 | 0/0 |
| Style stability across repeats (0-1) | 0.5 | 0.5 |
