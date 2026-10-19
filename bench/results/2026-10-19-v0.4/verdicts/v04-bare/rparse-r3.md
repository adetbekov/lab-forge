**Scores**

| | X P1 | Y P1 | X P2 | Y P2 |
|---|---|---|---|---|
| success | 5 | 4 | 5 | 5 |
| correctness | 4 | 4 | 4 | 3 |
| practices | 5 | 3 | 4 | 4 |
| optimality | 4 | 4 | 4 | 4 |
| bloat | 4 | 4 | 4 | 5 |
| scope | 3 | 4 | 4 | 5 |
| methodology | 5 | 4 | 5 | 4 |
| tests | 5 | 4 | 5 | 4 |

P3: X accuracy 5 / completeness 5 / conciseness 4 / usefulness 5. Y 5 / 4 / 4 / 4. Clarity X 4, Y 4. Questions X 5, Y 4.

Both suites pass under `python -m pytest` (X 16, Y 21), both evals run, and every mutation I applied (skip-list off, recall denominator, total-match, fence strip, retry prompt not updated, loop once, quantity ignored in field accuracy) was caught by at least one test on both sides. Ruff shows 7-8 autofixable style hits on each side under this environment's preset. Not decisive.

**X defects**
- Scope creep in P1: `baseline.json`, `runs/` per-run dumps, cost and latency metering, TOML config, README. Useful, but not asked (`rparse/eval.py:17-25`, `:101-120`).
- Library reads `rparse.toml` from the repo root on every default call (`rparse/parser.py:18-20`, `:33`). Fragile once installed, and `max_attempts=0` silently becomes 3.
- Fence stripping is anchored and needs a newline after the opener (`rparse/parser.py:11`). Fences with surrounding prose or `` ```json{ `` fall through to retry rather than parse. Y handles all four variants I tried.
- Negative quantities and totals validate fine (`rparse/models.py:7-15`). Minor.

**Y defects**
- Bare `pytest` from the root fails with `ModuleNotFoundError: rparse` (no `pythonpath` in `pyproject.toml:17-18`, package not installed). The reply only ever ran `python3 -m pytest`.
- Eval has no parse-error handling: one `ReceiptParseError` after retries aborts the whole run (`rparse/eval.py:69`). With a real client the P2 retry path makes this likely. No `parse_errors` metric either.
- Fake was tuned to the golden set after seeing the score (added `service` to `_SKIP`, `rparse/client.py:29`), and three tests lock the 1.000 in (`tests/test_eval.py:20-23`, `:33-35`, `:45-47`). Adding any golden receipt the regexes miss, like a two-line item, breaks the suite. X asserts `f1 > 0.5` and tracks drift via a baseline instead.
- Silent repair: a missing `total` becomes the sum of line totals (`rparse/parser.py:40-41`). Unrequested and masks a model omission.
- Prompt lives in `client.py:9-16`, unversioned; money is `float`; validation is hand-rolled. X has a versioned prompt recorded in the baseline, pydantic, and `Decimal`.
- `field_hits` pairs leftover items in order, so a wrong-name item earns credit on the other fields (`rparse/eval.py:45-48`). Documented, but debatable.

**P3 answers**
All refs I checked on both sides are correct (X: `parser.py:18-20,33-42`, `prompts.py:21-27`, `eval.py:61,65-68,98,117-120`, `rparse.toml:2,7`; Y: `parser.py:10,14-24,42-43,56-74`, `eval.py:58-59,67-70`, `client.py:27-40,47-78`). X's answer is complete, including the baseline refresh caveat. Y's is accurate but ends with "I didn't open `tests/test_eval.py`", leaving the one real hazard (tests pin F1 to 1.0) for the user to discover.

**Winners**
- P1: X. Sounder eval (parse errors counted, tolerant test, prompt versioning, `Decimal`), and bare `pytest` works. Its extra baseline/runs machinery is the only real knock.
- P2: X. Both implement retry-with-feedback cleanly and test it well, but Y's eval crashes on exactly the failure mode P2 introduces, while X's counts it. X's stricter fence regex is the trade-off.
- P3: X, narrowly. Equally accurate, but X verified the test coupling instead of deferring it.
- Overall: X. It is the more defensible LLM-app skeleton: schema validation, versioned prompt, eval that survives bad outputs and tracks drift. Y is leaner and its fence handling is more forgiving, but the brittle golden-locked tests, the crashing eval and the broken bare `pytest` are more costly in practice.

```json
{"X": {"P1": {"success": 5, "correctness": 4, "practices": 5, "optimality": 4, "bloat": 4, "scope": 3, "methodology": 5, "tests": 5}, "P2": {"success": 5, "correctness": 4, "practices": 4, "optimality": 4, "bloat": 4, "scope": 4, "methodology": 5, "tests": 5}, "P3": {"accuracy": 5, "completeness": 5, "conciseness": 4, "usefulness": 5}, "clarity": 4, "questions": 5}, "Y": {"P1": {"success": 4, "correctness": 4, "practices": 3, "optimality": 4, "bloat": 4, "scope": 4, "methodology": 4, "tests": 4}, "P2": {"success": 5, "correctness": 3, "practices": 4, "optimality": 4, "bloat": 5, "scope": 5, "methodology": 4, "tests": 4}, "P3": {"accuracy": 5, "completeness": 4, "conciseness": 4, "usefulness": 4}, "clarity": 4, "questions": 4}, "winner": {"P1": "X", "P2": "X", "P3": "X", "overall": "X"}}
```