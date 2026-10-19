| | X P1 | Y P1 | X P2 | Y P2 |
|---|---|---|---|---|
| success | 5 | 5 | 5 | 5 |
| correctness | 4 | 4 | 4 | 3 |
| practices | 4 | 4 | 4 | 4 |
| optimality | 4 | 3 | 4 | 4 |
| bloat | 4 | 3 | 4 | 4 |
| scope | 4 | 3 | 4 | 4 |
| methodology | 4 | 4 | 4 | 4 |
| tests | 3 | 4 | 5 | 4 |

P3: X accuracy 5 / completeness 5 / conciseness 4 / usefulness 4. Y 5 / 5 / 4 / 5. Clarity X 4, Y 4. Questions X 5, Y 5.

Verified: both snapshots pass 16 tests under `pytest` and `python -m pytest`, eval runs offline and matches its committed baseline (X F1 0.958, Y F1 0.872). Under the venv's ruff rule set X has 1 finding, Y has 8 (unsorted imports, `re.I` aliases, unclosed `open` in `tests/test_eval.py:51`).

**X defects**
- `rparse/eval.py:39-46`: field accuracy pairs each gold item with the best unused prediction even when zero fields match. A completely wrong item (`ZZZ`, qty 1) still scores a quantity hit, so the field metric is inflated. Reproduced: name 0.0, quantity 1.0.
- F1 formula is not pinned by tests. Replacing it with precision, or with the mean of P and R, leaves all 16 tests green, because every test case has P equal to R (P1 defect).
- `rparse/eval.py:60`: parse failures become a sentinel `Receipt(items=[], total=-1)` rather than a counted error.
- `rparse/fake.py:29`: a prompt without a `<receipt>` block raises a bare `IndexError`.
- No prompt version is recorded anywhere, so eval runs are not comparable across prompt edits.

**Y defects**
- `rparse/parser.py:33`: `max_attempts or default_max_attempts()` means `max_attempts=0` silently makes 3 calls (reproduced), and `max_attempts=-1` raises `UnboundLocalError` at line 42 instead of a clear error. The reply discloses the 0 case as if it were a feature.
- `rparse/parser.py:11`: the fence regex anchors to the whole reply, so JSON with prose around the fence fails all retries. X handles this.
- `rparse/models.py:6-10`: no constraints, so empty names and negative quantities validate (reproduced).
- `rparse/client.py:9-12, eval.py:17-24, 85-86`: `Completion.cost_usd`, `_Metered`, latency and cost reporting are unrequested plumbing for an offline fake.
- Field-accuracy pairing reuse mutation (`eval.py:47` pop → index) survives the tests.
- `rparse/eval.py:108-115`: prints deltas but never fails on regression; X exits 1 below baseline.

**Eval soundness, both sides.** Each fake was written alongside its own golden set, so the F1 measures the fake's regex coverage, not any model. Both honestly left failing cases in (X: multiline item; Y: `KIOSK 7` header and two-line items) and said so. Y's prompt versioning and parse-error count are the better hygiene; X's baseline gate is the better regression guard.

**P3.** All sampled refs on both sides match the snapshots (X: `parser.py:38-39, :64-66, :69-78, eval.py:56-60, :107-122`; Y: `parser.py:18-20, :33-42, prompts.py:21-27, eval.py:65-68, :98, :117-120`). X adds the exit-code gating detail. Y adds the useful caveat that a new receipt format may just drop the fake's score. Tie.

**Winners.** P1: X, narrowly. X's design is leaner with validated models and a regression gate, though Y's hand-computed F1 test is the one that actually pins the metric. P2: X. X's retry path handles prose around fences and rejects bad attempt counts cleanly, while Y's `or` fallback is a real bug with a crash on negative input. Overall: X, for fewer correctness bugs and less unrequested machinery, with the F1 test gap and loose field pairing as its main debts.

```json
{"X": {"P1": {"success": 5, "correctness": 4, "practices": 4, "optimality": 4, "bloat": 4, "scope": 4, "methodology": 4, "tests": 3}, "P2": {"success": 5, "correctness": 4, "practices": 4, "optimality": 4, "bloat": 4, "scope": 4, "methodology": 4, "tests": 5}, "P3": {"accuracy": 5, "completeness": 5, "conciseness": 4, "usefulness": 4}, "clarity": 4, "questions": 5}, "Y": {"P1": {"success": 5, "correctness": 4, "practices": 4, "optimality": 3, "bloat": 3, "scope": 3, "methodology": 4, "tests": 4}, "P2": {"success": 5, "correctness": 3, "practices": 4, "optimality": 4, "bloat": 4, "scope": 4, "methodology": 4, "tests": 4}, "P3": {"accuracy": 5, "completeness": 5, "conciseness": 4, "usefulness": 5}, "clarity": 4, "questions": 5}, "winner": {"P1": "X", "P2": "X", "P3": "tie", "overall": "X"}}
```