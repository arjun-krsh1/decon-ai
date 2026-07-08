"""
taxonomy.py — classify a cited URL into a source TYPE.

The source-type mix is the agent's "where to post" priority list, so this
classification directly drives strategy. Types (per brief §4):
    Your site | Competitor site | Reddit | Quora | Wikipedia | YouTube |
    Marketplace | Editorial/blog | Other
"""

from __future__ import annotations

from urllib.parse import urlparse

# Known Indian D2C skincare brand domains — used to tell "Your site" and
# "Competitor site" apart from editorial/marketplace pages.
BRAND_DOMAINS = {
    "Deconstruct": "thedeconstruct.in",
    "Minimalist": "beminimalist.co",
    "Dot & Key": "dotandkey.com",
    "Dr. Sheth's": "drsheths.com",
    "Dr Sheths": "drsheths.com",
    "The Derma Co": "thedermaco.com",
    "The Derma Co.": "thedermaco.com",
    "Foxtale": "foxtale.in",
    "Aqualogica": "aqualogica.in",
    "Re'equil": "reequil.com",
    "Plum": "plumgoodness.com",
    "Pilgrim": "discoverpilgrim.com",
    "mCaffeine": "mcaffeine.com",
    "Mamaearth": "mamaearth.in",
}

MARKETPLACE_DOMAINS = (
    "nykaa.com", "amazon.", "flipkart.com", "myntra.com",
    "purplle.com", "tira", "meesho.com", "ajio.com",
)

REDDIT = ("reddit.com",)
QUORA = ("quora.com",)
WIKIPEDIA = ("wikipedia.org", "wikidata.org")
YOUTUBE = ("youtube.com", "youtu.be")


def domain_of(url: str) -> str:
    """Return a normalised registrable-ish domain (no www)."""
    if not url:
        return ""
    try:
        netloc = urlparse(url if "://" in url else f"//{url}", scheme="").netloc or url
        netloc = netloc.lower().split(":")[0]
        return netloc[4:] if netloc.startswith("www.") else netloc
    except Exception:
        return url.lower()


def classify(url: str, brand: str, competitors: list[str]) -> str:
    """Classify one cited URL into a source type."""
    dom = domain_of(url)
    if not dom:
        return "Other"

    brand_dom = BRAND_DOMAINS.get(brand, "").lower()
    if brand_dom and brand_dom in dom:
        return "Your site"

    for c in competitors:
        cdom = BRAND_DOMAINS.get(c, "").lower()
        if cdom and cdom in dom:
            return "Competitor site"
        # fall back to a loose name match in the domain (e.g. "foxtale" in "foxtale.in")
        slug = c.lower().replace(" ", "").replace("'", "").replace("&", "and").replace(".", "")
        if slug and len(slug) > 3 and slug in dom.replace(".", "").replace("-", ""):
            return "Competitor site"

    if any(d in dom for d in REDDIT):
        return "Reddit"
    if any(d in dom for d in QUORA):
        return "Quora"
    if any(d in dom for d in WIKIPEDIA):
        return "Wikipedia"
    if any(d in dom for d in YOUTUBE):
        return "YouTube"
    if any(d in dom for d in MARKETPLACE_DOMAINS):
        return "Marketplace"
    return "Editorial/blog"
