# Components — blocks that replace bullets. All values from design-system.md.

1. **Metric card** — huge accent number, small gray caption, row of 3–4. Mandatory
   on the Results slide. **Inside the number, only the value is huge**: units and
   modifiers ("min", "%", "~", "d") set ~40–50% smaller, tucked close to the value
   ("**1** min", "~**90**%") — the eye must land on the number, not the unit.
   The Results metric row reveals progressively: one card per build step.

2. **Numbered cards 01–06** — oversized accent numeral + bold label + one-line
   gloss. For agenda, recipes, takeaways, plans. Never a plain numbered list.
   The numeral lives ONLY in the numeral element — never repeated inside the
   label text ("01" + "1 Route" = defect). Conclusions reveal one per slide;
   reference material all at once.

3. **Checklist engine** (signature Action device) — persistent split layout over
   many slides. Left ~35%: running problem list, "Symptom. → Need X" ("Memory of a
   goldfish. → Need a memory manager"); solved = checked + struck + dim, current =
   black bold, ONE active at a time. Right ~65%: the current fix (failure chat mock
   → diagram +1 block → same probe now passes). After 4–6 loops: version divider
   ("v1.0 done… is it?"), optionally round two.

3b. **List-of-blocks row** — any stacked list of cards leads each row with a bold
    key phrase, emoji PNG, or accent numeral; detail follows regular/gray. Never a
    column of uniform gray regular rows (flat = invisible).

4. **Spotlight tour** — full diagram, then N slides with exactly one component at
   full color and the rest dimmed ~15–20%, final slide all lit. Titles narrate.
   Use when ≥4 components each earn ≥1 minute; fewer → annotate the map instead.

5. **Zoom-in** — overview stays dimmed in a corner; focused block expands into a
   callout (fields as pills) + short responsibility list + optional 3–5-line code
   card.

6. **Chat mock** (evidence) — user bubble right/blue-tint, answer as gray card,
   verdict badge on the corner. Same probe query verbatim every time. One text
   size inside the card (only the tiny filename/meta header differs); no extra
   callout chips — anything already said by the title stays off the slide.
   In failure versions the code stays black and readable — the red X and title
   carry the verdict, not grayed-out text.

6b. **Verdict badges** — flat green-check / red-cross circles from
    `scripts/gen_verdict_badges.py` (crisper than the Apple glyphs). These two are
    the ONLY non-Apple pictograms allowed; every other pictogram is an Apple
    emoji PNG.

7. **Code card** — `#F5F5F7` window card, small gray filename header, ≤15 lines
   Menlo 14–16pt, line-height 1.4, 20–24px padding, indentation preserved exactly,
   left-aligned, no wrapping (trim the example instead). **Syntax-highlight the
   code**, muted palette on light gray: keywords `#0071E3`, strings `#34C759`,
   comments `#6E6E73`, functions `#5856D6`, rest black — soft, not a rainbow.
   One per slide, never raw code on background.

7b. **Annotation-as-next-step** (use often). Show the exhibit (diagram, chart,
    code) clean first — let the audience actually look at it; the caption,
    verdict badge, side note, or delta callout arrives on the NEXT build step.
    Secondary elements never compete with the exhibit's first impression.

8. **Config cards** (stack slide) — 4–6 cards: emoji PNG + tool bold + 1–2-line
   rationale ("Adam — converged 2× faster on our data"). Never logo soup.

9. **Comparison matrix** — capabilities × solutions, ours first; yes green / no red
   as text or emoji PNG; ≤5 columns.

10. **Before/after** — old chain left, all dim, "was"; new chain right, colored,
    "now"; arrow between; left→right always.

11. **Work-log item** (internal) — big accent "#N" + "Was: X → Did: Y" (fix bold)
    + mini diagram right. One per slide.

12. **Experiment template** (analytical) — per experiment the same trio:
    result pair + green delta / diagnostics chart / interpretation with
    green-yellow-red zones on the chart. Repetition is the feature.

13. **Divider** — full-bleed black, white bold 60–80pt, 1–4 words (often a
    question), optional single emoji PNG, one word may be accent blue.

14. **Analogy diagram** — hardest concept mapped to a household object (encoder =
    ZIP archiver). Exactly one per deck, right before the deepest dive.

15. **Emoji cast** — one Apple emoji per recurring entity, assigned at first
    appearance, never swapped; state emoji encode process status. Continuity object.

16. **Speaker/team cards** — photo circle, name bold, role gray, handle; past
    members dimmed. Thanks slide: handle + QR to artifacts.
