# PRF‑SUPAGROK‑V3‑MUX‑ROUTER
# UUID: 13c6a49f-bf62-4422-b8cd-13e4d8aa3101
# VERSION: FINAL—Gemini fallback chain + router export
# PURPOSE: Registers multiplexer routes for Gemini and OpenRouter access

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()

@router.post("/api/ask_gemini_or_openrouter")
async def ask_gemini_or_openrouter(req: Request):
    try:
        import importlib.util, subprocess, sys, os, requests

        def install(pkg):
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

        # ✅ Auto-install Google SDK
        if importlib.util.find_spec("google.generativeai") is None:
            install("google-generativeai")
        import google.generativeai as genai
        from google.generativeai import GenerativeModel

        body = await req.json()
        prompt = body.get("prompt", "").strip()
        if not prompt:
            return JSONResponse({"error": "Prompt required"}, status_code=400)

        # ✅ Secure and flexible key loader
        def get_key(service="GEMINI"):
            api_key = (
                req.headers.get("Authorization", "").replace("Bearer ", "").strip()
                or os.environ.get(f"{service}_API_KEY")
            )
            if not api_key:
                try:
                    import pyperclip
                    api_key = pyperclip.paste().strip()
                except Exception:
                    pass
            if not api_key:
                print(f"🔑 Paste your {service} key:")
                api_key = input(f"{service} API Key: ").strip()
            return api_key

        try:
            genai.configure(api_key=get_key("GEMINI"))
            response = GenerativeModel("gemini-pro").generate_content(prompt)
            return JSONResponse({
                "response": response.text,
                "source": "gemini"
            })
        except Exception as gemini_err:
            print("⚠️ Gemini failed, falling back to OpenRouter:", gemini_err)

        # ✅ Fallback: OpenRouter
        or_key = get_key("OPENROUTER")
        headers = {
            "Authorization": f"Bearer {or_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "openai/gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}]
        }
        resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        resp.raise_for_status()
        or_result = resp.json()
        final_reply = or_result["choices"][0]["message"]["content"]

        return JSONResponse({
            "response": final_reply,
            "source": "openrouter",
            "fallback": True
        })

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
