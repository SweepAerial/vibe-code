#!/usr/bin/env python3
"""Generate a horizontal topographic 'horizon' divider — a single organic
contour line spanning the canvas width, used as a section divider on the
home page (between the hero and the next section).

Output: images/topo-divider.svg
"""
import math
import random
from pathlib import Path

random.seed(31)

W, H = 2000, 80                # very short height — sits on a section seam
N = 320
STROKE = "#a78bda"

# Build the line from a sum of low-frequency sines so it undulates gently.
amps = [
    (random.uniform(8, 14),  random.uniform(0.6, 1.2),  random.uniform(0, math.tau)),
    (random.uniform(4, 8),   random.uniform(1.8, 2.6),  random.uniform(0, math.tau)),
    (random.uniform(2, 4),   random.uniform(3.5, 5.2),  random.uniform(0, math.tau)),
    (random.uniform(1, 2),   random.uniform(7.0, 9.0),  random.uniform(0, math.tau)),
]

pts = []
for i in range(N + 1):
    t = i / N
    x = t * W
    y = H / 2
    for a, f, p in amps:
        y += a * math.sin(t * f * math.pi * 2 + p)
    pts.append((x, y))

# Smooth via Catmull-Rom -> Bezier
def to_path(pts):
    d = [f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"]
    n = len(pts)
    for i in range(n - 1):
        p0 = pts[max(0, i - 1)]
        p1 = pts[i]
        p2 = pts[i + 1]
        p3 = pts[min(n - 1, i + 2)]
        c1x = p1[0] + (p2[0] - p0[0]) / 6
        c1y = p1[1] + (p2[1] - p0[1]) / 6
        c2x = p2[0] - (p3[0] - p1[0]) / 6
        c2y = p2[1] - (p3[1] - p1[1]) / 6
        d.append(f"C{c1x:.1f},{c1y:.1f} {c2x:.1f},{c2y:.1f} {p2[0]:.1f},{p2[1]:.1f}")
    return " ".join(d)

main = to_path(pts)
# Second, ghost line slightly offset for depth (like a second contour)
ghost = to_path([(x, y + 6) for x, y in pts])

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" preserveAspectRatio="none">
  <g fill="none" stroke="{STROKE}" stroke-linecap="round" stroke-linejoin="round">
    <path d="{ghost}" stroke-width="0.8" opacity="0.20"/>
    <path d="{main}"  stroke-width="1.3" opacity="0.55"/>
  </g>
</svg>
'''

out = Path(__file__).resolve().parent.parent / "images" / "topo-divider.svg"
out.write_text(svg)
print(f"wrote {out} ({out.stat().st_size} bytes)")
