# PRF-SUPAGROK-V3-MUX-ROUTER-GEMINI-OPENROUTER
# UUID: mr-abcdef01-2345-6789-abcd-ef0123456789
# Version: 1.1
# Description: FastAPI router for Gemini with OpenRouter fallback.
# Full Path: supagrok/routers/mux_router.py

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
import os
import subprocess
import sys
import requests
import importlib.util
from typing import Dict, Any

# Assuming key_loader.py is in supagrok.api
try:
    from ..api.key_loader import load_api_key 
except ImportError:
    # Fallback for direct execution or different structure
    # This might be needed if running tests directly on this file outside the main app context
    # Correctly navigate up two levels from supagrok/routers to the project root, then to supagrok/api
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '..', '..')) 
    sys.path.insert(0, project_root) 
    from supagrok.api.key_loader import load_api_key

router = APIRouter()

# --- Gemini Configuration ---
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"

# --- OpenRouter Configuration ---
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_DEFAULT_MODEL = "openai/gpt-3.5-turbo" 

def install_package(package_name: str):
    """Installs a package using pip."""
    try:
        print(f"📦 Attempting to install {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"✅ Successfully installed {package_name}.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package_name}. Error: {e}")
        raise

def check_and_install_gemini_sdk():
    """Checks if google.generativeai is installed, and installs it if not."""
    if importlib.util.find_spec("google.generativeai") is None:
        print("🐍 Google Generative AI SDK not found.")
        install_package("google-generativeai")
    importlib.invalidate_caches() 

async def call_gemini_api(api_key: str, prompt: str) -> Dict[str, Any]:
    """Calls the Gemini API."""
    check_and_install_gemini_sdk()
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-pro")
    
    print(f"✨ Calling Gemini API with prompt: '{prompt[:50]}...'" )
    response = await model.generate_content_async(prompt) 
    return {"response": response.text, "source": "gemini", "model_used": "gemini-pro"}

async def call_openrouter_api(api_key: str, prompt: str, model: str = OPENROUTER_DEFAULT_MODEL) -> Dict[str, Any]:
    """Calls the OpenRouter API."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }
    print(f"↪️ Calling OpenRouter API with model {model} and prompt: '{prompt[:50]}...'" )
    
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(OPENROUTER_API_URL, headers=headers, json=data, timeout=30.0)
            response.raise_for_status()
            response_json = response.json()
    except ImportError:
        print("⚠️ httpx not installed, falling back to synchronous 'requests' for OpenRouter.")
        import requests 
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=data, timeout=30.0)
        response.raise_for_status()
        response_json = response.json()

    return {
        "response": response_json["choices"][0]["message"]["content"],
        "source": "openrouter",
        "model_used": model,
        "fallback_triggered": True
    }

@router.post("/ask_gemini_or_openrouter")
async def ask_gemini_or_openrouter_endpoint(req: Request):
    try:
        payload = await req.json()
        prompt = payload.get("prompt")
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required.")

        # Try Gemini first
        gemini_api_key = load_api_key(req, "GEMINI")
        if gemini_api_key:
            try:
                result = await call_gemini_api(gemini_api_key, prompt)
                print("✅ Gemini API call successful.")
                return JSONResponse(content=result)
            except Exception as e_gemini:
                print(f"⚠️ Gemini API call failed: {e_gemini}. Attempting OpenRouter fallback.")
        else:
            print("🔑 Gemini API key not available. Proceeding to OpenRouter.")

        # Fallback to OpenRouter
        openrouter_api_key = load_api_key(req, "OPENROUTER") 
        if not openrouter_api_key:
            raise HTTPException(status_code=401, detail="OpenRouter API key not found and Gemini failed or key was missing.")
        
        try:
            result = await call_openrouter_api(openrouter_api_key, prompt)
            print("✅ OpenRouter API call successful (as fallback).")
            return JSONResponse(content=result)
        except Exception as e_openrouter:
            print(f"❌ OpenRouter API call also failed: {e_openrouter}")
            raise HTTPException(status_code=500, detail=f"Both Gemini and OpenRouter calls failed. OpenRouter error: {str(e_openrouter)}")

    except HTTPException as http_exc:
        raise http_exc 
    except Exception as e:
        print(f"💥 Unexpected error in /ask_gemini_or_openrouter: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")