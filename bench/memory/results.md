# Results: memory and knowledge graph spike (C7, pains 6, 13, 16), 2026-10-18

**Verdict: do not add a memory layer. Keep C7 as plain markdown** (repo `AGENTS.md` plus
global rule 13: decisions and gotchas go into `AGENTS.md` or `docs/wiki/`). The best
candidate, a generated code map, cost 6% more task tokens and gave the same quality.
The blind reviewers split 1:1 (code 29.2 vs 29.5 of 30). Memory between sessions already
works without it: the P2 follow-up was solved 4/4 and the tune was kept 4/4 in both arms.

## Options compared on paper

| | Markdown wiki (current C7) | MCP memory / knowledge graph | Generated code map |
|---|---|---|---|
| What it is | `AGENTS.md` facts + `docs/wiki/` read on demand | `@modelcontextprotocol/server-memory`: entities, relations, observations in a JSON file | `codemap.py`: one line per module with its classes and functions |
| Always-on cost | 0 beyond `AGENTS.md` (≤1k tokens) | 9 tool schemas in every session, about 1.5-2k tokens (estimate), half the 3.5k budget | 1 pointer line; the map itself (~5k tokens on optuna) only when read |
| Freshness | written by the agent, can go stale; rule 12 deletes stale lines | written by the agent, goes stale, and no human reviews it in a diff | rebuilt from code, never stale |
| Harness support | all 5 read `AGENTS.md` | all 5 run MCP, but config is per harness and needs Node | any harness, stdlib Python |
| Complexity | none, already shipped | a server per machine, per-harness config, a store outside git | 1 script (~60 lines) + a session-start hook |
| Covers | 13 (decisions), 6 (rule 12) | 13 | 16 (structure), not 13 |

MCP memory was dropped before the A/B: it pays always-on tokens in every session, it
stores knowledge where neither git nor the user sees it, and what it holds is exactly
what `AGENTS.md` already holds. The code map was the only option with a new mechanism
(fresh by construction) and no always-on cost, so it went to the A/B.

## A/B setup

- Bench `bench/`, case `optuna` (~70k lines, the case where the big picture matters
  most), 2 repeats, agent-driven, every step on Opus 5.5. Raw data:
  [`results/2026-10-18-memory-wiki-vs-map`](../results/2026-10-18-memory-wiki-vs-map/report.md).
- One P0 deploy (Sonnet) copied to all 4 workspaces, so only the map differs.
- `wiki`: lab-forge `main` as is. `map`: plus one line in the repo `AGENTS.md` "Read first"
  pointing at `.lab-forge/map.md` (git-ignored), rebuilt by `codemap.py` before every
  session, as a SessionStart hook would.

## Numbers

| Metric | wiki | map |
|---|---|---|
| Hidden checks solved (P1, P2) | 4/4 | 4/4 |
| Task tokens, k (P1+P2+T+P3) | 391 | 415 (+6%) |
| P1 tokens / tool calls (find where helpers live) | 96k / 42 | 91k / 30 |
| P2 tokens / tool calls (follow-up on P1) | 113k / 63 | 127k / 59 |
| P3 tokens / tool calls (trace TPE call path) | 103k / 27 | 112k / 35 |
| Task time, min | 16.2 | 12.7 |
| Blind code score, of 30 | 29.5 | 29.2 |
| P3 answer: accuracy / completeness | 5 / 4.5 | 5 / 5 |
| Style stability across repeats | 0.6 | 0.1 |

"pytest red" for one wiki step is a pre-existing collection error: `tests/study_tests/test_study.py`
needs `fakeredis`, which the bench venv does not have.

## Why the map did not pay

1. Orientation is a small share of a session. P1 is the only step where the map clearly
   helped (−29% tool calls, −5% tokens). In P2 and P3 the agent still had to open the
   files it changed or traced, and reading the 5k-token map came on top of that.
2. The repo `AGENTS.md` written at deploy already has a hand-picked `## Map` (packages,
   patterns, logging). A full module list adds little to it.
3. The map has no line numbers or call edges, so it cannot answer "which function calls
   which". `grep` does that in one call.
4. Memory between sessions is already covered by git (`git log`, the last commit) and by
   `AGENTS.md` overrides. Nothing in P2 or T needed more.

## Not measured

- Long chains (5+ sessions on one feature) and repos without a good `AGENTS.md` map:
  this is where a map or a decision log could still win. Pain 12 needs the same chains.
- n=2, one case, one judge per repeat. Agent-driven tokens do not show cache reads.
- MCP memory was not run; its cost is an estimate from the tool count.

## Next

Nothing to ship. `codemap.py` stays here as the experiment tool. Revisit if a long-chain
case is added to the bench and the plain-markdown arm loses facts across sessions.
