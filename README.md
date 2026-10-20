<p align="center">
  <img src="docs/assets/header.webp" alt="lab-forge — agent skill for data scientists" width="100%">
</p>

<p align="center">
  <a href="https://github.com/adetbekov/lab-forge/tags"><img src="https://img.shields.io/github/v/tag/adetbekov/lab-forge?label=version" alt="version"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue" alt="license MIT"></a>
  <a href="https://agentskills.io"><img src="https://img.shields.io/badge/format-Agent%20Skills-8a2be2" alt="Agent Skills"></a>
  <img src="https://img.shields.io/badge/agents-Claude%20Code%20%7C%20Codex%20%7C%20Cursor%20%7C%20Copilot-555" alt="agents: Claude Code, Codex, Cursor, Copilot">
  <a href="https://github.com/adetbekov/lab-forge/actions/workflows/tests.yml"><img src="https://github.com/adetbekov/lab-forge/actions/workflows/tests.yml/badge.svg?branch=main" alt="tests"></a>
</p>

**lab-forge is an agent skill that sets up your coding agent for data science and ML work.**

A plain coding agent in a DS/ML repo writes more code than the task needs, leaks future data into
validation, adds tests that would pass on broken code, edits files nobody asked about, and says "done"
before the output exists. lab-forge installs a small set of rules, skills and guards once, then stays out
of the way. You tune it with one phrase, not by editing prompts.

## Proof

Same tasks, fresh isolated sessions, hidden checks, blind X/Y review by Fable 5.1.
Main bench: 4 DS/ML cases × 3 repeats on Sonnet 5.5 ([v0.4.1 report](bench/results/2026-10-19-v0.4.1/report.md),
[all arms](bench/results/2026-10-19-v0.4.1/all-arms.md), [v0.4 report](bench/results/2026-10-19-v0.4/report.md)).

| | v0.4.1 | v0.4 | v0.3 | bare agent |
|---|---|---|---|---|
| Weighted code score, blind, 1-5 (v0.4.1 vs bare) | **4.55** | — | — | 4.28 |
| Blind head to head, v0.4.1 wins : losses | — | 6 : 4 | — | **10 : 2** |
| Solved, hidden checks | 24/24 | 21/24 | 24/24 | 24/24 |
| Claimed "done" but the check fails | **0/24** | 3/24 | 0/24 | 0/24 |
| Bare `pytest` green after each step | **23/23** | 24/24 | 22/22 | 14/24 |
| Mutants killed by the agent's own tests | 16/24 | 18/24 | 15/24 | 7/15 |
| Steps committed straight to `main` | 0/24 | 0/24 | 0/24 | 24/24 |
| Ruff errors in changed files | 15 | 27 | 15 | 44 |

## Quick start

The skill lives in `skills/lab-forge/` in the [Agent Skills](https://agentskills.io) format.

| Agent | Copy `skills/lab-forge` to |
|---|---|
| Claude Code | `~/.claude/skills/` (all projects) or `.claude/skills/` (one repo) |
| GitHub Copilot (VS Code) | `.github/skills/` or `.claude/skills/` |
| Codex and other `AGENTS.md` agents | `.agents/skills/` |
| Cursor | `.cursor/skills/` |

Then tell the agent:

> set up lab-forge for this project

To upgrade from an older version, check the diff first, then apply it (a backup is made):

```bash
python skills/lab-forge/scripts/upgrade.py --dry-run
python skills/lab-forge/scripts/upgrade.py --apply
```

## How it works

- **Core, defaults, profile.** One rule set per machine in `~/.lab-forge/`: a short core (≤30 lines),
  defaults you can override, and a profile (classic ML or LLM agents) copied into the repo `AGENTS.md`.
  Each repo keeps only its own facts; other agents get a pointer, not a copy.
- **Protected core.** The core and profile blocks change only through install or upgrade. A hook blocks
  agent edits to them and edits on `main`, and tune refuses phrases that would weaken a core rule.
- **Done means checked.** Before "done", the agent runs the task's entry point and checks that every
  file, key and metric the task names is there.
- **Tune.** Say "fewer tests" or "пиши короче" once. The agent writes one override line, shows the diff,
  and `undo` reverts it.
- **Upgrade.** `upgrade.py` moves v0.1-v0.4 installs to the current engine. A second run prints "up to date".

Design and trade-offs: [`docs/architecture.md`](docs/architecture.md).

## Links

- [Bench](bench/README.md): how every change is measured, and all past results.
- The `grill` skill builds on `grill-me` from [mattpocock/skills](https://github.com/mattpocock/skills) (MIT).
- License: [MIT](LICENSE).
