"""
snapshots.py — collect + store dated catalog snapshots for Comp's Nemesis.

A snapshot = every tracked brand's full normalized catalog on a given date.
Storage is behind a tiny interface so it can swap from local JSON (now) to a
Postgres DB (Supabase/Neon) later without touching the feature code.

The collector (collect_all) is what the scheduled GitHub Action — or the in-app
"Collect snapshot now" button — runs. The app only ever READS stored snapshots.
"""

from __future__ import annotations

import json
import pathlib
import datetime as _dt

from . import brands
from .shopify import fetch_products

# Local store (git-ignored). The DB upgrade replaces this layer only.
DATA = pathlib.Path("scraper/cache/comps_snapshots")
DATA.mkdir(parents=True, exist_ok=True)


def collect_all(progress_cb=None) -> dict:
    """Fetch every tracked brand's catalog. Returns {brand: [normalized products]}."""
    out = {}
    items = list(brands.BRANDS.items())
    for i, (brand, dom) in enumerate(items, 1):
        if progress_cb:
            progress_cb(i, len(items), brand)
        try:
            out[brand] = fetch_products(brand, dom)
        except Exception as e:
            print(f"[comps] {brand} failed: {e}")
            out[brand] = []
    return out


def save_snapshot(catalogs: dict, date: str | None = None) -> str:
    """Persist a snapshot under its date (YYYY-MM-DD). Returns the date key."""
    date = date or _dt.date.today().isoformat()
    payload = {"date": date, "catalogs": catalogs,
               "counts": {b: len(v) for b, v in catalogs.items()}}
    (DATA / f"{date}.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return date


def list_dates() -> list:
    return sorted(p.stem for p in DATA.glob("*.json"))


def load_snapshot(date: str) -> dict:
    p = DATA / f"{date}.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8")).get("catalogs", {})


def latest_two():
    """((prev_date, prev_catalogs) | (None, None), (curr_date, curr_catalogs))."""
    ds = list_dates()
    if not ds:
        return (None, None), (None, None)
    curr = (ds[-1], load_snapshot(ds[-1]))
    prev = (ds[-2], load_snapshot(ds[-2])) if len(ds) >= 2 else (None, None)
    return prev, curr
