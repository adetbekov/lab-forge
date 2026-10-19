**Scores**

| | X P1 | Y P1 | X P2 | Y P2 |
|---|---|---|---|---|
| success | 4 | 3 | 5 | 4 |
| correctness | 4 | 3 | 4 | 4 |
| practices | 4 | 3 | 4 | 4 |
| optimality | 4 | 3 | 4 | 4 |
| bloat | 4 | 3 | 4 | 4 |
| scope | 3 | 4 | 4 | 4 |
| methodology | 4 | 3 | 5 | 5 |
| tests | 5 | 3 | 5 | 4 |

| P3 | accuracy | completeness | conciseness | usefulness |
|---|---|---|---|---|
| X | 3 | 4 | 3 | 3 |
| Y | 5 | 4 | 4 | 5 |

Clarity: X 4, Y 4. Questions: X 3, Y 4.

**Verified runs.** Both evals run from the root. X: 15 tests pass under both `pytest` and `python -m pytest`. Y: 22 pass under `python -m pytest`, but bare `pytest` from the root fails with `ModuleNotFoundError: No module named 'rparse'` (no `pythonpath` in `Y/pyproject.toml:14-15`, package not installed). Ruff flags 4-5 cosmetic rules on each side.

**X defects**
- `rparse/parser.py:12` fence regex only matches when the whole reply is a fence. `Sure!\n```json…```` is passed through unchanged and fails validation (Y handles this).
- `tests/test_eval.py:25` hard-codes `len(rows) == 8`, so adding a golden receipt breaks the suite. The P3 answer said "I haven't checked" instead of looking, with the user unavailable.
- Unrequested extras: `golden/baseline.json`, `runs/latest.json`, `cost_usd`, `latency_s` (`eval.py:79-80`). `PROMPT_VERSION` (`prompts.py:1`) is declared but never recorded anywhere.
- Fake is narrow: 0.54 item F1 on Y's golden set.
- P3 refs off by one: `eval.py:77` (should be 78), `eval.py:90` (89), `92-96` (91-95).

**Y defects**
- `rparse/eval.py:82` does not catch `ReceiptParseError`, so one bad receipt aborts the whole eval (verified: a garbage client crashes `evaluate`). No parse-failure count.
- Item matching is untested: replacing `tp` with "count every prediction" or reducing `_key` to line_total only (`eval.py:16-23`) leaves all 22 tests green. Fake scores 1.0 on its own golden set, so F1 there is uninformative (Y admits this).
- `_key` ignores `unit_price`, so an item with a wrong unit price counts as a full match.
- `parser.py:93-96` silently defaults to the fake client; a production caller forgetting the client gets regex output with no warning. Floats for money with 0.005 tolerance.
- No prompt versioning; hand-rolled validation (`parser.py:52-72`) instead of a schema library.
- Fence-strip mutation survives because the brace fallback masks it (functionally fine, test gap).

**Winners**

- **P1: X.** Both meet the brief, but X's harness is sounder: parse failures are counted, items match on all four fields, Decimal money, and every mutation I tried was caught. Y's bare `pytest` fails from the root, its eval crashes on the first parse failure, and broken item matching goes undetected.
- **P2: X.** Both implement retry with error feedback correctly and test it with bad-first clients. X bumps the prompt version and its tests catch all mutations; Y's prose-tolerant fence handling is the one place it is stronger.
- **P3: Y.** Y's references are essentially all exact (I checked over fifteen), the trace is precise, and it states the concrete test thresholds a new receipt must meet. X has three off-by-one refs and left the one question that matters, whether a test pins the receipt count, unverified when it does.
- **Overall: X.** The code quality and eval methodology gap in P1 and P2 outweighs Y's better question answer.

```json
{"X": {"P1": {"success": 4, "correctness": 4, "practices": 4, "optimality": 4, "bloat": 4, "scope": 3, "methodology": 4, "tests": 5}, "P2": {"success": 5, "correctness": 4, "practices": 4, "optimality": 4, "bloat": 4, "scope": 4, "methodology": 5, "tests": 5}, "P3": {"accuracy": 3, "completeness": 4, "conciseness": 3, "usefulness": 3}, "clarity": 4, "questions": 3}, "Y": {"P1": {"success": 3, "correctness": 3, "practices": 3, "optimality": 3, "bloat": 3, "scope": 4, "methodology": 3, "tests": 3}, "P2": {"success": 4, "correctness": 4, "practices": 4, "optimality": 4, "bloat": 4, "scope": 4, "methodology": 5, "tests": 4}, "P3": {"accuracy": 5, "completeness": 4, "conciseness": 4, "usefulness": 5}, "clarity": 4, "questions": 4}, "winner": {"P1": "X", "P2": "X", "P3": "Y", "overall": "X"}}
```