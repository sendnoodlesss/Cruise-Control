"""
LLM Router — smart auto tier switching + full manual model selection.

Supports:
  - Auto mode:   picks model by task_type + configured tier (cheap/balanced/premium)
  - Manual mode: uses a specific model ID chosen by the user

Model ID format:   "provider/model-name"
  e.g.  "groq/llama3-8b-8192"
        "anthropic/claude-3-5-haiku-20241022"
        "lmstudio/local"
        "ollama/llama3"
"""

import os
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ── Full Model Catalogue ──────────────────────────────────────────────────────
# id:       used in .env and frontend dropdown  (provider/model-name)
# label:    shown in UI
# provider: groq | together | openai | anthropic | lmstudio | ollama
# tier:     cheap | balanced | premium
# ctx_k:    context window in thousands of tokens
# free:     True if provider has a free tier

MODEL_CATALOGUE = [
    # ── Groq (free tier, very fast) ───────────────────────────────────────────
    {"id": "groq/llama3-8b-8192",          "label": "Llama 3 8B (Groq)",          "provider": "groq",      "tier": "cheap",    "ctx_k": 8,    "free": True},
    {"id": "groq/llama3-70b-8192",         "label": "Llama 3 70B (Groq)",         "provider": "groq",      "tier": "balanced", "ctx_k": 8,    "free": True},
    {"id": "groq/llama-3.1-8b-instant",    "label": "Llama 3.1 8B Instant (Groq)","provider": "groq",      "tier": "cheap",    "ctx_k": 128,  "free": True},
    {"id": "groq/llama-3.3-70b-versatile", "label": "Llama 3.3 70B (Groq)",       "provider": "groq",      "tier": "balanced", "ctx_k": 128,  "free": True},
    {"id": "groq/mixtral-8x7b-32768",      "label": "Mixtral 8x7B (Groq)",        "provider": "groq",      "tier": "balanced", "ctx_k": 32,   "free": True},
    {"id": "groq/gemma2-9b-it",            "label": "Gemma 2 9B (Groq)",          "provider": "groq",      "tier": "cheap",    "ctx_k": 8,    "free": True},

    # ── Together AI ────────────────────────────────────────────────────────────
    {"id": "together/mistralai/Mistral-7B-Instruct-v0.3",      "label": "Mistral 7B (Together)",        "provider": "together", "tier": "cheap",    "ctx_k": 32,  "free": False},
    {"id": "together/mistralai/Mixtral-8x7B-Instruct-v0.1",    "label": "Mixtral 8x7B (Together)",      "provider": "together", "tier": "balanced", "ctx_k": 32,  "free": False},
    {"id": "together/meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",  "label": "Llama 3.1 8B Turbo (Together)",  "provider": "together", "tier": "cheap",    "ctx_k": 128, "free": False},
    {"id": "together/meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo", "label": "Llama 3.1 70B Turbo (Together)", "provider": "together", "tier": "balanced", "ctx_k": 128, "free": False},
    {"id": "together/meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo","label": "Llama 3.2 11B Vision (Together)","provider": "together", "tier": "balanced", "ctx_k": 128, "free": False},
    {"id": "together/Qwen/Qwen2.5-72B-Instruct-Turbo",         "label": "Qwen 2.5 72B (Together)",     "provider": "together", "tier": "balanced", "ctx_k": 32,  "free": False},
    {"id": "together/deepseek-ai/DeepSeek-R1",                 "label": "DeepSeek R1 (Together)",      "provider": "together", "tier": "premium",  "ctx_k": 64,  "free": False},

    # ── OpenAI ─────────────────────────────────────────────────────────────────
    {"id": "openai/gpt-4o-mini",   "label": "GPT-4o Mini (OpenAI)",    "provider": "openai", "tier": "cheap",    "ctx_k": 128, "free": False},
    {"id": "openai/gpt-4o",        "label": "GPT-4o (OpenAI)",         "provider": "openai", "tier": "premium",  "ctx_k": 128, "free": False},
    {"id": "openai/gpt-4-turbo",   "label": "GPT-4 Turbo (OpenAI)",    "provider": "openai", "tier": "premium",  "ctx_k": 128, "free": False},
    {"id": "openai/o1-mini",       "label": "o1 Mini (OpenAI)",        "provider": "openai", "tier": "balanced", "ctx_k": 128, "free": False},

    # ── Anthropic ──────────────────────────────────────────────────────────────
    {"id": "anthropic/claude-3-5-haiku-20241022",  "label": "Claude 3.5 Haiku (Anthropic)", "provider": "anthropic", "tier": "balanced", "ctx_k": 200, "free": False},
    {"id": "anthropic/claude-3-5-sonnet-20241022", "label": "Claude 3.5 Sonnet (Anthropic)","provider": "anthropic", "tier": "premium",  "ctx_k": 200, "free": False},
    {"id": "anthropic/claude-opus-4-5",            "label": "Claude Opus 4 (Anthropic)",    "provider": "anthropic", "tier": "premium",  "ctx_k": 200, "free": False},

    # ── LM Studio (local — no key needed) ─────────────────────────────────────
    {"id": "lmstudio/local",              "label": "LM Studio — active model (local)",          "provider": "lmstudio", "tier": "cheap", "ctx_k": 32, "free": True},
    {"id": "lmstudio/llama3",             "label": "LM Studio — Llama 3 (local)",               "provider": "lmstudio", "tier": "cheap", "ctx_k": 8,  "free": True},
    {"id": "lmstudio/mistral-7b",         "label": "LM Studio — Mistral 7B (local)",            "provider": "lmstudio", "tier": "cheap", "ctx_k": 32, "free": True},
    {"id": "lmstudio/phi-3-mini",         "label": "LM Studio — Phi-3 Mini (local)",            "provider": "lmstudio", "tier": "cheap", "ctx_k": 4,  "free": True},
    {"id": "lmstudio/deepseek-r1-7b",     "label": "LM Studio — DeepSeek R1 7B (local)",       "provider": "lmstudio", "tier": "cheap", "ctx_k": 32, "free": True},
    {"id": "lmstudio/qwen2.5-7b",         "label": "LM Studio — Qwen 2.5 7B (local)",          "provider": "lmstudio", "tier": "cheap", "ctx_k": 32, "free": True},
    {"id": "lmstudio/gemma-3-4b",         "label": "LM Studio — Gemma 3 4B (local)",           "provider": "lmstudio", "tier": "cheap", "ctx_k": 8,  "free": True},
    {"id": "lmstudio/codestral-22b",      "label": "LM Studio — Codestral 22B (local)",        "provider": "lmstudio", "tier": "balanced","ctx_k": 32, "free": True},

    # ── Ollama (local — no key needed) ────────────────────────────────────────
    {"id": "ollama/llama3",               "label": "Ollama — Llama 3 (local)",                 "provider": "ollama", "tier": "cheap",    "ctx_k": 8,  "free": True},
    {"id": "ollama/llama3.1",             "label": "Ollama — Llama 3.1 (local)",               "provider": "ollama", "tier": "cheap",    "ctx_k": 128,"free": True},
    {"id": "ollama/mistral",              "label": "Ollama — Mistral (local)",                 "provider": "ollama", "tier": "cheap",    "ctx_k": 32, "free": True},
    {"id": "ollama/phi3",                 "label": "Ollama — Phi-3 (local)",                   "provider": "ollama", "tier": "cheap",    "ctx_k": 4,  "free": True},
    {"id": "ollama/qwen2.5",              "label": "Ollama — Qwen 2.5 (local)",                "provider": "ollama", "tier": "cheap",    "ctx_k": 32, "free": True},
    {"id": "ollama/deepseek-r1",          "label": "Ollama — DeepSeek R1 (local)",             "provider": "ollama", "tier": "balanced", "ctx_k": 64, "free": True},
    {"id": "ollama/codellama",            "label": "Ollama — Code Llama (local)",              "provider": "ollama", "tier": "cheap",    "ctx_k": 16, "free": True},
    {"id": "ollama/gemma3",               "label": "Ollama — Gemma 3 (local)",                 "provider": "ollama", "tier": "cheap",    "ctx_k": 8,  "free": True},
]

# ── Task → tier → model preference order ─────────────────────────────────────
# Format: { tier: [preferred_model_id, fallback1, fallback2, ...] }
TASK_ROUTING = {
    "extract": {        # resume field extraction — cheap is fine
        "cheap":    ["groq/llama3-8b-8192", "groq/gemma2-9b-it", "groq/llama-3.1-8b-instant"],
        "balanced": ["groq/llama3-70b-8192", "groq/llama-3.3-70b-versatile"],
        "premium":  ["anthropic/claude-3-5-haiku-20241022", "openai/gpt-4o-mini"],
    },
    "classify": {       # relevance scoring — cheap is fine
        "cheap":    ["groq/llama3-8b-8192", "groq/gemma2-9b-it"],
        "balanced": ["groq/mixtral-8x7b-32768", "groq/llama3-70b-8192"],
        "premium":  ["anthropic/claude-3-5-haiku-20241022", "openai/gpt-4o-mini"],
    },
    "research": {       # company research — balanced is good
        "cheap":    ["groq/llama-3.1-8b-instant", "groq/llama3-8b-8192"],
        "balanced": ["groq/llama3-70b-8192", "groq/mixtral-8x7b-32768"],
        "premium":  ["anthropic/claude-3-5-sonnet-20241022", "openai/gpt-4o"],
    },
    "draft_email": {    # personalized email drafting — quality matters
        "cheap":    ["groq/llama3-70b-8192", "groq/llama-3.3-70b-versatile"],
        "balanced": ["anthropic/claude-3-5-haiku-20241022", "openai/gpt-4o-mini"],
        "premium":  ["anthropic/claude-3-5-sonnet-20241022", "openai/gpt-4o"],
    },
}

# Auto-tier defaults per task (when llm_tier == "auto")
AUTO_TIER = {
    "extract":    "cheap",
    "classify":   "cheap",
    "research":   "balanced",
    "draft_email":"premium",
}


def get_catalogue():
    """Return the full model catalogue (for /api/models/catalogue endpoint)."""
    return MODEL_CATALOGUE


def _get_key(provider: str) -> str:
    keys = {
        "groq":      os.getenv("GROQ_API_KEY", ""),
        "together":  os.getenv("TOGETHER_API_KEY", ""),
        "openai":    os.getenv("OPENAI_API_KEY", ""),
        "anthropic": os.getenv("ANTHROPIC_API_KEY", ""),
    }
    return keys.get(provider, "")


def _resolve_model_id(task_type: str, pathway: dict) -> str:
    """
    Given a task type and pathway config, return a concrete model_id to call.
    Priority order:
      1. Per-agent manual override  (pathway.llm_agent_<task>)
      2. Global manual model        (pathway.llm_manual_model, when llm_mode=manual)
      3. Tier-based auto routing    (pathway.llm_tier, default=auto)
    """
    agent_key = f"llm_agent_{task_type.replace('draft_email', 'draft')}"
    per_agent = pathway.get(agent_key, "")
    if per_agent:
        return per_agent

    if pathway.get("llm_mode") == "manual" and pathway.get("llm_manual_model"):
        return pathway["llm_manual_model"]

    tier = pathway.get("llm_tier", "auto")
    if tier == "auto":
        tier = AUTO_TIER.get(task_type, "balanced")

    candidates = TASK_ROUTING.get(task_type, {}).get(tier, [])
    for model_id in candidates:
        provider = model_id.split("/")[0]
        if provider in ("lmstudio", "ollama"):
            return model_id
        if _get_key(provider):
            return model_id

    # Absolute fallback — groq free
    return "groq/llama3-8b-8192"


async def call(task_type: str, system: str, user: str, session_id: str,
               pathway: dict = None) -> str:
    """
    Main entry point for all LLM calls in agents.

    task_type: "extract" | "classify" | "research" | "draft_email"
    pathway:   the pathway dict (for reading llm_mode/tier/overrides)
    """
    pathway = pathway or {}
    model_id = _resolve_model_id(task_type, pathway)
    provider, model_name = model_id.split("/", 1)
    logger.info(f"[LLM] task={task_type} model={model_id}")
    return await _dispatch(provider, model_name, system, user, session_id)


async def call_model(model_id: str, system: str, user: str, session_id: str) -> str:
    """Call a specific model directly (for manual mode)."""
    provider, model_name = model_id.split("/", 1)
    return await _dispatch(provider, model_name, system, user, session_id)


async def _dispatch(provider: str, model_name: str,
                    system: str, user: str, session_id: str) -> str:
    try:
        if provider == "groq":
            return await _call_groq(model_name, system, user)
        if provider == "anthropic":
            return await _call_anthropic(model_name, system, user)
        if provider == "openai":
            return await _call_openai(model_name, system, user)
        if provider == "together":
            return await _call_together(model_name, system, user)
        if provider == "lmstudio":
            return await _call_lmstudio(model_name, system, user)
        if provider == "ollama":
            return await _call_ollama(model_name, system, user)
        raise ValueError(f"Unknown provider: {provider}")
    except Exception as e:
        logger.error(f"[LLM] {provider}/{model_name} failed: {e}")
        return ""


# ── Provider implementations ──────────────────────────────────────────────────

async def _call_groq(model: str, system: str, user: str) -> str:
    from groq import AsyncGroq
    client = AsyncGroq(api_key=_get_key("groq"))
    resp = await client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system},
                  {"role": "user",   "content": user}],
        max_tokens=2048,
        temperature=0.3,
    )
    return resp.choices[0].message.content or ""


async def _call_anthropic(model: str, system: str, user: str) -> str:
    import anthropic
    client = anthropic.AsyncAnthropic(api_key=_get_key("anthropic"))
    msg = await client.messages.create(
        model=model,
        max_tokens=2048,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return msg.content[0].text if msg.content else ""


async def _call_openai(model: str, system: str, user: str) -> str:
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=_get_key("openai"))
    resp = await client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system},
                  {"role": "user",   "content": user}],
        max_tokens=2048,
        temperature=0.3,
    )
    return resp.choices[0].message.content or ""


async def _call_together(model: str, system: str, user: str) -> str:
    import httpx
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(
            "https://api.together.xyz/v1/chat/completions",
            headers={"Authorization": f"Bearer {_get_key('together')}"},
            json={"model": model, "max_tokens": 2048, "temperature": 0.3,
                  "messages": [{"role": "system", "content": system},
                                {"role": "user",   "content": user}]},
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"] or ""


async def _call_lmstudio(model: str, system: str, user: str) -> str:
    """OpenAI-compatible endpoint exposed by LM Studio on localhost:1234"""
    import httpx
    base_url = os.getenv("LM_STUDIO_URL", "http://localhost:1234")
    async with httpx.AsyncClient(timeout=120) as c:
        r = await c.post(
            f"{base_url}/v1/chat/completions",
            json={"model": model if model != "local" else "local-model",
                  "max_tokens": 2048, "temperature": 0.3,
                  "messages": [{"role": "system", "content": system},
                                {"role": "user",   "content": user}]},
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"] or ""


async def _call_ollama(model: str, system: str, user: str) -> str:
    import httpx
    base_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    async with httpx.AsyncClient(timeout=120) as c:
        r = await c.post(
            f"{base_url}/api/chat",
            json={"model": model, "stream": False,
                  "messages": [{"role": "system", "content": system},
                                {"role": "user",   "content": user}]},
        )
        r.raise_for_status()
        return r.json()["message"]["content"] or ""