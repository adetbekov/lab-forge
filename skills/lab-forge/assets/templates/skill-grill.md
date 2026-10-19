---
name: grill
description: Decides whether to ask before acting and asks as a real choice of 2-4 options. Use when a request is short or ambiguous, the user may know what the code does not (data, deadlines, consumers, past decisions), two reasonable approaches differ, or the user says "grill me", "ask me", "уточни", "спроси".
---

# grill

## 1. Gate
Read the code, config and history first. Ask only if all three hold:
- the files cannot answer it;
- different answers give different code, commands or results;
- a wrong guess costs more than one short message.
Otherwise decide, and name the decision as an assumption in your reply.

## 2. Ask
```
<what I found, one line, and why it matters>
1. <option> - <consequence>
2. <option> - <consequence>
3. other: ...
```
- 2-4 options a reasonable person would pick. No straw men, no "(recommended)".
- If one option is clearly right, do not ask. Decide and say why.
- Up to 3 independent questions per message, so the answer can be `1b 2a`.
  Ask dependent questions one at a time.
- Drill a vague answer once, then take it and record the assumption.

## 3. After the answer
Start the work at once. Do not repeat the question back or ask "shall I start?".
If the answer is a lasting preference ("always", "never", "fewer ..."), it is a
tune too. Record it as `references/tune.md` of lab-forge says.

## Example
User: "add a holdout eval"

Bad: "I recommend a 20% random split. Shall I proceed?"

Good:
```
Labels lag 30 days, so I split by time, not at random. Open: how many windows.
1. one holdout, last month - fast, about 8k rows, noisy metric
2. 3 rolling monthly folds - stable metric, 3x train time
3. other: ...
```
