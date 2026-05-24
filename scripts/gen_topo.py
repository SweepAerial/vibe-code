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
# Spatially diverse — enforce a min distance between picked contour centroids.
def centroid(path_d):
    nums = [float(n) for n in re.findall(r'-?\d+(?:\.\d+)?', path_d)]
    xs, ys = nums[0::2], nums[1::2]
    return (sum(xs) / len(xs), sum(ys) / len(ys))

import re
# Place dots across the whole canvas — the topo bg is masked
# differently per page (right side on most pages, left side on the
# home hero) so we want dots visible on either side. Target enough
# that ~50 fall in each visible half.
candidates = [
    (i, p) for i, p in enumerate(paths)
    if p["length"] > 200
]
random.shuffle(candidates)
TARGET = 50
MIN_DIST = 55  # viewBox units — light spread, allow many picks
chosen = []
for i, p in candidates:
    cx, cy = centroid(p["d"])
    if all(math.hypot(cx - ox, cy - oy) > MIN_DIST for ox, oy in (c[2] for c in chosen)):
        chosen.append((i, p, (cx, cy)))
    if len(chosen) >= TARGET:
        break
# Top up: only ~200 distinct contours exist, so allow multiple dots per
# contour (each placed at a different starting offset along the line).
if len(chosen) < TARGET:
    pool = candidates[:]
    while len(chosen) < TARGET and pool:
        i, p = random.choice(pool)
        chosen.append((i, p, centroid(p["d"])))
comet_picks = [(i, p) for (i, p, _) in chosen]
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
      .comet {{ fill: none; stroke: {STROKE_HOT}; stroke-width: 3.6; stroke-linecap: round;
              opacity: 0; }}
    </style>
    <filter id="glow" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="1.8" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
'''

body = "\n  ".join(path_lines)

comet_lines = []
# Bright dot that travels a short way along the contour and fades.
# Each dot gets a random starting offset so dots on the same contour
# appear at different positions instead of stacking.
for idx, (pi, p) in enumerate(comet_picks):
    perim = p["length"]
    gap = perim
    dot_len = 1.5                    # near-point — round linecap makes it a dot
    travel = perim * 0.18            # short glide along the line
    dur = 1.1 + (idx % 5) * 0.15     # 1.1-1.7s
    begin = (idx * 0.13) % 14        # densely staggered starts across 14s
    cycle_gap = 3 + (idx % 5)        # 3-7s quiet between blinks per dot
    start_off = random.uniform(0, perim)
    end_off = start_off + travel
    common_anim_begin = f"{begin}s;sweep{idx}.end+{cycle_gap}s"
    comet_lines.append(f'''  <path class="comet" d="{p["d"]}" stroke-dasharray="{dot_len} {gap:.1f}" stroke-dashoffset="{-start_off:.1f}">
    <animate attributeName="stroke-dashoffset" from="{-start_off:.1f}" to="{-end_off:.1f}" dur="{dur}s" begin="{common_anim_begin}" id="sweep{idx}" fill="freeze"/>
    <animate attributeName="opacity" values="0;0.95;0" keyTimes="0;0.18;1" dur="{dur}s" begin="{common_anim_begin}"/>
  </path>''')

svg = header + "  " + body + "\n" + "\n".join(comet_lines) + "\n</svg>\n"

out = Path(__file__).resolve().parent.parent / "images" / "topo-bg.svg"
out.write_text(svg)
print(f"wrote {out} ({out.stat().st_size} bytes, {len(paths)} contours, "
      f"{len(comet_picks)} comets)")
