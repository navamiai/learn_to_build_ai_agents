"""
config.py
Centralizes API key + provider loading so persona_bot.py never touches
os.environ directly.

load_dotenv() reads your .env file and copies each entry into the OS's
real environment variables (os.environ) — it doesn't create a separate,
private store. So the lookups below work identically whether a key was
set in .env, exported in your shell, or configured at the OS/system level
(e.g. in your CI provider or a system-wide environment file).
"""

import os

from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
PROVIDER = os.environ.get("PROVIDER", "anthropic")


def get_api_key(provider: str) -> str:
    """Return the API key for the given provider, or raise a clear KeyError
    naming the exact system environment variable that's missing."""
    key = OPENAI_API_KEY if provider == "openai" else ANTHROPIC_API_KEY
    if not key:
        raise KeyError("OPENAI_API_KEY" if provider == "openai" else "ANTHROPIC_API_KEY")
    return key


def has_api_key(provider: str) -> bool:
    return bool(OPENAI_API_KEY if provider == "openai" else ANTHROPIC_API_KEY)
