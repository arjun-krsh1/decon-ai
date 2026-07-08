# Market Intelligence Engine

A market-research platform for Deconstruct. One AI engine, many departments.
Each department is a **module**; the freebie module is the flagship.

## Run it (zero setup)

```bash
pip install -r requirements.txt
streamlit run app.py
```

Opens in your browser, works offline in **mock mode**. Use the sidebar to
switch departments (Freebie Intelligence ↔ Content & Social) — same screens,
same engine, different team. That switch is the platform demo.

## The big idea

Every department does the same four steps:

```
collect signals  ->  extract structure  ->  score vs a framework  ->  recommend / generate
```

So there is ONE generic engine (`core.py`) and each department is a small
config file (`modules/*.py`). Adding a department = adding one file. The
engine and UI never change.

## Files

| File | Role | Edit when… |
|------|------|-----------|
| `core.py` | Generic engine (recommend + generate) | almost never |
| `app.py` | Generic UI, driven by the active module | almost never |
| `llm.py` | Provider switch + cache (mock/Groq/Ollama) | almost never |
| `modules/base.py` | Defines what a Module is | almost never |
| `modules/freebies.py` | **Module #1** — Supply Chain (flagship) | building freebies |
| `modules/content.py` | **Module #2** — Content/Social (proof it scales) | building content |
| `modules/__init__.py` | Registry — list of active modules | adding a department |
| `warm_cache.py` | Pre-load demo answers for zero-latency stage demo | before demo |

## Add a new department (e.g. Product Development)

1. Copy `modules/freebies.py` to `modules/product_dev.py`.
2. Edit its data, `score()`, prompts, and the `MODULE = Module(...)` config.
3. Register it in `modules/__init__.py`.

Done. No other file changes. That extensibility IS your enterprise pitch.

## Speed / live demo (do not skip)

- **Never demo on Ollama** (slow on weak laptops). Demo on **Groq** (fast, free).
- Scores are pure Python math → they appear instantly, no model involved.
- Before the demo: configure Groq, edit the scenarios in `warm_cache.py` to
  match exactly what you'll click, then `python warm_cache.py`.
- For the demo: `DEMO_SAFE=1 streamlit run app.py` → only cached answers,
  instant, works even if the WiFi dies.
- Keep Ollama as your "runs fully offline inside company infra" pitch point.

## Enable live AI

```bash
export LLM_PROVIDER=groq
export GROQ_API_KEY=your_key   # free at console.groq.com
streamlit run app.py
```

## Hackathon scope discipline

Fully build the **freebie module**. Keep the **content module** as living proof
the platform scales. Present Product Dev / Pricing / etc. as the roadmap — do
not try to build five real data pipelines in one week. The synthetic data in
each module is a placeholder; say so in the pitch and show where real data plugs in.
```
```
