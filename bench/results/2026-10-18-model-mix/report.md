# Model mix: which model plays which role (JEB-1894), 2026-10-18

**Verdict: keep Opus for everything. No mix wins.** Both mixes cost more per solved step than
Opus alone (+43% and +86%) and scored the same or worse in blind review. Sonnet for everything
is 2.8x cheaper per solved step and passes every hidden check. It still lost all 4 blind
verdicts to Opus, mostly on ML correctness, so it does not meet "no loss of quality". lab-forge
sets no model and adds no subagent layout today, so this result changes no code.

## Arms

| Arm | Main session (takes the task, handles T and P3) | Planner | Coder |
|---|---|---|---|
| `mix1` | Sonnet | — | Opus subagent |
| `opus` (baseline) | Opus | — | main session itself |
| `sonnet` | Sonnet | — | main session itself |
| `mix4` | Sonnet | Opus subagent (read-only, plan only) | Sonnet subagent |

## Setup

- Bench on `main` (`b03d770`). Cases `churn`, `rparse`, `optuna` and `encoders`, 1 repeat,
  agent-driven mode, driver `bench/modelmix/mix.py`.
- P0 ran once per case on Sonnet, in the `opus` arm's workspace. It was then copied into the
  other 3 arms with paths rewritten, so only the models differ. `mix1` and `mix4` also got
  `HOME/.claude/agents/{planner,coder}.md` (`bench/modelmix/agents/`) and a "Model layout"
  section in `HOME/.claude/CLAUDE.md`.
- A delegating main session ends with `DELEGATE: <agent>` plus a handoff of at most 5 lines.
  The driver then starts the subagent, and a relay session continues the main session with its
  earlier reply and the subagent's report. This works like `bench/routing/rprompt.py` on
  `agent/mika/2099bdcd105b`, adapted to the planner and coder roles. In `mix4` each coding step
  is: main, planner, relay, coder, relay.
- T and P3 run as one main-session turn in every arm. The layout tells the main session to
  handle questions and settings itself.
- Blind review: 12 verdicts (every arm against `opus`, per case), all judged by Opus. The arm
  maps are in `verdicts/*/blind-map.json`.
- Prices match `bench/routing/cost.py` (JEB-1880). They use a blended $/MTok with the mix 2%
  input, 8% output, 80% cache read and 10% cache write: Opus $2.34, Sonnet $1.25.

## Result

| Metric | mix1 | opus | sonnet | mix4 |
|---|---|---|---|---|
| Solved, hidden checks (P1+P2) | 8/8 | 8/8 | 8/8 | 8/8 |
| Coding tokens, k | 965 | 521 | 354 | 1465 |
| Coding cost, $ | 1.74 | 1.22 | 0.44 | 2.27 |
| **$ per solved step** | 0.218 | **0.152** | **0.055** | 0.283 |
| vs opus | +43% | — | −64% | +86% |
| Cost incl. T and P3, $ | 2.09 | 2.02 | 0.79 | 2.62 |
| **Blind code score, of 30** (arm vs opus in its pair) | 28.2 vs 27.9 | 27.9-28.2 | 26.5 vs 28.2 | 27.0 vs 28.2 |
| Blind overall verdicts vs opus (win/tie/loss) | 0/0/4 | — | 0/0/4 | 0/1/3 |
| Blind P3 accuracy, of 5 | 4.0 | 5.0 | 4.5 | 4.5 |
| Tune applied in the next session (P3 in Russian) | 4/4 | 4/4 | 4/4 | 4/4 |
| Python lines changed | 1163 | 1260 | 858 | 986 |
| Sessions per coding step | 3 | 1 | 1 | 5 |

Cost by role, coding steps only:

| Arm | Main (incl. relays) | Planner | Coder |
|---|---|---|---|
| mix1 | Sonnet 474k, $0.59 | — | Opus 491k, $1.15 |
| mix4 | Sonnet 698k, $0.87 | Opus 398k, $0.93 | Sonnet 369k, $0.46 |
| opus | Opus 521k, $1.22 | — | — |
| sonnet | Sonnet 354k, $0.44 | — | — |

## Why

1. **Delegation costs more than the model saves.** The Opus coder in `mix1` used 491k tokens.
   The whole Opus arm used 521k: the coder re-reads the project as a fresh session. On top of
   that, the Sonnet main session spent 474k on reading the rules, writing handoffs and
   relaying. The same thing happened in JEB-1880: each main session costs 25-35k tokens per
   turn, and a delegated step needs two such turns.
2. **An Opus planner alone costs as much as the cheapest full arm twice over.** In `mix4` the
   planner (398k, $0.93) and the relays together cost more than Opus doing the work itself.
   The plans were good: the Sonnet coders followed them and solved 4/4 P2. But the review
   scored `mix4` code below `opus`. Lean tests, a weaker default-value test and an accepted
   `log_base=inf` all came through the plan unchanged.
3. **`mix1` gets Opus code but a Sonnet front end.** The code score sums tie (28.2 vs 27.9).
   Even so, `mix1` lost every overall verdict, for different reasons by case:
   - encoders and optuna: the code was a tie or close, and the Sonnet P3 answer decided the
     verdict. `mix1` P3 accuracy was 4.0 against 5.0, and in rparse its refs pointed past the
     end of the file.
   - churn and rparse: `mix1` also lost on code, on design choices that came from the 5-line
     handoff. In churn, calibration and the threshold share one validation split. In rparse,
     the golden set is fitted to the fake.

   It also paid 43% more.
4. **Sonnet alone: cheap and correct on the checks, weaker on judgment.** Its code score was
   26.5 vs 28.2, and correctness was 3.9 vs 4.9. Concrete defects:
   - churn: calibration and the F1 threshold are fit on the same validation split, logreg
     hyperparameters are left in code, and the default output overwrites
     `metrics/baseline.json`.
   - rparse: the golden set is fitted to the fake client (F1 0.92 means little), a negative
     `max_attempts` raises `UnboundLocalError`, and a new ruff I001 error was introduced while
     the reply claimed ruff was clean.
   - optuna P3: says the TPE relative path is "only for `multivariate=True`", which is wrong
     for single-objective studies in v5.0.0.

   Every hidden check passed. The defects are in methodology and accuracy, the parts that
   pains 10, 15 and 16 cover.

## Decision for lab-forge

- Default: no change. The main session uses the user's model (Opus), with no planner or coder
  subagents. `skills/lab-forge` sets no model, so there is nothing to change in code and no PR.
- Sonnet for everything is a possible budget option: about 1/3 of the cost, the same hidden
  checks, a loss on blind quality. Offering it would be a separate tune entry, not a default.
  That needs a product call and is out of scope here.

## Limits

- n=1 per case (16 coding steps per arm). Opus's own score varies by 0.3 between the 3 pairs,
  which is the judge noise. The quality gap for `sonnet` (−1.7) and the cost gaps (≥40%) are
  larger than that. The `mix1` vs `opus` code gap (+0.3) is not.
- Cost uses Agent tool proxy tokens and a fixed cache mix, not real billing. No paid headless
  run was made (out of scope). Delegation overhead is real in both measurements, so the
  ranking should hold.
- Every session also loaded the runner's own project instructions (the same for all arms).
- The Opus P2 runs in the first attempt were cut off by a server cancel. They were reset to the
  P1 commit and run again. The token counts for the Sonnet P2 and mix P2 main sessions come
  from that attempt's transcript.
- `mix4` optuna P2: the "pytest red" mark is an environment gap. The new tests sit in
  `tests/study_tests/test_optimize.py`, which cannot be collected without `fakeredis`. Its
  hidden check passed.

## Files

- `sessions.tsv`: every session, with step, role, model, tokens and tools.
- `runs.tsv`: per-step metrics for all 16 workspaces.
- `mix1-vs-opus.md`, `sonnet-vs-opus.md`, `mix4-vs-opus.md`: the `bench.py report` output for
  each pair.
- `verdicts/<arm>-vs-opus/`: the blind verdicts and arm maps.
