#!/usr/bin/env python3
"""Render the profile header as SVG with Archivo outlines converted to paths.

GitHub strips <style> and blocks webfonts inside README images, so live text
would fall back to Helvetica. Converting the glyphs to paths is the only way
to get the real Archivo 800 the portfolio site uses.

Run:  python3 profile/build-header.py
"""
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.pens.svgPathPen import SVGPathPen
from pathlib import Path

FONT = Path(__file__).parent / "archivo-latin-wght-normal.woff2"
OUT = Path(__file__).parent

INK, GROUND, ACCENT = "#201e1d", "#f3f2f2", "#ec3013"

_cache = {}


def face(weight):
    """Archivo instanced at one weight, with its cmap and glyph set."""
    if weight not in _cache:
        f = instancer.instantiateVariableFont(TTFont(FONT), {"wght": weight})
        _cache[weight] = (f, f.getBestCmap(), f.getGlyphSet(), f["hmtx"])
    return _cache[weight]


def text(s, size, weight, x, y, fill, tracking=0.0):
    """One run of text as a <path>. tracking is in em, like CSS letter-spacing."""
    font, cmap, glyphs, hmtx = face(weight)
    upem = font["head"].unitsPerEm
    scale = size / upem
    parts, pen_x = [], 0.0
    for ch in s:
        name = cmap.get(ord(ch))
        if name is None:
            pen_x += 0.5 * upem
            continue
        pen = SVGPathPen(glyphs)
        glyphs[name].draw(pen)
        d = pen.getCommands()
        if d:
            parts.append(f'<path d="{d}" transform="translate({pen_x:.1f} 0)"/>')
        pen_x += hmtx[name][0] + tracking * upem
    body = "".join(parts)
    # y-flip: font space is y-up, SVG is y-down
    return (
        f'<g fill="{fill}" transform="translate({x} {y}) scale({scale:.5f} {-scale:.5f})">'
        f"{body}</g>"
    ), pen_x * scale


def width_of(s, size, weight, tracking=0.0):
    font, cmap, _, hmtx = face(weight)
    upem = font["head"].unitsPerEm
    w = sum(
        (hmtx[cmap[ord(c)]][0] if ord(c) in cmap else 0.5 * upem) + tracking * upem
        for c in s
    )
    return w * size / upem


def rule(x, y, w, color, h=2):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}"/>'


def build(dark):
    ink = GROUND if dark else INK
    ground = INK if dark else GROUND
    W, H = 1200, 430
    M = 64  # left margin — everything is flush to it
    o = [f'<rect width="{W}" height="{H}" fill="{ground}"/>']

    # The one red element up top: a short accent rule, not a full-width band.
    o.append(rule(M, 56, 96, ACCENT, 8))

    # Wordmark, two lines, tight. This is the whole point of the header.
    o.append(text("HSIN-CHEN", 132, 800, M, 196, ink, -0.025)[0])
    o.append(text("PAI", 132, 800, M, 314, ink, -0.025)[0])

    # Tagline, set against the wordmark's second line on the right.
    tag = "I BUILD SYSTEMS"
    tag2 = "THAT SHIP AND GET USED."
    o.append(text(tag, 27, 600, M + 372, 268, ink, 0.02)[0])
    o.append(text(tag2, 27, 600, M + 372, 306, ink, 0.02)[0])

    # Bottom rule + the three facts, red numerals.
    o.append(rule(M, 352, W - 2 * M, ink))
    facts = [
        ("01", "NCKU × PURDUE  '27"),
        ("02", "CTO, TREKX"),
        ("03", "RMOT RESEARCH, NYCU"),
    ]
    x = M
    for num, label in facts:
        o.append(text(num, 19, 800, x, 392, ACCENT, 0.04)[0])
        nx = width_of(num, 19, 800, 0.04) + 14
        o.append(text(label, 19, 600, x + nx, 392, ink, 0.04)[0])
        x += nx + width_of(label, 19, 600, 0.04) + 56

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}" role="img" '
        f'aria-label="Hsin-Chen Pai — I build systems that ship and get used.">'
        + "".join(o)
        + "</svg>"
    )


for dark in (False, True):
    p = OUT / ("header-dark.svg" if dark else "header.svg")
    p.write_text(build(dark))
    print(f"{p.name}  {p.stat().st_size / 1024:.1f} KB")
