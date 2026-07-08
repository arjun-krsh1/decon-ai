"""
text_verify.py — automated label-text QC for product-swap results.

After the image model places your product into a scene, this compares the
GENERATED product's label against your ORIGINAL product photo using Gemini
vision, and returns a fidelity score (0-100) plus any specific text errors.

Used to pick the most-accurate candidate out of N renders and to show a
"text fidelity" badge before anything goes on stage — so distortion is caught
automatically, not by the audience.

Graceful: if GEMINI_API_KEY is absent or the call fails, returns score=None
(unverified) so the pipeline still works.
"""

from __future__ import annotations

import os
import json
import base64
import hashlib
import pathlib

import requests
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_VERIFY_MODEL", os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))

CACHE = pathlib.Path("scraper/cache/text_verify")
CACHE.mkdir(parents=True, exist_ok=True)

PASS_THRESHOLD = 90  # score >= this = safe to present

_PROMPT = """You are a strict quality inspector for product photography.

IMAGE 1 = the ORIGINAL product (the source of truth).
IMAGE 2 = a GENERATED image where that product was composited into a scene.

Compare ONLY the product's LABEL: its text, numbers, percentages, logo and
graphic marks. Ignore background, hand, lighting and angle differences.

Score how accurately IMAGE 2 reproduces the label of IMAGE 1, character by
character. 100 = every letter, number, word and logo is identical and crisp.
Deduct heavily for any missing, wrong, invented, misspelled, blurred, warped or
illegible text.

Return ONLY JSON:
{"score": <0-100 integer>,
 "issues": ["specific text/logo problems, empty list if none"],
 "verdict": "PASS" or "FAIL"}
Start with {"""


def _b64(b: bytes) -> str:
    return base64.b64encode(b).decode("utf-8")


def _cache_path(source_bytes: bytes, candidate_url: str) -> pathlib.Path:
    key = hashlib.md5(hashlib.md5(source_bytes).digest()
                      + candidate_url.encode()).hexdigest()
    return CACHE / f"{key}.json"


def verify_label_fidelity(source_product_bytes: bytes, source_mime: str,
                          candidate_image_url: str) -> dict:
    """
    Compare a generated candidate against the original product photo.
    Returns {"score": int|None, "issues": [str], "verdict": str, "error": str}.
    score is None when verification could not run (no key / fetch / API error).
    """
    result = {"score": None, "issues": [], "verdict": "UNVERIFIED", "error": ""}
    if not GEMINI_API_KEY:
        result["error"] = "No GEMINI_API_KEY"
        return result
    if not candidate_image_url:
        result["error"] = "No candidate image"
        return result

    cache_file = _cache_path(source_product_bytes, candidate_image_url)
    if cache_file.exists():
        try:
            return json.loads(cache_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    try:
        cand = requests.get(candidate_image_url, timeout=30).content
        url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
               f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}")
        payload = {
            "contents": [{"parts": [
                {"text": _PROMPT},
                {"inline_data": {"mime_type": source_mime or "image/jpeg",
                                 "data": _b64(source_product_bytes)}},
                {"inline_data": {"mime_type": "image/jpeg", "data": _b64(cand)}},
            ]}],
            "generationConfig": {"temperature": 0},
        }
        r = requests.post(url, json=payload, timeout=60)
        r.raise_for_status()
        cand_json = r.json()
        text = " ".join(
            p.get("text", "")
            for p in cand_json.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        ).strip()
        data = json.loads(text[text.index("{"): text.rindex("}") + 1])

        score = int(data.get("score", 0))
        result = {
            "score": score,
            "issues": [str(i) for i in data.get("issues", [])],
            "verdict": data.get("verdict", "PASS" if score >= PASS_THRESHOLD else "FAIL"),
            "error": "",
        }
        cache_file.write_text(json.dumps(result, indent=2, ensure_ascii=False),
                              encoding="utf-8")
        return result

    except Exception as e:
        result["error"] = str(e)
        return result
