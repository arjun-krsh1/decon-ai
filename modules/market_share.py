"""
modules/market_share.py — MODULE: Market Share (Digital Shelf Intelligence)

Measures Deconstruct's share of the digital shelf vs competitors across Amazon,
Nykaa, Myntra and Flipkart: share-of-shelf, share-of-search, assortment,
distribution gaps, demand proxies, price tiers, and a keyword analysis of why
the top products rank.

Engine: shelf_scraper.py (Scrapling + SerpAPI) + shelf_intel.py. This module is
just the registry entry; the dashboard block in app.py calls the engine directly.
"""

from modules.base import Module

MODULE = Module(
    key="market_share",
    label="Market Share",
    department="Strategy / Growth",
    tagline="Digital shelf-share, ranking dominance and keyword intelligence across "
            "Amazon, Nykaa, Myntra & Flipkart — benchmarked against Deconstruct.",
    input_fields=[],
    weights={},
    candidates=[],
    score=lambda c, i: (0, {}),
    explain_prompt=lambda c, i, p: "",
    generate_prompt=lambda i, n: "",
    mock_ideas=lambda i, n: [],
    radar=[],
    recommend_noun="shelf gap",
    generate_noun="shelf play",
)
