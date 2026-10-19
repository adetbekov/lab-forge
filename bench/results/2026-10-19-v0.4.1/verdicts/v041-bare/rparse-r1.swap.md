All verification is done. Here is the review.

| | X P1 | X P2 | Y P1 | Y P2 |
|---|---|---|---|---|
| success | 4 | 5 | 5 | 5 |
| correctness | 3 | 4 | 4 | 5 |
| practices | 3 | 3 | 4 | 4 |
| optimality | 4 | 4 | 3 | 4 |
| bloat | 4 | 4 | 3 | 4 |
| scope | 5 | 5 | 3 | 4 |
| methodology | 3 | 4 | 4 | 4 |
| tests | 3 | 3 | 4 | 5 |

| P3 | accuracy | completeness | conciseness | usefulness |
|---|---|---|---|---|
| X | 4 | 4 | 4 | 4 |
| Y | 4 | 5 | 4 | 4 |

Clarity: X 4, Y 4. Questions: X 4, Y 4.

**Runs.** Both evals run from the root and report F1 0.93–0.94 with total match 1.0. Both pass 19 tests via `python -m pytest`. Bare `pytest` fails on X with `ModuleNotFoundError: rparse` (no `pythonpath` in `pyproject.toml`, package not installed); Y passes. Ruff defaults: X has one unused import (`tests/test_rparse.py:1`), Y is clean.

**X defects**
- Item F1 key omits unit_price (`rparse/eval.py:17-18`), so an item with a wrong unit price counts as a full match. The "item-level F1" is on 3 of 4 fields.
- Eval tests are range checks on the golden run (`tests/test_rparse.py:50-54`, `:112-116`). Six mutations survived: precision using fn, F1 = precision, total-match ignoring the value, F1 key dropping qty/total, quantity and unit_price accuracy hard-wired to hit. Retry and attempt-count mutations were caught.
- Lax validation: `{"name": null, "quantity": true}` becomes name "None", quantity 1.0 (`rparse/parser.py:37-38`). Fake client drops any line containing "card" or "tax" anywhere (`rparse/client.py:30`), and parses `2 x Latte 7.00` as name "2 x Latte".
- Bare `pytest` does not work from the root.

**Y defects**
- Scope creep in P1: baseline regression gate with exit 1, timestamped `evals/runs/` files, `cost_usd` and `latency_s` in the report, README. `cost_usd` is on the `LLMClient` Protocol (`rparse/client.py:7`), so every client, including test doubles, must carry it. `eval.py` is 169 lines for an 8-receipt scorer.
- A receipt with no total line is returned as total 0 rather than absent (`rparse/fake_client.py:31`), since `Receipt.total` is required.
- One mutation survived: F1 key reduced to name only (`rparse/eval.py:59-60`) because the hand-computed test uses identical numbers across items.
- No prose-around-JSON fallback without a fence; that was not requested, so minor.

**P3 answers.** X: 14 of 15 refs checked are exact; `eval.py:56-59` is off by one (the try/except is 57-60). X warns that tests may hard-code the count but did not check; `tests/test_rparse.py:52` asserts 8, so adding a receipt does break a test. Y: refs to `parser.py` and `prompts.py` all exact; `eval.py:144` is 145, `eval.py:152-155` is 154-157. Y covers the baseline update step, which its design requires, and its test uses `>= 8` so the deferral is harmless.

**Winners.** P1: Y. Y's F1 covers all four fields, uses pydantic validation, has versioned prompts, works under bare `pytest`, and its scorer tests catch formula bugs; this outweighs the unrequested baseline machinery. P2: Y. Both implement retry correctly, but Y's tests catch every fence, retry, attempt-count and per-field mutation, while X's field-accuracy tests miss two of them. P3: tie. Overall: Y, for a sounder eval and tests that actually guard the behaviour, at the cost of a heavier eval module.

```json
{"X": {"P1": {"success": 4, "correctness": 3, "practices": 3, "optimality": 4, "bloat": 4, "scope": 5, "methodology": 3, "tests": 3}, "P2": {"success": 5, "correctness": 4, "practices": 3, "optimality": 4, "bloat": 4, "scope": 5, "methodology": 4, "tests": 3}, "P3": {"accuracy": 4, "completeness": 4, "conciseness": 4, "usefulness": 4}, "clarity": 4, "questions": 4}, "Y": {"P1": {"success": 5, "correctness": 4, "practices": 4, "optimality": 3, "bloat": 3, "scope": 3, "methodology": 4, "tests": 4}, "P2": {"success": 5, "correctness": 5, "practices": 4, "optimality": 4, "bloat": 4, "scope": 4, "methodology": 4, "tests": 5}, "P3": {"accuracy": 4, "completeness": 5, "conciseness": 4, "usefulness": 4}, "clarity": 4, "questions": 4}, "winner": {"P1": "Y", "P2": "Y", "P3": "tie", "overall": "Y"}}
```