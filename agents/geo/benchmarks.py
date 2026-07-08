"""
benchmarks.py — external, citable benchmarks about how AI engines surface brands.

Every recommendation the agent makes must carry a number. When the run's own
measured data isn't enough to justify a point, the playbook falls back to these
published benchmarks. Keep them here as single-source-of-truth constants.

Sources: aggregated GEO (Generative Engine Optimization) research, 2024–2025.
Treat as directional industry figures, not guarantees.
"""

# Share of AI citations by source, across major engines (ChatGPT, Gemini, Perplexity)
REDDIT_CITATION_SHARE = 40            # % — Reddit is the #1 cited source
WIKIPEDIA_CHATGPT_SHARE_LOW = 26      # % — low end of Wikipedia in ChatGPT top citations
WIKIPEDIA_CHATGPT_SHARE_HIGH = 48     # % — high end
TOP15_DOMAINS_SHARE = 68             # % of all AI citation share held by top 15 domains
STRUCTURED_VERIFIED_SHARE = 54       # % of citations from verified/structured/distributed data

# Content-shape levers (uplift to AI visibility / citation likelihood)
STATISTICS_UPLIFT = 22               # % more visibility when a page includes statistics
QUOTATION_UPLIFT = 37                # % more visibility when a page includes direct quotations
SELF_CONTAINED_CHUNK_MULTIPLIER = 2.3  # x more citations for 50–150 word self-contained chunks
CHUNK_MIN_WORDS = 50
CHUNK_MAX_WORDS = 150

# Human-readable one-liners the playbook can drop in verbatim.
NOTES = {
    "reddit": (
        f"Reddit is the single most-cited source in AI answers "
        f"(~{REDDIT_CITATION_SHARE}% citation frequency across major engines)."
    ),
    "wikipedia": (
        f"Wikipedia/structured data drives {WIKIPEDIA_CHATGPT_SHARE_LOW}–"
        f"{WIKIPEDIA_CHATGPT_SHARE_HIGH}% of ChatGPT's top citations; "
        f"Wikidata is foundational."
    ),
    "top15": (
        f"The top 15 domains capture ~{TOP15_DOMAINS_SHARE}% of all AI citation "
        f"share — being on those pages matters more than net-new pages."
    ),
    "structured": (
        f"~{STRUCTURED_VERIFIED_SHARE}% of AI citations come from verified, "
        f"structured or distributed data."
    ),
    "statistics": f"Adding statistics to a page lifts AI visibility ~{STATISTICS_UPLIFT}%.",
    "quotations": f"Adding direct quotations lifts AI visibility ~{QUOTATION_UPLIFT}%.",
    "chunks": (
        f"Self-contained {CHUNK_MIN_WORDS}–{CHUNK_MAX_WORDS} word chunks get "
        f"~{SELF_CONTAINED_CHUNK_MULTIPLIER}x more citations than unstructured text."
    ),
}
