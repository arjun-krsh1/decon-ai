"""
logo_lock.py — deterministic logo/badge compositing for product-swap results.

Generative image models (even Nano Banana Pro) cannot GUARANTEE perfect small,
curved or dense label text — a circular seal like "LIPOSOMAL TECHNOLOGY" is the
worst case. This module sidesteps the model entirely: it pastes your ORIGINAL
badge PIXELS onto the generated image, so the text is 100% correct by construction.

Pure PIL + numpy (no OpenCV / no new deploy deps). The caller positions the badge
(centre, size, rotation, optional perspective tilt); we mask, feather and composite
it. `auto_locate` is an OPTIONAL helper that pre-positions the badge via template
matching if OpenCV happens to be installed — it only *suggests* values, the paste
itself is always the reliable PIL path.
"""

from __future__ import annotations

import io
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops


def _open_rgba(b: bytes) -> Image.Image:
    return Image.open(io.BytesIO(b)).convert("RGBA")


def _remove_bg(logo: Image.Image, thresh: int = 245) -> Image.Image:
    """Knock near-white/near-black flat backgrounds out to transparent."""
    arr = np.asarray(logo.convert("RGB")).astype(np.int16)
    a = np.asarray(logo.split()[3]).copy()
    near_white = (arr[..., 0] >= thresh) & (arr[..., 1] >= thresh) & (arr[..., 2] >= thresh)
    a[near_white] = 0
    logo = logo.copy()
    logo.putalpha(Image.fromarray(a, "L"))
    return logo


def composite_logo(base_bytes: bytes, logo_bytes: bytes,
                   cx: float = 0.5, cy: float = 0.5, width_frac: float = 0.25,
                   aspect: float = 1.0, rotation: float = 0.0,
                   feather: float = 2.0, opacity: float = 1.0,
                   circular: bool = True, bg_remove: bool = False,
                   bg_thresh: int = 245) -> bytes:
    """
    Paste `logo` onto `base` at a chosen spot. Returns PNG bytes.

    cx, cy      : badge centre as fractions of base width/height (0..1)
    width_frac  : badge width as a fraction of base width (0..1)
    aspect      : height/width multiplier — <1 squashes vertically to fake a tilt
    rotation    : degrees, counter-clockwise
    feather     : gaussian blur (px) on the alpha edge, for a seamless seam
    opacity     : 0..1 overall
    circular    : mask the badge to an ellipse (perfect for round seals)
    bg_remove   : knock a flat white background out to transparent
    """
    base = Image.open(io.BytesIO(base_bytes)).convert("RGBA")
    logo = _open_rgba(logo_bytes)
    W, H = base.size

    if bg_remove:
        logo = _remove_bg(logo, bg_thresh)

    # scale
    tw = max(1, int(round(width_frac * W)))
    th = max(1, int(round(tw * (logo.height / logo.width) * aspect)))
    logo = logo.resize((tw, th), Image.LANCZOS)

    # alpha = existing alpha, optionally clipped to an ellipse
    alpha = logo.split()[3]
    if circular:
        emask = Image.new("L", (tw, th), 0)
        ImageDraw.Draw(emask).ellipse([0, 0, tw - 1, th - 1], fill=255)
        alpha = ImageChops.multiply(alpha, emask)
    if feather and feather > 0:
        alpha = alpha.filter(ImageFilter.GaussianBlur(float(feather)))
    if opacity < 1.0:
        alpha = alpha.point(lambda p: int(p * max(0.0, min(1.0, opacity))))
    logo.putalpha(alpha)

    # rotate about its own centre (expand canvas so nothing clips)
    if rotation:
        logo = logo.rotate(rotation, resample=Image.BICUBIC, expand=True)

    lw, lh = logo.size
    px = int(round(cx * W - lw / 2))
    py = int(round(cy * H - lh / 2))

    out = base.copy()
    out.alpha_composite(logo, (px, py))
    buf = io.BytesIO()
    out.convert("RGB").save(buf, "JPEG", quality=95)
    return buf.getvalue()


def auto_locate(base_bytes: bytes, logo_bytes: bytes):
    """
    OPTIONAL: suggest (cx, cy, width_frac, rotation) by locating the badge in the
    base image. Uses OpenCV multi-scale template matching IF cv2 is installed;
    returns None otherwise (caller falls back to manual placement). Never raises.
    """
    try:
        import cv2  # optional
    except Exception:
        return None
    try:
        base = np.asarray(Image.open(io.BytesIO(base_bytes)).convert("L"))
        logo = np.asarray(Image.open(io.BytesIO(logo_bytes)).convert("L"))
        Hb, Wb = base.shape
        best = None  # (score, cx, cy, width_frac)
        for wf in np.linspace(0.12, 0.6, 16):
            tw = int(wf * Wb)
            if tw < 12 or tw > Wb:
                continue
            th = max(1, int(tw * logo.shape[0] / logo.shape[1]))
            if th >= Hb:
                continue
            tmpl = cv2.resize(logo, (tw, th))
            res = cv2.matchTemplate(base, tmpl, cv2.TM_CCOEFF_NORMED)
            _, mx, _, mloc = cv2.minMaxLoc(res)
            if best is None or mx > best[0]:
                best = (mx, (mloc[0] + tw / 2) / Wb, (mloc[1] + th / 2) / Hb, wf)
        if best and best[0] >= 0.35:  # confidence floor
            return {"cx": round(best[1], 4), "cy": round(best[2], 4),
                    "width_frac": round(best[3], 4), "rotation": 0.0,
                    "confidence": round(float(best[0]), 3)}
    except Exception:
        return None
    return None
