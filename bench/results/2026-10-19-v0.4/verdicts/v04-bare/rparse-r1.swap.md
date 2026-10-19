Mutation results are now clean and I have everything needed. Summary of what the runs showed before the verdict:

- Both evals run offline and both suites pass 19 tests via `python -m pytest`. Bare `pytest` from Y's root fails to collect (`No module named 'rparse'`) because Y set no `pythonpath`; X's works.
- Ruff: only style-rule findings on both; Y additionally has an unused import and unsorted imports in its test file.
- Mutations: neither side's P1 tests pin the F1 formula (replacing F1 with precision survives) or the total-match value check. X's P2 tests caught all six mutations; Y's P2 tests missed broken `unit_price`/`quantity` scoring in `field_hits`, and removing Y's fence handling changed nothing because the brace grep makes it redundant.

## Scores

| Step | Metric | X | Y |
|---|---|---|---|
| P1 | success / correctness / practices | 4 / 4 / 4 | 3 / 3 / 3 |
| P1 | optimality / bloat / scope | 3 / 3 / 3 | 4 / 4 / 4 |
| P1 | methodology / tests | 4 / 3 | 4 / 3 |
| P2 | success / correctness / practices | 5 / 4 / 5 | 5 / 4 / 4 |
| P2 | optimality / bloat / scope | 5 / 5 / 5 | 4 / 4 / 5 |
| P2 | methodology / tests | 4 / 5 | 4 / 3 |
| P3 | accuracy / completeness / conciseness / usefulness | 5 / 4 / 4 / 5 | 4 / 4 / 4 / 4 |
| — | clarity / questions | 4 / 5 | 4 / 4 |

## Key defects

**X**
- `rparse/parser.py:29`: `client` is required, so the requested `parse_receipt(text)` signature is not honoured; the reply blames an external rule rather than the spec.
- `rparse/parser.py:21-26`: fence stripping only works when the fence is the whole reply. "Here you go:\n```json…```" fails all three attempts (probed).
- `rparse/eval.py:113-136`: baseline gating, `--promote`, run logs, cost and latency were not asked for in P1; `tests/test_eval.py:37,61` write run files into the repo's `runs/` during tests.
- `tests/test_eval.py:12-18`: the F1 case has P = R, so a broken F1 formula passes; no test checks a wrong total is counted as a miss.
- P3: says a new golden file just needs `pytest`, but `tests/test_eval.py:66` asserts exactly 8 cases and will fail.

**Y**
- `pyproject.toml`: no `pythonpath`, so bare `pytest` cannot import the package.
- `rparse/eval.py:17-18`: the item-F1 key omits `unit_price`; an item with a wrong unit price counts as a true positive (probed).
- `rparse/parser.py:42-45`: hand-rolled validation accepts `{}` as a valid empty receipt with `total=None`; money is `float`.
- `rparse/client.py:30,52`: `_SKIP.search` drops any line containing "card", "tax", "tip"… so "Cardamom 2.00" vanishes (probed, acknowledged in reply).
- `tests/test_rparse.py:112-124`: per-field tests do not detect broken `unit_price` or `quantity` scoring; `test_eval_scores_fake_client:53` asserts F1 < 1.0, so improving the fake breaks the suite.
- P3: `eval.py:56-59` is off by one (the try/except is 57-60); "nothing else needs registering" is contradicted by the receipt-count assertion it admits it did not check.

## Winners

- **P1: X.** Pydantic schema validation, Decimal money, a strict four-field F1, prompt versioning and working bare `pytest` outweigh X's scope creep and the required-client deviation. Y's F1 silently ignores unit price and its suite does not collect under plain `pytest`.
- **P2: X.** A 22-line parser diff that every mutation caught, plus a hand-computed field-accuracy test. Y's design is sound and more prose-tolerant, but its field-accuracy tests are bounds checks that miss broken scoring.
- **P3: X**, narrowly. All refs verified correct and the baseline-promote step is genuinely needed; both missed the hard-coded receipt-count assertion.
- **Overall: X.** Better eval soundness and LLM-app hygiene, at the cost of some unrequested harness machinery in P1.

```json
{"X": {"P1": {"success": 4, "correctness": 4, "practices": 4, "optimality": 3, "bloat": 3, "scope": 3, "methodology": 4, "tests": 3}, "P2": {"success": 5, "correctness": 4, "practices": 5, "optimality": 5, "bloat": 5, "scope": 5, "methodology": 4, "tests": 5}, "P3": {"accuracy": 5, "completeness": 4, "conciseness": 4, "usefulness": 5}, "clarity": 4, "questions": 5}, "Y": {"P1": {"success": 3, "correctness": 3, "practices": 3, "optimality": 4, "bloat": 4, "scope": 4, "methodology": 4, "tests": 3}, "P2": {"success": 5, "correctness": 4, "practices": 4, "optimality": 4, "bloat": 4, "scope": 5, "methodology": 4, "tests": 3}, "P3": {"accuracy": 4, "completeness": 4, "conciseness": 4, "usefulness": 4}, "clarity": 4, "questions": 4}, "winner": {"P1": "X", "P2": "X", "P3": "X", "overall": "X"}}
```