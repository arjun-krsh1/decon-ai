"""
image_gen.py — Image Generation & Editing via Magnific API (Nano Banana Pro Flash)

Public functions:
1. generate_image()       — text-to-image, or edit a single reference image.
2. generate_image_multi() — combine several reference images in one generation
                            (e.g. place a product into an existing scene).

Endpoint: POST /v1/ai/text-to-image/nano-banana-pro-flash
Auth:     x-magnific-api-key header
Flow:     async — submit job → poll until COMPLETED → return image URL

Results are cached to scraper/cache/generated_images/ for CACHE_TTL_HOURS so
repeated prompts return instantly (and cheaply).
"""

import os
import json
import time
import base64
import hashlib
import pathlib

import requests
from dotenv import load_dotenv

load_dotenv()

MAGNIFIC_KEY = os.getenv("MAGNIFIC_API_KEY", "")
# Two Nano Banana models are available on Magnific:
#   flash — fast + cheaper, but weaker at reproducing exact small text
#   pro   — slower, best-in-class at exact label text (used for product swaps)
FLASH_MODEL = "nano-banana-pro-flash"
PRO_MODEL = "nano-banana-pro"
# Default model for the general Design tabs (override via .env MAGNIFIC_MODEL).
MODEL = os.getenv("MAGNIFIC_MODEL", FLASH_MODEL)


def _endpoint(model=None):
    """Magnific text-to-image endpoint for a given model (defaults to MODEL)."""
    return f"https://api.magnific.com/v1/ai/text-to-image/{model or MODEL}"


BASE_URL = _endpoint()  # default endpoint (kept for back-compat)

CACHE = pathlib.Path("scraper/cache/generated_images")
CACHE.mkdir(parents=True, exist_ok=True)
CACHE_TTL_HOURS = 24

# how long to wait for an async job (60 polls * 3s = ~3 minutes) — the Pro model
# at 4K is slower than Flash, so give it comfortable headroom before timing out.
_POLL_ATTEMPTS = 60
_POLL_INTERVAL = 3


# ── Product-swap prompt engineering ───────────────────────────────────────────
# Replacing a product in a scene while keeping its LABEL TEXT perfectly intact is
# the hardest part for an image model. The prompt is "bookended": the text-fidelity
# rule is stated FIRST (highest attention) and restated LAST as a pass/fail check.

_SWAP_SCENE_INSTRUCTION = (
    "This is the SCENE image — the environment AND the correct size/position. Keep "
    "every part of it 100% identical: the hand, fingers, grip and skin tone; the "
    "background, surfaces, fabric and props; the lighting direction, intensity, "
    "colour temperature and shadows; the camera angle, framing and depth of field. "
    "CRITICAL: the product already in this scene is at the CORRECT size and "
    "position — the replacement must occupy the EXACT same footprint (same height, "
    "same width, same spot, same distance and angle to the fingers). The fingers "
    "must wrap the new product exactly as they wrap the original. Do NOT alter "
    "anything here and do NOT resize, zoom or re-frame. Only the product's surface "
    "appearance changes."
)

_SWAP_PRODUCT_INSTRUCTION = (
    "This is the reference for the product's APPEARANCE and LABEL ONLY. Reproduce "
    "it EXACTLY: every letter, number, word, percentage, symbol and logo on its "
    "label must appear letter-for-letter as shown here — same spelling, characters, "
    "order, fonts and placement. Preserve its exact shape, proportions, colours, "
    "gradients, finish and every graphic element. Do NOT redesign, restyle, "
    "translate, paraphrase, blur, warp, mirror or re-letter any part of it. "
    "IMPORTANT: do NOT use this image's size, crop, zoom or framing to decide how "
    "big the product appears — the output size and position come ENTIRELY from the "
    "SCENE image. Treat its label as a photo to be composited, never redrawn."
)


def build_swap_prompt(extra_instruction: str = "") -> str:
    """
    Build the strict, text-first prompt for replacing a product inside a scene.
    Text fidelity is asserted at the top AND bottom (bookended) because that is
    what the model attends to most.
    """
    extra = f"\n\nADDITIONAL DIRECTION FROM THE TEAM:\n{extra_instruction.strip()}" \
        if extra_instruction and extra_instruction.strip() else ""

    return f"""TASK: Inside the SCENE image, replace ONLY the product with the one shown in the PRODUCT image, keeping it at the EXACT same size and position as the product it replaces. Change nothing else.

#1 PRIORITY — TEXT FIDELITY:
Every letter, number, word, percentage, symbol and logo on the new product's label MUST be reproduced EXACTLY as it appears in the PRODUCT image — identical spelling, characters, order, fonts, sizes and placement. Do NOT invent, translate, paraphrase, drop, blur, smudge, warp, stretch, mirror or re-letter ANY text. Small text must stay crisp and legible — never gibberish. Treat the label as a photograph to be composited, not redrawn.

#2 PRIORITY — SIZE & PLACEMENT LOCK:
The new product MUST occupy the EXACT same footprint as the product it replaces in the SCENE: identical height and width within the frame, identical position, identical distance and angle relative to the hand and fingers. The fingers must wrap it exactly as they wrapped the original. Do NOT enlarge, shrink, zoom, rescale, re-centre or re-crop the product or the photo. The PRODUCT image is a reference for APPEARANCE and LABEL ONLY — IGNORE its size, crop and framing; never scale the output to match the product image. If the original bottle spans a certain height in the hand, the new one spans the identical height.

PRESERVE THE PRODUCT'S APPEARANCE EXACTLY:
- All label text and typography (see priority #1 — non-negotiable)
- The exact shape, silhouette, proportions, colours, gradients, finish and material
- The logo, icons and every graphic element
- Never restyle, redesign or "improve" the product

KEEP THE SCENE 100% IDENTICAL:
- Hand position, fingers, grip and skin tone — unchanged
- Background, surfaces, fabric and props — unchanged
- Lighting direction, intensity, colour temperature and shadows — unchanged
- Camera angle, composition, framing and depth of field — unchanged

INTEGRATION:
- Think of this as re-skinning the existing product in place: keep its exact size and position, change only its surface appearance to match the PRODUCT image
- Adapt ONLY the new product's lighting and shadows so it sits naturally in the scene
- Nothing outside the product may change{extra}

FINAL CHECK BEFORE YOU OUTPUT (non-negotiable):
1. Re-read every character on the product label — it MUST match the PRODUCT image letter-for-letter. Any wrong, distorted or invented text = FAILURE, redo it.
2. The product is the SAME size and in the SAME position as the original — the hand holds it identically. If it looks larger, smaller, zoomed or re-framed, that is a FAILURE, redo it.
3. The product's shape, colours and logo are unchanged; everything outside the product (hand, background, lighting) is identical to the SCENE image.
Perfect label text AND identical size/placement are the two most important requirements of this task."""


_AR_VALUES = {"1:1": 1.0, "4:5": 0.8, "3:4": 0.75, "2:3": 2 / 3,
              "9:16": 9 / 16, "16:9": 16 / 9}


def nearest_aspect_ratio(image_bytes, options=("1:1", "4:5", "3:4", "9:16", "16:9")):
    """
    Return the supported aspect-ratio string closest to an image's real shape.
    Used so a product swap keeps the SCENE's framing — forcing a mismatched ratio
    makes the model crop/zoom, which changes the product's apparent size.
    """
    try:
        import io
        from PIL import Image
        w, h = Image.open(io.BytesIO(image_bytes)).size
        ratio = w / h if h else 1.0
    except Exception:
        return options[0]
    cand = {o: _AR_VALUES[o] for o in options if o in _AR_VALUES}
    return min(cand, key=lambda o: abs(cand[o] - ratio))


def _headers():
    return {
        "x-magnific-api-key": MAGNIFIC_KEY,
        "Content-Type": "application/json",
    }


def _data_uri(image_bytes, mime="image/jpeg"):
    """Encode raw image bytes as a base64 data URI the API accepts."""
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:{mime};base64,{b64}"


def _reference_block(image_bytes, mime, instruction):
    """Build one entry for the API's `reference_images` list."""
    return {
        "image": _data_uri(image_bytes, mime),
        "text": instruction or "Reference image",
        "mime_type": mime,
    }


def _cache_file(prefix, prompt, aspect_ratio, resolution, seed, model=None):
    """Deterministic cache path. `seed` distinguishes reference images; `model`
    keeps Pro and Flash renders in separate cache entries."""
    key = hashlib.md5(
        f"{prompt}{aspect_ratio}{resolution}{seed}{model or MODEL}".encode()
    ).hexdigest()
    return CACHE / f"{prefix}{key}.json"


def _read_cache(cache_file):
    """Return a cached result (with cached=True) if fresh, else None."""
    if cache_file.exists():
        age_hours = (time.time() - cache_file.stat().st_mtime) / 3600
        if age_hours < CACHE_TTL_HOURS:
            cached = json.loads(cache_file.read_text(encoding="utf-8"))
            cached["cached"] = True
            return cached
    return None


def _poll_task(task_id, base_url=None):
    """Poll a submitted job until it completes. Returns the image URL or None."""
    base_url = base_url or BASE_URL
    for _ in range(_POLL_ATTEMPTS):
        time.sleep(_POLL_INTERVAL)
        r = requests.get(f"{base_url}/{task_id}", headers=_headers(), timeout=30)
        body = r.json()
        inner = body.get("data", body)
        status = inner.get("status", "")

        if status == "COMPLETED":
            generated = inner.get("generated", [])
            if not generated:
                return None
            first = generated[0]
            return first if isinstance(first, str) else first.get("url")

        if status in ("FAILED", "ERROR", "CANCELLED"):
            print(f"[image_gen] task {status}")
            return None

    return None  # timed out


def _submit_and_poll(payload, mode, cache_file, extra=None, base_url=None, model=None):
    """Submit a generation job, poll it, cache and return the result dict."""
    base_url = base_url or BASE_URL
    r = requests.post(base_url, headers=_headers(), json=payload, timeout=30)
    r.raise_for_status()
    data = r.json()
    task_id = data.get("data", {}).get("task_id") or data.get("task_id")

    if not task_id:
        return {"error": f"No task_id returned: {data}", "image_url": None}

    image_url = _poll_task(task_id, base_url=base_url)

    result = {
        "image_url": image_url,
        "task_id": task_id,
        "status": "COMPLETED" if image_url else "FAILED",
        "prompt": payload.get("prompt", ""),
        "model": model or MODEL,
        "mode": mode,
        "cached": False,
    }
    if extra:
        result.update(extra)

    if image_url:
        cache_file.write_text(json.dumps(result, indent=2), encoding="utf-8")

    return result


def generate_image(prompt, aspect_ratio="1:1", resolution="1K",
                   reference_image_bytes=None, reference_mime="image/jpeg",
                   reference_instruction="", model=None):
    """
    Generate or edit an image with Nano Banana Pro Flash.

    With `reference_image_bytes` → IMAGE EDITING: the model edits your image per
    the prompt and preserves everything you don't mention.
    Without it → TEXT TO IMAGE: generates from scratch.

    Returns a dict with image_url, mode, cached (or error).
    """
    if not MAGNIFIC_KEY:
        return {"error": "No MAGNIFIC_API_KEY in .env", "image_url": None}

    seed = (hashlib.md5(reference_image_bytes).hexdigest()[:8]
            if reference_image_bytes else "no_ref")
    cache_file = _cache_file("", prompt, aspect_ratio, resolution, seed, model)

    cached = _read_cache(cache_file)
    if cached:
        return cached

    payload = {
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "resolution": resolution,
    }

    if reference_image_bytes:
        payload["reference_images"] = [_reference_block(
            reference_image_bytes,
            reference_mime,
            reference_instruction or "Use this as the base image to edit",
        )]
        mode = "image_editing"
    else:
        mode = "text_to_image"

    try:
        return _submit_and_poll(payload, mode, cache_file,
                                base_url=_endpoint(model), model=model)
    except Exception as e:
        return {"error": str(e), "image_url": None}


def generate_image_multi(prompt, aspect_ratio="1:1", resolution="1K", images=None,
                         variant=0, model=None):
    """
    Multi-reference generation — combine several images in one prompt.

    images: list of dicts with keys `bytes`, `mime`, `instruction`, e.g.:
        [{"bytes": product_bytes, "mime": "image/jpeg",
          "instruction": "This is the main subject. Preserve it exactly."},
         {"bytes": scene_bytes, "mime": "image/jpeg",
          "instruction": "Place the subject into this scene."}]

    variant: >0 produces a DISTINCT candidate (best-of-N accuracy passes). Each
    variant has its own cache entry, so a pre-run demo replays instantly while
    fresh runs still explore different renders.

    Returns a dict with image_url, mode, cached (or error).
    """
    if not MAGNIFIC_KEY:
        return {"error": "No MAGNIFIC_API_KEY in .env", "image_url": None}
    if not images:
        return generate_image(prompt, aspect_ratio, resolution, model=model)

    if variant:
        prompt = f"{prompt}\n\n[render pass {variant}]"

    seed = hashlib.md5(b"".join(img["bytes"] for img in images)).hexdigest()[:8]
    cache_file = _cache_file("multi_", prompt, aspect_ratio, resolution, seed, model)

    cached = _read_cache(cache_file)
    if cached:
        return cached

    payload = {
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "resolution": resolution,
        "reference_images": [
            _reference_block(img["bytes"],
                             img.get("mime", "image/jpeg"),
                             img.get("instruction", "Reference image"))
            for img in images
        ],
    }

    try:
        return _submit_and_poll(
            payload,
            mode="multi_image_reference",
            cache_file=cache_file,
            extra={"num_references": len(images)},
            base_url=_endpoint(model),
            model=model,
        )
    except Exception as e:
        return {"error": str(e), "image_url": None}
