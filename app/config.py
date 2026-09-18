"""
Configuration management for GridWise.
Loads from environment variables / .env file.

Supports two LLM providers:
  - openai  (OPENAI_API_KEY)
  - groq    (GROQ_API_KEY) — uses Groq's OpenAI-compatible endpoint
"""
import logging
import os

from dotenv import load_dotenv

load_dotenv()


def _get_bool(key: str, default: bool) -> bool:
    val = os.getenv(key, "").strip().lower()
    if val in ("1", "true", "yes"):
        return True
    if val in ("0", "false", "no"):
        return False
    return default


# --- API Keys ---
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

# --- LLM Provider: "openai" or "groq" ---
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq" if GROQ_API_KEY else "openai").lower()

# --- LLM Model defaults per provider ---
_DEFAULT_MODELS = {
    "openai": "gpt-4o",
    "groq": "openai/gpt-oss-120b",
}
LLM_MODEL: str = os.getenv("LLM_MODEL", _DEFAULT_MODELS.get(LLM_PROVIDER, "gpt-4o"))

# --- Flags ---
MOCK_LLM: bool = _get_bool("MOCK_LLM", False)
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

# Numerical tolerance for floating-point feasibility checks
FEASIBILITY_TOL: float = 1e-5

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
