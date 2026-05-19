"""
Job Providers — pluggable interface.
  MockJobProvider: zero-cost dev data
  ApifyJobProvider: real scrape via Apify actor (needs APIFY_TOKEN in .env)
"""
import os
import random
import logging
from typing import List
from backend.models import Internship

logger = logging.getLogger(__name__)

LISTED_SOURCES = ["LinkedIn", "Indeed", "Internshala", "Glassdoor", "AngelList"]
LOCATIONS_POOL = ["Bangalore, IN", "Mumbai, IN", "Remote", "Delhi NCR, IN",
                  "Hyderabad, IN", "San Francisco, CA", "New York, NY", "London, UK"]

ROLE_COMPANY_POOL = {
    "business analyst": ["Razorpay","CRED","Meesho","Zerodha","Groww","Postman","Freshworks","Zoho"],
    "automation":       ["Make.com","Zapier","Bardeen","Tines","Pipedream","Activepieces","n8n.io","Relay.app"],
    "devops":           ["Render","Fly.io","Railway","Vercel","Northflank","Coolify","Porter","Spacelift"],
    "cloud":            ["Snowflake","Databricks","Confluent","MongoDB","Supabase","Neon","Turso","PlanetScale"],
    "ai":               ["Anthropic","Cohere","Mistral","Together AI","Replicate","Modal","Baseten","Fireworks AI"],
    "marketing":        ["Webflow","Framer","Notion","Linear","Loom","Cal.com"],
    "data":             ["dbt Labs","Hex","Preset","Metabase","Lightdash","Hightouch"],
    "default":          ["Lattice","Ramp","Brex","Mercury","Pilot","Deel","Rippling","Gusto"],
}


def _pick_pool(role: str) -> List[str]:
    r = role.lower()
    for key, pool in ROLE_COMPANY_POOL.items():
        if key in r:
            return pool
    return ROLE_COMPANY_POOL["default"]


class MockJobProvider:
    """Returns realistic-looking mock internships — no API calls."""

    def fetch(self, pathway: dict, count: int = 8) -> List[Internship]:
        companies = _pick_pool(pathway.get("role_category", ""))
        base_role = pathway.get("role_category", "").split()[0].strip() or "Intern"
        items = []
        for _ in range(count):
            c = random.choice(companies)
            loc = pathway.get("location") or random.choice(LOCATIONS_POOL)
            remote = (pathway.get("remote_type")
                      if pathway.get("remote_type") != "any"
                      else random.choice(["remote", "onsite", "hybrid"]))
            stipend = random.choice([15000, 20000, 25000, 30000, 40000, 50000])
            items.append(Internship(
                pathway_id=pathway["id"],
                source=random.choice(LISTED_SOURCES),
                title=f"{base_role} Intern",
                company=c,
                location=loc,
                is_remote=remote,
                stipend_or_salary=f"₹{stipend}/month",
                posted_date=f"{random.randint(1, 21)} days ago",
                apply_url=f"https://example.com/jobs/{c.lower().replace(' ', '-')}-intern",
                description_snippet=(
                    f"Hiring {base_role.lower()} intern to work on "
                    f"{pathway.get('role_category','').lower()} projects."
                ),
            ))
        return items


class ApifyJobProvider:
    """
    Scrapes real job listings via an Apify actor.
    Requires: APIFY_TOKEN in .env
    Actor used: https://apify.com/misceres/indeed-scraper (free tier: ~100 results/run)
    """

    ACTOR_ID = "misceres/indeed-scraper"

    def fetch(self, pathway: dict, count: int = 20) -> List[Internship]:
        token = os.getenv("APIFY_TOKEN", "")
        if not token:
            logger.warning("APIFY_TOKEN not set — falling back to MockJobProvider")
            return MockJobProvider().fetch(pathway, count)
        try:
            import httpx, time
            role = pathway.get("role_category", "intern")
            location = pathway.get("location", "India")
            # Start actor run
            run_resp = httpx.post(
                f"https://api.apify.com/v2/acts/{self.ACTOR_ID}/runs",
                params={"token": token},
                json={"position": role, "country": "IN", "location": location,
                      "maxItems": count, "parseCompanyDetails": False},
                timeout=30,
            )
            run_resp.raise_for_status()
            run_id = run_resp.json()["data"]["id"]
            # Poll for finish (max 60s)
            for _ in range(12):
                time.sleep(5)
                status = httpx.get(
                    f"https://api.apify.com/v2/actor-runs/{run_id}",
                    params={"token": token}, timeout=15,
                ).json()["data"]["status"]
                if status == "SUCCEEDED":
                    break
            # Fetch results
            items_resp = httpx.get(
                f"https://api.apify.com/v2/actor-runs/{run_id}/dataset/items",
                params={"token": token, "format": "json"}, timeout=15,
            )
            results = []
            for r in items_resp.json()[:count]:
                results.append(Internship(
                    pathway_id=pathway["id"],
                    source="Indeed (Apify)",
                    title=r.get("positionName", role),
                    company=r.get("company", "Unknown"),
                    location=r.get("location", location),
                    is_remote="remote" if "remote" in r.get("location","").lower() else "onsite",
                    stipend_or_salary=r.get("salary", "Not listed"),
                    posted_date=r.get("postedAt", "Recently"),
                    apply_url=r.get("url", ""),
                    description_snippet=r.get("description", "")[:300],
                ))
            return results
        except Exception as e:
            logger.error(f"ApifyJobProvider failed: {e} — falling back to mock")
            return MockJobProvider().fetch(pathway, count)


def get_provider(pathway: dict):
    """Return the correct provider based on pathway.job_provider."""
    if pathway.get("job_provider") == "apify":
        return ApifyJobProvider()
    return MockJobProvider()