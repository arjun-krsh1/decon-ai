"""
modules/product_intel.py — MODULE #5: Product Intelligence (Product Team)

Amazon competitor product analyser.
Input: keyword or URL → Output: ranked Excel + dashboard
"""

from modules.base import Module, clamp, weighted_total

WEIGHTS = {
    "rating_score":    0.25,
    "review_volume":   0.20,
    "price_value":     0.20,
    "claim_strength":  0.20,
    "rank_position":   0.15,
}

MODULE = Module(
    key="product_intel",
    label="Product Intelligence",
    department="Product Team",
    tagline="Amazon competitor analysis — ratings, reviews, claims, rankings. Excel + dashboard output.",
    input_fields=[],
    weights=WEIGHTS,
    candidates=[],
    score=lambda c, i: (0, {}),
    explain_prompt=lambda c, i, p: "",
    generate_prompt=lambda i, n: "",
    mock_ideas=lambda i, n: [],
    radar=[],
    recommend_noun="product",
    generate_noun="insight",
)