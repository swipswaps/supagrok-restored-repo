# PRF-SUPAGROK-V3-KEY-LOADER
# UUID: kl-01234567-89ab-cdef-0123-456789abcdef
# Version: 1.0
# Description: Handles loading API keys from various sources for Supagrok.
# Full Path: supagrok/api/key_loader.py

import os
import subprocess
from fastapi import Request

def load_api_key(req: Request, service_name: str = "DEFAULT_API_KEY") -> str | None:
    """
    Loads API key from request headers, then environment variables,
    then clipboard (Linux/xclip only), then prompts user.
    """
    # 1. Try Authorization header
    api_key = req.headers.get("Authorization", "").replace("Bearer ", "").strip()
    if api_key:
        print(f"🔑 API Key for {service_name} found in Authorization header.")
        return api_key

    # 2. Try environment variable (e.g., OPENROUTER_API_KEY, GEMINI_API_KEY)
    env_var_name = f"{service_name.upper()}_API_KEY"
    api_key = os.environ.get(env_var_name)
    if api_key:
        print(f"🔑 API Key for {service_name} found in environment variable {env_var_name}.")
        return api_key

    # 3. Try general SUPAGROK_API_KEY environment variable as a fallback
    api_key = os.environ.get("SUPAGROK_API_KEY")
    if api_key:
        print(f"🔑 API Key for {service_name} found in environment variable SUPAGROK_API_KEY.")
        return api_key

    # 4. Try clipboard (Linux/xclip only)
    try:
        clipboard_content = subprocess.check_output(["xclip", "-selection", "clipboard", "-o"], text=True).strip()
        if clipboard_content and (clipboard_content.startswith("sk-") or "AIzaSy" in clipboard_content): # Basic sanity check
            print(f"🔑 API Key for {service_name} potentially found in clipboard. Using it.")
            return clipboard_content
    except FileNotFoundError:
        print("📋 xclip not found, skipping clipboard check for API key.")
    except subprocess.CalledProcessError:
        print("📋 Clipboard is empty or does not contain a key, skipping.")
    except Exception as e:
        print(f"📋 Error accessing clipboard: {e}")

    # 5. Prompt user if running in an interactive terminal
    if os.isatty(0): # Check if stdin is a TTY
        try:
            print(f"🔐 API Key for {service_name} not found in headers, environment, or clipboard.")
            api_key_input = input(f"Enter API Key for {service_name} (or press Enter to skip): ").strip()
            if api_key_input:
                return api_key_input
        except RuntimeError: # Happens if input() is called in a non-interactive context
            print(f"🚫 Cannot prompt for {service_name} API key in non-interactive mode.")
    else:
        print(f"🚫 Non-interactive mode: Cannot prompt for {service_name} API key.")
        
    print(f"⚠️ API Key for {service_name} not provided through any method.")
    return None