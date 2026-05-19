"""Email Drafting Agent — personalized outreach via LLM."""
import logging
import json
from backend.models import OutreachEmail, UnlistedCompany
from backend.llm_router import call as llm_call

logger = logging.getLogger(__name__)

SYSTEM = """You draft concise, personalized internship outreach emails.
Tone: respectful, specific, no fabrication, under 160 words.
Return STRICT JSON with keys: subject (string), body (string).
No markdown. No preamble."""


async def draft_email(
    company: UnlistedCompany,
    profile: dict,
    pathway: dict,
) -> tuple[str, str]:
    """Returns (subject, body). Falls back to a template on failure."""
    role = pathway.get("role_category", "Intern")
    skills_str = ", ".join(profile.get("skills", [])[:8])
    user_msg = (
        f"Pathway role: {role}\n"
        f"Candidate skills: {skills_str}\n"
        f"Candidate summary: {profile.get('experience_summary','')}\n"
        f"Company: {company.company_name} ({company.website_url})\n"
        f"Company notes: {company.notes}\n"
        f"Domain keywords: {', '.join(company.domain_keywords)}\n\n"
        f"Write a personalized email expressing interest in an internship. "
        f"Mention 1 specific reason to reach out about the company and "
        f"2-3 candidate skills aligned to it."
    )
    try:
        raw = await llm_call(
            task_type="draft_email",
            system=SYSTEM,
            user=user_msg,
            session_id=f"draft-{pathway['id']}-{company.id[:6]}",
            pathway=pathway,
        )
        start, end = raw.find("{"), raw.rfind("}")
        if start >= 0:
            d = json.loads(raw[start:end+1])
            subject = d.get("subject", "")
            body    = d.get("body", "")
            if subject and body:
                return subject, body
    except Exception as e:
        logger.warning(f"Draft email LLM failed: {e}")

    # Fallback template
    subject = (f"Internship interest: {role.split()[0]} @ {company.company_name}")
    body = (
        f"Hi {company.company_name} team,\n\n"
        f"I'm reaching out about an internship opportunity in "
        f"{role.split()[0]}. I've been following "
        f"{company.company_name}'s work in "
        f"{', '.join(company.domain_keywords[:2])}, "
        f"and I'd love to contribute.\n\n"
        f"A bit about me: {profile.get('experience_summary','')[:200]}\n"
        f"My strongest skills: {skills_str}.\n\n"
        f"Would you be open to a 15-minute chat about an internship?\n\n"
        f"Thanks for your time."
    )
    return subject, body