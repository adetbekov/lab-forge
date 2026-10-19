# lab-forge v0.4.1 vs v0.4 and bare (JEB-1912), 2026-10-19

**Verdict: v0.4.1 fixes "done but not solved" and meets the token target, but not the cost target.** It
solves 24 of 24 steps (v0.4: 21) and claims no false done. Tokens per solved task are 5% over bare, inside
the 10% allowance. Cost per solved task is 13% over bare, outside it. Code quality holds: the weighted score
beats bare and matches v0.4. Mutants caught drop from 18 to 16 of 24.

Only the v0.4.1 arm ran: 4 cases, 3 repeats, 60 headless sessions, then 48 blind verdicts by Fable 5.1
(v041 vs bare and v041 vs v04, both X/Y orders). The v0.4, v0.3 and bare sessions are the recorded ones from
[`2026-10-19-v0.4`](../2026-10-19-v0.4/report.md), reused as they are. Their token counts are recounted from
the session transcripts, which changes bare's numbers; see "Token counts" below. Full tables:
[`all-arms.md`](all-arms.md), pairs [`v041-bare.md`](v041-bare.md) and [`v041-v04.md`](v041-v04.md). How it
ran and the session analysis: [`notes.md`](notes.md).

## Acceptance

| Criterion | Result | Met |
|---|---|---|
| Tokens per solved task ≤ bare +10% | 424k ± 5 vs 403k ± 7, +5% | yes |
| `cost_usd` per solved task ≤ bare +10% | $0.288 ± 0.01 vs $0.254 ± 0.00, +13% | no |
| "Done but not solved" 0 of 24 | 0 of 24 (v0.4: 3) | yes |
| Weighted code score ≥ bare | 4.55 ± 0.04 vs 4.28 ± 0.04 (pair) | yes |
| Weighted code score not below v0.4 by more than 1 SE | 4.60 ± 0.02 vs 4.56 ± 0.11 (pair) | yes |
| Mutants caught ≥ 18/24 | 16/24 (v0.4: 18/24) | no |

The ± values are the standard error over the 3 repeats. The cost SE for bare rounds to $0.00.

## Head to head (overall winner per case and repeat)

| Pair | Wins | Ties |
|---|---|---|
| v041 vs bare | 10 : 2 | 0 |
| v041 vs v04 | 6 : 4 | 2 |

v041 vs v04 is within noise: X/Y order changed the winner in 18 of 48 calls.

## What changed in v0.4.1

- C7 (core, so tune cannot drop it): before "done", run the task's entry point and check that its output has
  every file, key, field and metric the task names, spelled as the task spells them. All 3 v0.4 failures were
  exactly this: an eval report that renamed `line_total` to `total`, and a metrics JSON that stored both
  ROC-AUC values under `models.logreg` / `models.gboost` with no key naming the metric.
- Always-loaded text is shorter: core and defaults (−480 characters), the repo `AGENTS.md` template (−220,
  boilerplate only), the lab-forge skill description (−390) and the four repo skill descriptions (−330). Rule
  numbers and meaning are unchanged, so existing `replaces D<n>` overrides still apply.
- Engine version 0.4.1. A 0.4.0 global layer upgrades with `upgrade.py`; a second run prints "up to date".

## Where the cost goes

Per call, a deployed v0.4 workspace sends 4.5k more input tokens than bare (measured with one-turn probes on
a v0.4 optuna workspace): global rules 2.0k, repo `AGENTS.md` 1.5k, home skill descriptions 0.5k, repo skills
and commands 0.35k. Call counts per step are close to bare once tokens are counted honestly, so this fixed
overhead is most of the gap. The v0.4.1 cuts save about 0.25k of it on the global layer (measured on a fresh install).

| Step, task tokens (calls per session) | v041 | v04 | bare |
|---|---|---|---|
| P1 | 3781k (8.9) | 4253k (9.7) | 3780k (9.8) |
| P2 | 4449k (10.4) | 4822k (10.8) | 4212k (10.7) |
| T | 670k (1.9) | 710k (2.0) | 350k (1.3) |
| P3 | 1274k (3.5) | 1257k (3.4) | 1340k (4.0) |

Cost grows faster than tokens because each session writes the extra context to the prompt cache once, at
1.25x the input price: cache writes are 1.08M for v041 vs 0.91M for bare (+19%), cache reads +4%. T cannot
reach bare: a tune must call `tune.py` and then reply, two calls where bare answers in one and stores nothing
(its tune carried over 0 of 12 times).

## Trade-off

Getting cost under +10% needs roughly 1k fewer always-loaded tokens per call, a third of what is left. That
means dropping rules, not rewording them, and the rules carry the quality win (weighted score +0.27 over bare,
10:2 head to head) and the zero false-done result. This run does not cut them.

## Token counts in the v0.4 report

`claude -p` reports usage only for the last stretch of a session that a background task resumed; its
`total_cost_usd` still covers the whole session. In the v0.4 run this hid 1.17M bare task tokens (3 sessions)
and 0.36M of v0.3's. v0.4 was not affected. The bench now takes usage from the session transcript when it is
larger (`reported_tokens` keeps the CLI number); `bench.py retokens` recounts older runs. On the recounted
numbers v0.4 was +30% over bare in tokens per solved task, not +48%. This run caught 3 such v0.4.1 sessions
too.

## Other

- Task time, 53 min vs v0.4's 126, is not comparable: 12 workspaces ran here, 36 then, on the same 6 cores.
- One `pytest` red after a step (optuna r3 P1); the hidden check still passed.
- Ruff errors in changed files: 15 (v0.4: 27, bare: 44).
- The tune carried into the next session 4 of 12 times (v0.4: 5/12). Not in scope here.
- The lost mutant is churn P2 `config-ignored`, killed 1 of 3 times (v0.4: 3 of 3): two runs tested the
  config through `get_params`, which C6 already forbids. One mutant over three repeats; not separable from
  noise in this run.
