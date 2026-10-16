# Narrative — STAR, hypothesis, grilling, action titles

Structure first: skeleton → grill → titles → content. Iterate where change is cheap.

## STAR skeleton

| Section | Slides | Job |
|---|---|---|
| Situation | ~20% | Problem as a story with characters; quantify the pain ("100 ad-hoc requests, fast") |
| Task | ~10% | Falsifiable hypothesis (below) — the pivot of the deck |
| Action | ~60% | The solving journey: attempt → failure → fix → repeat (never a feature list) |
| Result | ~10% | Did the predicted signal appear? Numbers → summary |

Fixed frame around the core:

```
Title → Speaker card(s) → Agenda (3–4 numbered chips)
→ SITUATION → TASK (hypothesis) → DEMO (divider + real screenshot; BEFORE Action —
  audience follows mechanism better after seeing it run; internal status decks may
  move demo after the work log)
→ ACTION (the quest) → RESULT (divider → metric cards → summary)
→ Plans (optional) → Q&A/Thanks (contacts, QR to artifacts)
```

## Hypothesis slide (Lean UX, Gothelf)

> We believe that **[doing/building X]** for **[these people]** will achieve
> **[outcome]**, using **[approach/stack]**. We will know we are right when we see
> **[measurable signal]**.

- Signal defined BEFORE Action; Result answers exactly this sentence.
- Reveal in 2–3 build steps ending with the project name.
- Big-statement slide: NO action title above it — at most a 14pt gray kicker
  ("the bet"). One dominant element per slide (design-system.md).
- User can't fill the "we will know" clause → grilling finding: no success
  criterion exists yet. Push.

## Grill the author

Goal: shared understanding, every branch of the decision tree resolved, before any
slide exists. One focused question at a time; drill vague answers ("users happier"
→ "which metric, how much, measured how?"); devil's-advocate the weakest branch;
track open branches; stop and summarize when all resolved.

Branches: audience & the ONE takeaway sentence · hypothesis falsifiability · demo
availability · what actually failed along the way (failures ARE the Action section)
· the 3–4 real result metrics with baselines (no baseline → no wow; push for delta
form "2d → 0.5d") · what to cut for this audience.

Batch mode (no user): answer the 10 toughest questions from source material; put
unresolved assumptions in a visible block atop the outline.

## Action titles + ghost deck test

Every title = a full sentence stating the takeaway ("TTM dropped from 2 days to
half a day"), never a label ("Results"). Ghost test: titles alone, in order, must
tell the whole story — hook, hypothesis, journey, payoff. Apply before writing
content. Exception: dividers may be 1–4 words, ideally a question ("How did we
build it?") — questions drive momentum.

## Action = quest

Loop: attempt → honest failure → diagnose → fix (diagram +1 block) → replay the
same probe → next problem. Continuity objects (pick 2–3, reuse verbatim): a fixed
probe query, one growing core diagram, a consistent emoji cast. The core diagram is
versioned — +1 block per iteration, finale shows everything. Devices: checklist
engine & spotlight tour (components.md).

## Result with wow

Divider → ONE slide, 3–4 huge metric cards (deltas beat absolutes) → explicitly
close the hypothesis loop (signal met? honest no is a stronger talk) → Summary:
3–4 numbered takeaways (one per slide at conferences, all-at-once internal) →
keep Summary on screen during Q&A.

## Audience switch (design never changes; depth/humor do)

- Internal: informal titles, work-log items (#N was→did), CTA + links slides.
- Conference: full arc, longer quest, speaker cards, QR thanks, light humor beat
  every 10–15 slides.
- Executive/analytical: denser slides OK, zero jokes, per-experiment template
  (result → diagnostics → interpretation), bold every number, end on a
  recommendation.
