# Decon AI — Market Intelligence Engine
### An AI-native decision platform for D2C skincare

> Three production-grade **AI tools**, one engine. Each one takes a job that a team
> does manually over days — competitor research, shelf tracking, hiring — and turns it
> into a **grounded, AI-driven answer in minutes**.

**The three tools we're shipping:**
1. 🧠 **Product Intelligence** — AI competitor & category analyst (Amazon India)
2. 📊 **Market Share** — AI digital-shelf intelligence across 4 marketplaces
3. 🧑‍💼 **HR ATS AI** — AI resume screening & ranking engine

*Built on a multi-model AI core: Groq LPU (Llama 3.1 / 3.3, Gemma 2), local Ollama
(Llama 3.2), Google Gemini vision, and a provider-agnostic, self-caching LLM gateway.*

---
---

# 1 · 🧠 Product Intelligence
### *"Your AI competitor analyst that never sleeps."*

---

## The Problem We're Solving

- Brands make ₹-crore product bets on **gut feel** and week-old manual research.
- To understand ONE category on Amazon, a strategist manually opens dozens of listings,
  copies prices, reads hundreds of reviews, and still misses the signal.
- By the time the deck is ready, **the data is stale** and **the competitor set is incomplete**.
- Nobody can answer the CEO's real questions: *Where's the whitespace? What do we launch next? At what price?*

**In one line:** competitor intelligence is slow, shallow, biased, and out of date.

---

## How We're Doing It (AI Pipeline)

A **multi-stage AI agent** that goes from a category keyword → a boardroom-ready strategy:

1. **Acquire** — live pull of the real Amazon India shelf (prices, ratings, review counts, "bought last month", A+ bullets, and Amazon's own aggregated review *aspects*).
2. **Guarantee coverage** — a per-brand targeted crawl loop ensures **all 11 tracked competitors** are captured, not just whoever ranks today.
3. **Analyse** — an LLM extracts positioning, hero actives, claims, and — critically — **complaint signals mined from Amazon's full-base aspect counts**, not a handful of top reviews.
4. **Ground** — an *authoritative-facts override* forces every number (price, rating, ₹/ml) to come from source data; the **AI is only allowed to synthesize, never to invent a figure**.
5. **Decide** — a grounded **AI decision layer** produces two forward-looking deliverables:
   - **Category State-of-Play** — who's winning, why, and the biggest gaps.
   - **Launch / R&D Brief** — the exact next product to build, hero ingredient, target ₹ price band, claims, and names.

---

## The Tech Stack (this is where we invested)

**🤖 AI & Model Layer**
- **Groq LPU cloud inference** — Llama 3.1 8B Instant (fast path) + Llama 3.3 70B Versatile (deep reasoning) + Gemma 2 9B
- **Ollama local inference** — Llama 3.2 / Gemma for fully-private, offline runs
- **Provider-agnostic LLM gateway** — SHA-256 prompt-keyed disk cache, automatic 429 exponential-backoff, `DEMO_SAFE` zero-network mode
- **Prompt engineering** — structured-JSON extraction, temperature-0.1 determinism, **anti-hallucination grounding** (authoritative-facts override)

**🌐 Data Acquisition Layer**
- **SerpAPI** — Amazon India `search` + `amazon_product` structured engines
- **Apify actor integration** — deep review mining (gated tier)
- **Per-brand crawl orchestration** — guarantees full competitive coverage

**📊 NLP / Analytics Layer**
- **Aspect-based complaint mining** from marketplace-counted review aspects
- **Statistical engine** — price quartiles, **₹/ml normalization**, star-distribution, review time-series, demand modelling
- **Opportunity-gap detection** across the category

**📦 Delivery Layer**
- **Streamlit** app · **Plotly** interactive charts · **pandas + openpyxl** → **7-sheet Excel** (incl. State-of-Category + Launch Brief)
- Python 3.11 · on-disk result caching

---

## What The Solution Looks Like

- Type a category (e.g. *niacinamide serum*) → hit **Run**.
- A live dashboard: category KPIs, competitor scorecard, price/₹-ml bands, demand leaders, complaint heat-map.
- Two AI briefs rendered on screen: **State-of-Play** + **Launch Brief**.
- One click → **7-sheet Excel** the whole team can act on.

---

## How Easy Is It To Use

- **One input, one button.** No config, no spreadsheets, no manual scraping.
- Reads like a strategy memo, not a data dump — a founder gets it in 30 seconds.
- Pre-run + cached, so a live demo is **instant and zero-risk** (`DEMO_SAFE`).

---

## How Accurate Is It

- **Facts are source-exact — 0% estimation.** Every price, MRP, rating, review count and "bought last month" is read **directly from Amazon's structured data**, not guessed.
- **Complaint signals use Amazon's own full-base aspect counts** — statistically representative, not a biased top-10-review sample.
- **11/11 competitors guaranteed** via targeted per-brand crawl (Minimalist, Foxtale, The Derma Co., Dot & Key, Dr. Sheth's, Plum, Aqualogica, Pilgrim, Hyphen, Conscious Chemist + Deconstruct).
- **The AI cannot invent numbers** — the authoritative-facts override binds every figure to source; the model only *interprets*. Auditable end-to-end.

---
---

# 2 · 📊 Market Share
### *"AI eyes on every shelf, on every marketplace, every day."*

---

## The Problem We're Solving

- "What's our market share?" is unanswerable for D2C — there's no Nielsen for the digital shelf.
- Winning is decided by **share-of-shelf** and **search ranking** on Amazon, Nykaa, Myntra, Flipkart — and it changes weekly.
- Brands are **blind** to: which competitor owns which category, which keywords make products rank, and where they're simply **absent**.
- Manual checking across 4 sites × dozens of categories is impossible to sustain.

**In one line:** brands can't measure the shelf they actually compete on.

---

## How We're Doing It (AI Pipeline)

1. **Scan the shelf** — pull the top listings for each category across **Amazon · Nykaa · Myntra · Flipkart**.
2. **Extract the truth** — read each marketplace's **own hydration JSON** (the exact data the site renders) — not fragile HTML scraping.
3. **Measure** — compute **share-of-shelf**, ranking dominance, assortment breadth, and demand proxies, benchmarked against Deconstruct.
4. **Understand *why* with AI + NLP** — a **TF-IDF distinctiveness engine** surfaces the *peculiar* keywords that make products rank (not "serum" — but *gel, brightening, niacinamide, cooling*), per platform and per competitor.
5. **Explain** — an LLM writes the "**why the top products rank**" narrative and flags Deconstruct's distribution gaps.
6. **Track over time** — every run is snapshotted, so share-of-shelf movement is charted.

---

## The Tech Stack (this is where we invested)

**🕷️ Stealth Data Acquisition Layer**
- **Scrapling** — open-source, stealth, anti-bot headless scraping engine (the core of our multi-marketplace reach)
- **Embedded-JSON hydration extraction** — `window.__myx` (Myntra), `__PRELOADED_STATE__` (Nykaa), `__INITIAL_STATE__ / seoSchema` (Flipkart)
- **SerpAPI** — Amazon India structured engine
- **4-marketplace crawl orchestration** with per-platform parsers

**🤖 AI & NLP Layer**
- **TF-IDF distinctiveness keyword engine** — brand-name & generic-term exclusion, per-platform/per-competitor keyword attribution, product-level bifurcation (e.g. *Dot & Key Watermelon → cooling, hydration*)
- **Groq LPU inference** (Llama 3.1 / 3.3, Gemma 2) — ranking-driver explanations
- **Ollama** (Llama 3.2) local fallback · provider-agnostic cached gateway
- **Gap-analysis engine** — keyword whitespace Deconstruct isn't using

**📊 Analytics & Delivery Layer**
- Share-of-shelf math · rank aggregation · demand proxy modelling · **time-series snapshots**
- **Streamlit** · **Plotly** grouped/horizontal share charts · **9-sheet Excel with a documented methodology sheet**

---

## What The Solution Looks Like

- Pick categories + platforms → **Run Market-Share Analysis**.
- Headline metrics: Deconstruct shelf-share %, shelf leader, top-10 appearances, platforms present.
- **Scorecard** — Deconstruct vs every competitor (shelf %, SKUs, avg rank, rating, ₹, tier).
- Dashboard: share-of-shelf bars, per-platform breakdown, **winning keywords per platform**, share-over-time trend.
- **9-sheet Excel** with every formula documented.

---

## How Easy Is It To Use

- Select categories, hit one button — the shelf is measured across 4 sites automatically.
- Every number has a **plain-English "how this was calculated"** — no black boxes.
- Dashboards are self-explaining; the Excel is built for non-analysts.

---

## How Accurate Is It

- **Read straight from each marketplace's own data layer** — the same JSON the site uses to render — so listings, prices, ratings and ranks are **what the platform actually serves. No estimation.**
- **Share-of-shelf = real counts** of SKUs holding the top shelf for a search — a hard, reproducible number.
- **Demand is an explicitly-labelled proxy** (review volume) — we're transparent about what's measured vs modelled.
- **Keyword analysis is computed, not vibes** — TF-IDF with documented exclusion rules; the **methodology ships inside the Excel**. Fully auditable.

---
---

# 3 · 🧑‍💼 HR ATS AI
### *"An AI recruiter that reads every resume, fairly, in minutes."*

---

## The Problem We're Solving

- A single role attracts **hundreds of resumes**; humans skim ~6 seconds each and miss great candidates.
- Screening is **slow, inconsistent, and biased** — different reviewers weight things differently, and fatigue sets in by resume #40.
- There's **no audit trail** — "why was this candidate rejected?" has no defensible answer.
- Generic ATS keyword-matching rejects strong non-standard candidates.

**In one line:** hiring's first filter is a slow, inconsistent, unexplainable bottleneck.

---

## How We're Doing It (AI Pipeline)

1. **Ingest the JD** — parse the uploaded role (PDF / DOCX / TXT) into clean text.
2. **AI-structure the role** — an LLM extracts must-have skills, nice-to-haves, experience, education, responsibilities and culture cues into structured JSON.
3. **Generate an adaptive rubric** — the AI produces **role-specific evaluation criteria** ("what generic ATS systems miss for *this* role") and injects them into the scoring brief.
4. **Score on a weighted framework** — every candidate is graded across **5 weighted dimensions** and ranked 0–100.
5. **Explain every decision** — for each candidate: **Top 3 strengths + Top 2 gaps (evidence-cited)**, a hiring band, and notes.
6. **Deliver** — a ranked, Excel-ready shortlist + summary, top-3 write-ups, and pool-level red flags.

---

## The Tech Stack (this is where we invested)

**🤖 AI & Reasoning Layer**
- **Provider-agnostic LLM gateway** — Groq LPU (Llama 3.1 8B / Llama 3.3 70B / Gemma 2 9B) + Ollama local (Llama 3.2)
- **Two-stage prompt architecture** — LLM #1 structures the JD; **AI meta-prompting** generates a role-adaptive rubric; a frontier reasoning model executes candidate scoring
- **SHA-256 cached, temperature-controlled, `DEMO_SAFE`** deterministic inference

**📄 Document Intelligence Layer**
- **pdfplumber** (PDF), **python-docx** (DOCX), regex-fallback extraction — robust multi-format JD ingestion
- **Batch resume intake** — PDF attachments *or* Google Drive link sheets

**⚖️ Scoring & Delivery Layer**
- **5-dimension weighted model** — Skills 35% · Experience 25% · Education 15% · Culture 15% · Growth 10%
- **Explainable banding** — STRONG YES / YES / MAYBE / NO
- **17-column Excel-ready** ranked output (scores, evidence, gaps, recommendation, source)

---

## What The Solution Looks Like

- Upload a JD + point at the resumes → the engine builds an **expert AI recruiter brief** with a role-tuned rubric.
- Output: a **ranked table** — every candidate scored across 5 dimensions with a total, cited strengths/gaps, and a hiring call.
- Plus a summary (how many Strong-Yes/Yes/Maybe/No), top-3 candidate write-ups, and cross-pool red flags.

---

## How Easy Is It To Use

- **Drop a JD, drop resumes, get a ranked shortlist.** No setup.
- HR can add extra criteria in plain English — the AI folds it into the rubric.
- Output is Excel-ready — paste straight into the hiring tracker.

---

## How Accurate Is It

- **Reproducible & explainable** — a fixed weighted rubric means the same inputs give the same score, every time. Not a black box.
- **Evidence-cited** — every score carries **specific proof from the resume** (e.g. "5 yrs React, led team of 8"), so decisions are defensible and audit-ready.
- **Bias-reduced** — every candidate is judged on the **identical rubric**, removing reviewer drift and fatigue.
- **Role-adaptive** — AI-generated, JD-specific criteria catch strong candidates that keyword-only ATS systems reject.

---
---

# Appendix · The Decon AI Platform Stack
### *One shared, heavily-engineered AI core powers all three tools*

**🤖 Multi-Model AI Core**
- Groq LPU cloud — **Llama 3.1 8B Instant**, **Llama 3.3 70B Versatile**, **Gemma 2 9B**
- Ollama local inference — **Llama 3.2**, Gemma (offline / private)
- **Google Gemini 2.5** — vision + long-context reasoning (visual QA / verification)
- Provider-agnostic gateway: **SHA-256 disk cache**, **429 exponential-backoff**, `DEMO_SAFE` zero-network mode, mock/cloud/local hot-swap

**🌐 Data Acquisition**
- **Scrapling** (open-source stealth scraping) · **SerpAPI** · **Apify** actors · embedded-JSON hydration extraction · multi-site crawl orchestration

**📊 NLP · ML · Analytics**
- TF-IDF distinctiveness · aspect-based sentiment / complaint mining · statistical modelling (quartiles, ₹/ml, time-series) · best-of-N sampling + self-verification · anti-hallucination grounding

**📄 Document & Vision**
- pdfplumber · python-docx · PIL + numpy image compositing · Magnific / **Nano Banana Pro** generative imaging (Design suite)

**📦 App · Delivery · Infra**
- Streamlit · Plotly · pandas + openpyxl (multi-sheet Excel) · Python 3.11 · dotenv config · on-disk caching for demo-safe, zero-latency runs

> **The pitch in one line:** *We didn't build three demos — we built one grounded,
> multi-model AI engine and pointed it at three real business problems. Every number is
> source-true, every AI decision is explainable, and the whole thing ships today.*
