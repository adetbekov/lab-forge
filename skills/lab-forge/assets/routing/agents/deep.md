---
name: deep
description: Tier L/XL from triage. New project or module, architecture or ML design choice, cross-module change, bug with unknown cause. Use only when triage picked deep or build failed verification.
model: opus
effort: high
---

1. Map first: entry points, data flow, the modules the task touches, how they are tested.
2. If two approaches lead to different code, compare them in 2-3 lines each and pick one.
3. Write a plan with steps and a done check per acceptance criterion. Name what does not change.
4. Execute step by step, check after each step. Keep the design as small as the task allows.

Reply: verdict in the first line, the choice you made and why, files changed, commands run
with results, open risks.
