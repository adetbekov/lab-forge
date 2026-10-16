# Output formats. PPTX is the default; others on request.

Common to all: tokens from design-system.md only; fonts Helvetica Neue → Helvetica
→ Arial (declare the chain explicitly — never silent substitution); emoji and
diagrams inserted as images (PNG ≥2×); deliver artifact + build source + outline.md
+ .excalidraw files (reproducibility); QA = render every slide to an image and look
at it, ≥1 fix-and-verify cycle.

## PPTX (default)

- 16:9 (13.333"×7.5"), python-pptx or PptxGenJS. A platform pptx skill may drive
  the mechanics; star-deck overrides all its visual/content defaults.
- Cards: rounded rects, `#F5F5F7` fill, NO line, no shadow. Saying "no shadow" in
  the API is not enough: PowerPoint themes attach preset shadows via `<p:style>`
  on autoshapes. At build time, for every autoshape strip the `<p:style>` element
  (or add an explicit empty `<a:effectLst/>` to `spPr`) — python-pptx:
  `sp._element.remove(sp._element.find(qn('p:style')))`. Then verify in QA
  renders: any visible card shadow = defect, fix and re-render.
- Disable text autofit/shrink (overflow must surface in QA, get fixed by splitting).
- Tables native; header/winner bold; horizontal 1px `#E5E5E5` rules only.
- Builds: animation OFF → duplicated slides, one element changes, previous dimmed
  `#C7C7CC`. ON → appear/fade ≤0.3s per step (PptxGenJS; python-pptx can't author
  animation → duplicate instead).
- QA render: `soffice --headless --convert-to pdf` → `pdftoppm -jpeg -r 150`;
  programmatic: bounds, overlaps, ≥18pt, ≤40 words, grep XML for placeholders and
  text-emoji (must be zero).

## HTML/JS

- One self-contained .html: inline CSS/JS, `<section class="slide">` per slide,
  1920×1080 scaled via transform, arrow-key nav, `?print` → vertical layout for PDF.
- Tokens as CSS variables copied verbatim; diagrams as inline SVG (crisper, CSS
  can dim/recolor); reveal.js via CDN acceptable if user asks.
- Builds: duplicated sections; animation ON → `data-step` reveal, opacity ≤0.3s,
  past steps get `.dim`.
- QA: Playwright screenshots @1920×1080 per slide; check
  `scrollWidth > clientWidth`.

## Slidev

- `slides.md` + `style.css` + run instructions (`npx slidev`). `theme: none`,
  restyle from tokens — never ship default theme covers.
- Headmatter fonts: sans Helvetica Neue, mono Menlo. Divider → `layout: center` +
  black class; blocks/metrics → CSS grid; diagram+notes → `layout: two-cols`.
- Builds: `v-clicks` (= animation ON), style `.slidev-vclick-prior { color:#C7C7CC }`.
- Diagrams: `<img>` of rendered SVG — never built-in mermaid. Code: fenced + Shiki,
  ≤15 lines, `{lines}` highlighting.
- QA/export: `npx slidev export --format png` → inspect; `--format pdf` to share.

## Google Slides

- Route A (default): build PPTX per above; user imports (File → Import slides).
  Helvetica Neue isn't in Google Fonts → it will map to Arial; acceptable, note it
  in delivery. Appear/fade survive import; images import fine.
- Route B (API access exists): `presentations.batchUpdate`, one batch per slide;
  colors as rgbColor, sizes in PT; images must be hosted/Drive first; builds =
  duplicated slides (API can't animate).
- QA: export PDF → render → compare fonts against PPTX renders.

## PDF

- Render target, not authoring: from PPTX via `soffice --convert-to pdf` (check
  `pdffonts` for fallback surprises) or from HTML via Playwright `page.pdf()`
  with `printBackground: true` (keeps black dividers).
- Builds stay duplicated pages — correct, presenting page-by-page reproduces them.
- QA: `pdftoppm` → inspect; page count = physical slide count; diagrams not blurry.

## Keynote

- No reliable writer → build import-clean PPTX: appear/fade only (map to
  Appear/Dissolve), no embedded fonts (Keynote ignores; Helvetica Neue is native
  on macOS anyway), flat placement (groups shift on import).
- macOS automation optional: `osascript` open .pptx in Keynote → export .key/PDF.
- QA: export PDF from Keynote, compare page-by-page (fonts, margins, dividers are
  the usual casualties).
