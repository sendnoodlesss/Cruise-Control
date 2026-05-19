"""Resume Understanding Agent — extracts structured profile via LLM."""
import logging
import json
from backend.llm_router import call as llm_call

logger = logging.getLogger(__name__)

SYSTEM = """You extract structured candidate profiles from resumes.
Return STRICT JSON with keys:
  skills (list of strings),
  experience_summary (string, 2-3 sentences),
  preferred_domains (list of strings),
  keywords (list of 8-12 strings).
JSON only — no markdown, no explanation."""


async def extract_profile(resume_text: str, pathway: dict) -> dict:
    """Returns parsed profile dict. Falls back to empty defaults on failure."""
    if not resume_text or not resume_text.strip():
        return _default_profile(pathway)
    try:
        raw = await llm_call(
            task_type="extract",
            system=SYSTEM,
            user=f"Resume:\n{resume_text[:6000]}\n\nJSON only.",
            session_id=f"resume-{pathway['id']}",
            pathway=pathway,
        )
        start, end = raw.find("{"), raw.rfind("}")
        if start >= 0:
            return json.loads(raw[start:end+1])
    except Exception as e:
        logger.warning(f"Resume extract failed: {e}")
    return _default_profile(pathway)


def _default_profile(pathway: dict) -> dict:
    role = pathway.get("role_category", "")
    return {
        "skills": pathway.get("skills", ["Python", "SQL", "Excel",
                                          "Stakeholder communication"]),
        "experience_summary": "Candidate with strong analytical and "
                              "problem-solving background.",
        "preferred_domains": [role],
        "keywords": ["analysis", "ops", "strategy", "data", "research",
                     "communication", "problem-solving", "initiative"],
    }