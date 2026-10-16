# Style pack

Replaceable part of lab-forge. The engine reads only these paths:

- `principles.md` - how the author works; merged into every generated rule set.
- `bundled-skills/<name>/` - finished skills installed as-is (phase 5). Their
  main file is stored as `SKILL.md.bundle` so it does not load as part of lab-forge;
  install renames it back to `SKILL.md`.

Current bundled skills:

| Skill | Why it ships |
|---|---|
| `star-deck` | presentations of results in the author's format |

To make your own pack: replace `principles.md` with your ideas (keep the section
headings so the engine can find the task ladder and anti-slop list) and put your
finished skills into `bundled-skills/`, renaming each `SKILL.md` to
`SKILL.md.bundle`.
