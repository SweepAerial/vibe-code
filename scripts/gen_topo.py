#!/usr/bin/env python3
"""Generate a topographic background SVG. Distinct nested islands, smooth
flowing contours, no crossing between islands. Includes occasional animated
'light' sweeps along selected rings.

Output: images/topo-bg.svg
"""
import math
import random
from pathlib import Path

random.seed(11)

W, H = 2000, 1200
STROKE = "#a78bda"          # mid lilac — visible on light + dark themes
STROKE_HOT = "#6925bf"      # brand purple — used by the animated comet


def smooth_blob(cx, cy, rx, ry, points, offsets, rot=0.0):
    """Closed Catmull-Rom -> Bezier path. `offsets` is a list of per-angle
    radial multipliers (around 1.0). Sharing `offsets` between rings keeps
    them nested and parallel."""
    pts = []
    for i in range(points):
        a = 2 * math.pi * i / points + rot
        r = 1 + offsets[i]
        pts.append((cx + math.cos(a) * rx * r,
                    cy + math.sin(a) * ry * r))
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


def make_island(cx, cy, rx, ry, rings, points, jitter, ring_gap=0.91):
    """Generate nested ring path strings for one island. All rings share the
    same `offsets` so they nest cleanly (no crossings within the island)."""
    rot = random.random() * math.pi * 2
    # Low-frequency offsets give smooth, organic shapes (not scribbly).
    # Build from a few sine components so the perimeter undulates gently.
    harmonics = [
        (random.uniform(0.6, 1.0), random.randint(2, 3), random.random() * math.pi * 2),
        (random.uniform(0.3, 0.6), random.randint(3, 4), random.random() * math.pi * 2),
        (random.uniform(0.15, 0.3), random.randint(5, 7), random.random() * math.pi * 2),
    ]
    offsets = []
    for i in range(points):
        a = 2 * math.pi * i / points
        v = 0.0
        for amp, freq, phase in harmonics:
            v += amp * math.sin(a * freq + phase)
        # normalize harmonic sum then scale by jitter
        offsets.append(v / sum(h[0] for h in harmonics) * jitter)

    paths = []
    r1, r2 = rx, ry
    for i in range(rings):
        paths.append((smooth_blob(cx, cy, r1, r2, points, offsets, rot), i, rings,
                      max(r1, r2)))
        r1 *= ring_gap
        r2 *= ring_gap
    return paths


def island_bbox(cx, cy, rx, ry, jitter, pad=20):
    """Approx bounding box including jitter and a small pad."""
    ex = rx * (1 + jitter) + pad
    ey = ry * (1 + jitter) + pad
    return (cx - ex, cy - ey, cx + ex, cy + ey)


def bbox_overlap(a, b):
    return not (a[2] < b[0] or a[0] > b[2] or a[3] < b[1] or a[1] > b[3])


# Hand-placed island centers (cx, cy, rx, ry, rings, points, jitter).
# Spaced so their outer rings don't collide.
placed = [
    # Big anchors — elongated, more rings, gentler shrink
    (310,  240, 320, 170, 9, 44, 0.26),
    (1020, 220, 380, 160, 9, 46, 0.24),
    (1720, 300, 340, 200, 9, 44, 0.26),
    (640,  640, 320, 180, 9, 44, 0.26),
    (1320, 700, 400, 200, 10, 46, 0.24),
    (1830, 820, 260, 170, 7, 38, 0.26),
    (260,  900, 320, 170, 8, 42, 0.26),
    (760, 1040, 300, 130, 7, 38, 0.26),
    (1640,1060, 300, 130, 7, 38, 0.26),
    # Medium fillers
    (1480, 270, 140,  95, 5, 30, 0.28),
    ( 980, 480, 170, 100, 5, 32, 0.28),
    ( 350, 540, 140,  90, 5, 30, 0.28),
    (1130,1010, 170,  95, 5, 32, 0.28),
    (1820, 540, 140,  90, 5, 30, 0.28),
]

# Attempt a few additional random fillers but reject overlapping ones
existing_bboxes = [island_bbox(p[0], p[1], p[2], p[3], p[6]) for p in placed]
random.seed(23)
attempts = 0
while attempts < 200 and len(placed) < 22:
    attempts += 1
    cx = random.randint(120, W - 120)
    cy = random.randint(120, H - 120)
    rx = random.randint(70, 110)
    ry = int(rx * random.uniform(0.55, 0.85))
    jit = 0.24
    bb = island_bbox(cx, cy, rx, ry, jit, pad=30)
    if any(bbox_overlap(bb, eb) for eb in existing_bboxes):
        continue
    existing_bboxes.append(bb)
    placed.append((cx, cy, rx, ry, 3, 26, jit))


# Build paths and pick a handful of mid rings for animation
path_lines = []
anim_targets = []
pid = 0
random.seed(101)
for (cx, cy, rx, ry, rings, points, jit) in placed:
    isle_paths = make_island(cx, cy, rx, ry, rings, points, jit)
    # Mark one mid ring per medium/large island as comet target
    target_ring_idx = 1 if rings >= 5 else 0
    for (d, i, total, ring_r) in isle_paths:
        pid += 1
        outer = i == 0
        # subtle dashes on a single ring per island (not every other one)
        dashed = (rings >= 6 and i == total - 2)
        sw = 1.2 if outer else 0.9
        op = 0.32 if outer else 0.20
        anim_id = ""
        attrs = f'stroke-width="{sw}" opacity="{op}"'
        if dashed:
            attrs += ' stroke-dasharray="5 9"'
        if i == target_ring_idx and rings >= 5 and ring_r > 110:
            anim_id = f' id="r{pid}"'
            perim = 2 * math.pi * ring_r
            anim_targets.append((f"r{pid}", perim))
        path_lines.append(f'<path{anim_id} d="{d}" {attrs}/>')


header = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid slice">
  <defs>
    <style>
      path {{ fill: none; stroke: {STROKE}; stroke-linejoin: round; stroke-linecap: round; }}
      .comet {{ fill: none; stroke: {STROKE_HOT}; stroke-width: 1.8; stroke-linecap: round;
                filter: url(#glow); opacity: 0; }}
    </style>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="2.4" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
'''

body = "\n  ".join(path_lines)

# Animated comets: clone the target rings and sweep a short dash around them
import re
id_to_d = {}
for line in path_lines:
    m = re.search(r'id="(r\d+)"\s+d="([^"]+)"', line)
    if m:
        id_to_d[m.group(1)] = m.group(2)

comet_lines = []
selected = anim_targets[:6]
for idx, (rid, perim) in enumerate(selected):
    d = id_to_d.get(rid)
    if not d:
        continue
    seg = max(50, perim * 0.10)
    gap = perim
    dur = 8 + (idx % 3) * 2          # 8-12s per sweep
    begin = idx * 2.5                # stagger
    cycle_gap = 7 + (idx % 4) * 2    # quiet time between sweeps
    comet_lines.append(f'''  <path class="comet" d="{d}" stroke-dasharray="{seg:.1f} {gap:.1f}" stroke-dashoffset="0">
    <animate attributeName="stroke-dashoffset" from="0" to="{-perim:.1f}" dur="{dur}s" begin="{begin}s;sweep{idx}.end+{cycle_gap}s" id="sweep{idx}" fill="freeze"/>
    <animate attributeName="opacity" values="0;0.9;0.9;0" keyTimes="0;0.08;0.92;1" dur="{dur}s" begin="{begin}s;sweep{idx}.end+{cycle_gap}s"/>
  </path>''')

svg = header + "  " + body + "\n" + "\n".join(comet_lines) + "\n</svg>\n"

out = Path(__file__).resolve().parent.parent / "images" / "topo-bg.svg"
out.write_text(svg)
print(f"wrote {out} ({out.stat().st_size} bytes, {len(path_lines)} paths, "
      f"{len(placed)} islands, {len(selected)} comets)")
