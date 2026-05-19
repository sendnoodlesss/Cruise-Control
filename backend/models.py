"""Pydantic schemas for Cruise Control."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone, date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


def _uid():   return str(uuid.uuid4())
def _now():   return datetime.now(timezone.utc).isoformat()
def _today(): return date.today().isoformat()


# ── Pathway ───────────────────────────────────────────────────────────────────

class PathwayBase(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id:               str  = Field(default_factory=_uid)
    name:             str
    role_category:    str
    industry:         Optional[str]   = None
    skills:           List[str]       = Field(default_factory=list)
    location:         Optional[str]   = None
    remote_type:      str  = "any"
    min_stipend:      Optional[int]   = None
    job_provider:     str  = "mock"            # "mock" | "apify"
    resume_filename:  Optional[str]   = None
    resume_text:      Optional[str]   = None
    status:           str  = "idle"
    stage:            Optional[str]   = None
    stage_logs:       List[str]       = Field(default_factory=list)
    sheets_sync:      bool = False
    calendar_followup:bool = False
    daily_send_limit: int  = 20
    use_external_finders:      bool = True
    max_external_lookups:      int  = 50
    max_providers_per_company: int  = 2
    # ── LLM settings ──────────────────────────────────────────────────────────
    llm_mode:             str = "auto"
    llm_tier:             str = "auto"
    llm_manual_model:     str = ""
    llm_agent_extract:    str = ""
    llm_agent_classify:   str = ""
    llm_agent_research:   str = ""
    llm_agent_draft:      str = ""
    # ──────────────────────────────────────────────────────────────────────────
    created_at:   str = Field(default_factory=_now)
    last_run_at:  Optional[str] = None


class PathwayCreate(BaseModel):
    name:             str
    role_category:    str
    industry:         Optional[str]   = None
    skills:           List[str]       = Field(default_factory=list)
    location:         Optional[str]   = None
    remote_type:      str  = "any"
    min_stipend:      Optional[int]   = None
    job_provider:     str  = "mock"
    sheets_sync:      bool = False
    calendar_followup:bool = False
    llm_mode:         str  = "auto"
    llm_tier:         str  = "auto"
    llm_manual_model: str  = ""
    llm_agent_extract:    str = ""
    llm_agent_classify:   str = ""
    llm_agent_research:   str = ""
    llm_agent_draft:      str = ""


class PathwayUpdate(BaseModel):
    name:             Optional[str]  = None
    role_category:    Optional[str]  = None
    industry:         Optional[str]  = None
    skills:           Optional[List[str]] = None
    location:         Optional[str]  = None
    remote_type:      Optional[str]  = None
    min_stipend:      Optional[int]  = None
    job_provider:     Optional[str]  = None
    sheets_sync:      Optional[bool] = None
    calendar_followup:Optional[bool] = None
    daily_send_limit: Optional[int]  = None
    use_external_finders:      Optional[bool] = None
    max_external_lookups:      Optional[int]  = None
    max_providers_per_company: Optional[int]  = None
    llm_mode:             Optional[str] = None
    llm_tier:             Optional[str] = None
    llm_manual_model:     Optional[str] = None
    llm_agent_extract:    Optional[str] = None
    llm_agent_classify:   Optional[str] = None
    llm_agent_research:   Optional[str] = None
    llm_agent_draft:      Optional[str] = None


# ── Email Provider ────────────────────────────────────────────────────────────

class EmailProvider(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id:              str  = Field(default_factory=_uid)
    pathway_id:      str
    provider_name:   str
    api_key_masked:  str
    priority:        int  = 1
    daily_credit_limit:           Optional[int] = 25
    estimated_credits_used_today: int  = 0
    last_reset_date:  str  = Field(default_factory=_today)
    enabled:          bool = True


class EmailProviderCreate(BaseModel):
    provider_name:      str
    api_key:            str
    priority:           int  = 1
    daily_credit_limit: Optional[int] = 25
    enabled:            bool = True


# ── Contact (Email Finder target — person-level) ──────────────────────────────

class Contact(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id:            str  = Field(default_factory=_uid)
    pathway_id:    str
    company_id:    str                        # UnlistedCompany.id
    company_name:  str
    name:          Optional[str] = None
    title:         Optional[str] = None
    email:         Optional[str] = None
    seniority:     str  = "unknown"           # founder | exec | hr | other
    provider_name: Optional[str] = None
    verified:      bool = False
    created_at:    str  = Field(default_factory=_now)


# ── Internship ────────────────────────────────────────────────────────────────

class Internship(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id:                  str = Field(default_factory=_uid)
    pathway_id:          str
    source:              str
    title:               str
    company:             str
    location:            str
    is_remote:           str
    stipend_or_salary:   str
    posted_date:         str
    apply_url:           str
    description_snippet: str
    created_at:          str = Field(default_factory=_now)


# ── Unlisted Company ──────────────────────────────────────────────────────────

class UnlistedCompany(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id:                str  = Field(default_factory=_uid)
    pathway_id:        str
    company_name:      str
    domain_keywords:   List[str] = Field(default_factory=list)
    website_url:       str
    contact_email:     Optional[str] = None
    email_source_type: str  = "website_scrape"
    email_provider_name: Optional[str] = None
    evidence_url:      str
    relevance_score:   float = 0.0
    notes:             str
    created_at:        str  = Field(default_factory=_now)


# ── Outreach Email ────────────────────────────────────────────────────────────

class OutreachEmail(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id:                  str = Field(default_factory=_uid)
    pathway_id:          str
    unlisted_company_id: str
    company_name:        str
    email_to:            str
    subject:             str
    body:                str
    status:              str = "draft"        # draft | approved | sent | failed | removed
    created_at:          str = Field(default_factory=_now)
    sent_at:             Optional[str] = None


class EmailUpdate(BaseModel):
    subject: Optional[str] = None
    body:    Optional[str] = None
    status:  Optional[str] = None


class SendRequest(BaseModel):
    email_ids: List[str]