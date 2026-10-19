**Scores**

| | X P1 | Y P1 | X P2 | Y P2 | | X P3 | Y P3 |
|---|---|---|---|---|---|---|---|
| success | 5 | 5 | 5 | 5 | accuracy | 5 | 5 |
| correctness | 4 | 4 | 4 | 3 | completeness | 5 | 5 |
| practices | 4 | 4 | 4 | 4 | conciseness | 3 | 4 |
| optimality | 4 | 4 | 4 | 4 | usefulness | 4 | 5 |
| bloat | 4 | 4 | 4 | 4 | | | |
| scope | 3 | 4 | 5 | 4 | clarity | 4 | 4 |
| methodology | 5 | 5 | 4 | 3 | questions | 5 | 5 |
| tests | 4 | 3 | 5 | 3 | | | |

Both snapshots: 16 tests pass under `.venv/bin/pytest` and bare `pytest`; `python -m rparse.eval` runs offline (X f1 0.872, Y item_f1 0.958, both equal to committed baseline). Neither fitted the golden set to the fake: both kept known-failing receipts and said so.

**X defects**
- `rparse/parser.py:33` — `max_attempts or default` turns `max_attempts=0` into 3 silent calls (flagged in reply, not fixed).
- `rparse/parser.py:11` — fence regex is anchored to the whole reply; a fence with surrounding prose raises `ParseError` (verified). Meets the literal ask, less robust than Y.
- `rparse/eval.py:44` — per-field pairing is by name only, so a wrong name zeroes the other three fields. Deterministic and documented, but harsh.
- `rparse/client.py:9-11`, `rparse/eval.py:17-24` — P1 adds `cost_usd`, `_Metered`, latency; unrequested.
- Reply claims `ruff check .` clean; in this environment ruff reports 8 issues (unsorted imports `client.py:1-5`, etc.) and 5 unformatted files. Y shows 1 issue, formatted.
- Mutation: removing the qty-first regex (`client.py:50`) leaves all tests green; the golden test only asserts `f1 > 0.5` (`tests/test_eval.py:129`).

**Y defects**
- `rparse/eval.py:39-44` — greedy "best unused" pairing is order dependent. Verified: gold [Milk, Bread] vs pred [Bread] scores name 0/2; reversed gold order scores 1/2. Milk steals the Bread prediction on one shared field. Field accuracy is therefore not a stable metric.
- `tests/test_eval.py:125-135` — the field-accuracy test survives replacing `hits[f] += a == b` with `hits[f] += 1` (eval.py:46). It only checks a 2-gold/1-pred shape.
- `tests/test_eval.py:95-109` — F1 test only checks the 1.0 case; replacing f1 with precision (eval.py:82) keeps all 16 tests green. X's hand-computed P=1/2, R=1/3 test catches this.
- `rparse/eval.py:60` — parse failure is scored with a `total=-1` sentinel, which counts as a total match if gold is -1 (verified; contrived but hacky).
- No prompt versioning; the prompt lives inline in `parser.py:19`. X keeps `RECEIPT_PROMPT_VERSION` and records it in every eval run.

**Question (P3)**
All refs checked for both are correct (X: parser.py:18-20, 23-26, 38-42, prompts.py:21-27, eval.py:65-68, 98, 117-120, rparse.toml:2,7; Y: parser.py:38-39, 47-52, 64-78, 30, eval.py:55-60, 100, 107-122, config.toml:2). Y is tighter and mentions the exit-1 baseline gate and the ValueError guard, which matter when adding a receipt. X is accurate but longer and pads with rule-file asides.

**Winners**
- P1: tie. Both meet every requirement with comparable size. X has better LLM hygiene (versioned prompt, F1 test that actually constrains the formula) but more unrequested metering and lint noise; Y has a leaner client interface and a baseline gate but a weak F1 test.
- P2: X. Both strip fences and retry with the error fed back, and both retry paths are well tested (every retry/fence mutation failed tests on both sides). Y's per-field accuracy is order dependent and its test cannot detect a broken comparison; X's name-pairing is simple, deterministic, and its hand-computed test caught every mutation.
- Overall: X. The eval harness is the deliverable that must be trusted, and X's metrics are stable and its scorer tests are real; Y's field accuracy can change with golden item order, which undermines the P2 report.

```json
{"X": {"P1": {"success": 5, "correctness": 4, "practices": 4, "optimality": 4, "bloat": 4, "scope": 3, "methodology": 5, "tests": 4}, "P2": {"success": 5, "correctness": 4, "practices": 4, "optimality": 4, "bloat": 4, "scope": 5, "methodology": 4, "tests": 5}, "P3": {"accuracy": 5, "completeness": 5, "conciseness": 3, "usefulness": 4}, "clarity": 4, "questions": 5}, "Y": {"P1": {"success": 5, "correctness": 4, "practices": 4, "optimality": 4, "bloat": 4, "scope": 4, "methodology": 5, "tests": 3}, "P2": {"success": 5, "correctness": 3, "practices": 4, "optimality": 4, "bloat": 4, "scope": 4, "methodology": 3, "tests": 3}, "P3": {"accuracy": 5, "completeness": 5, "conciseness": 4, "usefulness": 5}, "clarity": 4, "questions": 5}, "winner": {"P1": "tie", "P2": "X", "P3": "Y", "overall": "X"}}
```