"""
db.py — Postgres storage for Comp's Nemesis (Supabase / Neon / any Postgres).

The scheduled GitHub Action writes a dated snapshot (one row per product per brand);
the Streamlit app only reads. Rows use the SAME normalized shape as shopify.py, so
changes.py diffing is reused unchanged. Connection via the DATABASE_URL env var.
Uses psycopg (v3); SQL is passed as literals (psycopg3 requirement).
"""

from __future__ import annotations

import os
import datetime as _dt

_COLS = ["brand", "handle", "url", "title", "product_type", "price", "mrp",
         "discount_pct", "available", "variants", "published_at"]


def _conn():
    import psycopg
    url = os.getenv("DATABASE_URL", "")
    if not url:
        raise RuntimeError("DATABASE_URL not set")
    return psycopg.connect(url)


def _ensure(cur):
    """Create the table + indexes if absent (one literal statement per execute)."""
    cur.execute("""CREATE TABLE IF NOT EXISTS comps_snapshots (
        snapshot_date date    NOT NULL,
        brand         text    NOT NULL,
        handle        text    NOT NULL,
        url           text,
        title         text,
        product_type  text,
        price         numeric,
        mrp           numeric,
        discount_pct  numeric,
        available     boolean,
        variants      integer,
        published_at  text,
        collected_at  timestamptz DEFAULT now(),
        PRIMARY KEY (snapshot_date, brand, handle)
    )""")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_comps_date ON comps_snapshots (snapshot_date)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_comps_brand ON comps_snapshots (brand)")


def init_schema():
    with _conn() as c, c.cursor() as cur:
        _ensure(cur)
        c.commit()


def write_snapshot(catalogs: dict, date: str | None = None):
    """Insert one snapshot (idempotent: replaces any existing rows for that date)."""
    date = date or _dt.date.today().isoformat()
    rows = [(date, b, p.get("handle", ""), p.get("url", ""), p.get("title", ""),
             p.get("product_type", ""), p.get("price", 0), p.get("mrp", 0),
             p.get("discount_pct", 0), bool(p.get("available")), p.get("variants", 0),
             p.get("published_at", ""))
            for b, prods in catalogs.items() for p in prods]
    with _conn() as c, c.cursor() as cur:
        _ensure(cur)
        cur.execute("DELETE FROM comps_snapshots WHERE snapshot_date = %s", (date,))
        if rows:
            cur.executemany(
                "INSERT INTO comps_snapshots "
                "(snapshot_date,brand,handle,url,title,product_type,price,mrp,"
                "discount_pct,available,variants,published_at)"
                " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", rows)
        c.commit()
    return date, len(rows)


def list_dates() -> list:
    with _conn() as c, c.cursor() as cur:
        cur.execute("SELECT DISTINCT snapshot_date FROM comps_snapshots ORDER BY snapshot_date")
        return [r[0].isoformat() for r in cur.fetchall()]


def load_snapshot(date: str) -> dict:
    """Return {brand: [normalized product dicts]} for a snapshot date."""
    with _conn() as c, c.cursor() as cur:
        cur.execute(
            "SELECT brand,handle,url,title,product_type,price,mrp,discount_pct,"
            "available,variants,published_at FROM comps_snapshots WHERE snapshot_date = %s",
            (date,))
        out = {}
        for row in cur.fetchall():
            d = dict(zip(_COLS, row))
            d["price"] = float(d["price"] or 0)
            d["mrp"] = float(d["mrp"] or 0)
            d["discount_pct"] = float(d["discount_pct"] or 0)
            d["available"] = bool(d["available"])
            out.setdefault(d["brand"], []).append(d)
        return out


def latest_two():
    """((prev_date, prev_catalogs)|(None,None), (curr_date, curr_catalogs)|(None,None))."""
    ds = list_dates()
    if not ds:
        return (None, None), (None, None)
    curr = (ds[-1], load_snapshot(ds[-1]))
    prev = (ds[-2], load_snapshot(ds[-2])) if len(ds) >= 2 else (None, None)
    return prev, curr


def has_data() -> bool:
    try:
        return bool(list_dates())
    except Exception:
        return False
