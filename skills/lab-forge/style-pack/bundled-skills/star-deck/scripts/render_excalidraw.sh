#!/usr/bin/env bash
# Render an .excalidraw JSON file to SVG via the Kroki API (zero install),
# then optionally to PNG if a converter is available.
#
# Usage: ./render_excalidraw.sh diagram.excalidraw [out.svg]
set -euo pipefail

IN="${1:?usage: render_excalidraw.sh diagram.excalidraw [out.svg]}"
OUT="${2:-${IN%.excalidraw}.svg}"

curl -sf --data-binary "@${IN}" -H "Content-Type: application/json" \
  https://kroki.io/excalidraw/svg > "${OUT}"
echo "SVG: ${OUT}"

PNG="${OUT%.svg}.png"
if command -v rsvg-convert >/dev/null 2>&1; then
  rsvg-convert -z 2 "${OUT}" -o "${PNG}" && echo "PNG: ${PNG}"
elif command -v inkscape >/dev/null 2>&1; then
  inkscape "${OUT}" --export-type=png --export-dpi=192 -o "${PNG}" && echo "PNG: ${PNG}"
elif python3 -c "import cairosvg" >/dev/null 2>&1; then
  python3 -c "import cairosvg,sys; cairosvg.svg2png(url='${OUT}', write_to='${PNG}', scale=2)" \
    && echo "PNG: ${PNG}"
else
  echo "No SVG->PNG converter found (rsvg-convert / inkscape / cairosvg). SVG only."
fi
