# Goldfish reviewer and the full Elephant-Goldfish flow on top of v0.4.1 and bare, Sonnet 5.5 (JEB-2081), 2026-11-01

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
| Tokens, k (subagents included) | 2235 | 1524 | 1684 | 1547 | 2125 |
| Subagents in these steps: runs, k tokens | 4, 221 | — | 4, 201 | — | — |
| Subagents in deploy (P0, not counted above): runs, k tokens | 2, 152 | — | 0, 0 | — | — |
| `cost_usd` | 1.47 | 0.97 | 1.14 | 0.89 | 2.97 |
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
python bench/goldfish/compare.py --out lfb --runs lfb/runs.tsv bench/results/2026-10-20-sonnet-hard/runs.tsv \
  --arm v041gf --arm v041 --arm baregf --arm bare --arm "opus=bare opus"
```

Claude Code 2.1.300, 4 workspaces, 10 sessions, no blind judge. New bench options: `--home-extra ARM=DIR` copies
`DIR` into that arm's `HOME/.claude` (here `bench/goldfish/agents/goldfish.md` and the one-line `CLAUDE.md`),
`--steps` runs only the named case steps (T and P3 do not feed these metrics), `--no-judge` skips verdicts.
Token counts now include subagent transcripts (`claude -p` usage leaves them out; `total_cost_usd` does not).

Spend: 5.47M tokens, $3.41 (1.55M of it is the v0.4.1 deploy), over the 5M budget by 0.47M because the
v041gf P2 sessions ran 580-640k each. Coding time is left out: goldfish ran as a background subagent, and the
CLI's `duration_ms` covers only the stretch after it returned.

## Follow-up: the full Elephant-Goldfish flow (EGM), P1 only

Asked after the run: goldfish above reviews code; in [EGM](https://github.com/google/elephant-goldfish-model)
(`403d888`) the elephant writes a design spec before any code, goldfish reviewers (9 personas, 5 stages) review
the spec, a human approves it, then the code follows. Two more arms, `egm` (bare + EGM) and `egm+v041`.

**Verdict: no, and it is the most expensive arm in the bench.** On P1 EGM costs 4.8x the tokens of v041
(4.4M vs 0.9M for 2 steps) and 9x bare, $1.69 per solved step against $0.26. It does not buy quality: with
lab-forge it kills 2/4 mutants against 4/4 and writes 81% more Python; without lab-forge it fails both hidden
checks, the only false "done" in this bench. Both fails are naming, not maths: fraud writes
`{"logistic_regression": 0.585, ...}` with no PR-AUC in any key, forecast writes the 3-fold average without
`mae` in its key. The task names those metrics, and every other arm got the same check.

| Metric | egm+v041 | v041gf | v041 | egm | baregf | bare | bare opus |
|---|---|---|---|---|---|---|---|
| Solved, hidden checks | 2/2 | 2/2 | 2/2 | 0/2 | 2/2 | 2/2 | 2/2 |
| Claimed done but check fails | 0 | 0 | 0 | 2 | 0 | 0 | 0 |
| Mutants killed by the agent's tests | 2/4 | 3/4 | 4/4 | 3/4 | 2/4 | 2/4 | 3/4 |
| Bare `pytest` green after step | 2/2 | 2/2 | 2/2 | 2/2 | 1/2 | 1/2 | 2/2 |
| Ruff errors in changed files | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Python lines changed | 752 | 435 | 416 | 789 | 402 | 428 | 830 |
| Tokens, k (subagents included) | 4402 | 1014 | 914 | 3554 | 650 | 392 | 769 |
| Subagents in these steps: runs, k tokens | 18, 825 | 4, 221 | — | 18, 596 | 4, 201 | — | — |
| Subagents in deploy (P0, not counted above): runs, k tokens | 0, 0 | 2, 152 | — | 0, 0 | 0, 0 | — | — |
| `cost_usd` | 3.39 | 0.70 | 0.53 | 2.98 | 0.51 | 0.35 | 1.25 |
| `cost_usd` per solved coding step | 1.69 | 0.35 | 0.26 | — | 0.25 | 0.17 | 0.62 |

Only P1 ran. P1 alone cost 1.6-2.4M tokens per step, so P2 would have taken the run to about 16M against the
~7M estimate; both `egm` P2 sessions were cancelled within 20 s of starting (0.42M tokens, not in the table)
and `egm+v041` never started P2. The user is not there to approve the spec, so every EGM gate was
auto-approved and the elephant made each owner decision itself: that removes the part of EGM a human adds.

Spend: 9.24M recorded tokens ($7.00, of which 1.29M the v0.4.1 deploy) plus 0.42M in the cancelled sessions.

```bash
with-secrets --path=/ai -- python bench/bench.py all --out egmrun --cases fraud forecast \
  --arm egmlf=skills/lab-forge --arm egm= --home-extra egmlf=bench/egm --home-extra egm=bench/egm \
  --plugin egmlf=EGM/distributions/claude --plugin egm=EGM/distributions/claude \
  --steps P1 P2 --reps 1 --model claude-sonnet-5-5 --jobs 4 --no-judge   # P2 cancelled, see above
python bench/bench.py report --out egmrun
python bench/goldfish/compare.py --out egmrun --out lfb --runs egmrun/runs.tsv lfb/runs.tsv \
  bench/results/2026-10-20-sonnet-hard/runs.tsv --steps P1 --arm "egmlf=egm+v041" --arm v041gf --arm v041 \
  --arm egm --arm baregf --arm bare --arm "opus=bare opus"
```

`EGM` is a clone of `google/elephant-goldfish-model` at `403d888`. `bench/egm/CLAUDE.md` is the user-level
trigger: EGM skills set `disable-model-invocation`, so the session reads `egm-draft` and `egm-review`
(`uninterrupted` preset) as files; `--plugin` loads the plugin so its reviewer agents exist, and `{plugin}` in
the rules becomes its path. EGM artifacts went to `HOME/egm`, outside the project. `runs-egm.tsv` holds these rows.
