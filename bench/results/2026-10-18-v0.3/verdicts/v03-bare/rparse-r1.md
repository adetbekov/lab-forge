## Scores

| Step | Criterion | X | Y |
|---|---|---|---|
| P1 | success / correctness / practices | 5 / 4 / 4 | 5 / 4 / 4 |
| P1 | optimality / bloat / scope | 3 / 2 / 4 | 5 / 5 / 4 |
| P2 | success / correctness / practices | 5 / 4 / 5 | 4 / 4 / 5 |
| P2 | optimality / bloat / scope | 3 / 3 / 4 | 5 / 5 / 5 |
| P3 | accuracy / completeness / conciseness / usefulness | 5 / 5 / 4 / 5 | 5 / 5 / 4 / 5 |
| | clarity / questions | 4 / 5 | 4 / 5 |

I ran both snapshots. X: 52 tests pass, ruff is clean, eval gives F1 0.941 and total-match 0.875. Y: 9 tests pass, ruff is clean, eval gives F1 0.837 and total-match 0.750, with delta vs baseline +0.0000.

## Defects: X

- **The eval set and the fake were built to fit each other.** X's own P1 reply says it wrote the golden set and the fake's rules together. 7 of 8 receipts score perfectly, and every layout in the golden set (column layout, two-line weighted items, `4 200,00`) has a matching regex in `rparse/clients.py:30-50`. That makes F1 0.94 mostly a regression check, not a quality measure.
- **Validation is hand-rolled and too lenient** (`rparse/parser.py:92-155`):
  - A missing `items` key defaults to `[]`. `{"total": 5}` is accepted as a valid receipt.
  - Unknown keys are ignored, and negative prices are accepted.
  - A missing `unit_price` or `line_total` is computed instead of rejected, so the retry path can never fire for that case.
- **`to_decimal` silently misreads European formats** (`rparse/models.py:30-33`). `"1.234,50"` becomes `1.23450`, with no error and so no retry.
- **Prompts are not versioned.** `SYSTEM_PROMPT` and `RETRY_PROMPT` are inline constants (`rparse/parser.py:13-38`), and the eval report does not record which prompt version was used.
- **Volume.** P1 was 1044 lines. The order-preserving DP alignment for per-field accuracy (`rparse/eval.py:143-169`) is sound, but it is heavy for this stage.

## Defects: Y

- **Fence stripping only works when the whole reply is one fenced block** (`rparse/parser.py:13`). I tested `"Here you go:\n```json{...}```"`: it failed all 3 attempts and raised `ParseError`, even though the JSON was valid.
- **Per-field accuracy is positional** (`rparse/eval.py:46`). One dropped or inserted item shifts every later item, which lowers the scores for the rest of that receipt. Y flags this in the code as a `# shortcut`.
- **The project cannot be installed as a package.** There is no `pyproject.toml`, the pydantic dependency is not declared anywhere, and pytest works only because it is run from the repo root.
- **The eval always uses the fake client** (`rparse/eval.py:81`), and there is no CLI option to choose another client. `run()` does accept a client, so a different client can be passed in from code.
- **Smaller issues:**
  - Every eval run writes a file to `eval/runs/` as a side effect, including the run inside `test_eval_cli_matches_committed_baseline`.
  - Test coverage of the fake client is thin: 2 tests.
- **On the positive side:**
  - Prompts are versioned files (`rparse/prompts/*_v1.txt`), and the prompt name is recorded in each run and in the baseline.
  - The pydantic schema uses `extra="forbid"` and has required fields.
  - The golden set keeps 2 cases the fake genuinely misses, instead of tuning the fake to pass them.

## P3

I checked more than 10 refs on each side.

**X:** all refs I checked are correct, for example `parser.py:77-78`, `:83`, `:86-89`, `:113-126`, `eval.py:212-215` and `:245`. One small slip: the `line_total` check in the golden-set test is at `tests/test_eval.py:64`, just outside the cited `57-62` range.

**Y:** all refs I checked are correct, for example `parser.py:36-37`, `:44-48`, `retry_v1.txt:1-10`, `eval.py:62-66`, `:81`, `:94-96` and `test_eval.py:37`. Its notes that a bad `max_attempts` raises plain `ValueError` rather than `ParseError`, and that the retry prompt is built after the last attempt but never sent, are both accurate. Its advice to update the baseline on purpose is useful. The `AGENTS.md` references are ignored, as instructed.

Both answers are accurate and complete, so P3 is a tie.

## Winners

- **P1: Y.** It meets every requirement with about a third of X's code. It has real schema validation, versioned prompts, and an eval whose golden set was not tuned to the fake.
- **P2: X.** Its fence and prose handling is more robust, it keeps the full attempt history, it has an end-to-end test of the eval recovering through retries, and its per-field alignment is better. Y's fence handling misses a common LLM output shape.
- **Overall: Y.** Y is a lean, idiomatic LLM-app skeleton with better hygiene: pydantic validation, versioned prompts recorded in the run, and a baseline delta. Its eval is also more honest, because the fake fails real cases instead of matching a co-designed golden set. X is more thorough and more robust in places, but it is about 3x the code, its validation is permissive enough to accept wrong data silently, and its prompts are not versioned.

```json
{"X": {"P1": {"success": 5, "correctness": 4, "practices": 4, "optimality": 3, "bloat": 2, "scope": 4}, "P2": {"success": 5, "correctness": 4, "practices": 5, "optimality": 3, "bloat": 3, "scope": 4}, "P3": {"accuracy": 5, "completeness": 5, "conciseness": 4, "usefulness": 5}, "clarity": 4, "questions": 5}, "Y": {"P1": {"success": 5, "correctness": 4, "practices": 4, "optimality": 5, "bloat": 5, "scope": 4}, "P2": {"success": 4, "correctness": 4, "practices": 5, "optimality": 5, "bloat": 5, "scope": 5}, "P3": {"accuracy": 5, "completeness": 5, "conciseness": 4, "usefulness": 5}, "clarity": 4, "questions": 5}, "winner": {"P1": "Y", "P2": "X", "P3": "tie", "overall": "Y"}}
```
