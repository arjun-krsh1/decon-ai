"""
CLI for the GEO Agent — run a live analysis from the terminal, no UI.

    python -m agents.geo --brand Deconstruct --category Sunscreen \
        --competitors "Minimalist,Dot & Key,The Derma Co,Foxtale,Aqualogica" \
        --models auto

Prints the playbook and writes the full contract JSON to scraper/cache/geo/.
"""

from __future__ import annotations

import sys
import json
import argparse
import pathlib

# Windows terminals default to cp1252; force UTF-8 so em-dashes/emoji print.
for _stream in (sys.stdout, sys.stderr):
    _reconfigure = getattr(_stream, "reconfigure", None)
    if _reconfigure:
        try:
            _reconfigure(encoding="utf-8")
        except Exception:
            pass

# allow `python -m agents.geo` from the project root
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from dotenv import load_dotenv  # noqa: E402
load_dotenv()

from agents.geo import run, GeoInput  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Decon Market Visibility (GEO) Agent")
    ap.add_argument("--brand", default="Deconstruct")
    ap.add_argument("--category", default="Sunscreen")
    ap.add_argument("--competitors",
                    default="Minimalist,Dot & Key,The Derma Co,Foxtale,Aqualogica,Dr. Sheth's")
    ap.add_argument("--models", default="auto",
                    help="comma list: auto | gemini | serpgroq | mock")
    ap.add_argument("--json", action="store_true", help="print full JSON contract")
    args = ap.parse_args()

    gi = GeoInput(
        brand=args.brand,
        category=args.category,
        competitors=[c.strip() for c in args.competitors.split(",") if c.strip()],
        models=[m.strip() for m in args.models.split(",") if m.strip()],
    )

    def progress(done, total, msg):
        print(f"  ({done}/{total}) {msg}", file=sys.stderr)

    out = run(gi, progress_cb=progress)

    print(f"\n{'='*64}")
    print(f"  {out.brand} — {out.category}   |  models: {', '.join(out.modelsUsed)}")
    print(f"  Shortlist rate (top-3, unbranded): {out.shortlistRate}%  "
          f"| long-list only: {out.longlistOnly}%")
    print(f"  Discovery questions graded: {out.unbrandedCount}  "
          f"(branded excluded: {out.brandedCount})")
    print(f"{'='*64}\n")
    print(out.playbook)

    if args.json:
        print("\n--- JSON ---")
        print(json.dumps(out.to_dict(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
