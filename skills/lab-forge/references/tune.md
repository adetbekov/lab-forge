# Tune mode

The deployed system lives on its own. Tune mode changes it without breaking it.

## Steps

1. Read `.lab-forge/state.md`: what lab-forge created, where, at which level, which
   assumptions were made, what was skipped.
2. Classify the request:
   - **rule change** ("stop adding type hints to notebooks") -> edit one line in
     the canonical rules file;
   - **new skill or command** -> create from templates, add one row to the
     skills table;
   - **new project** -> run deploy phases 0-1 for that project only, reuse the
     existing pack and answers;
   - **agent keeps ignoring a rule** -> see below;
   - **update pack** (new bundled skill, new principle) -> copy or edit, then
     re-merge only the affected sections.
3. Show the exact diff before writing. Touch only what the request needs.
4. Run `scripts/verify_setup.py`. Update `.lab-forge/state.md` (one line in the log).

## When the agent ignores a rule

Check in this order and fix the first cause found:
1. The rule is buried: move it up, make it one line, add the reason.
2. The rule is vague: replace with the concrete thing to do instead.
3. Two files say different things: remove the duplicate, keep a pointer.
4. The file is not read by this agent: re-run the test in
   `environment.md` section 5.
5. The rule needs enforcement: offer a guard, if the level allows.

## Drift check

Offer this when the user asks "is my setup still fine": compare files listed in
state with what is on disk, report files edited by hand (keep them - the user's
edit wins), budgets exceeded, broken links, skills never triggered that the user
remembers wanting.
