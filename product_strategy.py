"""
product_strategy.py — AI decision layer for Product Intelligence.

Turns the descriptive per-product data + category analytics into two forward-
looking, market-focused deliverables:

  1. Category "State of Play" — a synthesis of how the category is structured,
     who's winning and why, the biggest gaps, price dynamics, and concrete moves.
  2. Launch / R&D brief — "what Deconstruct should build next": concept, hero
     ingredient, target price (from the real ₹/ml bands), claims and a name.

Both are single Groq calls, GROUNDED in a compact numeric context built from the
scraped facts (Amazon prices, ratings, review volumes, and Amazon's own counted
complaint aspects). No numbers are invented — the AI only synthesises/decides.
"""

from __future__ import annotations

import json

from llm import groq_chat, groq_available
from product_analytics import category_analytics

BASELINE = "Deconstruct"


def build_context(results, keyword):
    """Compact, numeric, grounded summary of the run for the AI to reason over."""
    a = category_analytics(results, brand=BASELINE)
    ps, pm = a.get("price_stats", {}), a.get("per_ml_stats", {})
    L = [f"CATEGORY: {keyword}  |  {a.get('n', len(results))} competitor products analysed on Amazon India"]
    if ps:
        L.append(f"Selling-price band: ₹{ps['min']}–₹{ps['max']} (median ₹{ps['median']}, "
                 f"Q1 ₹{ps['q1']}, Q3 ₹{ps['q3']})")
    if pm:
        L.append(f"₹/ml band: ₹{pm['min']}–₹{pm['max']} (median ₹{pm['median']})")
    if a.get("ratings_avg"):
        L.append(f"Average rating across set: {a['ratings_avg']}/5")
    L.append("Demand leaders (bought/month · price): " + " | ".join(
        f"{d['brand']} (~{d['bought']:,}/mo, ₹{int(d['price']) if d.get('price') else '?'})"
        for d in a.get("demand", [])[:6] if d.get("bought")))
    L.append("Category COMPLAINT signals (Amazon aspect negatives across the full review base): " +
             " | ".join(f"{p['aspect']} {p['negative']} neg/{p['total']}" for p in a.get("pain_points", [])[:8]))
    L.append("Most common CLAIMS: " + ", ".join(f"{c} (×{n})" for c, n in a.get("claim_freq", [])[:10]))
    L.append("Most common ACTIVES: " + ", ".join(f"{i} (×{n})" for i, n in a.get("ingredient_freq", [])[:10]))
    L.append("\nPER-PRODUCT (brand | selling ₹ | rating (reviews) | bought/mo | biggest gap):")
    for r in results[:12]:
        L.append(f"- {r.get('brand', '?')} | ₹{r.get('price_inr', '?')} | "
                 f"★{r.get('rating', '?')} ({r.get('review_count', 0)} rev) | "
                 f"{r.get('bought_last_month', '') or '—'} | {str(r.get('market_gap', ''))[:130]}")
    dec = next((r for r in results if str(r.get("brand", "")).lower() == BASELINE.lower()), None)
    L.append(f"\nDECONSTRUCT in this set: {'yes — ' if dec else 'NOT present in the scanned set'}"
             + (f"₹{dec.get('price_inr')}, ★{dec.get('rating')} ({dec.get('review_count')} rev)" if dec else ""))
    return "\n".join(L), a


def _parse(raw, default):
    try:
        return json.loads(raw[raw.index("{"): raw.rindex("}") + 1])
    except Exception:
        return default


def category_state_of_play(context):
    if not groq_available():
        return {"summary": "Connect Groq for the AI category brief.", "strategic_moves": []}
    prompt = f"""You are the head of category strategy at Deconstruct (science-led Indian D2C skincare).
Below is real Amazon India data for one category. Produce a sharp state-of-play read.

{context}

Return ONLY JSON:
{{"market_structure": "2-3 sentences: price tiers, how brands cluster, breadth of the category",
 "leaders": [{{"brand": "", "why_winning": "why it leads — cite rating/reviews/demand/claims"}}],
 "biggest_gaps": ["3-5 unmet needs / whitespace, grounded in the complaint signals"],
 "price_dynamics": "2 sentences on pricing & ₹/ml dynamics and what it implies",
 "deconstruct_position": "where Deconstruct stands here (or the risk of being absent)",
 "strategic_moves": ["4-6 concrete, prioritised moves for Deconstruct in THIS category"],
 "summary": "3-4 sentence executive read a CEO could act on"}}
Ground every claim in the numbers above. JSON only."""
    return _parse(groq_chat(prompt, system="Output valid JSON only. Start with {.",
                            temperature=0.3, max_tokens=1700),
                  {"summary": "", "strategic_moves": []})


def launch_brief(context):
    if not groq_available():
        return {"concept": "Connect Groq for the launch brief.", "key_claims": []}
    prompt = f"""You are Deconstruct's product-innovation lead. Using the real Amazon India data below,
design the SINGLE best next product Deconstruct should launch in this category — one that attacks the
biggest unmet need (complaint signals) at a smart price, with science-forward, honest positioning.

{context}

Return ONLY JSON:
{{"opportunity": "the specific unmet need it targets — cite the complaint signal + counts",
 "concept": "1-2 sentence product concept",
 "hero_ingredient": "the lead active + % if relevant",
 "format": "gel/serum/cream/lotion/foam/stick",
 "target_skin": "primary skin type/concern",
 "key_claims": ["4-6 title/pack claims to lead with — mix winning category claims + the fix for the top complaint"],
 "target_price_inr": "a specific ₹ number or tight band",
 "price_rationale": "why this price — reference the ₹/ml band and where the gap is",
 "name_ideas": ["2-3 on-brand, science-forward names"],
 "why_now": "the evidence this will work — complaint counts, demand, gap",
 "positioning": "one-line positioning vs the category leaders"}}
Ground the price in the ₹/ml band and the opportunity in the complaint signals. JSON only."""
    return _parse(groq_chat(prompt, system="Output valid JSON only. Start with {.",
                            temperature=0.4, max_tokens=1700),
                  {"concept": "", "key_claims": []})


def strategy_briefs(results, keyword):
    """Compute both AI briefs (2 grounded Groq calls). Returns {} on empty input."""
    if not results:
        return {}
    context, analytics = build_context(results, keyword)
    return {
        "state_of_play": category_state_of_play(context),
        "launch_brief": launch_brief(context),
        "keyword": keyword,
    }
