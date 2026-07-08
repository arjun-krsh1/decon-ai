"""
product_analytics.py — pure-Python analytics for the Product Intelligence tool.

No network calls here — just deterministic maths over already-fetched data, so
every number is reproducible and testable:
  * pack-size parsing + ₹/ml normalisation (real cross-product price comparison)
  * star distribution from sampled reviews
  * rating-over-time + review velocity reconstructed from review dates
    (this is our free "historical" view — Amazon exposes no price history)

Category-level analytics (price bands, whitespace, comparison) build on top of
these in a later phase.
"""

from __future__ import annotations

import re
import statistics
from collections import Counter, defaultdict

# ── pack size / price-per-unit ────────────────────────────────────────────────
# grams ≈ millilitres for skincare, so we normalise everything to "ml-equivalent".
_SIZE_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(ml|ml\.|millilitre|milliliter|l|litre|liter|g|gm|gram|grams|kg)\b",
    re.IGNORECASE,
)
_UNIT_TO_ML = {"ml": 1, "l": 1000, "litre": 1000, "liter": 1000,
               "g": 1, "gm": 1, "gram": 1, "grams": 1, "kg": 1000}


def parse_pack_size(*texts) -> float | None:
    """
    Extract a pack size in ml-equivalent from any of the given text fields
    (title, bullets, details). Returns the largest plausible match, or None.
    """
    best = None
    for text in texts:
        if not text:
            continue
        for m in _SIZE_RE.finditer(str(text)):
            val = float(m.group(1))
            unit = m.group(2).lower().rstrip(".")
            unit = {"millilitre": "ml", "milliliter": "ml"}.get(unit, unit)
            ml = val * _UNIT_TO_ML.get(unit, 1)
            if 3 <= ml <= 5000:  # ignore junk like "SPF 50" or "2024"
                best = max(best or 0, ml)
    return best


def price_per_ml(price, size_ml) -> float | None:
    try:
        price = float(price)
        size_ml = float(size_ml)
        if price > 0 and size_ml > 0:
            return round(price / size_ml, 2)
    except (TypeError, ValueError):
        pass
    return None


# ── review-derived signals ────────────────────────────────────────────────────
def _star_of(review) -> int | None:
    """Best-effort integer star (1-5) from a review dict."""
    raw = review.get("stars", review.get("rating", ""))
    m = re.search(r"([1-5])(?:\.\d+)?", str(raw))
    return int(m.group(1)) if m else None


def star_distribution(reviews) -> dict:
    """Count of 1-5 star reviews across the sampled set (+ percentages)."""
    counts = Counter()
    for r in reviews:
        s = _star_of(r)
        if s:
            counts[s] += 1
    total = sum(counts.values())
    dist = {str(s): counts.get(s, 0) for s in range(5, 0, -1)}
    pct = {str(s): (round(100 * counts.get(s, 0) / total, 1) if total else 0.0)
           for s in range(5, 0, -1)}
    return {"counts": dist, "pct": pct, "sampled": total}


def _parse_date(text):
    """Parse an Amazon/SerpAPI review date string into a date, or None."""
    if not text:
        return None
    # strip "Reviewed in <country> on " prefix if present
    cleaned = re.sub(r"^.*?on\s+", "", str(text)).strip()
    # ISO (YYYY-MM-DD) first — dayfirst would misread it
    iso = re.match(r"(\d{4}-\d{2}-\d{2})", cleaned)
    if iso:
        try:
            from datetime import date as _d
            return _d.fromisoformat(iso.group(1))
        except Exception:
            pass
    try:
        from dateutil import parser as _dp
        return _dp.parse(cleaned, fuzzy=True, dayfirst=True).date()
    except Exception:
        m = re.search(r"(20\d{2})", str(text))  # last-ditch: just the year
        if m:
            try:
                from datetime import date
                return date(int(m.group(1)), 1, 1)
            except Exception:
                return None
    return None


def review_timeline(reviews) -> dict:
    """
    Rating-over-time and review velocity reconstructed from review dates.
    Returns {"monthly": [{"month":"YYYY-MM","avg":x,"count":n}], "velocity_per_month": v}.
    This is the free stand-in for Amazon's missing price/rating history.
    """
    buckets_sum = defaultdict(float)
    buckets_cnt = defaultdict(int)
    for r in reviews:
        d = _parse_date(r.get("date", ""))
        s = _star_of(r)
        if d and s:
            key = f"{d.year:04d}-{d.month:02d}"
            buckets_sum[key] += s
            buckets_cnt[key] += 1

    monthly = [
        {"month": k, "avg": round(buckets_sum[k] / buckets_cnt[k], 2), "count": buckets_cnt[k]}
        for k in sorted(buckets_cnt)
    ]
    velocity = round(sum(buckets_cnt.values()) / len(buckets_cnt), 1) if buckets_cnt else 0.0
    return {"monthly": monthly, "velocity_per_month": velocity}


# ── category-level analytics (one call over all analysed products) ────────────
def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def parse_bought(text) -> int:
    """'3K+ bought in past month' -> 3000 ; '500+ bought' -> 500 ; '' -> 0."""
    if not text:
        return 0
    m = re.search(r"([\d.,]+)\s*([kKmM]?)", str(text))
    if not m:
        return 0
    try:
        num = float(m.group(1).replace(",", ""))
    except ValueError:
        return 0
    mult = {"k": 1_000, "m": 1_000_000}.get(m.group(2).lower(), 1)
    return int(num * mult)


def _stats(vals) -> dict:
    vals = [v for v in vals if isinstance(v, (int, float)) and v > 0]
    if not vals:
        return {}
    q = statistics.quantiles(vals, n=4) if len(vals) >= 2 else [min(vals), statistics.median(vals), max(vals)]
    return {"min": round(min(vals)), "q1": round(q[0]), "median": round(statistics.median(vals)),
            "q3": round(q[2]), "max": round(max(vals)), "count": len(vals)}


def category_analytics(products, brand="Deconstruct") -> dict:
    """Aggregate a run's products into category-level intelligence."""
    ps = products or []

    price_stats = _stats([_num(p.get("price_inr")) for p in ps])
    per_ml_stats = _stats([p.get("price_per_ml") for p in ps
                           if isinstance(p.get("price_per_ml"), (int, float))])
    ratings = [_num(p.get("rating")) for p in ps]
    ratings = [r for r in ratings if r]

    claim_freq, ing_freq = Counter(), Counter()
    for p in ps:
        for c in (p.get("top_claims") or []):
            claim_freq[str(c).strip()[:60]] += 1
        for a in (p.get("key_actives") or []):
            ing_freq[str(a).strip()] += 1

    # cross-product aspect rollup (from Amazon's counted insights)
    agg = defaultdict(lambda: {"total": 0, "positive": 0, "negative": 0, "products": 0})
    for p in ps:
        for a in (p.get("amazon_aspects") or []):
            k = str(a.get("aspect", "")).strip()
            if not k:
                continue
            agg[k]["total"] += int(a.get("total", 0) or 0)
            agg[k]["positive"] += int(a.get("positive", 0) or 0)
            agg[k]["negative"] += int(a.get("negative", 0) or 0)
            agg[k]["products"] += 1
    aspects = []
    for k, v in agg.items():
        ratio = round(100 * v["positive"] / v["total"], 1) if v["total"] else 0.0
        aspects.append({"aspect": k, **v, "positive_ratio": ratio})
    aspects.sort(key=lambda a: a["total"], reverse=True)
    pain_points = sorted([a for a in aspects if int(a["negative"]) > 0],
                         key=lambda a: int(a["negative"]), reverse=True)[:6]

    demand = sorted(
        [{"brand": p.get("brand", ""), "product": p.get("product_name", ""),
          "bought": parse_bought(p.get("bought_last_month", "")),
          "price": _num(p.get("price_inr"))} for p in ps],
        key=lambda d: d["bought"], reverse=True)

    baseline = next((p for p in ps if str(p.get("brand", "")).strip().lower() == brand.lower()), None)

    return {
        "n": len(ps),
        "price_stats": price_stats,
        "per_ml_stats": per_ml_stats,
        "ratings_avg": round(statistics.mean(ratings), 2) if ratings else None,
        "claim_freq": claim_freq.most_common(12),
        "ingredient_freq": ing_freq.most_common(12),
        "aspects": aspects[:12],
        "pain_points": pain_points,
        "demand": demand,
        "baseline_present": baseline is not None,
        "baseline_brand": brand,
    }


def opportunity_cards(analytics: dict) -> list[dict]:
    """Turn analytics into ranked, number-backed launch/positioning opportunities."""
    cards = []
    for pp in analytics.get("pain_points", [])[:4]:
        cards.append({
            "type": "Beat a category weakness",
            "title": f"Own '{pp['aspect']}' — competitors are failing here",
            "detail": (f"{pp['negative']} negative mentions across {pp['products']} products flag "
                       f"{pp['aspect'].lower()}. A product that genuinely fixes this can win switchers."),
        })
    st = analytics.get("price_stats", {})
    if st:
        cards.append({
            "type": "Pricing whitespace",
            "title": f"Median competitor price is ₹{st.get('median')}",
            "detail": (f"Field spans ₹{st.get('min')}–₹{st.get('max')} (Q1 ₹{st.get('q1')}, "
                       f"Q3 ₹{st.get('q3')}, n={st.get('count')}). Position price deliberately vs this spread."),
        })
    pm = analytics.get("per_ml_stats", {})
    if pm:
        cards.append({
            "type": "Value (₹/ml) angle",
            "title": f"Category median is ₹{pm.get('median')}/ml",
            "detail": (f"₹/ml ranges ₹{pm.get('min')}–₹{pm.get('max')}. Undercutting on true unit price "
                       f"(not sticker price) is a defensible value claim."),
        })
    return cards
