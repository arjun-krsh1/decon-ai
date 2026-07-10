"""
enrich.py — ingredient (INCI) extraction + bundle detection for Comp's Nemesis.

Both are derived from the Shopify catalog we already collect:
  • ingredients  ← product description (body_html), matched against a documented
                   skincare-actives lexicon (deterministic + traceable, no guessing)
  • bundles      ← title / product_type keywords

Feeds #6 (cross-brand "rising ingredient" trends) and #8 (bundle/AOV strategy).
"""

from __future__ import annotations

import re
from collections import defaultdict

# canonical active -> substrings that indicate it (lower-cased match on description)
ACTIVES = {
    "Niacinamide": ["niacinamide"],
    "Salicylic acid (BHA)": ["salicylic"],
    "Hyaluronic acid": ["hyaluronic"],
    "Vitamin C": ["vitamin c", "ascorbic", "ferulic"],
    "Retinol / Retinoid": ["retinol", "retinoid", "retinal", "adapalene"],
    "Bakuchiol": ["bakuchiol"],
    "Ceramide": ["ceramide"],
    "Peptides": ["peptide"],
    "Glycolic acid (AHA)": ["glycolic"],
    "Lactic acid": ["lactic acid"],
    "Mandelic acid": ["mandelic"],
    "Azelaic acid": ["azelaic"],
    "Kojic acid": ["kojic"],
    "Alpha arbutin": ["arbutin"],
    "Benzoyl peroxide": ["benzoyl"],
    "Tranexamic acid": ["tranexamic"],
    "Zinc": ["zinc pca", "zinc oxide"],
    "Centella / Cica": ["centella", "cica", "madecassoside"],
    "Tea tree": ["tea tree"],
    "Squalane": ["squalane"],
    "Panthenol (B5)": ["panthenol"],
    "Caffeine": ["caffeine"],
    "Vitamin E": ["tocopherol", "vitamin e"],
    "Collagen": ["collagen"],
    "SPF / UV filters": ["spf", "avobenzone", "octocrylene", "zinc oxide", "titanium dioxide"],
}

BUNDLE_KW = ("kit", "combo", "bundle", " set", "duo", "trio", "regimen", "routine",
             "pack of", "gift set", "value pack", "hamper")


def _plain(body_html: str) -> str:
    return re.sub("<[^>]+>", " ", body_html or "").lower()


def extract_actives(body_html: str) -> list:
    """Detected actives in a product's description (canonical names, deduped)."""
    t = _plain(body_html)
    return sorted({canon for canon, syns in ACTIVES.items() if any(s in t for s in syns)})


def is_bundle(product: dict) -> bool:
    t = (product.get("title", "") + " " + product.get("product_type", "")).lower()
    return any(k in t for k in BUNDLE_KW)


def ingredient_trends(catalogs: dict) -> list:
    """Cross-brand active adoption: for each active, which brands feature it + count.
    A high brand_count = an active the category has converged on (are we late?)."""
    by_active = defaultdict(set)
    for brand, prods in (catalogs or {}).items():
        for p in prods:
            for a in extract_actives(p.get("body_html", "")):
                by_active[a].add(brand)
    rows = [{"active": a, "brand_count": len(bs), "brands": ", ".join(sorted(bs))}
            for a, bs in by_active.items()]
    rows.sort(key=lambda r: -r["brand_count"])
    return rows


def bundle_summary(catalogs: dict, baseline: str = "Deconstruct") -> list:
    """Per-brand bundle strategy: how many bundles, their share, and avg bundle price."""
    rows = []
    for brand, prods in (catalogs or {}).items():
        bundles = [p for p in prods if is_bundle(p)]
        prices = [p["price"] for p in bundles if p.get("price")]
        rows.append({
            "brand": brand,
            "is_baseline": brand == baseline,
            "bundles": len(bundles),
            "bundle_share_%": round(len(bundles) / len(prods) * 100) if prods else 0,
            "avg_bundle_price": round(sum(prices) / len(prices)) if prices else 0,
        })
    rows.sort(key=lambda r: (not r["is_baseline"], -r["bundles"]))
    return rows
