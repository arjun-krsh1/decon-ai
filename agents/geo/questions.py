"""
questions.py — buyer question sets used to probe AI engines.

Discovery (UNBRANDED) questions are the ones that count toward the headline
shortlist rate — they mimic a shopper who doesn't yet know which brand to buy.
Branded questions are included for context but excluded from the score (§4).

`{cat}` is filled with the category (lower-cased). Extra branded questions are
generated from the brand + competitor names so the branded/unbranded split is
always populated even for a new category.
"""

from __future__ import annotations

# Category-agnostic discovery questions — an Indian shopper asking an AI assistant.
_UNBRANDED_TEMPLATES = [
    "best {cat} for oily skin in India under 500 rupees",
    "best {cat} for dry sensitive skin in India",
    "which {cat} do dermatologists recommend in India",
    "top {cat} brands in India 2025",
    "affordable {cat} that actually works for Indian skin",
    "best {cat} for acne-prone skin India",
    "fragrance-free {cat} for sensitive skin India",
    "best {cat} for combination skin in humid weather India",
    "most recommended {cat} on Reddit India",
    "best budget {cat} for men in India",
]

_BRANDED_TEMPLATES = [
    "is {brand} {cat} any good",
    "{brand} vs {competitor} {cat} which is better",
]


def build_questions(brand: str, category: str, competitors: list[str],
                    n_unbranded: int = 8, n_branded: int = 2) -> list[str]:
    """Return a mixed list of discovery + branded questions for a category."""
    cat = (category or "product").strip().lower()
    qs = [t.format(cat=cat) for t in _UNBRANDED_TEMPLATES[:n_unbranded]]

    competitor = competitors[0] if competitors else "a competitor"
    branded = [t.format(brand=brand, cat=cat, competitor=competitor)
               for t in _BRANDED_TEMPLATES[:n_branded]]
    return qs + branded
