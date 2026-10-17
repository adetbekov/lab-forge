| | X P1 | X P2 | Y P1 | Y P2 |
|---|---|---|---|---|
| success | 5 | 5 | 4 | 5 |
| correctness | 3 | 4 | 4 | 4 |
| practices | 4 | 4 | 5 | 5 |
| optimality | 3 | 4 | 4 | 5 |
| bloat | 3 | 3 | 4 | 5 |
| scope | 4 | 4 | 3 | 5 |

| P3 | accuracy | completeness | conciseness | usefulness |
|---|---|---|---|---|
| X | 5 | 5 | 3 | 4 |
| Y | 5 | 4 | 4 | 4 |

Clarity: X 4, Y 3. Questions: X 4, Y 4.

Verification: X has 80 tests passing, ruff clean, and the eval works. Y has 28 tests passing and ruff clean, but its eval crashes when there is no `.git`.

**X defects**
- `rparse/models.py:99-101`: `items` defaults to `[]` and extra keys are ignored, so `{}` or `{"receipt": {...}}` is accepted as an empty receipt with no retry. X found this during P2 and deferred it.
- `rparse/models.py:43-48`: `"1,250"` is parsed as 1.250. `_fill_derivable` (`:71-96`) silently fills fields the LLM left out, which hides model errors.
- `rparse/parser.py:115` falls back to the fake client silently. The prompt is not versioned (`prompts.py:8`) and eval runs are not recorded.
- The fake gets 100% recall on its own golden set, so per-field accuracy is 1.000 everywhere and says nothing. The pinned numbers in `tests/test_eval.py:114-115,200,219,223` make golden edits costly. About 1370 lines of Python, against Y's 758.

**Y defects**
- `rparse/eval.py:168-178`: `_git(check=True)` makes the eval fail outside git, and every run writes a results file.
- `schema.py:20` requires `total`, but `prompts/v1.md:20` asks for `"total": null` on non-receipts. That answer costs 3 calls and then raises. Y deferred this.
- The schema cannot represent discounts (golden 005: items sum to 38.95, total is 36.95). Only a fence wrapping the whole answer is stripped (`parser.py:16`). The full raw output is logged at WARNING (`:66-72`).
- P1 extras nobody asked for: `params.toml`, the results journal, `plans/`, latency percentiles.

**P3:** all 10+ refs I checked on each side are correct. X is exhaustive but long. Y is tighter, and its golden test asserts `>= 8`, so adding a receipt needs no test edits.

**Winners**
- P1: Y. Versioned prompts, a strict schema and reproducible run records, in about half the code.
- P2: Y. Equal function in +254 lines, and its per-field metric actually tells fields apart. X still accepts `{}`.
- P3: tie.
- Overall: Y. Better LLM-app hygiene and leaner code. X's messages are clearer, but its lenient validation undercuts the robustness goal.

```json
{"X": {"P1": {"success": 5, "correctness": 3, "practices": 4, "optimality": 3, "bloat": 3, "scope": 4}, "P2": {"success": 5, "correctness": 4, "practices": 4, "optimality": 4, "bloat": 3, "scope": 4}, "P3": {"accuracy": 5, "completeness": 5, "conciseness": 3, "usefulness": 4}, "clarity": 4, "questions": 4}, "Y": {"P1": {"success": 4, "correctness": 4, "practices": 5, "optimality": 4, "bloat": 4, "scope": 3}, "P2": {"success": 5, "correctness": 4, "practices": 5, "optimality": 5, "bloat": 5, "scope": 5}, "P3": {"accuracy": 5, "completeness": 4, "conciseness": 4, "usefulness": 4}, "clarity": 3, "questions": 4}, "winner": {"P1": "Y", "P2": "Y", "P3": "tie", "overall": "Y"}}
```
