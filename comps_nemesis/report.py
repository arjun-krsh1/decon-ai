"""
report.py — multi-sheet Excel export for Comp's Nemesis.

Every row carries its public source URL (verifiability). Sheets: Overview,
Benchmark (per-brand), Launches, Price Moves, Discount Moves, Stock Flips,
Full Catalog, and Methodology / Data-Source Transparency.
"""

from __future__ import annotations

import io


def _df(rows):
    import pandas as pd
    return pd.DataFrame(rows) if rows else pd.DataFrame([{"note": "none in this period"}])


def _flatten(diffs: dict, key: str, cols: list) -> list:
    out = []
    for _brand, d in (diffs or {}).items():
        for x in d.get(key, []):
            out.append({c: x.get(c, "") for c in cols})
    return out


def build_excel(curr: dict, diffs: dict, bench: list, prev_date, curr_date) -> bytes:
    import pandas as pd
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xl:
        pd.DataFrame([{
            "Generated": curr_date or "",
            "Compared against": prev_date or "(baseline — no prior snapshot yet)",
            "Brands tracked": len(curr or {}),
            "Total products": sum(len(v) for v in (curr or {}).values()),
            "Baseline": "Deconstruct",
        }]).to_excel(xl, sheet_name="Overview", index=False)

        _df(bench).to_excel(xl, sheet_name="Benchmark", index=False)

        _df(_flatten(diffs, "launches",
                     ["brand", "title", "price", "product_type", "published_at", "url"])
            ).to_excel(xl, sheet_name="Launches", index=False)
        _df(_flatten(diffs, "removals",
                     ["brand", "title", "price", "url"])
            ).to_excel(xl, sheet_name="Removals", index=False)
        _df(_flatten(diffs, "price_changes",
                     ["brand", "title", "old_price", "new_price", "delta_pct", "url"])
            ).to_excel(xl, sheet_name="Price Moves", index=False)
        _df(_flatten(diffs, "discount_changes",
                     ["brand", "title", "old_discount", "new_discount", "url"])
            ).to_excel(xl, sheet_name="Discount Moves", index=False)
        _df(_flatten(diffs, "stock_changes",
                     ["brand", "title", "event", "url"])
            ).to_excel(xl, sheet_name="Stock Flips", index=False)

        catalog = [{"brand": p["brand"], "title": p["title"], "product_type": p["product_type"],
                    "price": p["price"], "mrp": p["mrp"], "discount_%": p["discount_pct"],
                    "available": p["available"], "published_at": p["published_at"], "url": p["url"]}
                   for prods in (curr or {}).values() for p in prods]
        _df(catalog).to_excel(xl, sheet_name="Full Catalog", index=False)

        meth = [
            {"Section": "Source", "Detail": "Each brand's own PUBLIC Shopify storefront JSON "
             "(/products.json) — the same data their website renders. No logins, no grey-hat."},
            {"Section": "Traceability", "Detail": "Every row's 'url' is the public product page — "
             "open it to verify any figure."},
            {"Section": "Launches / Removals", "Detail": "Product handles present in the current "
             "snapshot but not the previous one (or vice-versa)."},
            {"Section": "Price / Discount moves", "Detail": "Same product, changed selling price or "
             "discount depth (compare_at_price vs price) between snapshots."},
            {"Section": "Stock flips", "Detail": "Shopify variant 'available' flag changing between snapshots."},
            {"Section": "Baseline", "Detail": "Deconstruct is the baseline every competitor is measured against."},
            {"Section": "Cadence", "Detail": "A GitHub Action collects a fresh snapshot automatically every 2 days; "
             "comparisons appear from the second snapshot onward."},
            {"Section": "Junk SKUs", "Detail": "₹1 promos / gift cards / testers are flagged out of PRICE "
             "stats but kept for launch detection."},
        ]
        _df(meth).to_excel(xl, sheet_name="Methodology", index=False)
    return buf.getvalue()
