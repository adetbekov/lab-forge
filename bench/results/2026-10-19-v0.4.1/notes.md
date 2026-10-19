# JEB-1912: how the v0.4.1 bench ran, and the v0.4 session analysis

## Run

One out dir holds all four arms. The v0.4, v0.3 and bare workspaces of the v0.4 run (same seed, so the same
workspace names) were linked in read-only, with copies of their `state/` and `logs/`; `prepare` then created
only the 12 v0.4.1 workspaces, and `run` had nothing else pending. Same machine, Claude Code 2.1.300, default
model (Sonnet 5.5), same `--jobs 6`, same parent `CLAUDE.md` above the run dir (byte-identical to the v0.4
run's), same package versions in the fresh venvs.

```bash
python bench/bench.py prepare --out lfb --arm v041=skills/lab-forge --arm v04=<v0.4 run>/skills/v04/lab-forge \
  --arm v03=<v0.4 run>/skills/v03/lab-forge --arm bare=      # plus the linked v0.4-run workspaces
python bench/bench.py retokens --out lfb                     # recount the reused arms from their transcripts
with-secrets --path=/ai -- python bench/bench.py run --out lfb --jobs 6 --judge-jobs 8 \
  --pair v041,bare --pair v041,v04
```

60 sessions, then 48 verdicts by `claude-fable-5-1`, 8 at a time. `optuna-r3-v041-v04.swap` ended on a note
about a background check, with no JSON; it was judged again from the same prompt. v0.3 was not judged against
v0.4.1, so its blind-review rows in `all-arms.md` are empty (its code sum shows 0).

`verdicts/<pair>/` holds each verdict with its own `.map.json` (X/Y to arm), as in the v0.4 folder.

## Bench changes

- `claude()` takes usage from the session transcript (`HOME/.claude/projects/*/<session_id>.jsonl`) when it
  is larger than what `claude -p` reports, and keeps the CLI number in `reported_tokens`. Cost stays the CLI's
  `total_cost_usd`, which already covers the whole session.
- `retokens` does the same for recorded runs, pairing steps with transcripts in start order.
- `run --pair A,B` (repeatable) judges only the named pairs; `--judge-jobs N` runs verdicts in parallel; a
  verdict that already parses is kept, so a stopped run resumes.

Recounted in the reused arms (CLI-reported → transcript, task steps): bare encoders r3 P2 42k → 501k, bare
encoders r1 P2 158k → 529k, bare optuna r3 P2 35k → 379k, v0.3 encoders r1 P1 89k → 444k. Two deploy steps
also changed (v0.4 encoders r2, v0.3 rparse r3); deploys are not in the per-task numbers.

## v0.4 sessions: where P2 and T spent tokens

From the transcripts of the 48 task sessions per arm in the v0.4 run:

- Calls per session are close to bare once bare is counted honestly: P2 10.8 (v0.4) vs 10.7 (bare), P1 9.7 vs
  9.8. Tool output per session is also similar (P2: 15k characters on average for both).
- The first call of every v0.4 session is 3.7k (churn) to 4.7k (optuna) tokens larger than bare's, and that
  overhead is resent on every call. One-turn probes on a copy of a deployed v0.4 optuna workspace split it:
  global rules 1.97k, repo `AGENTS.md` 1.50k, home skill descriptions 0.54k (lab-forge 1.0k characters,
  bundled star-deck 0.7k), repo skills and commands 0.35k.
- T is one `tune.py` call plus the reply: 2 calls of about 29k each. Bare answers in one call and stores
  nothing.
- No repo skill was invoked in any v0.4 task session; their descriptions are pure context cost in the bench.
- Every arm loses 1-2 calls per coding step to `git commit` failing on a missing identity in the bench
  sandbox. Same for all arms, so it was left alone.

## The three v0.4 failures

| Step | Hidden check | Cause |
|---|---|---|
| churn r3 P1 | no JSON with two ROC-AUC values | `runs/metrics.json` held both AUCs as `models.logreg` / `models.gboost` next to `"metric": "roc_auc"`; no key names the metric |
| churn r3 P2 | same | same file layout, kept from P1 |
| rparse r1 P2 | eval output lacks `line_total` | the per-field accuracy reported `total` instead of the asked `line_total` |

In all three the agent ran its entry point and reported success; it never compared the output's names with
the task's. The new C7 asks for exactly that check. v0.4.1 solved all 24 steps.
