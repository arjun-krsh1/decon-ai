"""
extract.py — turn a free-text AI answer into structured data.

Output per answer: the ranked list of tracked brands the model recommended,
and the target brand's position (or None).

Two correctness rules from the brief drive the design:
  * "Deconstruct" is also an ordinary English word — the verb/adjective must
    NEVER be counted as a brand mention.
  * Only brands actually recommended count, in the order recommended.

Primary path is an LLM call returning strict JSON (retried once). If the LLM is
unavailable or returns junk, a deterministic name-scan fallback keeps the run
alive (lower fidelity, flagged by the caller).
"""

from __future__ import annotations

import re
import json

from llm import groq_chat, groq_available

_SKINCARE_CONTEXT = re.compile(
    r"(skincare|serum|sunscreen|spf|moisturi|cleanser|brand|\.co|\.in|®|™)",
    re.IGNORECASE,
)


def _known_brands(brand: str, competitors: list[str]) -> list[str]:
    seen, out = set(), []
    for b in [brand, *competitors]:
        key = b.strip().lower()
        if b.strip() and key not in seen:
            seen.add(key)
            out.append(b.strip())
    return out


def _parse_json_object(text: str) -> dict | None:
    if not text:
        return None
    try:
        return json.loads(text[text.index("{"): text.rindex("}") + 1])
    except Exception:
        return None


def _llm_extract(answer: str, brand: str, brands: list[str]) -> dict | None:
    prompt = f"""You are extracting structured data from a shopping assistant's answer.

TRACKED BRANDS (use these exact spellings): {", ".join(brands)}

ANSWER TO ANALYSE:
\"\"\"{answer[:3000]}\"\"\"

Task:
1. List, IN ORDER, only the tracked brands that are RECOMMENDED as products in this answer.
2. Report the position (1-based rank) of "{brand}" in that list, or null if absent.

CRITICAL: "{brand}" may also be an ordinary English word. Count it ONLY when it
clearly refers to the skincare brand being recommended — never when used as a
normal verb or adjective.

Return ONLY this JSON, nothing else:
{{"rankedBrands": ["Brand A", "Brand B"], "position": 1}}
Start with {{"""
    for _ in range(2):  # one retry on malformed output
        raw = groq_chat(prompt, system="Output valid JSON only. Start with {.",
                        temperature=0.0, max_tokens=400)
        data = _parse_json_object(raw)
        if isinstance(data, dict) and "rankedBrands" in data:
            return data
    return None


def _fallback_scan(answer: str, brand: str, brands: list[str]) -> dict:
    """Deterministic order-of-appearance scan when the LLM path is unavailable."""
    hits = []  # (index, canonical_name)
    for b in brands:
        pattern = re.compile(rf"\b{re.escape(b)}\b", re.IGNORECASE)
        m = pattern.search(answer)
        if not m:
            continue
        # "Deconstruct"-as-word guard: require capitalised form near skincare context
        if b.strip().lower() == "deconstruct":
            proper = re.search(r"\bDeconstruct\b", answer)
            if not proper:
                continue
            window = answer[max(0, proper.start() - 40): proper.end() + 40]
            if not _SKINCARE_CONTEXT.search(window):
                continue
            hits.append((proper.start(), b))
        else:
            hits.append((m.start(), b))

    hits.sort(key=lambda x: x[0])
    ranked = [name for _, name in hits]
    position = next((i + 1 for i, n in enumerate(ranked)
                     if n.strip().lower() == brand.strip().lower()), None)
    return {"rankedBrands": ranked, "position": position}


def _dedupe(names: list[str]) -> list[str]:
    """Drop repeats (case-insensitive) while preserving recommendation order."""
    seen, out = set(), []
    for n in names:
        key = n.strip().lower()
        if key and key not in seen:
            seen.add(key)
            out.append(n.strip())
    return out


def extract(answer: str, brand: str, competitors: list[str]) -> tuple[dict, bool]:
    """
    Returns ({"rankedBrands": [...], "position": int|None}, used_llm: bool).
    `used_llm` lets the caller flag lower-confidence fallback rows.

    Position is always recomputed from the de-duplicated ranked list, so it stays
    consistent regardless of what the model reported.
    """
    brands = _known_brands(brand, competitors)
    if not answer.strip():
        return {"rankedBrands": [], "position": None}, False

    used_llm = False
    ranked: list[str] = []
    if groq_available():
        data = _llm_extract(answer, brand, brands)
        if data is not None:
            ranked = [b for b in data.get("rankedBrands", []) if isinstance(b, str)]
            used_llm = True
    if not used_llm:
        ranked = _fallback_scan(answer, brand, brands)["rankedBrands"]

    ranked = _dedupe(ranked)
    position = next((i + 1 for i, n in enumerate(ranked)
                     if n.lower() == brand.strip().lower()), None)
    return {"rankedBrands": ranked, "position": position}, used_llm
