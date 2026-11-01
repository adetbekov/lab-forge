# Goldfish reviewer on top of v0.4.1 and bare, Sonnet 5.5, fraud and forecast (JEB-2081), 2026-11-01

**Verdict: goldfish does not pay off on these cases, with or without lab-forge.** Every arm solves 4/4 coding
steps with 0 false "done", so the hidden checks cannot separate them. With lab-forge it is worse on everything
measured: 7/9 mutants killed against 9/9, 17% more Python lines, +47% tokens and +52% cost per solved step.
Without lab-forge it changes nothing measured (5/9 mutants, bare `pytest` 2/4, 1 ruff error, same as bare) for
+9% tokens and +28% cost. n=1 per arm, so this is a direction, not a measurement.

| Metric | v041gf | v041 | baregf | bare | bare opus |
|---|---|---|---|---|---|
| Solved, hidden checks | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 |
| Claimed done but check fails | 0 | 0 | 0 | 0 | 0 |
| Mutants killed by the agent's tests | 7/9 | 9/9 | 5/9 | 5/9 | 7/9 |
| Bare `pytest` green after step | 4/4 | 4/4 | 2/4 | 2/4 | 4/4 |
| Ruff errors in changed files | 0 | 0 | 1 | 1 | 0 |
| Python lines changed | 727 | 624 | 722 | 742 | 1521 |
| Tokens, k (P1+P2, goldfish included) | 2235 | 1524 | 1684 | 1547 | 2125 |
| of which goldfish, k | 221 | — | 201 | — | — |
| Goldfish runs in P1+P2 | 4 | — | 4 | — | — |
| Goldfish in deploy (P0, not in the rows above): runs, k tokens | 2, 152 | — | 0, 0 | — | — |
| `cost_usd`, P1+P2 | 1.47 | 0.97 | 1.14 | 0.89 | 2.97 |
| `cost_usd` per solved coding step | 0.37 | 0.24 | 0.28 | 0.22 | 0.74 |

v041, bare and bare opus are the P1 and P2 rows of [`2026-10-20-sonnet-hard/runs.tsv`](../2026-10-20-sonnet-hard/runs.tsv)
(bench code unchanged since `eb6db14` apart from the options below), so their cost per step is lower here
than in that report, which also counted T and P3. Goldfish tokens are counted from the subagent transcripts.

## What goldfish found

It ran once per coding step in all 8 steps (`model: inherit`, read and bash only, task text as the only
input). Its findings were real but are not what the mutants and hidden checks measure: tests that would still
pass with the threshold fitted on test instead of validation, an `--as-of` cutoff off by one at midnight,
a training mask that may see the forecast window, a seasonal-naive baseline no test pins. Each review also
flagged "not committed", because the session calls goldfish before it commits. The main session's fixes added
code and tokens, not mutant kills; in the v041gf arm the forecast tests killed fewer mutants than v041 did.

The deploy step (P0) in v041gf also ran goldfish once per project (152k tokens, outside the table): the
CLAUDE.md line asks for it on "any task that changes code" and the deploy writes files.

## Run

```bash
with-secrets --path=/ai -- python bench/bench.py all --out lfb --cases fraud forecast \
  --arm v041gf=skills/lab-forge --arm baregf= --home-extra v041gf=bench/goldfish --home-extra baregf=bench/goldfish \
  --steps P1 P2 --reps 1 --model claude-sonnet-5-5 --jobs 4 --no-judge
python bench/goldfish/compare.py lfb bench/results/2026-10-20-sonnet-hard/runs.tsv
```

Claude Code 2.1.300, 4 workspaces, 10 sessions, no blind judge. New bench options: `--home-extra ARM=DIR` copies
`DIR` into that arm's `HOME/.claude` (here `bench/goldfish/agents/goldfish.md` and the one-line `CLAUDE.md`),
`--steps` runs only the named case steps (T and P3 do not feed these metrics), `--no-judge` skips verdicts.
Token counts now include subagent transcripts (`claude -p` usage leaves them out; `total_cost_usd` does not).

Spend: 5.47M tokens, $3.41 (1.55M of it is the v0.4.1 deploy), over the 5M budget by 0.47M because the
v041gf P2 sessions ran 580-640k each. Coding time is left out: goldfish ran as a background subagent, and the
CLI's `duration_ms` covers only the stretch after it returned.
