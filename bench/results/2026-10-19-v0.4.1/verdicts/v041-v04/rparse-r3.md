Both snapshots run end to end: 16 tests pass each (bare `pytest` and `python -m pytest`), `python -m rparse.eval` works from the root, and ruff only flags alias-style rules (FURB167, UP017) on both sides, so lint is a wash.

| | X P1 | Y P1 | X P2 | Y P2 | X P3 | Y P3 |
|---|---|---|---|---|---|---|
| success | 4 | 5 | 5 | 4 | | |
| correctness | 4 | 4 | 5 | 4 | | |
| practices | 4 | 4 | 5 | 4 | | |
| optimality | 4 | 4 | 5 | 3 | | |
| bloat | 4 | 4 | 5 | 4 | | |
| scope | 4 | 3 | 5 | 3 | | |
| methodology | 4 | 4 | 5 | 4 | | |
| tests | 3 | 4 | 5 | 3 | | |
| accuracy / completeness / conciseness / usefulness | | | | | 5/5/4/5 | 5/5/4/4 |

clarity: X 4, Y 4. questions: X 4, Y 5.

**X defects**
- `tests/test_eval.py:14-20`: the hand-computed F1 case has P = R, so replacing F1 with precision in `rparse/eval.py:87` survives the whole suite. For an eval harness that is the one formula that matters.
- `rparse/parser.py:33`: client is required, so the requested `parse_receipt(text)` signature is not honoured. The reply punts the decision back to an unavailable user.
- `rparse/client.py:23-24`: the fake's keyword lists (итого, к оплате, ндс, сдача) are tuned to its own golden set, and `tests/test_eval.py:35` asserts F1 > 0.9 against that fake. Honest in the reply, but the threshold test just echoes the fit.
- `evals/baseline.json:16` commits `latency_s`, pure machine noise.

**Y defects**
- `tests/test_parser.py:61`: the retry test only checks the literal label `Error:` and the bad reply. Dropping the validation error text from `rparse/prompts.py:25` survives the suite, so the one behaviour P2 named ("retry with the validation error fed back") is untested.
- `rparse/eval.py:44-49`: per-field accuracy only counts items whose name already matches, so quantity, unit_price and line_total can never exceed name accuracy. The baseline shows all four at 0.895, meaning the new metric carries no extra information.
- `rparse/parser.py:33`: `max_attempts or default` turns an explicit 0 into 3 silently, and `default_max_attempts` re-reads `rparse.toml` from disk on every call.
- `tests/test_parser.py:71-75` echoes the TOML value; the config file and `--config` flag (`rparse/eval.py:93`) are unrequested machinery for one integer.
- `rparse/client.py:38-40`: the fake hard-fails unless the prompt contains `<receipt>` tags, coupling it to the prompt template. `rparse/client.py:25` also reads "KIOSK 7" as an item, a false positive left in the baseline.
- `README.md` was not updated for retry behaviour in P2.

**P3 verification**: I checked every reference in both answers against the snapshots (X: `parser.py:35-38, 13, 41, 21-23, 43-48, 17`, `eval.py:103-106, 100-102, 129, 125, 145`, `client.py:34`, `test_eval.py:30-32`; Y: `rparse.toml:7, 2`, `parser.py:18-20, 33-42, 23-26`, `prompts.py:21-27`, `eval.py:65-68, 98, 61, 117-120`, `client.py:18-55`). All are correct. Both walk the loop accurately, both explain eval behaviour on failure, both give a usable recipe for adding a receipt. Y's note that a new receipt shifts metric denominators is a nice touch; X's pointer to the golden-set validity test is equally useful. Tie.

**Winners**
- P1: Y. Both deliver the full harness, but X's F1 test cannot tell F1 from precision and X changed the requested signature. Y's TOML creep is the smaller sin.
- P2: X. X's retry test catches a dropped error message, its order-fallback alignment makes per-field accuracy independent of name, it validates `max_attempts`, and it updated the README. Y's surviving mutation hits the exact feature requested.
- Overall: X. The P2 step is where LLM-app hygiene is decided, and X's parser plus field-accuracy design is cleaner and better tested. Y is close and more literal on the P1 signature, but its config layer and name-gated field metric reduce the value of what it added.

```json
{"X": {"P1": {"success": 4, "correctness": 4, "practices": 4, "optimality": 4, "bloat": 4, "scope": 4, "methodology": 4, "tests": 3}, "P2": {"success": 5, "correctness": 5, "practices": 5, "optimality": 5, "bloat": 5, "scope": 5, "methodology": 5, "tests": 5}, "P3": {"accuracy": 5, "completeness": 5, "conciseness": 4, "usefulness": 5}, "clarity": 4, "questions": 4}, "Y": {"P1": {"success": 5, "correctness": 4, "practices": 4, "optimality": 4, "bloat": 4, "scope": 3, "methodology": 4, "tests": 4}, "P2": {"success": 4, "correctness": 4, "practices": 4, "optimality": 3, "bloat": 4, "scope": 3, "methodology": 4, "tests": 3}, "P3": {"accuracy": 5, "completeness": 5, "conciseness": 4, "usefulness": 4}, "clarity": 4, "questions": 5}, "winner": {"P1": "Y", "P2": "X", "P3": "tie", "overall": "X"}}
```