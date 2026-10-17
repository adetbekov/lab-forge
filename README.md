# lab-forge

An agent skill that sets up an AI coding environment for data science, ML and
AI projects, and then gets out of the way.

You run it once. It reads your machine and your repos, asks only what it could
not detect, and writes a small set of rules, skills and commands that make the
agent work the way you do. Later runs only tune what is already there.

Status: **v0.2, experimental.** On the [bench](bench/README.md) it matches a plain
agent on explicit requirements (16/16 hidden checks), writes 56% less code and
wins the blind review 28.4 vs 25.0 of 30
([report](bench/results/2026-10-18-v0.2-vs-bare/report.md)).

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

Then ask the agent: "set up lab-forge for this project". On first use it installs the
global layer once per machine (`scripts/install_global.py install`): working rules in
`~/.lab-forge/`, a pointer in each agent's global file, and a hook that blocks edits on
`main`. Each repo keeps only its facts in `AGENTS.md`; an empty project gets seed mode
(that file plus two skills). Bundled skills go to your user skills folder once.
`scripts/smoke.py` checks that every agent really loads the rules.

## How it works

1. **Detect.** Agent, OS, tools, network, and how much you are allowed to change in each repo.
2. **Audit.** Mechanical checks plus a manual read, so problems come with proposed fixes.
3. **Interview.** Only the questions detection could not answer, each as a real choice of 2-4 options.
4. **Generate.** One canonical rules file, thin pointers for other agents, skills and commands, all within line budgets.
5. **Record.** `.lab-forge/state.md` lists what it owns, so tune mode edits instead of rebuilding.
6. **Tune.** Say "fewer tests" or "пиши короче" once. The agent writes one override line, shows the diff, and `undo` reverts it.

The style pack in `skills/lab-forge/style-pack/` holds the author's principles
and bundled skills. Swap it out and the engine serves someone else's style.

## Roadmap

- Model routing: small tasks on a cheaper model, hard ones escalated after a failed check
- Repeatable A/B benchmark across new, small and large projects

## Credits

The `grill` skill builds on `grill-me` from [mattpocock/skills](https://github.com/mattpocock/skills) (MIT).

## License

MIT
