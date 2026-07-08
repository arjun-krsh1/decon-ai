"""
llm.py — one place that talks to a language model, with on-disk caching.

The rest of the app never cares WHICH provider is used. It just calls
ask_llm(...). Switch providers by setting an environment variable:

    LLM_PROVIDER=mock     -> no setup, runs offline with templated text (default)
    LLM_PROVIDER=groq     -> fast + free cloud (needs GROQ_API_KEY)  [USE THIS LIVE]
    LLM_PROVIDER=ollama    -> fully local / private (needs Ollama running) [SLOW on weak laptops]

CACHING (the demo-safety feature):
Every ask_llm() answer is saved to .cache/llm_cache.json keyed by the exact
prompt, so repeated prompts return INSTANTLY from disk — no network, no model,
no risk even if the WiFi dies. Set DEMO_SAFE=1 to never make a live call.

groq_chat() is a direct Groq call (uncached) for agents that always need a real
LLM regardless of LLM_PROVIDER — e.g. the GEO agent's extractor.
"""

import os
import json
import time
import hashlib
import pathlib
import requests
from dotenv import load_dotenv

# Load .env HERE, before reading any config below. This module is imported by
# app.py before its own load_dotenv() runs, so we must not depend on the caller
# having loaded the environment first.
load_dotenv()

PROVIDER = os.getenv("LLM_PROVIDER", "mock").lower()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

# Set DEMO_SAFE=1 to NEVER make a live call — only use cache or templated
# fallback. Use this on stage for guaranteed zero-latency, zero-risk.
DEMO_SAFE = os.getenv("DEMO_SAFE", "0") == "1"

_CACHE_DIR = pathlib.Path(__file__).parent / ".cache"
_CACHE_FILE = _CACHE_DIR / "llm_cache.json"


def _load_cache():
    if _CACHE_FILE.exists():
        try:
            return json.loads(_CACHE_FILE.read_text())
        except Exception:
            return {}
    return {}


def _save_cache(cache):
    _CACHE_DIR.mkdir(exist_ok=True)
    _CACHE_FILE.write_text(json.dumps(cache, indent=2))


def _key(prompt, system, temperature):
    raw = f"{PROVIDER}|{GROQ_MODEL}|{OLLAMA_MODEL}|{temperature}|{system}|{prompt}"
    return hashlib.sha256(raw.encode()).hexdigest()


def llm_available() -> bool:
    """True if a real model is wired up. False means we're in mock mode."""
    if PROVIDER == "groq":
        return bool(GROQ_API_KEY)
    if PROVIDER == "ollama":
        return True
    return False


def ask_llm(prompt: str, system: str = "You are a concise analyst.",
            temperature: float = 0.4, max_tokens: int = 1024) -> str:
    """Send a prompt, get back text. Order of resolution:
    1. cache hit  -> instant, no network (this is what makes the demo safe)
    2. DEMO_SAFE  -> never call live; return "" so caller uses its template
    3. live call  -> Groq (fast) or Ollama, result is then cached
    Returns "" in mock mode so callers fall back to templated output.

    max_tokens raises the output cap for large structured JSON (it does not
    change the cache key, so identical prompts still share a cache entry)."""
    cache = _load_cache()
    k = _key(prompt, system, temperature)
    if k in cache:
        return cache[k]

    if DEMO_SAFE:
        return ""  # refuse live calls on stage; caller falls back to template

    text = ""
    try:
        if PROVIDER == "groq" and GROQ_API_KEY:
            text = _ask_groq(prompt, system, temperature, max_tokens)
        elif PROVIDER == "ollama":
            text = _ask_ollama(prompt, system, temperature)
    except Exception as e:
        print(f"[llm] provider error, falling back to mock: {e}")
        text = ""

    if text:
        cache[k] = text
        _save_cache(cache)
    return text


def groq_available() -> bool:
    """True if a Groq key is configured (independent of the active PROVIDER)."""
    return bool(GROQ_API_KEY)


def groq_chat(prompt: str, system: str = "You are a precise analyst.",
              temperature: float = 0.2, model: str = "", max_tokens: int = 1024,
              max_retries: int = 3) -> str:
    """
    Direct Groq chat call, regardless of LLM_PROVIDER. Used by agents that always
    need a real LLM (e.g. the GEO extractor) rather than the mock/cache path.

    Retries on HTTP 429 (rate limit), honouring the `Retry-After` header with
    exponential backoff, so large batch runs (e.g. Brand Media) self-throttle
    instead of dropping items. Returns "" if no key or on persistent failure —
    callers must handle the empty case.
    """
    if not GROQ_API_KEY:
        return ""
    payload = {
        "model": model or GROQ_MODEL,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    }
    backoff = 2.0
    for attempt in range(max_retries):
        try:
            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                json=payload,
                timeout=45,
            )
            if r.status_code == 429:
                wait = min(float(r.headers.get("retry-after", backoff)), 20.0)
                print(f"[llm] groq rate-limited (429) — waiting {wait:.0f}s "
                      f"(attempt {attempt + 1}/{max_retries})")
                time.sleep(wait)
                backoff *= 2
                continue
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"[llm] groq_chat error: {e}")
            return ""
    print("[llm] groq_chat: giving up after repeated 429s")
    return ""


def _ask_groq(prompt, system, temperature, max_tokens=1024):
    return groq_chat(prompt, system, temperature, max_tokens=max_tokens)


def _ask_ollama(prompt, system, temperature):
    r = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model": OLLAMA_MODEL,
            "stream": False,
            "options": {"temperature": temperature},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        },
        timeout=120,
    )
    r.raise_for_status()
    return r.json()["message"]["content"].strip()
