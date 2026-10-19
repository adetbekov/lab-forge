**Scores**

| Step | Metric | X | Y |
|---|---|---|---|
| P1 | success / correctness / practices | 5 / 4 / 4 | 3 / 3 / 3 |
| P1 | optimality / bloat / scope | 3 / 3 / 3 | 4 / 5 / 5 |
| P1 | methodology / tests | 5 / 5 | 4 / 2 |
| P2 | success / correctness / practices | 5 / 5 / 5 | 4 / 4 / 4 |
| P2 | optimality / bloat / scope | 4 / 4 / 4 | 4 / 4 / 5 |
| P2 | methodology / tests | 5 / 5 | 4 / 3 |
| P3 | accuracy / completeness / conciseness / usefulness | 4 / 4 / 4 / 4 | 5 / 5 / 4 / 4 |
| — | clarity / questions | 4 / 4 | 4 / 4 |

**Verified runs.** X: eval exits 0 with all deltas 0.0, bare `pytest` and `python -m pytest` both 19 passed. Y: eval prints F1 0.938, `python -m pytest` 19 passed, but bare `pytest` from the root fails with `ModuleNotFoundError: No module named 'rparse'` (no `pythonpath` in `pyproject.toml:7-8`, package not installed). Ruff flags 2 trivial items in X, 9 in Y including an unused import (`tests/test_rparse.py:1`).

**X defects**
- Scope creep in P1: baseline regression gate, timestamped run logs, cost and latency fields, `PROMPT_VERSION` reporting (`rparse/eval.py:24-27, 47-53, 149-164`). None requested; eval.py is 169 lines versus Y's 93.
- `cost_usd` is required on the `LLMClient` protocol (`rparse/client.py:7`), so every test double must declare it.
- `_key` reimplements `_norm` inline (`rparse/eval.py:59-64`).
- P3 refs: parser refs all exact, but `eval.py:144` is a blank line (load is 145), `152-155` should be 154-157, `158-162` should be 161-164.

**Y defects**
- Tests are weak: replacing the F1 formula with `f1 = p` (`rparse/eval.py:69`), making unit_price or quantity accuracy always true (`:46-47`), or reducing the item key to name only (`:18`) all leave 19 tests passing. `test_eval_scores_fake_client` and `test_field_accuracy` only assert ranges on the fake's output (`tests/test_rparse.py:53, 115-116`) and lock in the fake's known miss, so improving the fake breaks tests.
- F1 key omits unit_price (`rparse/eval.py:17-18`), so a wrong unit price still counts as a matched item.
- Validation is lenient: `{}` is accepted as an empty receipt with no error, and `"quantity": true` becomes 1.0 (`rparse/parser.py:42-45`). X rejects both via pydantic.
- Per-field accuracy is name-gated (`rparse/eval.py:41-43`): a misspelled name zeroes all four fields. Y flagged it; X aligns leftovers by order and measures each field.
- `_FENCE` is redundant with the brace search (`rparse/parser.py:14-21`); removing it changes nothing. No test uses multi-line JSON, so dropping `re.S` at line 21 also passes.
- No prompt versioning; prompt lives in `client.py:11-16`.
- P3: refs accurate (eval.py:56-59 is one line off), but it hedged on whether tests assert the receipt count instead of checking. They do (`tests/test_rparse.py:52`), so a user following its instructions hits a failing test.

**Winners**
- P1: X. Y is leaner and well-scoped, but bare `pytest` does not run, its validation lets `{}` through, and its eval tests cannot detect a broken F1. X over-delivers (regression gate, run logs) yet every mutation I tried was caught by a hand-computed test.
- P2: X. Both strip fences, feed the error back and raise a clear error after N attempts, with tests on the retry path. X's per-field metric is independently tested and pydantic does the validation; Y's unit_price and quantity accuracies are untested.
- P3: Y. More refs, nearly all exact, and a fuller walk through each ParseError branch and the aggregated final message. X has three off-by-a-few eval refs. Both left a trivial test check to the unavailable user.
- Overall: X. Stronger correctness, schema validation, prompt versioning and genuinely falsifying tests outweigh its unrequested eval machinery. Y's economy is real but rests on tests that mostly echo the fake client.

```json
{"X": {"P1": {"success": 5, "correctness": 4, "practices": 4, "optimality": 3, "bloat": 3, "scope": 3, "methodology": 5, "tests": 5}, "P2": {"success": 5, "correctness": 5, "practices": 5, "optimality": 4, "bloat": 4, "scope": 4, "methodology": 5, "tests": 5}, "P3": {"accuracy": 4, "completeness": 4, "conciseness": 4, "usefulness": 4}, "clarity": 4, "questions": 4}, "Y": {"P1": {"success": 3, "correctness": 3, "practices": 3, "optimality": 4, "bloat": 5, "scope": 5, "methodology": 4, "tests": 2}, "P2": {"success": 4, "correctness": 4, "practices": 4, "optimality": 4, "bloat": 4, "scope": 5, "methodology": 4, "tests": 3}, "P3": {"accuracy": 5, "completeness": 5, "conciseness": 4, "usefulness": 4}, "clarity": 4, "questions": 4}, "winner": {"P1": "X", "P2": "X", "P3": "Y", "overall": "X"}}
```