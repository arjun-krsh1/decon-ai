"""
prompt_engine.py — Decon AI Creative Prompt Generator
Optimised for GPT-4o image editing mode.

Workflow: Upload product image to ChatGPT → paste prompt → get creative output
The prompt strictly preserves product text, shape, colour, and proportions.
"""

import base64, json, sys, os
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()
from llm import ask_llm, llm_available

DECONSTRUCT_DNA = """
Deconstruct Skincare — Visual DNA:
- Colours: white (#F9F8F6), beige, black (#0A0A0A), salmon/pink accent, lime green (#C8F55A)
- Style: minimal, clinical, clean, lots of negative space
- Photography: soft natural lighting, clean backgrounds, no heavy filters
- Mood: scientific, trustworthy, premium but accessible
"""

# The strict preservation block — inserted into EVERY prompt
PRESERVATION_BLOCK = """STRICT PRODUCT PRESERVATION RULES — DO NOT VIOLATE ANY OF THESE:
1. DO NOT change, alter, remove or modify ANY text on the product label — every word, number, percentage and character must remain exactly as it appears in the uploaded image
2. DO NOT change the shape or proportions of the product bottle — preserve exact height-to-width ratio
3. DO NOT change any colour on the product — the grey glass, black cap, white label, salmon/pink band must remain identical
4. DO NOT change the brand name, ingredient names, percentages or any typography on the label
5. DO NOT distort, warp, stretch or rotate the product
6. The product is a FIXED, UNCHANGED element — only the background and environment around it changes
7. Treat the product like a sticker placed on top of a new background — the sticker never changes, only the background does"""


def analyse_product_image(image_bytes, product_name):
    if not llm_available():
        return f"A {product_name} dropper bottle, matte frosted grey glass, black ribbed pipette cap, white label with salmon/pink lower band containing ingredient text"
    try:
        import requests
        b64 = base64.b64encode(image_bytes).decode('utf-8')
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}"},
            json={
                "model": "meta-llama/llama-4-scout-17b-16e-instruct",
                "max_tokens": 250,
                "messages": [{"role": "user", "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                    {"type": "text", "text": f"You are describing a product for strict preservation in an AI prompt. List: exact bottle shape, cap type, glass colour/finish, label colours, any visible text/numbers/percentages on the label (list them all). Be precise. 4 sentences max."}
                ]}]
            }, timeout=30
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"A {product_name} skincare bottle — preserve all label text and product details exactly as shown"


def generate_prompts(product_name, product_description, creative_direction,
                     platform, brand_text, style_mood, n_variants=5,
                     composition_instruction="", pinterest_context=""):

    ratio_map = {
        "Instagram Post (1:1)": "1:1, 1080x1080px",
        "Instagram Story (9:16)": "9:16, 1080x1920px",
        "Instagram Reel Cover": "9:16, 1080x1920px",
        "Website Banner (16:9)": "16:9, 1920x1080px",
        "Ad Creative (4:5)": "4:5, 1080x1350px",
        "Packaging Mockup": "1:1, 1080x1080px",
    }
    ratio = ratio_map.get(platform, "1:1")

    system = """You are an expert AI art director who writes prompts for GPT-4o image editing.
Your prompts always start with strict product preservation instructions,
then describe the creative scene to build around the unchanged product.
You are known for writing prompts where the product NEVER gets distorted."""

    # brand_text contains the platform-specific guidelines injection
    guidelines_section = f"""
DECONSTRUCT BRAND GUIDELINES (MUST BE FOLLOWED IN EVERY PROMPT):
{brand_text}
""" if brand_text else f"""
DECONSTRUCT BRAND DNA:
{DECONSTRUCT_DNA}
"""

    composition_section = f"""
COMPOSITION LAYOUT (NON-NEGOTIABLE):
{composition_instruction}
""" if composition_instruction else ""

    pinterest_section = f"""
PINTEREST REFERENCE DESIGN LANGUAGE (adapt, do not copy):
{pinterest_context}
""" if pinterest_context else ""

    prompt = f"""Write {n_variants} different GPT-4o image editing prompts for this brief.

PRODUCT: {product_name}
PRODUCT DETAILS (from image analysis): {product_description}
CREATIVE DIRECTION: {creative_direction}
PLATFORM: {platform} ({ratio})
STYLE/MOOD: {style_mood}
{guidelines_section}{composition_section}{pinterest_section}

STRUCTURE OF EACH PROMPT:
Every prompt must start with the strict preservation block, then describe the scene.
The preservation block must come FIRST — before any creative description.

PRESERVATION BLOCK TO INCLUDE IN EVERY PROMPT (word for word):
"{PRESERVATION_BLOCK}"

AFTER THE PRESERVATION BLOCK, describe:
- The background/environment ({creative_direction})
- Lighting setup (direction, quality, temperature)
- Mood and atmosphere
- Colour palette of the scene
- Camera angle and composition
- Any additional elements (props, textures, environment)

Make each of the {n_variants} variants a DIFFERENT creative interpretation of "{creative_direction}":
- Variant 1: Most literal/direct interpretation
- Variant 2: More dramatic lighting version
- Variant 3: More minimal/clean version
- Variant 4: More atmospheric/moody version
- Variant 5: Most unexpected/creative interpretation

Return ONLY a JSON array of {n_variants} objects with keys:
"variant_name": short creative name
"full_prompt": the complete prompt to paste into ChatGPT (preservation block + scene description, 120-180 words total)
"scene_summary": one sentence describing what makes this variant different
"lighting": specific lighting setup used
"best_for": what this variant is best used for (e.g. Instagram feed, story ad, hero banner)

JSON only. Start with ["""

    result = ask_llm(prompt, system=system, temperature=0.75)
    try:
        start = result.index('[')
        end = result.rindex(']') + 1
        return json.loads(result[start:end])
    except Exception as e:
        print(f"[prompt_engine] {e}")
        return _fallback_prompts(product_name, product_description,
                                  creative_direction, style_mood, n_variants,
                                  brand_guidelines=brand_text)


def _fallback_prompts(product_name, product_description, creative_direction, style_mood, n, brand_guidelines=""):
    preservation = PRESERVATION_BLOCK.replace('\n', ' ')
    pool = [
        {
            "variant_name": "Dreamy Cloud Float",
            "full_prompt": f"{preservation} {'Brand guidelines: ' + brand_guidelines[:200] + '. ' if brand_guidelines else ''}Now place this exact unchanged product floating gently on a bed of soft white clouds. The sky behind is warm peach and golden, with soft volumetric godrays streaming down from upper left. The clouds cradle the base of the bottle. {style_mood} mood. Photorealistic commercial photography, 85mm lens, f/2.8, soft diffused lighting. The product must look exactly as uploaded — every label detail, every text, every colour preserved perfectly.",
            "scene_summary": "Product floating on clouds with warm golden godray lighting",
            "lighting": "Soft volumetric godrays from upper left, warm 5500K",
            "best_for": "Instagram feed post, hero banner"
        },
        {
            "variant_name": "Pure Studio Hero",
            "full_prompt": f"{preservation} Place this exact unchanged product on a pure white seamless studio background. Single softbox light from upper left at 45 degrees, soft shadow falling to the right. Product centered with generous negative space. Clinical, minimal, premium feel. {style_mood} aesthetic. Photorealistic, Phase One camera, 85mm f/2.8, ultra sharp. Every label text and detail on the product must remain exactly as in the uploaded image.",
            "scene_summary": "Clean white studio with precise directional lighting",
            "lighting": "Single softbox upper left 45°, soft fill right",
            "best_for": "Product page, clean Instagram post"
        },
        {
            "variant_name": "Dark Drama",
            "full_prompt": f"{preservation} Place this exact unchanged product against a deep charcoal black background. Single dramatic spotlight from directly above creating a perfect circle of light on the product. Subtle wisps of mist at the base. Editorial, premium, high-contrast mood. {style_mood}. Shot on Canon R5, 100mm f/2, ultra sharp product with soft background. Every character, number and word on the product label must be preserved exactly as uploaded.",
            "scene_summary": "Moody dark background with spotlight and mist",
            "lighting": "Single spotlight directly above, high contrast",
            "best_for": "Premium ads, story format, editorial"
        },
        {
            "variant_name": "Botanical Minimal",
            "full_prompt": f"{preservation} Place this exact unchanged product in a minimal flat lay composition. Clean white marble surface. A single small green leaf and one tiny white flower placed beside the bottle — not touching or obscuring any product text. Soft diffused natural light from directly above. Plenty of white negative space. {style_mood} feel. 50mm lens, f/4, photorealistic. The product label, text and colours must be 100% identical to the uploaded image.",
            "scene_summary": "Minimal flat lay with botanical accents on marble",
            "lighting": "Soft natural overhead diffused light",
            "best_for": "Instagram feed, clean aesthetic posts"
        },
        {
            "variant_name": "Dewy Skin Context",
            "full_prompt": f"{preservation} Place this exact unchanged product against a close-up background of glowing healthy dewy skin texture — extreme bokeh, very soft focus background. Warm peach and beige tones. Rim light from behind creating a subtle halo around the product. {style_mood} mood. 100mm macro, f/1.4, photorealistic. The product must appear perfectly sharp and unchanged — every label detail, text, percentage and colour exactly as uploaded.",
            "scene_summary": "Product against soft bokeh dewy skin background",
            "lighting": "Warm rim light from behind, soft ambient fill",
            "best_for": "Engagement posts, benefit-focused ads"
        },
    ]
    return pool[:n]


PLATFORM_SPECS = {
    "Instagram Post (1:1)": {"ratio": "1:1", "size": "1080x1080"},
    "Instagram Story (9:16)": {"ratio": "9:16", "size": "1080x1920"},
    "Instagram Reel Cover": {"ratio": "9:16", "size": "1080x1920"},
    "Website Banner (16:9)": {"ratio": "16:9", "size": "1920x1080"},
    "Ad Creative (4:5)": {"ratio": "4:5", "size": "1080x1350"},
    "Packaging Mockup": {"ratio": "1:1", "size": "1080x1080"},
}