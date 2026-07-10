"""
Comp's Nemesis — D2C competitor intelligence for Deconstruct.

Exploits the GAP between a brand's own website and its marketplace listings.
All data is PUBLIC and structured: each brand's Shopify storefront JSON
(/products.json, /sitemap.xml) plus the marketplace pipelines already in Decon AI.
Every datapoint carries its public source URL; Deconstruct is always the baseline.

One generic engine, per-feature modules:
  brands.py    — competitor registry (verified Shopify domains)
  shopify.py   — public-JSON adapter (catalog, prices, stock, ingredients, sitemap)
  (snapshots / launches / pricing / stock … added per feature)
"""

from .brands import BRANDS, BASELINE, domain_for
from .shopify import fetch_products, fetch_catalog, normalize, fetch_sitemap_urls

__all__ = ["BRANDS", "BASELINE", "domain_for",
           "fetch_products", "fetch_catalog", "normalize", "fetch_sitemap_urls"]
