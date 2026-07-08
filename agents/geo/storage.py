"""
storage.py — persist each run so the dashboard can show week-over-week trends.

AI citations are volatile (brief §4), so a single run is a snapshot, not a
verdict. Every run is written to scraper/cache/geo/ with a timestamp, matching
the on-disk cache pattern used elsewhere in Decon (no external DB required).
"""

from __future__ import annotations

import json
import pathlib
from datetime import datetime

STORE = pathlib.Path("scraper/cache/geo")
STORE.mkdir(parents=True, exist_ok=True)


def save_run(output: dict) -> pathlib.Path:
    """Persist one run; returns the file path."""
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    brand = str(output.get("brand", "brand")).lower().replace(" ", "_")
    cat = str(output.get("category", "cat")).lower().replace(" ", "_")
    path = STORE / f"run_{brand}_{cat}_{stamp}.json"
    path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def load_history(brand: str = "", category: str = "") -> list[dict]:
    """Load past runs (newest first), optionally filtered by brand/category."""
    runs = []
    for f in sorted(STORE.glob("run_*.json"), reverse=True):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if brand and data.get("brand", "").lower() != brand.lower():
            continue
        if category and data.get("category", "").lower() != category.lower():
            continue
        runs.append(data)
    return runs
