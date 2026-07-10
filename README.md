---
title: Decon AI — Market Intelligence Engine
emoji: 🧬
colorFrom: green
colorTo: gray
sdk: streamlit
app_file: app.py
pinned: false
python_version: "3.12"
---

# 🧬 Decon AI — Market Intelligence Engine

An AI decision platform for Deconstruct. One engine, five tools:

- **🧠 Product Intelligence** — live Amazon India competitor & category analysis with AI launch/R&D briefs.
- **📊 Market Share** — digital-shelf share across Amazon · Nykaa · Myntra · Flipkart, plus a **Google Console** tab that turns a Search Console export into a brand-manager report (noise-cleaned, 16-tab Excel).
- **🧑‍💼 HR ATS AI** — JD-aware resume screening and a ranked, evidence-cited shortlist.
- **🎨 Design** — product-in-scene replacement (Nano Banana Pro) + guaranteed-text **Logo Lock**.
- **🔍 Market Content Visibility (GEO)** — where the brand shows up when shoppers ask AI assistants.

Built on a provider-agnostic AI core (Groq · Google Gemini), live data (SerpAPI · ScraperAPI · Scrapling),
and grounded, auditable analytics — every number traces to a source.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Configuration (environment variables / host secrets)

| Variable | Purpose |
|---|---|
| `LLM_PROVIDER=groq` | selects the AI provider |
| `GROQ_API_KEY` | AI text analysis (all tools) |
| `SERPAPI_KEY` | Amazon India data |
| `GEMINI_API_KEY` | Design text-fidelity check + GEO probes |
| `MAGNIFIC_API_KEY` | Design image generation |
| `SCRAPER_API_KEY` | Nykaa/Myntra/Flipkart scraping from cloud IPs |
| `APIFY_KEY` | optional deep-review scraping |

Locally these live in a `.env`; on a host, set them as secrets/environment variables.
