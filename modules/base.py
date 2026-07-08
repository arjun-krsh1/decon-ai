"""
modules/base.py — defines what a "module" (department vertical) IS.

A Module is the ONLY thing that changes between departments. The engine in
core.py is generic and never needs editing when you add a new department —
you just write a new module file (see content.py / design.py) and register
it in modules/__init__.py.

This is the heart of the "platform, not a single tool" architecture.
"""

from dataclasses import dataclass
from typing import Callable, List, Dict, Any


@dataclass
class Module:
    key: str                 # short id, e.g. "content"
    label: str               # display name, e.g. "Content & Social Intelligence"
    department: str          # which team owns it, e.g. "Content / Social"
    tagline: str             # one-line description shown in the UI

    input_fields: List[Dict] # describes the UI inputs (see content.py for shape)
    weights: Dict[str, float]# scoring dimension -> weight (should sum to 1.0)
    candidates: List[Dict]   # the records this module ranks

    score: Callable          # (candidate, inputs) -> (total:int, parts:dict)
    explain_prompt: Callable # (candidate, inputs, parts) -> str  (LLM prompt)
    generate_prompt: Callable# (inputs, n) -> str                 (LLM prompt)
    mock_ideas: Callable     # (inputs, n) -> List[Dict]  (offline fallback ideas)
    radar: List[Dict]        # market-radar rows for this department

    recommend_noun: str = "recommendation"
    generate_noun: str = "idea"


# ---- shared scoring helpers any module can use --------------------------
def clamp(x, lo=0, hi=100):
    return max(lo, min(hi, x))


def weighted_total(parts: Dict[str, float], weights: Dict[str, float]) -> int:
    return round(sum(parts[k] * weights[k] for k in weights))
