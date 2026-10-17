# JEB-1879, headless: global layer + guard (arm a) vs v0.1 (arm b)

Real `claude -p` sessions (Claude Code 2.1.300, Opus 5.5), real hooks, case `churn`, 2 repeats,
20 sessions + 2 blind verdicts. No merges between steps: each arm keeps the branch it chose.

## Verdict

Confirms the agent-driven round with a real harness. The hook keeps every coding step off
`main` (0/4 vs 4/4), all hidden checks pass (4/4 vs 2/4), and the blind reviewer picks arm a
in both repeats (code 27.5 vs 26.5 of 30). It costs more: task tokens +53% and time +54%,
but cost per solved task is lower ($0.9 vs $1.4) because arm b failed half its checks.

| # | Pain | a | b |
|---|---|---|---|
| 3 | Commits to `main` | 0/4 | 4/4 |
| 2, 7 | Files outside scope; blind scope | 0; 4.0 | 0; 4.5 |
| 6 | Unresolved imports | 0 | 0 |
| 13 | P2 solved; tune applied next session | 2/2; 2/2 | 1/2; 2/2 |
| 18 | Style stability across repeats | 0.2 | 0.4 |

Weak spots: style stability is lower, and one arm-a repeat committed `uv.lock` and a plan file,
which inflates "all lines changed" (1456 vs 841). Python lines are close (778 vs 674).
Token counts here include cache reads, so they are not comparable with the agent-driven round.

Smoke on the same machine: `smoke.py --harness claude` passed (global and repo canary, guard
held). A direct "commit on main, do not branch" request was refused by the hook, and `main`
did not move.
