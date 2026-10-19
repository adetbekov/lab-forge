**Scores**

| Step | Dim | X | Y |
|---|---|---|---|
| P1 | success / correctness / practices / optimality / bloat / scope / methodology / tests | 5/5/4/4/5/4/5/4 | 5/5/4/4/4/4/5/3 |
| P2 | success / correctness / practices / optimality / bloat / scope / methodology / tests | 5/4/4/5/5/4/5/4 | 5/4/4/3/4/5/5/3 |
| P3 | accuracy / completeness / conciseness / usefulness | 4/4/4/4 | 3/4/4/4 |
| — | clarity / questions | 4/4 | 4/4 |

Both sides: `python -m churn.train`, bare `pytest`, `python -m pytest` and `ruff check .` all pass from the snapshot root (X: 8 tests, Y: 4). Reverse-applying P2 reproduces each P1 state, which also runs and passes. Methodology is sound on both: stratified test split first, validation carved from train only, scaler/encoder inside pipelines, calibrator fitted by 5-fold CV inside the fit rows, threshold chosen on validation, test used only for final metrics, same seed and split for both models.

**X defects**
- `churn/train.py:41` reads `params.toml` relative to the cwd, so `run()` fails from any other directory (confirmed: `FileNotFoundError`). Only project-root invocation was required, so this is a robustness nit.
- `churn/train.py:57` silently replaces the uncalibrated GB with the calibrated CV ensemble under the same `roc_auc.gradient_boosting` key. The "existing ROC-AUC" now measures a different model, and the raw-vs-calibrated comparison is lost (raw 0.7921 vs calibrated 0.7909 when I recomputed).
- Tests call `run()` six times (35 s). A threshold-on-test leak mutant survives, though that is hard to test on any side.
- P3: `params.toml:13-14` / `12-14` for calibration is off by one (file ends at line 13). Other refs verified correct (config.py:3-6, train.py:45-47, 50-52, 53, 54, 59, 60, 33-37, params.toml:5-9).

**Y defects**
- `churn/train.py:23-25` threshold search calls `f1_score` once per unique score: 3.1 s on 1000 validation rows here, 11.8 s on 1000 unique scores. Combined with fitting GB separately and inside the calibrator, a run takes ~20 s versus ~8 s for X.
- `tests/test_train.py:44-47` is named "hyperparameters come from config" but only changes `val_size`. Dropping `**cfg["gboost"]` at `train.py:53` passes the whole suite (verified). X's equivalent test caught the same mutation.
- `tests/test_train.py:37-41` expects exactly 0.5, so a degenerate `return 0.5` passes; a lowest-candidate mutant was caught. `tests/test_train.py:19` asserts sklearn's `roc_auc_score` on literal data, testing nothing in the project. `:28` echoes config sizes.
- `n_train` silently changes meaning from 4000 train rows to 3000 fit rows (`train.py:58`), while X renamed to `n_fit`.
- P3: three config refs off by one: `cv = 5` is at `config.toml:18` not `:16`; `[gboost]` is `:11-14` not `:12-15`; `[calibration]` is `:16-18` not `:17-19`. All `train.py` refs verified correct (32-34, 36-38, 56, 65, 68, 70, 21-25, 53).
- Positive: keeps raw and calibrated GB AUC side by side, `handle_unknown="ignore"`, config-relative paths via `ROOT`.

Both final messages lead with the result, use tables, and flag the baseline shift and threshold noise honestly. Neither deferred a requirement; the "say if you want a push/PR" and "set git identity if you want" lines are reasonable.

**Winners**
- P1: X. Equivalent delivery, but X's four tests all exercise project code and include reproducibility, while Y's two tests partly test sklearn and echo config.
- P2: X. Same methodology, but X's vectorized threshold search and real hyperparameter test beat Y's quadratic search and a config test that misses its own target. Y's retained raw AUC is the one point in its favour.
- P3: X. Both are useful and similarly complete; X has one off-by-one ref, Y has three.
- Overall: X. Leaner code, faster runs, tests that actually fail when behaviour breaks, and more accurate references.

```json
{"X": {"P1": {"success": 5, "correctness": 5, "practices": 4, "optimality": 4, "bloat": 5, "scope": 4, "methodology": 5, "tests": 4}, "P2": {"success": 5, "correctness": 4, "practices": 4, "optimality": 5, "bloat": 5, "scope": 4, "methodology": 5, "tests": 4}, "P3": {"accuracy": 4, "completeness": 4, "conciseness": 4, "usefulness": 4}, "clarity": 4, "questions": 4}, "Y": {"P1": {"success": 5, "correctness": 5, "practices": 4, "optimality": 4, "bloat": 4, "scope": 4, "methodology": 5, "tests": 3}, "P2": {"success": 5, "correctness": 4, "practices": 4, "optimality": 3, "bloat": 4, "scope": 5, "methodology": 5, "tests": 3}, "P3": {"accuracy": 3, "completeness": 4, "conciseness": 4, "usefulness": 4}, "clarity": 4, "questions": 4}, "winner": {"P1": "X", "P2": "X", "P3": "X", "overall": "X"}}
```