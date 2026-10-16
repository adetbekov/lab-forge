# lab-forge

An agent skill that sets up an AI coding environment for data science, ML and
AI projects, and then gets out of the way.

You run it once. It reads your machine and your repos, asks only what it could
not detect, and writes a small set of rules, skills and commands that make the
agent work the way you do. Later runs only tune what is already there.

Status: **v0.1, experimental.** The first A/B round against a plain agent showed
about 30% less code and less bloat, at the cost of missing some explicit
requirements. Fixes are in progress (see Roadmap).

## What it fixes

The usual complaints about a plain coding agent: too much code, edits outside
the task, new tests and edge cases nobody asked for, stale docs, forgetting
context between sessions, wasted tokens, no questions when it should ask, and a
different style every time.

## Install

The skill lives in `skills/lab-forge/` in the [Agent Skills](https://agentskills.io)
format (`SKILL.md` plus references and scripts).

| Agent | Copy `skills/lab-forge` to |
|---|---|
| Claude Code | `~/.claude/skills/` (all projects) or `.claude/skills/` (one repo) |
| GitHub Copilot (VS Code) | `.github/skills/` or `.claude/skills/` |
| Codex and other `AGENTS.md` agents | `.agents/skills/` |
| Cursor | `.cursor/skills/` |

Then ask the agent: "set up lab-forge for this project".

## How it works

1. **Detect.** Agent, OS, tools, network, and how much you are allowed to change in each repo.
2. **Audit.** Mechanical checks plus a manual read, so problems come with proposed fixes.
3. **Interview.** Only the questions detection could not answer, one at a time.
4. **Generate.** One canonical rules file, thin pointers for other agents, skills and commands, all within line budgets.
5. **Record.** `.lab-forge/state.md` lists what it owns, so tune mode edits instead of rebuilding.

The style pack in `skills/lab-forge/style-pack/` holds the author's principles
and bundled skills. Swap it out and the engine serves someone else's style.

## Roadmap

- Global layer installed once per machine, plus thin per-repo files
- Adapters that actually work in Claude Code, Codex, Copilot, Cursor and Antigravity
- Model routing: small tasks on a cheaper model, hard ones escalated after a failed check
- Interviews with real choices and short messages
- Tune mode that a user can steer in one line
- Repeatable A/B benchmark across new, small and large projects

## Credits

`grill-me` is adapted from [mattpocock/skills](https://github.com/mattpocock/skills) (MIT).

## License

MIT
