# JEB-1879: global layer + guard (arm a) vs v0.1 (arm b)

Cases `churn` and `encoders`, 2 repeats, 40 sessions + 4 blind verdicts, agent-driven
(no headless `claude -p` on the runner). Arm a is this branch, arm b is `main` at 8e97bcc.

## Verdict

The layer split wins on the pain it was built for and does not cost quality. The branch
rule holds everywhere (0/8 coding steps on `main` vs 6/8), the blind reviewer prefers arm a
in 3 of 4 case-repeats (code 28.0 vs 26.8 of 30), and task tokens are flat (+3%).

| # | Pain | a | b | Reading |
|---|---|---|---|---|
| 3 | Works on `main` | 0/8 | 6/8 | Closed. Every arm-a step branched; the hook fired on `main`. |
| 2, 7 | Outside scope, unasked work | 4 files, blind scope 4.5 | 4 files, 4.5 | Tie. All 8 out-of-scope files are `CHANGELOG.md` in `encoders`. One arm-a repo added an unasked dummy baseline; the hidden check rejects its AUC 0.5, which is both a-misses (6/8). |
| 6 | Stale docs, fake tech | 0 unresolved imports | 0 | No signal: these cases have no version trap. Arm a ran `guard.py imports` and read sklearn 1.9 signatures unprompted. |
| 12 | Tech debt from solving at once | — | — | Not measured: needs longer chains. |
| 13 | Forgets between sessions | P2 3/4, tune 4/4 | P2 4/4, tune 4/4 | Tie; the a-miss is the dummy-model case above. |
| 18 | Style differs | 0.6 | 0.5 | Better than v0.1 (v0.1 vs bare was 0.4 vs 0.7). |

## Defects found and fixed on this branch

- The engine was not installed as a user skill, so tune fell back to hand edits.
  `install_global.py` now links it into each harness's skills folder.
- A repo tune on `main` ran into the guard and landed on a side branch. `tune.py` now stores
  it in global overrides with a `[repo]` prefix when the repo is on its default branch.
- The hook ran with the project venv's Python. It now uses the base interpreter.

## Caveats

- Hooks were simulated: each session ran the hook command from `settings.json` by hand.
- Between steps every side branch was fast-forwarded into `main`, as if the user merged the PR,
  so each step starts from `main` in both arms.
- P2 was interrupted by a rate limit; all 8 workspaces were reset to their P1 commit and P2 reran.
- The first-round reproduction table in `report.md` assumes arm b is a bare agent; ignore it here.
