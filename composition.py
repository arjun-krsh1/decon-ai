"""
composition.py — Visual Composition Presets

Defines layout presets for product placement + text zones.
Each preset translates directly into prompt instructions.
"""

COMPOSITIONS = {
    "center_text_top": {
        "label": "Text Top · Product Center",
        "icon": "⬆️📦",
        "description": "Clean headline above, product centered below",
        "product_placement": "product centered horizontally, positioned in lower 60% of frame",
        "text_zone": "top 35% of frame completely clear for text overlay",
        "breathing_room": "generous negative space in top third",
        "best_for": ["Instagram Post", "Ad Creative"],
        "prompt_instruction": "Place the product centered horizontally in the lower 60% of the frame. The top 35% must be completely empty — clean background only, no product, no props — reserved for text overlay in post-production.",
    },
    "center_text_bottom": {
        "label": "Product Center · Text Bottom",
        "icon": "📦⬇️",
        "description": "Product as hero, text zone below",
        "product_placement": "product centered, positioned in upper 60% of frame",
        "text_zone": "bottom 30% of frame clear for text overlay",
        "breathing_room": "negative space in bottom third",
        "best_for": ["Instagram Post", "Instagram Story"],
        "prompt_instruction": "Place the product centered in the upper 60% of the frame. The bottom 30% must be completely empty — clean background only — reserved for text overlay in post-production.",
    },
    "right_text_left": {
        "label": "Text Left · Product Right",
        "icon": "📝➡️📦",
        "description": "Editorial split — text left, product right",
        "product_placement": "product in right 45% of frame, slightly off-center right",
        "text_zone": "left 45% of frame completely clear for text overlay",
        "breathing_room": "large negative space on left side",
        "best_for": ["Website Banner", "Ad Creative"],
        "prompt_instruction": "Place the product in the right 45% of the frame. The entire left 45% must be completely empty — clean background, no props, no elements — reserved for headline text in post-production. This is the standard Deconstruct website banner composition.",
    },
    "left_text_right": {
        "label": "Product Left · Text Right",
        "icon": "📦⬅️📝",
        "description": "Product left, text space right",
        "product_placement": "product in left 45% of frame",
        "text_zone": "right 45% of frame clear for text overlay",
        "breathing_room": "large negative space on right side",
        "best_for": ["Website Banner", "Ad Creative"],
        "prompt_instruction": "Place the product in the left 45% of the frame. The entire right 45% must be completely empty — clean background only — reserved for text overlay in post-production.",
    },
    "bottom_third": {
        "label": "Product Bottom · Full Text Area",
        "icon": "📝\n📦",
        "description": "Maximum text space — product anchored at bottom",
        "product_placement": "product anchored at bottom center, showing only top 70% of product",
        "text_zone": "top 55% of frame completely clear for large text",
        "breathing_room": "top half entirely empty",
        "best_for": ["Instagram Story", "Instagram Reel Cover"],
        "prompt_instruction": "Anchor the product at the very bottom center of the frame, with the bottom 10% cropped. The top 55% of the frame must be completely empty — clean background only — for large headline text in post-production. Strong visual weight at bottom.",
    },
    "split_diagonal": {
        "label": "Diagonal Split",
        "icon": "↗️📦",
        "description": "Dynamic diagonal — product one corner, text opposite",
        "product_placement": "product in bottom-right corner, angled slightly",
        "text_zone": "top-left 50% clear for text",
        "breathing_room": "strong diagonal negative space",
        "best_for": ["Ad Creative", "Instagram Reel Cover"],
        "prompt_instruction": "Place the product in the bottom-right area of the frame at a slight angle. The top-left 50% of the frame must be completely empty — clean background — creating a strong diagonal composition. Reserved for text in post-production.",
    },
    "full_center_minimal": {
        "label": "Full Center · No Text Zone",
        "icon": "📦",
        "description": "Product is the entire story — no text needed",
        "product_placement": "product perfectly centered, filling 70% of frame",
        "text_zone": "no text zone — product only",
        "breathing_room": "even padding all sides",
        "best_for": ["Website Product Card", "Packaging Mockup"],
        "prompt_instruction": "Place the product perfectly centered, filling approximately 70% of the frame with even padding on all sides. Pure product shot — no text zones needed. Clean background with subtle shadow.",
    },
    "story_cta": {
        "label": "Story · CTA Bottom",
        "icon": "📦\n[CTA]",
        "description": "Story format — product mid, CTA zone at bottom",
        "product_placement": "product centered in middle 50% of frame",
        "text_zone": "top 25% for headline, bottom 20% for CTA button",
        "breathing_room": "respects Instagram Story safe zones",
        "best_for": ["Instagram Story"],
        "prompt_instruction": "Place the product centered in the middle 50% of the frame (between 25% and 75% from top). Top 25% completely empty for headline. Bottom 20% completely empty for CTA button. This respects Instagram Story safe zones where UI elements appear.",
    },
}

TEXT_AMOUNT_OPTIONS = {
    "Single headline (1 line)": "Reserve space for approximately 1 bold headline line (60-80px height)",
    "Headline + subtext (2 lines)": "Reserve space for 1 bold headline + 1 subtext line (120px height total)",
    "Headline + body (3 lines)": "Reserve space for headline + 2 body lines (180px height total)",
    "Full text block (4+ lines)": "Reserve space for a full text block — large clear zone required",
    "No text — product only": "No text reservation needed",
}

def get_composition_prompt(composition_key, text_amount):
    """Returns the composition instruction for a given preset + text amount."""
    comp = COMPOSITIONS.get(composition_key, COMPOSITIONS["center_text_top"])
    text_inst = TEXT_AMOUNT_OPTIONS.get(text_amount, "")

    return f"""
COMPOSITION LAYOUT: {comp['label']}
{comp['prompt_instruction']}
TEXT ZONE REQUIREMENT: {text_inst}
IMPORTANT: The empty zones described above are NON-NEGOTIABLE — they must remain completely clean and empty for the design team to add text in post-production (Canva/Photoshop). Do not place any elements, props, or textures in these zones.
"""

def get_composition_display():
    """Returns compositions grouped for UI display."""
    return COMPOSITIONS