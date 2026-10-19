# lab-forge v0.4 vs v0.3 vs bare (JEB-1909), 2026-10-19

**Verdict: v0.4 writes the best code but costs more than bare, so it misses its cost target.** In blind
review it beats v0.3 8:3 and bare 9:0 head to head, with the highest weighted code score and the most
mutants caught. But it uses 48% more tokens and about 40% more money per solved task than bare, and it
is the only arm that reported a step as done when the hidden check failed (3 of 24).

All four cases, 3 repeats, 168 sessions, 72 blind verdicts by Fable 5.1 with X/Y judged in both orders.
Full tables: [`all-arms.md`](all-arms.md), pairs [`v04-v03.md`](v04-v03.md), [`v04-bare.md`](v04-bare.md),
[`v03-bare.md`](v03-bare.md). How it ran and the upgrade check: [`notes.md`](notes.md).

## Acceptance questions

| Question | Result | Met |
|---|---|---|
| Weighted code score (methodology and tests x2) v0.4 >= bare | 4.58 vs 4.32 (pair), 4.59 vs 4.34 (all arms) | yes |
| Weighted code score v0.4 > v0.3 | 4.60 vs 4.45 (pair), 4.59 vs 4.47 (all arms) | yes |
| Tokens per solved task v0.4 not worse than bare | 526k vs 355k, +48%; weighted (cache read x0.1) 121k vs 81k | no |
| `cost_usd` per solved task v0.4 not worse than bare | $0.35 ± 0.03 vs $0.25 ± 0.00 per repeat | no |
| Mutants caught | 18/24 killed vs v0.3 15/24 and bare 7/15 | yes |

The ± values are the standard error over the 3 repeats. The score gaps are several SE wide: v0.4 vs
bare 4.58 ± 0.06 vs 4.32 ± 0.03.

## Head to head (overall winner per case and repeat)

| Pair | Wins | Ties |
|---|---|---|
| v04 vs v03 | 8 : 3 | 1 |
| v04 vs bare | 9 : 0 | 3 |
| v03 vs bare | 9 : 2 | 1 |

v0.4 swept churn and encoders against v0.3. v0.3 still takes 2 of 3 optuna repeats and rparse r1. When
swapping X and Y changed the winner, the call counts as a tie: 41 of 144 calls.

## What is better

- Code: methodology 4.9 (v0.3 4.7, bare 4.7), tests 4.4 (4.2, 4.1), optimality 4.5 (4.2, 4.2),
  bloat 4.5 (4.3, 4.2).
- Bare `pytest` green after every step: 24/24 (v0.3 22/22, bare 14/24). No step committed to `main`.
- Answers to the read-only question: accuracy 4.5 and usefulness 4.4, the best of the three.
- Less code than both: 2541 Python lines changed (v0.3 2714, bare 2858).

## What is worse

- **Cost.** Task tokens 11.0M vs bare 8.5M (+30%), time 126 vs 80 min (+58%), 14.8 tool calls per solved
  task vs 11.5. Most of the extra goes to the follow-up step P2 (4.8M vs 3.0M) and to the tune step T
  (710k vs 350k). The deploy adds 689k per project, against v0.3's 613k.
- **Done but not solved: 3 steps, none for v0.3 or bare.** In churn r3, P1 and P2 never wrote the metrics
  JSON with both ROC-AUC values. In rparse r1, the P2 eval output lacks `line_total`. That is the
  "rushing to done" pain the core is meant to stop.
- Ruff errors in changed files: 27 (v0.3 15, bare 44).
- The tune phrase carried into the next session in only 5 of 12 repeats (v0.3 3/12, bare 0/12).

## Next

Rule and script changes are out of scope here (JEB-1909). A follow-up should cut P2 and T token use and
make the done check run the step's own output before claiming done. Then run this bench again.
