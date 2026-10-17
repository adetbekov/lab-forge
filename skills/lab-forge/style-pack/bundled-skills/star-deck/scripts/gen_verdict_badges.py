#!/usr/bin/env python3
"""Verdict badges (offline replacement for Apple emoji PNGs, network down):
green check circle / red cross circle, drawn with PIL, 128px, transparent bg.
"""

import pathlib

from PIL import Image, ImageDraw

HERE = pathlib.Path(__file__).parent
S = 128


def badge(name, color, strokes):
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([4, 4, S - 4, S - 4], fill=color)
    for pts in strokes:
        d.line(pts, fill="white", width=13, joint="curve")
        for p in pts:
            d.ellipse([p[0] - 6, p[1] - 6, p[0] + 6, p[1] + 6], fill="white")
    img.save(HERE / name)
    print(HERE / name)


badge("check.png", "#34C759", [[(34, 66), (56, 90), (94, 42)]])
badge("cross.png", "#FF3B30", [[(42, 42), (86, 86)], [(86, 42), (42, 86)]])
