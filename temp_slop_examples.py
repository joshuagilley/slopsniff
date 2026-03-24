"""Temporary fixture file to trigger SlopSniff findings."""

import os


def load_settings() -> dict[str, object]:
    # fallback-defaults: primitive env fallback
    timeout = os.getenv("TIMEOUT_SECONDS", 0)

    # fallback-defaults: catch-all returning primitive
    try:
        retries = int(os.getenv("RETRIES", 0))
    except Exception:
        return {}

    return {"timeout": timeout, "retries": retries}


# exposed-secrets: OpenAI-style key shape
TEMP_API_KEY = "sk-proj-abcdefghijklmnopqrstuvwxyz1234567890AB"
