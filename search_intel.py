"""
search_intel.py — Google Search Console "dump" → precise, transparent insights.

The core problem this solves: the brand name "deconstruct" is a common English word,
so a GSC export filtered to `+deconstruct` mixes real product demand with noise
("deconstruct internship", "deconstruct meaning", careers, etc.). Counting all of it
as brand demand caps accuracy at ~70%. This module classifies every query with a
documented, rule-based lexicon so the split is auditable — you can see exactly what
was kept, what was quarantined as noise, and why.

Everything here is deterministic and explainable (no black-box scoring): every number
in the report traces to a rule + a query list. Optional AI (Groq) only writes the
narrative summary on top of the computed facts.
"""

from __future__ import annotations

import io
import re
import json
from collections import defaultdict

import pandas as pd

from llm import groq_chat, groq_available

# ── lexicons (edit these to tune precision; the report prints them verbatim) ──
NICHE = [  # skincare product / ingredient / concern vocabulary → genuine demand
    "serum", "sunscreen", "sun screen", "sunblock", "spf", "moistur", "cream", "gel",
    "lotion", "cleanser", "face wash", "facewash", "toner", "mask", "scrub", "exfoli",
    "balm", "lip balm", "face oil", "foam", "mist", "essence", "peel", "under eye",
    "eye cream", "body lotion", "body wash",
    "niacinamide", "salicylic", "retinol", "retinoid", "hyaluronic", "vitamin c",
    "ascorbic", "ferulic", "azelaic", "glycolic", "lactic", "mandelic", "ceramide",
    "peptide", "benzoyl", "adapalene", "tranexamic", "kojic", "arbutin", "aha", "bha",
    "pha", "squalane", "panthenol", "centella", "cica", "tea tree",
    "acne", "pimple", "pigment", "dark spot", "dark circle", "tan", "oily skin",
    "dry skin", "sensitive skin", "pores", "blackhead", "whitehead", "wrinkle",
    "aging", "ageing", "dull", "glow", "bright", "hydrat", "redness", "blemish",
    "uneven", "skin tone", "melasma", "sunburn",
]
COMMERCIAL = ["coupon", "combo", "kit", "buy 1 get 1", "buy1get1", "b1g1", "bogo",
              "sale", "offer", "discount", "deal", "price", "cost", "mrp", "combo pack"]
REPUTATION = ["review", "customer care", "complaint", "good brand", "is deconstruct",
              "company", "contact", "legit", "genuine", "safe", "founder", "quality"]
NAV = [".com", ".in", "www", "site", "website", "app download", "app", "login",
       "online", "official"]
TOOL = ["skin analysis", "skin analyzer", "skin test", "skin quiz",
        "analyse my skin", "analyze my skin"]
NOISE = ["internship", "intern", "career", "job", "hiring", "vacancy", "recruit",
         "salary", "stipend", "unstop", "season 1", "season 2", "winner",
         "meaning", "definition", "define", "synonym", "derrida", "philosophy",
         "literary", "essay", "deconstruction", "wikipedia", "architecture",
         "fashion", "recipe", "song", "movie"]
BRAND = ["the deconstruct", "thedeconstruct", "deconstruct", "decon", "skincare",
         "skin care", "brand", "products", "product", "shop", "store"]

CTR_CURVE = {1: 0.28, 2: 0.15, 3: 0.10, 4: 0.07, 5: 0.05, 6: 0.04,
             7: 0.032, 8: 0.026, 9: 0.021, 10: 0.018}


def _has(text, terms):
    return any(t in text for t in terms)


def classify_query(query):
    """Return (klass, category, intent). Rule order is precedence — first match wins."""
    t = " " + str(query).lower().strip() + " "
    niche = _has(t, NICHE)
    commercial = _has(t, COMMERCIAL)

    if niche:
        return "product", _category(t), ("commercial" if commercial else "product/category")
    if _has(t, TOOL):
        return "tool", "—", "engagement"
    if _has(t, NOISE):
        return "noise", "—", "irrelevant"
    if commercial:
        return "commercial", "—", "commercial"
    if _has(t, REPUTATION):
        return "brand_info", "—", "reputation"
    # strip brand + nav tokens; if nothing meaningful remains → pure brand navigation
    residual = t
    for b in sorted(BRAND + NAV, key=len, reverse=True):
        residual = residual.replace(b, " ")
    residual = re.sub(r"[^a-z0-9]+", " ", residual).strip()
    if not residual:
        return "brand_core", "—", "navigational"
    return "ambiguous", "—", "unclassified"


def _category(t):
    if _has(t, ["spf", "sunscreen", "sun screen", "sunblock", "sunburn"]):
        return "Sunscreen"
    if _has(t, ["vitamin c", "ascorbic", "ferulic"]):
        return "Vitamin C"
    if "niacinamide" in t:
        return "Niacinamide"
    if _has(t, ["salicylic", "bha"]):
        return "Salicylic / BHA"
    if _has(t, ["retinol", "retinoid", "adapalene"]):
        return "Retinol"
    if "lip balm" in t:
        return "Lip Balm"
    if _has(t, ["face wash", "facewash", "cleanser"]):
        return "Cleanser / Face Wash"
    if _has(t, ["moistur"]) or ("cream" in t and "eye" not in t):
        return "Moisturizer"
    if "toner" in t:
        return "Toner"
    if _has(t, ["under eye", "eye cream", "dark circle"]):
        return "Under-Eye"
    if "serum" in t:
        return "Serum (other)"
    return "Other skincare"


def _expected_ctr(pos):
    p = int(round(pos))
    if p <= 10:
        return CTR_CURVE.get(max(p, 1), 0.018)
    return 0.010 if p <= 20 else 0.004


def _page_category(url):
    u = url.lower()
    m = re.search(r"/collections/([a-z0-9\-]+)", u) or re.search(r"/products/([a-z0-9\-]+)", u)
    slug = m.group(1).replace("-", " ") if m else ""
    if slug:
        return _category(" " + slug + " ") if _has(" " + slug + " ", NICHE) else slug.title()
    if "/pages/" in u:
        return "Info / Landing page"
    if u.rstrip("/").endswith(".in") or u.rstrip("/").endswith(".com"):
        return "Homepage"
    return "Other"


def analyse_dump(xlsx_bytes):
    """Full analysis of a GSC workbook export. Returns a JSON-serialisable dict."""
    xl = pd.ExcelFile(io.BytesIO(xlsx_bytes))
    tabs = xl.sheet_names

    def tab(name):
        return xl.parse(name) if name in tabs else pd.DataFrame()

    q = tab("Queries").rename(columns={"Top queries": "query"})
    q["query"] = q["query"].astype(str)
    cls_info = q["query"].apply(classify_query)
    q["cls"] = [c[0] for c in cls_info]
    q["cat"] = [c[1] for c in cls_info]
    q["intent"] = [c[2] for c in cls_info]

    tot_c, tot_i = int(q["Clicks"].sum()), int(q["Impressions"].sum())

    # class accounting (the accuracy panel)
    classes = []
    for cls, grp in q.groupby("cls"):
        classes.append({
            "class": cls, "queries": int(len(grp)),
            "clicks": int(grp["Clicks"].sum()), "impressions": int(grp["Impressions"].sum()),
            "clicks_pct": round(grp["Clicks"].sum() / max(tot_c, 1) * 100, 1),
            "impr_pct": round(grp["Impressions"].sum() / max(tot_i, 1) * 100, 1),
        })
    classes.sort(key=lambda c: -c["impressions"])

    def sample(cls, n=25):
        g = q[q.cls == cls].sort_values("Impressions", ascending=False).head(n)
        return [{"query": r.query, "clicks": int(r.Clicks), "impressions": int(r.Impressions),
                 "ctr": round(float(r.CTR) * 100, 2), "position": round(float(r.Position), 1)}
                for r in g.itertuples()]

    # category demand (product queries only)
    prod = q[q.cls == "product"]
    cats = []
    for c, grp in prod.groupby("cat"):
        imp = int(grp["Impressions"].sum())
        clk = int(grp["Clicks"].sum())
        ctr = round(clk / imp * 100, 2) if imp else 0.0
        pos = round((grp["Position"] * grp["Impressions"]).sum() / imp, 1) if imp else 0.0
        cats.append({"category": c, "queries": int(len(grp)), "clicks": clk,
                     "impressions": imp, "ctr_pct": ctr, "avg_position": pos})
    cats.sort(key=lambda x: -x["impressions"])

    # intent split
    intents = []
    for i, grp in q.groupby("intent"):
        intents.append({"intent": i, "clicks": int(grp["Clicks"].sum()),
                        "impressions": int(grp["Impressions"].sum()),
                        "impr_pct": round(grp["Impressions"].sum() / max(tot_i, 1) * 100, 1)})
    intents.sort(key=lambda x: -x["impressions"])

    # opportunities on product queries: striking distance + low CTR
    striking = [{"query": r.query, "position": round(float(r.Position), 1),
                 "impressions": int(r.Impressions), "clicks": int(r.Clicks)}
                for r in prod[(prod.Position >= 8) & (prod.Position <= 20)]
                .sort_values("Impressions", ascending=False).head(15).itertuples()]
    low_ctr = []
    for r in prod.itertuples():
        exp = _expected_ctr(r.Position)
        if r.Position <= 10 and float(r.CTR) < exp * 0.6 and r.Impressions >= 500:
            low_ctr.append({"query": r.query, "position": round(float(r.Position), 1),
                            "ctr": round(float(r.CTR) * 100, 2), "expected": round(exp * 100, 1),
                            "impressions": int(r.Impressions)})
    low_ctr.sort(key=lambda x: -x["impressions"])
    low_ctr = low_ctr[:15]

    # attribute interlinks — how concerns / ingredients / formats co-occur in demand
    ATTRS = {"oily skin": "oily skin", "dry skin": "dry skin", "acne": "acne", "tan": "tan",
             "glow": "glow", "bright": "brightening", "dark spot": "dark spots",
             "pigment": "pigmentation", "sensitive": "sensitive skin", "dull": "dullness",
             "gel": "gel", "serum": "serum", "sunscreen": "sunscreen", "spf 50": "SPF 50",
             "niacinamide": "niacinamide", "vitamin c": "vitamin C", "salicylic": "salicylic",
             "hyaluronic": "hyaluronic", "matte": "matte", "spray": "spray"}
    pair_w = defaultdict(int)
    for r in prod.itertuples():
        t = " " + r.query.lower() + " "
        found = sorted({label for key, label in ATTRS.items() if key in t})
        for a in range(len(found)):
            for b in range(a + 1, len(found)):
                pair_w[(found[a], found[b])] += int(r.Impressions)
    interlinks = [{"a": a, "b": b, "impressions": w}
                  for (a, b), w in sorted(pair_w.items(), key=lambda x: -x[1])[:15]]

    # pages → canonical category + page opportunities
    pg = tab("Pages").rename(columns={"Top pages": "page"})
    pages_opp = []
    if not pg.empty:
        pg["page"] = pg["page"].astype(str)
        for r in pg.sort_values("Impressions", ascending=False).head(20).itertuples():
            exp = _expected_ctr(r.Position)
            pages_opp.append({
                "page": r.page.replace("https://thedeconstruct.in", "") or "/",
                "category": _page_category(r.page),
                "clicks": int(r.Clicks), "impressions": int(r.Impressions),
                "ctr": round(float(r.CTR) * 100, 2), "position": round(float(r.Position), 1),
                "underperforming": bool(r.Position <= 10 and float(r.CTR) < exp * 0.6),
            })

    # trend / seasonality from the daily Chart tab
    ch = tab("Chart")
    trend = {"months": [], "spikes": [], "dow": [], "days": 0, "direction": ""}
    if not ch.empty and "Date" in ch.columns:
        ch = ch.copy()
        ch["Date"] = pd.to_datetime(ch["Date"])
        ch["month"] = ch["Date"].dt.strftime("%Y-%m")
        ch["dow"] = ch["Date"].dt.day_name()
        trend["days"] = int(len(ch))
        for m, grp in ch.groupby("month"):
            trend["months"].append({"month": m, "days": int(len(grp)),
                "clicks_per_day": round(grp["Clicks"].mean()), "impr_per_day": round(grp["Impressions"].mean()),
                "avg_position": round(grp["Position"].mean(), 2)})
        for r in ch.sort_values("Impressions", ascending=False).head(4).itertuples():
            trend["spikes"].append({"date": str(r.Date.date()), "dow": r.dow,
                                    "impressions": int(r.Impressions), "clicks": int(r.Clicks)})
        dow_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        dm = ch.groupby("dow")["Clicks"].mean()
        trend["dow"] = [{"day": d[:3], "clicks_per_day": round(dm.get(d, 0))} for d in dow_order]
        if trend["months"]:
            first, last = trend["months"][0]["clicks_per_day"], trend["months"][-1]["clicks_per_day"]
            trend["direction"] = ("up" if last > first * 1.1 else "down" if last < first * 0.9 else "flat")

    def small_tab(name, keycol):
        df = tab(name)
        if df.empty:
            return []
        return [{"name": str(getattr(r, keycol.replace(" ", "_"), getattr(r, "_1", ""))),
                 "clicks": int(r.Clicks), "impressions": int(r.Impressions),
                 "ctr": round(float(r.CTR) * 100, 2), "position": round(float(r.Position), 1)}
                for r in df.head(8).itertuples()]

    # geo / device / appearance (robust column access)
    def rows_of(name, label_col):
        df = tab(name)
        out = []
        if df.empty:
            return out
        for _, row in df.head(8).iterrows():
            out.append({"label": str(row[label_col]), "clicks": int(row["Clicks"]),
                        "impressions": int(row["Impressions"]), "ctr": round(float(row["CTR"]) * 100, 2),
                        "position": round(float(row["Position"]), 1)})
        return out

    filt = tab("Filters")
    filt_map = {str(r.Filter): str(r.Value) for r in filt.itertuples()} if not filt.empty else {}

    # full audit tables (every row) — the Excel report leans on these
    query_table = [{"query": r.query, "class": r.cls, "category": r.cat, "intent": r.intent,
                    "clicks": int(r.Clicks), "impressions": int(r.Impressions),
                    "ctr_pct": round(float(r.CTR) * 100, 2), "position": round(float(r.Position), 1)}
                   for r in q.itertuples()]
    page_table = ([{"page": r.page, "category": _page_category(r.page),
                    "clicks": int(r.Clicks), "impressions": int(r.Impressions),
                    "ctr_pct": round(float(r.CTR) * 100, 2), "position": round(float(r.Position), 1)}
                   for r in pg.itertuples()] if not pg.empty else [])

    return {
        "meta": {
            "date_range": filt_map.get("Date", ""), "query_filter": filt_map.get("Query", ""),
            "search_type": filt_map.get("Search type", ""),
            "total_clicks": tot_c, "total_impressions": tot_i,
            "query_rows": int(len(q)), "page_rows": int(len(pg)),
        },
        "classes": classes,
        "noise_samples": sample("noise"), "ambiguous_samples": sample("ambiguous"),
        "brand_core_samples": sample("brand_core", 10), "commercial_samples": sample("commercial", 12),
        "categories": cats, "intents": intents,
        "striking": striking, "low_ctr": low_ctr, "interlinks": interlinks,
        "pages": pages_opp, "trend": trend,
        "query_table": query_table, "page_table": page_table,
        "geo": rows_of("Countries", "Country"), "device": rows_of("Devices", "Device"),
        "appearance": rows_of("Search appearance", "Search Appearance"),
        "lexicon_sizes": {"niche": len(NICHE), "commercial": len(COMMERCIAL),
                          "reputation": len(REPUTATION), "noise": len(NOISE), "tool": len(TOOL)},
    }


def executive_summary(ins):
    """Grounded, brand-manager-tone read of the whole dump (one Groq call)."""
    if not groq_available():
        return {"headline": "Connect Groq (GROQ_API_KEY) for the AI executive summary.",
                "working": [], "not_working": [], "seasonality": "", "priorities": []}
    m = ins["meta"]
    leak = "; ".join(f"{p['page']} ({p['impressions']:,} impr, {p['ctr']}% CTR, pos {p['position']})"
                     for p in ins["pages"] if p["underperforming"])[:600]
    ctx = "\n".join([
        f"Brand: Deconstruct (thedeconstruct.in). Window: {m['date_range']}.",
        f"Totals (top-1000 branded queries): {m['total_clicks']:,} clicks, {m['total_impressions']:,} impressions.",
        "Category demand by impressions: " + ", ".join(f"{c['category']} {c['impressions']:,}" for c in ins["categories"][:7]),
        "Attribute interlinks (co-searched): " + ", ".join(f"{p['a']}+{p['b']}" for p in ins["interlinks"][:6]),
        "Monthly clicks/day: " + ", ".join(f"{mm['month']}={mm['clicks_per_day']}" for mm in ins["trend"]["months"]),
        "Underperforming high-traffic pages: " + leak,
    ])
    prompt = f"""You are a brand manager at Deconstruct reading its Google Search Console data. Write a crisp,
board-ready read a brand manager instantly understands. Ground EVERY point in the numbers and cite the metric.

{ctx}

Return ONLY JSON:
{{"headline": "1-2 sentences: what Deconstruct IS in search demand",
 "working": ["3-5 concrete things working, each citing the number"],
 "not_working": ["3-5 concrete leaks/gaps, each citing the number"],
 "seasonality": "1-2 sentences on the time trend and what it implies commercially",
 "priorities": ["ordered top 5 actions, most impactful first"]}}
JSON only. Start with {{"""
    raw = groq_chat(prompt, system="Output valid JSON only. Start with {.", temperature=0.3, max_tokens=1700)
    try:
        return json.loads(raw[raw.index("{"): raw.rindex("}") + 1])
    except Exception:
        return {"headline": (raw or "AI summary unavailable.")[:400],
                "working": [], "not_working": [], "seasonality": "", "priorities": []}


def deep_reads(ins):
    """Per-category verdicts + a keyword read (one grounded Groq call). Current-state, not growth."""
    if not groq_available():
        return {"category_reads": [], "keyword_read": ""}
    cats = ins["categories"][:8]
    kws = sorted([r for r in ins["query_table"] if r["class"] in ("product", "commercial")],
                 key=lambda r: -r["impressions"])[:16]
    L = ["Category performance (impressions, clicks, CTR%, weighted avg position):"]
    for c in cats:
        L.append(f"- {c['category']}: {c['impressions']:,} impr, {c['clicks']:,} clk, "
                 f"{c.get('ctr_pct', 0)}% CTR, pos {c.get('avg_position', 0)}")
    L.append("Top keywords (impr, CTR%, pos): " + " | ".join(
        f"{k['query']} ({k['impressions']:,}, {k['ctr_pct']}%, {k['position']})" for k in kws[:14]))
    L.append("Attribute interlinks: " + ", ".join(f"{p['a']}+{p['b']}" for p in ins["interlinks"][:6]))
    ctx = "\n".join(L)
    prompt = f"""You are Deconstruct's brand analyst. Below is CURRENT Google Search Console demand by category and keyword.
For each category give a one-word LABEL and a one-line NOTE that cites the number. LABEL must be exactly one of:
"Dominant" (large demand, healthy capture), "Scale up" (strong demand but weak CTR/position = biggest opportunity),
"Emerging" (smaller but real demand worth nurturing), "Underperforming" (demand exists, capture is poor).
Then a keyword_read on which patterns win (formats / actives / concerns) and what to target next.
IMPORTANT: this is a current-state snapshot from one export — do NOT claim growth-over-time.

{ctx}

Return ONLY JSON:
{{"category_reads":[{{"category":"","label":"","note":""}}],
 "keyword_read":"2-4 sentences: the keyword patterns that win and what to target next"}}
JSON only. Start with {{"""
    raw = groq_chat(prompt, system="Output valid JSON only. Start with {.", temperature=0.3, max_tokens=1500)
    try:
        return json.loads(raw[raw.index("{"): raw.rindex("}") + 1])
    except Exception:
        return {"category_reads": [], "keyword_read": ""}


def whats_working(ins):
    rows = []
    for c in sorted(ins["categories"], key=lambda x: -x["clicks"])[:5]:
        rows.append({"Area": "Category", "Item": c["category"], "Clicks": c["clicks"],
                     "Impressions": c["impressions"], "CTR %": "", "Position": "",
                     "Why it works": "High demand and winning clicks — a category you own"})
    for p in [p for p in ins["pages"] if not p["underperforming"]][:8]:
        rows.append({"Area": "Page", "Item": p["page"], "Clicks": p["clicks"],
                     "Impressions": p["impressions"], "CTR %": p["ctr"], "Position": p["position"],
                     "Why it works": "Ranks well and converts its impressions to clicks"})
    b = next((c for c in ins["classes"] if c["class"] == "brand_core"), {})
    if b:
        rows.append({"Area": "Brand", "Item": '"deconstruct" (navigational)', "Clicks": b.get("clicks", 0),
                     "Impressions": b.get("impressions", 0), "CTR %": "", "Position": "",
                     "Why it works": f"{b.get('clicks_pct', 0)}% of clicks are people searching the brand by name"})
    return rows


def whats_not_working(ins):
    rows = []
    for p in [p for p in ins["pages"] if p["underperforming"]][:10]:
        rows.append({"Issue": "Leaking page — high demand, weak capture", "Item": p["page"],
                     "Impressions": p["impressions"], "CTR %": p["ctr"], "Position": p["position"],
                     "What to do": "Improve ranking + rewrite title/snippet; the demand is already there"})
    for x in ins["striking"][:8]:
        rows.append({"Issue": "Striking distance (rank 8-20)", "Item": x["query"],
                     "Impressions": x["impressions"], "CTR %": "", "Position": x["position"],
                     "What to do": "One on-page push to break onto page 1"})
    for x in ins["low_ctr"][:8]:
        rows.append({"Issue": "Low CTR — ranks but under-clicked", "Item": x["query"],
                     "Impressions": x["impressions"], "CTR %": x["ctr"], "Position": x["position"],
                     "What to do": f"Title/meta rewrite — a result at pos {x['position']} should earn ~{x['expected']}%"})
    return rows


def to_excel(insights, exec_summary=None, reads=None):
    """Styled, charted, self-explanatory brand-manager workbook (built by excel_report)."""
    import excel_report
    return excel_report.build_workbook(insights, exec_summary or {}, reads or {},
                                       whats_working(insights), whats_not_working(insights))
