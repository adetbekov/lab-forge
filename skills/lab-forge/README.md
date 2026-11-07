# lab-forge

lab-forge is an agent skill that sets up a coding agent for data science and ML work. It installs a short
protected core of rules, a domain profile (classic ML or LLM agents), skills, commands and guards once, then
stays out of the way. Before saying "done" the agent runs the task's entry point and checks that every file,
key and metric the task names exists. You tune it with one phrase ("fewer tests", "пиши короче") and `undo`
reverts it.

What it runs: stdlib Python scripts in `scripts/` (environment detection, repo audit, global install, upgrade,
tune, guard hook, smoke test). It writes only to `~/.lab-forge/`, the harness's user-level files and the
project's `AGENTS.md`; nothing leaves the machine unless you opt into the decision-model hooks with your own
endpoint and key.

Install in Claude Code (2.1.275 or later):

```
/plugin install lab-forge --marketplace adetbekov/lab-forge
```

Other agents, upgrade, bench results and the design: https://github.com/adetbekov/lab-forge
