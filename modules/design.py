"""
modules/design.py — MODULE #3: Design Intelligence (Design/Creative team)

Generates creative content concepts inspired by global brand trends.
Each concept includes a ready-to-use ChatGPT image generation prompt
so the design team can go straight from idea to mockup.
"""

from modules.base import Module, clamp, weighted_total

DECONSTRUCT_AESTHETIC = """
Deconstruct is a science-backed Indian D2C skincare brand.
Brand DNA:
- Colours: white, off-white, beige, black, lime/acid green accent (#C8F55A)
- Style: minimal, clinical, clean, lots of whitespace
- Typography: modern sans-serif, bold ingredient names
- Photography: flat-lay or close-up product shots, clean white/beige backgrounds
- Mood: trustworthy, scientific, premium but accessible, honest
- Voice: direct, ingredient-forward, no fluff
- NOT: busy, colourful, heavily filtered, over-styled, luxury gold
"""

# Inspired concepts catalogue — what global brands are doing right now
CONCEPTS = [
    {"name": "Korean Glass Skin Flat-lay",
     "market": "🇰🇷 South Korea", "format": "Instagram Post / Reel cover",
     "inspired_by": "COSRX, Some By Mi",
     "trend_momentum": 90, "brand_fit": 88, "novelty": 72, "adaptability": 85,
     "description": "Minimal product flat-lay on white/marble surface, soft side lighting, one hero product with a single ingredient highlight (e.g. a hyaluronic acid droplet). Very clean, very shareable.",
     "best_for": ["Vitamin C Serum", "Moisturizer", "Niacinamide Serum"]},
    {"name": "Clinical Before/After Split",
     "market": "🇺🇸 USA", "format": "Instagram Carousel / Ad",
     "inspired_by": "The Ordinary, Paula's Choice",
     "trend_momentum": 85, "brand_fit": 95, "novelty": 60, "adaptability": 90,
     "description": "Left: problem skin (acne, dark spots, dullness). Right: result after 30 days. Clean clinical font overlay with ingredient name. No over-editing — real skin texture visible. Very Deconstruct.",
     "best_for": ["Vitamin C Serum", "Niacinamide Serum", "Sunscreen"]},
    {"name": "Ingredient Hero Close-up",
     "market": "🇪🇺 Europe", "format": "Instagram Post / Website Banner",
     "inspired_by": "La Roche-Posay, Bioderma",
     "trend_momentum": 82, "brand_fit": 96, "novelty": 78, "adaptability": 88,
     "description": "Extreme macro of the hero ingredient (niacinamide crystals, vitamin C powder, hyaluronic acid gel). Black or white background. Bold ingredient % overlay. Looks like a science journal cover.",
     "best_for": ["Vitamin C Serum", "Niacinamide Serum", "Retinol Serum"]},
    {"name": "Routine Step Carousel",
     "market": "🇰🇷 South Korea", "format": "Instagram Carousel",
     "inspired_by": "Innisfree, Skin1004",
     "trend_momentum": 88, "brand_fit": 85, "novelty": 65, "adaptability": 92,
     "description": "Each slide = one step in the routine. Minimal product shot + step number + one-line benefit. Last slide = full routine laid out together. Very save-worthy and shareable.",
     "best_for": ["Sunscreen", "Moisturizer", "Cleanser"]},
    {"name": "Dupe Culture Comparison",
     "market": "🇬🇧 UK", "format": "Instagram Reel / Story",
     "inspired_by": "Ordinary Skincare UK creators",
     "trend_momentum": 91, "brand_fit": 80, "novelty": 85, "adaptability": 83,
     "description": "Split screen: premium brand (₹3000) vs Deconstruct (₹500). Same active %. Bold text overlay. Very honest, very viral. UK audience loves this — India will too.",
     "best_for": ["Vitamin C Serum", "Niacinamide Serum", "Retinol Serum"]},
    {"name": "AM/PM Routine Split",
     "market": "🇨🇳 China", "format": "Instagram Post / Carousel",
     "inspired_by": "Douyin beauty creators",
     "trend_momentum": 86, "brand_fit": 87, "novelty": 70, "adaptability": 89,
     "description": "Left half: morning routine products on bright white. Right half: night routine on dark/charcoal background. Clean line down the middle. Very visual, shows full product range.",
     "best_for": ["Sunscreen", "Moisturizer", "Retinol Serum"]},
    {"name": "Minimalist Product Launch Card",
     "market": "🇪🇺 Europe", "format": "Instagram Post / Ad",
     "inspired_by": "Typology, Medik8",
     "trend_momentum": 80, "brand_fit": 97, "novelty": 68, "adaptability": 94,
     "description": "Pure white background. Product centered. Large bold ingredient name at top. One benefit line below. No clutter whatsoever. Looks expensive, costs nothing to produce.",
     "best_for": ["Sunscreen", "Vitamin C Serum", "Moisturizer", "Cleanser"]},
    {"name": "Skin Concern Problem-Solution",
     "market": "🇦🇪 Middle East", "format": "Instagram Carousel / Story",
     "inspired_by": "Gulf beauty creators",
     "trend_momentum": 87, "brand_fit": 84, "novelty": 74, "adaptability": 86,
     "description": "Slide 1: The problem (dark spots, oiliness, acne) with bold text. Slide 2: The ingredient that fixes it. Slide 3: The product. Very direct, very high save rate from Indian audience too.",
     "best_for": ["Niacinamide Serum", "Vitamin C Serum", "Sunscreen"]},
    {"name": "BTS Lab / Formulation Story",
     "market": "🇺🇸 USA", "format": "Instagram Reel / Story",
     "inspired_by": "Drunk Elephant, Deciem",
     "trend_momentum": 83, "brand_fit": 93, "novelty": 82, "adaptability": 80,
     "description": "Behind-the-scenes of product formulation, testing, lab equipment. No script, raw and authentic. Shows the science is real. Perfect for Deconstruct's 'information over impulse' positioning.",
     "best_for": ["Vitamin C Serum", "Niacinamide Serum", "Retinol Serum", "Sunscreen"]},
    {"name": "Texture / Sensorial Close-up",
     "market": "🇰🇷 South Korea", "format": "Instagram Reel / Post",
     "inspired_by": "Laneige, Sulwhasoo",
     "trend_momentum": 84, "brand_fit": 82, "novelty": 79, "adaptability": 87,
     "description": "Extreme close-up of product texture — serum drop, cream swirl, gel texture. Slow motion if video. Clean background. No text needed. Pure sensory appeal. Gets massive engagement.",
     "best_for": ["Moisturizer", "Vitamin C Serum", "Cleanser"]},
]

WEIGHTS = {
    "brand_fit": 0.35,
    "trend_momentum": 0.25,
    "novelty": 0.20,
    "adaptability": 0.20,
}


def score(candidate, inputs):
    # boost score if product matches best_for list
    product_boost = 10 if inputs.get("product") in candidate.get("best_for", []) else 0
    # boost for matching market preference
    market_boost = 8 if inputs.get("market", "Global") in candidate.get("market", "") else 0

    parts = {
        "brand_fit": clamp(candidate["brand_fit"] + product_boost),
        "trend_momentum": clamp(candidate["trend_momentum"] + market_boost),
        "novelty": candidate["novelty"],
        "adaptability": candidate["adaptability"],
    }
    return weighted_total(parts, WEIGHTS), parts


def explain_prompt(candidate, inputs, parts):
    return (
        f"In 3 short bullets, explain why the '{candidate['name']}' creative concept "
        f"(inspired by {candidate['inspired_by']}) works well for Deconstruct's "
        f"{inputs['product']} on {inputs['platform']}. "
        f"Focus on: why it fits Deconstruct's aesthetic, why Indian audience will respond, "
        f"and one specific execution tip. Bullets only, no preamble."
    )


def generate_prompt(inputs, n):
    return (
        f"You are a creative director for Deconstruct, an Indian D2C skincare brand. "
        f"Deconstruct's aesthetic: minimal, clinical, clean, white/black/beige palette, "
        f"science-forward, honest. Platform: {inputs.get('platform','Instagram')}. "
        f"Product: {inputs.get('product','Sunscreen')}. Mood: {inputs.get('mood','Premium')}. "
        f"Generate {n} original creative content concepts inspired by what's trending in "
        f"global skincare brands right now. "
        f"Each concept should be specific and actionable for Deconstruct's design team. "
        f"Return ONLY a JSON array. Each object must have: "
        f'"idea" (concept name), "format" (Instagram Post/Reel/Carousel/Story), '
        f'"visual_description" (exactly what the design should look like — colours, layout, elements), '
        f'"inspired_by" (which market/brand trend inspired this), '
        f'"chatgpt_prompt" (a ready-to-use DALL-E/Midjourney prompt the design team can use directly). '
        f"JSON array only. Start with ["
    )


def mock_ideas(inputs, n):
    product = inputs.get("product", "Sunscreen")
    platform = inputs.get("platform", "Instagram")
    pool = [
        {
            "idea": f"Clinical White — {product} Hero Shot",
            "format": "Instagram Post",
            "visual_description": f"Pure white background. {product} bottle centered. Bold black text: the hero ingredient name and %. Lime green accent line at bottom. Zero clutter. Looks like a science label.",
            "inspired_by": "🇪🇺 European pharmacy brands (La Roche-Posay, Typology)",
            "chatgpt_prompt": f"Product photography of a minimalist skincare bottle on pure white background, clinical aesthetic, bold black sans-serif text showing ingredient percentage, lime green accent, high key lighting, no shadows, flat lay, photorealistic, 4K",
        },
        {
            "idea": f"Before/After Truth — {product} Results",
            "format": "Instagram Carousel",
            "visual_description": "Slide 1: Close-up real skin showing concern (no over-editing). Slide 2: Same area after 4 weeks. Slide 3: Product + ingredient callout. Clean clinical font. Real skin texture kept visible.",
            "inspired_by": "🇺🇸 USA — The Ordinary, Paula's Choice honest marketing",
            "chatgpt_prompt": f"Split screen before and after skincare transformation, left side shows skin concern, right side shows clear glowing skin, clinical minimal style, clean white background, honest unfiltered photography, dermatological aesthetic",
        },
        {
            "idea": f"Ingredient Macro — Science as Art",
            "format": "Instagram Post",
            "visual_description": f"Extreme macro photography of the hero ingredient texture or molecular structure. Black background. Bold white ingredient name overlay. Looks like a science journal cover. Very premium, zero product visible.",
            "inspired_by": "🇰🇷 South Korea — ingredient-first storytelling",
            "chatgpt_prompt": f"Extreme macro photograph of skincare ingredient crystals/gel on black background, scientific aesthetic, ultra detailed, laboratory photography style, moody lighting, ingredient name in bold white minimalist typography overlay",
        },
    ]
    return pool[:n]


MODULE = Module(
    key="design",
    label="Design Intelligence",
    department="Design / Creative",
    tagline="AI creative briefs inspired by global brand trends. Ready-to-use ChatGPT prompts included.",
    input_fields=[
        {"name": "product", "label": "Product", "type": "select",
         "options": ["Sunscreen", "Vitamin C Serum", "Moisturizer",
                     "Cleanser", "Retinol Serum", "Niacinamide Serum"]},
        {"name": "platform", "label": "Platform", "type": "select",
         "options": ["Instagram", "YouTube Thumbnail", "Website Banner",
                     "Ad Creative", "Packaging"]},
        {"name": "market", "label": "Inspiration market", "type": "select",
         "options": ["Global", "South Korea 🇰🇷", "USA 🇺🇸",
                     "Europe 🇪🇺", "Middle East 🇦🇪", "UK 🇬🇧"]},
        {"name": "mood", "label": "Mood", "type": "select",
         "for_generate": True,
         "options": ["Clinical / Scientific", "Minimal / Premium",
                     "Fresh / Youthful", "Bold / Confident", "Warm / Approachable"]},
    ],
    weights=WEIGHTS,
    candidates=CONCEPTS,
    score=score,
    explain_prompt=explain_prompt,
    generate_prompt=generate_prompt,
    mock_ideas=mock_ideas,
    radar=[
        {"signal": "Ingredient-as-hero visual language", "direction": "rising",
         "india_status": "emerging",
         "note": "Global brands making the ingredient the star, not the product. Huge for science-first brands."},
        {"signal": "Real skin / anti-filter movement", "direction": "rising",
         "india_status": "early",
         "note": "UK and US creators going no-filter. Deconstruct's honesty positioning is perfectly timed."},
        {"signal": "Busy colourful D2C ads", "direction": "declining",
         "india_status": "saturated",
         "note": "Clutter fatigue setting in. Minimal clinical wins attention now."},
    ],
    recommend_noun="creative concept",
    generate_noun="creative brief",
)