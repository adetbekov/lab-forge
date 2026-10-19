| | X P1 | Y P1 | X P2 | Y P2 | X P3 | Y P3 |
|---|---|---|---|---|---|---|
| success | 5 | 5 | 5 | 5 | | |
| correctness | 4 | 4 | 4 | 5 | | |
| practices | 4 | 4 | 4 | 4 | | |
| optimality | 4 | 4 | 4 | 4 | | |
| bloat | 4 | 4 | 4 | 4 | | |
| scope | 4 | 4 | 4 | 5 | | |
| methodology | 5 | 4 | 5 | 5 | | |
| tests | 4 | 4 | 5 | 5 | | |
| accuracy / completeness / conciseness / usefulness | | | | | 3 / 3 / 4 / 3 | 5 / 5 / 4 / 5 |

Clarity: X 4, Y 4. Questions: X 3, Y 4.

Both snapshots run clean: eval prints zero deltas, bare `pytest` and `python -m pytest` pass (X 15, Y 17). Ruff in this environment flags only auto-fixable alias/style rules on both (X 5, Y 9); not a real defect on either side.

**X defects**
- `rparse/fake.py:23` the fake extracts receipt text by splitting the prompt on sentinel markers, so the fake is coupled to prompt layout. `rparse/client.py:7` has a single `prompt` string, no system/user split, which real SDKs want.
- `rparse/parser.py:12` fence regex is anchored to the whole reply. "Sure:\n```json …```" fails all three attempts and raises `ParseError` (verified by running it). Y handles this.
- `golden/baseline.json:11` commits `latency_s`, so every `--write-baseline` churns a nondeterministic number and the CLI prints a meaningless delta each run.
- `rparse/prompts.py:1` bumps `PROMPT_VERSION` to v2 although the parse prompt text did not change.
- Tests: hard-coded 8 at `tests/test_eval.py:25`. A mutation making total-match always true survives (no test with a wrong total). All seven other mutations were caught.
- P3 answer: `eval.py:77` and `eval.py:90` are off by one (parse_failures is line 78, `FakeClient()` is line 89). It says it did not check whether tests hard-code the count, which they do at `tests/test_eval.py:25`, leaving a predictable breakage for the user.

**Y defects**
- `rparse/eval.py:23` item F1 key omits `unit_price`. A prediction with the wrong unit price but right line total scores F1 1.0 (verified). The request asked for four-field items, so this inflates the headline metric.
- `tests/test_eval.py:54-55` pins `delta … +0.0000`, so any intended fake improvement breaks tests until the baseline is refreshed; also each pytest run writes a new timestamped file to `evals/runs/` (10 files after my runs).
- `rparse/parser.py:11` fence search is unanchored: "use ```json``` please {…}" yields an empty string. Edge case, triggers a retry.
- Hard-coded 8 at `tests/test_eval.py:42`; same surviving total-match mutation as X. All seven other mutations caught, usually by several tests.
- P3 answer: all refs checked are correct; `tests/test_eval.py:51-57` overshoots the file end by one line.

**Winners**
- P1: tie. X scores items on all four fields and keeps a sane `>=` baseline gate, but its fake parses the prompt by sentinel and its baseline carries latency. Y has the cleaner client contract (system/user, fake gets raw text) and a subprocess CLI test, but its F1 ignores unit price.
- P2: Y. Both meet every requirement with well-targeted tests, but Y's fence handling survives prose-prefixed replies, it does not bump a prompt version needlessly, and its retry tests check both message content and call count more thoroughly.
- P3: Y. Every reference lands, it names the exact test that will break when a receipt is added, and it lists the fake's supported row shapes. X has two off-by-one refs and defers a check it could have run.
- Overall: Y. Equal on delivery, Y is more robust on the retry path and far more accurate on the question; X's only clear lead is the stricter F1 key.

```json
{"X": {"P1": {"success": 5, "correctness": 4, "practices": 4, "optimality": 4, "bloat": 4, "scope": 4, "methodology": 5, "tests": 4}, "P2": {"success": 5, "correctness": 4, "practices": 4, "optimality": 4, "bloat": 4, "scope": 4, "methodology": 5, "tests": 5}, "P3": {"accuracy": 3, "completeness": 3, "conciseness": 4, "usefulness": 3}, "clarity": 4, "questions": 3}, "Y": {"P1": {"success": 5, "correctness": 4, "practices": 4, "optimality": 4, "bloat": 4, "scope": 4, "methodology": 4, "tests": 4}, "P2": {"success": 5, "correctness": 5, "practices": 4, "optimality": 4, "bloat": 4, "scope": 5, "methodology": 5, "tests": 5}, "P3": {"accuracy": 5, "completeness": 5, "conciseness": 4, "usefulness": 5}, "clarity": 4, "questions": 4}, "winner": {"P1": "tie", "P2": "Y", "P3": "Y", "overall": "Y"}}
```