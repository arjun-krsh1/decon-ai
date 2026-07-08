# Deploying Decon AI on Render

The app runs **identically** to your local machine — same code, same pinned package
versions (`requirements.txt`), same keys (read from environment variables). No code
changes are needed to host it; these are the only steps.

---

## Before you start
1. **Rotate the API keys** that were shared in chat (Groq, Gemini, Magnific, Apify, the
   Google service-account). Put the **fresh** values into Render (Step 3) — never into the repo.
2. Make sure `.env` is **not** committed — the included `.gitignore` already blocks it.
3. Have a (private) **GitHub repo** and a free **Render** account.

## Step 1 — Push the code to GitHub (private repo)
```bash
git init
git add .
git commit -m "Decon AI"
git branch -M main
git remote add origin https://github.com/<you>/decon-ai.git
git push -u origin main
```
Double-check `.env` did **not** get pushed (it shouldn't — `.gitignore` blocks it).

## Step 2 — Create the service on Render
- Render dashboard → **New + → Blueprint** → select this repo. It reads `render.yaml`
  and configures everything (build command, start command, Python version).
- *(Manual alternative — New + → Web Service:)*
  - Build command: `pip install -r requirements.txt`
  - Start command: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true`
  - Add env var `PYTHON_VERSION = 3.13.4`

## Step 3 — Add your keys (Environment tab)
Set these as environment variables in Render (values only in the dashboard):

| Variable | Needed for | Required? |
|---|---|---|
| `LLM_PROVIDER` = `groq` | all AI features | ✅ |
| `GROQ_API_KEY` | all AI text (Product Intel, HR, GSC, GEO) | ✅ |
| `SERPAPI_KEY` | Amazon data (Product Intel + Market Share) | ✅ |
| `GEMINI_API_KEY` | Design text-fidelity check + GEO | ✅ |
| `MAGNIFIC_API_KEY` | Design image generation | ✅ |
| `APIFY_KEY` | deep-review scraping (optional) | ⬜ |
| `GSC_SA_JSON` | GSC *live* API (the CSV/Excel import needs nothing) | ⬜ |

## Step 4 — Deploy & share
- Click **Deploy**. First build takes a few minutes (installing the packages).
- Open the URL Render gives you, smoke-test each tool, then send the URL to the team.

---

## Good to know
- **Free plan sleeps** after 15 min idle (first visitor waits ~40s to wake it). Switch
  `plan: free` → `starter` in `render.yaml` (or the dashboard) for always-on (~$7/mo).
- **No login** (as requested) → anyone with the URL can open it. The URL is random and
  hard to guess — treat it as sensitive and don't post it publicly.
- **The only thing that can differ from local:** live scraping of Nykaa/Myntra/Flipkart
  may hit anti-bot from Render's datacenter IP. Amazon (SerpAPI) and every other tool are
  identical. Pre-run one Market-Share scan so the cache serves the team full data.
- **Redeploys** happen automatically on every `git push` (`autoDeploy: true`).
