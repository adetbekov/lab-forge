# Results: model routing (C2, C5, C8), 2026-10-18

## v2: tier rule in the main thread + Stop hook (JEB-1890)

**Verdict: v2 loses as well, by less. Keep routing off by default.** On the coding steps it
cost 11% more per solved step than running everything on Opus ($0.152 vs $0.137). Both arms
solved 16/16 hidden checks. The tier-rule estimate from v1 (about −16%) did not hold: the
triage session is gone, but a delegated task still needs the main session, and that
session alone costs about 75% of a whole fixed run.

### Setup
- Cases `churn`, `rparse`, `optuna`, `encoders`, 2 repeats, agent-driven mode. Raw data:
  [`results/2026-10-18-routing-v2-fixed-vs-routed`](../results/2026-10-18-routing-v2-fixed-vs-routed/report.md).
- P0 ran once per case and repeat on Sonnet. It was copied into both arms (paths rewritten),
  then `tune.py routing on` ran in the routed HOME.
- `fixed`: each step is one Opus 5.5 session at default effort.
- `routed-v2`: the main session (Opus, the user's model) reads one override line with the
  tier rule. S goes to `quick` (Sonnet/low), M goes to `build` (Sonnet/high), and L/XL the
  main session does itself and then calls `verifier` (Haiku/low). `verify_stop.py` runs as
  Stop and SubagentStop hook: the harness runs it after every session, and a block goes
  back to that session once. The worker report goes back to the same main session, which
  is resumed for the final reply (`bench/routing/rprompt.py`).
- Only P1 and P2 ran, where routing applies. T, P3 and the blind review were skipped to
  stay within the session quota: v1 already showed them unchanged by routing (4/4 tune
  applied, quality a tie).

### Coding steps (P1 + P2)

| Metric | fixed | routed-v2 |
|---|---|---|
| Solved, hidden checks | 16/16 | 16/16 |
| Tokens, k | 939 | 1397 |
| Cost, $ (`cost.py`, v1 pricing) | 2.20 | 2.44 |
| Cost per solved step, $ | 0.137 | 0.152 |
| Escalations | — | 0/16 |
| Stop hook blocks (all false: env gap) | — | 2 |
| Files outside scope / unresolved imports | 4 / 0 | 4 / 3 |

The tokens split by role: main sessions 755k (Opus), workers 534k (Sonnet), verifier
109k (Haiku). By tier, with routed against fixed on the same steps:

| Tier | Steps | fixed, $ | routed, $ | Diff |
|---|---|---|---|---|
| quick | 7 | 0.91 | 0.98 | +8% |
| build | 5 | 0.72 | 0.82 | +14% |
| L/XL, main does it | 4 | 0.57 | 0.64 | +12% |

Every one of the 16 steps cost more in the routed arm.

### Why it loses
1. **The main session is not free.** On a delegated step the main session reads the rules,
   picks the tier, writes the handoff and later relays the report: 31-34k tokens on the
   first turn and 36-41k at the end, all on Opus. The Sonnet worker saves about half of a
   50-65k Opus run, which is less than the main session costs. On the 5.5 price sheet
   (Opus 2x Sonnet, the same cache-read price for both) a split pays off only when the
   worker's share of the tokens is far larger than the main session's.
2. **L/XL gains nothing.** The main session does the work, so cost equals fixed plus a
   Haiku verifier (about $0.002) plus the relay turn. All 4 verifier runs returned PASS.
3. **The hook added a false block and scope creep.** In optuna r2 P2,
   `tests/study_tests/test_optimize.py` fails to collect because the venv lacks `fakeredis`,
   a gap that was already there. The hook blocked the worker (no fix possible) and then
   the main session, which patched `optuna/testing/storages.py` to make the import lazy.
   That edit is outside the task and adds 3 unresolved imports.

### Fixed in this run
- `tune.py routing on/off` never overwrites or deletes a file it did not write.
  `~/.lab-forge/routing.json` stores a hash of each file it wrote; a user's own or edited
  `quick.md`/`build.md`/`verifier.md` is skipped. Test:
  `tests/test_layers.py::test_routing_leaves_user_files_alone`.
- The triage skill and the `deep` agent are removed: the tier table is one override line.
- `verify_stop.py` runs pytest on the changed test files first. The `- Test:` line in
  `state.md` is now only a fallback, and it is ignored when it holds a placeholder: deploys
  wrote values such as `uv run pytest tests/<file> -k <name>`, which ran the whole suite
  or failed.
- Hidden check `churn`: two false negatives fixed (a `vs_baseline` AUC delta of 0.0, and
  scores keyed by model name under `"metric": "roc_auc"`). `recheck` was run on every step.

### Limits
- Token counts are the Agent tool's per-session total, the same proxy v1 used, priced with
  the same assumed mix. Billing per turn would favour short sessions. Fixed sessions made
  349 tool calls in total, against 132 for routed workers plus 142 for routed main
  sessions, so the true gap could be smaller or could reverse. Only a headless run
  (`bench.py all`, which reads real `usage`) can settle it. That needs an API key or OAuth
  token on the bench machine.
- The routed main session in churn r1 P1 started `verifier` itself, as a nested subagent
  whose tokens it did not report. It is counted at v1's average of 28.5k Haiku tokens.
- n=2, one model family, synthetic tasks of 1-3 files. The tier picks were 7 quick,
  5 build and 4 L. No task was large enough for `build` to pay off.

## v1: triage session + verifier subagent (first run)

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
