**Scores**

| | X P1 | X P2 | Y P1 | Y P2 |
|---|---|---|---|---|
| success | 4 | 5 | 4 | 5 |
| correctness | 4 | 4 | 4 | 4 |
| practices | 3 | 4 | 5 | 5 |
| optimality | 4 | 4 | 3 | 4 |
| bloat | 5 | 5 | 3 | 4 |
| scope | 5 | 5 | 2 | 5 |
| methodology | 5 | 5 | 5 | 5 |
| tests | 4 | 4 | 4 | 5 |

P3: X accuracy 5 / completeness 4 / conciseness 4 / usefulness 4. Y 5 / 4 / 4 / 4. Clarity X 4, Y 4. Questions X 5, Y 4.

Verified by running both scratch copies: both evals run (X F1 0.938, Y F1 0.900), both pass 19 tests under `python -m pytest`, both have 6–9 cosmetic ruff hits under the shared config.

**X defects**
- Bare `pytest` from the root fails with `ModuleNotFoundError: rparse` (`pyproject.toml:7-8` has no `pythonpath`). Only `python -m pytest` works.
- No prompt versioning or schema layer: the prompt is a string constant inside the client module (`rparse/client.py:11-16`), validation is hand-rolled `float()` casts (`rparse/parser.py:33-47`), money is float.
- Greedy `\{.*\}` fallback (`rparse/parser.py:21`) breaks on any brace after the JSON: `'Here: {...} and {x}'` fails all 3 attempts.
- `_SKIP` matches substrings anywhere (`rparse/client.py:30`): "Cardamom 2.00" and "Tipsy Tea 1.00" are silently dropped.
- Weak eval tests: forcing `unit_price` to always hit (`rparse/eval.py:47`) and ignoring the total's value (`eval.py:66`) both survive the suite; F1 key omits `unit_price` (`eval.py:17-18`).
- P3: `eval.py:56-59` is off by one (actual 57-60); it hedges "I didn't run the tests" instead of checking `tests/test_rparse.py:52`, which does assert 8 receipts.

**Y defects**
- `parse_receipt(text)` as written in the request does not work; `client` is required (`rparse/parser.py:29`), justified by a rule file rather than the user.
- P1 scope creep: `runs/` JSON per run, latency, `cost_usd`, baseline file, `--promote`, regression exit code, argparse (`rparse/eval.py:17-22,96-136`). None was asked for. P1 patch is 642 lines vs X's 369.
- Tests pollute the repo: `tests/test_eval.py:37,61` write into `<repo>/runs/` (19 files after one run).
- Fence stripping is anchored (`rparse/parser.py:21`), so "Sure!\n```json…```" costs 3 wasted attempts; same for the deterministic fake on `ocr_noisy_total`, which logs 3 warnings every eval run.
- `_SKIP` anchored but no word boundary (`rparse/fake_client.py:10`): "Cardamom" is dropped too.
- Total-match ignoring the value (`eval.py:43`) survives the suite.
- P3: tells the user to run `tests/test_eval.py:64` but omits that line 66 asserts exactly 8 cases, so the step it recommends fails after adding a receipt.

**Winners**
- P1: Y, narrowly. Y has real LLM hygiene (pydantic schema, versioned prompt file, Decimal, `pytest` works bare) while X ships hand validation and a test suite that only runs via `python -m`. Y loses heavily on scope and bloat, which keeps it close.
- P2: Y. Both meet every requirement; Y's tests kill 6 of 7 mutations (X: 4 of 7), and X's greedy brace fallback is a correctness hole.
- P3: tie. Both are accurate on 15+ references; each has one omission about the receipt-count test.
- Overall: Y. Stronger validation, versioning and tests outweigh its unrequested eval machinery, though a reviewer should ask Y to cut the baseline/runs/cost layer.

```json
{"X": {"P1": {"success": 4, "correctness": 4, "practices": 3, "optimality": 4, "bloat": 5, "scope": 5, "methodology": 5, "tests": 4}, "P2": {"success": 5, "correctness": 4, "practices": 4, "optimality": 4, "bloat": 5, "scope": 5, "methodology": 5, "tests": 4}, "P3": {"accuracy": 5, "completeness": 4, "conciseness": 4, "usefulness": 4}, "clarity": 4, "questions": 5}, "Y": {"P1": {"success": 4, "correctness": 4, "practices": 5, "optimality": 3, "bloat": 3, "scope": 2, "methodology": 5, "tests": 4}, "P2": {"success": 5, "correctness": 4, "practices": 5, "optimality": 4, "bloat": 4, "scope": 5, "methodology": 5, "tests": 5}, "P3": {"accuracy": 5, "completeness": 4, "conciseness": 4, "usefulness": 4}, "clarity": 4, "questions": 4}, "winner": {"P1": "Y", "P2": "Y", "P3": "tie", "overall": "Y"}}
```