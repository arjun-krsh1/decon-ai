"""
pinterest_engine.py — Pinterest Reference Design Language Extractor

Step 1: Analyse uploaded Pinterest/reference image
         → Extract design language (mood, layout, lighting, colour story, texture)

Step 2: Reinterpret through Deconstruct's brand guidelines
         → Generate a prompt that captures the spirit, not the copy

The AI is explicitly instructed: STUDY and ADAPT, never copy or replace.
"""

import base64
import json
import sys
import os
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()
from llm import ask_llm, llm_available

DECONSTRUCT_REINTERPRETATION_RULES = """
REINTERPRETATION RULES (critical — read carefully):
1. DO NOT replicate the reference image — study its design language only
2. DO NOT replace the competitor/reference product with Deconstruct's product
3. DO NOT copy the exact colour palette — adapt it to Deconstruct's palette
4. DO NOT copy layout exactly — use it as structural inspiration only
5. DO translate: mood, lighting quality, compositional technique, texture feeling
6. DO apply Deconstruct's colours: black (#0A0A0A), white, cream (#F9F8F6), salmon (#F4A99A), lime (#C8F55A)
7. DO maintain Deconstruct's science-first, minimal, clinical aesthetic
8. The output should feel INSPIRED BY the reference, not derived from it
9. A designer seeing both images should say "I can see the influence" not "that's a copy"
"""

DESIGN_LANGUAGE_DIMENSIONS = {
    "mood": "Overall emotional tone and feeling",
    "lighting": "Quality, direction, temperature of light",
    "colour_story": "Dominant colours, accent colours, contrast level",
    "composition": "Layout structure, product placement, negative space usage",
    "texture_material": "Surface textures, material feel, tactile quality",
    "depth_perspective": "Depth of field, camera angle, perspective",
    "props_environment": "Background elements, props, environmental context",
    "typography_space": "How text zones are handled, whitespace philosophy",
}


def extract_design_language(image_bytes, filename="reference"):
    """
    Analyse a reference image and extract its design language.
    Returns a structured design language card.
    """
    if not llm_available():
        return _mock_design_language()

    try:
        import requests
        b64 = base64.b64encode(image_bytes).decode('utf-8')

        ext = filename.split('.')[-1].lower()
        mime = f"image/{ext}" if ext in ('jpg','jpeg','png','webp') else "image/jpeg"
        if ext == 'jpg':
            mime = "image/jpeg"

        prompt = f"""You are a senior creative director analysing a reference image for design inspiration.

Your job is NOT to copy this image but to extract its DESIGN LANGUAGE — the underlying creative decisions that make it work.

Analyse this image and return a JSON object with these exact keys:

"mood": The emotional tone (e.g. "dreamy and soft", "bold and clinical", "warm and intimate")
"lighting_quality": How light is used (e.g. "soft diffused overhead", "dramatic side lighting", "warm backlighting")
"lighting_direction": Where light comes from (e.g. "upper left at 45 degrees", "directly above", "behind subject")
"colour_story": Dominant colours and their relationship (e.g. "warm terracotta and cream, low saturation")
"colour_temperature": "warm" or "cool" or "neutral"
"contrast_level": "high", "medium", or "low"
"composition_type": Layout structure (e.g. "centered hero", "rule of thirds left", "diagonal split")
"negative_space": How empty space is used (e.g. "generous top third", "minimal, product fills frame")
"product_position": Where the hero element sits (e.g. "lower center", "right third", "floating center")
"background_treatment": What the background looks like (e.g. "pure white", "soft gradient cream", "textured stone")
"texture_feel": Material and tactile quality (e.g. "clinical smooth", "organic natural", "luxe marble")
"depth_of_field": "shallow bokeh background" or "sharp throughout" or "medium depth"
"camera_angle": "straight on", "slight above", "below" etc
"props": Any supporting elements (e.g. "none", "single green leaf", "water droplets")
"what_makes_it_work": 2-3 sentences on WHY this image is effective — the design principles at play
"design_principles": List of 3-5 core design principles this image demonstrates

JSON only. Start with {{"""

        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}"},
            json={
                "model": "meta-llama/llama-4-scout-17b-16e-instruct",
                "max_tokens": 800,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "image_url",
                         "image_url": {"url": f"data:{mime};base64,{b64}"}},
                        {"type": "text", "text": prompt}
                    ]
                }]
            },
            timeout=45
        )
        r.raise_for_status()
        result = r.json()["choices"][0]["message"]["content"].strip()
        start = result.index('{')
        end = result.rindex('}') + 1
        return json.loads(result[start:end])

    except Exception as e:
        print(f"[pinterest] extraction error: {e}")
        return _mock_design_language()


def reinterpret_for_deconstruct(design_language, product_name,
                                  composition_instruction="", guidelines_injection=""):
    """
    Take the design language card and reinterpret it for Deconstruct.
    Returns a complete prompt + a human-readable reinterpretation card.
    """
    dl = design_language

    system = """You are a senior creative director for Deconstruct skincare.
Your skill is studying reference images and reinterpreting their design language
through Deconstruct's own brand identity — never copying, always adapting.
You understand that great design adaptation means capturing the spirit while
changing everything that makes it belong to someone else."""

    prompt = f"""You have analysed a reference image and extracted its design language.
Now reinterpret this for Deconstruct skincare — adapting the design principles,
NOT copying the execution.

EXTRACTED DESIGN LANGUAGE FROM REFERENCE:
- Mood: {dl.get('mood', '—')}
- Lighting: {dl.get('lighting_quality', '—')}, {dl.get('lighting_direction', '—')}
- Colour story: {dl.get('colour_story', '—')} ({dl.get('colour_temperature', '—')} tone)
- Contrast: {dl.get('contrast_level', '—')}
- Composition: {dl.get('composition_type', '—')}
- Negative space: {dl.get('negative_space', '—')}
- Background: {dl.get('background_treatment', '—')}
- Texture feel: {dl.get('texture_feel', '—')}
- Camera: {dl.get('camera_angle', '—')}, {dl.get('depth_of_field', '—')}
- What makes it work: {dl.get('what_makes_it_work', '—')}
- Design principles: {', '.join(dl.get('design_principles', []))}

DECONSTRUCT BRAND GUIDELINES:
{guidelines_injection}

PRODUCT: {product_name}
COMPOSITION LAYOUT: {composition_instruction}

{DECONSTRUCT_REINTERPRETATION_RULES}

Generate a complete GPT-4o image editing prompt that:
1. Captures the MOOD of the reference ({dl.get('mood', '')})
2. Adapts the LIGHTING approach ({dl.get('lighting_quality', '')})
3. Uses Deconstruct's COLOURS instead of the reference colours
4. Applies the COMPOSITIONAL technique ({dl.get('composition_type', '')})
5. Maintains Deconstruct's clinical, science-backed aesthetic
6. Preserves the product label exactly (include strict preservation rules)

Also provide a "reinterpretation_card" explaining the translation:
what you kept from the reference and what you changed to match Deconstruct.

Return a JSON object with:
"reinterpretation_card": {{
  "kept_from_reference": list of 3-4 things adapted from the reference,
  "changed_for_deconstruct": list of 3-4 things changed to fit Deconstruct,
  "design_translation": one paragraph explaining the creative decision
}},
"full_prompt": the complete GPT-4o prompt (150-200 words, includes preservation rules),
"lighting_spec": specific lighting setup derived from the reference,
"scene_description": one sentence describing the final scene

JSON only. Start with {{"""

    result = ask_llm(prompt, system=system, temperature=0.6)

    try:
        start = result.index('{')
        end = result.rindex('}') + 1
        return json.loads(result[start:end])
    except Exception as e:
        print(f"[pinterest] reinterpretation error: {e}")
        return _mock_reinterpretation(dl, product_name)


def _mock_design_language():
    return {
        "mood": "Dreamy and ethereal with premium feel",
        "lighting_quality": "Soft diffused light",
        "lighting_direction": "Upper left at 45 degrees",
        "colour_story": "Warm cream and beige tones with soft highlights",
        "colour_temperature": "warm",
        "contrast_level": "low",
        "composition_type": "Centered hero with generous negative space",
        "negative_space": "Generous top third clear",
        "product_position": "Lower center",
        "background_treatment": "Soft gradient from cream to white",
        "texture_feel": "Smooth, clean, minimal",
        "depth_of_field": "Shallow bokeh background",
        "camera_angle": "Slight above",
        "props": "None",
        "what_makes_it_work": "The generous negative space creates breathing room that makes the product feel premium. The soft warm lighting adds approachability without sacrificing cleanliness.",
        "design_principles": [
            "Generous negative space = premium perception",
            "Soft directional light = product depth without harshness",
            "Minimal props = product confidence"
        ]
    }


def _mock_reinterpretation(dl, product_name):
    return {
        "reinterpretation_card": {
            "kept_from_reference": [
                f"Mood: {dl.get('mood', 'dreamy, premium feel')}",
                f"Lighting: {dl.get('lighting_quality', 'soft diffused')} approach",
                f"Composition: {dl.get('composition_type', 'centered hero')} structure",
                "Generous negative space philosophy",
            ],
            "changed_for_deconstruct": [
                f"Colour palette → Deconstruct white/cream (#F9F8F6) instead of reference colours",
                "Background → clean clinical white instead of styled environment",
                "Texture → minimal, science-forward instead of organic/lifestyle",
                "Mood → clinical precision added to the dreaminess",
            ],
            "design_translation": f"The reference's {dl.get('mood','premium')} mood is preserved but reinterpreted through Deconstruct's science-first lens — the warm softness becomes clinical precision, the colours shift to our white/cream/salmon palette, and the composition's breathing room is maintained to honour our 'information over impulse' brand philosophy."
        },
        "full_prompt": f"STRICT PRODUCT PRESERVATION: DO NOT change any text, shape, colour or label on the product. Place the {product_name} with {dl.get('lighting_quality','soft diffused')} lighting from {dl.get('lighting_direction','upper left')}. Background: clean white (#F9F8F6) — Deconstruct's signature cream-white. Camera: {dl.get('camera_angle','slight above')}. {dl.get('depth_of_field','Shallow depth of field')}. Mood: {dl.get('mood','premium and clean')} reinterpreted through a clinical, science-backed aesthetic. Deconstruct brand colours only: black, white, salmon accent. No props. Generous negative space.",
        "lighting_spec": f"{dl.get('lighting_quality','Soft diffused')} light from {dl.get('lighting_direction','upper left at 45 degrees')}",
        "scene_description": f"Product with adapted {dl.get('mood','premium')} mood, Deconstruct palette, {dl.get('composition_type','centered')} composition"
    }