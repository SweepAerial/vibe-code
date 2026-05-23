#!/usr/bin/env python3
"""Generate square 'avatar' topo background SVGs in multiple colour combos.
These are boosted (higher opacity / thicker strokes) for use at small sizes
like email-signature avatars (~200 px).

Outputs to images/avatar-topo/topo-<bg>-<stroke>.svg
"""
import math
import random
from pathlib import Path

import numpy as np
from skimage import measure

random.seed(13)
np.random.seed(13)

SIZE = 1200                  # square viewBox
GRID = 220
SX = SY = SIZE / GRID

OUT_DIR = Path(__file__).resolve().parent.parent / "images" / "avatar-topo"
OUT_DIR.mkdir(parents=True, exist_ok=True)


# ---- Elevation field (square) -----------------------------------------------
def make_field():
    xs = np.linspace(0, 1, GRID)
    X, Y = np.meshgrid(xs, xs)
    field = np.zeros_like(X)
    for freq, amp in [(1.6, 1.0), (2.7, 0.55), (4.3, 0.32), (7.1, 0.18), (11.0, 0.10)]:
        ang = np.random.uniform(0, math.pi * 2)
        phx = np.random.uniform(0, math.pi * 2)
        phy = np.random.uniform(0, math.pi * 2)
        kx = math.cos(ang) * freq * math.pi * 2
        ky = math.sin(ang) * freq * math.pi * 2
        field += amp * np.sin(X * kx + phx) * np.cos(Y * ky + phy)
    # A few peaks/pits so we get nested loops near the centre too
    for _ in range(5):
        px, py = np.random.uniform(0.15, 0.85), np.random.uniform(0.15, 0.85)
        sigma = np.random.uniform(0.07, 0.14)
        sign = np.random.choice([-1.0, 1.0])
        amp = np.random.uniform(0.8, 1.6) * sign
        field += amp * np.exp(-(((X - px) ** 2 + (Y - py) ** 2) / (2 * sigma ** 2)))
    field -= field.mean()
    field /= field.std()
    return field


field = make_field()
lo, hi = np.percentile(field, [3, 97])
N_LEVELS = 22
levels = np.linspace(lo, hi, N_LEVELS)


def path_from_contour(contour, simplify=0.8):
    pts = []
    last = None
    for row, col in contour:
        x = col * SX
        y = row * SY
        if last is None or (abs(x - last[0]) + abs(y - last[1])) > simplify:
            pts.append((x, y))
            last = (x, y)
    if len(pts) < 3:
        return None
    parts = [f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"]
    for x, y in pts[1:]:
        parts.append(f"L{x:.1f},{y:.1f}")
    return " ".join(parts)


contours = []
for li, lvl in enumerate(levels):
    for c in measure.find_contours(field, lvl):
        if len(c) < 8:
            continue
        d = path_from_contour(c)
        if d is None:
            continue
        contours.append((d, li))


def build_svg(bg, stroke, opacity_outer=0.75, opacity_inner=0.50,
              sw_outer=2.2, sw_inner=1.4):
    """Build an SVG string for one colour combo. Strokes are boosted so the
    pattern reads at avatar sizes (~200 px)."""
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SIZE} {SIZE}" '
        f'preserveAspectRatio="xMidYMid slice">',
        f'  <rect width="{SIZE}" height="{SIZE}" fill="{bg}"/>',
        f'  <g fill="none" stroke="{stroke}" stroke-linejoin="round" stroke-linecap="round">',
    ]
    for d, li in contours:
        every5 = (li % 5 == 0)
        sw = sw_outer if every5 else sw_inner
        op = opacity_outer if every5 else opacity_inner
        parts.append(f'    <path d="{d}" stroke-width="{sw}" opacity="{op}"/>')
    parts.append('  </g>')
    parts.append('</svg>\n')
    return "\n".join(parts)


# ---- Colour combos ----------------------------------------------------------
# (filename suffix, background, stroke)
combos = [
    ("dark-lilac",     "#0a0a0a", "#a78bda"),  # dark bg, lilac lines
    ("dark-purple",    "#0a0a0a", "#6925bf"),  # dark bg, brand purple lines
    ("light-purple",   "#f0f2f5", "#6925bf"),  # light bg, brand purple lines
    ("light-dkpurple", "#f0f2f5", "#4a1a8a"),  # light bg, darker purple lines
    ("purple-white",   "#6925bf", "#ffffff"),  # brand purple bg, white lines
    ("purple-light",   "#6925bf", "#e8d9ff"),  # brand purple bg, pale lilac
    ("dkpurple-lilac", "#2a0f4e", "#a78bda"),  # very dark purple bg, lilac
    ("dkpurple-white", "#2a0f4e", "#ffffff"),  # very dark purple bg, white
]

written = []
for suffix, bg, stroke in combos:
    # Slightly different boost per combo for best readability
    if bg.startswith("#0") or bg.startswith("#2"):
        op_o, op_i = 0.80, 0.55
    elif bg == "#6925bf":
        op_o, op_i = 0.75, 0.45
    else:  # light bg
        op_o, op_i = 0.70, 0.45
    svg = build_svg(bg, stroke, opacity_outer=op_o, opacity_inner=op_i)
    path = OUT_DIR / f"topo-{suffix}.svg"
    path.write_text(svg)
    written.append(path)

for p in written:
    print(f"wrote {p} ({p.stat().st_size} bytes)")
