"""
changes.py — the intelligence layer: diff two snapshots into competitive signals.

Given a brand's previous vs current catalog, surface:
  • launches      — product handles that appeared (early-warning; site leads marketplace)
  • removals      — handles that disappeared (discontinued / delisted)
  • price_changes — same product, different price (+ % delta)
  • discount_changes — discount depth moved (campaign / inventory pressure)
  • stock_changes — availability flipped (stock-out or restock)

Junk SKUs (₹1 promos, gift cards, testers) are flagged so they don't distort
PRICE analysis — but launches keep everything (a new kit is still a real signal).
"""

from __future__ import annotations

_NOISE_KW = ("gift card", "e-gift", "tester", "sample", "trial", "freebie", "free gift")


def is_noise(p: dict, min_price: float = 10.0) -> bool:
    """True for non-real-product SKUs that would distort price analysis."""
    title = (p.get("title", "") + " " + p.get("product_type", "")).lower()
    return p.get("price", 0) < min_price or any(k in title for k in _NOISE_KW)


def diff_brand(prev: list, curr: list) -> dict:
    """Diff one brand's previous vs current catalog (lists of normalized products)."""
    pv = {p["handle"]: p for p in (prev or []) if p.get("handle")}
    cu = {p["handle"]: p for p in (curr or []) if p.get("handle")}

    launches = [cu[h] for h in cu if h not in pv]
    removals = [pv[h] for h in pv if h not in cu]

    price_changes, discount_changes, stock_changes = [], [], []
    for h in cu:
        if h not in pv:
            continue
        a, b = pv[h], cu[h]
        if a.get("price") and b.get("price") and a["price"] != b["price"]:
            price_changes.append({
                "brand": b["brand"], "title": b["title"], "url": b["url"],
                "old_price": a["price"], "new_price": b["price"],
                "delta_pct": round((b["price"] - a["price"]) / a["price"] * 100, 1),
                "noise": is_noise(b),
            })
        if a.get("discount_pct", 0) != b.get("discount_pct", 0):
            discount_changes.append({
                "brand": b["brand"], "title": b["title"], "url": b["url"],
                "old_discount": a.get("discount_pct", 0), "new_discount": b.get("discount_pct", 0),
                "deepened": b.get("discount_pct", 0) > a.get("discount_pct", 0),
            })
        if bool(a.get("available")) != bool(b.get("available")):
            stock_changes.append({
                "brand": b["brand"], "title": b["title"], "url": b["url"],
                "now_available": bool(b.get("available")),
                "event": "restocked" if b.get("available") else "went out of stock",
            })
    return {"launches": launches, "removals": removals, "price_changes": price_changes,
            "discount_changes": discount_changes, "stock_changes": stock_changes}


def diff_all(prev_catalogs: dict, curr_catalogs: dict) -> dict:
    """Per-brand diffs across all brands present in the current snapshot."""
    return {brand: diff_brand((prev_catalogs or {}).get(brand, []), products)
            for brand, products in (curr_catalogs or {}).items()}


def benchmark(catalogs: dict, baseline: str = "Deconstruct") -> list:
    """Per-brand catalog snapshot (real from ONE snapshot) — the always-on benchmark."""
    rows = []
    for brand, prods in (catalogs or {}).items():
        real = [p for p in prods if not is_noise(p)]
        prices = [p["price"] for p in real if p.get("price")]
        disc = [p for p in real if p.get("discount_pct", 0) > 0]
        oos = [p for p in prods if not p.get("available")]
        pubs = [p.get("published_at", "") for p in prods if p.get("published_at")]
        rows.append({
            "brand": brand,
            "is_baseline": brand == baseline,
            "products": len(prods),
            "avg_price": round(sum(prices) / len(prices)) if prices else 0,
            "on_discount_%": round(len(disc) / len(real) * 100) if real else 0,
            "avg_discount_%": round(sum(p["discount_pct"] for p in disc) / len(disc), 1) if disc else 0,
            "out_of_stock": len(oos),
            "newest_launch": max(pubs) if pubs else "",
        })
    rows.sort(key=lambda r: (not r["is_baseline"], -r["products"]))
    return rows


def summarize(diffs: dict) -> dict:
    """Roll per-brand diffs into headline counts for the dashboard."""
    rows = []
    for brand, d in diffs.items():
        rows.append({
            "brand": brand,
            "launches": len(d["launches"]),
            "removals": len(d["removals"]),
            "price_moves": len(d["price_changes"]),
            "discount_moves": len(d["discount_changes"]),
            "stock_flips": len(d["stock_changes"]),
        })
    rows.sort(key=lambda r: -(r["launches"] + r["price_moves"] + r["stock_flips"]))
    return {"by_brand": rows,
            "total_launches": sum(r["launches"] for r in rows),
            "total_removals": sum(r["removals"] for r in rows)}
