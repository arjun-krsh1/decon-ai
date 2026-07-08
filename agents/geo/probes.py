"""
probes.py — the "mystery shopper" layer.

Each Prober asks an AI assistant a buyer question with WEB SEARCH ON and returns
the answer text plus the source URLs the model cited. The rest of the pipeline
is provider-agnostic, so adding a provider = adding a Prober here.

Providers:
    GeminiProber   — Google Gemini + Google Search grounding (free tier). PRIMARY.
                     Measures what a real engine on Google's index recommends.
    SerpGroqProber — SerpAPI (Google results) + Groq synthesis. Runs on keys you
                     already have. A proxy for a real engine, useful as fallback
                     and for cheap scale.
    MockProber     — deterministic offline data so the full loop runs with no keys.

The probe NEVER asks the model to explain its ranking logic (models can't
introspect that reliably). It only observes what gets recommended and cited.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field

import requests

from .taxonomy import domain_of

SHOPPER_SYSTEM = (
    "You are a helpful shopping assistant for a consumer in India. "
    "When asked for product recommendations, search the web and recommend "
    "specific, currently-available named brands and products sold in India. "
    "Present them as a clear ranked list, best first, with a one-line reason each. "
    "Prefer options a real shopper could buy today."
)

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
_RESOLVE_REDIRECTS = os.getenv("GEO_RESOLVE_REDIRECTS", "1") == "1"
_redirect_cache: dict[str, str] = {}


@dataclass
class ProbeResult:
    question: str
    answer: str = ""
    sources: list[str] = field(default_factory=list)   # domains or URLs
    model: str = ""
    error: str = ""


def _resolve_domain(url: str, fallback_title: str = "") -> str:
    """
    Gemini grounding returns redirect URLs; resolve to the real domain when we
    can, else use the chunk title (often already a domain), else the raw domain.
    Cached so repeated sources across questions cost one lookup.
    """
    title_dom = domain_of(fallback_title) if fallback_title else ""
    if "grounding-api-redirect" not in url and "vertexaisearch" not in url:
        return domain_of(url) or title_dom or fallback_title

    if url in _redirect_cache:
        return _redirect_cache[url]

    resolved = ""
    if _RESOLVE_REDIRECTS:
        try:
            r = requests.get(url, allow_redirects=True, timeout=8,
                             headers={"User-Agent": "Mozilla/5.0"})
            resolved = domain_of(r.url)
        except Exception:
            resolved = ""
    resolved = resolved or title_dom or (fallback_title or "unknown")
    _redirect_cache[url] = resolved
    return resolved


class Prober:
    name = "base"

    def available(self) -> bool:
        raise NotImplementedError

    def probe(self, question: str) -> ProbeResult:
        raise NotImplementedError


class GeminiProber(Prober):
    name = "gemini"

    def __init__(self):
        self.key = os.getenv("GEMINI_API_KEY", "")

    def available(self) -> bool:
        return bool(self.key)

    def probe(self, question: str) -> ProbeResult:
        if not self.key:
            return ProbeResult(question, error="No GEMINI_API_KEY", model=self.name)
        url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
               f"{GEMINI_MODEL}:generateContent?key={self.key}")
        payload = {
            "systemInstruction": {"parts": [{"text": SHOPPER_SYSTEM}]},
            "contents": [{"parts": [{"text": question}]}],
            "tools": [{"google_search": {}}],
        }
        try:
            r = requests.post(url, json=payload, timeout=60)
            r.raise_for_status()
            data = r.json()
            cand = (data.get("candidates") or [{}])[0]
            parts = cand.get("content", {}).get("parts", [])
            answer = " ".join(p.get("text", "") for p in parts).strip()

            sources: list[str] = []
            gm = cand.get("groundingMetadata", {})
            for chunk in gm.get("groundingChunks", []):
                web = chunk.get("web", {})
                uri, title = web.get("uri", ""), web.get("title", "")
                dom = _resolve_domain(uri, title) if uri else domain_of(title)
                if dom and dom not in sources:
                    sources.append(dom)

            if not answer:
                return ProbeResult(question, error="Empty Gemini answer", model=self.name)
            return ProbeResult(question, answer=answer, sources=sources, model=self.name)
        except Exception as e:
            return ProbeResult(question, error=f"Gemini error: {e}", model=self.name)


class SerpGroqProber(Prober):
    """SerpAPI (real Google results) + Groq synthesis. Runs on existing keys."""
    name = "serpgroq"

    def __init__(self):
        self.serp_key = os.getenv("SERPAPI_KEY", "")

    def available(self) -> bool:
        from llm import groq_available
        return bool(self.serp_key) and groq_available()

    def probe(self, question: str) -> ProbeResult:
        from llm import groq_chat, groq_available
        if not self.serp_key:
            return ProbeResult(question, error="No SERPAPI_KEY", model=self.name)
        if not groq_available():
            return ProbeResult(question, error="No GROQ_API_KEY", model=self.name)
        try:
            r = requests.get(
                "https://serpapi.com/search",
                params={"engine": "google", "q": question, "gl": "in",
                        "hl": "en", "num": 10, "api_key": self.serp_key},
                timeout=30,
            )
            r.raise_for_status()
            organic = r.json().get("organic_results", [])[:10]
            sources = [o.get("link", "") for o in organic if o.get("link")]
            context = "\n".join(
                f"- {o.get('title','')}: {o.get('snippet','')} ({o.get('link','')})"
                for o in organic
            )
            prompt = (
                f"A shopper in India asked: \"{question}\"\n\n"
                f"Here are live Google results:\n{context}\n\n"
                f"Acting as a shopping assistant, recommend the best specific named "
                f"products/brands available in India, as a ranked list (best first) "
                f"with a one-line reason each. Base it only on these results."
            )
            answer = groq_chat(prompt, system=SHOPPER_SYSTEM, temperature=0.3, max_tokens=900)
            if not answer:
                return ProbeResult(question, error="Groq synthesis empty",
                                   sources=sources, model=self.name)
            return ProbeResult(question, answer=answer, sources=sources, model=self.name)
        except Exception as e:
            return ProbeResult(question, error=f"SerpGroq error: {e}", model=self.name)


class MockProber(Prober):
    """Deterministic offline probe so the pipeline runs with zero keys."""
    name = "mock"

    def available(self) -> bool:
        return True

    def probe(self, question: str) -> ProbeResult:
        time.sleep(0.02)
        q = question.lower()
        # Deconstruct deliberately absent from most discovery answers (the problem).
        answer = (
            "For this, popular options in India are: "
            "1. Minimalist — well reviewed and affordable. "
            "2. Dot & Key — widely recommended. "
            "3. The Derma Co — dermatologist-led range. "
            "4. Foxtale — trending among younger buyers. "
            "5. Aqualogica — good for hydration."
        )
        if "deconstruct" in q:  # branded question → brand appears
            answer += " Deconstruct is also a solid science-led choice."
        sources = ["reddit.com", "nykaa.com", "beminimalist.co",
                   "thedermaco.com", "youtube.com"]
        return ProbeResult(question, answer=answer, sources=sources, model=self.name)


# registry — order defines auto-selection preference (best fidelity first)
_PROBERS = {
    "gemini": GeminiProber,
    "serpgroq": SerpGroqProber,
    "mock": MockProber,
}


def get_prober(name: str) -> Prober:
    cls = _PROBERS.get(name.lower())
    if not cls:
        raise ValueError(f"Unknown prober '{name}'. Options: {list(_PROBERS)}")
    return cls()


def resolve_probers(models: list[str]) -> list[Prober]:
    """
    Turn requested model names into available Prober instances.
    'auto' picks the best available real provider, falling back to mock so a run
    never dies just because a key is missing.
    """
    chosen: list[Prober] = []
    requested = [m.lower() for m in (models or ["auto"])]

    if "auto" in requested:
        for name in ("gemini", "serpgroq", "mock"):
            p = get_prober(name)
            if p.available():
                chosen.append(p)
                break
    for m in requested:
        if m == "auto":
            continue
        p = get_prober(m)
        if p.available() and not any(c.name == p.name for c in chosen):
            chosen.append(p)

    if not chosen:
        chosen.append(MockProber())
    return chosen
