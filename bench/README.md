# bench: repeatable A/B for lab-forge

Every lab-forge component goes into `main` only after it wins here. The bench runs the same tasks in fresh,
isolated sessions with and without a skill, then scores each step with hidden checks and a blind X/Y review.

Latest results: [`results/2026-10-18-v0.2-vs-bare`](results/2026-10-18-v0.2-vs-bare/report.md),
[`results/2026-10-18-layers-vs-v0.1`](results/2026-10-18-layers-vs-v0.1/notes.md),
[`results/2026-10-18-layers-vs-v0.1-headless`](results/2026-10-18-layers-vs-v0.1-headless/notes.md),
[`results/2026-10-18-memory-wiki-vs-map`](results/2026-10-18-memory-wiki-vs-map/report.md) ([summary](memory/results.md));
[`results/2026-10-18-model-mix`](results/2026-10-18-model-mix/report.md) (which model plays which role, `modelmix/mix.py`);
previous: [`v0.1`](results/2026-10-17-v0.1-vs-bare/report.md).

## Run it

Needs `git`, `uv`, Python 3.11+, and the `claude` CLI authenticated through `ANTHROPIC_API_KEY` or
`CLAUDE_CODE_OAUTH_TOKEN`. Each session gets its own `HOME`, so user-level skills and rules never leak in.

```bash
python bench/bench.py all --out /tmp/lfb                      # lab-forge (skills/lab-forge) vs bare agent, 2 repeats
python bench/bench.py all --out /tmp/lfb --arm new=path/to/skill --arm old=skills/lab-forge
python bench/bench.py all --out /tmp/lfb --cases churn --reps 1 --model claude-sonnet-5-5   # quick smoke
```

The result is `/tmp/lfb/report.md` and `/tmp/lfb/runs.tsv`. Only those two files and the verdicts go into
`results/<date>-<what>/`; workspaces and logs stay out of git. A full run is 72 sessions plus 8 verdicts,
about 4M tokens.

### Without a headless CLI (agent-driven)

When `claude -p` is not available, an orchestrating agent runs each step in a fresh subagent:

1. `bench.py prepare --out DIR`: creates workspaces and their venvs.
2. `bench.py next --out DIR`: writes the next prompt for every workspace and prints the paths. Run each one in
   a new session (all of them in parallel), then
   `bench.py record --out DIR WS STEP --tokens N --tools N --ms N`. Repeat until `next` prints nothing.
3. `bench.py pack --out DIR`: writes one blind review prompt per case and repeat. Run each in a new session.
   The reviewer saves `<key>.verdict.md` next to it.
4. `bench.py report --out DIR`.

If a hidden check turns out to be wrong, fix it and run `bench.py recheck --out DIR`; no session needs to rerun.

## What one run does

| Case | Fixture | Kind |
|---|---|---|
| `churn` | empty dir | new classic-ML project (sklearn) |
| `rparse` | empty dir | new LLM app: receipt parser, fake client, golden set |
| `optuna` | `optuna/optuna@v5.0.0`, ~70k lines | existing large repo |
| `encoders` | `scikit-learn-contrib/category_encoders@v2.11.1`, ~8k lines | existing small repo |

Each workspace runs these steps, each in a fresh session with no memory. The user is "unavailable", so the
agent works in batch mode.

- `P0`: skill deploy (skill arms only).
- `P1`: new project or first feature.
- `P2`: follow-up that depends on P1.
- `T`: a one-line preference ("From now on, answer my questions about this project in Russian.").
- `P3`: a read-only question.

Workspace names are hashes, so neither the agent nor the reviewer can read the arm from a path.

## Metrics, and which pain each one covers

Pains are numbered as in [`docs/architecture.md`](../docs/architecture.md).

| # | Pain | Metric in `report.md` | How |
|---|---|---|---|
| 1, 9 | Too much code, huge scripts | Python and all lines changed, largest new file; blind `bloat`, `optimality` | diff, judge |
| 2, 7 | Edits outside the task, unasked work | files outside the case's `scope`; blind `scope` | diff, judge |
| 3 | Works on `main` | coding steps committed straight to `main` | git |
| 4 | Extra tests | tests added | diff |
| 5, 14 | Tokens, time, cost | task tokens, tokens and $ per solved task, time; deploy tokens | driver |
| 8, 17 | Questions, doubt | questions in coding replies; blind `questions` (asked or deferred only when warranted) | reply, judge |
| 10, 15 | Fake tech, rushing to "done" | hidden checks solved; "claimed done but check fails"; pytest red; new ruff errors | hidden check |
| 11 | Robotic replies | blind `clarity` | judge |
| 13 | Forgets between sessions | P2 requirements that depend on P1 (hidden check) | hidden check |
| 16 | Misses the big picture | blind `correctness`, `practices` | judge |
| 18 | Style differs every time | stability across repeats: Jaccard of changed files × line ratio | diff |
| 19 | Tuning in one phrase | `T` applied in the next session (P3 answered in Russian) | reply |
| 6 | Stale docs, fake tech | imports in changed files that do not resolve in the venv | diff, venv |
| 12 | Tech debt | not measured yet: needs longer chains of steps | — |

The report also checks the first round's conclusions automatically: less code, better bloat score, explicit
requirements not better, task tokens within ±15%, deploy 40-100k, and the LLM case won by lab-forge.

## Adding a case

Add `cases/<name>/case.toml` (fixture, packages, `scope`, steps) and `cases/<name>/check.py STEP`. The check runs
from a fresh checkout of the step's tree and exits 0 when every explicit requirement holds. Test it against the
pristine fixture (it must fail) and against a reference fix (it must pass) before a paid run. Fixtures must be
public or synthetic.
