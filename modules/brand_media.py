"""
modules/brand_media.py — MODULE #6: Brand Media Analyser

Weekly social media competitive intelligence.
Compares 5 competitors against Deconstruct as baseline.
Sources: SerpAPI Google search + Playwright for full captions.
Output: Excel + Dashboard
"""

from modules.base import Module, clamp, weighted_total

WEIGHTS = {
    "content_volume":    0.20,
    "claim_diversity":   0.25,
    "engagement_signal": 0.20,
    "concern_coverage":  0.20,
    "format_variety":    0.15,
}

# Fixed 6 brands — Deconstruct is always the baseline
BRANDS = [
    {"name": "Deconstruct",     "handle": "deconstruct_skincare",  "search": "deconstruct skincare",  "is_baseline": True},
    {"name": "Minimalist",      "handle": "minimalist.india",       "search": "minimalist skincare",   "is_baseline": False},
    {"name": "Foxtale",         "handle": "foxtalecare",            "search": "foxtale skincare",      "is_baseline": False},
    {"name": "The Derma Co",    "handle": "thedermacompany",        "search": "derma co skincare",     "is_baseline": False},
    {"name": "Re'equil",        "handle": "reequil",                "search": "reequil skincare",      "is_baseline": False},
    {"name": "Dot & Key",       "handle": "dotandkey.care",         "search": "dot and key skincare",  "is_baseline": False},
]

MODULE = Module(
    key="brand_media",
    label="Brand Media Analyser",
    department="Marketing / Brand",
    tagline="Weekly social media competitor intelligence — all insights benchmarked against Deconstruct.",
    input_fields=[],
    weights=WEIGHTS,
    candidates=[],
    score=lambda c, i: (0, {}),
    explain_prompt=lambda c, i, p: "",
    generate_prompt=lambda i, n: "",
    mock_ideas=lambda i, n: [],
    radar=[],
    recommend_noun="insight",
    generate_noun="opportunity",
)