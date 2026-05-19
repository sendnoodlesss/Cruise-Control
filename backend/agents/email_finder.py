"""
Email Finder Agent.
Priority order:
  1. Website scrape (free)
  2. Hunter.io (25 free searches/month)
  3. Mark as not found

Stores person-level Contact records, de-prioritises careers@/info@ generics.
"""
import os
import re
import logging
import httpx
from typing import Optional
from backend.models import UnlistedCompany, Contact

logger = logging.getLogger(__name__)

GENERIC_PREFIXES = {"careers", "info", "hello", "hi", "contact", "team",
                    "jobs", "recruitment", "hr", "admin", "support"}


def _is_generic(email: str) -> bool:
    local = email.split("@")[0].lower()
    return local in GENERIC_PREFIXES


def _scrape_website(domain: str) -> Optional[str]:
    """Try to find a non-generic email on the company's homepage."""
    try:
        r = httpx.get(f"https://{domain}", timeout=8, follow_redirects=True,
                      headers={"User-Agent": "Mozilla/5.0"})
        emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
                            r.text)
        # Prefer person-level emails, then fallback to generic
        personal = [e for e in emails
                    if domain.split(".")[0] in e and not _is_generic(e)]
        generic  = [e for e in emails if _is_generic(e)]
        return (personal or generic or [None])[0]
    except Exception as e:
        logger.debug(f"Website scrape failed for {domain}: {e}")
        return None


def _hunter_lookup(domain: str, api_key: str) -> Optional[dict]:
    """
    Hunter.io domain search — returns best contact dict or None.
    API docs: https://hunter.io/api-documentation/v2#domain-search
    Env var:  HUNTER_API_KEY
    Free tier: 25 searches/month
    """
    try:
        r = httpx.get(
            "https://api.hunter.io/v2/domain-search",
            params={"domain": domain, "api_key": api_key, "limit": 5},
            timeout=10,
        )
        data = r.json().get("data", {})
        emails = data.get("emails", [])
        if not emails:
            return None
        # Sort: founder > executive > it/engineering > other; skip generics
        SENIORITY_RANK = {"founder": 0, "executive": 1, "it": 2,
                          "engineering": 2, "hr": 3, "other": 4}
        personal = [e for e in emails if not _is_generic(e.get("value", ""))]
        if not personal:
            return None
        personal.sort(key=lambda e: SENIORITY_RANK.get(
            (e.get("seniority") or e.get("department") or "other").lower(), 4))
        best = personal[0]
        return {
            "email":    best.get("value"),
            "name":     f"{best.get('first_name','')} {best.get('last_name','')}".strip(),
            "title":    best.get("position", ""),
            "seniority": best.get("seniority", "unknown"),
        }
    except Exception as e:
        logger.debug(f"Hunter lookup failed for {domain}: {e}")
        return None


def find_email_for_company(company: UnlistedCompany,
                            pathway: dict,
                            db_providers: list) -> tuple[Optional[str], str, Optional[str], Contact | None]:
    """
    Returns (email, source_type, provider_name, Contact|None).
    Tries: website scrape → Hunter → None.
    """
    domain = company.website_url.replace("https://", "").replace("http://", "").split("/")[0]

    # 1. Website scrape (always free)
    email = _scrape_website(domain)
    if email:
        contact = Contact(
            pathway_id=company.pathway_id,
            company_id=company.id,
            company_name=company.company_name,
            email=email,
            seniority="unknown",
            provider_name="website_scrape",
        )
        return email, "website_scrape", None, contact

    # 2. Hunter.io (if key available and pathway allows external finders)
    if pathway.get("use_external_finders", True):
        hunter_key = os.getenv("HUNTER_API_KEY", "")
        if hunter_key:
            result = _hunter_lookup(domain, hunter_key)
            if result:
                contact = Contact(
                    pathway_id=company.pathway_id,
                    company_id=company.id,
                    company_name=company.company_name,
                    name=result.get("name"),
                    title=result.get("title"),
                    email=result["email"],
                    seniority=result.get("seniority", "unknown"),
                    provider_name="hunter",
                    verified=True,
                )
                return result["email"], "hunter_api", "hunter", contact

    return None, "not_found", None, None
