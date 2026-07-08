"""
trends.py — Global Trend Radar

Tracks skincare trends across 5 key markets:
  🇰🇷 South Korea  — origin market, 12-18 months ahead of India
  🇺🇸 USA          — mainstream adoption, 6-9 months ahead
  🇨🇳 China        — largest market, fast-moving, 6-12 months ahead
  🇫🇷 France       — ingredient science, minimalist, 12+ months ahead
  🇬🇧 UK/England   — similar climate to India, 6-9 months ahead

Sources:
- Google Trends per country
- AI analysis of market-specific signals
- Fallback curated dataset if APIs fail

RUN IT:
    python trends.py
"""

import json
import time
import pathlib
import sys
from datetime import datetime

sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()
from llm import ask_llm

CACHE = pathlib.Path('scraper/cache')
CACHE.mkdir(exist_ok=True)
OUTPUT = CACHE / 'trends.json'

# ── markets to track ──────────────────────────────────────────────────────────
MARKETS = [
    {"name": "South Korea", "geo": "KR", "flag": "🇰🇷",
     "lag_months": "12-18", "why": "Origin of most global skincare trends"},
    {"name": "USA",         "geo": "US", "flag": "🇺🇸",
     "lag_months": "6-9",  "why": "Fastest mainstream adoption, best data"},
    {"name": "China",       "geo": "CN", "flag": "🇨🇳",
     "lag_months": "6-12", "why": "Largest beauty market, fast-moving social"},
    {"name": "France",      "geo": "FR", "flag": "🇫🇷",
     "lag_months": "12+",  "why": "Pharmacy skincare, ingredient science leader"},
    {"name": "UK",          "geo": "GB", "flag": "🇬🇧",
     "lag_months": "6-9",  "why": "Similar climate/pollution concerns to India"},
]

TOPICS = [
    "skin barrier repair",
    "glass skin routine",
    "skin cycling",
    "body skin care",
    "sunscreen reapplication",
    "niacinamide serum",
    "peptide skincare",
    "snail mucin",
    "tranexamic acid",
    "collagen serum",
    "retinol serum",
    "azelaic acid",
    "slugging skincare",
    "lip care routine",
    "centella asiatica",
]


# ── Google Trends per market ──────────────────────────────────────────────────
def fetch_google_trends_for_market(market):
    try:
        from pytrends.request import TrendReq
        pytrends = TrendReq(hl='en-US', tz=360, timeout=(10, 25))
        geo = market["geo"]
        results = []

        for i in range(0, len(TOPICS), 5):
            batch = TOPICS[i:i+5]
            try:
                pytrends.build_payload(batch, cat=0, timeframe='today 3-m', geo=geo)
                data = pytrends.interest_over_time()
                if data.empty:
                    time.sleep(3)
                    continue
                for topic in batch:
                    if topic not in data.columns:
                        continue
                    series = data[topic]
                    avg = float(series.mean())
                    recent = float(series.tail(4).mean())
                    if avg < 5:
                        continue  # skip topics with no real interest
                    direction = "rising" if recent > avg * 1.1 else (
                                "declining" if recent < avg * 0.9 else "stable")
                    results.append({
                        "topic": topic,
                        "avg_interest": round(avg, 1),
                        "recent_interest": round(recent, 1),
                        "direction": direction,
                    })
                time.sleep(3)
            except Exception as e:
                print(f"      batch error: {e}")
                time.sleep(6)
                continue

        return sorted(results, key=lambda x: x["recent_interest"], reverse=True)

    except Exception as e:
        print(f"    Google Trends error for {market['name']}: {e}")
        return []


# ── AI analysis per market ────────────────────────────────────────────────────
def analyse_market(market, trends_data):
    flag = market["flag"]
    name = market["name"]
    lag = market["lag_months"]

    if trends_data:
        trends_summary = "\n".join(
            f"- {t['topic']}: {t['direction']} (interest: {t['recent_interest']})"
            for t in trends_data[:8]
        )
    else:
        trends_summary = "No live data — use your knowledge of this market."

    prompt = f"""You are a global skincare market analyst for Deconstruct, an Indian D2C skincare brand.

Analyse the {name} skincare market ({flag}).
India typically adopts {name} trends {lag} months later.

Google Trends data for {name} (last 3 months):
{trends_summary}

Identify the TOP 3 rising skincare trends in {name} right now that:
1. Are gaining momentum in {name}
2. Have NOT yet fully reached the Indian mass market
3. Are relevant to a science-based D2C skincare brand

For each trend return a JSON object with:
  "signal": "trend name (short, punchy)",
  "market": "{name}",
  "flag": "{flag}",
  "direction": "rising",
  "india_status": "early or emerging or mainstream",
  "india_lag": "{lag} months",
  "note": "one sentence — why this matters for Deconstruct India",
  "freebie_opportunity": "specific low-cost freebie idea under Rs30 that taps this trend"

Return ONLY a JSON array of 3 objects. No markdown. Start with ["""

    time.sleep(4)
    result = ask_llm(prompt, system="Output valid JSON arrays only. Start with [", temperature=0.3)

    try:
        start = result.index('[')
        end = result.rindex(']') + 1
        return json.loads(result[start:end])
    except Exception as e:
        print(f"    AI parse error for {name}: {e}")
        return []


# ── fallback data — one set per market ───────────────────────────────────────
FALLBACK = [
    # South Korea
    {"signal": "Skin cycling (structured multi-night routine)",
     "market": "South Korea", "flag": "🇰🇷", "direction": "rising",
     "india_status": "early", "india_lag": "12-18 months",
     "note": "Korean consumers now follow strict retinol/acid/recovery night cycles — Indian audience ready for education.",
     "freebie_opportunity": "Mini skin cycling guide card + retinol sample sachet"},
    {"signal": "Essence layering (7-skin method revival)",
     "market": "South Korea", "flag": "🇰🇷", "direction": "rising",
     "india_status": "early", "india_lag": "12-18 months",
     "note": "Multiple thin hydration layers trending again; positions toners as essential.",
     "freebie_opportunity": "Travel toner sample with layering instructions"},
    {"signal": "Sunscreen as skincare (not just protection)",
     "market": "South Korea", "flag": "🇰🇷", "direction": "rising",
     "india_status": "emerging", "india_lag": "12-18 months",
     "note": "Korea elevated SPF to a skincare step; India still treats it as optional.",
     "freebie_opportunity": "UV reminder card + mini mirror for reapplication"},
    # USA
    {"signal": "Body care routines (treating body like face)",
     "market": "USA", "flag": "🇺🇸", "direction": "rising",
     "india_status": "early", "india_lag": "6-9 months",
     "note": "US consumers applying serums and SPF to body; untapped in Indian D2C.",
     "freebie_opportunity": "Travel-size body lotion sample"},
    {"signal": "Barrier repair (ceramide focus post over-exfoliation)",
     "market": "USA", "flag": "🇺🇸", "direction": "rising",
     "india_status": "emerging", "india_lag": "6-9 months",
     "note": "Over-exfoliation backlash driving ceramide and moisture barrier products.",
     "freebie_opportunity": "Ceramide balm sample sachet"},
    {"signal": "Tranexamic acid for hyperpigmentation",
     "market": "USA", "flag": "🇺🇸", "direction": "rising",
     "india_status": "early", "india_lag": "6-9 months",
     "note": "Emerging as next niacinamide — huge relevance for Indian skin concerns.",
     "freebie_opportunity": "Tranexamic acid trial sachet with before/after card"},
    # China
    {"signal": "Collagen-boosting ingestibles + topicals combo",
     "market": "China", "flag": "🇨🇳", "direction": "rising",
     "india_status": "early", "india_lag": "6-12 months",
     "note": "Chinese consumers pairing topical collagen serums with supplements — new category forming.",
     "freebie_opportunity": "Mini collagen serum sample"},
    {"signal": "Whitening to brightening repositioning",
     "market": "China", "flag": "🇨🇳", "direction": "rising",
     "india_status": "emerging", "india_lag": "6-12 months",
     "note": "Brands shifting 'whitening' to 'brightening' framing — more relevant to Indian consumers.",
     "freebie_opportunity": "Vitamin C brightening serum sample"},
    {"signal": "Probiotic / microbiome skincare",
     "market": "China", "flag": "🇨🇳", "direction": "rising",
     "india_status": "early", "india_lag": "6-12 months",
     "note": "Gut-skin axis trending in premium Chinese beauty; India still in early awareness.",
     "freebie_opportunity": "Probiotic moisturiser sample sachet"},
    # France
    {"signal": "Pharmacy-grade minimalism (fewer, proven ingredients)",
     "market": "France", "flag": "🇫🇷", "direction": "rising",
     "india_status": "emerging", "india_lag": "12+ months",
     "note": "French consumers choosing 3-step routines with clinical actives — counter to complexity trend.",
     "freebie_opportunity": "Mini ingredient education card (what you need, what to skip)"},
    {"signal": "SPF in every step (tinted moisturisers with SPF)",
     "market": "France", "flag": "🇫🇷", "direction": "rising",
     "india_status": "early", "india_lag": "12+ months",
     "note": "French pharmacies pushing SPF-infused daily moisturisers as the norm.",
     "freebie_opportunity": "SPF moisturiser sample sachet"},
    {"signal": "Retinol normalisation for all ages",
     "market": "France", "flag": "🇫🇷", "direction": "rising",
     "india_status": "emerging", "india_lag": "12+ months",
     "note": "French dermatologists recommending retinol from age 25; India still sees it as advanced.",
     "freebie_opportunity": "Retinol starter guide + low-dose sample"},
    # UK
    {"signal": "Hyperpigmentation focus (pollution + hormonal)",
     "market": "UK", "flag": "🇬🇧", "direction": "rising",
     "india_status": "mainstream", "india_lag": "6-9 months",
     "note": "UK brands addressing pollution-driven pigmentation — identical concern in Indian metros.",
     "freebie_opportunity": "Niacinamide serum sample targeting dark spots"},
    {"signal": "Sensitive skin / redness-calming actives",
     "market": "UK", "flag": "🇬🇧", "direction": "rising",
     "india_status": "emerging", "india_lag": "6-9 months",
     "note": "Centella, azelaic acid and cica for reactive skin trending in UK — rising in India too.",
     "freebie_opportunity": "Centella/cica calming serum sample"},
    {"signal": "Peptides as the next hero ingredient",
     "market": "UK", "flag": "🇬🇧", "direction": "rising",
     "india_status": "early", "india_lag": "6-9 months",
     "note": "UK consumers graduating from niacinamide to peptides — same journey Indian consumers will take.",
     "freebie_opportunity": "Peptide serum sample with explanation card"},
]


# ── main ──────────────────────────────────────────────────────────────────────
def run():
    print(f"\n{'='*55}")
    print(f"  Global Trend Radar  —  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  Markets: {' '.join(m['flag'] for m in MARKETS)}")
    print(f"{'='*55}\n")

    # use cache if fresh
    if OUTPUT.exists():
        age_hours = (time.time() - OUTPUT.stat().st_mtime) / 3600
        if age_hours < 12:
            print(f"Using cached trends ({age_hours:.1f}h old).")
            print("Delete scraper/cache/trends.json to refresh.\n")
            data = json.loads(OUTPUT.read_text(encoding='utf-8'))
            for t in data:
                print(f"  {t['flag']} {t['signal']} [{t['india_status']}]")
            return data

    all_trends = []

    for market in MARKETS:
        print(f"{market['flag']} {market['name']} (lag: {market['lag_months']} months)...")
        trends_data = fetch_google_trends_for_market(market)
        print(f"  Google Trends: {len(trends_data)} signals")

        ai_trends = analyse_market(market, trends_data)
        if ai_trends:
            print(f"  AI extracted {len(ai_trends)} trends")
            all_trends.extend(ai_trends)
        else:
            # use fallback for this market
            fallback = [t for t in FALLBACK if t["market"] == market["name"]]
            print(f"  Using fallback ({len(fallback)} trends)")
            all_trends.extend(fallback)

        time.sleep(3)

    OUTPUT.write_text(
        json.dumps(all_trends, indent=2, ensure_ascii=False),
        encoding='utf-8'
    )

    print(f"\n{'='*55}")
    print(f"  Done. {len(all_trends)} trends across {len(MARKETS)} markets")
    print(f"  Saved to scraper/cache/trends.json")
    print(f"{'='*55}\n")

    for t in all_trends:
        print(f"  {t['flag']} [{t['market']}] {t['signal']} — {t['india_status']}")

    return all_trends


if __name__ == "__main__":
    run()