"""
gsc_engine.py — Google Search Console (own-site) keyword intelligence.

Pulls REAL first-party search data for a verified property via the Search Console
API (Search Analytics), then turns it into a prioritised, AI-drafted action plan:
striking-distance keywords, low-CTR rewrite wins, content-gap questions and
decliners — i.e. it automates what an SEO team does by hand.

AUTH — service account (recommended, demo-safe, headless):
  1. Google Cloud → create a project → enable "Google Search Console API".
  2. Create a Service Account → create a JSON key → download it.
  3. In Search Console → Settings → Users & permissions → Add user →
     paste the service account's client_email (…@….iam.gserviceaccount.com),
     "Restricted" access is enough.
  4. Point GSC_SA_JSON at the key path in .env, OR upload it in the app.
No interactive OAuth, no consent screen, no redirect — it just works on stage.

⚠️  The service-account key is a SECRET. Keep it out of any commit and out of chat.
"""

from __future__ import annotations

import os
import io
import json
import datetime as _dt

from dotenv import load_dotenv

load_dotenv()

from llm import groq_chat, groq_available

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]


# ── auth ──────────────────────────────────────────────────────────────────────
def parse_sa_json(raw_bytes):
    """Validate an uploaded service-account key. Returns (info|None, email, error)."""
    try:
        info = json.loads(raw_bytes)
    except Exception as e:
        return None, "", f"Not valid JSON: {e}"
    if info.get("type") != "service_account" or not info.get("client_email"):
        return None, "", "This isn't a service-account key JSON (need type=service_account)."
    return info, info.get("client_email", ""), ""


def _credentials(sa_info=None, sa_path=None):
    from google.oauth2 import service_account
    if sa_info:
        return service_account.Credentials.from_service_account_info(sa_info, scopes=SCOPES)
    path = sa_path or os.getenv("GSC_SA_JSON", "")
    if path and os.path.exists(path):
        return service_account.Credentials.from_service_account_file(path, scopes=SCOPES)
    return None


def _service(sa_info=None, sa_path=None):
    from googleapiclient.discovery import build
    creds = _credentials(sa_info, sa_path)
    if not creds:
        return None
    return build("searchconsole", "v1", credentials=creds, cache_discovery=False)


def list_sites(sa_info=None, sa_path=None):
    """Return (site_urls, error) the credentials can read."""
    try:
        svc = _service(sa_info, sa_path)
        if not svc:
            return [], "No credentials — set GSC_SA_JSON in .env or upload the key file."
        resp = svc.sites().list().execute()  # type: ignore[attr-defined]
        sites = [s["siteUrl"] for s in resp.get("siteEntry", [])
                 if s.get("permissionLevel") != "siteUnverifiedUser"]
        return sorted(sites), ""
    except Exception as e:
        return [], str(e)


# ── fetch ─────────────────────────────────────────────────────────────────────
def fetch_queries(site_url, start, end, dimensions=("query",), row_limit=25000,
                  sa_info=None, sa_path=None):
    """Raw Search-Analytics rows for a period. Returns (rows, error)."""
    try:
        svc = _service(sa_info, sa_path)
        if not svc:
            return [], "No credentials."
        body = {"startDate": start, "endDate": end,
                "dimensions": list(dimensions), "rowLimit": row_limit,
                "dataState": "final"}
        resp = svc.searchanalytics().query(siteUrl=site_url, body=body).execute()  # type: ignore[attr-defined]
        dims = list(dimensions)
        rows = []
        for r in resp.get("rows", []):
            keys = r.get("keys", [])
            row = {dims[i]: keys[i] for i in range(len(dims)) if i < len(keys)}
            row.update({
                "clicks": r.get("clicks", 0),
                "impressions": r.get("impressions", 0),
                "ctr": r.get("ctr", 0.0),
                "position": r.get("position", 0.0),
            })
            rows.append(row)
        return rows, ""
    except Exception as e:
        return [], str(e)


def parse_gsc_csv(file_bytes, filename=""):
    """
    Parse a Search Console → Performance → Export 'Queries' file into query rows —
    NO Google Cloud / API / billing needed. Accepts .csv, .xlsx/.xls, or the .zip
    Google hands you (extracts the Queries csv). Returns (rows, error).
    """
    import pandas as pd
    name = (filename or "").lower()
    try:
        if name.endswith(".zip"):
            import zipfile
            zf = zipfile.ZipFile(io.BytesIO(file_bytes))
            target = (next((n for n in zf.namelist()
                            if "quer" in n.lower() and n.lower().endswith(".csv")), None)
                      or next((n for n in zf.namelist() if n.lower().endswith(".csv")), None))
            if not target:
                return [], "No CSV found inside the ZIP export."
            df = pd.read_csv(io.BytesIO(zf.read(target)))
        elif name.endswith((".xlsx", ".xls")):
            xl = pd.ExcelFile(io.BytesIO(file_bytes))
            sheet = next((s for s in xl.sheet_names if "quer" in str(s).lower()), xl.sheet_names[0])
            df = xl.parse(sheet)
        else:
            df = pd.read_csv(io.BytesIO(file_bytes))
    except Exception as e:
        return [], f"Couldn't read the file: {e}"
    return _rows_from_df(df)


def _rows_from_df(df):
    """Map a Search Console export dataframe → normalised query rows."""
    cols = {str(c).lower().strip(): c for c in df.columns}

    def find(*keys):
        for k in keys:
            for lc, orig in cols.items():
                if k in lc:
                    return orig
        return None

    qc = find("top quer", "query", "quer")
    cc, ic, rc, pc = find("click"), find("impress"), find("ctr"), find("position")
    if not qc or (cc is None and ic is None):
        return [], ("This doesn't look like a Search Console 'Queries' export — I need a query "
                    "column plus clicks/impressions. In Search Console: Performance → Export → the Queries tab.")

    rows = []
    for _, r in df.iterrows():
        q = str(r.get(qc, "")).strip()
        if not q or q.lower() == "nan":
            continue

        def num(col, is_ctr=False):
            if col is None:
                return 0.0
            s = str(r.get(col, 0))
            had_pct = "%" in s
            try:
                v = float(s.replace(",", "").replace("%", "").strip())
            except Exception:
                return 0.0
            if is_ctr and (had_pct or v > 1):   # "3.4%" / bare "3.4" → fraction
                v = v / 100.0
            return v

        rows.append({"query": q, "clicks": num(cc), "impressions": num(ic),
                     "ctr": num(rc, is_ctr=True), "position": num(pc)})
    return rows, ""


def default_periods(days=28, lag_days=3):
    """(start, end, prev_start, prev_end) as ISO dates. GSC lags ~2-3 days."""
    end = _dt.date.today() - _dt.timedelta(days=lag_days)
    start = end - _dt.timedelta(days=days - 1)
    prev_end = start - _dt.timedelta(days=1)
    prev_start = prev_end - _dt.timedelta(days=days - 1)
    return start.isoformat(), end.isoformat(), prev_start.isoformat(), prev_end.isoformat()


# ── analysis ──────────────────────────────────────────────────────────────────
_CTR_CURVE = {1: 0.28, 2: 0.15, 3: 0.10, 4: 0.07, 5: 0.05,
              6: 0.04, 7: 0.032, 8: 0.026, 9: 0.021, 10: 0.018}


def _expected_ctr(pos):
    p = int(round(pos))
    if p <= 10:
        return _CTR_CURVE.get(max(p, 1), 0.018)
    if p <= 20:
        return 0.010
    return 0.004


_QWORDS = ("how", "what", "why", "best", "which", "can", "does", "is", "are",
           "vs", "review", "benefits", "for", "when", "should")


def analyse(rows, prev_rows=None, min_impr=20):
    """Bucket raw query rows into opportunity lists. Pure, testable, no network."""
    rows = [r for r in rows if r.get("impressions", 0) >= min_impr and r.get("query")]

    striking = sorted([r for r in rows if 8 <= r["position"] <= 20],
                      key=lambda r: -r["impressions"])[:100]

    low_ctr = []
    for r in rows:
        if r["position"] <= 10:
            exp = _expected_ctr(r["position"])
            if r["ctr"] < exp * 0.6:
                low_ctr.append({**r, "expected_ctr": round(exp, 3),
                                "ctr_gap": round(exp - r["ctr"], 4)})
    low_ctr.sort(key=lambda r: -(r["ctr_gap"] * r["impressions"]))
    low_ctr = low_ctr[:100]

    def _is_question(q):
        ql = q.lower()
        return any(ql.startswith(w + " ") or (" " + w + " ") in ql for w in _QWORDS)
    questions = sorted([r for r in rows if _is_question(r["query"])],
                       key=lambda r: -r["impressions"])[:100]

    decliners = []
    if prev_rows:
        prev = {r["query"]: r for r in prev_rows if r.get("query")}
        for r in rows:
            p = prev.get(r["query"])
            if not p:
                continue
            pos_delta = r["position"] - p["position"]      # +ve = fell in rankings
            clk_delta = r["clicks"] - p["clicks"]
            if pos_delta >= 1.0 or clk_delta <= -5:
                decliners.append({**r, "prev_position": round(p["position"], 1),
                                  "pos_delta": round(pos_delta, 1),
                                  "prev_clicks": p["clicks"], "clk_delta": clk_delta})
        decliners.sort(key=lambda r: -r["pos_delta"])
        decliners = decliners[:100]

    totals = {
        "queries": len(rows),
        "clicks": round(sum(r["clicks"] for r in rows)),
        "impressions": round(sum(r["impressions"] for r in rows)),
        "avg_position": round(sum(r["position"] for r in rows) / len(rows), 1) if rows else 0,
        "avg_ctr_pct": round(100 * sum(r["clicks"] for r in rows) /
                             max(sum(r["impressions"] for r in rows), 1), 2),
    }
    return {"totals": totals, "striking": striking, "low_ctr": low_ctr,
            "questions": questions, "decliners": decliners}


# ── AI decision layer ───────────────────────────────────────────────────────────
def ai_actions(site_url, analysis):
    """Groq turns the buckets into a grounded, prioritised SEO action plan."""
    if not groq_available():
        return {"summary": "Connect Groq (GROQ_API_KEY) for the AI action plan.",
                "quick_wins": [], "content_to_create": [], "priorities": []}
    s = analysis
    L = [f"SITE: {site_url}", f"TOTALS: {s['totals']}",
         "\nSTRIKING-DISTANCE queries (rank 8-20 — one push from page 1):"]
    for r in s["striking"][:12]:
        L.append(f"- '{r['query']}' | pos {r['position']:.1f} | {int(r['impressions'])} impr | {int(r['clicks'])} clicks")
    L.append("\nLOW-CTR queries (ranking well but under-clicked — title/meta fix):")
    for r in s["low_ctr"][:10]:
        L.append(f"- '{r['query']}' | pos {r['position']:.1f} | CTR {r['ctr']*100:.1f}% vs ~{r['expected_ctr']*100:.0f}% expected | {int(r['impressions'])} impr")
    L.append("\nQUESTION / informational queries (content-gap candidates):")
    for r in s["questions"][:10]:
        L.append(f"- '{r['query']}' | {int(r['impressions'])} impr | pos {r['position']:.1f}")
    if s["decliners"]:
        L.append("\nDECLINING queries (losing position vs previous period):")
        for r in s["decliners"][:8]:
            L.append(f"- '{r['query']}' | pos {r['position']:.1f} (was {r['prev_position']}) | Δpos {r['pos_delta']}")
    context = "\n".join(L)

    prompt = f"""You are Deconstruct's SEO lead. Below is REAL Google Search Console data for OUR OWN site.
Turn it into a prioritised action plan for the biggest, easiest search wins. Ground EVERY action in the
data by citing the exact query and its metric — never invent queries or numbers.

{context}

Return ONLY JSON:
{{"summary": "3-4 sentences: where the biggest, least-effort search wins are, grounded in the numbers",
 "quick_wins": [{{"query": "", "action": "the specific move", "why": "cite the metric", "suggested_title": "a rewritten <title> tag if it's a CTR/ranking fix, else empty"}}],
 "content_to_create": [{{"topic": "", "target_query": "", "format": "blog / PDP / FAQ / landing page"}}],
 "priorities": ["ordered top 5 things to do first, most impactful first"]}}
JSON only. Start with {{"""
    raw = groq_chat(prompt, system="Output valid JSON only. Start with {.",
                    temperature=0.3, max_tokens=1900)
    try:
        return json.loads(raw[raw.index("{"): raw.rindex("}") + 1])
    except Exception:
        return {"summary": (raw or "AI plan unavailable.")[:600],
                "quick_wins": [], "content_to_create": [], "priorities": []}


# ── excel ───────────────────────────────────────────────────────────────────────
def _df(rows):
    import pandas as pd
    return pd.DataFrame(rows) if rows else pd.DataFrame([{"note": "none found in this period"}])


def to_excel(site_url, analysis, ai, period_label=""):
    try:
        import pandas as pd
    except Exception:
        return None
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xl:
        pd.DataFrame([{"Site": site_url, "Period": period_label, **analysis["totals"]}]
                     ).to_excel(xl, sheet_name="Overview", index=False)
        _df(analysis["striking"]).to_excel(xl, sheet_name="Striking Distance", index=False)
        _df(analysis["low_ctr"]).to_excel(xl, sheet_name="Low-CTR Wins", index=False)
        _df(analysis["questions"]).to_excel(xl, sheet_name="Content Gaps", index=False)
        _df(analysis["decliners"]).to_excel(xl, sheet_name="Decliners", index=False)
        if ai.get("quick_wins"):
            _df(ai["quick_wins"]).to_excel(xl, sheet_name="AI Quick Wins", index=False)
        if ai.get("content_to_create"):
            _df(ai["content_to_create"]).to_excel(xl, sheet_name="AI Content Plan", index=False)
        if ai.get("priorities"):
            pd.DataFrame({"Priority order": ai["priorities"]}).to_excel(
                xl, sheet_name="AI Priorities", index=False)
    return buf.getvalue()


METHODOLOGY = {
    "source": "Google Search Console API (Search Analytics) — first-party data for your VERIFIED property. "
              "Exactly the clicks / impressions / CTR / average position Google records; nothing estimated.",
    "striking": "Queries whose average position is 8–20 — already on/near page 1, so a small on-page push "
                "can win outsized clicks. Sorted by impressions (biggest demand first).",
    "low_ctr": "Queries ranking in the top 10 but earning fewer clicks than a typical result at that "
               "position (position-based CTR curve). These are pure title/meta rewrite wins — the ranking is already there.",
    "content_gaps": "Question / informational queries you already get impressions for but likely have no "
                    "dedicated page targeting — candidates for a blog / FAQ / landing page.",
    "decliners": "Queries whose average position fell (or clicks dropped) vs the previous equal-length period.",
    "ai": "Groq LLM ranks the buckets into a grounded action plan (quick wins, content plan, priorities), "
          "citing the exact query + metric behind each recommendation. It never invents queries or numbers.",
}
