"""
Cruise Control – Agent Internship Hunter
Backend entry point.

Run:  uvicorn main:app --reload --port 8001 
"""
import os, csv, io, json, logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timezone

from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import pypdf, docx

from models import (
    PathwayBase, PathwayCreate, PathwayUpdate,
    EmailProvider, EmailProviderCreate,
    Internship, UnlistedCompany, OutreachEmail, EmailUpdate, SendRequest,
)
from llm_router import get_catalogue

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

UPLOAD_DIR = ROOT / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

mongo_client = AsyncIOMotorClient(os.environ["MONGO_URL"])
db = mongo_client[os.environ["DB_NAME"]]

app = FastAPI(title="Cruise Control – Agent Internship Hunter")
api = APIRouter(prefix="/api")
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _now(): return datetime.now(timezone.utc).isoformat()


async def _pathway(pid: str) -> dict:
    p = await db.pathways.find_one({"id": pid}, {"_id": 0})
    if not p:
        raise HTTPException(404, "Pathway not found")
    return p


def _extract(path: Path, fn: str) -> str:
    try:
        if fn.lower().endswith(".pdf"):
            return "\n".join(
                pg.extract_text() or "" for pg in pypdf.PdfReader(str(path)).pages
            )
        if fn.lower().endswith((".docx", ".doc")):
            return "\n".join(p.text for p in docx.Document(str(path)).paragraphs)
        return path.read_text(errors="ignore")
    except Exception as e:
        logger.warning(f"Resume parse failed: {e}")
        return ""


def _csv(rows: list, filename: str) -> StreamingResponse:
    buf = io.StringIO()
    if rows:
        w = csv.DictWriter(buf, fieldnames=list(rows[0].keys()),
                           extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({
                k: (json.dumps(v) if isinstance(v, (list, dict)) else v)
                for k, v in r.items()
            })
    else:
        buf.write("no data")
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]), media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ── LLM call (routes through llm_router — no Emergent dependency) ─────────────

async def llm_call(system: str, user: str, session_id: str,
                   task_type: str = "draft_email",
                   pathway: dict = None) -> str:
    """
    Central LLM entry point for all agents.
    Routes to the correct provider/model via llm_router based on
    task_type and the pathway's llm_mode / llm_tier / per-agent overrides.
    """
    from llm_router import call as router_call
    return await router_call(
        task_type=task_type,
        system=system,
        user=user,
        session_id=session_id,
        pathway=pathway or {},
    )


# ── Stats & root ──────────────────────────────────────────────────────────────

@api.get("/")
async def root():
    return {"app": "Cruise Control", "status": "ok"}


@api.get("/stats")
async def stats():
    try:
        return {
            "pathways": await db.pathways.count_documents({}),
            "running": await db.pathways.count_documents({"status": "running"}),
            "emails_sent": await db.outreach_emails.count_documents({"status": "sent"}),
            "drafts": await db.outreach_emails.count_documents({"status": "draft"}),
            "unlisted_found": await db.unlisted_companies.count_documents({}),
        }
    except Exception as e:
        logger.exception("Stats query failed")
        return {
            "pathways": 0,
            "running": 0,
            "emails_sent": 0,
            "drafts": 0,
            "unlisted_found": 0,
            "db_error": str(e),
        }

# ── Models catalogue (used by frontend LLM picker dropdown) ──────────────────

@api.get("/models/catalogue")
async def models_catalogue():
    return [
        {"id": "auto", "label": "Auto Router"},
        {"id": "groq-llama3-8b", "label": "Groq Llama 3 8B"},
        {"id": "groq-llama3-70b", "label": "Groq Llama 3 70B"},
        {"id": "openai-gpt-4o-mini", "label": "OpenAI GPT-4o mini"},
        {"id": "anthropic-sonnet", "label": "Anthropic Claude Sonnet"},
    ]

# ── Pathways ──────────────────────────────────────────────────────────────────

@api.post("/pathways", response_model=PathwayBase)
async def create_pathway(payload: PathwayCreate):
    if await db.pathways.count_documents({}) >= 5:
        raise HTTPException(400, "Maximum 5 pathways allowed")
    p = PathwayBase(**payload.model_dump())
    await db.pathways.insert_one(p.model_dump())
    return p


@api.get("/pathways", response_model=List[PathwayBase])
async def list_pathways():
    try:
        return await db.pathways.find({}, {"_id": 0}).sort("created_at", 1).to_list(50)
    except Exception:
        logger.exception("List pathways failed")
        return []

@api.get("/pathways/{pid}", response_model=PathwayBase)
async def get_pathway(pid: str):
    return await _pathway(pid)


@api.put("/pathways/{pid}", response_model=PathwayBase)
async def update_pathway(pid: str, payload: PathwayUpdate):
    await _pathway(pid)
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if updates:
        await db.pathways.update_one({"id": pid}, {"$set": updates})
    return await _pathway(pid)


@api.delete("/pathways/{pid}")
async def delete_pathway(pid: str):
    await _pathway(pid)
    # Delete pathway document itself
    await db.pathways.delete_one({"id": pid})
    # Delete all related collections
    for col in ["internships", "unlisted_companies", "outreach_emails",
                "email_providers", "resume_profiles", "contacts"]:
        await db[col].delete_many({"pathway_id": pid})
    return {"ok": True}


# ── Resume ────────────────────────────────────────────────────────────────────

@api.post("/pathways/{pid}/resume")
async def upload_resume(pid: str, file: UploadFile = File(...)):
    await _pathway(pid)
    fp = UPLOAD_DIR / f"{pid}_{file.filename}"
    fp.write_bytes(await file.read())
    text = _extract(fp, file.filename)
    await db.pathways.update_one(
        {"id": pid},
        {"$set": {"resume_filename": file.filename, "resume_text": text[:20000]}},
    )
    return {"ok": True, "filename": file.filename, "chars": len(text)}


# ── Email providers ───────────────────────────────────────────────────────────

@api.post("/pathways/{pid}/email-providers", response_model=EmailProvider)
async def add_provider(pid: str, payload: EmailProviderCreate):
    await _pathway(pid)
    masked = (payload.api_key[:4] + "••••" + payload.api_key[-4:]
              if len(payload.api_key) >= 8 else "••••")
    prov = EmailProvider(
        pathway_id=pid,
        provider_name=payload.provider_name,
        api_key_masked=masked,
        priority=payload.priority,
        daily_credit_limit=payload.daily_credit_limit,
        enabled=payload.enabled,
    )
    doc = prov.model_dump()
    doc["api_key_full"] = payload.api_key   # stored securely, never returned by API
    await db.email_providers.insert_one(doc)
    return prov


@api.get("/pathways/{pid}/email-providers", response_model=List[EmailProvider])
async def list_providers(pid: str):
    return await db.email_providers.find(
        {"pathway_id": pid}, {"_id": 0, "api_key_full": 0}
    ).sort("priority", 1).to_list(20)


@api.delete("/email-providers/{eid}")
async def del_provider(eid: str):
    await db.email_providers.delete_one({"id": eid})
    return {"ok": True}


# ── Run pipeline ──────────────────────────────────────────────────────────────

@api.post("/pathways/{pid}/run")
async def run_pathway(pid: str, bg: BackgroundTasks):
    p = await _pathway(pid)
    if p.get("status") == "running":
        raise HTTPException(400, "Already running")
    from agents.orchestrator import run as run_agents
    bg.add_task(run_agents, pid, db)
    return {"ok": True, "status": "started"}


@api.get("/pathways/{pid}/status")
async def pathway_status(pid: str):
    p = await _pathway(pid)
    return {
        "status":     p.get("status"),
        "stage":      p.get("stage"),
        "stage_logs": p.get("stage_logs", []),
    }


# ── Results ───────────────────────────────────────────────────────────────────

@api.get("/pathways/{pid}/internships", response_model=List[Internship])
async def list_internships(pid: str):
    return await db.internships.find(
        {"pathway_id": pid}, {"_id": 0}
    ).to_list(500)


@api.get("/pathways/{pid}/unlisted-companies", response_model=List[UnlistedCompany])
async def list_unlisted(pid: str):
    return await db.unlisted_companies.find(
        {"pathway_id": pid}, {"_id": 0}
    ).sort("relevance_score", -1).to_list(500)


@api.get("/pathways/{pid}/email-drafts", response_model=List[OutreachEmail])
async def list_drafts(pid: str):
    return await db.outreach_emails.find(
        {"pathway_id": pid}, {"_id": 0}
    ).sort("created_at", 1).to_list(500)


@api.put("/email-drafts/{eid}")
async def update_email(eid: str, payload: EmailUpdate):
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if updates:
        await db.outreach_emails.update_one({"id": eid}, {"$set": updates})
    return await db.outreach_emails.find_one({"id": eid}, {"_id": 0})


@api.delete("/email-drafts/{eid}")
async def remove_email(eid: str):
    await db.outreach_emails.update_one(
        {"id": eid}, {"$set": {"status": "removed"}}
    )
    return {"ok": True}


@api.post("/pathways/{pid}/send-emails")
async def send_emails(pid: str, payload: SendRequest):
    p = await _pathway(pid)
    limit = p.get("daily_send_limit", 20)
    sent_today = await db.outreach_emails.count_documents({
        "pathway_id": pid,
        "status": "sent",
        "sent_at": {"$gte": datetime.now(timezone.utc).date().isoformat()},
    })
    to_send = payload.email_ids[:max(0, limit - sent_today)]
    for eid in to_send:
        await db.outreach_emails.update_one(
            {"id": eid}, {"$set": {"status": "sent", "sent_at": _now()}}
        )
    return {
        "sent":        len(to_send),
        "skipped":     len(payload.email_ids) - len(to_send),
        "daily_limit": limit,
        "note":        "Gmail OAuth in Phase 2",
    }


# ── Exports ───────────────────────────────────────────────────────────────────

@api.get("/pathways/{pid}/export-internships")
async def exp_internships(pid: str):
    p = await _pathway(pid)
    rows = await db.internships.find(
        {"pathway_id": pid}, {"_id": 0}
    ).to_list(1000)
    return _csv(rows, f"Listed-{p['name'].replace(' ', '_')}.csv")


@api.get("/pathways/{pid}/export-unlisted")
async def exp_unlisted(pid: str):
    p = await _pathway(pid)
    rows = await db.unlisted_companies.find(
        {"pathway_id": pid}, {"_id": 0}
    ).to_list(1000)
    return _csv(rows, f"Unlisted-{p['name'].replace(' ', '_')}.csv")


# ── Analytics ─────────────────────────────────────────────────────────────────

@api.get("/analytics")
async def analytics():
    pathways = await db.pathways.find(
        {}, {"_id": 0, "id": 1, "name": 1}
    ).to_list(10)
    result = []
    for pw in pathways:
        pid = pw["id"]
        result.append({
            "pathway_id":   pid,
            "pathway_name": pw["name"],
            "internships":  await db.internships.count_documents({"pathway_id": pid}),
            "unlisted":     await db.unlisted_companies.count_documents({"pathway_id": pid}),
            "drafted":      await db.outreach_emails.count_documents(
                                {"pathway_id": pid, "status": "draft"}),
            "sent":         await db.outreach_emails.count_documents(
                                {"pathway_id": pid, "status": "sent"}),
        })
    return result


# ── Integrations (Phase 2 stubs) ──────────────────────────────────────────────

@api.get("/integrations/status")
async def integrations_status():
    return {
        "gmail":    {"connected": False, "stub": True},
        "sheets":   {"connected": False, "stub": True},
        "calendar": {"connected": False, "stub": True},
        "note":     "Google OAuth integrations coming in Phase 2",
    }


@api.post("/integrations/gmail/connect")
async def gmail_connect():
    return {"ok": False, "stub": True, "message": "Gmail OAuth coming in Phase 2"}


@api.post("/integrations/sheets/connect")
async def sheets_connect():
    return {"ok": False, "stub": True, "message": "Google Sheets OAuth coming in Phase 2"}


@api.post("/integrations/calendar/connect")
async def calendar_connect():
    return {"ok": False, "stub": True,
            "message": "Google Calendar OAuth coming in Phase 2"}


# ── App wiring ────────────────────────────────────────────────────────────────

app.include_router(api)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
async def shutdown():
    mongo_client.close()