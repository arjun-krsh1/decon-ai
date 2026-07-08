"""
schemas.py — the typed input/output contract for the Market Visibility (GEO) Agent.

This is the stable interface the Decon orchestrator (and downstream Content /
Social / Listing agents) depend on. Keep it backwards-compatible.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class GeoInput:
    brand: str                       # e.g. "Deconstruct"
    category: str                    # e.g. "Sunscreen"
    competitors: list[str] = field(default_factory=list)
    questions: list[str] = field(default_factory=list)
    models: list[str] = field(default_factory=lambda: ["auto"])

    @classmethod
    def from_dict(cls, d: dict) -> "GeoInput":
        return cls(
            brand=d["brand"],
            category=d.get("category", ""),
            competitors=list(d.get("competitors", [])),
            questions=list(d.get("questions", [])),
            models=list(d.get("models", ["auto"])),
        )


@dataclass
class PerQuestion:
    question: str
    branded: bool
    rankedBrands: list[str]
    position: Optional[int]          # target brand rank (1-based) or None if absent
    sources: list[str]               # cited URLs
    model: str = ""
    answer: str = ""                 # raw answer text (kept for transparency/audit)
    error: str = ""                  # non-empty if this probe failed (run continues)


@dataclass
class BrandCount:
    brand: str
    count: int


@dataclass
class SourceTypePct:
    type: str
    pct: float
    count: int = 0


@dataclass
class DomainCount:
    domain: str
    count: int


@dataclass
class GeoOutput:
    brand: str
    category: str
    shortlistRate: float                     # % top-3 on UNBRANDED discovery questions
    longlistOnly: float                      # % ranked #4+ on unbranded questions
    brandRanking: list[BrandCount]           # who AI recommends most (top-3 hits)
    sourceTypeMix: list[SourceTypePct]       # where to post, ranked by share
    citedDomains: list[DomainCount]
    perQuestion: list[PerQuestion]
    playbook: str                            # number-backed where/what/fix plan
    unbrandedCount: int = 0
    brandedCount: int = 0
    modelsUsed: list[str] = field(default_factory=list)
    generatedAt: str = ""
    deepDive: Optional[dict] = None

    def to_dict(self) -> dict:
        return asdict(self)
