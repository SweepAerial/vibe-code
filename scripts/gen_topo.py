#!/usr/bin/env python3
"""Generate a busy topographic background SVG with subtle animated 'light' pulses
on some contour rings. Output: images/topo-bg.svg"""
import math
import random
from pathlib import Path

random.seed(7)

W, H = 2000, 1200
STROKE = "#a78bda"        # mid lilac — visible on both light and dark
STROKE_HOT = "#ffd24a"    # warm highlight used by the animated comet


def smooth_blob(cx, cy, rx, ry, points=18, jitter=0.18, rot=0.0, shape_seed=None):
    """Return a closed smooth (cubic Bezier) blob path centered at (cx,cy).
    shape_seed lets nested rings share the same per-angle radial offset pattern,
    so concentric rings stay nested and parallel rather than crossing."""
    if shape_seed is None:
        shape_seed = random.random() * 1e9
    rng = random.Random(shape_seed)
    offsets = [(rng.random() - 0.5) * 2 * jitter for _ in range(points)]
    pts = []
    for i in range(points):
        a = 2 * math.pi * i / points + rot
        r_jit = 1 + offsets[i]
        x = cx + math.cos(a) * rx * r_jit
        y = cy + math.sin(a) * ry * r_jit
        pts.append((x, y))
    # Catmull-Rom -> Bezier
    n = len(pts)
    d = [f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"]
    for i in range(n):
        p0 = pts[(i - 1) % n]
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        p3 = pts[(i + 2) % n]
        c1x = p1[0] + (p2[0] - p0[0]) / 6
        c1y = p1[1] + (p2[1] - p0[1]) / 6
        c2x = p2[0] - (p3[0] - p1[0]) / 6
        c2y = p2[1] - (p3[1] - p1[1]) / 6
        d.append(f"C{c1x:.1f},{c1y:.1f} {c2x:.1f},{c2y:.1f} {p2[0]:.1f},{p2[1]:.1f}")
    d.append("Z")
    return " ".join(d)


def island(cx, cy, base_rx, base_ry, rings, points=18, jitter=0.18, shrink=0.82):
    """Yield (path_d, ring_index, total_rings) for nested concentric blobs.
    All rings share the same shape_seed so they nest cleanly."""
    rot = random.random() * math.pi * 2
    shape_seed = random.random() * 1e9
    rx, ry = base_rx, base_ry
    for i in range(rings):
        yield smooth_blob(cx, cy, rx, ry, points=points,
                          jitter=jitter * (1 - i * 0.04), rot=rot,
                          shape_seed=shape_seed), i, rings
        rx *= shrink
        ry *= shrink


# Define island centers across the canvas — overlapping for a busy look.
# tuple = (cx, cy, rx, ry, rings, points, jitter)
# Elongated, overlapping islands give a flowing-contour look rather than bullseyes
islands = [
    (260, 260, 460, 220, 7, 30, 0.42),
    (1080, 180, 520, 180, 6, 32, 0.40),
    (1740, 290, 480, 240, 7, 30, 0.42),
    (880, 640, 600, 260, 8, 32, 0.40),
    (1560, 620, 420, 220, 7, 28, 0.42),
    (290, 740, 420, 220, 6, 28, 0.42),
    (1870, 920, 500, 240, 7, 30, 0.40),
    (900, 1020, 540, 200, 6, 30, 0.42),
    (340, 1070, 420, 180, 5, 26, 0.42),
    (1390, 1040, 360, 180, 5, 26, 0.42),
    (650, 350, 280, 140, 5, 24, 0.44),
    (1300, 400, 300, 150, 5, 24, 0.44),
    (1180, 820, 320, 160, 5, 24, 0.44),
    (560, 920, 300, 150, 5, 24, 0.44),
    (1680, 1050, 300, 150, 5, 24, 0.44),
]
# Smaller scattered islands to fill density
for _ in range(18):
    cx = random.randint(80, W - 80)
    cy = random.randint(80, H - 80)
    r = random.randint(110, 230)
    rr = r * random.uniform(0.4, 0.7)
    rings = random.randint(3, 5)
    islands.append((cx, cy, r, rr, rings, 22, 0.44))

# Build paths. Mark some rings as dashed; collect candidates for the animated pulse.
path_lines = []
animated_targets = []  # list of (path_id, length_estimate)

pid = 0
for (cx, cy, rx, ry, rings, pts, jit) in islands:
    for d, i, total in island(cx, cy, rx, ry, rings, points=pts, jitter=jit):
        pid += 1
        # styling: outer rings slightly heavier, alternating dashed
        outer = i < 2
        dashed = (i % 4 == 1) and rings >= 5
        sw = 1.4 if outer else 1.0
        op = 0.55 if outer else 0.42
        cls = []
        attrs = f'stroke-width="{sw}" opacity="{op}"'
        if dashed:
            attrs += ' stroke-dasharray="6 7"'
        # Mark a handful of medium rings as animation targets
        anim_id = ""
        if not dashed and i in (1, 2) and rx > 200 and random.random() < 0.45:
            anim_id = f' id="r{pid}"'
            # rough perimeter estimate for dash math
            perim = 2 * math.pi * ((rx + ry) / 2) * (0.82 ** i)
            animated_targets.append((f"r{pid}", perim))
        path_lines.append(f'<path{anim_id} d="{d}" {attrs}/>')

# Build the SVG
header = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid slice">
  <defs>
    <style>
      path {{ fill: none; stroke: {STROKE}; stroke-linejoin: round; stroke-linecap: round; }}
      .comet {{ fill: none; stroke: {STROKE_HOT}; stroke-width: 1.6; stroke-linecap: round;
                 filter: url(#glow); opacity: 0.0; }}
    </style>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="2.2" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
'''

body = "\n  ".join(path_lines)

# Animated comets: clone selected rings as overlays and animate stroke-dashoffset
comet_lines = []
# Find the d attribute for each animated id
import re
id_to_d = {}
for line in path_lines:
    m = re.search(r'id="(r\d+)"\s+d="([^"]+)"', line)
    if m:
        id_to_d[m.group(1)] = m.group(2)

# Limit to ~8 simultaneous comets staggered in time
selected = animated_targets[:10]
for idx, (rid, perim) in enumerate(selected):
    d = id_to_d.get(rid)
    if not d:
        continue
    seg = max(40, perim * 0.08)        # short bright arc
    gap = perim                         # rest of ring hidden
    dash = f"{seg:.1f} {gap:.1f}"
    dur = 7 + (idx % 4) * 2             # 7s-13s
    begin = idx * 1.8                   # stagger starts
    cycle_gap = 6 + (idx % 3) * 2       # quiet time between sweeps
    total = dur + cycle_gap
    # We animate dashoffset from 0 -> -perim, and opacity in a short window
    comet_lines.append(f'''  <path class="comet" d="{d}" stroke-dasharray="{dash}" stroke-dashoffset="0">
    <animate attributeName="stroke-dashoffset" from="0" to="{-perim:.1f}" dur="{dur}s" begin="{begin}s;sweep{idx}.end+{cycle_gap}s" id="sweep{idx}" fill="freeze"/>
    <animate attributeName="opacity" values="0;0.9;0.9;0" keyTimes="0;0.08;0.92;1" dur="{dur}s" begin="{begin}s;sweep{idx}.end+{cycle_gap}s"/>
  </path>''')

svg = header + "  " + body + "\n" + "\n".join(comet_lines) + "\n</svg>\n"

out = Path(__file__).resolve().parent.parent / "images" / "topo-bg.svg"
out.write_text(svg)
print(f"wrote {out} ({out.stat().st_size} bytes, {len(path_lines)} paths, {len(selected)} comets)")
