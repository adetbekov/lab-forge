## Scores

| Step | Metric | X | Y |
|---|---|---|---|
| P1 | success / correctness / practices | 5 / 5 / 4 | 3 / 3 / 4 |
| P1 | optimality / bloat / scope | 5 / 5 / 4 | 3 / 3 / 4 |
| P2 | success / correctness / practices | 5 / 5 / 4 | 4 / 4 / 5 |
| P2 | optimality / bloat / scope | 4 / 5 / 5 | 4 / 4 / 4 |
| P3 | accuracy / completeness / conciseness / usefulness | 5 / 5 / 4 / 4 | 5 / 5 / 4 / 5 |
| - | clarity / questions | 4 / 5 | 4 / 3 |

**Runs.** X runs from the root with no install and reproduces its committed metrics exactly. Pytest gives 5 passed and ruff is clean. Y runs only because of an untracked `.pth` in the venv that points at another workspace's `src/`. Without it: `ModuleNotFoundError: No module named 'churn'`. With `src` on the path, Y reproduces its metrics, pytest gives 5 passed and ruff is clean.

**Method.** Both are leakage-free. Preprocessing sits inside a `Pipeline`, sigmoid calibration (5-fold CV) uses the fit split only, the threshold is tuned on validation only, and test is used only for scoring.

## Key defects

**X**
- `churn/train.py:58-65`: GBM hyperparameters are mapped key by key, so adding one (for example `max_depth`) needs a code edit.
- `params.toml:15-23`: calibration and threshold settings are mixed into the GBM section. `threshold_grid=100` only restates sklearn's default.
- P1 adds a dummy baseline and average precision that nobody asked for (`train.py:49-51,111`).

**Y**
- The required command does not work (P1). Because of the src layout, `python -m churn.train` fails without `pip install -e .`. Y patched the venv outside the repo and left the install step to the user.
- Stale-data bug: `src/churn/train.py:28-32` regenerates the CSV only when it is missing. After a change to `seed` or `n_rows` it silently trains on old data. Y flagged this but did not fix it.
- Extra structure nobody asked for: a 13-line wrapper in `split.py`, plus a CLI and CSV caching in `generate.py:72-91`. The total is about 426 lines against X's 352.
- `params.toml:30`: P2 renames the run, so `python -m churn.train` writes `gbm_calibrated_f1.json` and `baseline.json` no longer matches what the command produces.
- What Y does better: `**params["gbm"]` pass-through (`train.py:42`) and a good `tests/test_evaluate.py`.

**P3.** I checked about 12 refs on each side, and all are correct. Y is a bit more useful: it explains the `[gbm]` pass-through and warns that the baseline comparison is skewed by training size (4000 vs 3200 rows).

## Winners

- **P1: X.** The required command works with no install, the code is leaner, and there is no stale-cache trap.
- **P2: X.** Both implement the same sound calibration and threshold method. Y's config design is better, but it still depends on the venv hack and moves the metrics output to a new file.
- **P3: Y,** narrowly. Its answer is tighter and adds a practical caveat.
- **Overall: X.** X meets every explicit requirement out of the box with less code and equally sound ML. Y is more modular, but it pushes a setup step onto an unavailable user and adds an unrequested cache with a real stale-data bug.

```json
{"X": {"P1": {"success": 5, "correctness": 5, "practices": 4, "optimality": 5, "bloat": 5, "scope": 4}, "P2": {"success": 5, "correctness": 5, "practices": 4, "optimality": 4, "bloat": 5, "scope": 5}, "P3": {"accuracy": 5, "completeness": 5, "conciseness": 4, "usefulness": 4}, "clarity": 4, "questions": 5}, "Y": {"P1": {"success": 3, "correctness": 3, "practices": 4, "optimality": 3, "bloat": 3, "scope": 4}, "P2": {"success": 4, "correctness": 4, "practices": 5, "optimality": 4, "bloat": 4, "scope": 4}, "P3": {"accuracy": 5, "completeness": 5, "conciseness": 4, "usefulness": 5}, "clarity": 4, "questions": 3}, "winner": {"P1": "X", "P2": "X", "P3": "Y", "overall": "X"}}
```
