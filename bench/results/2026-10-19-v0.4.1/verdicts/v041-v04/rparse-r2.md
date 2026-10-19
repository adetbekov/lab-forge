Both suites pass (X 17, Y 15), both evals run from the root, and `ruff check .` fails on both with the same class of extended rules (FURB167, UP017/RUF022, C408), despite both replies claiming clean lint. I treat that as a shared minor defect.

| Step | Metric | X | Y |
|---|---|---|---|
| P1 | success / correctness / practices | 5 / 4 / 4 | 5 / 4 / 4 |
| P1 | optimality / bloat / scope | 4 / 4 / 4 | 4 / 4 / 4 |
| P1 | methodology / tests | 4 / 5 | 4 / 4 |
| P2 | success / correctness / practices | 5 / 5 / 4 | 5 / 4 / 4 |
| P2 | optimality / bloat / scope | 5 / 5 / 5 | 5 / 5 / 4 |
| P2 | methodology / tests | 5 / 5 | 5 / 4 |
| P3 | accuracy / completeness / conciseness / usefulness | 5 / 5 / 3 / 5 | 4 / 3 / 4 / 3 |
| — | clarity / questions | 4 / 4 | 4 / 3 |

**X defects**
- `rparse/eval.py:23`: the item F1 key is (name, quantity, line_total) and omits unit_price, so a wrong unit price never costs F1. Only the P2 `acc_unit_price` metric catches it.
- `rparse/client.py:12-16`: the fake is fitted to the golden layouts (Cyrillic ИТОГО, `qty x unit total`), so the 0.95 F1 measures the regex, not the parser. Both sides share this; X's reply says so.
- `tests/test_eval.py:42`: hard-coded `== 8`, and `tests/test_eval.py:51-56` runs a subprocess that writes into `evals/runs/` as a side effect.
- Thirteen lines over 100 chars; the retry-feedback test asserts on fragile substrings (`tests/test_parser.py:80`).
- P2 reply defers the prompt-version bump to the user ("Say if you want it bumped"); minor.

**Y defects**
- `rparse/parser.py:12,19-23`: `strip_fences` only matches a fence that spans the whole reply. "Here:\n```json…```" is not stripped and burns a retry (verified).
- `rparse/fake.py:23`: the fake splits the prompt on `<<<RECEIPT` delimiters, coupling it to the prompt template. Changing the prompt breaks the fake and the eval.
- `rparse/fake.py:35-36`: missing total silently falls back to a sum of items, fitted to the `no_total_line` golden row. A "ИТОГО TOTAL" line becomes an item (verified).
- `rparse/models.py:6-10`: no constraints, so empty names and negative quantities validate. `rparse/parser.py:26` has no empty-text guard and returns an empty receipt for "".
- Tests: the per-field accuracy denominator mutation (dividing by predicted count instead of gold count) survived the suite. `tests/test_eval.py:64-66` only asserts values lie in [0,1]. `golden/baseline.json` stores `latency_s`, so every run prints a noisy latency delta.
- P3: `eval.py:77` should be 78 and `eval.py:90` should be 89. More importantly Y says it did not check whether tests hard-code the count; `tests/test_eval.py:25` does (`== 8`) and `tests/test_eval.py:49-53` gates on the baseline, so adding a receipt that lowers F1 breaks the suite. That gap was one file read away.

**Mutation checks (scratch copies)**: F1 formula, fake quantity, None-as-total-hit, fence no-op, dropped retry feedback, extra attempt, case-sensitive field match, always-hit field: all caught by both. Y missed only the accuracy denominator.

**Winners**
- P1: X, narrowly. Y's eval matches on all four fields and has a perfect-client sanity test, but X's constrained models, empty-text guard, and a fake decoupled from the prompt are more robust foundations. Both fakes are fitted to their golden sets.
- P2: X. Its fence stripping tolerates leading prose, every mutation was caught, and the diff is equally lean.
- P3: X. Every one of the 19 refs I checked was right, and it surfaced the hard-coded count test that Y left for the user to discover.
- Overall: X. The implementations are close in size and quality, but X is stricter where it matters for an LLM app (schema constraints, fence tolerance, test coverage) and its answer was verified rather than hedged.

```json
{"X": {"P1": {"success": 5, "correctness": 4, "practices": 4, "optimality": 4, "bloat": 4, "scope": 4, "methodology": 4, "tests": 5}, "P2": {"success": 5, "correctness": 5, "practices": 4, "optimality": 5, "bloat": 5, "scope": 5, "methodology": 5, "tests": 5}, "P3": {"accuracy": 5, "completeness": 5, "conciseness": 3, "usefulness": 5}, "clarity": 4, "questions": 4}, "Y": {"P1": {"success": 5, "correctness": 4, "practices": 4, "optimality": 4, "bloat": 4, "scope": 4, "methodology": 4, "tests": 4}, "P2": {"success": 5, "correctness": 4, "practices": 4, "optimality": 5, "bloat": 5, "scope": 4, "methodology": 5, "tests": 4}, "P3": {"accuracy": 4, "completeness": 3, "conciseness": 4, "usefulness": 3}, "clarity": 4, "questions": 3}, "winner": {"P1": "X", "P2": "X", "P3": "X", "overall": "X"}}
```