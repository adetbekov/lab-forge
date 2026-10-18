# lab-forge v0.3: v0.2 plus ponytail's ideas (JEB-1895), 2026-10-18

**Verdict: ship v0.3.** In blind review it beats every other arm head to head: v0.2 3:1,
ponytail 4:0, bare 3:1. It makes no edits outside the task (v0.2 made 2), answers
questions with more accurate `file:line` refs (4.8 vs 4.2), and finishes 19% faster.
The code sum is a tie with v0.2 (27.8 vs 28.1, within ±2). v0.3 still lost churn,
where it fitted calibration and the threshold on the same validation rows.

## What changed against v0.2

Two templates, both within their line budgets:

- `assets/templates/global-agents.md` (still 60 lines):
  - Rule 8 is now ponytail's ladder: skip it, reuse the repo, stdlib, an installed
    dependency, one line, and only then new code.
  - Rule 9: "Lean on the solution, never on the change". Code must not be right by accident
    (loop leftovers, dict order, the cwd), and a known limit is marked `# shortcut: ...`.
  - Rule 11: never cut validation of untrusted input or error handling that guards data.
  - Rule 12: no CHANGELOG, baseline or other artifacts unless asked.
  - Rule 15: no narration of hooks or rules, and cite `file:line` only after reading those
    lines.
  - Rule 17: the `DONE` / `DONE_WITH_CONCERNS` status token is replaced by one closing
    line saying what was skipped and the risk.
- `assets/templates/skill-self-review.md`: a new "By accident" check.

## Result

Same cases, seed and fixtures as [`2026-10-18-ponytail`](../2026-10-18-ponytail/report.md),
1 repeat. v03 ran 20 new sessions; the other three arms are reused as they were.

| | v03 | v02 | pony | bare |
|---|---|---|---|---|
| Hidden checks solved | 8/8 | 8/8 | 8/8 | 8/8 |
| Task tokens, k (no deploy) | 852 | 839 | **620** | 676 |
| Task time, min | 40.2 | 49.8 | **35.2** | 54.5 |
| All lines changed | 1029 | 1071 | **793** | 2373 |
| Files outside task scope | **0** | 2 | **0** | 2 |
| Coding steps on `main` | **0/8** | **0/8** | 8/8 | 8/8 |
| Tune applied next session | 4/4 | 4/4 | 3/4 | 4/4 |
| pytest red after step | 1 | 0 | 0 | 0 |

Head to head (blind, overall winner per case):

| Pair | churn | encoders | optuna | rparse | Score | Code sum | P3 accuracy |
|---|---|---|---|---|---|---|---|
| v03 vs v02 | v02 | v03 | v03 | v03 | **3:1** | 27.8 vs 28.1 | 4.8 vs 4.2 |
| v03 vs pony | v03 | v03 | v03 | v03 | **4:0** | 27.5 vs 28.2 | 4.8 vs 4.5 |
| v03 vs bare | bare | v03 | v03 | v03 | **3:1** | 28.1 vs 25.2 | 4.8 vs 5.0 |

Against ponytail, v03 wins every case even though its code sum is lower. Ponytail
maxes out bloat and scope, while v03 wins on practices (4.8 vs 4.1), correctness and the
answers. The code sum weights those five criteria equally, so the two signals disagree.

Details: [`v03-v02.md`](v03-v02.md), [`v03-pony.md`](v03-pony.md), [`v03-bare.md`](v03-bare.md),
[`all-arms.md`](all-arms.md), verdicts in `verdicts/<pair>/`.

## Why

1. **The scope rule worked.** In `encoders`, v0.2 and bare both added CHANGELOG entries
   to a released section. v03 did not, and said so in its reply.
2. **"Cite only what you read" fixed the rparse answers.** v0.2 cited lines past the end
   of `eval.py` (a run in the model-mix round did the same). v03's refs were all accurate,
   and that alone won it rparse against v0.2.
3. **Tests moved to the repo's own patterns.** In optuna, v03 put the warning test in
   `test_optimize.py` with the existing caplog fixture. Two reviewers named that as the
   deciding point. The cost: that file needs `fakeredis`, which the bench venv lacks, so
   the bench's pytest run went red. The hidden check passed.
4. **Churn is still the weak case.** v03 calibrated on the validation split and then
   picked the threshold on the same rows. v0.2 and bare calibrated with CV on train. A
   follow-up (v04) added "never fit two things on the same rows" to the classic-ml
   profile's slop list and reran churn. The rule never reached the repo `AGENTS.md`,
   and the agent did the same thing again, arguing that sigmoid calibration is
   monotone. That change was reverted and is not in v0.3. Next time, put it in the
   profile's invariants, which deploy copies.

## Limitations

- One repeat. Reviewers and agents are the same model family. Replies that cite
  `AGENTS.md` partly reveal the arm.
- v03 tokens are +2% vs v0.2 and +26% vs bare. In agent-driven mode, every guard-hook
  call is a simulated shell command, so this needs a headless recheck.
