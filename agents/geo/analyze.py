"""
analyze.py — aggregate per-question probe results into the headline metrics.

Key methodology rules (brief §4):
  * The headline shortlist rate uses UNBRANDED discovery questions only.
  * Position 1–3 = shortlisted; 4+ = long-list only (functionally invisible).
  * Errored probes are excluded from rate denominators (they were never observed).
  * Source-type mix is measured on discovery answers — that's the "where to post" list.
"""

from __future__ import annotations

import re
from collections import Counter

from .schemas import PerQuestion, BrandCount, SourceTypePct, DomainCount
from .taxonomy import classify, domain_of


def is_branded(question: str, brands: list[str]) -> bool:
    """A question is 'branded' if it names any tracked brand."""
    for b in brands:
        if re.search(rf"\b{re.escape(b)}\b", question, re.IGNORECASE):
            return True
    return False


def _pct(part: int, whole: int) -> float:
    return round(100 * part / whole, 1) if whole else 0.0


def analyze(rows: list[PerQuestion], brand: str, competitors: list[str]) -> dict:
    unbranded = [r for r in rows if not r.branded and not r.error]
    graded = len(unbranded)

    shortlisted = sum(1 for r in unbranded if r.position and r.position <= 3)
    longlist = sum(1 for r in unbranded if r.position and r.position >= 4)

    # who AI recommends most — top-3 appearances across discovery answers
    top3 = Counter()
    for r in unbranded:
        for b in r.rankedBrands[:3]:
            top3[b] += 1
    brand_ranking = [BrandCount(b, c) for b, c in top3.most_common()]

    # source-type mix + cited domains, measured on discovery answers
    type_counter: Counter = Counter()
    domain_counter: Counter = Counter()
    for r in unbranded:
        for src in r.sources:
            type_counter[classify(src, brand, competitors)] += 1
            dom = domain_of(src) or src
            if dom:
                domain_counter[dom] += 1

    total_src = sum(type_counter.values())
    source_mix = [SourceTypePct(t, _pct(c, total_src), c)
                  for t, c in type_counter.most_common()]
    cited_domains = [DomainCount(d, c) for d, c in domain_counter.most_common(20)]

    return {
        "shortlistRate": _pct(shortlisted, graded),
        "longlistOnly": _pct(longlist, graded),
        "brandRanking": brand_ranking,
        "sourceTypeMix": source_mix,
        "citedDomains": cited_domains,
        "unbrandedCount": graded,
        "brandedCount": sum(1 for r in rows if r.branded),
    }
