# JEB-1909: v0.4 vs v0.3 and bare, upgrade from v0.1

Two parts: the headless A/B is in [`report.md`](report.md), the upgrade check is below.

## Upgrade from v0.1 (fixture)

Setup: `tests/fixtures/v0.1` copied into a fresh git repo at `~/churn` in a throwaway `HOME`, with a
hand-written line already in `~/.claude/CLAUDE.md` ("my own global line"). Engine at `main` @ 8dc57d9.

```bash
python skills/lab-forge/scripts/upgrade.py --dry-run --repo ~/churn   # upgrade-v0.1.diff
python skills/lab-forge/scripts/upgrade.py --apply   --repo ~/churn   # throwaway copy only
python skills/lab-forge/scripts/upgrade.py --dry-run --repo ~/churn   # upgrade-v0.1-rerun.txt
```

[`upgrade-v0.1.diff`](upgrade-v0.1.diff) is the dry run's diff for user-facing files (global state,
`~/.claude/CLAUDE.md`, `settings.json`, the repo's `AGENTS.md`, `CLAUDE.md`, state). The engine copies it
also writes into `~/.lab-forge/` (core, defaults, guard, tune, install script) are left out.

| Check | Result |
|---|---|
| Dry run writes nothing | yes, exit 0 |
| Hand-written repo lines kept (`10. Use polars`, the 60-day churn label, VPC rule, `params.toml`) | all, once each |
| Rules the core now holds removed from the repo file (sizes, skills table, delivery) | yes |
| Profile block `classic-ml` | 1 |
| Core block in `~/.claude/CLAUDE.md` | 1, after the user's own line, which stays |
| `PreToolUse` hooks in `settings.json` | 1 |
| Repo `CLAUDE.md` | `@AGENTS.md` (was a 3-line text pointer) |
| Second dry run after `--apply` | `up to date: no changes` |
| Conflicts | none |

Repo `AGENTS.md` goes from 55 to 37 lines. Not yet run against Yeldos's real v0.1 install; `--apply`
there waits for Yeldos's go-ahead.

Nit: the state log line reads `2026-10-18 upgrade 0.1 -> 0.4.0` on 2026-10-19 (local date of the
machine's timezone vs UTC); harmless.

## How the A/B ran

```bash
with-secrets --path=/ai -- python bench/bench.py all --out lfb --reps 3 --jobs 6 \
  --arm v04=skills/lab-forge --arm v03=<git archive 8417b6c skills/lab-forge> --arm bare=
```

168 agent sessions (Claude Code 2.1.300, default model), then 72 verdicts by `claude-fable-5-1`, every pair
judged in both X/Y orders. `bench.py all` judges one prompt at a time (~7 min each), so it was stopped
after the sessions and the remaining verdicts ran 8 at a time through the same `bench.claude()` and
`Bench.pack()` / `Bench.report()` calls. Two verdicts needed care:

- `encoders-r2-v04-bare.swap`: the judge's final message was a note about a background test run, with no
  JSON. Judged again from the same prompt.
- `rparse-r3-v04-bare`: the prose quoted `` ```json{ `` inline and `verdict()` took it for the opening
  fence. The parser now matches fences at line start only (`bench.py`, test in `test_bench.py`).

`verdicts/<pair>/` holds each verdict with its own `.map.json` (X/Y to arm). The reps were shuffled
separately, so the per-case `blind-map.json` that `rebuild` reads does not fit here.
