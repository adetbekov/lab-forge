**Scores**

| | X P1 | X P2 | Y P1 | Y P2 |
|---|---|---|---|---|
| success | 4 | 5 | 4 | 5 |
| correctness | 3 | 4 | 4 | 5 |
| practices | 3 | 4 | 5 | 5 |
| optimality | 4 | 5 | 3 | 4 |
| bloat | 5 | 5 | 3 | 4 |
| scope | 5 | 5 | 3 | 4 |
| methodology | 2 | 3 | 4 | 4 |
| tests | 3 | 3 | 4 | 5 |

P3: X accuracy 4 / completeness 3 / conciseness 4 / usefulness 3. Y 5 / 5 / 4 / 5. Clarity X 4, Y 4. Questions X 5, Y 3.

**Verified runs.** Both evals run and `python -m pytest` passes (X 21, Y 16). Bare `pytest` from X's root fails at collection with `ModuleNotFoundError: rparse` (no `pythonpath` in `pyproject.toml`, package not installed); Y passes. Ruff: both have only alias/sort nits.

**X defects**
- Eval is fitted to the golden set: the reply admits adding `service` to `_SKIP` (`rparse/client.py:29`) to reach 1.000, and `tests/test_eval.py:20-23,45-47` assert exact 1.0. The harness cannot show a gap, and any harder golden receipt breaks three tests.
- `_key` (`rparse/eval.py:15`) strips everything but `[a-z0-9]`, so every Cyrillic item name becomes `""`. `score_items([Молоко],[Хлеб])` returns a true positive. Fatal for a Kazakhstan receipt product.
- `evaluate` (`rparse/eval.py:69`) does not catch `ReceiptParseError`; one receipt that exhausts retries aborts the whole eval.
- Missing `total` is silently replaced by the item sum (`rparse/parser.py:41`), masking model errors in the total-match metric.
- Mutation results: swapping fp/fn in `score_items` survives (test uses symmetric 1,1,1); removing the leftover-pairing branch of `field_hits` (`rparse/eval.py:48-50`) survives. Retry, give-up and fence mutations were caught.
- No prompt versioning, no logging of retries.

**Y defects**
- Signature deviates from the requested `parse_receipt(text)`: client is required (`rparse/parser.py:33`) and P1 defers with "say if you want a default" to an absent user.
- Unrequested machinery in P1: cost tracking, latency, run archiving, baseline delta, `--update-baseline`, README (`rparse/eval.py:25-32,120-147`). `latency_s` in a committed baseline is noise.
- `score([])` raises `ZeroDivisionError` (`rparse/eval.py:92`); precision formula is untested (mutation to `tp/(tp+fn)` survived).
- Fake drops wrapped names (`rparse/client.py:34`), which is deliberate and keeps F1 at 0.9545, so the harness measures something. All four P2 mutations (feedback, fences, leftover pairing, retry loop) were caught.

**Question (P3).** X's refs check out except `eval.py:70` is `score_items`, not the parse call (69). X did not open `tests/test_eval.py`, which is exactly the file whose exact-1.0 asserts make adding a receipt fail, and it omits that the eval aborts on a parse failure. Y's refs (`parser.py:35-38,41,43-48,13,17`, `eval.py:103-106,125,129,145`, `client.py:34`, `test_eval.py:30-32`) all check; it covers eval behaviour on failure, the baseline update and the test gate.

**Winners.** P1: Y. X is leaner and matches the signature, but its eval is tuned to score 1.0, Cyrillic names collapse to one key, and bare `pytest` does not run; Y's eval is honest and schema-validated, at the cost of unrequested baseline and cost plumbing. P2: Y. Both implement retry-with-feedback correctly, but Y's eval survives parse failures, logs attempts, and its tests caught every mutation, while X's leftover-pairing branch is untested. P3: Y, for complete and verified references. Overall: Y.

```json
{"X": {"P1": {"success": 4, "correctness": 3, "practices": 3, "optimality": 4, "bloat": 5, "scope": 5, "methodology": 2, "tests": 3}, "P2": {"success": 5, "correctness": 4, "practices": 4, "optimality": 5, "bloat": 5, "scope": 5, "methodology": 3, "tests": 3}, "P3": {"accuracy": 4, "completeness": 3, "conciseness": 4, "usefulness": 3}, "clarity": 4, "questions": 5}, "Y": {"P1": {"success": 4, "correctness": 4, "practices": 5, "optimality": 3, "bloat": 3, "scope": 3, "methodology": 4, "tests": 4}, "P2": {"success": 5, "correctness": 5, "practices": 5, "optimality": 4, "bloat": 4, "scope": 4, "methodology": 4, "tests": 5}, "P3": {"accuracy": 5, "completeness": 5, "conciseness": 4, "usefulness": 5}, "clarity": 4, "questions": 3}, "winner": {"P1": "Y", "P2": "Y", "P3": "Y", "overall": "Y"}}
```