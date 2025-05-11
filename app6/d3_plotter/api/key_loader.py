# Loads API key from headers or env
import os

def load_api_key(request):
    key = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    return key or os.getenv("SUPAGROK_API_KEY")
