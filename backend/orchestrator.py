"""
Pathway Orchestrator — coordinates all 6 agent stages.
Reads LLM settings from pathway doc and passes them to llm_router.
"""
import asyncio
import json
import logging
import random
from datetime import datetime, timezone

from backend.models import Internship, UnlistedCompany, OutreachEmail
from backend import llm_router

logger = logging.getLogger(__name__)


def _now(): return datetime.now(timezone.utc).isoformat()


# ── Mock data pools ───────────────────────────────────────────────────────────

SOURCES = ["LinkedIn", "Indeed", "Internshala", "Glassdoor", "AngelList"]
LOCATIONS = ["Bangalore, IN", "Mumbai, IN", "Remote", "Delhi NCR, IN",
             "Hyderabad, IN", "San Francisco, CA", "London, UK"]

ROLE_COMPANIES = {
    "business analyst": ["Razorpay","CRED","Meesho","Zerodha","Groww","Postman","Freshworks"],
    "automation":       ["Make.com","Zapier","Bardeen","Tines","Pipedream","n8n.io","Relay.app"],
    "devops":           ["Render","Fly.io","Railway","Vercel","Northflank","Porter"],
    "cloud":            ["Snowflake","Databricks","MongoDB","Supabase","Neon","PlanetScale"],
    "ai":               ["Anthropic","Cohere","Mistral","Together AI","Modal","Fireworks AI"],
    "marketing":        ["Webflow","Framer","Notion","Linear","Loom","Cal.com"],
    "data":             ["dbt Labs","Hex","Metabase","Lightdash","Hightouch"],
    "default":          ["Lattice","Ramp","Brex","Mercury","Deel","Rippling","Gusto"],
}
EXTRA_STARTUPS = ["Lumora Labs","Northwind AI","Quill Stack","Vertex Loop",
                  "Atlas Forge","Pulse Synth","Cobalt Path","Mira Systems"]


def _companies_for(role: str):
    for key, pool in ROLE_COMPANIES.items():
        if key in role.lower():
            return pool
    return ROLE_COMPANIES["default"]


async def _log(db, pathway_id: str, msg: str, stage: str = None):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"{ts}  {msg}"
    update = {"$push": {"stage_logs": {"$each": [line], "$slice": -80}}}
    if stage:
        update["$set"] = {"stage": stage}
    await db.pathways.update_one({"id": pathway_id}, update)
    logger.info(f"{pathway_id[:8]}  {line}")


async def run(pathway_id: str, db):
    """Main pipeline. Called as a FastAPI BackgroundTask."""
    try:
        await db.pathways.update_one(
            {"id": pathway_id},
            {"$set": {"status": "running", "stage_logs": [], "stage": "init"}}
        )
        p = await db.pathways.find_one({"id": pathway_id}, {"_id": 0})

        # Clear old results
        for col in ["internships", "unlisted_companies", "outreach_emails"]:
            await db[col].delete_many({"pathway_id": pathway_id})

        # ── Stage 1: Listed jobs ───────────────────────────────────────────────
        await _log(db, pathway_id, "Orchestrator ▶ Stage 1 — Listed-Jobs Scraper", "scraping_listed")
        await asyncio.sleep(1.2)
        pool = _companies_for(p["role_category"])
        listed = []
        for _ in range(random.randint(6, 12)):
            co = random.choice(pool)
            loc = p.get("location") or random.choice(LOCATIONS)
            stipend = random.choice([15000, 20000, 25000, 30000, 40000, 50000])
            listed.append(Internship(
                pathway_id=pathway_id,
                source=random.choice(SOURCES),
                title=f"{p['role_category'].split()[0]} Intern",
                company=co, location=loc,
                is_remote=p.get("remote_type", "any"),
                stipend_or_salary=f"₹{stipend}/month",
                posted_date=f"{random.randint(1,14)} days ago",
                apply_url=f"https://example.com/jobs/{co.lower().replace(' ','-')}",
                description_snippet=f"Hiring intern to work on {p['role_category'].lower()} projects.",
            ).model_dump())
        await db.internships.insert_many(listed)
        await _log(db, pathway_id, f"Agent 1 ✓  Scraped {len(listed)} listings across {', '.join(SOURCES[:3])}")

        # ── Stage 2: Unlisted companies ───────────────────────────────────────
        await _log(db, pathway_id, "Stage 2 — Discovering unlisted startups", "discovering_unlisted")
        await asyncio.sleep(1.2)
        all_cos = _companies_for(p["role_category"]) + EXTRA_STARTUPS
        random.shuffle(all_cos)
        unlisted_docs = []
        unlisted_objs = []
        for co in all_cos[:random.randint(5, 9)]:
            slug = co.lower().replace(" ", "-")
            if random.random() < 0.4:
                email, src = f"careers@{slug}.com", "website_scrape"
            elif random.random() < 0.5:
                email, src = f"hiring@{slug}.com", "hunter_api"
            else:
                email, src = None, "not_found"
            obj = UnlistedCompany(
                pathway_id=pathway_id,
                company_name=co,
                domain_keywords=[w.lower() for w in p["role_category"].split()][:3],
                website_url=f"https://{slug}.com",
                contact_email=email, email_source_type=src,
                evidence_url=f"https://news.ycombinator.com/item?id={random.randint(38000000,39999999)}",
                relevance_score=round(random.uniform(0.55, 0.95), 2),
                notes=f"Recently raised funding, works in {p['role_category'].split()[0]} space.",
            )
            unlisted_objs.append(obj)
            unlisted_docs.append(obj.model_dump())
        await db.unlisted_companies.insert_many(unlisted_docs)
        found_emails = sum(1 for u in unlisted_objs if u.contact_email)
        await _log(db, pathway_id, f"Agent 2 ✓  Found {len(unlisted_objs)} companies, {found_emails} emails")

        # ── Stage 3: Email finder ─────────────────────────────────────────────
        await _log(db, pathway_id, "Stage 3 — Email finder (website scrape + provider stack)", "email_finding")
        await asyncio.sleep(1.0)
        await _log(db, pathway_id, f"Agent 3 ✓  {found_emails}/{len(unlisted_objs)} contacts resolved")

        # ── Stage 4: Resume understanding ─────────────────────────────────────
        await _log(db, pathway_id, "Stage 4 — Resume Understanding Agent (LLM)", "understanding_resume")
        resume_text = p.get("resume_text", "")
        profile = {"skills": [], "experience_summary": "", "preferred_domains": [], "keywords": []}
        if resume_text:
            sys_msg = ("You extract structured candidate profiles from resumes. "
                       "Return STRICT JSON with keys: skills (list), experience_summary (string, 2-3 sentences), "
                       "preferred_domains (list), keywords (list of 8-12). No markdown, no extra text.")
            usr_msg = f"Resume:\n{resume_text[:6000]}\n\nJSON only."
            raw = await llm_router.call("extract", sys_msg, usr_msg,
                                        f"resume-{pathway_id}", pathway=p)
            try:
                start, end = raw.find("{"), raw.rfind("}")
                profile = json.loads(raw[start:end+1]) if start >= 0 else profile
            except Exception:
                pass
        else:
            role = p["role_category"]
            profile = {
                "skills": ["Python", "SQL", "Excel", "Communication"],
                "experience_summary": f"Candidate seeking {role} internship with strong analytical skills.",
                "preferred_domains": [role],
                "keywords": ["analysis", "strategy", "operations", "data", "research"],
            }
        await db.resume_profiles.update_one(
            {"pathway_id": pathway_id},
            {"$set": {"pathway_id": pathway_id, "profile": profile, "updated_at": _now()}},
            upsert=True,
        )
        await _log(db, pathway_id,
                   f"Agent 4 ✓  Extracted {len(profile.get('skills',[]))} skills, "
                   f"{len(profile.get('keywords',[]))} keywords")

        # ── Stage 5: Matching + email drafting ────────────────────────────────
        await _log(db, pathway_id, "Stage 5 — Matching & Email Drafting Agent (LLM)", "drafting_emails")
        skills_str = ", ".join(profile.get("skills", [])[:8])
        drafts = []
        for u in unlisted_objs:
            if not u.contact_email or u.relevance_score < 0.6:
                continue
            subject, body = "", ""
            if resume_text:
                sys_msg = ("You draft concise, personalized internship outreach emails. "
                           "Tone: respectful, specific, under 150 words. "
                           "Return STRICT JSON with keys: subject, body. No markdown.")
                usr_msg = (f"Pathway role: {p['role_category']}\n"
                           f"Candidate skills: {skills_str}\n"
                           f"Summary: {profile.get('experience_summary','')}\n"
                           f"Company: {u.company_name} ({u.website_url})\n"
                           f"Notes: {u.notes}\n"
                           f"Keywords: {', '.join(u.domain_keywords)}\n"
                           "Write personalized email. JSON only.")
                raw = await llm_router.call("draft_email", sys_msg, usr_msg,
                                            f"draft-{pathway_id}-{u.id[:6]}", pathway=p)
                try:
                    s, e = raw.find("{"), raw.rfind("}")
                    d = json.loads(raw[s:e+1]) if s >= 0 else {}
                    subject, body = d.get("subject", ""), d.get("body", "")
                except Exception:
                    pass
            if not subject:
                subject = f"Internship Inquiry — {p['role_category']} @ {u.company_name}"
            if not body:
                body = (f"Hi,\n\nI came across {u.company_name} and was impressed by your work "
                        f"in {', '.join(u.domain_keywords[:2])}.\n\n"
                        f"I'm actively seeking a {p['role_category']} internship and believe my "
                        f"background in {skills_str[:80]} aligns well with what you're building.\n\n"
                        f"Would you be open to a brief conversation?\n\nBest,\nAayush")
            drafts.append(OutreachEmail(
                pathway_id=pathway_id,
                unlisted_company_id=u.id,
                company_name=u.company_name,
                email_to=u.contact_email,
                subject=subject, body=body,
            ).model_dump())
        if drafts:
            await db.outreach_emails.insert_many(drafts)
        await _log(db, pathway_id, f"Agent 5 ✓  Drafted {len(drafts)} personalized emails")

        # ── Stage 6: Awaiting approval ────────────────────────────────────────
        await _log(db, pathway_id,
                   "Stage 6 — Pipeline complete ✓  Review emails before sending",
                   "awaiting_approval")
        await db.pathways.update_one(
            {"id": pathway_id},
            {"$set": {"status": "completed", "last_run_at": _now()}}
        )

    except Exception as e:
        logger.exception("Pathway run failed")
        await _log(db, pathway_id, f"ERROR: {e}", "error")
        await db.pathways.update_one({"id": pathway_id}, {"$set": {"status": "error"}})
        