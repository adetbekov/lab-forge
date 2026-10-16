# Design system — fixed, Apple-clean. Take every value from here; never invent.

## Canvas

- 16:9, white `#FFFFFF` on all content slides. Margins ≥ 0.5" (48px @1920×1080).
- Block gap: 24 / 32 / 48px — pick one per slide, keep it consistent on that slide.
- Chrome: optional slide number bottom-right, 12pt gray. Nothing else.

## Colors

| Token | Hex | Role |
|---|---|---|
| black | `#1D1D1F` | ALL primary text and primary diagram strokes |
| gray | `#6E6E73` | secondary/extra info ONLY — never primary content |
| dim | `#C7C7CC` | already-covered build elements only |
| card | `#F5F5F7` | card fill (borderless) |
| accent | `#0071E3` | big numbers, current checklist item, title emphasis |
| success | `#34C759` | positive delta / solved (in exhibits, not titles) |
| problem | `#FF3B30` | failure / removed (in exhibits, not titles) |
| new | `#FF9500` | THE new element of this slide (in exhibits, not titles) |
| indigo | `#5856D6` | functions in code, extra diagram cluster |

- 60-30-10: white+black ≈60%, gray/card ≈30%, color ≈10%.
- **Gray is never primary.** If information matters on THIS slide, it's black.
  Gray = captions, sources, side notes. Dim = only things the audience already
  processed on a previous build step; dimmed text must stay legible — never dim
  body-size text below `#C7C7CC`, never dim the current slide's main content.
- **Titles: black, plus optionally 1–2 words in accent blue. Never red/orange/
  green in titles** — semantic color lives in the exhibit (the failed card, the
  new block), the title stays calm.
- Dividers: full-bleed `#000000` white text is the default, but not a cage —
  occasionally use accent blue or a semantic color that fits the moment (green
  for the results divider, orange for "v1.0 done… is it?"). 1–2 colored dividers
  per deck max; black stays the workhorse.

## One dominant element per slide (hierarchy contract)

Every slide has exactly ONE visually dominant element — a big statement, a metric
row, a diagram, or a card grid. Everything else supports it, at least one full
step down in size/weight. Concretely:

- **Big-statement slides (incl. hypothesis): drop the action title**, or demote it
  to a kicker — 14pt gray, above the statement. Never bold-28pt title + bold-40pt
  statement together: two shouting elements = zero hierarchy.
- Alternative separation: put the statement white-on-black in a full-width card —
  then a normal title may stay.
- If two things feel equally important, split the slide.

## Typography — Helvetica Neue everywhere (→ Helvetica → Arial)

| Role | Weight / size |
|---|---|
| Action title | Bold 28pt |
| Kicker (above big statement) | Regular 14pt gray |
| Big statement / divider | Bold 60–80pt |
| Metric number | Bold 90–120pt, accent; units/modifiers ("min","%","~") 40–50% smaller, tight to the value |
| Body / card text | Regular 18–20pt |
| Caption / source | Regular 12–14pt, gray |
| Code / diagram labels | Menlo (→ Consolas) 14–16pt |

- Hierarchy = size + weight only. Big type IS the style: when in doubt, bigger and
  fewer words. Numbers huge, captions small.
- Multi-line big statements: line-height 0.95–1.05 (tight = solid, single object;
  loose lines fall apart visually).
- Body left-aligned, never centered/justified. Never below 18pt — split instead.
- ≤ 40 words body per slide. Exception: hypothesis slide ≤ 60 (alone on slide).
- Bold ≤ 2 key words per block. No underlines, no accent lines, no shadows.

## Emphasis techniques (beyond color/size of whole blocks)

Pick ONE per text element; don't stack them; sprinkle across the deck, not per slide:

1. **In-text size jump** — inside one sentence/statement, set the key word(s)
   noticeably larger than the rest of the same line.
2. **Highlight pill** — the key word(s) in a rounded rectangle, accent (or
   semantic) fill, WHITE text inside; surrounding text stays default black.
   Pointwise only — a big highlight box looks ridiculous.
3. **Pencil circle / underline** — hand-drawn (Excalidraw-style, roughness 1)
   ellipse or underline around a word, accent color.
4. **Inline emoji** — an Apple emoji PNG sitting right beside a key word inside
   the main text. Max 1–2 times per WHOLE deck.

## Spacing = proximity (grouping law)

Related things sit close; unrelated things sit far — distance IS the grouping
signal. Gap inside a group < gap between groups, always by a clear step (e.g. 12px
inside, 32px between). Identical inner padding on all cards of a slide (20–24px).
Never let leftover space stretch gaps between related lines. QA catches uneven
paddings as a defect.

## Cards & layout

- Card: `#F5F5F7` fill, NO border, 16px radius, no shadow, 20–24px padding,
  title bold 18pt, body ≤ 2 lines. Max 3–4 per row, > 6 → split slide.
- **List-of-blocks slides must be catchy, not flat:** each row/card leads with a
  bold key phrase (or an emoji PNG / accent numeral), detail after it in regular
  or gray. A column of same-gray regular-weight rows is a defect.
- Tables: no vertical lines, no zebra; 1px `#E5E5E5` horizontal rules; header and
  winning row bold black.
- Layouts (never same twice in a row; build steps of one logical slide exempt —
  identical layout required): TITLE / DIVIDER(black) / BIG-STATEMENT /
  BLOCKS(default) / METRIC-ROW / DIAGRAM-left+notes-right / COMPARISON(was left
  dimmed → now right colored) / TABLE(≤5×6).
- Before/after reads left → right. 200px+ whitespace around the dominant element.

## Emoji

- **Use them proactively** — vibe-carrying Apple emoji are part of the voice
  (title mood, section dividers, diagram cast, config cards, list-row leads) —
  but in moderation: 1–3 per slide, each doing semantic work. A deck with zero
  emoji is as wrong as a deck drowning in them.
- Always Apple PNG via `scripts/fetch_apple_emoji.py`, placed as image 40–64px
  inline / 96–128px diagram node. Never typed as text.
- Verdicts (pass/fail) use the flat badges from `scripts/gen_verdict_badges.py`
  instead of Apple check/cross — the one sanctioned exception. No other icon
  sets, no decorative symbols.

## Animation

- Default OFF → builds are duplicated slides, one changed element per copy,
  previous elements dimmed `#C7C7CC` (headline/labels may dim; keep body legible).
- If enabled: appear/fade only, ≤ 0.3s, one new element per step, no transitions.

## Don't (AI-slop + flatness list)

Gradients, glassmorphism, shadows, borders on cards, stock photos, icon sets,
purple gradients, centered body text, > 3 colors per slide, walls of text,
plain bullet lists (steps → numbered cards; parts → labeled blocks; comparisons
→ table), two competing bold text blocks, semantic colors in titles, gray primary
content, flat unaccented block lists, loose line-height on big statements,
uneven card paddings.
