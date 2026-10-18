## Scores

| Dim | X P1 | Y P1 | X P2 | Y P2 |
|---|---|---|---|---|
| success | 5 | 5 | 5 | 5 |
| correctness | 4 | 4 | 5 | 3 |
| practices | 4 | 4 | 4 | 4 |
| optimality | 4 | 4 | 4 | 4 |
| bloat | 4 | 4 | 4 | 4 |
| scope | 4 | 4 | 5 | 4 |

| P3 / global | X | Y |
|---|---|---|
| accuracy | 2 | 5 |
| completeness | 4 | 4 |
| conciseness | 4 | 4 |
| usefulness | 3 | 5 |
| clarity | 4 | 4 |
| questions | 5 | 5 |

Verified: both snapshots run `python -m rparse.eval` cleanly, pytest passes (X 10, Y 9), and ruff is clean on both.

## Defects: X

- Golden set is easy and reads as tuned to the fake. 7 of 8 receipts score F1 1.000, every receipt has a total, and there are no discount, thousands-separator or no-total cases (`evals/golden/*`). As a result F1 0.894 says little.
- The retry feedback is appended to the system prompt (`rparse/parser.py:45`) rather than sent as a follow-up user turn. It works, but it is unconventional.
- The line-total field is named `total` (`rparse/models.py:17`), the same name as the receipt total. This is ambiguous next to the requested "line total".
- P3 refs are largely wrong. All `eval.py` refs are fabricated: `:101-105`, `:146`, `:155`, `:158-161`, `:179-181` point past the end of a 110-line file (the real lines are 26-30, 80, 83-86, 104-105). `models.py:21,36` and `:28-32` are wrong (real: 12, 27, 19-23). It also cites `tests/test_parser.py:41-44,77-79` as covering client exceptions, but those tests cover invalid replies and exhausted retries.
- Strengths: the arithmetic validator (`models.py:19-23`), greedy best-match pairing for per-field accuracy (`eval.py:37-46`), fence regex that also handles one-line fences, `raise ... from error`, and a `PROMPT_VERSION` bump.

## Defects: Y

- Per-field accuracy uses positional alignment (`rparse/eval.py:46`). One extra or missing item shifts every later item. Y documents this as a shortcut, but it distorts the new metric on its own `thousands-space` case.
- The fence regex requires a newline after the opening fence (`rparse/parser.py:13`), so a one-line fence such as ```` ```json {...}``` ```` is not stripped and wastes a retry.
- The schema has no constraints (`models.py:8-14`): empty names and negative quantities are accepted, and there is no arithmetic check.
- The fake emits floats (`client.py:28-29`), and `ParseError` is not chained to the `ValidationError` (`parser.py:48`).
- The retry prompt version is not recorded in the eval output, and every eval run, including the one inside the test, writes a new timestamped file to `eval/runs/`.
- Strengths: harder and more honest golden set (thousands separators, discount, tip/tax, no total, OCR noise) with 2 genuine misses; prompts versioned as files; retry goes as a user turn that includes the OCR text; a CLI test pins the baseline. In P3, every one of the ~20 refs I checked is correct, and it adds non-obvious points (the retry prompt is built after the last attempt but never sent; an invalid `expected` crashes the eval).

## Winners

- P1: tie. X has the stronger schema; Y has the more meaningful eval set.
- P2: X. Best-match field pairing, more robust fence stripping and exception chaining make it the more correct implementation.
- P3: Y. Its refs are accurate; about half of X's are wrong, including a false claim about test coverage.
- Overall: Y, narrowly. The code differences are modest and partly offset (X wins P2 on correctness, Y has a sounder golden set). X's P3 answer, however, gives the user line numbers that do not exist, which is a real trust defect for a question that explicitly asked for file:line references.

```json
{"X": {"P1": {"success": 5, "correctness": 4, "practices": 4, "optimality": 4, "bloat": 4, "scope": 4}, "P2": {"success": 5, "correctness": 5, "practices": 4, "optimality": 4, "bloat": 4, "scope": 5}, "P3": {"accuracy": 2, "completeness": 4, "conciseness": 4, "usefulness": 3}, "clarity": 4, "questions": 5}, "Y": {"P1": {"success": 5, "correctness": 4, "practices": 4, "optimality": 4, "bloat": 4, "scope": 4}, "P2": {"success": 5, "correctness": 3, "practices": 4, "optimality": 4, "bloat": 4, "scope": 4}, "P3": {"accuracy": 5, "completeness": 4, "conciseness": 4, "usefulness": 5}, "clarity": 4, "questions": 5}, "winner": {"P1": "tie", "P2": "X", "P3": "Y", "overall": "Y"}}
```
