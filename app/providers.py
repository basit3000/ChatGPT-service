"""
LLM Provider registry.

Each provider exposes an OpenAI-compatible /v1/models endpoint.
Models are always fetched live from the API and cached for CACHE_TTL seconds.
"""

import os
import time
import threading
from pathlib import Path
import httpx
from dotenv import load_dotenv

# Load .env from project root (one level up from app/)
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

CACHE_TTL = 300  # seconds

# ── provider definitions ────────────────────────────────────────
PROVIDERS = {
    "openai": {
        "name": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "env_key": "OPENAI_API_KEY",
        "default_model": "gpt-4o-mini",
    },
    "groq": {
        "name": "Groq",
        "base_url": "https://api.groq.com/openai/v1",
        "env_key": "GROQ_API_KEY",
        "default_model": "llama-3.3-70b-versatile",
    },
    "together": {
        "name": "Together",
        "base_url": "https://api.together.xyz/v1",
        "env_key": "TOGETHER_API_KEY",
        "default_model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    },
    "openrouter": {
        "name": "OpenRouter",
        "base_url": "https://openrouter.ai/api/v1",
        "env_key": "OPENROUTER_API_KEY",
        "default_model": "openai/gpt-4o-mini",
    },
}

# ── cache ────────────────────────────────────────────────────────
_cache: dict[str, dict] = {}      # provider -> {"models": [...], "ts": float}
_lock = threading.Lock()


def _fetch_models(provider: str, api_key: str | None = None) -> list[str]:
    """Hit the provider's /v1/models endpoint. Returns sorted model id list or empty list on failure."""
    cfg = PROVIDERS.get(provider)
    if not cfg:
        return []
    key = (api_key or os.getenv(cfg["env_key"], "")).strip()
    if not key:
        return []
    try:
        resp = httpx.get(
            f"{cfg['base_url']}/models",
            headers={"Authorization": f"Bearer {key}"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json().get("data", [])
        return sorted(m["id"] for m in data if m.get("id"))
    except Exception:
        return []


def get_models(provider: str, api_key: str | None = None) -> list[str]:
    """Return model list for a provider fetched live from the API (cached for CACHE_TTL)."""
    cfg = PROVIDERS.get(provider)
    if not cfg:
        return []

    with _lock:
        cached = _cache.get(provider)
        if cached and (time.time() - cached["ts"]) < CACHE_TTL:
            return cached["models"]

    models = _fetch_models(provider, api_key)
    if models:
        with _lock:
            _cache[provider] = {"models": models, "ts": time.time()}
    return models


def get_all_models(api_keys: dict[str, str | None] | None = None) -> dict[str, list[str]]:
    """Return {provider: [models]} for every registered provider."""
    keys = api_keys or {}
    return {p: get_models(p, keys.get(p)) for p in PROVIDERS}


def get_base_url(provider: str) -> str | None:
    """Return the base URL for the OpenAI client (None = default OpenAI)."""
    cfg = PROVIDERS.get(provider)
    if not cfg or provider == "openai":
        return None
    return cfg["base_url"]


def get_default_model(provider: str) -> str:
    cfg = PROVIDERS.get(provider)
    return cfg["default_model"] if cfg else "gpt-4o-mini"


def invalidate_cache(provider: str | None = None):
    """Clear cached models for one or all providers."""
    with _lock:
        if provider:
            _cache.pop(provider, None)
        else:
            _cache.clear()
