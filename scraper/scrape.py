"""
scraper/scrape.py — scrapes India's top 10 skincare D2C brands for
freebie/offer intelligence, then uses AI to extract structured data.

HOW IT WORKS
------------
1. Visits each brand's offers/products page using a real headless browser
   (Playwright) so JS-rendered content loads properly.
2. Pulls visible text using BeautifulSoup.
3. Sends that text to Groq (AI) to extract structured freebie info.
4. Saves raw HTML + structured JSON to scraper/cache/ so the demo
   never needs a live scrape.

RUN IT
------
    python scraper/scrape.py

Results land in scraper/cache/<brand>_raw.txt and scraper/cache/<brand>_data.json
These feed directly into the platform's freebie catalogue.
"""

import os, json, time, pathlib
from datetime import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

# ── cache folder ──────────────────────────────────────────────────────────────
CACHE = pathlib.Path(__file__).parent / "cache"
CACHE.mkdir(exist_ok=True)

# ── the 10 brands ─────────────────────────────────────────────────────────────
BRANDS = [
    {
        "name": "Minimalist",
        "urls": [
            "https://minimalist.com/collections/all",
            "https://minimalist.com",
        ],
    },
    {
        "name": "The Derma Co",
        "urls": [
            "https://thedermacompany.com/collections/all",
            "https://thedermacompany.com",
        ],
    },
    {
        "name": "Foxtale",
        "urls": [
            "https://foxtale.in/collections/all",
            "https://foxtale.in",
        ],
    },
    {
        "name": "Plum",
        "urls": [
            "https://plumgoodness.com/collections/all",
            "https://plumgoodness.com",
        ],
    },
    {
        "name": "Dot & Key",
        "urls": [
            "https://dotandkey.com/collections/all",
            "https://dotandkey.com",
        ],
    },
    {
        "name": "Pilgrim",
        "urls": [
            "https://pilgrimbeauty.in/collections/all",
            "https://pilgrimbeauty.in",
        ],
    },
    {
        "name": "mCaffeine",
        "urls": [
            "https://mcaffeine.com/collections/all",
            "https://mcaffeine.com",
        ],
    },
    {
        "name": "Mamaearth",
        "urls": [
            "https://mamaearth.in/collections/all",
            "https://mamaearth.in",
        ],
    },
    {
        "name": "WOW Skin Science",
        "urls": [
            "https://buywow.in/collections/all",
            "https://buywow.in",
        ],
    },
    {
        "name": "Re'equil",
        "urls": [
            "https://reequil.com/collections/all",
            "https://reequil.com",
        ],
    },
]

# ── scraping helpers ──────────────────────────────────────────────────────────

def scrape_page(url: str, wait_seconds: int = 3) -> str:
    """
    Use Playwright to load a page (handles JS), return visible text.
    Falls back to empty string on any error.
    """
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            )
            page.goto(url, timeout=30000, wait_until="domcontentloaded")
            time.sleep(wait_seconds)
            html = page.content()
            browser.close()

        soup = BeautifulSoup(html, "html.parser")

        # remove noise
        for tag in soup(["script", "style", "nav", "footer",
                          "header", "noscript", "svg", "iframe"]):
            tag.decompose()

        # grab meaningful text chunks
        chunks = []
        for el in soup.find_all(["h1","h2","h3","p","li","span","div","a"]):
            txt = el.get_text(" ", strip=True)
            if 20 < len(txt) < 500:
                chunks.append(txt)

        # deduplicate while preserving order
        seen, clean = set(), []
        for c in chunks:
            if c not in seen:
                seen.add(c)
                clean.append(c)

        return "\n".join(clean[:300])

    except Exception as e:
        print(f"    [scraper] error on {url}: {e}")
        return ""


def extract_with_ai(brand_name: str, raw_text: str) -> list:
    """
    Send raw page text to Groq. Ask it to pull out structured freebie/offer data.
    Returns a list of dicts.
    """
    if not raw_text.strip():
        return []

    import sys
    sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
    from llm import ask_llm

    prompt = f"""
You are a market research analyst for an Indian skincare brand.

Below is text scraped from {brand_name}'s website.

Extract ALL mentions of:
- Free gifts / freebies / GWP (gift with purchase)
- Discounts or offers (e.g. "buy 2 get 1 free", "free product on orders above Rs X")
- Bundling deals
- Loyalty or reward perks
- Any product they highlight as a trial / sample

For EACH one found, return a JSON object with these exact keys:
  "brand"           : "{brand_name}"
  "freebie"         : short name of the free item or offer
  "condition"       : what triggers it e.g. "order above Rs999" (or null)
  "category"        : one of: skincare-trial | skincare-tool | accessory | discount | bundle | other
  "est_cost"        : rough manufacturing cost in rupees as a number (or null)
  "perceived_value" : 0-100, how valuable a customer would find this
  "novelty"         : 0-100, how fresh/surprising vs typical freebies
  "source_url"      : null

Return ONLY a valid JSON array. No explanation, no markdown, no preamble.
If nothing relevant is found, return [].

--- SCRAPED TEXT START ---
{raw_text[:6000]}
--- SCRAPED TEXT END ---
"""
    result = ask_llm(
        prompt,
        system="You are a precise JSON-only data extractor. Output valid JSON arrays only.",
        temperature=0.1
    )

    try:
        start = result.index("[")
        end   = result.rindex("]") + 1
        return json.loads(result[start:end])
    except Exception:
        print(f"    [ai] could not parse JSON for {brand_name}")
        return []


# ── main scrape loop ──────────────────────────────────────────────────────────

def scrape_brand(brand: dict) -> list:
    name      = brand["name"]
    safe_name = name.lower().replace(" ", "_").replace("'", "").replace("&", "and")

    raw_path  = CACHE / f"{safe_name}_raw.txt"
    data_path = CACHE / f"{safe_name}_data.json"

    # use cache if less than 24 hours old
    if data_path.exists():
        age_hours = (time.time() - data_path.stat().st_mtime) / 3600
        if age_hours < 24:
            print(f"  [{name}] using cached data ({age_hours:.1f}h old)")
            return json.loads(data_path.read_text())

    print(f"  [{name}] scraping...")
    combined_text = ""
    for url in brand["urls"]:
        print(f"    -> {url}")
        text = scrape_page(url)
        if text:
            combined_text += f"\n\n=== {url} ===\n{text}"
            break   # one good page is enough

    raw_path.write_text(combined_text, encoding="utf-8")
    print(f"    saved {len(combined_text)} chars of raw text")

    print(f"    extracting with AI...")
    records = extract_with_ai(name, combined_text)
    print(f"    found {len(records)} freebie/offer records")

    data_path.write_text(
        json.dumps(records, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    return records


def load_all_cached() -> list:
    """Load all cached brand data without scraping. Use this in the dashboard."""
    all_records = []
    for f in sorted(CACHE.glob("*_data.json")):
        if f.name == "all_brands.json":
            continue
        try:
            all_records.extend(json.loads(f.read_text()))
        except Exception:
            pass
    return all_records


def run_all():
    print(f"\n{'='*60}")
    print(f"  Freebie Intelligence Scraper")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  Targeting {len(BRANDS)} brands")
    print(f"{'='*60}\n")

    all_records = []

    for brand in BRANDS:
        try:
            records = scrape_brand(brand)
            all_records.extend(records)
            time.sleep(2)   # be polite — don't hammer servers
        except Exception as e:
            print(f"  [{brand['name']}] FAILED: {e}")
            continue

    combined_path = CACHE / "all_brands.json"
    combined_path.write_text(
        json.dumps(all_records, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(f"\n{'='*60}")
    print(f"  Done. {len(all_records)} total records across {len(BRANDS)} brands.")
    print(f"  Combined -> scraper/cache/all_brands.json")
    print(f"{'='*60}\n")

    return all_records


if __name__ == "__main__":
    run_all()