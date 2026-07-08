"""
modules/geo.py — MODULE: Market Visibility (GEO Agent)

Measures how visible Deconstruct is inside AI-assistant answers (ChatGPT / Gemini
/ Perplexity), diagnoses why, and produces a number-backed content playbook.

The engine lives in agents/geo/ (framework-agnostic, independently runnable). This
module is just the registry entry + metadata for the Streamlit shell; the
dashboard block in app.py calls agents.geo.run() directly.
"""

from modules.base import Module

MODULE = Module(
    key="geo",
    label="Market Content Visibility",
    department="Marketing / Growth",
    tagline="Measure how often AI assistants recommend Deconstruct — and get a "
            "number-backed plan to fix it.",
    input_fields=[],
    weights={},
    candidates=[],
    score=lambda c, i: (0, {}),
    explain_prompt=lambda c, i, p: "",
    generate_prompt=lambda i, n: "",
    mock_ideas=lambda i, n: [],
    radar=[],
    recommend_noun="visibility gap",
    generate_noun="content play",
)
