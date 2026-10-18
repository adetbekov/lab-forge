# JEB-1909: v0.4 vs v0.3 and bare, upgrade from v0.1

Two parts. The upgrade check is done. The headless A/B has not run yet: this machine has neither
`ANTHROPIC_API_KEY` nor `CLAUDE_CODE_OAUTH_TOKEN`, and `claude -p` in an isolated `HOME` answers
"Not logged in". `runs.tsv` and `report.md` land here once it runs.

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
there waits for his go-ahead.

Nit: the state log line reads `2026-10-18 upgrade 0.1 -> 0.4.0` on 2026-10-19 (local date of the
machine's timezone vs UTC); harmless.

## A/B (pending)

Planned: `bench.py all --cases churn rparse optuna encoders --reps 3 --arm v04=skills/lab-forge
--arm v03=<v0.3 @ 8417b6c> --arm bare= --judge-model claude-fable-5-1`, X/Y in both orders, `pack` and
`report` per pair. Questions the report must answer: weighted score (methodology and tests x2)
v0.4 >= bare and > v0.3; tokens and `cost_usd` per solved task v0.4 not worse than bare; mutants caught.
