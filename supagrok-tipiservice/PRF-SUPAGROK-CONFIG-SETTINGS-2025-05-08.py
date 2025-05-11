#!/usr/bin/env python3
# PRF-SUPAGROK-CONFIG-SETTINGS-2025-05-08
# UUID: f1d8c3b0-1e2a-4b3c-8d4e-5f6a7b8c9d0a
# Timestamp: 2025-05-08T17:00:00Z
# Description: Configuration settings for Supagrok clipboard integration.

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

COPYQ_FLATPAK_ID = "com.github.hluk.copyq"

LOG_DIR = BASE_DIR / "logs"
CLIPBOARD_AUDIT_LOG_FILE = LOG_DIR / "clipboard_audit.md"
CLIPBOARD_REJECTS_LOG_FILE = LOG_DIR / "clipboard_rejects.log"

MAX_DEDUP_CACHE_SIZE = 20000  # Number of recent hashes to keep for deduplication
POLL_INTERVAL_SECONDS = 1    # How often to check the clipboard

XCLIP_CMD = ["xclip", "-selection", "clipboard", "-o"]