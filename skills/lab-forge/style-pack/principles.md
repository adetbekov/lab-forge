# Style pack - principles

The author's way of working, distilled to ideas. These are merged into every
generated rule set. They describe intent, not code: never copy structures from
the projects these ideas came from. Tools and frameworks are chosen from what the
target project already uses.

## 1. Decomposition

- Big work becomes small steps. Each step has an explicit input, an explicit
  output and a way to check it. A step that cannot be checked is not a step yet.
- A pipeline is a chain of named stages, each doing one thing (feature build,
  split, train, evaluate, report; or retrieve, reason, call tool, answer).
  The orchestrator (DVC stages, a Flow with steps, Makefile targets, an agent
  graph) is whatever the project uses - the idea is the same.
- One task from the tracker = one hypothesis = one place for its artifacts.

## 2. Structure

- Shared logic lives apart from the concrete case: a base abstraction with thin
  implementations that fill in only what differs (template method: read ->
  process -> compute). Use this when there are two or more cases or the shape is
  clearly reusable. One case -> write it directly, abstract when the second one
  arrives.
- Behavior is set by config, not by editing code: one params file per project,
  one card per model or agent profile. Changing a threshold never needs a diff
  in logic.
- A project can be a template that is copied and filled in (placeholders in the
  config), with common machinery in a shared library the template only calls.

## 3. Experiments vs production

- Exploration lives in notebooks or scratch scripts (text format such as
  jupytext percent, so it diffs). Production code never contains cells.
- Promotion to production needs a measurement that proves the gain.
- The result of DS work is a number against a baseline ("72% -> 85%", "2d ->
  0.5d"), not "shipped a feature". No baseline -> first task is to get one.
- Work behind a stable interface: change the implementation, keep the signature,
  so others are not blocked.

## 4. Size of ceremony (task ladder)

| Size | Looks like | What the agent does |
|---|---|---|
| S | one clear change, one file or two | just do it, show the diff, no plan file |
| M | several steps or files, one feature | short plan in chat -> confirm -> step by step, check after each |
| L | new module, pipeline, agent, unclear scope | grill -> written plan with steps and done criteria -> confirm -> execute step by step |
| XL | irreversible or architectural choice | as L, plus a short decision record if the user agrees |

When unsure between two sizes, ask one question instead of choosing the bigger one.

## 5. Anti-slop rules

- Smallest diff that solves the task. No drive-by refactors, renames or reformatting.
- Match the existing patterns of the file and project before inventing new ones.
- No abstraction for a single use, no config option nobody asked for.
- No defensive code without a reason: no swallowed exceptions, no `except: pass`,
  no silent fallbacks, no retries or sleeps that hide a real problem.
- No new dependency without asking.
- No comments that restate the code. Docstrings explain why and contracts.
- No `print` with emoji in production code; use the project's logger.
- Explicit names over short ones (`build_features(month)` not `proc(d)`).
- If something does not work: stop and say so. No quiet workaround.

## 6. Markdown diet

- Rules file: short, numbered, linking to details instead of repeating them.
- Do not document what does not exist yet. Plans live apart from docs, and only
  when the task is L or bigger.
- No generated READMEs, changelogs, status pages or ADRs unless asked or clearly
  needed.

## 7. Delivery

- PR description: what and why in one paragraph, steps, how it was checked,
  known gaps. Short.
- Wiki page (Confluence or similar): written for the reader who was not in the
  room; results with baseline first, details after.
- Presentation: use the bundled `star-deck` skill.
- Commit: one logical change, small. No AI co-author lines, no emoji.
