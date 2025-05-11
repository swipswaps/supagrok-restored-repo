#!/usr/bin/env python3
# PRF-SUPAGROK-RAGCONFIG-2025-05-10
# UUID: cfg-a1b2c3d4-e5f6-7890-1234-567890abcdef
# Timestamp: 2025-05-10T19:30:00Z
# Last Modified: 2025-05-10T20:00:00Z 
# Description: (supagrok_rag_system_v2_final/supagrok_rag_config.py) Configuration settings for the Supagrok RAG system. Handles API keys, storage paths, and other system parameters.
# Dependencies: python-dotenv, os, pathlib, typing
# Inputs: .env file in CWD or parent directories (expected to contain OPENAI_API_KEY)
# Outputs: Configuration variables (API key, storage path, preferred languages)
# Version: 1.3.1
# Author: SupagrokAgent/1.5
# PRF-Codex-Version: 1.7

import os
from pathlib import Path
from dotenv import load_dotenv
import logging
from typing import List, Optional as TypingOptional 

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def find_dotenv_config() -> TypingOptional[Path]:
    """Searches for .env file in current and parent directories up to two levels."""
    cwd = Path.cwd()
    paths_to_check = [
        cwd / ".env",
        cwd.parent / ".env",
        cwd.parent.parent / ".env" 
    ]
    for env_path_candidate in paths_to_check:
        if env_path_candidate.is_file(): 
            return env_path_candidate
    return None

env_path_found_config = find_dotenv_config()

if env_path_found_config:
    logger.info(f"Loading .env file from: {env_path_found_config}")
    load_dotenv(dotenv_path=env_path_found_config)
else:
    logger.warning(".env file not found in CWD or parent directories (up to 2 levels). Relying on environment variables.")
    load_dotenv() 


OPENAI_API_KEY_CONFIG: TypingOptional[str] = os.getenv("OPENAI_API_KEY")

STORAGE_DIR_NAME_CONFIG: str = "supagrok_rag_storage_v2_final" 
STORAGE_DIR_CONFIG_PATH: Path = Path.cwd() / STORAGE_DIR_NAME_CONFIG

YOUTUBE_PREFERRED_SUBTITLE_LANGS_CONFIG: List[str] = ['en', 'en-US', 'en-GB', 'en-AU', 'en-CA']


def ensure_openai_api_key() -> None:
    """Checks for OpenAI API key and raises ValueError if not found."""
    if not OPENAI_API_KEY_CONFIG:
        msg = "OPENAI_API_KEY not found. Please set it in your .env file or environment."
        logger.error(msg)
        raise ValueError(msg)
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY_CONFIG 
    logger.info("OpenAI API key loaded and verified from configuration.")

def get_storage_path() -> Path:
    """Returns the path to the storage directory, creating it if it doesn't exist."""
    STORAGE_DIR_CONFIG_PATH.mkdir(parents=True, exist_ok=True)
    return STORAGE_DIR_CONFIG_PATH

def get_youtube_preferred_subtitle_langs() -> List[str]:
    """Returns the list of preferred YouTube subtitle languages."""
    return YOUTUBE_PREFERRED_SUBTITLE_LANGS_CONFIG

if __name__ == "__main__":
    logger.info("Configuration module self-test:")
    try:
        ensure_openai_api_key()
        logger.info("OpenAI API Key check passed (key presence verified).")
    except ValueError as e:
        logger.error(f"Configuration Self-Test Error: {e}")
    
    storage_location = get_storage_path()
    logger.info(f"Default vector store location: {storage_location}")
    logger.info(f"Preferred YouTube subtitle languages: {get_youtube_preferred_subtitle_langs()}")
    logger.info("Configuration module self-test finished.")
