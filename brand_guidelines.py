"""
brand_guidelines.py — Deconstruct Brand Guidelines Engine

Analyses uploaded reference images + text notes to extract
platform-specific creative guidelines. Stores them and feeds
them into the prompt generator automatically.
"""

import json
import base64
import pathlib
import sys
import os
sys.path.insert(0, '.')
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
load_dotenv()
from llm import ask_llm, llm_available

GUIDELINES_FILE = pathlib.Path("scraper/cache/brand_guidelines.json")

# ── Deconstruct baseline — extracted from website + Instagram analysis ────────
DECONSTRUCT_BASELINE = {
    "brand_name": "Deconstruct",
    "brand_essence": "Science-backed, highly effective yet gentle skincare. Information over impulse. Transparency over claims.",
    "brand_voice": "Direct, honest, ingredient-forward. No fluff, no gimmicks. Speaks to informed consumers.",

    "colours": {
        "primary_black": "#0A0A0A",
        "primary_white": "#FFFFFF",
        "background_cream": "#F9F8F6",
        "accent_salmon": "#F4A99A",
        "accent_lime": "#C8F55A",
        "text_grey": "#666666",
        "border_light": "#E8E8E8",
        "notes": "Black and white are the dominant colours. Salmon/pink is the product accent (varies per product line). Lime green is the digital/campaign accent. Never use gold, never use busy gradients."
    },

    "typography": {
        "primary_font": "Inter or similar geometric sans-serif",
        "heading_style": "Bold, tight tracking, uppercase for categories",
        "body_style": "Regular weight, high readability, scientific terminology used confidently",
        "ingredient_style": "Bold percentage + ingredient name is the hero typographic element (e.g. '10% Niacinamide')",
        "notes": "Typography is always left-aligned or centered. Never decorative fonts. Never script."
    },

    "photography": {
        "style": "Clean product photography, clinical aesthetic",
        "backgrounds": "White, off-white (#F9F8F6), or very light beige",
        "lighting": "Soft, diffused natural light. No harsh shadows. No dramatic lighting except for special campaigns.",
        "props": "Minimal or none. Occasionally a single botanical element.",
        "skin_photography": "Real skin texture, no heavy retouching, authentic",
        "notes": "Product is always the hero. Never bury the product in props or environment."
    },

    "do_not": [
        "Heavy filters or oversaturation",
        "Gold or luxury styling",
        "Busy or cluttered layouts",
        "Decorative or script fonts",
        "Overclaiming language (miracle, magic, best ever)",
        "Stock photo lifestyle imagery",
        "Dark moody backgrounds for product shots (only for special campaigns)",
        "Text-heavy images without breathing room",
        "Misrepresenting ingredient percentages"
    ]
}

# ── Platform-specific baseline guidelines ─────────────────────────────────────
PLATFORM_BASELINES = {
    "Instagram Post (1:1)": {
        "dimensions": "1080 x 1080px (1:1) — Feed post",
        "safe_zone": "Keep all text and key visuals within 75px from edges",
        "text_rules": [
            "Headline: max 6 words, bold, upper or title case",
            "Subtext: max 15 words, regular weight",
            "Ingredient callout: bold % + name (e.g. '10% Niacinamide') — always present for product posts",
            "Never more than 3 text elements on one image",
        ],
        "composition": [
            "Product centered or rule-of-thirds placement",
            "Generous negative space — minimum 30% of image",
            "White or off-white background for product posts",
            "Carousel: first slide must have the hook — bold claim or question",
        ],
        "colours": "Stick to brand palette. One accent colour maximum per post.",
        "what_works": "Ingredient education carousels, before/after, clean product flat-lays, scientific fact posts",
        "what_to_avoid": "Busy backgrounds, too many elements, illegible small text, stock lifestyle images",
    },

    "Instagram Story (9:16)": {
        "dimensions": "1080 x 1920px (9:16) — Vertical",
        "safe_zone": "Top 250px and bottom 250px are UI zones — keep content between 250px and 1670px",
        "text_rules": [
            "Large bold headline in top third",
            "CTA in bottom third (e.g. 'Swipe up', 'Shop now')",
            "Max 20 words total on screen",
        ],
        "composition": [
            "Product in center or lower-center",
            "Bold colour block or clean gradient background",
            "Use the salmon/lime accent for CTA buttons",
        ],
        "colours": "Can be slightly bolder than feed — use salmon or lime as background accent",
        "what_works": "Flash sales, ingredient reveals, polls, swipe-up to product",
        "what_to_avoid": "Too much text, covering the product with text, ignoring safe zones",
    },

    "Instagram Reel Cover": {
        "dimensions": "1080 x 1920px (9:16) — but shown as 1080x1350 in feed crop",
        "safe_zone": "Keep key content in center 1080x1080 zone — top and bottom get cropped in feed",
        "text_rules": [
            "Title/hook in large bold text — must be readable as thumbnail",
            "Max 5 words — it's a thumbnail, not an article",
        ],
        "composition": [
            "Strong visual hook — face, product, or bold text",
            "High contrast between text and background",
            "Brand element (product or logo) visible in feed crop zone",
        ],
        "colours": "High contrast — black text on white or white text on dark",
        "what_works": "Bold question, ingredient spotlight, transformation hook",
        "what_to_avoid": "Cluttered frame, small text, brand name only (no hook)",
    },

    "Website Banner (16:9)": {
        "dimensions": "1920 x 800px desktop / 800 x 800px mobile",
        "safe_zone": "Keep text in left 50% on desktop. Center on mobile.",
        "text_rules": [
            "H1: 2-5 words, bold, black on white or white on dark",
            "Subtext: one benefit line, max 10 words",
            "CTA button: 2-3 words (Shop Now, Explore, Learn More)",
        ],
        "composition": [
            "Product on right side (desktop), centered (mobile)",
            "Clean background — white, cream, or very soft gradient",
            "Text left-aligned on desktop",
            "Plenty of breathing room — never cramped",
        ],
        "colours": "White/cream background with black text is the standard. Salmon for CTA buttons.",
        "what_works": "Hero product + benefit headline + CTA. Simple. Clean.",
        "what_to_avoid": "Too many products in one banner, dark moody backgrounds for main hero, small CTA",
    },

    "Packaging Mockup": {
        "dimensions": "800 x 800px or 600 x 600px",
        "safe_zone": "Product must fill 60-70% of the frame",
        "text_rules": [
            "Product name only — no additional text on image",
            "Let the label speak — Deconstruct labels are already information-rich",
        ],
        "composition": [
            "Pure white background",
            "Product perfectly centered, slightly below center",
            "Subtle drop shadow or no shadow",
            "Clean, no props",
        ],
        "colours": "Pure white background. No exceptions for standard product cards.",
        "what_works": "Clean white product shot with perfect lighting",
        "what_to_avoid": "Coloured backgrounds, props, anything that distracts from the product",
    },

    "Ad Creative (Meta/Google)": {
        "dimensions": "1080 x 1080px (feed) / 1080 x 1920px (story) / 1200 x 628px (display)",
        "safe_zone": "Keep all text in center 80% — ad platforms crop edges",
        "text_rules": [
            "Primary text: bold benefit claim, max 8 words",
            "Ingredient callout: always present — this is Deconstruct's differentiator",
            "Price/offer: clear and legible if present",
            "Logo: small, top-left or bottom-right",
        ],
        "composition": [
            "Product hero — large and clear",
            "Benefit-first messaging — lead with what it does, not what it is",
            "High contrast for scroll-stopping in feed",
        ],
        "colours": "High contrast. Black/white with salmon or lime accent. Avoid low-contrast.",
        "what_works": "Ingredient % as hero element, before/after, clinical proof points",
        "what_to_avoid": "Lifestyle-only images with no product, vague claims, low contrast, cluttered",
    },
}


def analyse_reference_images(image_files, platform, text_notes=""):
    """
    Analyse uploaded reference images to extract additional guidelines.
    image_files: list of (filename, bytes) tuples
    Returns: additional guidelines dict
    """
    if not llm_available() or not image_files:
        return {}

    try:
        import requests
        import os

        # build image content blocks
        content = []
        for fname, fbytes in image_files[:5]:  # max 5 images
            b64 = base64.b64encode(fbytes).decode('utf-8')
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
            })

        notes_text = f"\nAdditional context from the team: {text_notes}" if text_notes else ""
        content.append({
            "type": "text",
            "text": f"""You are analysing Deconstruct skincare's {platform} creatives.
Extract specific, actionable design guidelines from these examples.{notes_text}

Return a JSON object with:
"observed_patterns": list of specific visual patterns you see (e.g. "Product always on right side")
"text_placement": where text appears and how it's styled
"colour_usage": specific colours and how they're used
"composition_rules": layout and composition patterns
"do_not": things clearly avoided in these examples
"unique_to_platform": guidelines specific to this platform
"team_notes": any insights from the team notes

JSON only. Start with {{"""
        })

        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}"},
            json={
                "model": "meta-llama/llama-4-scout-17b-16e-instruct",
                "max_tokens": 800,
                "messages": [{"role": "user", "content": content}]
            },
            timeout=45
        )
        r.raise_for_status()
        result = r.json()["choices"][0]["message"]["content"].strip()
        start = result.index('{')
        end = result.rindex('}') + 1
        return json.loads(result[start:end])
    except Exception as e:
        print(f"[guidelines] image analysis error: {e}")
        return {}


def build_guidelines(platform, image_files=None, text_notes=""):
    """Build complete guidelines for a platform."""
    baseline = PLATFORM_BASELINES.get(platform, {})

    if image_files:
        observed = analyse_reference_images(image_files, platform, text_notes)
    else:
        observed = {}

    # merge baseline + observed
    guidelines = {
        "platform": platform,
        "brand_baseline": DECONSTRUCT_BASELINE,
        "platform_rules": baseline,
        "observed_from_examples": observed,
        "text_notes": text_notes,
        "generated_at": str(pathlib.Path(__file__).stat().st_mtime),
    }

    return guidelines


def save_guidelines(platform, guidelines):
    """Save guidelines to cache."""
    all_guidelines = load_all_guidelines()
    all_guidelines[platform] = guidelines
    GUIDELINES_FILE.write_text(
        json.dumps(all_guidelines, indent=2, ensure_ascii=False),
        encoding='utf-8'
    )


def load_all_guidelines():
    """Load all saved guidelines."""
    if GUIDELINES_FILE.exists():
        try:
            return json.loads(GUIDELINES_FILE.read_text(encoding='utf-8'))
        except Exception:
            pass
    return {}


def guidelines_to_prompt_injection(platform):
    """
    Convert guidelines for a platform into a prompt injection string.
    This gets prepended to every design prompt for that platform.
    """
    all_g = load_all_guidelines()
    g = all_g.get(platform, {})

    if not g:
        # use baseline even if no custom guidelines saved
        baseline = PLATFORM_BASELINES.get(platform, {})
        brand = DECONSTRUCT_BASELINE
    else:
        baseline = g.get("platform_rules", PLATFORM_BASELINES.get(platform, {}))
        brand = g.get("brand_baseline", DECONSTRUCT_BASELINE)

    observed = g.get("observed_from_examples", {})
    notes = g.get("text_notes", "")

    lines = [
        f"DECONSTRUCT BRAND GUIDELINES FOR {platform.upper()}:",
        f"Dimensions: {baseline.get('dimensions', 'Standard')}",
        f"Safe zone: {baseline.get('safe_zone', 'Standard margins')}",
        f"Background: White or off-white (#F9F8F6) — never dark for standard posts",
        f"Colours: Black (#0A0A0A), White, Salmon accent (#F4A99A), Lime (#C8F55A)",
        f"Typography: Bold geometric sans-serif. Ingredient % always prominent.",
        f"Text rules: {' | '.join(baseline.get('text_rules', [])[:3])}",
        f"Composition: {' | '.join(baseline.get('composition', [])[:3])}",
        f"AVOID: {', '.join(brand['do_not'][:5])}",
    ]

    if observed:
        if observed.get("observed_patterns"):
            lines.append(f"Observed patterns: {', '.join(observed['observed_patterns'][:3])}")

    if notes:
        lines.append(f"Team notes: {notes}")

    return "\n".join(lines)


def generate_guideline_doc(platform=None):
    """Generate a human-readable guideline document for one or all platforms."""
    all_g = load_all_guidelines()
    platforms = [platform] if platform else list(PLATFORM_BASELINES.keys())

    doc = ["# Deconstruct Creative Guidelines\n"]
    doc.append(f"**Brand Essence:** {DECONSTRUCT_BASELINE['brand_essence']}\n")
    doc.append(f"**Brand Voice:** {DECONSTRUCT_BASELINE['brand_voice']}\n")
    doc.append("\n---\n")

    for p in platforms:
        baseline = PLATFORM_BASELINES.get(p, {})
        saved = all_g.get(p, {})
        observed = saved.get("observed_from_examples", {})
        notes = saved.get("text_notes", "")

        doc.append(f"\n## {p}\n")
        doc.append(f"**Dimensions:** {baseline.get('dimensions','—')}\n")
        doc.append(f"**Safe Zone:** {baseline.get('safe_zone','—')}\n\n")

        doc.append("**Text Rules:**\n")
        for rule in baseline.get("text_rules", []):
            doc.append(f"- {rule}\n")

        doc.append("\n**Composition:**\n")
        for rule in baseline.get("composition", []):
            doc.append(f"- {rule}\n")

        doc.append(f"\n**Colours:** {baseline.get('colours','—')}\n")
        doc.append(f"\n**What works:** {baseline.get('what_works','—')}\n")
        doc.append(f"\n**What to avoid:** {baseline.get('what_to_avoid','—')}\n")

        if observed:
            doc.append("\n**Observed from your examples:**\n")
            for k, v in observed.items():
                if isinstance(v, list) and v:
                    doc.append(f"- {k.replace('_',' ').title()}: {', '.join(str(x) for x in v[:3])}\n")
                elif isinstance(v, str) and v:
                    doc.append(f"- {k.replace('_',' ').title()}: {v}\n")

        if notes:
            doc.append(f"\n**Team notes:** {notes}\n")

        doc.append("\n---\n")

    return "".join(doc)