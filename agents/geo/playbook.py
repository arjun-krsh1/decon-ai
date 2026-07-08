"""
playbook.py — turn measured metrics into a number-backed action plan.

Every line carries a number, sourced from either the run's measured data or the
published benchmarks in benchmarks.py (brief §4). Generation is deterministic
(no LLM) so the numbers are always internally consistent and reproducible.

Sections: Verdict → Where to post → What to post → Foundation fixes.
"""

from __future__ import annotations

from . import benchmarks as B
from .schemas import PerQuestion


def _mix_lookup(source_mix) -> dict[str, float]:
    return {s.type: s.pct for s in source_mix}


def generate(analysis: dict, rows: list[PerQuestion], brand: str) -> str:
    sr = analysis["shortlistRate"]
    ll = analysis["longlistOnly"]
    graded = analysis["unbrandedCount"]
    ranking = analysis["brandRanking"]
    mix = _mix_lookup(analysis["sourceTypeMix"])

    lines: list[str] = []

    # ── Verdict ───────────────────────────────────────────────────────────────
    lines.append(f"## Verdict — {brand} in AI answers")
    lines.append(
        f"Across {graded} discovery (unbranded) questions, **{brand} is shortlisted "
        f"(top-3) in {sr}%** of AI answers and appears long-list-only (#4+) in {ll}%."
    )
    top = next((b for b in ranking if b.brand.lower() != brand.lower()), None)
    if top:
        lead = next((b for b in ranking if b.brand.lower() == brand.lower()), None)
        lead_ct = lead.count if lead else 0
        lines.append(
            f"AI recommends **{top.brand}** most often — top-3 in {top.count} of "
            f"{graded} answers vs {brand}'s {lead_ct}. That gap is the target."
        )
    if sr == 0:
        lines.append(
            f"⚠️ {brand} is effectively invisible on discovery questions. "
            f"The fastest lever is the live-retrieval path below, not brand ads."
        )

    # ── Where to post ─────────────────────────────────────────────────────────
    lines.append("\n## Where to post — ranked by measured citation share")
    your = mix.get("Your site", 0.0)
    comp = mix.get("Competitor site", 0.0)
    reddit = mix.get("Reddit", 0.0)
    market = mix.get("Marketplace", 0.0)

    lines.append(
        f"- **Reddit** — {reddit}% of the sources AI cited here, and {B.NOTES['reddit']} "
        f"Priority 1: earn genuine, rules-respecting Reddit presence on these questions."
    )
    lines.append(
        f"- **Marketplaces (Nykaa/Amazon/etc.)** — {market}% of cited sources here. "
        f"Ensure listings + structured data are complete; {B.NOTES['structured']}"
    )
    lines.append(
        f"- **Your own site** — cited {your}% vs competitors' {comp}%. "
        + ("Competitors' pages are being pulled far more — close this with retrieval-ready pages."
           if comp > your else
           "Keep expanding retrieval-ready pages to hold this lead.")
    )
    lines.append(f"- **Wikipedia / structured data** — {B.NOTES['wikipedia']} {B.NOTES['top15']}")

    # ── What to post ──────────────────────────────────────────────────────────
    absent = [r for r in rows
              if not r.branded and not r.error and (r.position is None or r.position > 3)]
    lines.append("\n## What to post — questions where you're absent or buried")
    if absent:
        for r in absent[:8]:
            where = "absent" if r.position is None else f"ranked #{r.position}"
            lines.append(f"- \"{r.question}\" — currently {where}. "
                         f"Publish a focused, evidence-dense answer page + seed a genuine community thread.")
    else:
        lines.append("- You're shortlisted on every measured discovery question. "
                     "Shift to defending share and widening the question set.")

    # ── Foundation fixes ──────────────────────────────────────────────────────
    lines.append("\n## Foundation fixes — make every page retrieval-ready")
    lines.append(f"- Structure pages as self-contained {B.CHUNK_MIN_WORDS}–{B.CHUNK_MAX_WORDS} "
                 f"word answer blocks — {B.NOTES['chunks']}")
    lines.append(f"- Add hard numbers to claims — {B.NOTES['statistics']}")
    lines.append(f"- Add expert/derm direct quotations — {B.NOTES['quotations']}")
    lines.append(f"- Publish/maintain a Wikidata entry and consistent structured data — "
                 f"{B.NOTES['structured']}")

    return "\n".join(lines)
