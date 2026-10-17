## Scores

| Step | Criterion | X | Y |
|---|---|---|---|
| P1 | success / correctness / practices | 4 / 4 / 5 | 4 / 3 / 4 |
| P1 | optimality / bloat / scope | 4 / 4 / 4 | 4 / 4 / 4 |
| P2 | success / correctness / practices | 5 / 5 / 5 | 5 / 3 / 3 |
| P2 | optimality / bloat / scope | 4 / 4 / 5 | 4 / 4 / 4 |
| P3 | accuracy / completeness / conciseness / usefulness | 5 / 5 / 4 / 5 | 5 / 5 / 4 / 5 |
| - | clarity / questions | 4 / 4 | 4 / 4 |

Verified by running both snapshots. X: 45 tests pass, ruff clean, eval F1 0.877 and total-match 0.75. Y: 20 tests pass, ruff clean, eval F1 0.571 and total-match 0.75.

## X defects
- **Eval needs an untracked venv change.** The `src/` layout means `python -m rparse.eval` only works because of a `.pth` file the agent wrote into the venv. That file is outside git, so in a fresh clone the eval fails until someone runs `pip install -e .`. The agent did flag this.
- **Fake client looks fitted to the golden set.** Nearly every rule matches one golden receipt: the `kg x 2.80/kg` suffix and the name-then-qty-line state (`fake_client.py:15,22-24,70`) match r02 and r08, the `amount due` rule (`:33`) matches r08, and the tax-flag letters (`:14`) match r04. The labels and the rules were written together. Real gaps remain (r03, r04, r05), but the 0.877 F1 is optimistic.
- **Empty receipts are rejected.** `Receipt.items` has `min_length=1` (`schema.py:24`), so a valid receipt with no items fails validation.
- **Logging and naming nits.** Every failed attempt that will be retried is logged at ERROR (`parser.py:52`). Having both `rparse/eval.py` and `rparse/evals/` is confusing.

## Y defects
- **Required `total` breaks the eval methodology.** `Receipt.total` is required (`schema.py:21`), and the fake leaves out `total` when there is no TOTAL line (`fake_client.py:71`). So 005 and 006 become parse errors that score 0 items even though the items were extracted. Each one also burns 3 identical retries. The F1 mixes up "no total found" with "item extraction failed", and the schema pushes a real model to invent a total.
- **Receipt content leaks into logs and retry prompts.** The raw response and the full pydantic error, including `input_value`, are logged at WARNING (`parser.py:49-56`). The same noisy `str(err)`, with errors.pydantic.dev URLs and input values, is fed back as the retry prompt (`parser.py:58`).
- **Prompt version not bumped.** `PROMPT_VERSION` stays `v1` even though a retry prompt was added (`prompts.py:3,20-29`), so result files from before and after retries can't be told apart.
- **Tolerance is too loose.** `money_tolerance` 0.01 is inclusive and also applied to quantity (`scorer.py:29-31`): 1.20 vs 1.21 counts as a match, and so does 0.540 kg vs 0.55 kg.
- **Smaller issues:**
  - `write_result` overwrites a result file if two runs land in the same second (`runner.py:62`).
  - `plans/bootstrap.md` is committed although nobody asked for it.
  - Empty text is not checked.

## P3
I checked more than 10 refs for each side. For X: `parser.py:26-29,46,48,49-59,60-65,66-67`, `runner.py:25-39,46-51`, `scorer.py:96`, `test_golden.py:14-18,21-26`. For Y: `parser.py:16-18,41-42,45,47,48-56,57-58,59-68`, `runner.py:20-32,40-47`, `scorer.py:60-63`, `test_eval.py:104-111`. All are accurate on both sides, and both describe the step-by-step flow correctly. X adds `raw_output`/`__cause__` and the labelling conventions. Y correctly notes that the raw response gets logged. The two are equivalent.

## Winners
- **P1: X.** X has the sounder schema (nullable total), keeps receipt content out of logs, has more meaningful tests, and has a documented labelling convention. Y's fake is more honest, but its required total distorts the eval.
- **P2: X.** X's retry loop feeds back clean `loc: msg` errors, bumps the prompt version, keeps logs free of receipt content, and has thorough retry tests. Y's version works, but its hygiene is weaker.
- **P3: tie.**
- **Overall: X.** Both meet the explicit requirements, and both eval harnesses run offline. X makes better LLM-app decisions: nullable total, no receipt content in logs, prompt versioning and structured error feedback. Its weak points are a fake client that is arguably fitted to the golden set and an eval that depends on an untracked venv tweak. Y's simpler, less fitted fake gives a more honest baseline, but its schema choice corrupts the F1 and its retry prompt and logging are sloppier.

```json
{"X": {"P1": {"success": 4, "correctness": 4, "practices": 5, "optimality": 4, "bloat": 4, "scope": 4}, "P2": {"success": 5, "correctness": 5, "practices": 5, "optimality": 4, "bloat": 4, "scope": 5}, "P3": {"accuracy": 5, "completeness": 5, "conciseness": 4, "usefulness": 5}, "clarity": 4, "questions": 4}, "Y": {"P1": {"success": 4, "correctness": 3, "practices": 4, "optimality": 4, "bloat": 4, "scope": 4}, "P2": {"success": 5, "correctness": 3, "practices": 3, "optimality": 4, "bloat": 4, "scope": 4}, "P3": {"accuracy": 5, "completeness": 5, "conciseness": 4, "usefulness": 5}, "clarity": 4, "questions": 4}, "winner": {"P1": "X", "P2": "X", "P3": "tie", "overall": "X"}}
```
