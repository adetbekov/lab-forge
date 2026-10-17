## Scores

| | X P1 | X P2 | Y P1 | Y P2 |
|---|---|---|---|---|
| success | 4 | 5 | 5 | 5 |
| correctness | 3 | 4 | 4 | 4 |
| practices | 4 | 5 | 3 | 4 |
| optimality | 4 | 5 | 4 | 4 |
| bloat | 4 | 4 | 4 | 4 |
| scope | 4 | 4 | 4 | 4 |

| P3 | X | Y |
|---|---|---|
| accuracy | 5 | 5 |
| completeness | 5 | 5 |
| conciseness | 3 | 4 |
| usefulness | 5 | 5 |
| clarity | 4 | 4 |
| questions | 4 | 5 |

Both snapshots run cleanly. X: eval F1 0.933, total 0.875, 37 tests pass. Y: eval F1 0.806, total 0.875, 53 tests pass. Ruff is clean on both.

## Key defects

**X**
- The prompt and schema contradict each other. `prompts/v1.txt:12` says "use null" for unreadable values, but `schema.py:25` (and the item fields) reject null. This is why r06 fails in X's own eval, and after P2 it costs 3 model calls. It was flagged twice and never fixed.
- The fake is fitted to the golden set. `fake_client.py:23-27` lists exactly the golden set's words ("service", "paid", "барлығы"), so 7 of 8 receipts score perfectly and the 0.933 F1 shows little. The reply admits this.
- Each eval run writes a report into the repo (`eval.py:225-231`). Three were committed, about 380 lines of churn.
- Field alignment pairs items on any one agreeing field, quantity alone included (`eval.py:79`).
- `parse_receipt(text, client)` differs from the requested signature. This was a choice and was disclosed.
- Strengths: prompts are versioned files, settings live in `params.toml`, reports record a golden-set hash plus cost and latency, and the retry loop is lean (`parser.py:74-90`).

**Y**
- No prompt versioning. The prompt and retry template are inline constants (`parser.py:18-31,69-82`), and eval results are not saved.
- With no client passed, it quietly uses the fake (`parser.py:144-147`). That is a trap in production.
- The eval catches only `ReceiptParseError` (`eval.py:79`), so a client exception aborts the run. X has the same gap.
- Tests hardcode the golden-set size: 8 receipts, 30 items, 16 calls (`tests/test_eval.py:39,65,93,100`).
- Strengths: `total` is nullable, which matches the prompt. The fake is not tuned to the golden set (it misses 04, 05, 07 and 08), so the F1 tells good output from bad. Fence extraction is robust, the echoed reply is capped, and `.attempts` keeps the retry history.

**P3:** I checked more than 10 refs per side. Nearly all are exact; the one weak ref is X's `tests/test_parser.py:154`, which points at the end of a test, not the give-up test at `:117`. Y is shorter and correctly warns that the hardcoded test counts need updating. X runs longer but usefully notes that null outputs waste attempts.

## Winners

- **P1: Y.** X shipped the prompt/schema contradiction and a fitted fake. Y's schema matches its prompt, it keeps the requested signature, and its eval baseline is meaningful.
- **P2: X.** X is leaner and has better LLM hygiene: a versioned retry prompt, `max_attempts` in config, and cost and latency that include retries. Its parser is 90 lines against Y's 167.
- **P3: Y.** Accuracy is equal; Y is more concise.
- **Overall: Y, narrowly.** Y's eval is sound and its schema is consistent; its gaps are hygiene (inline prompts, defaulting to the fake). X has better experiment tooling, but the null rejection was never fixed and its F1 comes from a fitted fake.

```json
{"X": {"P1": {"success": 4, "correctness": 3, "practices": 4, "optimality": 4, "bloat": 4, "scope": 4}, "P2": {"success": 5, "correctness": 4, "practices": 5, "optimality": 5, "bloat": 4, "scope": 4}, "P3": {"accuracy": 5, "completeness": 5, "conciseness": 3, "usefulness": 5}, "clarity": 4, "questions": 4}, "Y": {"P1": {"success": 5, "correctness": 4, "practices": 3, "optimality": 4, "bloat": 4, "scope": 4}, "P2": {"success": 5, "correctness": 4, "practices": 4, "optimality": 4, "bloat": 4, "scope": 4}, "P3": {"accuracy": 5, "completeness": 5, "conciseness": 4, "usefulness": 5}, "clarity": 4, "questions": 5}, "winner": {"P1": "Y", "P2": "X", "P3": "Y", "overall": "Y"}}
```
