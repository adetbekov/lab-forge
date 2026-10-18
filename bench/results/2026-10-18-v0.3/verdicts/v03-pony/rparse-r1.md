## Scores

| Dim | X P1 | Y P1 | X P2 | Y P2 |
|---|---|---|---|---|
| success | 5 | 5 | 5 | 5 |
| correctness | 3 | 4 | 4 | 4 |
| practices | 4 | 5 | 4 | 4 |
| optimality | 5 | 4 | 5 | 4 |
| bloat | 5 | 4 | 5 | 4 |
| scope | 5 | 4 | 5 | 4 |

| P3 | X | Y |
|---|---|---|
| accuracy | 5 | 5 |
| completeness | 4 | 5 |
| conciseness | 4 | 4 |
| usefulness | 4 | 5 |
| clarity | 4 | 4 |
| questions | 5 | 5 |

Verified: X: eval prints F1 0.947, total-match 1.000; 13 passed; ruff check and format are clean. Y: eval prints F1 0.8372, total-match 0.75, delta +0.0000; 9 passed; ruff check is clean, but `ruff format --check` would reformat 5 files.

## Key defects

**X**
- Eval soundness: the same author wrote the golden set and the regex fake together. 7 of 8 receipts score 1.00 and total-match is 1.000, and the only miss is a case labelled "deliberately hard" (`rparse/eval.py:60`). So the F1 says almost nothing. The reply admits it overstates quality. `tests/test_rparse.py:64` then locks in `total_rate == 1.0`, which makes adding a harder receipt fail the tests.
- `rparse/eval.py:255`: `main()` does not catch the parser's `ValueError`. Once a real client is plugged in, one bad receipt crashes the whole eval instead of scoring as a miss.
- `FakeClient.complete` gets the receipt by splitting the prompt string on `"RECEIPT:\n"` (`rparse/__init__.py:57`). That couples the fake to the prompt's wording. The prompt is an inline constant with no version.
- Per-field accuracy (`rparse/eval.py:95-106`) matches each field as its own multiset, so a correct price on an unrelated item counts as a hit. The method is weak, though the reply documents it.
- Schema checks are hand-rolled (`_parse_reply`, `rparse/__init__.py:117-138`). Extra keys are accepted silently.

**Y**
- Per-field accuracy aligns items by position (`rparse/eval.py:46`). One dropped item shifts every later field to wrong. Extra predictions are never penalized, because the denominator is n_gold. It is marked `# shortcut`.
- `FENCE` (`rparse/parser.py:13`) requires a newline after the opening fence, so a one-line block like ```` ```json {...}``` ```` is not unwrapped. It falls through to a retry instead.
- Unrequested extras: per-run files in `eval/runs/`, the baseline/`--update-baseline` machinery, and `AGENTS.md` edits. `ruff format` was not applied. `tests/test_eval.py:37` hardcodes `receipts == 8`.
- The eval is hardwired to `FakeClient` (`rparse/eval.py:81`). There is no way to pick a client, although `run(client)` is pluggable.
- Strengths: pydantic schema with `extra="forbid"`; versioned prompt files, including `retry_v1.txt`; the prompt version is recorded in eval output; system and user prompts are split; `ParseError` keeps `.raw`; parse errors are scored as misses. The golden set has real misses (thousands separators, OCR noise), so the eval numbers mean something.

**P3 refs:** I checked 15 or more references on each side and all are correct. X's warning about the F1 threshold is correct: missing 2 more items gives exactly 0.900, and the test requires a strict `>`. Y also correctly notes the baseline rewrite, the hardcoded `receipts == 8` test, and how the eval handles a parse error. Only Y's `AGENTS.md:31` reference could not be checked, because that file is not in the snapshot.

## Winners

- P1: **Y**. X is leaner, but its eval is effectively fitted to its own fake, and the eval crashes on any parse failure. Y has proper schema validation, versioned prompts and a golden set the fake genuinely misses.
- P2: **Y** (narrow). Both implement fence stripping, retry with the error fed back and clear failures. X is simpler. Y keeps the retry prompt versioned, keeps the raw output on errors, and counts parse failures in the eval.
- P3: **Y** (narrow). Both are accurate; Y covers more of the follow-through for adding a golden receipt.
- Overall: **Y**. Y's eval produces meaningful F1, and its LLM-app hygiene (pydantic validation, prompt files, pluggable system/user client, baseline tracking) is markedly better. X is tidier and smaller, but its metrics are close to self-confirming and it is less robust to a real client.

```json
{"X": {"P1": {"success": 5, "correctness": 3, "practices": 4, "optimality": 5, "bloat": 5, "scope": 5}, "P2": {"success": 5, "correctness": 4, "practices": 4, "optimality": 5, "bloat": 5, "scope": 5}, "P3": {"accuracy": 5, "completeness": 4, "conciseness": 4, "usefulness": 4}, "clarity": 4, "questions": 5}, "Y": {"P1": {"success": 5, "correctness": 4, "practices": 5, "optimality": 4, "bloat": 4, "scope": 4}, "P2": {"success": 5, "correctness": 4, "practices": 4, "optimality": 4, "bloat": 4, "scope": 4}, "P3": {"accuracy": 5, "completeness": 5, "conciseness": 4, "usefulness": 5}, "clarity": 4, "questions": 5}, "winner": {"P1": "Y", "P2": "Y", "P3": "Y", "overall": "Y"}}
```
