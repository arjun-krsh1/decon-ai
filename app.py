"""
app.py — Decon AI | Market Intelligence Engine
Each department has its own custom tabs and UI.
Run with: python -m streamlit run app.py
"""

import os
from datetime import datetime
"""
app.py — Decon AI | Market Intelligence Engine
Each department has its own custom tabs and UI.
Run with: python -m streamlit run app.py
"""

import json
import streamlit as st

# ── Streamlit Community Cloud: copy st.secrets → os.environ BEFORE importing
#    modules/llm (they read os.getenv at import time). No-op on Render/local,
#    where keys already come from environment variables / .env.
try:
    for _k, _v in st.secrets.items():
        os.environ.setdefault(_k, str(_v))
except Exception:
    pass

from modules import MODULES
from llm import llm_available, DEMO_SAFE
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(
    page_title="Decon AI",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&display=swap');

:root {
    --ink:      #0A0A0A;
    --ink-soft: #1A1A1A;
    --cream:    #F6F5F2;
    --card:     #FFFFFF;
    --line:     #ECEBE6;
    --line-2:   #E2E1DB;
    --muted:    #6B6B6B;
    --faint:    #9A9A96;
    --lime:     #C8F55A;
    --lime-ink: #0A0A0A;
    --salmon:   #F4A99A;
}

/* ── Base ─────────────────────────────────────────────────────────────────── */
html, body, [class*="css"], .stApp, button, input, textarea, select {
    font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    -webkit-font-smoothing: antialiased;
}
#MainMenu, footer, header, [data-testid="stToolbar"] { visibility: hidden; }
.stApp { background: var(--cream); color: var(--ink); }
.block-container { padding-top: 2.4rem; padding-bottom: 3rem; max-width: 1240px; }

/* Headings + text in the main pane */
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5 {
    color: var(--ink) !important;
    font-weight: 600 !important;
    letter-spacing: -0.02em !important;
}
.stApp h2 { font-size: 24px !important; margin-top: 8px !important; }
.stApp h3 { font-size: 19px !important; }
.stApp h4 { font-size: 17px !important; }
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li { color: #2E2E2E; line-height: 1.7; }
[data-testid="stCaptionContainer"], .stCaption { color: var(--muted) !important; }
a, a:visited { color: #0A0A0A; text-decoration: underline; text-underline-offset: 2px; }

/* ── Sidebar ──────────────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: var(--ink);
    border-right: 1px solid #191919;
}
section[data-testid="stSidebar"] * { color: #DCDCDC !important; }
section[data-testid="stSidebar"] hr { border-color: #242424 !important; }
section[data-testid="stSidebar"] [role="radiogroup"] label {
    padding: 4px 0; font-size: 14px; font-weight: 500;
}

/* ── Hero ─────────────────────────────────────────────────────────────────── */
.hero {
    background: var(--ink);
    border: 1px solid #202020;
    border-radius: 18px;
    padding: 34px 40px;
    margin-bottom: 26px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.hero-logo { font-size: 34px; font-weight: 700; color: #fff; letter-spacing: -0.03em; }
.hero-logo span { color: var(--lime); }
.hero-sub { font-size: 13px; color: #8A8A8A; margin-top: 8px; letter-spacing: 0.01em; }
.hero-badge {
    background: rgba(200,245,90,0.10);
    border: 1px solid rgba(200,245,90,0.28);
    color: var(--lime);
    padding: 9px 18px;
    border-radius: 100px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.02em;
}

/* ── Metric cards ─────────────────────────────────────────────────────────── */
.metrics { display: flex; gap: 14px; margin-bottom: 26px; }
.metric {
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 20px 24px;
    flex: 1;
    transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
}
.metric:hover { transform: translateY(-2px); box-shadow: 0 8px 22px rgba(10,10,10,0.06); border-color: var(--line-2); }
.metric-val { font-size: 34px; font-weight: 700; color: var(--ink); line-height: 1.05; letter-spacing: -0.03em; }
.metric-label { font-size: 11px; color: var(--muted); margin-top: 8px; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600; }
.metric-sub { font-size: 11px; color: var(--faint); margin-top: 3px; }

/* ── Department pill ──────────────────────────────────────────────────────── */
.dept-pill {
    display: inline-block; padding: 6px 15px; border-radius: 100px;
    font-size: 11px; font-weight: 600; letter-spacing: 0.03em; margin-bottom: 18px;
    background: #EFEEE9; color: #3A3A3A; border: 1px solid var(--line-2);
}
.dept-supply, .dept-content, .dept-design { background: #EFEEE9; color: #3A3A3A; }

/* ── Cards ────────────────────────────────────────────────────────────────── */
.card {
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 16px;
    padding: 24px 26px;
    margin-bottom: 14px;
    transition: box-shadow .18s ease, border-color .18s ease;
}
.card:hover { box-shadow: 0 8px 24px rgba(10,10,10,0.06); border-color: var(--line-2); }
.card-rank { font-size: 10px; font-weight: 700; color: var(--faint); text-transform: uppercase; letter-spacing: 0.14em; margin-bottom: 6px; }
.card-title { font-size: 20px; font-weight: 600; color: var(--ink); margin-bottom: 12px; letter-spacing: -0.02em; }
.pill {
    display: inline-block; padding: 5px 13px; border-radius: 100px;
    font-size: 12px; font-weight: 600; margin-right: 6px;
}
.pill-score { background: var(--ink); color: var(--lime); }
.pill-cost, .pill-market { background: #F0EFEA; color: #4A4A4A; }
.pill-format { background: #FBE7E2; color: #B4503E; }
.competitor-box {
    background: #FBF3EF; border: 1px solid #F3D9D0; border-radius: 10px;
    padding: 10px 14px; font-size: 13px; color: #9A4B39; margin: 12px 0;
}
.why-text { font-size: 14px; color: #3E3E3E; line-height: 1.75; margin-top: 12px; }

/* ── Idea cards ───────────────────────────────────────────────────────────── */
.idea-card {
    background: var(--card); border: 1px solid var(--line);
    border-left: 3px solid var(--lime); border-radius: 14px;
    padding: 20px 24px; margin-bottom: 12px;
}
.idea-title { font-size: 16px; font-weight: 600; color: var(--ink); margin-bottom: 6px; }
.idea-meta { font-size: 12px; color: var(--faint); margin-bottom: 8px; }
.idea-desc { font-size: 14px; color: #3E3E3E; line-height: 1.65; }
.chatgpt-box {
    background: #F4FAE9; border: 1px solid #DCEFB5; border-radius: 10px;
    padding: 12px 16px; margin-top: 12px; font-size: 12px; color: #4C6B1F;
}

/* ── Trend cards ──────────────────────────────────────────────────────────── */
.trend-card {
    background: var(--card); border: 1px solid var(--line);
    border-radius: 14px; padding: 20px 24px; margin-bottom: 12px;
}
.trend-market-hdr {
    font-size: 15px; font-weight: 600; color: var(--ink);
    margin: 24px 0 12px 0; padding-bottom: 8px; border-bottom: 1.5px solid var(--ink);
    display: flex; align-items: center; justify-content: space-between;
}
.trend-signal { font-size: 15px; font-weight: 600; color: var(--ink); }
.trend-note { font-size: 13px; color: var(--muted); margin-top: 5px; line-height: 1.65; }
.trend-opp {
    background: #F4FAE9; border: 1px solid #DCEFB5; border-radius: 8px;
    padding: 8px 14px; font-size: 13px; color: #4C6B1F; margin-top: 10px;
}

/* ── Status badges ────────────────────────────────────────────────────────── */
.badge {
    display: inline-block; padding: 3px 11px; border-radius: 100px;
    font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em;
}
.b-early { background: #EAF6D6; color: #4C6B1F; }
.b-emerging { background: #FBF1D6; color: #85601A; }
.b-mainstream { background: #FBE7DC; color: #99441F; }
.b-saturated { background: #FADFDA; color: #97362B; }

/* ── Tabs ─────────────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px; background: #EBEAE4; padding: 5px; border-radius: 12px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 9px; padding: 8px 20px; font-weight: 500; font-size: 13.5px; color: var(--muted);
}
.stTabs [aria-selected="true"] {
    background: #fff !important; color: var(--ink) !important; font-weight: 600 !important;
    box-shadow: 0 1px 3px rgba(10,10,10,0.10);
}

/* ── Buttons ──────────────────────────────────────────────────────────────── */
.stButton > button, .stDownloadButton > button {
    background: var(--ink) !important; color: #fff !important;
    border: 1px solid var(--ink) !important; border-radius: 10px !important;
    font-weight: 600 !important; font-size: 14px !important; padding: 10px 26px !important;
    transition: all .18s ease !important; letter-spacing: 0.01em !important;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    background: var(--ink-soft) !important; transform: translateY(-1px) !important;
    box-shadow: 0 6px 16px rgba(10,10,10,0.16) !important;
}
.stButton > button[kind="primary"] { background: var(--ink) !important; }
.stButton > button[kind="secondary"] {
    background: #fff !important; color: var(--ink) !important; border: 1.5px solid var(--ink) !important;
}

/* ── Inputs ───────────────────────────────────────────────────────────────── */
.stTextInput input, .stTextArea textarea, .stNumberInput input {
    border-radius: 10px !important; border: 1px solid var(--line-2) !important;
    background: #fff !important; color: var(--ink) !important; font-size: 14px !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: var(--ink) !important; box-shadow: 0 0 0 3px rgba(200,245,90,0.30) !important;
}
[data-baseweb="select"] > div {
    border-radius: 10px !important; border-color: var(--line-2) !important; background: #fff !important;
}
.stSlider [data-baseweb="slider"] [role="slider"] { background: var(--ink) !important; }
.stSlider [data-testid="stTickBarMin"], .stSlider [data-testid="stTickBarMax"] { color: var(--faint) !important; }

/* Progress bar + spinner in brand lime */
.stProgress > div > div > div { background: var(--lime) !important; }

/* Expander */
div[data-testid="stExpander"] {
    background: #fff; border: 1px solid var(--line) !important; border-radius: 12px !important;
}
div[data-testid="stExpander"] summary { font-weight: 600; color: var(--ink); }

/* Section label helper */
.sec-label {
    font-size: 10px; font-weight: 700; color: var(--faint);
    text-transform: uppercase; letter-spacing: 0.16em; margin: 4px 0 10px;
}
</style>
""", unsafe_allow_html=True)


# ── helpers ───────────────────────────────────────────────────────────────────
def platform_metrics():
    """Headline platform stats — honest, no fabricated volumes."""
    tools = len(MODULES)
    keys = [os.getenv(k, "") for k in
            ("GROQ_API_KEY", "SERPAPI_KEY", "APIFY_KEY", "MAGNIFIC_API_KEY")]
    live_sources = sum(1 for k in keys if k)
    return tools, 6, 6, live_sources   # tools, competitor brands, markets, live sources


# ── sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:16px 0 24px;">
        <div style="font-size:24px;font-weight:800;letter-spacing:-0.5px;">
            🧬 Decon <span style="color:#C8F55A;">AI</span>
        </div>
        <div style="font-size:11px;color:#555;margin-top:4px;">Market Intelligence Engine</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="font-size:10px;color:#444;text-transform:uppercase;letter-spacing:1.5px;font-weight:700;margin-bottom:10px;">Department</div>', unsafe_allow_html=True)
    choice = st.radio("", [m.label for m in MODULES], label_visibility="collapsed")
    module = next(m for m in MODULES if m.label == choice)

    dept_colors = {"Supply Chain": "dept-supply", "Content / Social": "dept-content", "Design / Creative": "dept-design"}
    st.markdown(f'<span class="dept-pill {dept_colors.get(module.department,"dept-supply")}">{module.department}</span>', unsafe_allow_html=True)

    st.divider()
    st.markdown('<div style="font-size:10px;color:#444;text-transform:uppercase;letter-spacing:1.5px;font-weight:700;margin-bottom:10px;">System</div>', unsafe_allow_html=True)

    if DEMO_SAFE:
        st.markdown('<div style="background:#0D2A0D;color:#C8F55A !important;padding:7px 12px;border-radius:8px;font-size:11px;font-weight:600;margin-bottom:12px;">⚡ DEMO SAFE MODE</div>', unsafe_allow_html=True)

    _engines = [
        ("Gemini",   "Content Market probes",   bool(os.getenv("GEMINI_API_KEY", ""))),
        ("Groq",     "Analysis & extraction",   llm_available()),
        ("SerpAPI",  "Search · Amazon",         bool(os.getenv("SERPAPI_KEY", ""))),
        ("Apify",    "Instagram · Brand Media", bool(os.getenv("APIFY_KEY", ""))),
        ("Magnific", "Image gen · Design",      bool(os.getenv("MAGNIFIC_API_KEY", ""))),
    ]
    _rows = ""
    for _name, _role, _ok in _engines:
        _dot = "#C8F55A" if _ok else "#3A3A3A"
        _glow = "box-shadow:0 0 7px rgba(200,245,90,0.65);" if _ok else ""
        _status = "LIVE" if _ok else "OFF"
        _stxt = "#C8F55A" if _ok else "#6A6A6A"
        _rows += (
            '<div style="display:flex;align-items:center;gap:9px;margin-bottom:11px;">'
            f'<span style="width:8px;height:8px;border-radius:50%;background:{_dot};{_glow}flex-shrink:0;"></span>'
            '<div style="flex:1;line-height:1.25;">'
            f'<div style="font-size:12px;font-weight:600;color:#ECECEC !important;">{_name}</div>'
            f'<div style="font-size:10px;color:#7C7C7C !important;">{_role}</div></div>'
            f'<span style="font-size:9px;font-weight:700;letter-spacing:0.08em;color:{_stxt} !important;">{_status}</span>'
            '</div>'
        )
    st.markdown(_rows, unsafe_allow_html=True)

    st.divider()
    st.markdown('<div style="font-size:10px;color:#444;text-transform:uppercase;letter-spacing:1.5px;font-weight:700;margin-bottom:12px;">Scoring Model</div>', unsafe_allow_html=True)
    for k, v in module.weights.items():
        pct = int(v*100)
        st.markdown(f"""
        <div style="margin-bottom:10px;">
            <div style="display:flex;justify-content:space-between;font-size:11px;color:#888;margin-bottom:4px;">
                <span>{k.replace("_"," ").title()}</span>
                <span style="color:#C8F55A;font-weight:700;">{pct}%</span>
            </div>
            <div style="background:#222;border-radius:4px;height:4px;">
                <div style="background:linear-gradient(90deg,#C8F55A,#8BC34A);width:{min(pct*3,100)}%;height:4px;border-radius:4px;"></div>
            </div>
        </div>""", unsafe_allow_html=True)


# ── hero + metrics ────────────────────────────────────────────────────────────
tools_n, brands_n, markets_n, sources_n = platform_metrics()

st.markdown(f"""
<div class="hero">
    <div>
        <div class="hero-logo">Decon <span>AI</span></div>
        <div class="hero-sub">Market Intelligence Engine &nbsp;·&nbsp; {module.department} &nbsp;·&nbsp; {module.label}</div>
    </div>
    <div class="hero-badge">🧬 Science-driven decisions</div>
</div>
<div class="metrics">
    <div class="metric">
        <div class="metric-val">{tools_n}</div>
        <div class="metric-label">AI Tools Live</div>
        <div class="metric-sub">One engine, many teams</div>
    </div>
    <div class="metric">
        <div class="metric-val">{brands_n}</div>
        <div class="metric-label">Competitor Brands</div>
        <div class="metric-sub">India D2C skincare</div>
    </div>
    <div class="metric">
        <div class="metric-val">{sources_n}</div>
        <div class="metric-label">Live Data Sources</div>
        <div class="metric-sub">API keys connected</div>
    </div>
    <div class="metric">
        <div class="metric-val">{markets_n}</div>
        <div class="metric-label">Markets Monitored</div>
        <div class="metric-sub">🇰🇷 🇺🇸 🇨🇳 🇫🇷 🇬🇧 🇦🇪</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# MARKET CONTENT VISIBILITY (GEO AGENT)
# ══════════════════════════════════════════════════════════════════════════════
if module.key == "geo":
    from agents.geo import run as geo_run, GeoInput
    from agents.geo.questions import build_questions
    from agents.geo.storage import load_history
    from agents.geo.probes import GeminiProber, SerpGroqProber

    gemini_ok = GeminiProber().available()
    serp_ok = SerpGroqProber().available()

    tab1, tab2 = st.tabs(["🔍  Market Scan", "📈  Trend"])

    with tab1:
        st.markdown("#### 🔍 Are you visible when shoppers ask AI?")
        st.caption("Shoppers ask ChatGPT / Gemini / Perplexity for product picks and buy what they're told. "
                   "This probes real AI assistants with buyer questions, measures where Deconstruct ranks, and "
                   "returns a number-backed plan to get recommended. Only unbranded discovery questions count toward the score.")

        if gemini_ok:
            engine_note = "✅ Gemini (real Google-grounded engine) connected — highest-fidelity probes"
        elif serp_ok:
            engine_note = "✅ SerpAPI + Groq proxy connected — add GEMINI_API_KEY for real-engine fidelity"
        else:
            engine_note = "⚠️ No live engine key — running in mock mode. Add GEMINI_API_KEY (free) or SERPAPI_KEY + GROQ_API_KEY."
        st.markdown(f'<div style="background:#0A0A0A;border-radius:12px;padding:12px 18px;margin-bottom:16px;color:#C8F55A;font-size:12px;font-weight:600;">{engine_note}</div>', unsafe_allow_html=True)

        col1, col2 = st.columns([2, 1])
        with col1:
            geo_cat = st.text_input("Product category", value="Sunscreen", key="geo_cat")
            geo_comp = st.text_area("Tracked competitors (comma-separated)",
                                    value="Minimalist, Dot & Key, The Derma Co, Foxtale, Aqualogica, Dr. Sheth's",
                                    height=80, key="geo_comp")
        with col2:
            prov_opts = ["auto"]
            if gemini_ok:
                prov_opts.append("gemini")
            if serp_ok:
                prov_opts.append("serpgroq")
            prov_opts.append("mock")
            geo_prov = st.selectbox("AI engine to probe", prov_opts, key="geo_prov")
            geo_nq = st.slider("Discovery questions", 4, 10, 6, key="geo_nq")

        if st.button("🚀 Run Market Scan", type="primary", key="geo_run_btn"):
            competitors = [c.strip() for c in geo_comp.split(",") if c.strip()]
            questions = build_questions("Deconstruct", geo_cat, competitors, n_unbranded=geo_nq)
            gi = GeoInput(brand="Deconstruct", category=geo_cat, competitors=competitors,
                          questions=questions, models=[geo_prov])

            progress_bar = st.progress(0)
            status = st.empty()

            def geo_progress(done, total, msg):
                progress_bar.progress(min(int(done / max(total, 1) * 100), 99))
                status.markdown(f"⚙️ {msg}")

            with st.spinner("Probing AI engines... (mystery-shopper mode)"):
                out = geo_run(gi, progress_cb=geo_progress)
            progress_bar.progress(100)
            status.markdown(f"✅ Done — {out.unbrandedCount} discovery questions graded via {', '.join(out.modelsUsed)}")
            st.session_state["geo_out"] = out.to_dict()

        out = st.session_state.get("geo_out")
        if out:
            top_comp = next((b for b in out["brandRanking"] if b["brand"].lower() != "deconstruct"), None)
            top_comp_label = f'{top_comp["brand"]} ({top_comp["count"]})' if top_comp else "—"
            st.markdown(f'''
            <div class="metrics" style="margin-top:8px;">
                <div class="metric"><div class="metric-val">{out["shortlistRate"]}%</div>
                    <div class="metric-label">Shortlist Rate</div><div class="metric-sub">Top-3 on discovery Qs</div></div>
                <div class="metric"><div class="metric-val">{out["longlistOnly"]}%</div>
                    <div class="metric-label">Long-list Only</div><div class="metric-sub">Ranked #4+ (invisible)</div></div>
                <div class="metric"><div class="metric-val" style="font-size:22px;">{top_comp_label}</div>
                    <div class="metric-label">AI's Top Pick</div><div class="metric-sub">Most-recommended rival</div></div>
                <div class="metric"><div class="metric-val">{out["unbrandedCount"]}</div>
                    <div class="metric-label">Questions Graded</div><div class="metric-sub">Branded excluded: {out["brandedCount"]}</div></div>
            </div>''', unsafe_allow_html=True)

            try:
                import plotly.graph_objects as go
                colA, colB = st.columns(2)
                with colA:
                    br = out["brandRanking"][:8]
                    if br:
                        names = [b["brand"] for b in br]
                        counts = [b["count"] for b in br]
                        colors = ["#C8F55A" if n.lower() == "deconstruct" else "#BEBCB3" for n in names]
                        figb = go.Figure(go.Bar(x=counts, y=names, orientation="h",
                                                marker_color=colors, text=counts, textposition="outside"))
                        figb.update_layout(title="Who AI recommends most (top-3 hits)", height=340,
                                           paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                           font=dict(family="DM Sans", color="#0A0A0A"),
                                           yaxis=dict(autorange="reversed"), margin=dict(l=10, r=10))
                        st.plotly_chart(figb, use_container_width=True)
                with colB:
                    mix = out["sourceTypeMix"]
                    if mix:
                        figm = go.Figure(go.Bar(x=[m["type"] for m in mix], y=[m["pct"] for m in mix],
                                                marker_color="#C8F55A",
                                                text=[f'{m["pct"]}%' for m in mix], textposition="outside"))
                        figm.update_layout(title="Where AI pulls answers from (where to post)", height=340,
                                           paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                           font=dict(family="DM Sans", color="#0A0A0A"),
                                           margin=dict(l=10, r=10))
                        st.plotly_chart(figm, use_container_width=True)
            except ImportError:
                st.info("Install plotly for charts: `pip install plotly`")

            st.markdown("### 📋 Playbook")
            st.markdown(out["playbook"])

            with st.expander("Per-question detail — what AI actually said"):
                for r in out["perQuestion"]:
                    tag = "🔒 branded" if r["branded"] else "🔍 discovery"
                    pos = f'#{r["position"]}' if r["position"] else "absent"
                    err = f' · ⚠️ {r["error"]}' if r["error"] else ""
                    st.markdown(f'**{tag}** · Deconstruct: **{pos}** · _{r["question"]}_{err}')
                    if r["rankedBrands"]:
                        st.caption("AI ranked: " + " → ".join(r["rankedBrands"][:6]))

            st.download_button("📥 Download full report (JSON)",
                               data=json.dumps(out, indent=2, ensure_ascii=False).encode("utf-8"),
                               file_name=f"decon_geo_{out['category'].replace(' ', '_')}.json",
                               mime="application/json", key="geo_dl")

    with tab2:
        st.markdown("#### 📈 Content Market Trend")
        st.caption("AI citations swing week to week — track shortlist rate across repeated (e.g. weekly) runs.")
        hist = load_history("Deconstruct", st.session_state.get("geo_cat", ""))
        if len(hist) < 2:
            st.info("Need at least 2 saved runs to show a trend. Each scan is saved automatically — run it weekly.")
        else:
            try:
                import plotly.graph_objects as go
                hist_sorted = list(reversed(hist))
                x = [h.get("generatedAt", "")[:16] for h in hist_sorted]
                y = [h.get("shortlistRate", 0) for h in hist_sorted]
                figt = go.Figure(go.Scatter(x=x, y=y, mode="lines+markers",
                                            line_color="#0A0A0A", marker=dict(color="#C8F55A", size=9)))
                figt.update_layout(title="Shortlist rate over time (%)", height=360,
                                   paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                   font=dict(family="DM Sans", color="#0A0A0A"),
                                   yaxis=dict(range=[0, 100]))
                st.plotly_chart(figt, use_container_width=True)
            except ImportError:
                for h in hist:
                    st.markdown(f'- {h.get("generatedAt", "")[:16]} — {h.get("shortlistRate", 0)}%')


# ══════════════════════════════════════════════════════════════════════════════
# DESIGN INTELLIGENCE
# ══════════════════════════════════════════════════════════════════════════════


elif module.key == "design":
    from image_gen import (generate_image, generate_image_multi, build_swap_prompt,
                           nearest_aspect_ratio, PRO_MODEL, FLASH_MODEL)
    from brand_guidelines import guidelines_to_prompt_injection

    PLATFORMS = {
        "Instagram Post (1:1)":   {"ar": "1:1",  "label": "1080x1080px"},
        "Instagram Story (9:16)": {"ar": "9:16", "label": "1080x1920px"},
        "Instagram Reel (9:16)":  {"ar": "9:16", "label": "1080x1920px"},
        "Website Banner (16:9)":  {"ar": "16:9", "label": "1920x1080px"},
        "Ad Creative (4:5)":      {"ar": "4:5",  "label": "1080x1350px"},
        "Packaging Mockup (1:1)": {"ar": "1:1",  "label": "1080x1080px"},
    }

    TEXT_ZONES = {
        "No text zone — product fills frame": "",
        "Text top — product bottom half":     "Leave the top 35% completely empty for text overlay. Place the subject in the lower 60% of the frame.",
        "Text bottom — product top half":     "Leave the bottom 30% completely empty for text overlay. Place the subject in the upper 60% of the frame.",
        "Text left — product right side":     "Leave the entire left 45% completely empty for text overlay. Place the subject on the right side of the frame.",
        "Text right — product left side":     "Leave the entire right 45% completely empty for text overlay. Place the subject on the left side of the frame.",
        "Diagonal — text top-left, product bottom-right": "Place the subject in the bottom-right area. Leave the top-left 50% completely empty for text.",
    }

    tab1, tab2, tab3, tab4 = st.tabs(["🖼️  Edit / Generate", "✨  Text to Image",
                                      "🔄  Replace Product in Scene", "🔒  Logo Lock"])

    # ── TAB 1: IMAGE EDITING ──────────────────────────────────────────────────
    with tab1:
        st.markdown("#### 🖼️ Edit or Generate with Reference Image")
        st.markdown("""
        <div style="background:#0A0A0A;border-radius:12px;padding:14px 20px;margin-bottom:16px;">
            <div style="font-size:13px;font-weight:700;color:#C8F55A;margin-bottom:8px;">HOW THIS WORKS</div>
            <div style="display:flex;gap:20px;">
                <div style="flex:1;font-size:12px;color:#CCC;line-height:1.7;">
                    <b style="color:white;">With reference image:</b><br>
                    Nano Banana reads YOUR exact image and edits it per your instruction.
                    The original is preserved — only what you ask changes.
                    e.g. "Remove the products from the shelf" keeps the shelf intact.
                </div>
                <div style="flex:1;font-size:12px;color:#CCC;line-height:1.7;">
                    <b style="color:white;">Without reference image:</b><br>
                    Generates a new image from scratch based on your prompt.
                    Brand guidelines are applied automatically.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_l, col_r = st.columns([1, 1])

        with col_l:
            st.markdown("**1. Upload your main image**")
            st.caption("The subject to edit or the product to place in a scene")
            ref_img = st.file_uploader(
                "Main image",
                type=["jpg", "jpeg", "png", "webp"],
                label_visibility="collapsed",
                key="d_ref_img"
            )
            if ref_img:
                st.image(ref_img, use_container_width=True)
                st.success("✅ Main image loaded")
            else:
                st.info("No image — will generate from scratch")

            st.markdown("**2. Upload inspiration/reference (optional)**")
            st.caption("Nano Banana will apply the style, mood, or lighting from this image")
            insp_img = st.file_uploader(
                "Inspiration image",
                type=["jpg", "jpeg", "png", "webp"],
                label_visibility="collapsed",
                key="d_insp_img"
            )
            if insp_img:
                st.image(insp_img, use_container_width=True)
                st.success("✅ Inspiration image loaded — style will be applied")

        with col_r:
            st.markdown("**3. What do you want?**")
            if ref_img and insp_img:
                st.caption("Tell it how to combine both images")
                user_prompt = st.text_area(
                    "Instruction",
                    placeholder="e.g. Apply the lighting and mood from the inspiration to my product",
                    height=160,
                    label_visibility="collapsed",
                    key="d_prompt_both"
                )
            elif ref_img:
                st.caption("Describe what to change in your uploaded image")
                user_prompt = st.text_area(
                    "Instruction",
                    placeholder="e.g. Remove products from shelf but keep the shelf intact",
                    height=160,
                    label_visibility="collapsed",
                    key="d_prompt_edit"
                )
            else:
                st.caption("Describe the image you want to create")
                user_prompt = st.text_area(
                    "Prompt",
                    placeholder="e.g. Deconstruct serum bottle floating on clouds with golden light",
                    height=160,
                    label_visibility="collapsed",
                    key="d_prompt_gen"
                )

        col_p, col_r2, col_t = st.columns(3)
        platform = col_p.selectbox("Platform", list(PLATFORMS.keys()), key="d_platform")
        resolution = col_r2.selectbox("Resolution", ["1K", "2K", "4K"], key="d_res")
        text_zone = col_t.selectbox("Text placement", list(TEXT_ZONES.keys()), key="d_zone")

        st.caption(f"📐 {PLATFORMS[platform]['label']} · {PLATFORMS[platform]['ar']}")
        st.markdown("")

        if st.button("🖼️ Generate", type="primary", key="d_gen", use_container_width=True):
            prompt_val = user_prompt if user_prompt else ""
            if not prompt_val.strip():
                st.error("Write a prompt or instruction first.")
            else:
                # build final prompt
                zone_text = TEXT_ZONES.get(text_zone, "")
                guidelines = guidelines_to_prompt_injection(platform)

                if ref_img:
                    # editing mode — keep prompt clean and direct
                    final_prompt = prompt_val.strip()
                    if zone_text:
                        final_prompt += f" Additionally: {zone_text}"
                    ref_bytes = ref_img.read()
                    mime = f"image/{ref_img.name.split('.')[-1].lower().replace('jpg','jpeg')}"
                    ref_instruction = f"This is the base image. Edit it per the prompt. Keep everything NOT mentioned in the prompt exactly as it is."
                else:
                    # generation mode — inject brand guidelines
                    final_prompt = prompt_val.strip()
                    if zone_text:
                        final_prompt += "\n\nTEXT ZONE: " + zone_text
                    final_prompt += "\n\nStyle: clean, clinical, minimal. " + guidelines[:300]
                    ref_bytes = None
                    ref_instruction = ""
                    mime = "image/jpeg"

                mode_label = "editing your reference image" if ref_img else "generating from scratch"
                with st.spinner(f"Nano Banana is {mode_label}... (~15-20 sec)"):
                    result = generate_image(
                        prompt=final_prompt,
                        aspect_ratio=PLATFORMS[platform]["ar"],
                        resolution=resolution,
                        reference_image_bytes=ref_bytes,
                        reference_mime=mime,
                        reference_instruction=ref_instruction
                    )

                if result.get("image_url"):
                    mode = result.get("mode","")
                    if mode == "multi_image_reference":
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            st.markdown("**Your product**")
                            ref_img.seek(0)
                            st.image(ref_img.read(), use_container_width=True)
                        with c2:
                            st.markdown("**Inspiration**")
                            insp_img.seek(0)
                            st.image(insp_img.read(), use_container_width=True)
                        with c3:
                            st.markdown("**Result ✅**")
                            st.image(result["image_url"], use_container_width=True)
                    elif ref_img:
                        c1, c2 = st.columns(2)
                        with c1:
                            st.markdown("**Before**")
                            ref_img.seek(0)
                            st.image(ref_img.read(), use_container_width=True)
                        with c2:
                            st.markdown("**After ✅**")
                            st.image(result["image_url"], use_container_width=True)
                    else:
                        st.image(result["image_url"], use_container_width=True)

                    st.markdown(f"""
                    <div style="background:#0A0A0A;border-radius:10px;padding:10px 16px;margin-top:8px;">
                        <div style="font-size:11px;color:#C8F55A;font-weight:700;">
                            ✅ {result.get('mode','').replace('_',' ').upper()} · Nano Banana Pro Flash
                            · {platform} · {resolution}
                            {'· from cache' if result.get('cached') else '· fresh generation'}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    try:
                        import requests as _req
                        img_bytes = _req.get(result["image_url"], timeout=30).content
                        st.download_button(
                            "📥 Download",
                            data=img_bytes,
                            file_name=f"decon_{result.get('mode','gen')}_{resolution}.jpg",
                            mime="image/jpeg"
                        )
                    except Exception:
                        st.info(f"[Open image]({result['image_url']})")
                else:
                    st.error(f"Failed: {result.get('error','Unknown error')}")

    # ── TAB 3: REPLACE PRODUCT IN SCENE ──────────────────────────────────────
    with tab3:
        st.markdown("#### 🔄 Replace Product in Scene")
        st.markdown("""
        <div style="background:#0A0A0A;border-radius:12px;padding:14px 20px;margin-bottom:16px;">
            <div style="font-size:13px;font-weight:700;color:#C8F55A;margin-bottom:8px;">HOW THIS WORKS</div>
            <div style="font-size:12px;color:#CCC;line-height:1.8;">
                Upload a <b style="color:white;">scene image</b> (e.g. hand holding a product, shelf, flat lay) →
                Upload your <b style="color:white;">new product</b> to place in that scene →
                Nano Banana <b style="color:white;">Pro</b> replaces the original product with yours while keeping
                <b style="color:white;">everything else exactly the same</b> —
                the hand, background, lighting, composition, shadows. Every render is then
                <b style="color:#C8F55A;">auto-checked letter-for-letter</b> against your product photo, and it
                <b style="color:#C8F55A;">re-renders until the label text passes</b> — no more manual retries.
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_s1, col_s2 = st.columns(2)

        with col_s1:
            st.markdown("**1. Scene image** (the full photo to edit)")
            st.caption("The image containing the product you want to replace")
            scene_img = st.file_uploader(
                "Scene", type=["jpg","jpeg","png","webp"],
                label_visibility="collapsed", key="rp_scene"
            )
            if scene_img:
                st.image(scene_img, use_container_width=True)
                st.success("✅ Scene loaded")

        with col_s2:
            st.markdown("**2. Your product** (what to put in the scene)")
            st.caption("This product will replace the existing one in the scene")
            new_product_img = st.file_uploader(
                "New product", type=["jpg","jpeg","png","webp"],
                label_visibility="collapsed", key="rp_product"
            )
            if new_product_img:
                st.image(new_product_img, use_container_width=True)
                st.success("✅ New product loaded")

        st.markdown("**3. Extra instruction (optional)**")
        extra_instr = st.text_input(
            "Extra",
            placeholder="e.g. Match the lighting angle to the original product, keep the hand position identical",
            label_visibility="collapsed",
            key="rp_extra"
        )

        col_rp1, col_rp2 = st.columns(2)
        rp_platform = col_rp1.selectbox("Format", list(PLATFORMS.keys()), key="rp_platform")
        rp_res = col_rp2.selectbox("Resolution", ["1K", "2K", "4K"], index=1, key="rp_res")
        rp_max = st.slider(
            "Max attempts — keeps re-rendering until the label text passes QC, then stops early "
            "(a clean render costs just 1 attempt)",
            1, 6, 4, key="rp_passes")
        cbo1, cbo2 = st.columns(2)
        rp_match = cbo1.checkbox("Match the scene's shape (keeps the product's size & position accurate)",
                                 value=True, key="rp_match")
        rp_pro = cbo2.checkbox("Maximum text fidelity (Pro model — slower, sharpest small text)",
                               value=True, key="rp_pro")
        st.caption("💡 Each render is auto-checked letter-for-letter against your product photo (Gemini) and "
                   "the tool **stops at the first render that passes** — so it does your manual retries "
                   "automatically without wasting tokens. Pro model + 4K give the sharpest small text; a "
                   "pre-run replays instantly from cache.")

        st.markdown("")
        if st.button("🔄 Replace Product", type="primary", key="rp_generate", use_container_width=True):
            if not scene_img:
                st.error("Upload the scene image first.")
            elif not new_product_img:
                st.error("Upload your new product image.")
            else:
                scene_bytes = scene_img.read()
                product_bytes = new_product_img.read()
                scene_mime = f"image/{scene_img.name.split('.')[-1].lower().replace('jpg','jpeg')}"
                product_mime = f"image/{new_product_img.name.split('.')[-1].lower().replace('jpg','jpeg')}"

                from image_gen import _SWAP_SCENE_INSTRUCTION, _SWAP_PRODUCT_INSTRUCTION
                from text_verify import verify_label_fidelity, PASS_THRESHOLD
                base_instruction = build_swap_prompt(extra_instr)
                rp_ar = nearest_aspect_ratio(scene_bytes) if rp_match else PLATFORMS[rp_platform]["ar"]
                images_payload = [
                    {"bytes": scene_bytes, "mime": scene_mime, "instruction": _SWAP_SCENE_INSTRUCTION},
                    {"bytes": product_bytes, "mime": product_mime, "instruction": _SWAP_PRODUCT_INSTRUCTION},
                ]

                rp_model = PRO_MODEL if rp_pro else FLASH_MODEL
                model_label = "Nano Banana Pro" if rp_pro else "Nano Banana Pro Flash"

                prog = st.progress(0)
                stat = st.empty()
                candidates = []   # list of (result, verdict)
                passed_on = None  # 1-based attempt that first passed QC (None = none passed)
                for i in range(rp_max):
                    stat.markdown(f"⚙️ Rendering attempt {i+1} of up to {rp_max} "
                                  f"({model_label} · {rp_res})…")
                    res = generate_image_multi(
                        prompt=base_instruction,
                        aspect_ratio=rp_ar,
                        resolution=rp_res,
                        images=images_payload,
                        variant=i,
                        model=rp_model,
                    )
                    if res.get("image_url"):
                        stat.markdown(f"🔎 Auto-checking the label letter-for-letter against your "
                                      f"product photo (attempt {i+1})…")
                        verdict = verify_label_fidelity(product_bytes, product_mime, res["image_url"])
                        candidates.append((res, verdict))
                        sc = verdict.get("score")
                        # Stop the instant a render passes QC — this is the token/time saver.
                        if isinstance(sc, int) and sc >= PASS_THRESHOLD:
                            passed_on = i + 1
                            prog.progress(100)
                            break
                        # No verifier available (no Gemini key) → can't judge, so don't loop blindly.
                        if sc is None:
                            break
                    prog.progress(int((i + 1) / rp_max * 100))
                prog.empty()
                stat.empty()

                if not candidates:
                    st.error("All render attempts failed. Check your Magnific key/quota and retry.")
                    st.info("Tip: the scene image should clearly show a product that can be replaced.")
                else:
                    # auto-select the most text-accurate candidate (unverified = -1)
                    def _score(cv):
                        s = cv[1].get("score")
                        return s if isinstance(s, int) else -1
                    candidates.sort(key=_score, reverse=True)
                    best_res, best_v = candidates[0]
                    score = best_v.get("score")

                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.markdown("**Original scene**")
                        scene_img.seek(0)
                        st.image(scene_img.read(), use_container_width=True)
                    with c2:
                        st.markdown("**New product**")
                        new_product_img.seek(0)
                        st.image(new_product_img.read(), use_container_width=True)
                    with c3:
                        st.markdown("**Result ✅**")
                        st.image(best_res["image_url"], use_container_width=True)

                    # ── text-fidelity badge ──
                    if score is None:
                        bg, txt, msg = ("#1A1A1A", "#C8F55A",
                                        "Text fidelity: unverified — add GEMINI_API_KEY to enable auto-QC")
                    elif score >= PASS_THRESHOLD:
                        _att = f" on attempt {passed_on}" if passed_on else ""
                        bg, txt, msg = ("#0D2A0D", "#C8F55A",
                                        f"Text fidelity {score}/100 · PASS ✓{_att} — safe to present")
                    else:
                        bg, txt, msg = ("#2A0D0D", "#FCA5A5",
                                        f"Text fidelity {score}/100 · best of {len(candidates)} — review before presenting")
                    st.markdown(f"""
                    <div style="background:{bg};border-radius:10px;padding:11px 16px;margin-top:8px;">
                        <div style="font-size:12px;color:{txt};font-weight:700;">🔎 {msg}</div>
                        <div style="font-size:10px;color:#9A9A9A;margin-top:3px;">
                            {len(candidates)} attempt(s) · {model_label} · {rp_platform} · {rp_res}
                            {'· from cache' if best_res.get('cached') else '· fresh'}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    if score is not None and score < PASS_THRESHOLD:
                        issues = best_v.get("issues", [])
                        st.warning(f"⚠️ Tried {len(candidates)} render(s) and none passed QC — showing the "
                                   "closest. Turn on the Pro model, raise max attempts / go to 4K, or upload "
                                   "a sharper, straight-on product photo (small text needs to be legible in the source).")
                        if issues:
                            st.markdown("**Detected text problems:**")
                            for it in issues[:6]:
                                st.markdown(f"- {it}")

                    try:
                        import requests as _req
                        img_bytes = _req.get(best_res["image_url"], timeout=30).content
                        st.session_state["ll_base_bytes"] = img_bytes  # for Logo Lock tab
                        st.download_button("📥 Download Result", data=img_bytes,
                                           file_name=f"decon_replaced_{rp_res}.jpg",
                                           mime="image/jpeg", key="rp_dl")
                        st.caption("🔒 Curved/tiny label text still off? Open the **Logo Lock** tab — "
                                   "it pastes your exact badge onto this result for guaranteed-perfect text.")
                    except Exception:
                        st.info(f"[Open image]({best_res['image_url']})")

                    # ── all candidates + scores ──
                    if len(candidates) > 1:
                        with st.expander(f"Compare all {len(candidates)} candidates"):
                            cols = st.columns(len(candidates))
                            for idx, ((res, v), col) in enumerate(zip(candidates, cols), 1):
                                sc = v.get("score")
                                tag = "★ selected" if idx == 1 else f"#{idx}"
                                col.image(res["image_url"], use_container_width=True)
                                col.caption(f"{tag} · fidelity {sc if sc is not None else '—'}")

    # ── TAB 2: TEXT TO IMAGE ──────────────────────────────────────────────────
    with tab2:
        st.markdown("#### ✨ Text to Image")
        st.caption("Pure creative generation. No reference image. Write what you want, get it.")

        t2i_prompt = st.text_area(
            "Describe your image",
            placeholder="e.g. Aerial view of skincare ingredients on white marble",
            height=120,
            key="t2i_prompt"
        )

        c1, c2, c3 = st.columns(3)
        t2i_platform = c1.selectbox("Format", list(PLATFORMS.keys()), key="t2i_platform")
        t2i_res = c2.selectbox("Resolution", ["1K", "2K", "4K"], key="t2i_res")
        t2i_zone = c3.selectbox("Text placement", list(TEXT_ZONES.keys()), key="t2i_zone")

        st.markdown("")
        if st.button("✨ Generate", type="primary", key="t2i_gen", use_container_width=True):
            if not t2i_prompt.strip():
                st.error("Write a prompt first.")
            else:
                zone = TEXT_ZONES.get(t2i_zone, "")
                fp = t2i_prompt.strip()
                if zone:
                    fp += f" {zone}"

                with st.spinner("Generating with Nano Banana Pro Flash..."):
                    result = generate_image(
                        prompt=fp,
                        aspect_ratio=PLATFORMS[t2i_platform]["ar"],
                        resolution=t2i_res
                    )

                if result.get("image_url"):
                    st.image(result["image_url"], use_container_width=True)
                    st.markdown(f"""
                    <div style="background:#0A0A0A;border-radius:10px;padding:10px 14px;margin-top:6px;">
                        <div style="font-size:11px;color:#C8F55A;font-weight:700;">
                            ✅ TEXT TO IMAGE · Nano Banana Pro Flash · {t2i_platform} · {t2i_res}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    try:
                        import requests as _req
                        img_bytes = _req.get(result["image_url"], timeout=30).content
                        st.download_button("📥 Download", data=img_bytes,
                                          file_name=f"decon_t2i_{t2i_res}.jpg",
                                          mime="image/jpeg")
                    except Exception:
                        st.info(f"[Open image]({result['image_url']})")
                else:
                    st.error(f"Failed: {result.get('error','Unknown error')}")

    # ── TAB 4: LOGO LOCK (deterministic, guaranteed-perfect text) ──────────────
    with tab4:
        import logo_lock as _ll

        st.markdown("#### 🔒 Logo Lock — guaranteed-perfect badge text")
        st.markdown("""
        <div style="background:#0A0A0A;border-radius:12px;padding:14px 20px;margin-bottom:16px;">
            <div style="font-size:13px;font-weight:700;color:#C8F55A;margin-bottom:8px;">WHY THIS EXISTS</div>
            <div style="font-size:12px;color:#CCC;line-height:1.8;">
                No AI image model can <b style="color:white;">guarantee</b> perfect small, curved or dense
                label text (a circular seal like "LIPOSOMAL TECHNOLOGY" is the worst case). Instead of
                gambling on re-renders, this <b style="color:#C8F55A;">pastes your real badge pixels</b> onto
                the result — so the text is 100% correct <b style="color:white;">by construction</b>, zero
                distortion. Works on any base image, including this tool's Replace results or GPT / Nano Banana renders.
            </div>
        </div>
        """, unsafe_allow_html=True)

        colu1, colu2 = st.columns(2)
        with colu1:
            st.markdown("**1. Base image** (the render to fix)")
            _last = st.session_state.get("ll_base_bytes")
            _use_last = False
            if _last:
                _use_last = st.checkbox("Use my last Replace result", value=True, key="ll_uselast")
            ll_base_bytes = None
            if _use_last and _last:
                ll_base_bytes = _last
                st.image(ll_base_bytes, use_container_width=True)
            else:
                _b = st.file_uploader("Base", type=["jpg","jpeg","png","webp"],
                                      label_visibility="collapsed", key="ll_base_up")
                if _b:
                    ll_base_bytes = _b.getvalue()
                    st.image(ll_base_bytes, use_container_width=True)
        with colu2:
            st.markdown("**2. Your logo / badge** (the exact artwork)")
            st.caption("Transparent PNG is ideal. For a round seal, a tight square crop works — "
                       "turn on 'Circular mask' below.")
            _l = st.file_uploader("Logo", type=["png","jpg","jpeg","webp"],
                                  label_visibility="collapsed", key="ll_logo_up")
            ll_logo_bytes = _l.getvalue() if _l else None
            if ll_logo_bytes:
                st.image(ll_logo_bytes, use_container_width=True)

        if ll_base_bytes and ll_logo_bytes:
            # Optional one-click pre-position (only if OpenCV is installed).
            _auto = _ll.auto_locate(ll_base_bytes, ll_logo_bytes)
            if _auto:
                if st.button(f"🎯 Auto-locate badge (confidence {_auto['confidence']})", key="ll_auto"):
                    st.session_state["ll_cx"] = float(_auto["cx"])
                    st.session_state["ll_cy"] = float(_auto["cy"])
                    st.session_state["ll_size"] = round(_auto["width_frac"] * 100)
                    st.rerun()

            st.markdown("**3. Position the badge** — the preview updates live")
            cc1, cc2 = st.columns(2)
            cx = cc1.slider("Horizontal position", 0.0, 1.0, 0.50, 0.005, key="ll_cx")
            cy = cc2.slider("Vertical position", 0.0, 1.0, 0.50, 0.005, key="ll_cy")
            size = cc1.slider("Size (% of image width)", 5, 90, 25, key="ll_size") / 100.0
            rot = cc2.slider("Rotation (°)", -180, 180, 0, key="ll_rot")
            tilt = cc1.slider("Vertical squash (fake perspective tilt)", 50, 100, 100,
                              key="ll_tilt") / 100.0
            feather = cc2.slider("Edge feather (px)", 0.0, 8.0, 1.5, 0.5, key="ll_feather")
            opacity = cc1.slider("Opacity", 0.2, 1.0, 1.0, 0.05, key="ll_op")
            circular = cc2.checkbox("Circular mask (round badge)", value=True, key="ll_circ")
            bg = st.checkbox("Remove flat white background from the logo", value=False, key="ll_bg")

            try:
                out = _ll.composite_logo(
                    ll_base_bytes, ll_logo_bytes, cx=cx, cy=cy, width_frac=size,
                    aspect=tilt, rotation=float(rot), feather=feather,
                    opacity=opacity, circular=circular, bg_remove=bg)
                st.markdown("**Result — your exact badge, perfect text ✅**")
                st.image(out, use_container_width=True)
                st.download_button("📥 Download locked image", data=out,
                                   file_name="decon_logo_locked.jpg", mime="image/jpeg",
                                   type="primary", key="ll_dl")
                st.caption("💡 Line the badge up over the distorted seal, match its size/rotation, "
                           "then download. The text can never distort — these are your original pixels.")
            except Exception as e:
                st.error(f"Compositing failed: {e}")
        else:
            st.info("Load a **base image** and a **logo/badge** above to start positioning.")

elif module.key == "hr":
    from hr_engine import (extract_jd_text, summarise_jd,
                            generate_ats_prompt, generate_prompt_with_ai,
                            SCORING_DIMENSIONS, EXCEL_COLUMNS)
    from hr_processor import process_resumes, results_to_excel

    tab1, tab2, tab3 = st.tabs([
        "⚡  Direct Evaluation",
        "📋  Prompt Generator",
        "📊  Scoring Guide"
    ])

    # ── Tab 1: Direct Evaluation ──────────────────────────────────────────────
    with tab1:
        st.markdown("#### ⚡ Direct Resume Evaluation")
        st.caption("Upload JD + up to 20 PDF resumes → Decon AI scores them directly → download ranked Excel. No copy-pasting needed.")

        st.markdown("""
        <div style="background:#0A0A0A;border-radius:14px;padding:18px 22px;margin-bottom:20px;">
            <div style="font-size:13px;font-weight:700;color:#C8F55A;margin-bottom:12px;">HOW IT WORKS</div>
            <div style="display:flex;gap:16px;">
                <div style="flex:1;background:rgba(255,255,255,0.05);border-radius:10px;padding:12px;text-align:center;">
                    <div style="font-size:20px;margin-bottom:4px;">📄</div>
                    <div style="font-size:11px;color:#CCC;">Upload JD</div>
                </div>
                <div style="flex:1;background:rgba(255,255,255,0.05);border-radius:10px;padding:12px;text-align:center;">
                    <div style="font-size:20px;margin-bottom:4px;">📁</div>
                    <div style="font-size:11px;color:#CCC;">Upload up to 20 resume PDFs</div>
                </div>
                <div style="flex:1;background:rgba(255,255,255,0.05);border-radius:10px;padding:12px;text-align:center;">
                    <div style="font-size:20px;margin-bottom:4px;">🤖</div>
                    <div style="font-size:11px;color:#CCC;">AI reads & scores each one</div>
                </div>
                <div style="flex:1;background:rgba(200,245,90,0.1);border:1px solid rgba(200,245,90,0.2);border-radius:10px;padding:12px;text-align:center;">
                    <div style="font-size:20px;margin-bottom:4px;">📊</div>
                    <div style="font-size:11px;color:#C8F55A;font-weight:600;">Download ranked Excel</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_jd2, col_extra2 = st.columns([1,1])
        with col_jd2:
            st.markdown("**1. Upload Job Description**")
            jd_file2 = st.file_uploader("JD", type=["pdf","docx","txt"],
                                         label_visibility="collapsed", key="hr_jd2")
            if jd_file2:
                st.success(f"✅ {jd_file2.name}")

        with col_extra2:
            st.markdown("**2. Extra criteria**")
            extra2 = st.text_area("Extra", height=100, label_visibility="collapsed",
                                   key="hr_extra2",
                                   placeholder="e.g. Must have D2C experience\nPrefer Bangalore based\nBudget: 8-12 LPA")

        st.markdown("**3. Upload resumes (up to 20 PDFs)**")
        resume_files = st.file_uploader(
            "Resumes",
            type=["pdf"],
            accept_multiple_files=True,
            label_visibility="collapsed",
            key="hr_resumes"
        )

        if resume_files:
            if len(resume_files) > 20:
                st.warning(f"⚠️ {len(resume_files)} files uploaded — only first 20 will be processed. Use the Prompt Generator tab for 100+ resumes.")
                resume_files = resume_files[:20]
            else:
                st.success(f"✅ {len(resume_files)} resumes loaded")

        st.markdown("")
        col_hr1, col_hr2 = st.columns(2)
        with col_hr1:
            do_evaluate = st.button("🚀 Evaluate & Get Excel", type="primary",
                                     key="btn_hr_eval", use_container_width=True)
        with col_hr2:
            do_hr_prompt = st.button("📋 Generate Prompt Instead",
                                      type="secondary", key="btn_hr_eval_prompt",
                                      use_container_width=True)

        # show prompt mode inline if clicked
        if do_hr_prompt:
            if not jd_file2:
                st.error("Upload a JD first.")
            else:
                jd_bytes_p = jd_file2.read()
                jd_text_p = extract_jd_text(jd_bytes_p, jd_file2.name)
                n_res = len(resume_files) if resume_files else 50
                mode_p = "pdf" if resume_files else "pdf"
                with st.spinner("Generating prompt..."):
                    jd_sum_p = summarise_jd(jd_text_p)
                    prompt_p = generate_prompt_with_ai(jd_text_p, jd_sum_p,
                                                        extra2, mode_p,
                                                        n_res, "Deconstruct")
                st.success("✅ Prompt ready — paste into Claude or ChatGPT with your resumes")
                st.code(prompt_p, language=None)

        if do_evaluate:
            if not jd_file2:
                st.error("Upload a JD first.")
            elif not resume_files:
                st.error("Upload at least one resume PDF.")
            else:
                # extract JD
                jd_bytes = jd_file2.read()
                jd_text = extract_jd_text(jd_bytes, jd_file2.name)
                jd_summary = summarise_jd(jd_text)

                if isinstance(jd_summary, dict) and "raw" not in jd_summary:
                    st.info(f"📋 Role: **{jd_summary.get('role_title','?')}** | Skills: {', '.join(jd_summary.get('key_skills',[])[:5])}")

                # progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()

                def update_progress(i, total, filename):
                    pct = int((i / total) * 100)
                    progress_bar.progress(pct)
                    status_text.markdown(f"⚙️ Evaluating **{filename}** ({i+1}/{total})...")

                # process
                files_data = [(f.name, f.read()) for f in resume_files]
                with st.spinner("AI is reading and scoring resumes..."):
                    results = process_resumes(
                        resume_files=files_data,
                        jd_text=jd_text,
                        extra_criteria=extra2,
                        progress_callback=update_progress
                    )

                progress_bar.progress(100)
                status_text.markdown("✅ All resumes evaluated!")

                # show results preview
                st.markdown(f"### Rankings — {len(results)} candidates evaluated")

                # quick summary pills
                strong = sum(1 for r in results if r.get("recommendation")=="STRONG YES")
                yes = sum(1 for r in results if r.get("recommendation")=="YES")
                maybe = sum(1 for r in results if r.get("recommendation")=="MAYBE")
                no = sum(1 for r in results if r.get("recommendation")=="NO")

                st.markdown(f"""
                <div style="display:flex;gap:12px;margin:16px 0;">
                    <div style="background:#DCFCE7;border-radius:10px;padding:12px 20px;text-align:center;flex:1;">
                        <div style="font-size:24px;font-weight:800;color:#166534;">{strong}</div>
                        <div style="font-size:11px;color:#166534;font-weight:600;">STRONG YES</div>
                    </div>
                    <div style="background:#FEF9C3;border-radius:10px;padding:12px 20px;text-align:center;flex:1;">
                        <div style="font-size:24px;font-weight:800;color:#854D0E;">{yes}</div>
                        <div style="font-size:11px;color:#854D0E;font-weight:600;">YES</div>
                    </div>
                    <div style="background:#FFEDD5;border-radius:10px;padding:12px 20px;text-align:center;flex:1;">
                        <div style="font-size:24px;font-weight:800;color:#9A3412;">{maybe}</div>
                        <div style="font-size:11px;color:#9A3412;font-weight:600;">MAYBE</div>
                    </div>
                    <div style="background:#FEE2E2;border-radius:10px;padding:12px 20px;text-align:center;flex:1;">
                        <div style="font-size:24px;font-weight:800;color:#991B1B;">{no}</div>
                        <div style="font-size:11px;color:#991B1B;font-weight:600;">NO</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # top 3 candidates
                for i, r in enumerate(results[:3], 1):
                    rec = r.get("recommendation","")
                    rec_color = {"STRONG YES":"#166534","YES":"#854D0E",
                                  "MAYBE":"#9A3412","NO":"#991B1B"}.get(rec,"#666")
                    rec_bg = {"STRONG YES":"#DCFCE7","YES":"#FEF9C3",
                               "MAYBE":"#FFEDD5","NO":"#FEE2E2"}.get(rec,"#F5F5F5")

                    st.markdown(f"""
                    <div class="card">
                        <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                            <div>
                                <div class="card-rank">#{i} Ranked Candidate</div>
                                <div class="card-title">{r.get('name','Unknown')}</div>
                                <div style="font-size:13px;color:#666;">
                                    {r.get('current_role','')} @ {r.get('current_company','')}
                                    · {r.get('years_experience','')} years
                                </div>
                            </div>
                            <div style="text-align:right;">
                                <span class="pill pill-score">Score {r.get('total_score',0)}/100</span><br><br>
                                <span style="background:{rec_bg};color:{rec_color};padding:4px 12px;
                                            border-radius:12px;font-size:12px;font-weight:700;">
                                    {rec}
                                </span>
                            </div>
                        </div>
                        <div style="margin-top:10px;font-size:13px;color:#555;">
                            <b>Strengths:</b> {' · '.join(r.get('strengths',[])[:3])}<br>
                            <b>Gaps:</b> {' · '.join(r.get('gaps',[])[:2])}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                if len(results) > 3:
                    st.caption(f"+ {len(results)-3} more candidates in the Excel download below")

                # Excel download
                st.markdown("")
                excel_bytes = results_to_excel(results)
                st.download_button(
                    label="📥 Download Full Ranked Excel",
                    data=excel_bytes,
                    file_name=f"decon_ats_rankings_{jd_summary.get('role_title','candidates').replace(' ','_')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary",
                    key="hr_download"
                )

    # ── Tab 2: Prompt Generator ───────────────────────────────────────────────
    with tab2:
        st.markdown("#### 📋 Prompt Generator")
        st.caption("For 100+ resumes — generates a prompt to paste into Claude/ChatGPT.")

        col_jd3, col_extra3 = st.columns([1,1])
        with col_jd3:
            st.markdown("**Upload JD**")
            jd_file3 = st.file_uploader("JD3", type=["pdf","docx","txt"],
                                         label_visibility="collapsed", key="hr_jd3")
            if jd_file3:
                st.success(f"✅ {jd_file3.name}")
        with col_extra3:
            st.markdown("**Extra criteria**")
            extra3 = st.text_area("Extra3", height=100,
                                   label_visibility="collapsed", key="hr_extra3",
                                   placeholder="Location, salary range, domain requirements...")

        st.markdown("**How are the resumes?**")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("📁 Downloaded PDF Files", key="hr_pdf3", use_container_width=True):
                st.session_state["hr_mode3"] = "pdf"
        with c2:
            if st.button("🔗 Google Drive Links File", key="hr_drive3", use_container_width=True):
                st.session_state["hr_mode3"] = "drive"

        mode3 = st.session_state.get("hr_mode3")
        if mode3 == "drive":
            st.warning("⚠️ Drive links must be set to 'Anyone with link can view'")

        resume_count3 = st.slider("Number of resumes", 10, 200, 100, 10, key="hr_count3")

        if st.button("Generate Prompt", type="primary", key="btn_hr_prompt"):
            if not jd_file3:
                st.error("Upload JD first.")
            elif not mode3:
                st.error("Select PDF or Drive Links above.")
            else:
                jd_bytes3 = jd_file3.read()
                jd_text3 = extract_jd_text(jd_bytes3, jd_file3.name)
                with st.spinner("Generating prompt..."):
                    jd_sum3 = summarise_jd(jd_text3)
                    prompt3 = generate_prompt_with_ai(jd_text3, jd_sum3,
                                                       extra3, mode3,
                                                       resume_count3, "Deconstruct")
                st.success("✅ Prompt ready")
                st.code(prompt3, language=None)

    # ── Tab 3: Scoring Guide ──────────────────────────────────────────────────
    with tab3:
        st.markdown("#### 📊 Scoring Framework")
        for d in SCORING_DIMENSIONS:
            st.markdown(f"""
            <div class="card">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div class="card-title" style="font-size:16px;margin-bottom:4px;">{d['label']}</div>
                    <span class="pill pill-score">{d['weight']}%</span>
                </div>
                <div class="why-text" style="margin-top:0;">{d['description']}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("""
        <div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:12px;padding:16px 20px;margin-top:8px;">
            <div style="font-weight:700;color:#166534;margin-bottom:10px;">Hiring Recommendation Scale</div>
            <div style="display:flex;gap:12px;">
                <div style="background:#DCFCE7;border-radius:8px;padding:10px 16px;text-align:center;flex:1;">
                    <div style="font-weight:800;color:#166534;font-size:16px;">85-100</div>
                    <div style="font-size:11px;color:#166534;font-weight:600;">STRONG YES</div>
                </div>
                <div style="background:#FEF9C3;border-radius:8px;padding:10px 16px;text-align:center;flex:1;">
                    <div style="font-weight:800;color:#854D0E;font-size:16px;">70-84</div>
                    <div style="font-size:11px;color:#854D0E;font-weight:600;">YES</div>
                </div>
                <div style="background:#FFEDD5;border-radius:8px;padding:10px 16px;text-align:center;flex:1;">
                    <div style="font-weight:800;color:#9A3412;font-size:16px;">55-69</div>
                    <div style="font-size:11px;color:#9A3412;font-weight:600;">MAYBE</div>
                </div>
                <div style="background:#FEE2E2;border-radius:8px;padding:10px 16px;text-align:center;flex:1;">
                    <div style="font-weight:800;color:#991B1B;font-size:16px;">0-54</div>
                    <div style="font-size:11px;color:#991B1B;font-weight:600;">NO</div>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PRODUCT INTELLIGENCE
# ══════════════════════════════════════════════════════════════════════════════
elif module.key == "product_intel":
    from amazon_scraper import run_analysis, to_excel, search_amazon, safe_number

    tab1, tab2 = st.tabs(["🔍  Competitor Analysis", "📊  Dashboard"])

    # store results in session state so both tabs can access
    if "pi_results" not in st.session_state:
        st.session_state["pi_results"] = []
    if "pi_keyword" not in st.session_state:
        st.session_state["pi_keyword"] = ""

    # ── Tab 1: Input + Analysis ───────────────────────────────────────────────
    with tab1:
        st.markdown("#### 🔍 Amazon Competitor Analysis")
        st.caption("Enter a keyword or paste URLs — get brand, product, price, rating, reviews, claims, ranking, sentiment. Excel output.")

        # how it works
        st.markdown("""
        <div style="background:#0A0A0A;border-radius:14px;padding:18px 22px;margin-bottom:20px;">
            <div style="font-size:13px;font-weight:700;color:#C8F55A;margin-bottom:12px;">HOW IT WORKS</div>
            <div style="display:flex;gap:16px;">
                <div style="flex:1;background:rgba(255,255,255,0.05);border-radius:10px;padding:12px;text-align:center;">
                    <div style="font-size:20px;margin-bottom:4px;">🔎</div>
                    <div style="font-size:11px;color:#CCC;">Keyword search or paste URLs</div>
                </div>
                <div style="flex:1;background:rgba(255,255,255,0.05);border-radius:10px;padding:12px;text-align:center;">
                    <div style="font-size:20px;margin-bottom:4px;">🌐</div>
                    <div style="font-size:11px;color:#CCC;">Scrapes each product page</div>
                </div>
                <div style="flex:1;background:rgba(255,255,255,0.05);border-radius:10px;padding:12px;text-align:center;">
                    <div style="font-size:20px;margin-bottom:4px;">🤖</div>
                    <div style="font-size:11px;color:#CCC;">AI extracts claims + sentiment</div>
                </div>
                <div style="flex:1;background:rgba(200,245,90,0.1);border:1px solid rgba(200,245,90,0.2);border-radius:10px;padding:12px;text-align:center;">
                    <div style="font-size:20px;margin-bottom:4px;">📊</div>
                    <div style="font-size:11px;color:#C8F55A;font-weight:600;">Ranked Excel + Dashboard</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # input mode toggle
        input_mode = st.radio(
            "Input method",
            ["🔎 Keyword Search", "🔗 Paste Product URLs"],
            horizontal=True,
            key="pi_mode"
        )

        col1, col2 = st.columns([2, 1])

        with col1:
            if input_mode == "🔎 Keyword Search":
                keyword = st.text_input(
                    "Product keyword",
                    placeholder="e.g. gel sunscreen india, niacinamide serum, vitamin c face wash",
                    key="pi_keyword_input"
                )
                n_results = st.slider("Max products to analyse", 5, 20, 12, key="pi_n")
                pi_comp_only = st.checkbox(
                    "Only my tracked competitors (recommended)", value=True, key="pi_comp_only")
                from amazon_scraper import TARGET_COMPETITORS
                st.caption("Tracked: " + " · ".join(TARGET_COMPETITORS))
                urls_input = ""
            else:
                keyword = st.text_input(
                    "Label for this analysis",
                    placeholder="e.g. Gel Sunscreen Competitors",
                    key="pi_label"
                )
                urls_input = st.text_area(
                    "Paste Amazon URLs (one per line)",
                    placeholder="https://www.amazon.in/dp/ASIN1\nhttps://www.amazon.in/dp/ASIN2\nhttps://www.amazon.in/dp/ASIN3",
                    height=150,
                    key="pi_urls"
                )
                n_results = 10

        with col2:
            date_from = st.text_input(
                "Date / Timeline",
                value=datetime.now().strftime("%B %Y"),
                key="pi_date",
                help="e.g. June 2026, Q2 2026"
            )
            st.markdown("")
            st.markdown("")

            # SerpAPI key status
            serp_key = os.getenv("SERPAPI_KEY","")
            if serp_key:
                st.markdown('<div style="background:#DCFCE7;border-radius:8px;padding:8px 12px;font-size:12px;color:#166534;">✅ SerpAPI connected</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div style="background:#FEF9C3;border-radius:8px;padding:8px 12px;font-size:12px;color:#854D0E;">⚠️ No SerpAPI key — using demo data.<br>Add SERPAPI_KEY to .env for live data.</div>', unsafe_allow_html=True)

        st.markdown("")
        if st.button("🚀 Run Analysis", type="primary", key="btn_pi_run", use_container_width=False):
            if not keyword:
                st.error("Enter a keyword or label first.")
            else:
                progress_bar = st.progress(0)
                status = st.empty()

                def update_progress(i, total, msg):
                    pct = int((i / max(total,1)) * 100)
                    progress_bar.progress(min(pct, 95))
                    status.markdown(f"⚙️ {msg}")

                urls = [u.strip() for u in urls_input.split("\n") if u.strip()] if urls_input else None

                with st.spinner(""):
                    results = run_analysis(
                        keyword=keyword,
                        urls=urls,
                        n_results=n_results,
                        date_from=date_from,
                        progress_cb=update_progress,
                        competitors_only=st.session_state.get("pi_comp_only", True),
                    )

                progress_bar.progress(100)
                status.markdown(f"✅ Analysed {len(results)} products")

                st.session_state["pi_results"] = results
                st.session_state["pi_keyword"] = keyword

                # AI decision layer: category state-of-play + launch/R&D brief
                try:
                    from product_strategy import strategy_briefs
                    with st.spinner("AI: building category state-of-play + launch brief…"):
                        st.session_state["pi_strategy"] = strategy_briefs(results, keyword)
                except Exception as _e:
                    st.session_state["pi_strategy"] = {}

                # quick summary
                def _safe(val, default=0):
                    import re as _re
                    try:
                        m = _re.search(r"[0-9]+\.?[0-9]*", str(val).replace(",",""))
                        return float(m.group()) if m else default
                    except Exception:
                        return default
                avg_rating = round(sum(_safe(r.get("rating",0)) for r in results) / max(len(results),1), 1)
                avg_price  = round(sum(_safe(r.get("price_inr",0)) for r in results) / max(len(results),1))

                st.markdown(f"""
                <div style="display:flex;gap:12px;margin:16px 0;">
                    <div class="metric" style="flex:1;">
                        <div class="metric-val">{len(results)}</div>
                        <div class="metric-label">Products Analysed</div>
                    </div>
                    <div class="metric" style="flex:1;">
                        <div class="metric-val">{avg_rating}⭐</div>
                        <div class="metric-label">Avg Rating</div>
                    </div>
                    <div class="metric" style="flex:1;">
                        <div class="metric-val">₹{avg_price}</div>
                        <div class="metric-label">Avg Price</div>
                    </div>
                    <div class="metric" style="flex:1;">
                        <div class="metric-val">{results[0].get('brand','') if results else '—'}</div>
                        <div class="metric-label">Top Ranked Brand</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # top 3 products preview
                st.markdown("### Top Competitors")
                for r in results[:3]:
                    sentiment_color = "#166534" if r.get("review_sentiment") == "Positive" else "#9A3412"
                    sentiment_bg = "#DCFCE7" if r.get("review_sentiment") == "Positive" else "#FFEDD5"
                    claims_html = "".join(f'<div style="font-size:12px;color:#555;">• {c}</div>' for c in r.get("top_claims",[])[:3])

                    mrp_v = safe_number(r.get('mrp', r.get('price_inr',0)))
                    sell_v = safe_number(r.get('price_inr',0))
                    disc_v = str(r.get('discount_pct',''))
                    price_html = (
                        f'<span style="text-decoration:line-through;color:#AAA;font-size:12px;">₹{int(mrp_v)}</span> '
                        f'<span style="color:#166534;font-weight:700;">₹{int(sell_v)}</span> '
                        f'<span style="background:#DCFCE7;color:#166534;padding:1px 6px;border-radius:6px;font-size:11px;">{disc_v}</span>'
                    ) if mrp_v and mrp_v != sell_v else f'<span style="font-weight:700;">₹{int(sell_v)}</span>'

                    about = r.get('about_product','')
                    about_html = f'<div style="font-size:12px;color:#555;margin:6px 0;line-height:1.5;">{about[:200]}...</div>' if about else ''

                    st.markdown(f"""
                    <div class="card">
                        <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                            <div style="flex:1;">
                                <div class="card-rank">#{r.get('final_rank','')} · Amazon Rank #{r.get('keyword_rank','')}</div>
                                <div class="card-title">{r.get('product_name','')[:70]}</div>
                                <div style="font-size:13px;color:#888;margin-bottom:6px;">
                                    {r.get('brand','')} · {price_html} · ⭐{r.get('rating','')} · {r.get('review_count','')} reviews
                                </div>
                                <div style="font-size:12px;color:#555;margin-bottom:6px;">
                                    <b>Category rank:</b> {r.get('category_rank','Not found')}
                                </div>
                                {about_html}
                                <b style="font-size:12px;color:#333;">Key claims:</b>
                                {claims_html}
                            </div>
                            <div style="margin-left:16px;text-align:center;">
                                <span class="pill pill-score">{r.get('total_score',0)}/100</span><br><br>
                                <span style="background:{sentiment_bg};color:{sentiment_color};
                                            padding:3px 10px;border-radius:10px;font-size:11px;font-weight:600;">
                                    {r.get('review_sentiment','—')}
                                </span>
                                <div style="font-size:11px;color:#888;margin-top:8px;">
                                    {r.get('date_range','')}
                                </div>
                            </div>
                        </div>
                        <div style="margin-top:10px;border-top:1px solid #EEE;padding-top:8px;">
                            <div style="display:flex;gap:16px;">
                                <div style="flex:1;background:#F0FDF4;border-radius:8px;padding:10px;">
                                    <div style="font-size:10px;font-weight:700;color:#166534;margin-bottom:4px;text-transform:uppercase;">What Customers Love</div>
                                    <div style="font-size:12px;color:#166534;line-height:1.6;">
                                        {(r.get("key_positives","") if isinstance(r.get("key_positives",""), str) else " ".join(r.get("key_positives",[])))[:300]}...
                                    </div>
                                </div>
                                <div style="flex:1;background:#FEF2F2;border-radius:8px;padding:10px;">
                                    <div style="font-size:10px;font-weight:700;color:#991B1B;margin-bottom:4px;text-transform:uppercase;">What Customers Complain About</div>
                                    <div style="font-size:12px;color:#991B1B;line-height:1.6;">
                                        {(r.get("key_negatives","") if isinstance(r.get("key_negatives",""), str) else " ".join(r.get("key_negatives",[])))[:300]}...
                                    </div>
                                </div>
                            </div>
                            {f'<div style="margin-top:8px;font-size:12px;color:#666;"><b>Market gap:</b> {r.get("market_gap","")}</div>' if r.get("market_gap") else ""}
                            <div style="margin-top:8px;font-size:10px;color:#9A9A96;">
                                📊 Analysed <b>{r.get('reviews_sampled',0)}</b> sampled reviews (recent + critical) ·
                                aspect sentiment from Amazon across all <b>{r.get('review_count','?')}</b> reviews
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                if len(results) > 3:
                    st.caption(f"+ {len(results)-3} more products in Excel download and Dashboard tab")

                # Excel download (includes the AI State-of-Play + Launch Brief sheets)
                st.markdown("")
                excel = to_excel(results, keyword, strategy=st.session_state.get("pi_strategy"))
                fname = f"decon_amazon_{keyword.replace(' ','_')}_{datetime.now().strftime('%Y%m%d')}.xlsx"
                st.download_button(
                    "📥 Download Full Analysis Excel",
                    data=excel,
                    file_name=fname,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary"
                )

    # ── Tab 2: Dashboard ──────────────────────────────────────────────────────
    with tab2:
        results = st.session_state.get("pi_results", [])
        keyword = st.session_state.get("pi_keyword", "")

        st.markdown("#### 📊 Competitive Intelligence Dashboard")

        if not results:
            st.info("Run an analysis in the Competitor Analysis tab first — the dashboard will populate here.")
        else:
            st.caption(f"Keyword: **{keyword}** · {len(results)} products · {results[0].get('date_range','')}")

            # ── AI decision layer: category state-of-play + launch brief ──
            _strat = st.session_state.get("pi_strategy") or {}
            _sop = _strat.get("state_of_play", {}) or {}
            _lb = _strat.get("launch_brief", {}) or {}
            if _sop.get("summary"):
                st.markdown("### 🧠 Category State of Play")
                st.caption("AI synthesis across all analysed products — grounded in the scraped prices, "
                           "ratings, demand and Amazon's counted complaint aspects.")
                st.markdown(f"> {_sop.get('summary','')}")
                cA, cB = st.columns(2)
                with cA:
                    if _sop.get("biggest_gaps"):
                        st.markdown("**Biggest gaps**")
                        for g in _sop.get("biggest_gaps", [])[:5]:
                            st.markdown(f"- {g}")
                with cB:
                    if _sop.get("strategic_moves"):
                        st.markdown("**Strategic moves for Deconstruct**")
                        for m in _sop.get("strategic_moves", [])[:6]:
                            st.markdown(f"- {m}")
                for _lab, _key in [("Market structure", "market_structure"),
                                   ("Price dynamics", "price_dynamics"),
                                   ("Deconstruct's position", "deconstruct_position")]:
                    if _sop.get(_key):
                        st.markdown(f"**{_lab}:** {_sop[_key]}")
            if _lb.get("concept"):
                st.markdown("### 🚀 Launch / R&D Brief — what to build next")
                st.markdown(
                    f'<div class="card" style="border-left:4px solid #C8F55A;">'
                    f'<div class="card-title" style="margin-bottom:6px;">{_lb.get("concept","")}</div>'
                    f'<div style="font-size:13px;color:#555;line-height:1.7;">'
                    f'<b>Opportunity:</b> {_lb.get("opportunity","")}<br>'
                    f'<b>Hero ingredient:</b> {_lb.get("hero_ingredient","")} &nbsp;·&nbsp; '
                    f'<b>Format:</b> {_lb.get("format","")} &nbsp;·&nbsp; '
                    f'<b>Target skin:</b> {_lb.get("target_skin","")}<br>'
                    f'<b>Target price:</b> {_lb.get("target_price_inr","")} — {_lb.get("price_rationale","")}<br>'
                    f'<b>Positioning:</b> {_lb.get("positioning","")}</div>'
                    f'<div style="margin-top:8px;"><b style="font-size:12px;">Key claims:</b> '
                    + " · ".join(f'<span class="pill pill-format">{c}</span>' for c in _lb.get("key_claims", [])[:6])
                    + f'</div><div style="margin-top:8px;font-size:12px;color:#888;">'
                    f'💡 Name ideas: {", ".join(_lb.get("name_ideas", []))} &nbsp;|&nbsp; '
                    f'Why now: {_lb.get("why_now","")}</div></div>',
                    unsafe_allow_html=True)
            st.divider()

            # ── Category Intelligence: pricing bands, demand, whitespace ──
            from product_analytics import category_analytics, opportunity_cards
            from amazon_scraper import load_snapshots
            pi_an = category_analytics(results)
            _ps = pi_an.get("price_stats", {})
            _pm = pi_an.get("per_ml_stats", {})
            _top = (pi_an.get("demand") or [{}])[0]
            st.markdown(f"""
            <div class="metrics" style="margin-top:6px;">
                <div class="metric"><div class="metric-val">₹{_ps.get('median','—')}</div>
                    <div class="metric-label">Median Price</div><div class="metric-sub">₹{_ps.get('min','?')}–₹{_ps.get('max','?')} range</div></div>
                <div class="metric"><div class="metric-val">₹{_pm.get('median','—')}</div>
                    <div class="metric-label">Median ₹/ml</div><div class="metric-sub">₹{_pm.get('min','?')}–₹{_pm.get('max','?')}</div></div>
                <div class="metric"><div class="metric-val" style="font-size:19px;">{_top.get('brand','—')}</div>
                    <div class="metric-label">Top Seller</div><div class="metric-sub">~{_top.get('bought',0):,}/mo bought</div></div>
                <div class="metric"><div class="metric-val">{pi_an.get('ratings_avg') or '—'}★</div>
                    <div class="metric-label">Avg Rating</div><div class="metric-sub">{pi_an.get('n',0)} products</div></div>
            </div>""", unsafe_allow_html=True)

            st.markdown("##### 🎯 Opportunities & Whitespace")
            _oc = opportunity_cards(pi_an)
            _ocols = st.columns(2)
            for _i, _c in enumerate(_oc):
                _ocols[_i % 2].markdown(
                    f'<div style="background:#fff;border:1px solid #ECEBE6;border-left:3px solid #C8F55A;'
                    f'border-radius:12px;padding:12px 16px;margin-bottom:10px;min-height:96px;">'
                    f'<div style="font-size:10px;font-weight:700;color:#9A9A96;text-transform:uppercase;letter-spacing:0.08em;">{_c["type"]}</div>'
                    f'<div style="font-size:14px;font-weight:600;color:#0A0A0A;margin:3px 0 5px;">{_c["title"]}</div>'
                    f'<div style="font-size:12px;color:#555;line-height:1.55;">{_c["detail"]}</div></div>',
                    unsafe_allow_html=True)

            # free "history": median competitor price across past runs
            _hist = load_snapshots(keyword)
            if len(_hist) >= 2:
                try:
                    import plotly.graph_objects as _go
                    def _medprice(h):
                        pr = sorted(p.get("price_inr") for p in h.get("products", [])
                                    if isinstance(p.get("price_inr"), (int, float)))
                        return round(pr[len(pr)//2]) if pr else None
                    _rev = list(reversed(_hist))
                    _ft = _go.Figure(_go.Scatter(
                        x=[h.get("generated_at", "")[:10] for h in _rev],
                        y=[_medprice(h) for h in _rev],
                        mode="lines+markers", line_color="#0A0A0A",
                        marker=dict(color="#C8F55A", size=9)))
                    _ft.update_layout(title="Median competitor price over past runs (₹)", height=300,
                                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                      font=dict(family="DM Sans", color="#0A0A0A"))
                    st.plotly_chart(_ft, use_container_width=True)
                except Exception:
                    pass

            st.divider()

            # radar chart using plotly
            try:
                import plotly.graph_objects as go
                import plotly.express as px

                # ── Score breakdown radar for top 5 ──
                top5 = results[:5]
                categories = ["Rating", "Reviews", "Price Value", "Claims", "Rank"]

                fig_radar = go.Figure()
                colors = ["#C8F55A","#F4A99A","#60A5FA","#A78BFA","#FB923C"]

                for i, r in enumerate(top5):
                    sp = r.get("score_parts", {})
                    vals = [
                        sp.get("rating_score", 0),
                        sp.get("review_volume", 0),
                        sp.get("price_value", 0),
                        sp.get("claim_strength", 0),
                        sp.get("rank_position", 0),
                    ]
                    name = f"{r.get('brand','')} ({r.get('total_score',0)})"
                    fig_radar.add_trace(go.Scatterpolar(
                        r=vals + [vals[0]],
                        theta=categories + [categories[0]],
                        fill='toself',
                        name=name,
                        line_color=colors[i % len(colors)],
                        opacity=0.7
                    ))

                fig_radar.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0,100])),
                    showlegend=True,
                    title=f"Competitive Radar — Top 5 for '{keyword}'",
                    height=450,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(family="DM Sans", size=12),
                )
                st.plotly_chart(fig_radar, use_container_width=True)

                col_c1, col_c2 = st.columns(2)

                with col_c1:
                    # Price vs Rating scatter
                    brands = [r.get("brand","")[:15] for r in results]
                    import re as _re2
                    def _sf(v):
                        try:
                            m = _re2.search(r"[0-9]+\.?[0-9]*", str(v).replace(",",""))
                            return float(m.group()) if m else 0
                        except: return 0
                    prices  = [_sf(r.get("price_inr", 0)) for r in results]
                    ratings = [_sf(r.get("rating", 0)) for r in results]
                    scores = [r.get("total_score",0) for r in results]

                    fig_scatter = px.scatter(
                        x=prices, y=ratings,
                        text=brands,
                        size=scores,
                        color=scores,
                        color_continuous_scale=["#FEE2E2","#FEF9C3","#DCFCE7"],
                        labels={"x":"Price (₹)","y":"Rating","color":"Score"},
                        title="Price vs Rating (bubble size = total score)"
                    )
                    fig_scatter.update_traces(textposition='top center', textfont_size=9)
                    fig_scatter.update_layout(height=350, paper_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_scatter, use_container_width=True)

                with col_c2:
                    # Claims strength bar
                    claim_scores = [r.get("claim_strength", r.get("score_parts",{}).get("claim_strength",0)) for r in results]
                    fig_bar = px.bar(
                        x=[r.get("brand","")[:12] for r in results],
                        y=claim_scores,
                        color=claim_scores,
                        color_continuous_scale=["#FEE2E2","#FEF9C3","#DCFCE7"],
                        labels={"x":"Brand","y":"Claim Strength","color":""},
                        title="Claim Strength by Brand"
                    )
                    fig_bar.update_layout(height=350, paper_bgcolor='rgba(0,0,0,0)',
                                          showlegend=False)
                    st.plotly_chart(fig_bar, use_container_width=True)

                # sentiment summary
                st.markdown("#### Review Sentiment Summary")
                scols = st.columns(len(results[:6]))
                for i, (r, col) in enumerate(zip(results[:6], scols)):
                    sentiment = r.get("review_sentiment","—")
                    s_color = "#166534" if sentiment=="Positive" else "#9A3412" if sentiment=="Negative" else "#854D0E"
                    s_bg = "#DCFCE7" if sentiment=="Positive" else "#FEE2E2" if sentiment=="Negative" else "#FEF9C3"
                    col.markdown(f"""
                    <div style="background:{s_bg};border-radius:10px;padding:10px;text-align:center;">
                        <div style="font-size:11px;font-weight:700;color:{s_color};">{r.get('brand','')[:12]}</div>
                        <div style="font-size:10px;color:{s_color};margin-top:3px;">{sentiment}</div>
                        <div style="font-size:13px;font-weight:800;color:#0A0A0A;margin-top:2px;">⭐{r.get('rating','')}</div>
                    </div>
                    """, unsafe_allow_html=True)

            except ImportError:
                st.warning("Install plotly for visualisations: `pip install plotly`")
                # fallback table
                for r in results:
                    st.markdown(f"**#{r.get('final_rank')}** {r.get('brand')} — {r.get('product_name','')[:50]} | Score: {r.get('total_score')}/100 | ₹{r.get('price_inr')} | ⭐{r.get('rating')}")


# ══════════════════════════════════════════════════════════════════════════════
# BRAND MEDIA ANALYSER
# ══════════════════════════════════════════════════════════════════════════════
elif module.key == "brand_media":
    import brand_scraper as _bs
    import brand_intel as _bi

    tab1, tab2 = st.tabs(["🔍  Run Analysis", "📊  Intelligence Dashboard"])

    # ── Tab 1: run ────────────────────────────────────────────────────────────
    with tab1:
        st.markdown("#### 🔍 Weekly Instagram Competitor Analysis")
        st.caption("Reads each competitor's official account (top posts) + the creators who post about "
                   "them using brand keywords (the biggest bracket), profiles those creators "
                   "(tier · sector · content style), and benchmarks everything against Deconstruct.")

        _apify_ok = bool(os.getenv("APIFY_KEY", ""))
        _msg = ("✅ Apify connected — live Instagram data" if _apify_ok
                else "⚠️ No APIFY_KEY — running on mock data. Add APIFY_KEY to .env for live scraping.")
        st.markdown(f'<div style="background:#0A0A0A;border-radius:12px;padding:12px 18px;'
                    f'margin-bottom:14px;color:#C8F55A;font-size:12px;font-weight:600;">{_msg}</div>',
                    unsafe_allow_html=True)

        st.markdown("**Tracked accounts:** " + " · ".join(f"@{b['handle']}" for b in _bs.BRANDS))

        c1, c2, c3, c4 = st.columns(4)
        bm_days = c1.slider("Days window", 7, 30, 20, key="bm_days")
        bm_posts = c2.slider("Posts fetched / account", 20, 40, 40, key="bm_posts")
        bm_cap = c3.slider("Creators profiled / brand", 4, 15, 8, key="bm_cap")
        bm_minf = c4.select_slider("Min. followers", options=[1000, 5000, 10000, 25000, 50000, 100000],
                                   value=10000, key="bm_minf")
        st.caption("Methodology: take each brand's **highest-viewed skincare videos** (last N days, "
                   "brand keywords + skincare context), find their creators, and keep only those above "
                   f"the follower floor — no 600-follower pages. Brand keywords are disambiguated so "
                   "'deconstruct' won't pull in demolition/architecture accounts.")

        if st.button("🚀 Run Weekly Analysis", type="primary", key="bm_run"):
            prog = st.progress(0)
            status = st.empty()

            def _bm_cb(done, total, msg):
                prog.progress(min(int(done / max(total, 1) * 100), 95))
                status.markdown(f"⚙️ {msg}")

            with st.spinner("Scraping Instagram + profiling creators… (a few minutes)"):
                posts = _bs.fetch_account_posts(days_back=bm_days, max_posts=bm_posts, progress_cb=_bm_cb)
                report = _bi.build_report(posts, days_back=bm_days,
                                          infl_cap_per_brand=bm_cap, min_followers=bm_minf,
                                          progress_cb=_bm_cb)
            report["generated_at"] = datetime.now().isoformat(timespec="seconds")
            _bs.save_snapshot(report)
            prog.progress(100)
            status.markdown("✅ Analysis complete")
            st.session_state["bm_report"] = report

        report = st.session_state.get("bm_report")
        if report:
            dec = next((b for b in report["brands"] if b.get("is_baseline")), {})
            ia = report["influencer_analysis"]
            st.markdown(f"""
            <div class="metrics" style="margin-top:8px;">
                <div class="metric"><div class="metric-val">{len(report['brands'])}</div>
                    <div class="metric-label">Brands Analysed</div><div class="metric-sub">Deconstruct = baseline</div></div>
                <div class="metric"><div class="metric-val">{ia.get('total_influencers',0)}</div>
                    <div class="metric-label">Creators Profiled</div><div class="metric-sub">tier · sector · style</div></div>
                <div class="metric"><div class="metric-val">{len(ia.get('overlaps',{}))}</div>
                    <div class="metric-label">Cross-Brand Creators</div><div class="metric-sub">work with 2+ rivals</div></div>
                <div class="metric"><div class="metric-val">{dec.get('format_pct',{}).get('reel',0)}%</div>
                    <div class="metric-label">Deconstruct Reels</div><div class="metric-sub">of its top posts</div></div>
            </div>""", unsafe_allow_html=True)

            for b in report["brands"]:
                s = b.get("strategy", {})
                base = b.get("is_baseline")
                launches = " · ".join(s.get("launches", [])[:3]) or "—"
                newmkt = " · ".join(s.get("new_market_signals", [])[:3]) or "—"
                st.markdown(f"""
                <div class="card" style="{'border-left:4px solid #C8F55A;' if base else ''}">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div class="card-title" style="margin-bottom:2px;">{'⭐ ' if base else ''}{b['brand']}</div>
                        <div style="font-size:12px;color:#888;">{b['posts_per_week']}/wk · avg {b['avg_likes']}❤ · {b['collabs']} collabs</div>
                    </div>
                    <div style="font-size:12px;color:#666;margin:4px 0 8px;">
                        Format mix (top posts): <b>{b['format_pct'].get('reel',0)}% Reels</b> ·
                        {b['format_pct'].get('carousel',0)}% Carousel · {b['format_pct'].get('image',0)}% Static
                        &nbsp;|&nbsp; Influencer tiers: {b.get('influencer_tier_mix',{})}
                    </div>
                    <div class="why-text" style="margin-top:0;">{s.get('content_summary','')}</div>
                    <div style="font-size:12px;color:#555;margin-top:8px;">
                        <b>Launches:</b> {launches}<br><b>New-market signals:</b> {newmkt}
                    </div>
                </div>""", unsafe_allow_html=True)

            xls = _bi.report_to_excel(report)
            if xls:
                st.download_button("📥 Download Full Report (4-sheet Excel)", data=xls,
                                   file_name=f"decon_brand_media_{datetime.now().strftime('%Y%m%d')}.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                   type="primary", key="bm_dl")

    # ── Tab 2: dashboard ──────────────────────────────────────────────────────
    with tab2:
        report = st.session_state.get("bm_report")
        st.markdown("#### 📊 Intelligence Dashboard")
        if not report:
            st.info("Run the analysis first — the dashboard populates here.")
        else:
            try:
                import plotly.graph_objects as go
                brands = report["brands"]
                names = [b["brand"] for b in brands]
                base_color = ["#C8F55A" if b.get("is_baseline") else "#BEBCB3" for b in brands]

                col1, col2 = st.columns(2)
                with col1:
                    fig = go.Figure()
                    for fmt, col in [("reel", "#0A0A0A"), ("carousel", "#F4A99A"), ("image", "#CFCDC4")]:
                        fig.add_trace(go.Bar(name=fmt.title(), x=names,
                                             y=[b["format_pct"].get(fmt, 0) for b in brands]))
                    fig.update_layout(barmode="stack", title="Format mix of top posts (%)",
                                      height=350, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                      font=dict(family="DM Sans", color="#0A0A0A"), legend=dict(orientation="h"))
                    st.plotly_chart(fig, use_container_width=True)
                with col2:
                    fig2 = go.Figure(go.Bar(x=names, y=[b["avg_likes"] for b in brands],
                                            marker_color=base_color,
                                            text=[b["avg_likes"] for b in brands], textposition="outside"))
                    fig2.update_layout(title="Avg engagement (likes) on top posts", height=350,
                                       paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                       font=dict(family="DM Sans", color="#0A0A0A"))
                    st.plotly_chart(fig2, use_container_width=True)

                ia = report["influencer_analysis"]
                col3, col4 = st.columns(2)
                with col3:
                    td = ia.get("tier_distribution", {})
                    if td:
                        fig3 = go.Figure(go.Bar(x=list(td.keys()), y=list(td.values()),
                                                marker_color="#C8F55A",
                                                text=list(td.values()), textposition="outside"))
                        fig3.update_layout(title="Creator tiers used (across competitors)", height=330,
                                           paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                           font=dict(family="DM Sans", color="#0A0A0A"))
                        st.plotly_chart(fig3, use_container_width=True)
                with col4:
                    sd = ia.get("sector_distribution", {})
                    if sd:
                        items = list(sd.items())[:8]
                        fig4 = go.Figure(go.Bar(x=[v for _, v in items], y=[k for k, _ in items],
                                                orientation="h", marker_color="#60A5FA",
                                                text=[v for _, v in items], textposition="outside"))
                        fig4.update_layout(title="Creator sectors / niches", height=330,
                                           paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                           font=dict(family="DM Sans", color="#0A0A0A"),
                                           yaxis=dict(autorange="reversed"))
                        st.plotly_chart(fig4, use_container_width=True)
            except ImportError:
                st.warning("Install plotly for charts: `pip install plotly`")

            recs = report.get("recommendations", {})
            st.markdown("### 🎯 Recommendations for Deconstruct")
            if recs.get("summary"):
                st.markdown(f"> {recs['summary']}")
            pcols = st.columns(3)
            for col, (title, key) in zip(pcols, [("🎬 Reels Playbook", "reels_playbook"),
                                                 ("🖼️ Static / Carousel", "static_playbook"),
                                                 ("🤝 Influencer Strategy", "influencer_strategy")]):
                with col:
                    st.markdown(f"**{title}**")
                    for item in recs.get(key, []):
                        st.markdown(f"- {item}")

            overlaps = ia.get("overlaps", {})
            if overlaps:
                st.markdown("### ⚔️ Cross-brand creators (working with multiple competitors)")
                for h, bl in list(overlaps.items())[:12]:
                    st.markdown(f"- **@{h}** → {', '.join(bl)}")

            with st.expander("All profiled creators (tier · sector · content)"):
                infl = report.get("influencers", {})
                rows = sorted(infl.items(), key=lambda kv: kv[1].get("followers", 0) or 0, reverse=True)
                for h, inf in rows:
                    st.markdown(f"**@{h}** · {inf.get('tier','')} ({inf.get('followers',0):,}) · "
                                f"{inf.get('sector','')} · {inf.get('content_style','')} "
                                f"· _{', '.join(inf.get('brands',[]))}_")


# ══════════════════════════════════════════════════════════════════════════════
# MARKET SHARE (DIGITAL SHELF INTELLIGENCE)
# ══════════════════════════════════════════════════════════════════════════════
elif module.key == "market_share":
    import shelf_scraper as _ss
    import shelf_intel as _si
    from amazon_scraper import TARGET_COMPETITORS as _TC

    tab1, tab2, tab3 = st.tabs(["🔍  Run Analysis", "📊  Shelf Dashboard", "🔎  Google Console"])

    with tab1:
        st.markdown("#### 🔍 Digital Shelf & Market-Share Analysis")
        st.caption("Scans the top listings for each category across Amazon · Nykaa · Myntra · Flipkart, "
                   "then measures share-of-shelf, ranking dominance, assortment, demand proxies and the "
                   "keywords that make products rank — benchmarked against Deconstruct. "
                   "Numbers are read directly from each marketplace (no estimation); 'demand' uses review volume as a labelled proxy.")

        cats = st.multiselect("Categories to measure share in",
                              _ss.DEFAULT_CATEGORIES + ["lip balm", "toner", "body lotion",
                                                        "vitamin c face wash", "spf 50 sunscreen"],
                              default=["sunscreen", "vitamin c serum", "niacinamide serum", "moisturizer"],
                              key="ms_cats")
        c1, c2 = st.columns(2)
        plats = c1.multiselect("Platforms", _ss.PLATFORMS, default=_ss.PLATFORMS, key="ms_plats")
        n_per = c2.slider("Top listings per category/platform", 10, 40, 25, key="ms_nper")
        st.caption(f"Tracked competitors: {', '.join(_TC)} · plus any other brand that shows up on the top shelf.")

        if st.button("🚀 Run Market-Share Analysis", type="primary", key="ms_run"):
            prog = st.progress(0)
            status = st.empty()

            def _ms_cb(done, total, msg):
                prog.progress(min(int(done / max(total, 1) * 100), 95))
                status.markdown(f"⚙️ {msg}")

            with st.spinner("Scanning the digital shelf across marketplaces…"):
                listings, cov = _ss.collect_shelf(keywords=cats, platforms=plats,
                                                  n_per=n_per, progress_cb=_ms_cb)
                report = _si.build_shelf_report(listings, cov, tracked_brands=_TC, progress_cb=_ms_cb)
            _si.save_shelf_snapshot(report)
            prog.progress(100)
            status.markdown(f"✅ Analysed {report['total_listings']} listings across "
                            f"{len(report['platforms'])} platforms")
            st.session_state["ms_report"] = report
            st.session_state["ms_listings"] = listings
            st.session_state["ms_cov"] = cov

        report = st.session_state.get("ms_report")
        if report:
            # ── fetch-mode diagnostic (proxy on/off + per-platform counts) ──
            _cov = st.session_state.get("ms_cov", {})
            _proxy = ("ScraperAPI proxy ✅" if _ss.SCRAPER_API_KEY
                      else "direct — no proxy key (cloud sites may block Nykaa/Myntra/Flipkart)")
            if _cov:
                _cnts = " · ".join(f"{p}: {sum(v.values())}" for p, v in _cov.items())
                st.caption(f"🌐 Fetch mode: **{_proxy}**  ·  listings pulled — {_cnts}")

            dec = next((s for s in report["scorecard"] if s.get("is_baseline")), {})
            leader = report["share_of_shelf"][0] if report["share_of_shelf"] else {}
            st.markdown(f"""
            <div class="metrics" style="margin-top:8px;">
                <div class="metric"><div class="metric-val">{dec.get('shelf_pct',0)}%</div>
                    <div class="metric-label">Deconstruct Shelf Share</div><div class="metric-sub">{dec.get('skus',0)} SKUs on the top shelf</div></div>
                <div class="metric"><div class="metric-val" style="font-size:20px;">{leader.get('brand','—')}</div>
                    <div class="metric-label">Shelf Leader</div><div class="metric-sub">{leader.get('pct',0)}% of shelf</div></div>
                <div class="metric"><div class="metric-val">{dec.get('top10',0)}</div>
                    <div class="metric-label">Top-10 Appearances</div><div class="metric-sub">share of search</div></div>
                <div class="metric"><div class="metric-val">{dec.get('platforms_present',0)}/{len(report['platforms'])}</div>
                    <div class="metric-label">Platforms Present</div><div class="metric-sub">distribution</div></div>
            </div>""", unsafe_allow_html=True)

            if report["deconstruct_distribution_gaps"]:
                st.warning("📦 Distribution gap — Deconstruct is absent on: "
                           + ", ".join(report["deconstruct_distribution_gaps"]))

            st.markdown("##### 🏆 Scorecard — Deconstruct vs competitors")
            import pandas as _pd
            sc = _pd.DataFrame([{
                "Brand": s["brand"], "Shelf %": s["shelf_pct"], "SKUs": s["skus"],
                "Top-10": s["top10"], "Avg Rank": s["avg_rank"],
                "Reviews (proxy)": s["total_reviews"], "Rating": s["avg_rating"],
                "Avg ₹": s["avg_price"], "Tier": s["price_tier"], "Platforms": s["platforms_present"],
            } for s in report["scorecard"]])
            st.dataframe(sc, use_container_width=True, hide_index=True)

            xls = _si.shelf_report_to_excel(report, st.session_state.get("ms_listings", []))
            if xls:
                st.download_button("📥 Download Full Report (6-sheet Excel)", data=xls,
                                   file_name=f"decon_market_share_{datetime.now().strftime('%Y%m%d')}.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                   type="primary", key="ms_dl")

    with tab2:
        report = st.session_state.get("ms_report")
        st.markdown("#### 📊 Shelf Dashboard")
        if not report:
            st.info("Run the analysis first — the dashboard populates here.")
        else:
            meth = report.get("methodology", {})
            with st.expander("ⓘ  How every number here is calculated — data source & method"):
                st.markdown(f"**Overview** — {meth.get('overview','')}")
                st.markdown(f"**Share of Shelf** — {meth.get('share_of_shelf','')}")
                st.markdown(f"**Search Dominance** — {meth.get('search_dominance','')}")
                st.markdown(f"**Assortment / gaps** — {meth.get('assortment','')}")
                st.markdown(f"**Demand proxy** — {meth.get('demand','')}")
                st.markdown(f"**Keywords** — {meth.get('keywords','')}")
                st.markdown(f"**All listings (raw evidence)** — {meth.get('all_listings','')}")
                st.caption(meth.get("tracked", ""))
            try:
                import plotly.graph_objects as go
                sos = report["share_of_shelf"][:10]
                names = [s["brand"] for s in sos]
                colors = ["#C8F55A" if b == "Deconstruct" else "#BEBCB3" for b in names]
                fig = go.Figure(go.Bar(x=[s["pct"] for s in sos], y=names, orientation="h",
                                       marker_color=colors, text=[f"{s['pct']}%" for s in sos],
                                       textposition="outside"))
                fig.update_layout(title="Share of Shelf — top brands (blended across platforms)",
                                  height=380, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                  font=dict(family="DM Sans", color="#0A0A0A"),
                                  yaxis=dict(autorange="reversed"), margin=dict(l=10, r=10))
                st.plotly_chart(fig, use_container_width=True)

                # per-platform shelf share for tracked brands (grouped)
                plats = report["platforms"]
                sos_p = report["share_of_shelf_by_platform"]
                tracked = [s["brand"] for s in report["scorecard"]][:6]
                figp = go.Figure()
                for b in tracked:
                    figp.add_trace(go.Bar(name=b, x=plats,
                        y=[next((r["pct"] for r in sos_p.get(p, []) if r["brand"] == b), 0) for p in plats]))
                figp.update_layout(barmode="group", title="Shelf share by platform (tracked brands)",
                                   height=380, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                   font=dict(family="DM Sans", color="#0A0A0A"), legend=dict(orientation="h"))
                st.plotly_chart(figp, use_container_width=True)
                st.caption("Share of Shelf % = a brand's SKUs in the scanned top listings ÷ all scanned "
                           "listings (per platform). Deconstruct in lime.")
            except ImportError:
                st.warning("Install plotly for charts.")

            # ── keyword gaps (AI) — the headline "what to do" ──
            ga = report.get("gap_analysis", {})
            st.markdown("### 🎯 Keyword & claim gaps for Deconstruct")
            st.caption("What the top-ranked listings claim that Deconstruct doesn't — AI-analysed, grounded in the scraped titles.")
            if ga.get("summary"):
                st.markdown(f"> {ga['summary']}")
            for a in ga.get("actions", [])[:7]:
                st.markdown(f"- {a}")

            # ── distinctive keywords per category ──
            st.markdown("### 🔑 Distinctive keywords by category")
            st.caption("Terms frequent in a category's top listings but rare across other categories "
                       "(the category's own name removed) — the words that actually differentiate winners.")
            kbc = report.get("keyword_by_category", {})
            for cat, kws in kbc.items():
                st.markdown(f"**{cat}** — " + " · ".join(f"{k['kw']} (×{k['listings']})" for k in kws[:10]))

            # ── keywords each competitor leads with ──
            st.markdown("### 🏷️ Keywords each competitor owns")
            kco = report.get("keyword_by_competitor", {})
            ccols = st.columns(2)
            for i, (b, kws) in enumerate(kco.items()):
                ccols[i % 2].markdown(f"**{b}** — " + ", ".join(k for k, _ in kws[:8]))

            # ── product-level bifurcation ──
            with st.expander("🧴 Product-level keyword breakdown (top products)"):
                for p in report.get("product_keywords", [])[:24]:
                    st.markdown(f"**[{p['platform']}] {p['brand']}** · {p['title'][:60]} → "
                                f"_{', '.join(p['keywords'][:6])}_")

            # movement over time
            snaps = _si.load_shelf_snapshots()
            if len(snaps) >= 2:
                st.markdown("### 📈 Deconstruct shelf share over time")
                try:
                    import plotly.graph_objects as go
                    rev = list(reversed(snaps))
                    def _dec(sn):
                        return next((s["shelf_pct"] for s in sn.get("scorecard", [])
                                     if s.get("is_baseline")), None)
                    figt = go.Figure(go.Scatter(x=[s.get("generated_at", "")[:16] for s in rev],
                                                y=[_dec(s) for s in rev], mode="lines+markers",
                                                line_color="#0A0A0A", marker=dict(color="#C8F55A", size=9)))
                    figt.update_layout(title="Deconstruct share of shelf (%)", height=320,
                                       paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                       font=dict(family="DM Sans", color="#0A0A0A"))
                    st.plotly_chart(figt, use_container_width=True)
                except ImportError:
                    pass

    # ── TAB 3: GOOGLE CONSOLE (import a Search Console export → deep brand report) ──
    with tab3:
        import search_intel as _sin
        import pandas as _pd

        st.markdown("#### 🔎 Google Console — import & deep-analyse your Search Console export")
        st.markdown("""
        <div style="background:#0A0A0A;border-radius:12px;padding:14px 20px;margin-bottom:16px;">
            <div style="font-size:13px;font-weight:700;color:#C8F55A;margin-bottom:8px;">HOW THIS WORKS</div>
            <div style="font-size:12px;color:#CCC;line-height:1.8;">
                In Search Console → <b style="color:white;">Performance → Export</b>, download the Excel/ZIP, then
                <b style="color:white;">import it here</b>. The engine strips brand-name noise
                (“deconstruct internship”, the dictionary sense) with an <b style="color:#C8F55A;">auditable lexicon</b>,
                then builds a brand-manager report — what’s working, what’s not, seasonality, category demand,
                demand interlinks and the biggest fixable opportunities — plus a downloadable
                <b style="color:white;">16-tab Excel</b> (charts, AI scorecard, glossary on every tab). Every number traces to a rule.
            </div>
        </div>
        """, unsafe_allow_html=True)

        gc_up = st.file_uploader("Import Search Console export (.xlsx workbook or .zip)",
                                 type=["xlsx", "zip"], key="gc_up")
        if st.button("📥 Import & Analyse", type="primary", key="gc_run", disabled=not gc_up):
            with st.spinner("Classifying queries, removing brand-name noise, computing insights + AI summary…"):
                try:
                    _ins = _sin.analyse_dump(gc_up.getvalue())
                    _es = _sin.executive_summary(_ins)
                    _reads = _sin.deep_reads(_ins)
                    _xls = _sin.to_excel(_ins, _es, _reads)   # built once, here
                    st.session_state["gc_report"] = {"ins": _ins, "es": _es,
                                                     "reads": _reads, "xls": _xls}
                except Exception as e:
                    st.error(f"Couldn't parse that file: {e}. Use the .xlsx/.zip from "
                             "Search Console → Performance → Export.")

        rep = st.session_state.get("gc_report")
        if not rep:
            st.info("Import your Search Console export above to generate the report.")
        else:
            ins, es = rep["ins"], rep["es"]
            m = ins["meta"]
            by = {c["class"]: c for c in ins["classes"]}
            classified = round(100 - by.get("ambiguous", {}).get("impr_pct", 0), 1)
            kept = round(by.get("product", {}).get("impr_pct", 0) + by.get("commercial", {}).get("impr_pct", 0), 1)
            noise = by.get("noise", {}).get("impr_pct", 0)

            st.markdown(f"##### 📊 thedeconstruct.in · {m['date_range']}")
            st.markdown(f"""<div class="metrics" style="margin-top:4px;">
                <div class="metric"><div class="metric-val">{m['total_clicks']:,}</div><div class="metric-label">Clicks</div></div>
                <div class="metric"><div class="metric-val">{m['total_impressions']:,}</div><div class="metric-label">Impressions</div></div>
                <div class="metric"><div class="metric-val">{kept}%</div><div class="metric-label">Real product demand</div></div>
                <div class="metric"><div class="metric-val">{noise}%</div><div class="metric-label">Brand-name noise removed</div></div>
            </div>""", unsafe_allow_html=True)

            st.download_button("📥 Download the full brand report — 16-tab Excel (charts + insights + glossary)",
                data=rep["xls"],
                file_name=f"decon_search_console_report_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary", key="gc_dl")
            st.caption("Every tab in the Excel opens with what it shows, how it's calculated, how accurate it is, "
                       "and a plain-English glossary — plus a charted Dashboard and an AI Product Scorecard.")

            if es.get("headline"):
                st.markdown(f"> **{es['headline']}**")
            cwa, cwb = st.columns(2)
            with cwa:
                st.markdown("**✅ What's working**")
                for w in es.get("working", [])[:5]:
                    st.markdown(f"- {w}")
            with cwb:
                st.markdown("**⚠️ What's not working**")
                for w in es.get("not_working", [])[:5]:
                    st.markdown(f"- {w}")
            if es.get("seasonality"):
                st.info(f"📅 {es['seasonality']}")
            if es.get("priorities"):
                st.markdown("**🎯 Priorities**")
                for i, p in enumerate(es["priorities"][:5], 1):
                    st.markdown(f"{i}. {p}")

            # ── AI Product Scorecard (category verdicts) ──
            reads = rep.get("reads", {})
            if reads.get("category_reads"):
                st.markdown("##### 🧴 Product scorecard — where each category stands")
                _vmap = {"Dominant": "🟢", "Scale up": "🟠", "Emerging": "⚪", "Underperforming": "🔴"}
                st.dataframe(_pd.DataFrame([{
                    "Category": c.get("category", ""),
                    "Verdict": f"{_vmap.get(c.get('label',''),'')} {c.get('label','')}".strip(),
                    "What it means": c.get("note", "")} for c in reads["category_reads"]]),
                    use_container_width=True, hide_index=True)
            if reads.get("keyword_read"):
                st.info(f"🔑 **Keyword read:** {reads['keyword_read']}")

            with st.expander("🔬 Data & accuracy — how brand-name noise was removed", expanded=True):
                st.caption(f"Export filtered to `{m['query_filter']}` — every query contains the brand word. "
                           f"An auditable lexicon classifies each: **{classified}%** of impressions classified, "
                           f"**{noise}%** isolated as non-skincare noise (vs a ~70% manual baseline).")
                st.dataframe(_pd.DataFrame([{
                    "Class": c["class"], "Queries": c["queries"], "Clicks": c["clicks"],
                    "Impressions": c["impressions"], "Impr %": c["impr_pct"]} for c in ins["classes"]]),
                    use_container_width=True, hide_index=True)
                noise_qs = [r["query"] for r in ins["query_table"] if r["class"] == "noise"][:12]
                if noise_qs:
                    st.caption("Excluded as noise: " + " · ".join(noise_qs))

            st.markdown("##### 🧴 Category demand (brand-name noise removed)")
            st.dataframe(_pd.DataFrame([{
                "Category": c["category"], "Queries": c["queries"], "Clicks": c["clicks"],
                "Impressions": c["impressions"]} for c in ins["categories"]]),
                use_container_width=True, hide_index=True)

            with st.expander("🔗 How demand interlinks (attributes searched together)"):
                st.dataframe(_pd.DataFrame([{
                    "Attribute A": p["a"], "Attribute B": p["b"], "Impressions": p["impressions"]}
                    for p in ins["interlinks"]]), use_container_width=True, hide_index=True)

            st.markdown("##### 🛠️ Biggest fixable opportunities (high demand, weak capture)")
            opp_pages = [p for p in ins["pages"] if p["underperforming"]][:12]
            if opp_pages:
                st.dataframe(_pd.DataFrame([{
                    "Page": p["page"], "Category": p["category"], "Impressions": p["impressions"],
                    "CTR %": p["ctr"], "Position": p["position"]} for p in opp_pages]),
                    use_container_width=True, hide_index=True)
            cS, cL = st.columns(2)
            with cS:
                st.markdown("**Striking distance (rank 8–20)**")
                st.dataframe(_pd.DataFrame([{
                    "Query": x["query"], "Pos": x["position"], "Impr": x["impressions"]}
                    for x in ins["striking"][:10]]), use_container_width=True, hide_index=True)
            with cL:
                st.markdown("**Low-CTR wins**")
                st.dataframe(_pd.DataFrame([{
                    "Query": x["query"], "Pos": x["position"], "CTR %": x["ctr"], "Exp %": x["expected"]}
                    for x in ins["low_ctr"][:10]]), use_container_width=True, hide_index=True)

            st.caption("ⓘ Seasonality note: this export's daily tab is totals, so per-category seasonal curves need "
                       "category-segmented exports (documented in the Excel's Methodology tab). Full detail — "
                       "all queries, pages, intent, geo, devices — is in the downloadable Excel.")

elif module.key == "comps_nemesis":
    from comps_nemesis import db as _cndb, changes as _cnch, report as _cnrep
    import pandas as _pd

    st.markdown("#### 🥷 Comp's Nemesis — competitor intelligence")
    st.caption("Built entirely from PUBLIC data — each brand's own Shopify storefront. A robot collects a "
               "fresh snapshot every 2 days; everything is benchmarked against Deconstruct and every row "
               "traces to a public URL. The team does nothing — just read.")

    @st.cache_data(ttl=600, show_spinner="Reading competitor database…")
    def _cn_load():
        return _cndb.latest_two()

    try:
        (prev_date, prev_cat), (curr_date, curr_cat) = _cn_load()
        db_ok = True
    except Exception as e:
        db_ok, curr_cat, curr_date, prev_cat, prev_date = False, {}, None, None, None
        st.error(f"Can't reach the competitor database — check DATABASE_URL in the app secrets. ({str(e)[:120]})")

    if db_ok and not curr_cat:
        st.info("No snapshots collected yet. The automatic collector runs every 2 days — the first snapshot "
                "will appear here right after it runs. (An admin can trigger the first run from the GitHub "
                "Action's 'Run workflow' button.)")
    elif db_ok:
        bench = _cnch.benchmark(curr_cat)
        diffs = _cnch.diff_all(prev_cat, curr_cat) if prev_cat else {}
        summ = _cnch.summarize(diffs) if diffs else {"total_launches": 0, "total_removals": 0}
        total_products = sum(len(v) for v in curr_cat.values())

        st.markdown(f"""<div class="metrics">
            <div class="metric"><div class="metric-val">{len(curr_cat)}</div><div class="metric-label">Brands tracked</div></div>
            <div class="metric"><div class="metric-val">{total_products:,}</div><div class="metric-label">Products monitored</div></div>
            <div class="metric"><div class="metric-val">{summ['total_launches']}</div><div class="metric-label">New launches</div><div class="metric-sub">since {prev_date or '—'}</div></div>
            <div class="metric"><div class="metric-val" style="font-size:17px;">{curr_date}</div><div class="metric-label">Latest snapshot</div></div>
        </div>""", unsafe_allow_html=True)

        if not prev_cat:
            st.info(f"📸 Baseline captured {curr_date}. Change-tracking (launches, price moves, stock flips) "
                    "activates automatically after the next collection (≤ 2 days).")

        xls = _cnrep.build_excel(curr_cat, diffs, bench, prev_date, curr_date)
        st.download_button("📥 Download full report (Excel)", data=xls,
                           file_name=f"comps_nemesis_{curr_date}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           type="primary", key="cn_dl")

        if prev_cat:
            launches = [x for b in diffs for x in diffs[b]["launches"]]
            st.markdown(f"##### 🆕 New launches since {prev_date} · {len(launches)} found")
            if launches:
                st.dataframe(_pd.DataFrame([{
                    "Brand": x["brand"], "Product": x["title"], "₹": x["price"],
                    "Type": x["product_type"], "Published": x["published_at"], "Source": x["url"]}
                    for x in launches]), use_container_width=True, hide_index=True)
            else:
                st.caption("No new products since the last snapshot.")

            cca, ccb = st.columns(2)
            with cca:
                pm = [x for b in diffs for x in diffs[b]["price_changes"] if not x.get("noise")]
                st.markdown(f"##### 💰 Price moves · {len(pm)}")
                if pm:
                    st.dataframe(_pd.DataFrame([{
                        "Brand": x["brand"], "Product": x["title"][:32],
                        "Old ₹": x["old_price"], "New ₹": x["new_price"], "Δ%": x["delta_pct"]}
                        for x in pm]), use_container_width=True, hide_index=True)
                else:
                    st.caption("None.")
            with ccb:
                sf = [x for b in diffs for x in diffs[b]["stock_changes"]]
                st.markdown(f"##### 📦 Stock flips · {len(sf)}")
                if sf:
                    st.dataframe(_pd.DataFrame([{
                        "Brand": x["brand"], "Product": x["title"][:32], "Event": x["event"]}
                        for x in sf]), use_container_width=True, hide_index=True)
                else:
                    st.caption("None.")

        st.markdown("##### 🏁 Catalog benchmark (Deconstruct = baseline, top row)")
        st.dataframe(_pd.DataFrame(bench).drop(columns=["is_baseline"]).rename(columns={
            "brand": "Brand", "products": "Products", "avg_price": "Avg ₹",
            "on_discount_%": "On discount %", "avg_discount_%": "Avg discount %",
            "out_of_stock": "Out of stock", "newest_launch": "Newest launch"}),
            use_container_width=True, hide_index=True)

        with st.expander("ⓘ Data Source Transparency — where every number comes from"):
            st.markdown(
                "- **Source:** each brand's own **public Shopify storefront JSON** (`/products.json`) — the exact "
                "data their website serves. No logins, no grey-hat scraping.\n"
                "- **Verifiable:** every row carries its **public product URL** — open it to check any figure.\n"
                "- **Launches / removals:** product handles that appear / disappear between snapshots.\n"
                "- **Price / discount / stock:** the same product's fields changing between snapshots.\n"
                "- **Cadence:** a GitHub Action collects a snapshot **every 2 days**, automatically; comparisons "
                "appear from the second snapshot onward.\n"
                "- **Junk SKUs** (₹1 promos, gift cards, testers) are flagged out of price stats, kept for launches.\n"
                "- **Baseline:** Deconstruct.")
