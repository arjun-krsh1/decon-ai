"""
shopify.py — public-JSON adapter for Comp's Nemesis.

Reads a brand's OWN public storefront JSON (the same data its website uses):
  /products.json?limit=250&page=N   → full catalog: title, type, tags, variants
                                       (price, compare_at_price=MRP, available), body_html
  /sitemap.xml → /sitemap_products_*.xml → product URLs + lastmod

No logins, no grey-hat — this is Shopify's public storefront API. Every product
carries its public source URL for verifiability. A ScraperAPI fallback covers any
store that starts blocking datacenter IPs (none do today, per the probe).
"""

from __future__ import annotations

import os
import time
import json
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus

import requests
from dotenv import load_dotenv

load_dotenv()

SCRAPER_API_KEY = os.getenv("SCRAPER_API_KEY", "")
_UA = {"User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/125.0 Safari/537.36")}


# Per-run fetch accounting: how many pages went out FREE (direct) vs. through
# PAID ScraperAPI credits. proxy == 0 means the run spent zero ScraperAPI credits.
FETCH_STATS = {"direct": 0, "proxy": 0, "fail": 0}


def _get(url: str, timeout: int = 45) -> str:
    """Public GET returning text (''). Direct (free) first; ScraperAPI fallback if blocked."""
    try:
        r = requests.get(url, headers=_UA, timeout=timeout, allow_redirects=True)
        if r.status_code == 200:
            FETCH_STATS["direct"] += 1
            return r.text
    except Exception:
        pass
    if SCRAPER_API_KEY:
        try:
            prox = (f"http://api.scraperapi.com/?api_key={SCRAPER_API_KEY}"
                    f"&url={quote_plus(url)}&country_code=in")
            r = requests.get(prox, timeout=90)
            if r.status_code == 200:
                FETCH_STATS["proxy"] += 1
                return r.text
        except Exception:
            pass
    FETCH_STATS["fail"] += 1
    return ""


def _num(x) -> float:
    try:
        return float(x)
    except Exception:
        return 0.0


# ── catalog (the Phase-1 workhorse: one call → launches + price + stock + ingredients) ──
def fetch_catalog(domain: str, max_pages: int = 12, page_size: int = 250) -> list:
    """All raw Shopify products via paginated /products.json."""
    out = []
    for page in range(1, max_pages + 1):
        body = _get(f"https://{domain}/products.json?limit={page_size}&page={page}")
        if not body:
            break
        try:
            batch = json.loads(body).get("products", [])
        except Exception:
            break
        if not batch:
            break
        out.extend(batch)
        if len(batch) < page_size:
            break
        time.sleep(0.4)  # polite
    return out


def normalize(brand: str, domain: str, p: dict) -> dict:
    """One Shopify product → flat, tracked-fields dict (price range across variants)."""
    handle = p.get("handle", "")
    variants = p.get("variants") or []
    prices = [_num(v.get("price")) for v in variants if v.get("price") not in (None, "")]
    comps = [_num(v.get("compare_at_price")) for v in variants
             if v.get("compare_at_price") not in (None, "")]
    price = min(prices) if prices else 0.0
    mrp = max(comps) if comps else 0.0
    discount = round((1 - price / mrp) * 100, 1) if (mrp and price and mrp > price) else 0.0
    return {
        "brand": brand,
        "handle": handle,
        "url": f"https://{domain}/products/{handle}",
        "title": p.get("title", ""),
        "product_type": p.get("product_type", ""),
        "vendor": p.get("vendor", ""),
        "tags": ", ".join(p["tags"]) if isinstance(p.get("tags"), list) else (p.get("tags") or ""),
        "price": price,
        "mrp": mrp,
        "discount_pct": discount,
        "available": bool(any(v.get("available") for v in variants)),
        "variants": len(variants),
        "published_at": (p.get("published_at") or "")[:10],
        "updated_at": (p.get("updated_at") or "")[:10],
        "body_html": p.get("body_html") or "",
    }


def fetch_products(brand: str, domain: str) -> list:
    """Fetch + normalize a brand's whole catalog."""
    return [normalize(brand, domain, p) for p in fetch_catalog(domain)]


# ── sitemap (secondary: lastmod signal + URLs beyond the catalog) ──
def fetch_sitemap_urls(domain: str) -> list:
    """Product URLs + lastmod from /sitemap.xml (follows nested product sitemaps)."""
    urls = []
    root_xml = _get(f"https://{domain}/sitemap.xml")
    if not root_xml:
        return urls
    try:
        root = ET.fromstring(root_xml)
    except Exception:
        return urls
    prod_maps = [el.text for el in root.iter()
                 if el.tag.endswith("loc") and el.text and "sitemap_products" in el.text]
    for pm in prod_maps:
        body = _get(pm)
        if not body:
            continue
        try:
            r = ET.fromstring(body)
        except Exception:
            continue
        for url_el in r.iter():
            if not url_el.tag.endswith("url"):
                continue
            loc = lastmod = ""
            for c in url_el:
                if c.tag.endswith("loc"):
                    loc = c.text or ""
                elif c.tag.endswith("lastmod"):
                    lastmod = c.text or ""
            if "/products/" in loc:
                urls.append({"loc": loc, "lastmod": lastmod[:10]})
        time.sleep(0.3)
    return urls
