**Scores**

| | X P1 | Y P1 | X P2 | Y P2 |
|---|---|---|---|---|
| success | 5 | 4 | 5 | 5 |
| correctness | 4 | 4 | 3 | 5 |
| practices | 3 | 4 | 3 | 4 |
| optimality | 3 | 4 | 3 | 4 |
| bloat | 4 | 4 | 4 | 4 |
| scope | 4 | 4 | 4 | 4 |
| methodology | 4 | 4 | 3 | 4 |
| tests | 3 | 4 | 3 | 4 |

P3: X accuracy 5 / completeness 4 / conciseness 4 / usefulness 4. Y accuracy 4 / completeness 5 / conciseness 4 / usefulness 4. Clarity X 4, Y 4. Questions X 5, Y 4.

Verified: both snapshots pass bare `pytest` and `python -m pytest` (16 each), both evals run (X F1 0.872, Y 0.9545, zero delta vs baseline). Both replies claim `ruff check .` clean, but this environment's ruff reports 8 findings for X (incl. unsorted imports `rparse/client.py:1-5`, `open()` without context manager `tests/test_eval.py:51`) and 4 for Y (only FURB/UP alias rules).

**X defects**
- `rparse/parser.py:33` `max_attempts or default_max_attempts()`: `max_attempts=0` silently makes 3 calls (confirmed). `parser.py:18-20` reads `rparse.toml` from disk relative to `__file__` on every call, so the library breaks when installed outside the repo.
- `parser.py:11,25` fence regex only matches when the whole reply is a fence; "Here you go:\n```json…```" is not stripped (Y handles it).
- `rparse/eval.py:37-50` per-field accuracy pairs only by name, so quantity/unit_price/line_total are capped by name accuracy; baseline shows all four identical (0.895), so the new metric carries no extra signal.
- `rparse/client.py:38-40` FakeClient parses the receipt out of the prompt's `<receipt>` tag and raises bare `ValueError` if the prompt wording changes, crashing the eval instead of recording a parse error. Also `parser.py:32` silently falls back to the fake in production.
- `tests/test_parser.py:71-75` `test_attempts_default_comes_from_toml` echoes the config value; replacing the TOML read with a literal `3` passes all tests.
- F1 key test gap: dropping name, quantity or unit_price from `_keys` (`eval.py:27-30`) still passes all tests (the "wrong price" fixture changes both price fields).

**Y defects**
- `rparse/parser.py:33` requires `client`; the literal `parse_receipt(text)` from P1 does not run. Flagged with "say if you want a default" while the user was unavailable. Defensible hygiene, but a departure.
- `rparse/models.py:15` line item field is `total` while the spec and the report key say `line_total`; `Receipt.total` vs `LineItem.total` is ambiguous.
- Same F1 key gap as X: dropping any single field from `_keys` (`eval.py:35-36`) survives the suite.
- `tests/test_eval.py:35` asserts `item_f1 > 0.9`, a threshold tied to the fake's current behaviour.
- `rparse/client.py:49-50` fake invents a total by summing items when no TOTAL line exists, which flatters total-match on unlabeled receipts.

**Mutation results**: X killed 7 of 9 first-round mutations (survivors: TOML default, key-drop). Y killed all 9 targeted mutations except the symmetric key-drop. Y's retry test checks the pydantic error names the missing field and that the JSON error text reaches the next prompt; X only checks "Error:" and the bad reply are present.

**Question**: X's refs all check (parser 18-20/33-42, prompts 21-27, eval 61/65-68/98/117-120, toml 2/7). Y's refs check except `eval.py:100-102`, which is slightly off (id/text are read at 103/106). Y adds the ValueError guards, logging and the ≥8 golden test; X adds the baseline-denominator caveat. Tie.

**Winners**: P1 Y, P2 Y, P3 tie, overall Y. Y's design is cleaner for an LLM app: strict schema (`extra="forbid"`), a system/user client interface that doesn't couple the fake to prompt internals, a pure scorer, and a per-field metric that actually distinguishes fields. X meets every literal requirement but adds a runtime TOML dependency, a degenerate per-field metric, and a config-echo test.

```json
{"X": {"P1": {"success": 5, "correctness": 4, "practices": 3, "optimality": 3, "bloat": 4, "scope": 4, "methodology": 4, "tests": 3}, "P2": {"success": 5, "correctness": 3, "practices": 3, "optimality": 3, "bloat": 4, "scope": 4, "methodology": 3, "tests": 3}, "P3": {"accuracy": 5, "completeness": 4, "conciseness": 4, "usefulness": 4}, "clarity": 4, "questions": 5}, "Y": {"P1": {"success": 4, "correctness": 4, "practices": 4, "optimality": 4, "bloat": 4, "scope": 4, "methodology": 4, "tests": 4}, "P2": {"success": 5, "correctness": 5, "practices": 4, "optimality": 4, "bloat": 4, "scope": 4, "methodology": 4, "tests": 4}, "P3": {"accuracy": 4, "completeness": 5, "conciseness": 4, "usefulness": 4}, "clarity": 4, "questions": 4}, "winner": {"P1": "Y", "P2": "Y", "P3": "tie", "overall": "Y"}}
```