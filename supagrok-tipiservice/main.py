# PRF-SUPAGROK-V3-MAIN-APP-R1
# UUID: ma-01234567-89ab-cdef-0123-456789abcdef-r1
# Version: 1.1
# Description: Main FastAPI application for Supagrok V3. Includes /v3 API prefix.
# Full Path: /home/owner/Documents/scripts/AICode/680fddc4-f7f8-8008-a24f-ccde790499ca/app/supagrok_restored_repo/supagrok-tipiservice/main.py
# Changelog:
#   V1.1: Added /health endpoint.
#   V1.0: Initial version with /v3 prefix for mux_router.

from fastapi import FastAPI
import uvicorn

# Assuming mux_router.py is in supagrok/routers/
# and your current directory (where main.py is) is the project root for supagrok-tipiservice
from supagrok.routers import mux_router

app = FastAPI(
    title="Supagrok V3 API",
    description="API for interacting with multiple LLMs via Supagrok, with Gemini/OpenRouter fallback.",
    version="3.0.0"
)

app.include_router(mux_router.router, prefix="/v3")

@app.get("/", summary="Root Endpoint", description="Provides a welcome message for the Supagrok V3 API.")
async def read_root():
    return {"message": "Welcome to Supagrok V3! API endpoints are under /v3/"}

@app.get("/health", summary="Health Check", description="Returns the operational status of the API.")
async def health_check():
    return {"status": "healthy", "version": app.version}

if __name__ == "__main__":
    # This is primarily for local development.
    # For production, use a process manager like Gunicorn or Uvicorn directly.
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)