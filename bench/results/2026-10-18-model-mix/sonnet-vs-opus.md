# lab-forge bench: sonnet vs opus

## Objective metrics

| Metric | sonnet | opus |
|---|---|---|
| Solved, hidden checks | 8/8 | 8/8 |
| Claimed done but check fails (committed, not solved) | 0 | 0 |
| pytest red after step | 0 | 0 |
| Task tokens, k (all steps except deploy) | 635.9 | 862.4 |
| Tokens per solved task, k | 79.5 | 107.8 |
| Deploy tokens per project, k | 58.4 | 58.4 |
| Python lines changed (no AI files) | 858 | 1260 |
| All lines changed (no AI files) | 1135 | 1505 |
| Largest new .py file, lines | 104 | 194 |
| Tests added | 31 | 27 |
| Files changed outside task scope | 2 | 2 |
| Coding steps committed straight to main | 0/8 | 0/8 |
| Coding steps left uncommitted | 0 | 0 |
| Ruff errors in changed files | 1 | 0 |
| Imports that do not resolve | 0 | 0 |
| Questions in coding-step replies | 0 | 0 |
| Files written during read-only question | 0 | 0 |
| Tune phrase applied in next session | 4/4 | 4/4 |

## Blind review (4 verdicts, 1-5)

| Criterion | sonnet | opus |
|---|---|---|
| clarity | 4 | 4 |
| code:bloat | 4.6 | 4.4 |
| code:correctness | 3.9 | 4.9 |
| code:optimality | 4.4 | 4.6 |
| code:practices | 4.1 | 4.6 |
| code:scope | 4.9 | 4.8 |
| code:success | 4.6 | 5 |
| question:accuracy | 4.5 | 5 |
| question:completeness | 4.2 | 5 |
| question:conciseness | 4 | 4 |
| question:usefulness | 4.2 | 5 |
| questions | 5 | 5 |
| **code sum of 30** | 26.5 | 28.2 |

## Winners by case and repeat

| case-repeat | steps…, overall |
|---|---|
| churn-r1 | opus, opus, opus, opus |
| encoders-r1 | sonnet, opus, opus, opus |
| optuna-r1 | tie, opus, opus, opus |
| rparse-r1 | opus, opus, tie, opus |

