import logging

import google.generativeai as genai

from config import settings
from ragchat.cache import TTLCache, cache_key, normalize_query
from ragchat.constants import GEMINI_MODEL, LLM_CACHE_TTL, LLM_FALLBACK

logger = logging.getLogger(__name__)

_llm_cache = TTLCache(ttl_seconds=LLM_CACHE_TTL)


def generate_answer(prompt: str) -> str:
    key = cache_key("llm", normalize_query(prompt))
    cached = _llm_cache.get(key)
    if cached is not None:
        return cached

    keys = settings.gemini_keys
    if not keys:
        logger.warning("No Gemini API key configured")
        return LLM_FALLBACK

    last_error: Exception | None = None
    for api_key in keys:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(GEMINI_MODEL)
            response = model.generate_content(prompt)
            text = (getattr(response, "text", None) or "").strip()
            if not text:
                continue
            _llm_cache.set(key, text)
            return text
        except Exception as exc:
            last_error = exc
            logger.warning("Gemini key failed: %s", exc)

    if last_error is not None:
        logger.error("All Gemini keys failed: %s", last_error)
    return LLM_FALLBACK


def clear_llm_cache() -> None:
    _llm_cache.clear()
