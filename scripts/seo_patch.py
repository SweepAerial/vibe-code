#!/usr/bin/env python3
"""SEO patch: rewrites <title>, <meta description>, adds keywords,
canonical, Open Graph + Twitter card tags, and JSON-LD LocalBusiness
schema on the main pages. Also improves a few generic image alts.

Run from repo root: python3 scripts/seo_patch.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://sweepaerial.com.au"
BRAND = "Sweep Aerial Photography"

# Per-page SEO content. Title format follows the user's "Top 10 Coffee Shops"
# example — front-loaded with keyword + benefit/specificity, brand at the end.
PAGES = {
    "home.html": {
        "url": f"{SITE}/",
        "title": "Drone Mapping Australia: Precision Aerial Surveys, GIS & Construction Monitoring | Sweep Aerial Photography",
        "desc": "Australia-wide drone mapping, aerial surveys, GIS outputs, construction progress monitoring, stockpile volume calculations and custom reports. Fast turnaround. Get a free quote.",
        "keywords": "drone mapping australia, aerial survey, drone surveying services, construction progress monitoring, stockpile volume measurement, gis mapping drone, orthomosaic mapping, photogrammetry services, drone gis, aerial photography construction",
        "og_image": "/images/FullSweepLogoWhiteOutline.svg",
    },
    "services.html": {
        "url": f"{SITE}/services.html",
        "title": "5 Drone Survey Services Built for Construction, Mining & Land Development | Sweep Aerial",
        "desc": "Explore our five core drone services: high-accuracy drone mapping, construction visualisations, construction progress monitoring, stockpile volume calculations and custom GIS reports. Delivered Australia-wide with fast turnaround.",
        "keywords": "drone mapping services, construction progress drone monitoring, stockpile volume drone, orthomosaic generation, 3d site reconstruction, gaussian splatting construction, drone gis reports, aerial photogrammetry, construction site survey drone, mine site drone survey",
        "og_image": "/images/FullSweepLogoWhiteOutline.svg",
    },
    "portfolio.html": {
        "url": f"{SITE}/portfolio.html",
        "title": "Drone Mapping Portfolio: Real Construction & Survey Project Deliverables | Sweep Aerial",
        "desc": "Browse real-world drone mapping, orthomosaic, photogrammetry and construction monitoring projects delivered by Sweep Aerial Photography. See raw aerial capture compared to processed outputs.",
        "keywords": "drone mapping portfolio, orthomosaic examples, construction drone survey case study, drone photogrammetry samples, aerial survey portfolio australia, drone mapping deliverables",
        "og_image": "/images/FullSweepLogoWhiteOutline.svg",
    },
    "about.html": {
        "url": f"{SITE}/about.html",
        "title": "About Sweep Aerial Photography | Australia's Precision Drone Mapping & Survey Team",
        "desc": "Meet the surveyors and drone operators behind Sweep Aerial Photography. We invest in industry-leading hardware and processing software to deliver precision aerial intelligence with fast turnaround.",
        "keywords": "drone surveyors australia, professional drone mapping team, aerial survey company, drone surveying experts, photogrammetry specialists australia",
        "og_image": "/images/FullSweepLogoWhiteOutline.svg",
    },
    "contact.html": {
        "url": f"{SITE}/contact.html",
        "title": "Get a Free Drone Mapping Quote | Sweep Aerial Photography Australia",
        "desc": "Request a free, no-obligation quote for drone mapping, aerial surveys, construction progress monitoring or stockpile volume calculations. Australia-wide coverage. Reply within one business day.",
        "keywords": "drone mapping quote, aerial survey quote australia, construction drone services contact, hire drone surveyor, drone mapping cost",
        "og_image": "/images/FullSweepLogoWhiteOutline.svg",
    },
    "index.html": {
        "url": f"{SITE}/",
        "title": "Sweep Aerial Photography | Drone Mapping & Aerial Survey Services — Coming Soon",
        "desc": "Sweep Aerial Photography: precision drone mapping, construction progress monitoring, stockpile volume calculations, photogrammetry and GIS reports. Launching soon — register your interest for a free project consultation.",
        "keywords": "drone mapping australia, aerial survey services, construction drone monitoring, stockpile volume drone, photogrammetry australia, drone gis, sweep aerial photography",
        "og_image": "/images/FullSweepLogoWhiteOutline.svg",
    },
}


def upsert_meta(html, name, content, attr="name"):
    """Insert or replace <meta name|property="..." content="..."> inside <head>."""
    pattern = re.compile(rf'<meta\s+{attr}="{re.escape(name)}"[^>]*>', re.IGNORECASE)
    tag = f'<meta {attr}="{name}" content="{content}">'
    if pattern.search(html):
        return pattern.sub(tag, html)
    # insert after <meta name="viewport"...>
    return re.sub(r'(<meta\s+name="viewport"[^>]*>)',
                  r'\1\n  ' + tag, html, count=1)


def upsert_link(html, rel, href, extra=""):
    pattern = re.compile(rf'<link\s+rel="{re.escape(rel)}"[^>]*>', re.IGNORECASE)
    tag = f'<link rel="{rel}" href="{href}"{(" " + extra) if extra else ""}>'
    if pattern.search(html):
        return pattern.sub(tag, html)
    return re.sub(r'(<meta\s+name="viewport"[^>]*>)',
                  r'\1\n  ' + tag, html, count=1)


def replace_title(html, title):
    return re.sub(r'<title>.*?</title>', f'<title>{title}</title>', html,
                  count=1, flags=re.DOTALL)


# ---- JSON-LD LocalBusiness/ProfessionalService schema -----------------------
JSON_LD = '''<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "ProfessionalService",
  "name": "Sweep Aerial Photography",
  "url": "%(site)s",
  "logo": "%(site)s/images/FullSweepLogoWhiteOutline.svg",
  "image": "%(site)s/images/FullSweepLogoWhiteOutline.svg",
  "description": "Precision drone mapping, aerial surveys, construction progress monitoring, stockpile volume calculations, photogrammetry and GIS reporting across Australia.",
  "email": "hello@sweepaerial.com.au",
  "telephone": "+61411209280",
  "areaServed": { "@type": "Country", "name": "Australia" },
  "serviceType": [
    "Drone Mapping",
    "Aerial Survey",
    "Construction Progress Monitoring",
    "Stockpile Volume Calculation",
    "Photogrammetry",
    "GIS Reporting",
    "Construction Visualisation"
  ],
  "sameAs": []
}
</script>''' % {"site": SITE}


def inject_jsonld(html):
    if "application/ld+json" in html:
        return html
    return html.replace("</head>", "  " + JSON_LD + "\n</head>", 1)


def add_social_and_canonical(html, page):
    html = upsert_link(html, "canonical", page["url"])
    # Open Graph
    html = upsert_meta(html, "og:type", "website", attr="property")
    html = upsert_meta(html, "og:site_name", BRAND, attr="property")
    html = upsert_meta(html, "og:title", page["title"], attr="property")
    html = upsert_meta(html, "og:description", page["desc"], attr="property")
    html = upsert_meta(html, "og:url", page["url"], attr="property")
    html = upsert_meta(html, "og:image", SITE + page["og_image"], attr="property")
    # Twitter card
    html = upsert_meta(html, "twitter:card", "summary_large_image")
    html = upsert_meta(html, "twitter:title", page["title"])
    html = upsert_meta(html, "twitter:description", page["desc"])
    html = upsert_meta(html, "twitter:image", SITE + page["og_image"])
    # Robots (allow indexing on main pages)
    html = upsert_meta(html, "robots", "index,follow")
    # Author
    html = upsert_meta(html, "author", BRAND)
    return html


# ---- Image alt improvements -------------------------------------------------
ALT_REWRITES = {
    'alt="Raw aerial capture"':
        'alt="Raw aerial drone capture of a construction site before photogrammetry processing"',
    'alt="Processed aerial output"':
        'alt="Processed orthomosaic map output from drone photogrammetry"',
    'alt="Processed orthomosaic"':
        'alt="Geo-referenced orthomosaic processed from drone aerial imagery"',
    'alt="Sweep Aerial"':
        'alt="Sweep Aerial Photography drone mapping and aerial survey services Australia"',
    'alt="Sweep Aerial Photography"':
        'alt="Sweep Aerial Photography logo — Australian drone mapping and aerial survey company"',
}


def rewrite_alts(html):
    for old, new in ALT_REWRITES.items():
        html = html.replace(old, new)
    return html


# ---- Apply ------------------------------------------------------------------
for fname, page in PAGES.items():
    path = ROOT / fname
    if not path.exists():
        print(f"skip {fname} (missing)")
        continue
    html = path.read_text()
    html = replace_title(html, page["title"])
    html = upsert_meta(html, "description", page["desc"])
    html = upsert_meta(html, "keywords", page["keywords"])
    html = add_social_and_canonical(html, page)
    html = inject_jsonld(html)
    html = rewrite_alts(html)
    path.write_text(html)
    print(f"patched {fname}")

# ---- robots.txt + sitemap.xml -----------------------------------------------
robots = f"""User-agent: *
Allow: /
Disallow: /portal.html
Disallow: /portal-dashboard.html

Sitemap: {SITE}/sitemap.xml
"""
(ROOT / "robots.txt").write_text(robots)
print("wrote robots.txt")

urls = [
    ("/", "1.0", "weekly"),
    ("/services.html", "0.9", "monthly"),
    ("/portfolio.html", "0.8", "monthly"),
    ("/about.html", "0.6", "monthly"),
    ("/contact.html", "0.7", "monthly"),
]
sitemap_entries = "\n".join(
    f'  <url>\n    <loc>{SITE}{u}</loc>\n    <changefreq>{cf}</changefreq>\n'
    f'    <priority>{p}</priority>\n  </url>'
    for u, p, cf in urls
)
sitemap = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{sitemap_entries}
</urlset>
'''
(ROOT / "sitemap.xml").write_text(sitemap)
print("wrote sitemap.xml")
