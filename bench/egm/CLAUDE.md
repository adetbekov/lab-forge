Before writing code for a P1/P2 coding step (any task that changes code), run the Elephant-Goldfish flow from the `egm` plugin at {plugin}: read its SKILL.md files as files (the Skill tool refuses them) and use {plugin} wherever they say `${CLAUDE_PLUGIN_ROOT}`.
1. Read {plugin}/skills/egm-draft/SKILL.md and write the design draft for the task. The task text is the brief. The user is not available: every approval gate is approved, and you make each owner decision yourself and record it in the draft.
2. Read {plugin}/skills/egm-review/SKILL.md and run its `uninterrupted` preset on the draft, with no extra goldfish context.
3. Fix every blocker and major from `consolidated_review_report.md` in the draft, then implement the task from the draft.
EGM artifact directory: ~/egm (outside the project)
