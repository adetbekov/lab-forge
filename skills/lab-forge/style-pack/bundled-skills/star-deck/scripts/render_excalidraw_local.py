#!/usr/bin/env python3
"""Local .excalidraw -> PNG renderer (offline fallback for Kroki).

Supports the subset used by star-deck diagrams: rounded rectangles, lines,
multi-line text (mono), arrows with polyline points + end arrowhead,
solid/dashed/dotted strokes, fills, opacity.

Usage: python3 render_local.py diagram.excalidraw [out.png]
"""

import json
import math
import pathlib
import sys

import cairosvg

MONO = "DejaVu Sans Mono, monospace"
SANS = "DejaVu Sans, sans-serif"
DASH = {"solid": None, "dashed": "13,9", "dotted": "3,7"}


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def el_bbox(el):
    if el["type"] in ("arrow", "line"):
        xs = [el["x"] + p[0] for p in el["points"]]
        ys = [el["y"] + p[1] for p in el["points"]]
        return min(xs), min(ys), max(xs), max(ys)
    return el["x"], el["y"], el["x"] + el.get("width", 0), el["y"] + el.get("height", 0)


def render(path, out_png=None, scale=2.0):
    data = json.loads(pathlib.Path(path).read_text())
    els = [e for e in data["elements"] if not e.get("isDeleted")]
    x0 = min(el_bbox(e)[0] for e in els) - 12
    y0 = min(el_bbox(e)[1] for e in els) - 12
    x1 = max(el_bbox(e)[2] for e in els) + 12
    y1 = max(el_bbox(e)[3] for e in els) + 12
    w, h = x1 - x0, y1 - y0
    parts = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="{h:.0f}" '
            f'viewBox="{x0:.0f} {y0:.0f} {w:.0f} {h:.0f}">'
        )
    ]
    for el in els:
        op = el.get("opacity", 100) / 100.0
        stroke = el.get("strokeColor", "#1D1D1F")
        sw = el.get("strokeWidth", 1) * 1.6
        dash = DASH.get(el.get("strokeStyle", "solid"))
        d_attr = f' stroke-dasharray="{dash}"' if dash else ""
        t = el["type"]
        if t == "rectangle":
            fill = el.get("backgroundColor", "transparent")
            fill = "none" if fill == "transparent" else fill
            rx = 14 if el.get("roundness") else 0
            parts.append(
                f'<rect x="{el["x"]}" y="{el["y"]}" width="{el["width"]}" '
                f'height="{el["height"]}" rx="{rx}" fill="{fill}" stroke="{stroke}" '
                f'stroke-width="{sw}"{d_attr} opacity="{op}"/>'
            )
        elif t == "ellipse":
            fill = el.get("backgroundColor", "transparent")
            fill = "none" if fill == "transparent" else fill
            cx, cy = el["x"] + el["width"] / 2, el["y"] + el["height"] / 2
            parts.append(
                f'<ellipse cx="{cx}" cy="{cy}" '
                f'rx="{el["width"] / 2}" ry="{el["height"] / 2}" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d_attr} '
                f'opacity="{op}"/>'
            )
        elif t == "text":
            fs = el.get("fontSize", 16)
            fam = MONO if el.get("fontFamily", 3) == 3 else SANS
            lines = el["text"].split("\n")
            align = el.get("textAlign", "center")
            if align == "center":
                tx, anchor = el["x"] + el.get("width", 0) / 2, "middle"
            elif align == "right":
                tx, anchor = el["x"] + el.get("width", 0), "end"
            else:
                tx, anchor = el["x"], "start"
            lh = fs * el.get("lineHeight", 1.25)
            total = lh * len(lines)
            ty0 = el["y"] + (el.get("height", total) - total) / 2 + fs * 0.82
            for i, ln in enumerate(lines):
                parts.append(
                    f'<text x="{tx}" y="{ty0 + i * lh:.1f}" font-family="{fam}" '
                    f'font-size="{fs}" fill="{stroke}" text-anchor="{anchor}" '
                    f'opacity="{op}">{esc(ln)}</text>'
                )
        elif t in ("arrow", "line"):
            pts = [(el["x"] + p[0], el["y"] + p[1]) for p in el["points"]]
            d = "M " + " L ".join(f"{px:.1f} {py:.1f}" for px, py in pts)
            parts.append(
                f'<path d="{d}" fill="none" stroke="{stroke}" stroke-width="{sw}"'
                f'{d_attr} opacity="{op}"/>'
            )
            if t == "arrow" and el.get("endArrowhead") == "arrow":
                (ax, ay), (bx, by) = pts[-2], pts[-1]
                ang = math.atan2(by - ay, bx - ax)
                size = 11 + sw * 1.5
                for da in (math.radians(153), -math.radians(153)):
                    ex = bx + size * math.cos(ang + da)
                    ey = by + size * math.sin(ang + da)
                    parts.append(
                        f'<path d="M {bx:.1f} {by:.1f} L {ex:.1f} {ey:.1f}" '
                        f'fill="none" stroke="{stroke}" stroke-width="{sw}" '
                        f'opacity="{op}" stroke-linecap="round"/>'
                    )
    parts.append("</svg>")
    svg = "".join(parts)
    out = pathlib.Path(out_png or str(path).replace(".excalidraw", ".png"))
    cairosvg.svg2png(bytestring=svg.encode(), write_to=str(out), scale=scale)
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    print(render(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
