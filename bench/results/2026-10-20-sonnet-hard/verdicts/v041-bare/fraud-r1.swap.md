## Scores

| | X P1 | Y P1 | X P2 | Y P2 |
|---|---|---|---|---|
| success | 4 | 4 | 5 | 5 |
| correctness | 5 | 4 | 5 | 4 |
| practices | 4 | 4 | 4 | 4 |
| optimality | 4 | 4 | 4 | 4 |
| bloat | 4 | 4 | 4 | 4 |
| scope | 4 | 3 | 4 | 4 |
| methodology | 5 | 5 | 5 | 5 |
| tests | 5 | 4 | 5 | 4 |

| | X P3 | Y P3 |
|---|---|---|
| accuracy | 4 | 3 |
| completeness | 5 | 4 |
| conciseness | 4 | 4 |
| usefulness | 5 | 4 |

Clarity: X 5, Y 4. Questions: X 5, Y 4.

## What I ran

Both snapshots: `python -m fraud.train`, `--as-of 2024-09-01`, pytest (bare and `-m`), ruff. Both train runs succeed and ruff is clean. X fails under bare `pytest` with "No module named fraud" since it has no pyproject or conftest; `python -m pytest` passes 9 tests. Y passes 10 tests both ways.

I brute-forced every history feature against a naive per-row filter on random data with many same-user same-timestamp ties, brute-forced threshold optimality over 300 random cost settings, and ran six or seven mutations per side. Every mutation on both sides was caught by at least one test.

## X defects

- `fraud/train.py:29-33` and the whole pipeline have no bare-pytest path setup, so `pytest` from the root errors. Minor but it was the explicit test command.
- `fraud/train.py:105-108` records `n_train` twice (top level and in `meta`). Trivial duplication.
- Question refs `config.toml:3-4` and `config.toml:7-8` are off by one (those lines are the section headers). All other refs verified correct.

## Y defects

- `fraud/features.py:13-24` treats same-timestamp rows as history by input order. With ties the output differs from strict point-in-time and changes when rows are shuffled (44 of 44 tied rows mismatched my brute force). The generator never produces ties, so no practical leak, but the guarantee is weaker and order-dependent.
- `fraud/train.py:39-41` only tries observed scores, so "flag nothing" is never a candidate. Suboptimal in 127 of 300 random cost trials, though essentially never at 50:1.
- `fraud/train.py:29-30` returns an empty train set when `round(n*frac)` is 0 (tiny `--as-of` windows).
- P1 scope: committed an unrequested `metrics/baseline.json`, added `reports/` to `.gitignore` so the requested metrics file is never committed, and left the baseline stale after P2.
- `tests/test_fraud.py:112-122` deletes and rewrites the real `reports/metrics.json` and hardcodes 12800.
- Question answer cites `fraud/features.py:112-129` and `config.toml:154-156`; those files are 27 and 24 lines long. It also says it did not check for a leakage test although one exists.
- Gradient boosting PR-AUC is 0.51 against 0.72 for logistic regression. Not a bug, but a weak baseline that Y flagged without investigating.

## Winners

**P1: X.** Both meet every requirement, but X's features are tie-safe and shuffle-invariant with a test proving it, and X added nothing unrequested beyond a few extra features. Y shipped a stale baseline artifact and gitignored the requested report.

**P2: X.** Both choose the threshold on validation only, fit scalers and models on train only, and keep `--as-of` rows out of everything. X's threshold search includes the flag-nothing option and its split handles edge sizes.

**P3: X.** X's references are correct apart from two off-by-one config lines. Y has two line references that cannot exist and understates its own test coverage.

**Overall: X.** Same size (about 340 lines each), same methodology, but X is more correct on ties and threshold edge cases, stays within scope, and its answer is verifiable. Y's one clear advantage is that bare `pytest` works.

```json
{"X": {"P1": {"success": 4, "correctness": 5, "practices": 4, "optimality": 4, "bloat": 4, "scope": 4, "methodology": 5, "tests": 5}, "P2": {"success": 5, "correctness": 5, "practices": 4, "optimality": 4, "bloat": 4, "scope": 4, "methodology": 5, "tests": 5}, "P3": {"accuracy": 4, "completeness": 5, "conciseness": 4, "usefulness": 5}, "clarity": 5, "questions": 5}, "Y": {"P1": {"success": 4, "correctness": 4, "practices": 4, "optimality": 4, "bloat": 4, "scope": 3, "methodology": 5, "tests": 4}, "P2": {"success": 5, "correctness": 4, "practices": 4, "optimality": 4, "bloat": 4, "scope": 4, "methodology": 5, "tests": 4}, "P3": {"accuracy": 3, "completeness": 4, "conciseness": 4, "usefulness": 4}, "clarity": 4, "questions": 4}, "winner": {"P1": "X", "P2": "X", "P3": "X", "overall": "X"}}
```