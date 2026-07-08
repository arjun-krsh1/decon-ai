"""
core.py — the GENERIC engine. It knows nothing about freebies or content;
it just orchestrates any Module. Adding a department never touches this file.

Two public functions:
    recommend(module, inputs)  -> ranked existing candidates + reasoning
    innovate(module, inputs)   -> brand-new AI-generated ideas
"""

import json
from llm import ask_llm, llm_available


def _explain(module, candidate, inputs, parts):
    if llm_available():
        text = ask_llm(module.explain_prompt(candidate, inputs, parts))
        if text:
            return text
    # offline template fallback — uses the highest-scoring dimensions
    top = sorted(parts.items(), key=lambda kv: kv[1], reverse=True)[:3]
    return "\n".join(f"- Strong on {k.replace('_', ' ')} ({v}/100)" for k, v in top)


def recommend(module, inputs, top_n=3):
    results = []
    for c in module.candidates:
        total, parts = module.score(c, inputs)
        if total < 0:
            continue
        results.append({
            "name": c["name"],
            "meta": _meta(c),
            "score": total,
            "parts": parts,
            "why": _explain(module, c, inputs, parts),
            "brand": c.get("brand", ""),           # pass brand through
            "condition": c.get("condition", ""),   # pass condition through
        })
    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:top_n]


def innovate(module, inputs, n=3):
    if llm_available():
        text = ask_llm(module.generate_prompt(inputs, n), temperature=0.8)
        try:
            return json.loads(text[text.index("["):text.rindex("]") + 1])[:n]
        except Exception:
            pass
    return module.mock_ideas(inputs, n)


def _meta(candidate):
    """Pick a short detail to show next to a candidate (cost if present)."""
    if "cost" in candidate:
        return f"Cost: Rs{candidate['cost']}"
    return candidate.get("context", "")[:60]