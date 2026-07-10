"""
modules/comps_nemesis.py — MODULE: Comp's Nemesis (competitor intelligence)

Exploits the gap between competitors' own websites and their marketplace listings.
An automatic GitHub Action collects a public-data snapshot every 2 days into Postgres;
this module's dashboard (in app.py) reads that history and surfaces launches, price
moves, discount cadence and stock-outs — all benchmarked against Deconstruct.

Engine: the comps_nemesis/ package (shopify · snapshots · changes · db · report).
This file is just the registry entry.
"""

from modules.base import Module

MODULE = Module(
    key="comps_nemesis",
    label="Comp's Nemesis",
    department="Strategy / Growth",
    tagline="Competitor intelligence from public data — launches, price moves, discounts "
            "and stock-outs across 11 D2C brands, tracked over time vs Deconstruct.",
    input_fields=[],
    weights={},
    candidates=[],
    score=lambda c, i: (0, {}),
    explain_prompt=lambda c, i, p: "",
    generate_prompt=lambda i, n: "",
    mock_ideas=lambda i, n: [],
    radar=[],
    recommend_noun="competitor signal",
    generate_noun="counter-move",
)
