# JEB-1893: decision hooks (d1-ultra, hosted) vs main

All four cases, 2 repeats, 72 sessions + 8 blind verdicts, headless `claude -p`. Both arms are this branch's
`skills/lab-forge`; the `decide` arm's deploy request also asks for the hosted decision hooks, so the agent
runs `install_global.py --decide hosted` itself, as a user would.

```bash
with-secrets -- python bench/bench.py all --out DIR --arm decide=skills/lab-forge --arm main=skills/lab-forge \
    --decide decide=hosted --jobs 8
```

The run hit the Claude session limit after the P2 wave. The 7 sessions it killed were reset to their last
recorded tree and rerun with `bench.py run`; no recorded step was rerun.

## Verdict

No measurable win on the pain the layer targets, and no cost. Two of three acceptance gates hold, the
third cannot move here: `main` already has 0 false "done", so there is nothing to reduce.

| Gate | decide | main | Holds |
|---|---|---|---|
| Claimed done but check fails goes down | 0 | 0 | no change (floor) |
| Hidden checks solved do not go down | 16/16 | 16/16 | yes |
| Task tokens within +5% | 6897k | 6939k (−0.6%) | yes |

Other signals: pytest red after a step 0 vs 1, task time 42 vs 49 min, blind code sum 26.1 vs 24.9 of 30.
Ruff errors 11 vs 4, all in `rparse`, which is a new project with no lint config. Deploy tokens +9%
(732k vs 674k per project): the deploy reads one more section and runs the installer with `--decide`.

## What the hooks did

Hooks were installed in 8/8 `decide` homes (`Stop` + `UserPromptSubmit`) and in 0/8 `main` homes.

| Hook | Fired | Acted | Where |
|---|---|---|---|
| `decide stop` | 51 Stop events | 8 blocks | 7 on the P0 deploy, 1 on a coding step |
| `decide skill` | every prompt | 5 hints | all `load skill task-intake`, on coding steps |

- The 7 deploy blocks all came from reports that list caveats (no git identity, Python 3.13 vs 3.12, smoke
  test left for a fresh chat). The model reads "open problem mentioned" and blocks once; the agent then
  restates the same report. Harmless, but it adds one turn per deploy and no value.
- The one coding-step block was a true positive: optuna P2 ended with `DONE_WITH_CONCERNS: mypy result on
  the changed files not confirmed`. The step was solved either way.
- No hook call errored or timed out in a way visible in the transcripts (fail-open would have hidden it,
  so this is a lower bound on problems, not proof).

## Reading

This bench's coding tasks are easy enough that both arms solve all 16 and never claim a false "done", so a
"done?" check has nothing to catch. To show the effect, the bench needs cases where `main` rushes: a hidden
requirement that is easy to skip, or a check that only fails at runtime. Until then the layer stays opt-in,
default `off`.
