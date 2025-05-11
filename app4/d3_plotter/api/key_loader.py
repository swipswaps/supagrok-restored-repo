# PRF‑SUPAGROK‑V3‑KEY‑LOADER
# UUID: 4a7c24e5-d564-4041-90fd-8c2f23a391af
# PURPOSE: Load user-provided API key from forwarded header or fallback to .env

import os

def load_api_key(request) -> str:
    """
    Checks for a user-submitted API key in the request header.
    Falls back to environment variable if none found.
    """
    api_key = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key or len(api_key) < 20:
        raise ValueError("API key missing or invalid.")
    return api_key
