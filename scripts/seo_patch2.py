#!/usr/bin/env python3
"""SEO pass 2: FAQPage schema, BreadcrumbList schema, Service schema,
font preconnect on all pages, and a few keyword-rich internal links in
body copy. Run after seo_patch.py."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://sweepaerial.com.au"
BRAND = "Sweep Aerial Photography"


def insert_before_close_head(html, snippet):
    return html.replace("</head>", "  " + snippet + "\n</head>", 1)


def already_has(html, marker):
    return marker in html


# ---- Font preconnect on every main page (perf -> Core Web Vitals) -----------
PRECONNECT = '''<link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'''

for fname in ["home.html", "services.html", "portfolio.html", "about.html",
              "contact.html"]:
    p = ROOT / fname
    html = p.read_text()
    if 'rel="preconnect" href="https://fonts.googleapis.com"' not in html:
        # insert just after viewport meta
        html = re.sub(r'(<meta\s+name="viewport"[^>]*>)',
                      r'\1\n  ' + PRECONNECT, html, count=1)
        p.write_text(html)
        print(f"preconnect added to {fname}")


# ---- BreadcrumbList JSON-LD -------------------------------------------------
BREADCRUMBS = {
    "services.html":  [("Home", "/"), ("Services", "/services.html")],
    "portfolio.html": [("Home", "/"), ("Portfolio", "/portfolio.html")],
    "about.html":     [("Home", "/"), ("About", "/about.html")],
    "contact.html":   [("Home", "/"), ("Contact", "/contact.html")],
}

for fname, trail in BREADCRUMBS.items():
    p = ROOT / fname
    html = p.read_text()
    if '"BreadcrumbList"' in html:
        continue
    items = ",\n    ".join(
        f'{{"@type":"ListItem","position":{i+1},"name":"{name}","item":"{SITE}{url}"}}'
        for i, (name, url) in enumerate(trail)
    )
    snippet = f'''<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {items}
  ]
}}
</script>'''
    p.write_text(insert_before_close_head(html, snippet))
    print(f"breadcrumbs added to {fname}")


# ---- FAQPage JSON-LD on contact.html ----------------------------------------
FAQ_ITEMS = [
    ("What areas do you operate in?",
     "We operate Australia-wide. Our team is based in Australia but we regularly travel for drone mapping and aerial survey projects across all states and territories. Travel costs may apply for remote or regional locations and are included in your quote."),
    ("Do you handle CASA airspace approvals?",
     "Yes. We hold a CASA ReOC (Remotely Piloted Aircraft Operator's Certificate) and manage all airspace approvals, NOTAM submissions, and site permissions as part of our standard drone mapping workflow. You don't need to handle any aviation compliance."),
    ("How accurate are your survey outputs?",
     "With RTK-enabled drones and ground control points, we achieve horizontal accuracy of 2-3cm and vertical accuracy of 3-5cm on our drone surveys. For applications requiring tighter tolerances such as cadastral surveys, discuss your specific requirements with us upfront."),
    ("What file formats do you deliver?",
     "We deliver in the formats your team already uses: GeoTIFF orthomosaics, LAS/LAZ point clouds, OBJ/FBX meshes, SHP/GDB GIS data, DXF/DWG CAD files, and KML/KMZ for Google Earth. Tell us what platform you work in and we will match it."),
]

p = ROOT / "contact.html"
html = p.read_text()
if '"FAQPage"' not in html:
    qa = ",\n    ".join(
        '{{"@type":"Question","name":"{q}","acceptedAnswer":{{"@type":"Answer","text":"{a}"}}}}'
        .format(q=q.replace('"', '\\"'), a=a.replace('"', '\\"'))
        for q, a in FAQ_ITEMS
    )
    snippet = f'''<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {qa}
  ]
}}
</script>'''
    p.write_text(insert_before_close_head(html, snippet))
    print("FAQPage schema added to contact.html")


# ---- Service ItemList JSON-LD on services.html ------------------------------
SERVICES = [
    ("Drone Mapping",
     "High-accuracy drone mapping, orthomosaics, point clouds and digital surface models for construction, mining and land development sites across Australia."),
    ("Construction Visualisations",
     "3D photorealistic site reconstructions and Gaussian splat visualisations that turn aerial captures into shareable interactive models."),
    ("Construction Progress Monitoring",
     "Regular drone capture and side-by-side change detection so project managers can track schedule, earthworks and build progress over time."),
    ("Stockpile Volume Calculations",
     "Stockpile volume measurement from drone imagery, delivered with full calculation reports and comparison over time."),
    ("Customised GIS Reports",
     "Tailored GIS deliverables, CAD overlays, contour maps and analysis reports formatted for the platforms your team already uses."),
]
p = ROOT / "services.html"
html = p.read_text()
if '"OfferCatalog"' not in html:
    items = ",\n        ".join(
        '{{"@type":"Offer","itemOffered":{{"@type":"Service","name":"{n}","description":"{d}"}}}}'
        .format(n=n, d=d.replace('"', '\\"'))
        for n, d in SERVICES
    )
    snippet = f'''<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "ProfessionalService",
  "name": "{BRAND}",
  "url": "{SITE}/services.html",
  "areaServed": {{"@type":"Country","name":"Australia"}},
  "hasOfferCatalog": {{
    "@type": "OfferCatalog",
    "name": "Drone Mapping & Aerial Survey Services",
    "itemListElement": [
        {items}
    ]
  }}
}}
</script>'''
    p.write_text(insert_before_close_head(html, snippet))
    print("Service OfferCatalog schema added to services.html")


# ---- Internal linking: convert a few mentions in body copy to anchors -------
# Only patch first occurrence on each page to avoid over-optimisation.
INTERNAL_LINKS = {
    "home.html": [
        ("Drone mapping, Gaussian splatting, construction monitoring",
         '<a href="services.html">Drone mapping</a>, Gaussian splatting, <a href="services.html#progress">construction monitoring</a>'),
    ],
    "about.html": [
        ("drone operators",
         '<a href="services.html">drone operators</a>'),
    ],
    "portfolio.html": [
        ("Our Work in the Field",
         "Our Work in the Field"),  # unchanged; placeholder if needed
    ],
}

for fname, pairs in INTERNAL_LINKS.items():
    p = ROOT / fname
    if not p.exists():
        continue
    html = p.read_text()
    changed = False
    for old, new in pairs:
        if old in html and new != old and new not in html:
            html = html.replace(old, new, 1)
            changed = True
    if changed:
        p.write_text(html)
        print(f"internal links added to {fname}")
