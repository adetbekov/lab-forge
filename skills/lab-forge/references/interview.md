# Interview protocol

Ask only when the user knows something the files do not, and the answer changes
what gets built. Every question offers a real choice. The same rules drive the
`grill` skill in daily work (`assets/templates/skill-grill.md`).

## Gate: ask or decide

Ask only if all three hold:
1. Detection, the audit and the code cannot answer it.
2. Two answers lead to different files, commands or results.
3. A wrong guess costs more than one short message to fix.

Otherwise decide, and write the decision as an assumption the user can correct.
Never ask for permission to follow your own recommendation.

## Question format

```
<one line: what I found and why it matters>
1. <option> - <what changes if chosen>
2. <option> - <what changes>
3. <other: ...>
```

- 2-4 options, each one a choice a reasonable person would make. Use no straw
  men and no "agree?". If only one option is sane, it is a decision, not a question.
- Put no recommended option first and no "(recommended)" label. If one option
  is clearly better, say why in the first line and make it a decision instead.
- One message holds up to 3 independent questions, numbered, so the user answers
  `1b 2a`. Ask dependent questions one at a time.
- Drill a vague answer once. Then take it and record the assumption.

## Branches for deploy (skip what detection settled)

1. **Scope**: which projects; repo, several, or user level only.
2. **Ownership level** per project (0-3), see `environment.md`.
3. **Domain profile**: classic ML, LLM/agents, analytics, mixed (`profiles/`).
4. **Stack facts not in files**: where data lives, how jobs run, tracker, deploy.
5. **Restrictions**: network, what may not leave the machine, forbidden tools,
   approvals. These become invariants.
6. **Delivery**: PR platform, wiki and whether the agent can reach it, slides,
   AI co-author trailer (detect first, see `generation.md` section 3).
7. **Languages**: identifiers, comments, commits, docs.
8. **Pain points**: what annoys the user most. Each becomes one concrete rule.

Close with a summary of up to 5 lines: decided, assumed, still open.

## Batch mode

No user in the loop: answer each branch from evidence and mark it `detected` or
`assumed`. Put the `assumed` items at the top of the skeleton. The user fixes
them later with one phrase (`tune.md`).
