"""
Market Visibility (GEO) Agent — measures how visible a brand is inside AI
answers, diagnoses why, and produces a number-backed content playbook.

Public API:
    from agents.geo import run, GeoInput, GeoOutput
"""

from .schemas import GeoInput, GeoOutput
from .agent import run

__all__ = ["run", "GeoInput", "GeoOutput"]
