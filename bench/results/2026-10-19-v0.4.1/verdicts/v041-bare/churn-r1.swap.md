**Scores**

| | X P1 | Y P1 | X P2 | Y P2 |
|---|---|---|---|---|
| success | 5 | 5 | 5 | 5 |
| correctness | 5 | 5 | 4 | 4 |
| practices | 4 | 4 | 4 | 3 |
| optimality | 4 | 5 | 4 | 4 |
| bloat | 4 | 5 | 4 | 5 |
| scope | 3 | 4 | 4 | 5 |
| methodology | 5 | 5 | 3 | 4 |
| tests | 4 | 4 | 3 | 3 |

| | X | Y |
|---|---|---|
| P3 accuracy / completeness / conciseness / usefulness | 5 / 5 / 3 / 4 | 4 / 5 / 4 / 4 |
| clarity | 4 | 4 |
| questions | 4 | 5 |

Verified by running: both snapshots run `python -m churn.train` from the root with no install, bare `pytest` passes (X 6, Y 5), reconstructed P1 states also pass (X 4, Y 3). Ruff: X clean and formatted; Y fails two I001 import-order errors and three files are unformatted after P2 (`churn/train.py:11`, `tests/test_churn.py:6-7`).

**X defects**
- `churn/train.py:80-82` (P2): logreg is fitted on all 4000 training rows, gboost on 3200. The two compared models no longer share a training set, and `n_train: 4000` in the JSON misdescribes what gboost saw. X flagged it but chose it anyway.
- `tests/test_train.py:50-56`: the config test changes `n_estimators` and `cv` together. Mutating train.py to ignore `cfg["gboost"]` entirely still passes all 6 tests. Dropping calibration and picking the threshold on test also pass undetected.
- P1 scope: unrequested CSV dump to `data/churn.csv` (`train.py:56-58`), timestamped `runs/<id>/` directories, committed `metrics/baseline.json`, AGENTS.md edit.
- P3 answer leans on "invariant P1/P2/P3" and AGENTS.md references that mean nothing to the reader.

**Y defects**
- `tests/test_churn.py:51-58`: the "config drives hyperparameters" test only asserts `n_val == 400`. Ignoring `cfg["gradient_boosting"]` passes all 5 tests. Dropping calibration and the test-set threshold leak also survive.
- `churn/config.json:3`: isotonic calibration with cv=5 on 3000 fit rows means each calibrator learns on 600 rows; sigmoid is the safer default at this size. Threshold lands at 0.17 with precision 0.32.
- `churn/train.py:45`: `test_size=0.2` stays hardcoded while everything else moved to config (not strictly asked, but inconsistent).
- Ruff/format regressions after P2, noted above.
- P3 refs: `handle_unknown` is at `train.py:24`, not `:20`; pipelines are `50-56`, not `51-56`. All other refs checked (45, 47-49, 58, 70, 72, 74-77, config 2, 5-10) are exact.

**Winners**

- **P1: Y.** Both are correct, leakage-free and tested. Y is smaller and stays inside the ask; X adds run directories, a data dump and a committed baseline nobody requested. X's signal test (month-to-month vs two-year churn rate) is the one place X's tests are meaningfully stronger.
- **P2: Y.** Y fits both models on the same fit split and uses validation only for the threshold, which is the clean design. X's asymmetric training sets break the comparability it set up in P1. Y's ruff and isotonic choices cost it, but not enough to overturn the methodology edge. Both test suites miss the same three mutants.
- **P3: X.** Every X reference I checked is exact (config.toml 1-3, 13-16, 18-20; train.py 26-34, 42, 47-51, 61-68, 78, 80-98) and it discloses the logreg/gboost asymmetry. Y is clearer prose but two line refs are off.
- **Overall: Y**, narrowly. Y delivers the leaner, more defensible pipeline with a fair model comparison and nothing out of scope. X writes cleaner, lint-clean code and a more precise answer, but its P1 scope creep and P2 training-set asymmetry are the more consequential defects.

```json
{"X": {"P1": {"success": 5, "correctness": 5, "practices": 4, "optimality": 4, "bloat": 4, "scope": 3, "methodology": 5, "tests": 4}, "P2": {"success": 5, "correctness": 4, "practices": 4, "optimality": 4, "bloat": 4, "scope": 4, "methodology": 3, "tests": 3}, "P3": {"accuracy": 5, "completeness": 5, "conciseness": 3, "usefulness": 4}, "clarity": 4, "questions": 4}, "Y": {"P1": {"success": 5, "correctness": 5, "practices": 4, "optimality": 5, "bloat": 5, "scope": 4, "methodology": 5, "tests": 4}, "P2": {"success": 5, "correctness": 4, "practices": 3, "optimality": 4, "bloat": 5, "scope": 5, "methodology": 4, "tests": 3}, "P3": {"accuracy": 4, "completeness": 5, "conciseness": 4, "usefulness": 4}, "clarity": 4, "questions": 5}, "winner": {"P1": "Y", "P2": "Y", "P3": "X", "overall": "Y"}}
```