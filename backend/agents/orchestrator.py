"""
Orchestrator — runs the 6-stage agent pipeline for a pathway.
Called by main.py as a FastAPI BackgroundTask.
"""
import asyncio
import logging
import random
from datetime import datetime, timezone

from backend.models import OutreachEmail, UnlistedCompany
from backend.agents.job_providers  import get_provider
from backend.agents.email_finder   import find_email_for_company
from backend.agents.resume_agent   import extract_profile
from backend.agents.drafting_agent import draft_email

logger = logging.getLogger(__name__)

EXTRA_COMPANIES = [
    "Lumora Labs", "Northwind AI", "Quill Stack", "Vertex Loop",
    "Atlas Forge", "Pulse Synth", "Cobalt Path", "Mira Systems",
    "Helix Cloud", "Beacon Works",
]


def _now(): return datetime.now(timezone.utc).isoformat()


async def _log(db, pathway_id: str, msg: str, stage: str = None):
    update = {"$push": {"stage_logs": {"$each": [msg], "$slice": -50}}}
    if stage:
        update["$set"] = {"stage": stage}
    await db.pathways.update_one({"id": pathway_id}, update)
    logger.info(f"{pathway_id[:8]} | {msg}")


def _mock_unlisted(pathway: dict, count: int = 6) -> list[UnlistedCompany]:
    role_words = [w.strip().lower()
                  for w in pathway.get("role_category", "").replace(",", " ").split()
                  if w.strip()]
    pool = EXTRA_COMPANIES[:]
    random.shuffle(pool)
    out = []
    for c in pool[:count]:
        slug = c.lower().replace(" ", "-")
        domain = f"{slug}.com"
        out.append(UnlistedCompany(
            pathway_id=pathway["id"],
            company_name=c,
            domain_keywords=role_words[:3] + [random.choice(
                ["startup", "seed-stage", "series-a", "yc-backed"])],
            website_url=f"https://{domain}",
            evidence_url=(
                f"https://news.ycombinator.com/item?id="
                f"{random.randint(38_000_000, 39_999_999)}"
            ),
            relevance_score=round(random.uniform(0.55, 0.95), 2),
            notes=(
                f"Recently raised funding; works in "
                f"{pathway.get('role_category','').split()[0]} space."
            ),
        ))
    return out


async def run(pathway_id: str, db) -> None:
    """Main entry point — called as a background task."""
    try:
        await db.pathways.update_one(
            {"id": pathway_id},
            {"$set": {"status": "running", "stage_logs": [], "stage": "init"}},
        )
        p = await db.pathways.find_one({"id": pathway_id}, {"_id": 0})
        if not p:
            return

        # Clear prior results
        for col in ["internships", "unlisted_companies",
                    "outreach_emails", "contacts"]:
            await db[col].delete_many({"pathway_id": pathway_id})

        # ── Stage 1: Listed jobs scraper ──────────────────────────────────────
        await _log(db, pathway_id,
                   "Orchestrator starting → Listed-Jobs Scraper Agent",
                   "scraping_listed")
        await asyncio.sleep(1.2)
        provider = get_provider(p)
        listed = provider.fetch(p, count=random.randint(6, 12))
        if listed:
            await db.internships.insert_many([i.model_dump() for i in listed])
        await _log(db, pathway_id,
                   f"Agent 1 ✓ Scraped {len(listed)} listed internships "
                   f"({p.get('job_provider','mock')} provider)")

        # ── Stage 2: Unlisted company research ───────────────────────────────
        await _log(db, pathway_id,
                   "Agent 2 Discovering unlisted startups...",
                   "discovering_unlisted")
        await asyncio.sleep(1.2)
        unlisted = _mock_unlisted(p, count=random.randint(5, 9))
        if unlisted:
            await db.unlisted_companies.insert_many(
                [u.model_dump() for u in unlisted])
        await _log(db, pathway_id,
                   f"Agent 2 ✓ Found {len(unlisted)} unlisted companies")

        # ── Stage 3: Email finding (website scrape → Hunter) ─────────────────
        await _log(db, pathway_id,
                   "Agent 3 Running email scrape + provider fallback...",
                   "email_finding")
        await asyncio.sleep(1.0)
        db_providers = await db.email_providers.find(
            {"pathway_id": pathway_id, "enabled": True},
            {"_id": 0}
        ).sort("priority", 1).to_list(10)

        found_count = 0
        for u in unlisted:
            email, src_type, prov_name, contact = find_email_for_company(
                u, p, db_providers)
            if email:
                await db.unlisted_companies.update_one(
                    {"id": u.id},
                    {"$set": {"contact_email": email,
                               "email_source_type": src_type,
                               "email_provider_name": prov_name}},
                )
                u.contact_email = email
                found_count += 1
            if contact:
                await db.contacts.insert_one(contact.model_dump())

        await _log(db, pathway_id,
                   f"Agent 3 ✓ Emails found: {found_count}/{len(unlisted)}")

        # ── Stage 4: Resume understanding ─────────────────────────────────────
        await _log(db, pathway_id,
                   "Agent 4 Understanding resume with LLM...",
                   "understanding_resume")
        resume_text = p.get("resume_text", "")
        profile = await extract_profile(resume_text, p)
        await db.resume_profiles.update_one(
            {"pathway_id": pathway_id},
            {"$set": {"pathway_id": pathway_id,
                       "profile": profile, "updated_at": _now()}},
            upsert=True,
        )
        await _log(db, pathway_id,
                   f"Agent 4 ✓ Extracted {len(profile.get('skills',[]))} skills, "
                   f"{len(profile.get('keywords',[]))} keywords")

        # ── Stage 5: Matching + email drafting ───────────────────────────────
        await _log(db, pathway_id,
                   "Agent 5 Matching candidate to companies and drafting emails...",
                   "drafting_emails")
        drafts: list[OutreachEmail] = []
        for u in unlisted:
            if not u.contact_email or u.relevance_score < 0.60:
                continue
            subject, body = await draft_email(u, profile, p)
            drafts.append(OutreachEmail(
                pathway_id=pathway_id,
                unlisted_company_id=u.id,
                company_name=u.company_name,
                email_to=u.contact_email,
                subject=subject,
                body=body,
            ))
        if drafts:
            await db.outreach_emails.insert_many(
                [d.model_dump() for d in drafts])
        await _log(db, pathway_id,
                   f"Agent 5 ✓ Drafted {len(drafts)} personalized outreach emails")

        # ── Stage 6: Awaiting approval ───────────────────────────────────────
        await _log(db, pathway_id,
                   "Orchestrator ✓ Pipeline complete — awaiting user approval to send",
                   "awaiting_approval")
        await db.pathways.update_one(
            {"id": pathway_id},
            {"$set": {"status": "completed", "last_run_at": _now()}},
        )

    except Exception as e:
        logger.exception("Pathway run failed")
        await _log(db, pathway_id, f"ERROR: {e}", "error")
        await db.pathways.update_one(
            {"id": pathway_id},
            {"$set": {"status": "error"}},
        )