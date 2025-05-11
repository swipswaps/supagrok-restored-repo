#!/usr/bin/env python3
# PRF‑SUPAGROK‑V3‑MUX‑ROUTER‑TESTER‑WITH‑GEMINI
# UUID: e7825b0a-7190-4a9d-8084-d8e26db67a00
# VERSION: v2.0 — Adds clipboard/env key ingestion, Gemini path prioritized

import os, json, requests

PROMPT = "Summarize how photosynthesis works in 2 sentences."
BASE_URL = "http://localhost:8000/api"

def get_key():
    try:
        import pyperclip
        clip = pyperclip.paste().strip()
        if clip:
            return clip
    except Exception:
        pass
    return os.getenv("SUPAGROK_API_KEY") or input("Paste your API key: ").strip()

def test_llm(endpoint, key):
    print(f"🚀 Testing /{endpoint}")
    url = f"{BASE_URL}/{endpoint}"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    try:
        res = requests.post(url, json={"prompt": PROMPT}, headers=headers, timeout=15)
        res.raise_for_status()
        print("✅", res.json().get("response", "")[:300])
    except Exception as e:
        print(f"❌ {endpoint} failed:", e)

if __name__ == "__main__":
    key = get_key()
    for ep in ["ask_gemini", "ask_claude", "ask_groq", "ask_openai"]:
        test_llm(ep, key)
