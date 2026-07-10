"""
collect.py — the automatic collector for Comp's Nemesis.

Run by the GitHub Action every 2 days (and manually via "Run workflow" if needed).
Fetches every tracked brand's public Shopify catalog and writes one dated snapshot
to Postgres. The team never runs this — it's fully automated. The app only reads.

Needs env var DATABASE_URL (Postgres). SCRAPER_API_KEY is optional (proxy fallback).
"""

import sys

from comps_nemesis import snapshots, db


def _progress(i, n, brand):
    print(f"  [{i}/{n}] {brand}", flush=True)


def main():
    print("Comp's Nemesis — collecting snapshot…", flush=True)
    db.init_schema()
    catalogs = snapshots.collect_all(progress_cb=_progress)
    date, rows = db.write_snapshot(catalogs)
    counts = ", ".join(f"{b}:{len(v)}" for b, v in catalogs.items())
    print(f"\n✓ snapshot {date} written — {rows} product rows across {len(catalogs)} brands")
    print(f"  {counts}", flush=True)
    if rows == 0:
        print("!! no rows collected", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
