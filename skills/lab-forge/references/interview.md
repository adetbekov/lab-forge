# Interview protocol

Borrowed from grill-me: one question at a time, each with a recommended answer,
and never ask what the codebase can answer.

## Rules

- Before each question, check whether detection or the audit already answered
  it. If yes, state the finding and ask only for confirmation when it matters.
- Give options with your recommendation first; the user can answer with one word.
- Drill vague answers once ("everything should be tested" -> "which part breaks
  most often?"). Do not drill twice; take the answer and note the assumption.
- Stop when every branch below is resolved or explicitly deferred. Summarize the
  answers in five lines before the skeleton.

## Branches (in order, skip resolved ones)

1. **Scope** - which projects get the setup; one repo, several, or user level only.
2. **Ownership level** per project (0-3), see `environment.md`.
3. **Domain profile** - classic ML, LLM/agents, analytics, mixed. Pick the file in
   `profiles/`; mixed projects get both with a short note which part is which.
4. **Stack facts not visible in files** - where data lives, how jobs run,
   experiment tracker, how models or agents are deployed.
5. **Restrictions** - network, what may not leave the machine, forbidden tools
   or services, data access rules, required approval steps. These become
   invariants in the rules file.
6. **Delivery channels** - PR platform and template, wiki (Confluence or other)
   and whether the agent can reach it or only drafts text, presentations.
7. **Languages** - of code identifiers, comments/docstrings, commits, docs.
8. **Pain points** - what the agent does today that annoys the user most. Each
   answer becomes one concrete rule in the anti-slop section.

## Batch mode

No user in the loop: answer each branch from evidence, mark each answer as
`detected` or `assumed`, and put all `assumed` items in a visible block at the
top of the skeleton so the user can correct them later in tune mode.
