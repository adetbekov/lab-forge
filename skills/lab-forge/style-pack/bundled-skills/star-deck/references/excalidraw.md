# Excalidraw — the only diagram tool. Ship PNG on slide + .excalidraw source.

## Diagrams argue, don't display

Before shipping: (a) isomorphism — remove all text mentally, structure alone must
still say it (pipeline/fan-out/hierarchy/loop); (b) education — viewer learns
something concrete. A row of labeled boxes is a list in costume. One structural
pattern per concept, different patterns across the deck: assembly line, fan-out,
convergence, hub-with-hanging-capabilities (agent + model/memory/tools below on
dotted lines), tree (lines + free text, no boxes), side-by-side, nested containers,
gap/break (missing piece).

## Grammar

- Flow strictly left → right (input left, output right). Vertical only for
  prompt-anatomy stacks and CI pipelines.
- Style: **hybrid hand-drawn is the default** — boxes/arrows `roughness: 1`
  (whiteboard feel), labels mono `fontFamily: 3` (readable text over style),
  lowercase. Hand-drawn ellipses/underlines double as pencil-circle emphasis on
  slide text (design-system.md, emphasis technique 3).
- Rounded rects `roundness:{"type":3}`, `strokeWidth: 1` (2 for the focus element),
  `opacity: 100`, `fontSize: 16` (20 section labels).
- Colors (main deck palette, nothing else):

  | Meaning | Stroke | Fill |
  |---|---|---|
  | main flow (default) | `#1D1D1F` | transparent |
  | cluster: blue | `#0071E3` | `#F0F7FF` |
  | cluster: green | `#34C759` | `#F0FBF2` |
  | cluster: indigo | `#5856D6` | `#F2F2FC` |
  | cluster: orange | `#FF9500` | `#FFF7EC` |
  | NEW focus | `#FF9500` | `#FFF7EC` |
  | failure | `#FF3B30` | `#FFF2F1` |
  | retired/background | `#C7C7CC` | transparent |

- **Gray is never primary: the main flow of THIS slide gets black strokes.**
  Gray only for retired/replaced/background elements. In versioned quest
  diagrams: existing active blocks black, the new block orange — do NOT gray
  the whole pipeline (unreadable, says "nothing here matters").
  Exception: spotlight-tour steps intentionally dim everything but the focus
  (~15–20%) — allowed because the full map was already shown in black.
- **Cluster by domain, don't monochrome.** ≥5 nodes → group by domain/type
  (sources, processing, storage, consumers…); same-domain nodes share one color.
- **Adjacent clusters must CONTRAST.** Pick hues far apart (blue↔orange,
  blue↔green, green↔indigo); never two look-alike hues side by side (no
  cyan-next-to-blue). If a hue is doing semantic work on this slide (orange =
  new element, green = success verdict), clusters skip that hue there.
  One loud element per diagram version — always the newly added block.
- Containers: dashed rounded rects for module boundaries, title top-left inside;
  <30% of text inside containers (free-floating labels + typography carry
  hierarchy). Stacked-card glyph (2–3 offset copies) = "many", annotate count.
- Arrows: solid main flow / dashed async / dotted optional; arrowhead at
  destination only.
- Versioned core diagram: author once; produce versions by recolor only (new block
  orange, old dim) — never redraw, or blocks jump between slides.
- Emoji cast members may be nodes (Apple PNG placed on slide, or image element).

## Geometry

Hero 300×150, primary 180×90, secondary 120×60; 200px+ whitespace around hero.
Labeled arrows 150–200px, unlabeled 100–120px; columns 300–400px apart; container
padding 50–60px. Box width ≥ `max(160, chars × 9)` px (×18 CJK) — no truncation.

## JSON essentials

```json
{"type":"excalidraw","version":2,"source":"star-deck","elements":[],
 "appState":{"viewBackgroundColor":"#ffffff","gridSize":20},"files":{}}
```

Element base: descriptive string `id` ("retriever_rect"), `type,x,y,width,height,
strokeColor,backgroundColor,fillStyle:"solid",strokeWidth,strokeStyle,roughness,
opacity,seed,version:1,versionNonce:0,isDeleted:false,groupIds:[],boundElements,
angle:0,locked:false,link:null`.
Text adds: `text,originalText,fontSize,fontFamily,textAlign,verticalAlign,
containerId,lineHeight:1.25`.
Arrow adds: `points:[[0,0],[dx,dy]]` (L-route via midpoints; curve
`roundness:{"type":2}`), `startBinding/endBinding:{elementId,focus:0,gap:2}`,
`endArrowhead:"arrow"`, `startArrowhead:null`.
Container↔label is bidirectional: shape `boundElements:[{id,type:"text"}]` AND
text `containerId`.

## Workflow

1. Words first: pattern, elements, direction.
2. >~10 elements → build JSON section by section (descriptive IDs, seeds 100xx/
   200xx per section); never one-shot large diagrams.
3. Render, in this order (sandboxes often block arbitrary domains):
   (a) `scripts/render_excalidraw.sh d.excalidraw` (Kroki API);
   (b) Kroki blocked → ASK the user to enable network access first
   (SKILL.md network fallback protocol); declined or batch mode →
   (c) `npm install excalidraw-to-svg` + a small Node script;
   (d) `scripts/render_excalidraw_local.py d.excalidraw` (bundled offline
   renderer, needs `pip install cairosvg`; covers the star-deck subset:
   rounded rects, arrows, dashes, mono text, fills).
   **Never "fall back" to drawing diagrams with native PowerPoint/HTML
   shapes** — that abandons the .excalidraw source and the diagram grammar;
   it is a defect, not a fallback. Always render PNG ≥2×.
4. LOOK at the render: left→right, no label overlaps, no arrow crossings, one loud
   element, dims actually dim, no truncation. ≥1 fix cycle (2–4 typical).
