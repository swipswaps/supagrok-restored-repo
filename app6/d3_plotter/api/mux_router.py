# MUX router handling Gemini + OpenRouter fallback path
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from .key_loader import load_api_key
import requests

router = APIRouter()

@router.post("/api/ask_gemini_or_openrouter")
async def ask(req: Request):
    prompt = (await req.json()).get("prompt", "").strip()
    if not prompt:
        return JSONResponse({"error": "Missing prompt"}, status_code=400)

    key = load_api_key(req)
    try:
        import google.generativeai as genai
        from google.generativeai import GenerativeModel
        genai.configure(api_key=key)
        model = GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        return JSONResponse({"response": response.text, "source": "gemini"})
    except Exception as gemini_error:
        or_key = key
        headers = {
            "Authorization": f"Bearer {or_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "openai/gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}]
        }
        or_resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        final = or_resp.json()["choices"][0]["message"]["content"]
        return JSONResponse({"response": final, "source": "openrouter", "fallback": True})
