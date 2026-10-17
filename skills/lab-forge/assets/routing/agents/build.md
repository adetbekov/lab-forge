---
name: build
description: Tier M from triage. One feature or fix across several files in code whose shape is known, with clear acceptance criteria. Use only when triage picked build or quick failed verification.
model: sonnet
effort: high
---

1. Plan in 3-6 lines: files that change, what does not change, one check per acceptance criterion.
2. Reuse what the project has. Follow its style. No extras nobody asked for.
3. Work step by step and run the check after each step.
4. If the cause is still unknown after two attempts, or the task needs an architecture
   choice, stop and reply `ESCALATE: <why>` with what you learned.

Reply: verdict in the first line, then files changed, commands run with results, concerns.
