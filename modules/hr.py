"""
modules/hr.py — MODULE #4: HR ATS AI (HR Team)

Generates a production-ready prompt for Claude/GPT that:
- Takes a Job Description + extra criteria
- Evaluates 100-200 resumes (PDF or Drive links)
- Returns a ranked Excel sheet with scores across multiple metrics
"""

from modules.base import Module, clamp, weighted_total

WEIGHTS = {
    "skills_match": 0.35,
    "experience_relevance": 0.25,
    "education_fit": 0.15,
    "cultural_indicators": 0.15,
    "growth_trajectory": 0.10,
}

MODULE = Module(
    key="hr",
    label="HR ATS AI",
    department="Human Resources",
    tagline="Drop a JD, get a ranked shortlist. Works with PDF resumes or Google Drive links.",
    input_fields=[],
    weights=WEIGHTS,
    candidates=[],
    score=lambda c, i: (0, {}),
    explain_prompt=lambda c, i, p: "",
    generate_prompt=lambda i, n: "",
    mock_ideas=lambda i, n: [],
    radar=[],
    recommend_noun="candidate",
    generate_noun="shortlist",
)