## Scores

| | X | Y |
|---|---|---|
| P1 success/correct/practices/optimal/bloat/scope | 5/4/5/5/5/4 | 5/4/4/4/3/4 |
| P2 success/correct/practices/optimal/bloat/scope | 5/4/4/5/5/5 | 5/5/5/4/3/4 |
| P3 accuracy/completeness/concise/useful | 5/5/4/5 | 5/5/4/5 |
| clarity | 4 | 4 |
| questions | 5 | 5 |

Verified: both snapshots run `python -m rparse.eval`. X reports F1 0.7917 and total-match 0.875, with one case ending in ParseError. Y reports F1 0.806 and total-match 7/8. Tests pass (X 20, Y 53), and ruff check and ruff format are clean on both. Neither fake client is overfitted to its golden set: each misses real cases, such as X `06_restaurant_tip` and `08_ocr_noise`, and Y `08_kz_restaurant` and `05_ocr_noisy`. Both expose `LLMClient` as a Protocol and validate replies through pydantic. All P3 file:line references I sampled (15+ per side) were correct.

## Key defects

**X**
- `rparse/parser.py:17,28-31`: fences are stripped only when the whole reply is one fenced block. Prose plus a fence, or an unclosed fence, still triggers a retry. That meets the literal request but is fragile.
- `rparse/models.py:21`: `total` is required. Receipts without a TOTAL line therefore always burn all 3 calls and raise. The eval shows this on `08_ocr_noise` (3 WARNINGs, deterministic, so the retries are wasted).
- `rparse/eval.py:62`: field-accuracy alignment pairs a gold item with the best remaining prediction even when they share nothing, so unrelated items can be compared field by field.
- `rparse/parser.py:63`: the full pydantic `str(e)`, including doc URLs, goes into the repair prompt and the error. That is noisy feedback for the model.
- Strengths: versioned prompts (`prompts.py:3`, `PROMPT_VERSION` recorded in the report) and a committed baseline with a regression test (`tests/test_eval.py:110-115`). This is the better LLM-app hygiene.

**Y**
- No prompt versioning anywhere. `SYSTEM_PROMPT` sits inline in `rparse/parser.py:18-31`, and the eval report does not record which prompt produced it.
- No committed baseline. The tests instead hardcode golden-set counts (`tests/test_eval.py:39,65,93,100`), so adding one receipt means editing four asserts, as Y's own P3 answer admits.
- Circular dependency: `fake.py:13` imports from `parser`, and `parser.py:145` works around it with a lazy import.
- Larger than needed: 1354 lines against 910. It adds latency timing (`eval.py:75-91`), a `--client module:attr` loader and `Attempt` history. Some of this is useful but was not requested.
- Strengths: more robust extraction (`parser.py:85-97`), compact field-level error feedback with the echoed reply capped (`:39,100-112`), name normalization and numeric tolerance in scoring (`scoring.py:26-48`), and evidence-gated alignment (`:55-81`). Its oracle and flaky-oracle eval tests also check the scorer itself.

## Winners
- **P1: X.** X's design is leaner and has proper prompt versioning plus a baseline. Y's scorer is somewhat more careful, but it is larger and has no versioning.
- **P2: Y.** Y's retry and fence handling is more robust, its error feedback is cleaner, and its retry tests are more thorough. X's version is correct and minimal but brittle on fence variants.
- **P3: tie.** Both answers are accurate and complete. X correctly points to the baseline workflow. Y correctly lists the hardcoded test numbers that must change.
- **Overall: X, narrowly.** Both fully meet every request. X does it in two-thirds of the code with better LLM-app hygiene (versioned prompts, baseline regression). Y's parsing robustness and scoring are stronger, but it has no prompt versioning and its tests are brittle.

```json
{"X": {"P1": {"success": 5, "correctness": 4, "practices": 5, "optimality": 5, "bloat": 5, "scope": 4}, "P2": {"success": 5, "correctness": 4, "practices": 4, "optimality": 5, "bloat": 5, "scope": 5}, "P3": {"accuracy": 5, "completeness": 5, "conciseness": 4, "usefulness": 5}, "clarity": 4, "questions": 5}, "Y": {"P1": {"success": 5, "correctness": 4, "practices": 4, "optimality": 4, "bloat": 3, "scope": 4}, "P2": {"success": 5, "correctness": 5, "practices": 5, "optimality": 4, "bloat": 3, "scope": 4}, "P3": {"accuracy": 5, "completeness": 5, "conciseness": 4, "usefulness": 5}, "clarity": 4, "questions": 5}, "winner": {"P1": "X", "P2": "Y", "P3": "tie", "overall": "X"}}
```
