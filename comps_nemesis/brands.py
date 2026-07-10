"""
Competitor registry for Comp's Nemesis.

Domains verified live via each brand's public /products.json + /sitemap.xml
(feasibility probe, all 11 confirmed Shopify). Deconstruct is the baseline that
every comparison is measured against.
"""

BASELINE = "Deconstruct"

# brand -> primary storefront domain (Shopify)
BRANDS = {
    "Deconstruct":        "thedeconstruct.in",
    "Minimalist":         "beminimalist.co",
    "Foxtale":            "foxtale.in",
    "The Derma Co.":      "thedermaco.com",
    "Dot & Key":          "dotandkey.com",
    "Dr. Sheth's":        "drsheths.com",
    "Plum":               "plumgoodness.com",
    "Aqualogica":         "aqualogica.in",
    "Pilgrim":            "discoverpilgrim.com",
    "Hyphen":             "letshyphen.com",
    "Conscious Chemist":  "consciouschemist.com",
}

# Observed field availability from the probe (for transparent UI notes / graceful handling).
# compare_at_price (MRP) is only surfaced by some stores (often only while discounted).
HAS_MRP_FIELD = {"Deconstruct", "Minimalist", "Dot & Key", "Plum", "Pilgrim", "Conscious Chemist"}
HAS_DESCRIPTION = {"Deconstruct", "The Derma Co.", "Dot & Key", "Dr. Sheth's",
                   "Plum", "Pilgrim", "Hyphen", "Conscious Chemist"}


def domain_for(brand: str) -> str:
    return BRANDS.get(brand, "")


def competitors():
    """All tracked brands except the baseline."""
    return [b for b in BRANDS if b != BASELINE]
