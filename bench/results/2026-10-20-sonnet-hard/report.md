# lab-forge v0.4.1 vs bare on Sonnet 5.5, two hard cases (JEB-1915), 2026-10-20

**Verdict: yes, use v0.4.1 by default on Sonnet.** On the two new hard cases both arms solve every step, so
the hidden checks do not separate them, and the blind judge calls both cases a tie (each verdict flipped with
the X/Y order). Where they differ, v0.4.1 is ahead: its tests kill 9 of 9 mutants against 5 of 9, its suite
runs under bare `pytest` in 4 of 4 steps against 2 of 4, it changes 16% fewer Python lines, never commits to
`main`, and its coding steps took 14.5 min against 36.1. Task tokens are equal (−2%), task cost is 10% higher
($0.32 vs $0.29 per solved step), plus a one-off deploy of 643k tokens, about $0.30 per project. One
repeat per arm, so this is a direction, not a measurement.

| Metric | v0.4.1 | bare |
|---|---|---|
| Blind weighted code score, 1-5 | 4.3 | 4.3 |
| Blind code sum of 30 | 25.4 | 25.6 |
| Blind overall winner (fraud, forecast) | tie, tie | tie, tie |
| Solved, hidden checks | 4/4 | 4/4 |
| Claimed done but check fails | 0 | 0 |
| Mutants killed by the agent's tests | 9/9 | 5/9 |
| Bare `pytest` green after step | 4/4 | 2/4 |
| Python lines changed | 624 | 742 |
| Task tokens, k (P1-P3, no deploy) | 1761 | 1789 |
| `cost_usd`, tasks (P1-P3) | 1.29 | 1.17 |
| `cost_usd` per solved coding step | 0.32 | 0.29 |
| `cost_usd`, deploy (2 projects) | 0.59 | — |
| Coding time, min | 14.5 | 36.1 |
| Tune phrase applied in the next session | 0/2 | 0/2 |

## The cases

Both are new, synthetic projects (no fixture to clone) with a P1 → P2 chain where P2 changes what P1 built:

- `fraud`: card fraud on transaction histories. P1 asks for per-user history features in
  `fraud.features.build_features` that see only the user's earlier transactions, a time split and PR-AUC; P2
  adds a validation period, a cost-minimizing threshold (miss 50, false alarm 1), a 7-day distinct-category
  feature and `--as-of`. The hidden check runs the entry point twice and probes the feature function: later
  transactions, flipped labels and other users must not move a feature.
- `forecast`: daily store sales with a rolling-origin backtest. P1 asks for lag and rolling features of each
  store's own past; P2 says forecasts are issued 7 days ahead, so every feature and the baseline must use only
  sales from `horizon` days earlier, adds WAPE, `best_model` and `--horizon 14`. The check probes
  `make_features` at horizons 7 and 14 (a rolling mean that includes the day itself, or a lag of 1 left from P1,
  fails) and checks that `--horizon 14` changes the WAPE.

Mutants: swapped `predict_proba`, reversed `sort_values` and swapped `confusion_matrix` cells (fraud); dropped
`shift`, 1.5x regressor predictions and every multi-period `shift` cut to 1 (forecast). `costs-swapped` was
n/a in both fraud arms: neither used `confusion_matrix`.

Both checks were tested on a reference solution (pass), an empty project (fail) and leaky feature functions
(fail, see `bench/test_bench.py`). The traps did not catch anyone: on these prompts Sonnet 5.5 writes
point-in-time features with or without lab-forge. bare lost on tests and packaging, not on correctness.

## Run

```bash
with-secrets --path=/ai -- python bench/bench.py all --out lfb --cases fraud forecast \
  --arm v041=skills/lab-forge --arm bare= --reps 1 --model claude-sonnet-5-5 --jobs 4 --judge-jobs 4
python bench/bench.py recheck --out lfb && python bench/bench.py report --out lfb
```

Claude Code 2.1.300, 4 workspaces (18 sessions), 4 verdicts by `claude-fable-5-1`, X/Y in both orders.
`--cases` takes space-separated names. The first pass failed v0.4.1's forecast P2: its `make_features`
raises `ValueError` for `horizon=14` with its default lags (7, 14, ...), while the backtest drops lags shorter
than the horizon and `--horizon 14` works. That is a deliberate guard, not a leak, so the check now accepts a
`ValueError` at horizon 14 (the run with `--horizon 14` still has to pass), and `recheck` scored it solved.
No session was rerun.

Tune: both v0.4.1 projects wrote "Answer questions about this project in Russian." under `## Overrides` in
`AGENTS.md` (imported by `CLAUDE.md`), yet the next session answered in English, the same as bare. The
v0.4.1 run got 4/12 here; with n=2 this is not a finding yet, but it is the one place v0.4.1 did not beat bare.

The generated report follows.

## Generated report: v041 vs bare

## First-round conclusions: 5/6 reproduced

| Conclusion | First round | This run | Holds |
|---|---|---|---|
| Less code with lab-forge (≤ −15%) | −30% | -16% | yes |
| Blind bloat score higher with lab-forge | 4.75 vs 3.6 | 4.50 vs 4.25 | yes |
| Explicit requirements: lab-forge not better | 3.75 vs 4.75 | 4.62 vs 4.62 | yes |
| Task tokens within ±15% | +3% | -2% | yes |
| Deploy costs 40-100k tokens per project | 48-90k | 643k | no |
| Overall quality a tie (±2 of 30) | 25.0 vs 24.9 | 25.4 vs 25.6 | yes |
| LLM project won by lab-forge | A won c2 | 0/0 repeats | — |

## Objective metrics

| Metric | v041 | bare |
|---|---|---|
| Solved, hidden checks | 4/4 | 4/4 |
| Claimed done but check fails (committed, not solved) | 0 | 0 |
| pytest red after step | 0 | 0 |
| Task tokens, k (all steps except deploy) | 1761.3 | 1788.9 |
| Tokens per solved task, k | 440.3 | 447.2 |
| Cost per solved task, $ | 0.3 | 0.3 |
| Task time, min | 14.5 | 36.1 |
| Deploy tokens per project, k | 643.0 | — |
| Python lines changed (no AI files) | 624 | 742 |
| All lines changed (no AI files) | 744 | 874 |
| Largest new .py file, lines | 79 | 66 |
| Tests added | 23 | 21 |
| Files changed outside task scope | 0 | 0 |
| Coding steps committed straight to main | 0/4 | 4/4 |
| Coding steps left uncommitted | 0 | 0 |
| Ruff errors in changed files | 0 | 1 |
| Imports that do not resolve | 0 | 0 |
| Questions in coding-step replies | 0 | 0 |
| Files written during read-only question | 0 | 0 |
| Tune phrase applied in next session | 0/2 | 0/2 |
| Style stability across repeats (0-1) | — | — |
| Tool calls per solved task | 12.0 | 13.8 |
| Weighted tokens per solved task, k (cache read x0.1, write x1.25) | 106.2 | 99.1 |
| Bare `pytest` green after step | 4/4 | 2/4 |
| Mutants killed by the agent's tests | 9/9 | 5/9 |

## Spread over repeats (mean ± SE)

| Metric | v041 | bare |
|---|---|---|
| Tokens per solved task, k | 440.32 (n=1) | 447.22 (n=1) |
| Cost per solved task, $ | 0.32 (n=1) | 0.29 (n=1) |
| code sum of 30 | 25.38 (n=1) | 25.62 (n=1) |
| weighted code score, 1-5 | 4.29 (n=1) | 4.35 (n=1) |

## Blind review (4 verdicts, 1-5)

| Criterion | v041 | bare |
|---|---|---|
| clarity | 4 | 4.2 |
| code:bloat | 4.5 | 4.2 |
| code:correctness | 4.2 | 4.8 |
| code:methodology | 4.9 | 4.5 |
| code:optimality | 4 | 4.1 |
| code:practices | 4 | 3.8 |
| code:scope | 4 | 4.1 |
| code:success | 4.6 | 4.6 |
| code:tests | 3.9 | 4.2 |
| question:accuracy | 3.8 | 4 |
| question:completeness | 4 | 5 |
| question:conciseness | 4.5 | 3.5 |
| question:usefulness | 3.8 | 4.5 |
| questions | 4.2 | 4.8 |
| **code sum of 30** | 25.4 | 25.6 |
| **weighted code score, 1-5** | 4.3 | 4.3 |

## Winners by case and repeat

| case-repeat | steps…, overall |
|---|---|
| forecast-r1 | tie, tie, v041, tie |
| fraud-r1 | tie, tie, bare, tie |

X/Y order changed the winner in 6 of 8 calls; those count as ties.
