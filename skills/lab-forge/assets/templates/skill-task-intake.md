---
name: task-intake
description: Sizes a new task (S/M/L/XL), splits it into checkable steps and, for big tasks only, writes a short plan before coding. Use when the user gives a task, ticket or idea that is not a one-line change, or says "new task", "break it down", "plan", "decompose".
---

# task-intake

## 1. Size
Use the ladder in the global rules (`~/.lab-forge/AGENTS.md`, rule 2). State the size in one line with the reason.
- S -> stop this skill, just do the task.
- M -> steps 3-4 in chat, no file.
- L/XL -> steps 2-5.

## 2. Grill (L/XL only)
Use skill `grill`: ask only what changes the plan, as 2-4 real options, until these are
clear: goal and how success is measured (baseline!), inputs and where they live,
outputs and who consumes them, constraints, what is out of scope. If the code
can answer a question, read the code instead of asking.

## 3. Decompose
Split into steps. Each step:
- does one thing, in one module or stage;
- has input -> output -> check (a command, a test, a metric);
- is small enough for one reviewable commit.
Prefer extending existing modules and patterns ({{pattern_examples}}) over new ones.

## 4. Confirm
Show the steps. Wait for "ok" or edits. Then execute one step at a time: do it,
run its check, report in 2-3 lines, go to the next.

## 5. Plan file (L/XL only)
Save to {{plans_path}}/<task-id>.md, max 60 lines:
goal and metric, steps with checks, open questions, decisions made.
Update it when a step changes; delete or archive it when the task is merged.
