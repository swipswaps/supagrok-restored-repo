#!/usr/bin/env python3
# PRF-SUPAGROK-RAGYOUTUBEUTILS-2025-05-10
# UUID: ytutil-b2c3d4e5-f6a7-8901-2345-67890abcde
# Timestamp: 2025-05-10T19:30:00Z
# Last Modified: 2025-05-10T19:30:00Z 
# Description: (supagrok_rag_system_v2_final/supagrok_youtube_ingest_utils.py) Utilities for fetching YouTube video information and subtitles using yt-dlp for RAG ingestion.
# Dependencies: Python packages: None directly, uses subprocess. System dependencies: yt-dlp
# Inputs: YouTube video URL, preferred language codes.
# Outputs: Dictionary containing video title, cleaned subtitle text, URL, and language code.
# Version: 1.2.0
# Author: SupagrokAgent/1.5
# PRF-Codex-Version: 1.7

import subprocess
import pathlib
import json
import logging
import tempfile
import re
import shutil 
import sys 
import os # For os.access
from typing import List, Optional as TypingOptional, Dict, Tuple, Any

logger = logging.getLogger(__name__)

YT_DLP_CMD_PATH_UTIL: str = "yt-dlp" # Default, can be overridden by check function

_yt_dlp_available_ytutil: TypingOptional[bool] = None

def check_yt_dlp_availability() -> bool:
    """Checks if yt-dlp is installed and available. Prefers venv, then system PATH. Caches result."""
    global _yt_dlp_available_ytutil
    global YT_DLP_CMD_PATH_UTIL # Allow modification of the global command path

    if _yt_dlp_available_ytutil is None:
        # Check in venv's bin directory first
        venv_bin_path = Path(sys.executable).parent
        yt_dlp_in_venv = venv_bin_path / "yt-dlp" # Default command name
        
        if yt_dlp_in_venv.is_file() and os.access(yt_dlp_in_venv, os.X_OK):
            logger.info(f"Using yt-dlp from virtual environment: {yt_dlp_in_venv}")
            YT_DLP_CMD_PATH_UTIL = str(yt_dlp_in_venv)
            _yt_dlp_available_ytutil = True
        else:
            # If not in venv, check system PATH
            system_yt_dlp_path = shutil.which("yt-dlp")
            if system_yt_dlp_path:
                logger.info(f"Using system-wide yt-dlp found at: {system_yt_dlp_path}")
                YT_DLP_CMD_PATH_UTIL = system_yt_dlp_path
                _yt_dlp_available_ytutil = True
            else:
                logger.error("'yt-dlp' command not found in venv or system PATH. Please ensure it's installed.")
                logger.error("Try: 'pip install yt-dlp' (in your venv) or install system-wide via your package manager.")
                _yt_dlp_available_ytutil = False
    return _yt_dlp_available_ytutil

def _run_yt_dlp_command(command_args: List[str]) -> Tuple[TypingOptional[str], TypingOptional[str], int]:
    """
    Runs a yt-dlp command using subprocess. Returns (stdout, stderr, return_code).
    Uses the globally determined YT_DLP_CMD_PATH_UTIL.
    """
    if not check_yt_dlp_availability():
        return None, f"'{YT_DLP_CMD_PATH_UTIL}' not available.", -1

    full_command = [YT_DLP_CMD_PATH_UTIL] + command_args
    logger.debug(f"Executing yt-dlp command: {' '.join(full_command)}")
    try:
        process = subprocess.run(
            full_command,
            capture_output=True,
            text=True,
            check=False, 
            timeout=180  # Increased timeout for potentially long operations
        )
        if process.returncode != 0:
            logger.warning(f"yt-dlp command failed with exit code {process.returncode}.")
            logger.warning(f"Command: {' '.join(full_command)}")
            stderr_output = process.stderr.strip() if process.stderr else 'No stderr'
            logger.warning(f"yt-dlp stderr: {stderr_output}")
        return process.stdout, process.stderr, process.returncode
    except FileNotFoundError: 
        logger.error(f"'{YT_DLP_CMD_PATH_UTIL}' command not found during execution attempt. This should have been caught by check_yt_dlp_availability.")
        return None, f"'{YT_DLP_CMD_PATH_UTIL}' not found.", -1
    except subprocess.TimeoutExpired:
        logger.error(f"yt-dlp command timed out: {' '.join(full_command)}")
        return None, "Command timed out.", -1
    except Exception as e:
        logger.error(f"An unexpected error occurred while running yt-dlp: {e}", exc_info=True)
        return None, str(e), -1

def get_video_info(video_url: str) -> TypingOptional[Dict[str, Any]]:
    """Fetches video metadata using yt-dlp. Returns parsed JSON dict or None."""
    logger.info(f"Fetching video info for: {video_url}")
    args = ["--dump-json", "--no-warnings", "--skip-download", video_url]
    stdout, _, rc = _run_yt_dlp_command(args)

    if rc != 0 or not stdout:
        logger.error(f"Failed to get video info for {video_url} (rc={rc}).")
        return None
    try:
        return json.loads(stdout)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from yt-dlp for {video_url}: {e}")
        logger.debug(f"Problematic yt-dlp stdout (first 500 chars): {stdout[:500]}...")
        return None

def _parse_vtt_content(vtt_content: str) -> str:
    """Basic parser for VTT content to extract plain text."""
    content_no_tags = re.sub(r'<[^>]+>', '', vtt_content) 
    lines = content_no_tags.splitlines()
    text_lines = []
    
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped or \
           line_stripped.upper() == "WEBVTT" or \
           "-->" in line_stripped or \
           re.fullmatch(r'\d+', line_stripped) or \
           line_stripped.startswith("Kind:") or \
           line_stripped.startswith("Language:"):
            continue
        text_lines.append(line_stripped)
        
    if not text_lines: return ""
        
    deduplicated_text_lines = [text_lines[0]]
    for i in range(1, len(text_lines)):
        if text_lines[i] != text_lines[i-1]:
            deduplicated_text_lines.append(text_lines[i])
            
    return "\n".join(deduplicated_text_lines)

def fetch_youtube_subtitle_text(video_url: str, preferred_langs: List[str]) -> TypingOptional[Dict[str, str]]:
    """Fetches and parses subtitles. Returns dict with title, text, URL, language, or None."""
    if not check_yt_dlp_availability(): return None

    video_info = get_video_info(video_url)
    if not video_info: return None

    video_title = video_info.get("title", "Unknown Title")
    logger.info(f"Processing video: {video_title}")

    sub_options = [] 
    # yt-dlp's --list-subs output format can vary. --dump-json is more reliable.
    # 'subtitles' for manual, 'automatic_captions' for auto. Both are dicts of lang_code -> list of formats.
    for lang_code_key, subs_list_formats in video_info.get("subtitles", {}).items():
        for sub_entry_format in subs_list_formats: 
            if sub_entry_format.get('ext') == 'vtt': 
                sub_options.append((lang_code_key, "--write-sub", sub_entry_format)) # lang_code_key is like 'en', 'es'
    for lang_code_key, subs_list_formats in video_info.get("automatic_captions", {}).items():
        for sub_entry_format in subs_list_formats:
            if sub_entry_format.get('ext') == 'vtt':
                sub_options.append((lang_code_key, "--write-auto-sub", sub_entry_format))
    
    selected_option_tuple = None # (actual_lang_code, sub_type_flag_str)
    # Try preferred languages for manual subtitles first
    for pref_lang_code in preferred_langs:
        for actual_lang_code, sub_type_flag, sub_info_dict in sub_options:
            if actual_lang_code.startswith(pref_lang_code) and sub_type_flag == "--write-sub":
                selected_option_tuple = (actual_lang_code, sub_type_flag)
                break
        if selected_option_tuple: break
    
    # If no manual sub found in preferred_langs, try for auto-generated ones in preferred_langs
    if not selected_option_tuple:
        for pref_lang_code in preferred_langs:
            for actual_lang_code, sub_type_flag, sub_info_dict in sub_options:
                if actual_lang_code.startswith(pref_lang_code) and sub_type_flag == "--write-auto-sub":
                    selected_option_tuple = (actual_lang_code, sub_type_flag)
                    break
            if selected_option_tuple: break
    
    # Fallback: if still no preferred lang, take the first available English manual, then any English auto
    if not selected_option_tuple:
        for actual_lang_code, sub_type_flag, sub_info_dict in sub_options: # Check all manual subs
            if actual_lang_code.startswith('en') and sub_type_flag == "--write-sub":
                selected_option_tuple = (actual_lang_code, sub_type_flag)
                break
    if not selected_option_tuple:
        for actual_lang_code, sub_type_flag, sub_info_dict in sub_options: # Check all auto subs
             if actual_lang_code.startswith('en') and sub_type_flag == "--write-auto-sub":
                selected_option_tuple = (actual_lang_code, sub_type_flag)
                break

    if not selected_option_tuple:
        logger.warning(f"No suitable VTT subtitles found for {video_url} (tried preferred: {preferred_langs}). Available options: {sub_options}")
        return None
    
    final_selected_lang_code, final_selected_sub_type_flag = selected_option_tuple
    logger.info(f"Selected subtitle: lang='{final_selected_lang_code}', type='{final_selected_sub_type_flag.replace('--write-', '')}' for {video_url}")

    with tempfile.TemporaryDirectory(prefix="supagrok_subs_") as tmpdir:
        temp_dir_path = pathlib.Path(tmpdir)
        # Use a generic name, yt-dlp will add extension and lang.
        temp_sub_file_output_template = temp_dir_path / "subtitle_download.%(ext)s"
        
        # Command construction
        # Use --sub-langs with the *exact* language code yt-dlp reported (final_selected_lang_code)
        cmd_dl = [
            final_selected_sub_type_flag, # --write-sub or --write-auto-sub
            "--skip-download",
            "--sub-format", "vtt", 
            "--sub-langs", final_selected_lang_code, 
            "-o", str(temp_sub_file_output_template), 
            video_url
        ]
        
        _, _, rc_dl = _run_yt_dlp_command(cmd_dl)
        if rc_dl != 0:
            logger.error(f"yt-dlp failed to download subtitles for {video_url} (lang: {final_selected_lang_code}).")
            return None

        # Find the downloaded .vtt file. yt-dlp usually names it like <output_template_name>.<lang_code>.vtt
        # e.g., subtitle_download.en.vtt
        # A more robust way is to list .vtt files in tmpdir as yt-dlp naming can be tricky.
        downloaded_vtt_files = list(temp_dir_path.glob("*.vtt"))
        
        if not downloaded_vtt_files:
            logger.error(f"Subtitle file (.vtt) not found in temp directory {tmpdir} after yt-dlp call for lang {final_selected_lang_code}.")
            return None
        
        # Assuming the first .vtt file found is the one we want.
        actual_downloaded_sub_file = downloaded_vtt_files[0]
        logger.info(f"Found downloaded subtitle file: {actual_downloaded_sub_file}")

        try:
            vtt_content = actual_downloaded_sub_file.read_text(encoding='utf-8')
            cleaned_text = _parse_vtt_content(vtt_content)
            if not cleaned_text.strip():
                logger.warning(f"Subtitles for {video_url} (lang: {final_selected_lang_code}) were empty after parsing.")
            
            return {
                "title": video_title,
                "text": cleaned_text,
                "url": video_url,
                "language": final_selected_lang_code # The language code yt-dlp used
            }
        except Exception as e:
            logger.error(f"Failed to read or parse subtitle file {actual_downloaded_sub_file}: {e}", exc_info=True)
            return None

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG) # Use DEBUG for testing this module
    
    if not check_yt_dlp_availability():
        sys.exit("FATAL: yt-dlp is not available. Cannot run Supagrok YouTube Ingest Utilities tests.")
        
    # Test with the RAG strategy video
    test_video_url_rag_strategy = "https://www.youtube.com/watch?v=z_LGan-t2Mo" 
    # Test with LlamaIndex intro video
    test_video_url_llindex_intro = "https://www.youtube.com/watch?v=pNcQ5xxNl3E" 
    
    preferred_langs_for_test = ['en', 'en-US', 'en-GB'] 
    try:
        # Attempt to load from config if available, otherwise use default
        from supagrok_rag_config import get_youtube_preferred_subtitle_langs
        preferred_langs_for_test = get_youtube_preferred_subtitle_langs()
        logger.info(f"Using preferred languages from config: {preferred_langs_for_test}")
    except ImportError:
        logger.info(f"supagrok_rag_config not available for test, using default preferred_langs: {preferred_langs_for_test}")

    videos_to_test = [test_video_url_rag_strategy, test_video_url_llindex_intro]
    for current_test_url in videos_to_test:
        logger.info(f"\n--- Testing subtitle fetching for: {current_test_url} ---")
        subtitle_data_result = fetch_youtube_subtitle_text(current_test_url, preferred_langs_for_test)
        if subtitle_data_result:
            logger.info(f"Successfully fetched subtitles for video titled: '{subtitle_data_result['title']}'")
            logger.info(f"Language code used: {subtitle_data_result['language']}")
            logger.info(f"Subtitle Text (first 200 chars):\n{subtitle_data_result['text'][:200].strip()}...")
        else:
            logger.error(f"Failed to fetch subtitles for {current_test_url}")
    logger.info("\nSupagrok YouTube Ingest Utilities self-test finished.")
