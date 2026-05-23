#!/usr/bin/env python3
"""Generate a topographic background SVG by contouring a real 2D elevation
field. Uses sum-of-sines noise + marching-squares (skimage.measure.find_contours)
so the resulting lines behave like real topo contours: closed loops around
peaks, meandering ridges, lines that run off the edges, never crossing.

Adds occasional 'comet' light sweeps along a few selected contour lines.

Output: images/topo-bg.svg
"""
import math
import random
from pathlib import Path

import numpy as np
from skimage import measure

random.seed(5)
np.random.seed(5)

W, H = 2000, 1200
GRID_W, GRID_H = 320, 192        # field resolution (scaled to viewBox)
SX = W / GRID_W
SY = H / GRID_H

STROKE = "#a78bda"
STROKE_HOT = "#6925bf"           # brand purple


# ---- Elevation field --------------------------------------------------------
def make_field():
    """Sum of low-frequency 2D sines with random orientation / phase, plus a
    few gaussian 'peaks' to give the map clear elevation maxima around which
    contours form tight nested loops."""
    xs = np.linspace(0, 1, GRID_W)
    ys = np.linspace(0, 1, GRID_H)
    X, Y = np.meshgrid(xs, ys)

    field = np.zeros_like(X)
    # Layered sines — varying spatial frequencies & directions
    for freq, amp in [(1.6, 1.0), (2.7, 0.55), (4.3, 0.32), (7.1, 0.18), (11.0, 0.10)]:
        ang = np.random.uniform(0, math.pi * 2)
        phx = np.random.uniform(0, math.pi * 2)
        phy = np.random.uniform(0, math.pi * 2)
        kx = math.cos(ang) * freq * math.pi * 2
        ky = math.sin(ang) * freq * math.pi * 2
        field += amp * np.sin(X * kx + phx) * np.cos(Y * ky + phy)

    # Add a handful of gaussian peaks/pits to produce nested concentric loops
    for _ in range(7):
        px, py = np.random.uniform(0.05, 0.95), np.random.uniform(0.05, 0.95)
        sigma = np.random.uniform(0.06, 0.13)
        sign = np.random.choice([-1.0, 1.0])
        amp = np.random.uniform(0.8, 1.6) * sign
        field += amp * np.exp(-(((X - px) ** 2 + (Y - py) ** 2) / (2 * sigma ** 2)))

    # normalise
    field -= field.mean()
    field /= field.std()
    return field


field = make_field()

# Pick contour levels evenly spaced across the field's value range, skipping
# the very extremes so we get a satisfying number of lines.
lo, hi = np.percentile(field, [3, 97])
N_LEVELS = 26
levels = np.linspace(lo, hi, N_LEVELS)


# ---- Build SVG paths from contours ------------------------------------------
def path_from_contour(contour, simplify=1.0):
    """contour is an (N,2) array of (row, col) coordinates from find_contours.
    Convert to viewBox space and emit an SVG polyline path."""
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


paths = []           # list of dicts {d, level_idx, length, closed}
for li, lvl in enumerate(levels):
    for c in measure.find_contours(field, lvl):
        if len(c) < 8:
            continue
        d = path_from_contour(c, simplify=0.8)
        if d is None:
            continue
        # length in field-grid units (approx)
        diffs = np.diff(c, axis=0)
        length = float(np.sum(np.hypot(diffs[:, 0] * SY, diffs[:, 1] * SX)))
        closed = bool(np.allclose(c[0], c[-1]))
        paths.append({"d": d, "li": li, "length": length, "closed": closed})


# ---- Pick comet target paths: medium-length closed loops in mid-elevation ---
candidates = [
    (i, p) for i, p in enumerate(paths)
    if p["closed"] and 600 < p["length"] < 2200 and 6 <= p["li"] <= N_LEVELS - 6
]
random.shuffle(candidates)
comet_picks = candidates[:6]
comet_ids = {i: f"c{k}" for k, (i, _) in enumerate(comet_picks)}


# ---- Emit SVG ---------------------------------------------------------------
def style_for(p):
    # Faint, subtle background; slight emphasis every ~5th contour like real maps
    every5 = (p["li"] % 5 == 0)
    sw = 1.2 if every5 else 0.8
    op = 0.42 if every5 else 0.26
    return sw, op


path_lines = []
for i, p in enumerate(paths):
    sw, op = style_for(p)
    attrs = f'stroke-width="{sw}" opacity="{op}"'
    pid = comet_ids.get(i, "")
    id_attr = f' id="{pid}"' if pid else ""
    path_lines.append(f'<path{id_attr} d="{p["d"]}" {attrs}/>')

header = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid slice">
  <defs>
    <style>
      path {{ fill: none; stroke: {STROKE}; stroke-linejoin: round; stroke-linecap: round; }}
      .comet {{ fill: none; stroke: {STROKE_HOT}; stroke-width: 1.8; stroke-linecap: round;
                filter: url(#glow); opacity: 0; }}
    </style>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="2.6" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
'''

body = "\n  ".join(path_lines)

comet_lines = []
for idx, (pi, p) in enumerate(comet_picks):
    perim = p["length"]
    seg = max(60, perim * 0.10)
    gap = perim
    dur = 9 + (idx % 3) * 2
    begin = idx * 2.6
    cycle_gap = 8 + (idx % 4) * 2
    comet_lines.append(f'''  <path class="comet" d="{p["d"]}" stroke-dasharray="{seg:.1f} {gap:.1f}" stroke-dashoffset="0">
    <animate attributeName="stroke-dashoffset" from="0" to="{-perim:.1f}" dur="{dur}s" begin="{begin}s;sweep{idx}.end+{cycle_gap}s" id="sweep{idx}" fill="freeze"/>
    <animate attributeName="opacity" values="0;0.9;0.9;0" keyTimes="0;0.08;0.92;1" dur="{dur}s" begin="{begin}s;sweep{idx}.end+{cycle_gap}s"/>
  </path>''')

svg = header + "  " + body + "\n" + "\n".join(comet_lines) + "\n</svg>\n"

out = Path(__file__).resolve().parent.parent / "images" / "topo-bg.svg"
out.write_text(svg)
print(f"wrote {out} ({out.stat().st_size} bytes, {len(paths)} contours, "
      f"{len(comet_picks)} comets)")
