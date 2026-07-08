"""
hr_engine.py — HR ATS Prompt Generator

Reads the uploaded JD (PDF or text), combines with extra criteria,
and generates a complete prompt for Claude/GPT that outputs a ranked
Excel-ready shortlist.
"""

import json
import sys
import os
import pathlib
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()
from llm import ask_llm, llm_available

# ── scoring dimensions ────────────────────────────────────────────────────────
SCORING_DIMENSIONS = [
    {"key": "skills_match",          "label": "Skills Match",           "weight": 35,
     "description": "How well candidate's skills match the JD requirements"},
    {"key": "experience_relevance",  "label": "Experience Relevance",   "weight": 25,
     "description": "Relevance and depth of work experience to the role"},
    {"key": "education_fit",         "label": "Education Fit",          "weight": 15,
     "description": "Educational background alignment with role requirements"},
    {"key": "cultural_indicators",   "label": "Cultural Indicators",    "weight": 15,
     "description": "Signals of culture fit, values, collaboration, communication"},
    {"key": "growth_trajectory",     "label": "Growth Trajectory",      "weight": 10,
     "description": "Evidence of learning, progression, and increasing responsibility"},
]

# ── Excel output format ───────────────────────────────────────────────────────
EXCEL_COLUMNS = [
    "Rank",
    "Candidate Name",
    "Current Role",
    "Current Company",
    "Years of Experience",
    "Education",
    "Skills Match (35%)",
    "Experience Relevance (25%)",
    "Education Fit (15%)",
    "Cultural Indicators (15%)",
    "Growth Trajectory (10%)",
    "TOTAL SCORE (0-100)",
    "Top 3 Strengths",
    "Top 2 Gaps",
    "Hiring Recommendation",
    "Notes",
    "Resume Source",
]


def extract_jd_text(file_bytes, filename):
    """Extract text from uploaded JD file (PDF or DOCX or TXT)."""
    ext = pathlib.Path(filename).suffix.lower()

    if ext == '.txt':
        try:
            return file_bytes.decode('utf-8', errors='ignore')
        except Exception:
            return ""

    if ext == '.pdf':
        try:
            import pdfplumber
            import io
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                return "\n".join(
                    page.extract_text() or "" for page in pdf.pages
                )
        except ImportError:
            # fallback — try raw text extraction
            try:
                text = file_bytes.decode('latin-1', errors='ignore')
                # rough extraction of readable text from PDF
                import re
                chunks = re.findall(r'[A-Za-z][A-Za-z0-9 ,.\-/\n]{10,}', text)
                return "\n".join(chunks[:200])
            except Exception:
                return "[PDF text extraction failed — paste JD text manually]"

    if ext in ('.doc', '.docx'):
        try:
            import docx
            import io
            doc = docx.Document(io.BytesIO(file_bytes))
            return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except Exception:
            return "[DOCX extraction failed — paste JD text manually]"

    return file_bytes.decode('utf-8', errors='ignore')


def summarise_jd(jd_text):
    """Use AI to extract key requirements from the JD."""
    if not llm_available() or not jd_text.strip():
        return jd_text[:2000]

    prompt = f"""Extract the key requirements from this Job Description in a structured way.

Return a JSON object with:
"role_title": job title
"department": department/team
"key_skills": list of must-have technical skills
"nice_to_have": list of good-to-have skills
"experience_required": years and type of experience needed
"education": education requirements
"key_responsibilities": top 5 responsibilities (brief)
"cultural_fit": any culture/values mentions

JSON only. Start with {{

JD TEXT:
{jd_text[:4000]}"""

    result = ask_llm(prompt, system="Extract structured JSON from job descriptions.", temperature=0.1)
    try:
        start = result.index('{')
        end = result.rindex('}') + 1
        return json.loads(result[start:end])
    except Exception:
        return {"raw": jd_text[:2000]}


def generate_ats_prompt(jd_text, jd_summary, extra_criteria, resume_mode,
                         resume_count, company_name="Deconstruct"):
    """Generate the full ATS prompt for Claude/GPT."""

    # build the JD section
    if isinstance(jd_summary, dict) and "raw" not in jd_summary:
        jd_section = f"""
ROLE: {jd_summary.get('role_title', 'Not specified')}
DEPARTMENT: {jd_summary.get('department', 'Not specified')}

MUST-HAVE SKILLS: {', '.join(jd_summary.get('key_skills', []))}
NICE-TO-HAVE: {', '.join(jd_summary.get('nice_to_have', []))}
EXPERIENCE REQUIRED: {jd_summary.get('experience_required', 'Not specified')}
EDUCATION: {jd_summary.get('education', 'Not specified')}

KEY RESPONSIBILITIES:
{chr(10).join(f"- {r}" for r in jd_summary.get('key_responsibilities', []))}

CULTURE/VALUES: {jd_summary.get('cultural_fit', 'Not specified')}"""
    else:
        jd_section = jd_text[:3000]

    # build resume section based on mode
    if resume_mode == "pdf":
        resume_instructions = f"""
RESUME INPUT METHOD: PDF FILES
I am attaching {resume_count} resume PDFs to this conversation.
For each resume PDF attached:
1. Read the full resume carefully
2. Extract candidate information
3. Score against all dimensions below
4. Add to the ranking table"""

        resume_note = f"Note: All {resume_count} resumes are attached as PDF files to this message."

    else:  # drive links
        resume_instructions = f"""
RESUME INPUT METHOD: GOOGLE DRIVE LINKS
I am providing a file (Excel/Google Sheet) containing {resume_count} Google Drive links to resumes.
For each Drive link:
1. Open the link (ensure links are set to "Anyone with link can view")
2. Read the full resume document
3. Extract candidate information
4. Score against all dimensions below
5. Add to the ranking table

IMPORTANT: If any Drive link is inaccessible (private/restricted), mark that candidate as
"Link Inaccessible" in the Notes column and skip to next."""

        resume_note = f"Note: The {resume_count} resume links are provided in the attached file."

    # build scoring section
    scoring_section = "\n".join(
        f"- {d['label']} ({d['weight']}%): {d['description']}"
        for d in SCORING_DIMENSIONS
    )

    # build excel columns section
    columns_section = " | ".join(EXCEL_COLUMNS)

    # extra criteria section
    extra_section = f"\nADDITIONAL CRITERIA FROM HR TEAM:\n{extra_criteria}" if extra_criteria.strip() else ""

    prompt = f"""You are an expert HR recruiter and ATS system for {company_name}.

Your task: Evaluate all resumes against the Job Description below and produce a ranked shortlist in Excel-ready format.

═══════════════════════════════════════════════════════════
JOB DESCRIPTION
═══════════════════════════════════════════════════════════
{jd_section}
{extra_section}

═══════════════════════════════════════════════════════════
RESUME INPUT
═══════════════════════════════════════════════════════════
{resume_instructions}

═══════════════════════════════════════════════════════════
SCORING FRAMEWORK (Total: 100 points)
═══════════════════════════════════════════════════════════
Score each candidate on these dimensions (0-100 each, weighted):
{scoring_section}

TOTAL SCORE = (Skills Match × 0.35) + (Experience × 0.25) + (Education × 0.15) + (Cultural × 0.15) + (Growth × 0.10)

Hiring Recommendation categories:
- STRONG YES (85-100): Interview immediately
- YES (70-84): Shortlist for interview
- MAYBE (55-69): Keep as backup, consider if top candidates decline
- NO (below 55): Does not meet minimum requirements

═══════════════════════════════════════════════════════════
OUTPUT FORMAT
═══════════════════════════════════════════════════════════
Produce a table with these EXACT columns (copy-paste ready for Excel):
{columns_section}

FORMATTING RULES:
- Sort by TOTAL SCORE descending (Rank 1 = highest score)
- Top 3 Strengths: comma-separated, specific and evidence-based (e.g. "5 years React experience, led team of 8")
- Top 2 Gaps: honest gaps vs JD requirements (e.g. "No Python experience, only 2 years total vs 4 required")
- Notes: any flags, standout qualities, or concerns
- Use | as column separator so it can be pasted directly into Excel

After the table, provide:
1. SUMMARY: How many Strong Yes / Yes / Maybe / No
2. TOP 3 CANDIDATES: Brief paragraph on why each is exceptional
3. RED FLAGS: Any concerns noticed across the candidate pool
4. HIRING RECOMMENDATION: Which candidate to call first and why

{resume_note}

Begin evaluation now. Process ALL {resume_count} resumes before producing the final table."""

    return prompt


def generate_prompt_with_ai(jd_text, jd_summary, extra_criteria,
                              resume_mode, resume_count, company_name):
    """
    Use AI to generate an even more tailored ATS prompt
    based on the specific JD requirements.
    """
    if not llm_available():
        return generate_ats_prompt(jd_text, jd_summary, extra_criteria,
                                    resume_mode, resume_count, company_name)

    # Get role-specific scoring adjustments from AI
    role_title = jd_summary.get('role_title', 'the role') if isinstance(jd_summary, dict) else 'the role'
    key_skills = jd_summary.get('key_skills', []) if isinstance(jd_summary, dict) else []

    tweak_prompt = f"""For a {role_title} position requiring skills in {', '.join(key_skills[:5])},
what are the 3 most important role-specific things to look for in resumes that generic ATS systems miss?
Keep it to 3 bullet points, very specific to this role type. No preamble."""

    role_specific = ask_llm(tweak_prompt, temperature=0.3)

    # inject role-specific tips into the base prompt
    base = generate_ats_prompt(jd_text, jd_summary, extra_criteria,
                                resume_mode, resume_count, company_name)

    if role_specific:
        injection = f"""
═══════════════════════════════════════════════════════════
ROLE-SPECIFIC EVALUATION TIPS (AI-generated for this JD)
═══════════════════════════════════════════════════════════
{role_specific}
"""
        # insert before OUTPUT FORMAT section
        base = base.replace(
            "═══════════════════════════════════════════════════════════\nOUTPUT FORMAT",
            injection + "═══════════════════════════════════════════════════════════\nOUTPUT FORMAT"
        )

    return base