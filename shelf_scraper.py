"""
shelf_scraper.py — Digital-Shelf data layer for the Market Share module.

For a category keyword, pull the top listings from each marketplace and normalise
them to a common shape, so the analytics layer can compute share-of-shelf,
share-of-search, assortment, price tiers and keyword patterns.

Sources (chosen for reliability, verified against live pages):
  Amazon   → SerpAPI (reuse the Product-Intel pipeline; brand+price+rating+reviews)
  Myntra   → window.__myx JSON state (brand+price+rating+count)
  Nykaa    → __PRELOADED_STATE__ JSON (brand+price+mrp+rating+count)
  Flipkart → __INITIAL_STATE__ SEO schema (title+url+rank; top ~10)

Every field is a DIRECT read from the marketplace's own embedded data — no AI,
no estimation. Missing fields are left empty (never fabricated).
"""

from __future__ import annotations

import os
import json
import time
import hashlib
import pathlib
import http.client
from urllib.parse import quote_plus

# Some marketplaces (Nykaa) return >100 response headers via ScraperAPI; Python's
# default cap (100) makes `requests` raise "got more than 100 headers". Lift it.
http.client._MAXHEADERS = 1000  # type: ignore[attr-defined]

from dotenv import load_dotenv
load_dotenv()

from amazon_scraper import search_amazon, match_competitor, safe_number

# When set, Nykaa/Myntra/Flipkart requests route through ScraperAPI's residential
# proxies — needed on cloud hosts whose datacenter IPs those sites block. Unset
# (e.g. locally) → direct stealth HTTP, so local behaviour is unchanged.
SCRAPER_API_KEY = os.getenv("SCRAPER_API_KEY", "")
SCRAPER_API_COUNTRY = os.getenv("SCRAPER_API_COUNTRY", "in")

CACHE = pathlib.Path("scraper/cache/shelf")
CACHE.mkdir(parents=True, exist_ok=True)

PLATFORMS = ["Amazon", "Nykaa", "Myntra", "Flipkart"]

DEFAULT_CATEGORIES = [
    "sunscreen", "vitamin c serum", "niacinamide serum", "moisturizer",
    "face wash", "face serum", "retinol serum", "sunscreen for oily skin",
]


def _fetch(url):
    """Fast HTTP GET returning HTML (or '').

    If SCRAPER_API_KEY is set, the request is proxied through ScraperAPI (rotating
    residential IPs + anti-bot bypass, India geo) — this is what makes Nykaa/Myntra/
    Flipkart work on a cloud host whose datacenter IP those sites block. With no key
    it falls back to Scrapling's direct stealth HTTP, so local behaviour is unchanged.
    """
    # ── ScraperAPI path (cloud): plain requests — ScraperAPI handles the stealth ──
    if SCRAPER_API_KEY:
        import requests
        target = (f"http://api.scraperapi.com/?api_key={SCRAPER_API_KEY}"
                  f"&url={quote_plus(url)}&country_code={SCRAPER_API_COUNTRY}")
        try:
            r = requests.get(target, timeout=90)
            if r.status_code == 200 and r.text:
                return r.text
            print(f"    [shelf] scraperapi {url[:45]} -> HTTP {r.status_code}: {r.text[:100]}")
        except Exception as e:
            print(f"    [shelf] scraperapi error {url[:45]}: {e}")
        return ""

    # ── direct path (local): Scrapling stealth HTTP ──
    from scrapling.fetchers import Fetcher
    try:
        p = Fetcher.get(url, stealthy_headers=True, timeout=30)
        if p.status == 200:
            return p.html_content or ""
        print(f"    [shelf] fetch {url[:50]} -> HTTP {p.status}")
    except Exception as e:
        print(f"    [shelf] fetch error {url[:50]}: {e}")
    return ""


def _json_after(html, marker):
    """Extract the first balanced JSON object appearing after `marker`."""
    i = html.find(marker)
    if i < 0:
        return None
    b = html.find("{", i)
    if b < 0:
        return None
    try:
        obj, _ = json.JSONDecoder().raw_decode(html, b)
        return obj
    except Exception:
        return None


def _canon_brand(raw, title):
    """Canonical tracked-brand name if it matches one, else the cleaned raw brand."""
    canon = match_competitor(raw or "", title or "")
    if canon:
        return canon, True
    raw = (raw or "").strip()
    if not raw and title:                       # Flipkart: derive from title
        raw = str(title).split(",")[0].split(" ")[0].strip()
    return (raw or "Unknown"), False


def _listing(platform, keyword, rank, title, brand_raw, price=0, mrp=0,
             rating=0, reviews=0, url=""):
    brand, tracked = _canon_brand(brand_raw, title)
    return {
        "platform": platform, "keyword": keyword, "rank": rank,
        "title": str(title or "")[:160], "brand": brand, "brand_raw": str(brand_raw or ""),
        "is_tracked": tracked,
        "price": safe_number(price), "mrp": safe_number(mrp),
        "rating": round(safe_number(rating, max_val=5), 1),
        "reviews": int(safe_number(reviews)),
        "url": url,
    }


# ── per-platform scrapers ─────────────────────────────────────────────────────
def scrape_amazon(keyword, n=20):
    out = []
    for i, sr in enumerate(search_amazon(keyword, n), 1):
        out.append(_listing("Amazon", keyword, i, sr.get("title", ""), sr.get("brand", ""),
                            price=sr.get("price", 0), mrp=sr.get("mrp", 0),
                            rating=sr.get("rating", 0), reviews=sr.get("review_count_raw", 0),
                            url=sr.get("url", "")))
    return out


def scrape_myntra(keyword, n=30):
    html = _fetch(f"https://www.myntra.com/{keyword.replace(' ', '-')}")
    obj = _json_after(html, "window.__myx")
    prods = (((obj or {}).get("searchData") or {}).get("results") or {}).get("products", []) if obj else []
    out = []
    for i, p in enumerate(prods[:n], 1):
        out.append(_listing("Myntra", keyword, i, p.get("productName", ""), p.get("brand", ""),
                            price=p.get("price", 0), rating=p.get("rating", 0),
                            reviews=p.get("ratingCount", 0),
                            url=f"https://www.myntra.com/{p.get('landingPageUrl', '')}"))
    return out


def scrape_nykaa(keyword, n=30):
    html = _fetch(f"https://www.nykaa.com/search/result/?q={keyword.replace(' ', '%20')}")
    obj = _json_after(html, "__PRELOADED_STATE__")
    prods = ((((obj or {}).get("categoryListing") or {}).get("listingData") or {})
             .get("products", [])) if obj else []
    out = []
    for i, p in enumerate(prods[:n], 1):
        slug = p.get("slug", "")
        out.append(_listing("Nykaa", keyword, i, p.get("name", p.get("title", "")),
                            p.get("brandName", ""), price=p.get("price", 0), mrp=p.get("mrp", 0),
                            rating=p.get("rating", 0), reviews=p.get("ratingCount", 0),
                            url=f"https://www.nykaa.com/{slug}/p/{p.get('productId', '')}" if slug else ""))
    return out


def scrape_flipkart(keyword, n=20):
    html = _fetch(f"https://www.flipkart.com/search?q={keyword.replace(' ', '%20')}")
    obj = _json_after(html, "__INITIAL_STATE__")
    items = ((((obj or {}).get("pageDataV4") or {}).get("browseMetadata") or {})
             .get("seoSchema") or {}).get("itemListElement", []) if obj else []
    out = []
    for it in items[:n]:
        pos = it.get("position", len(out) + 1)
        out.append(_listing("Flipkart", keyword, pos, it.get("name", ""), "",
                            url=it.get("url", "")))
    return out


_SCRAPERS = {"Amazon": scrape_amazon, "Nykaa": scrape_nykaa,
             "Myntra": scrape_myntra, "Flipkart": scrape_flipkart}


# ── orchestrator ──────────────────────────────────────────────────────────────
def collect_shelf(keywords=None, platforms=None, n_per=25, progress_cb=None):
    """
    Scrape every (platform × keyword) and return all normalised listings + a
    coverage report {platform: {keyword: count}} so gaps are transparent.
    Cached 12h per (platform, keyword).
    """
    keywords = keywords or DEFAULT_CATEGORIES
    platforms = platforms or PLATFORMS
    listings, coverage = [], {p: {} for p in platforms}
    total = len(platforms) * len(keywords)
    done = 0

    for kw in keywords:
        for plat in platforms:
            if progress_cb:
                progress_cb(done, total, f"{plat}: '{kw}'")
            ck = CACHE / f"{plat}_{hashlib.md5(f'{kw}_{n_per}'.encode()).hexdigest()}.json"
            rows = None
            if ck.exists() and (time.time() - ck.stat().st_mtime) / 3600 < 12:
                try:
                    rows = json.loads(ck.read_text(encoding="utf-8"))
                except Exception:
                    rows = None
            if rows is None:
                try:
                    rows = _SCRAPERS[plat](kw, n_per)
                    ck.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
                except Exception as e:
                    print(f"[shelf] {plat}/{kw} failed: {e}")
                    rows = []
                time.sleep(1.0)  # be polite
            coverage[plat][kw] = len(rows)
            listings.extend(rows)
            done += 1

    print("[shelf] coverage: " + " | ".join(
        f"{p}={sum(c.values())}" for p, c in coverage.items()))
    return listings, coverage
