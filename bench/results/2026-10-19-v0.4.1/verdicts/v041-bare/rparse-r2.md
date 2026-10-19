Both scratch copies match their snapshots again. I have everything needed for the write-up.

## Scores

| | X P1 | Y P1 | X P2 | Y P2 |
|---|---|---|---|---|
| success | 4 | 4 | 4 | 5 |
| correctness | 3 | 4 | 3 | 4 |
| practices | 3 | 4 | 3 | 4 |
| optimality | 4 | 4 | 4 | 4 |
| bloat | 3 | 4 | 4 | 4 |
| scope | 5 | 3 | 5 | 4 |
| methodology | 3 | 4 | 4 | 4 |
| tests | 3 | 4 | 4 | 5 |

| P3 | accuracy | completeness | conciseness | usefulness |
|---|---|---|---|---|
| X | 5 | 4 | 4 | 4 |
| Y | 4 | 4 | 3 | 4 |

clarity: X 3, Y 4. questions: X 5, Y 4.

## Defects, X

- **Bare `pytest` fails** at P1 and P2 with `ModuleNotFoundError: No module named 'rparse'`. Only `python -m pytest` works, since `pyproject.toml` sets no `pythonpath` and the package is not installed. The request said "pytest tests".
- **Eval aborts on a parse failure.** `rparse/eval.py:82` calls `parse_receipt` with no `except`, so one unrecoverable receipt crashes the whole run instead of being counted. A retry-then-raise parser (P2) makes this likely with a real model.
- **Item F1 ignores unit price.** `rparse/eval.py:17` keys on name, quantity and line total only, so a wrong unit price still counts as a true positive. I confirmed it with a probe.
- **F1 is fitted to the golden set.** Score is 1.000 on every metric; X admits this. No hand-computed matching test exists, and replacing `item_counts` with `min(n_pred, n_gold)` left all 22 tests green.
- **Default `client=None` silently uses the fake in production code** (`rparse/parser.py:93-96`).
- Minor: no prompt versioning; P1 reply dumps per-file line counts.

## Defects, Y

- **`Receipt.total` cannot be null** (`rparse/models.py:14`), so a receipt with no printed total can never validate from a real model. The fake papers over this by summing items (`rparse/fake.py:35-36`), which also makes the `no_total_line` golden case a fitted match.
- **Brittle eval tests.** Adding one golden row breaks three tests: `tests/test_eval.py:25` hard-codes `== 8`, line 46 hard-codes 8 failures, and the baseline-floor test fails if the fake misses the new row. The P3 answer should have checked this instead of hedging.
- **Unrequested machinery in P1**: `cost_usd`, `latency_s`, baseline file, `runs/` output, README. `latency_s` churns the baseline on every write (visible in the P2 patch).
- `PROMPT_VERSION` is bumped but read nowhere. `strip_fences` fails on prose plus a fence, which X handles.
- Off-by-one refs in P3: `eval.py:77`, `:90`, `:92-96` are each one line off.

## Mutation results

Y: all six mutations (retry prompt, fence strip, extra attempt, field_hits, item_counts, F1 formula) were caught. X: retry prompt, give-up logic and field_hits were caught; the item-matching mutation survived.

## Winners

- **P1: Y.** Y's eval shows a non-trivial score with deliberate misses, hand-computed matching tests, and bare `pytest` works. X's harness is tight and in-scope but scores a tautological 1.0, ignores unit price, and plain `pytest` fails.
- **P2: Y.** Both implement retry and per-field accuracy correctly with bad-first-client tests. Y also counts parse failures in the eval, where X's eval crashes.
- **P3: X.** X's references are exact and it correctly states the test-threshold consequences of a new golden case. Y gives a more complete workflow but has off-by-one refs and leaves an easily checked question open.
- **Overall: Y.** Its parser and eval are more robust and better tested, at the cost of some scope creep and a nullable-total gap. X is leaner and answered the question better, but the eval soundness and `pytest` issues weigh more.

```json
{"X": {"P1": {"success": 4, "correctness": 3, "practices": 3, "optimality": 4, "bloat": 3, "scope": 5, "methodology": 3, "tests": 3}, "P2": {"success": 4, "correctness": 3, "practices": 3, "optimality": 4, "bloat": 4, "scope": 5, "methodology": 4, "tests": 4}, "P3": {"accuracy": 5, "completeness": 4, "conciseness": 4, "usefulness": 4}, "clarity": 3, "questions": 5}, "Y": {"P1": {"success": 4, "correctness": 4, "practices": 4, "optimality": 4, "bloat": 4, "scope": 3, "methodology": 4, "tests": 4}, "P2": {"success": 5, "correctness": 4, "practices": 4, "optimality": 4, "bloat": 4, "scope": 4, "methodology": 4, "tests": 5}, "P3": {"accuracy": 4, "completeness": 4, "conciseness": 3, "usefulness": 4}, "clarity": 4, "questions": 4}, "winner": {"P1": "Y", "P2": "Y", "P3": "X", "overall": "Y"}}
```