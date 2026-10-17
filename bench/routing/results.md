# Results: model routing (C2, C5, C8), 2026-10-18

**Verdict: routing as built loses. Do not enable it by default.** On the coding steps it
cost 28% more than running everything on Opus and solved 6/8 hidden checks against 8/8.
Blind quality was a tie (27.0 vs 26.9 of 30). The extra sessions eat the savings: the
triage session and the verifier used 470k of the 941k tokens routing spent on coding.
The component stays in the repo, off by default, behind `tune.py routing on`.

## Setup

- Bench: `bench/` cases `churn`, `rparse`, `optuna`, `encoders`, 1 repeat, agent-driven
  mode. Raw data: [`results/2026-10-18-routing-fixed-vs-routed`](../results/2026-10-18-routing-fixed-vs-routed/report.md).
- Both arms use the same lab-forge deploy. P0 ran once per case on Sonnet and was
  copied to both arms, so only routing differs.
- `fixed`: every step on Opus 5.5 at its default effort.
- `routed`: `tune.py routing on`. For P1 and P2, a triage session picks the tier, the
  tier's subagent does the work, and verifier checks it. FAIL means one retry, one tier
  up. T and P3 run in the main thread.
- Tiers: quick = Sonnet/low, build = Sonnet/high, deep = Opus/high, verifier = Haiku/low.
- Triage picked deep for 2 steps (new projects), build for 5 and quick for 1. The
  escalation rate was 1/8 (optuna P2).

## Coding steps (P1 + P2), where routing applies

| Metric | fixed | routed |
|---|---|---|
| Solved, hidden checks | 8/8 | 6/8 |
| Tokens, k | 436 | 941 |
| Cost, $ (see pricing) | 1.02 | 1.31 |
| Cost per solved step, $ | 0.13 | 0.22 |
| Blind code score, of 30 | 26.9 | 27.0 |

Routed tokens by role: workers 414k, escalation 57k, triage 211k, verifier 259k.

**Pricing.** The Agent tool reports only total tokens per session. Cost uses list prices
(Opus 5.5 $4/$20, Sonnet 5.5 $2/$10, Haiku 5.5 $0.10/$0.50 per MTok in/out, cache reads
$0.20 for both Opus and Sonnet) and an assumed agentic mix: 80% cache read, 10% cache
write, 2% fresh input, 8% output. Pricing everything at the input/output rates gives the
same direction: +16% for routing. Triage is priced as Opus, the main thread's model.

## What went wrong, and what it taught

1. **Overhead beats the price gap.** On the 5.5 price sheet Opus costs only 2x Sonnet,
   and cache reads cost the same on both. Every subagent is a new session that pays its
   own start-up (about 25k tokens) with a cold cache. Triage plus verifier add two such
   sessions to every coding task.
2. **Verifier v1 missed a real failure.** In rparse P1, deep (Opus) used a `src/` layout,
   so `python -m rparse.eval` works only through an untracked `.pth`. It also changed the
   required signature `parse_receipt(text)`. Verifier ran the eval with `PYTHONPATH=src`
   and returned PASS. Fix (v2, in this PR): run commands exactly as the task states, and
   any name/signature/path change is FAIL. Re-run on the same tree: v2 returned FAIL.
   P2 inherited the layout, so both rparse misses come from this one step.
3. **One false FAIL cost an escalation.** In optuna P2, the new tests failed to collect
   because the venv lacks `fakeredis`, a pre-existing gap. Deep moved the tests to a file
   that runs. That was correct, but it cost 87k tokens.
4. **The main thread must keep its model.** A first run put the main thread on Sonnet.
   It did not store "from now on, answer in Russian" in 4/4 cases, and 1/4 after a
   triage fix. With the main thread on Opus it stored it 4/4. Routing now changes only
   subagent models.

## Not measured

- Prompt-cache hit rate: the Agent tool does not report cache tokens. By construction
  every subagent starts on a cold prefix.
- The Stop hook (`verify_stop.py`): the simulated sessions do not run hooks. It is
  covered by unit runs only (red test blocks, green passes, unchanged tree skips).
- Codex agents: the generated TOML parses, but no Codex session was run.
- n=1 per case, one judge per case.

## Next

The cheap version to test is triage as one rule in the main thread (no separate session)
and the Stop hook instead of the verifier subagent. Repricing this run's worker tokens
that way gives about $0.85 against $1.02 for fixed (−16%), but nothing proves it yet.
