#!/usr/bin/env python3
# PRF-SUPAGROK-AGENT-CLIPBOARD-INGESTION-2025-05-08
# UUID: c4d6e7f8-9a0b-1c2d-3e4f-5a6b7c8d9e0f
# Timestamp: 2025-05-08T17:15:00Z
# Description: Supagrok agent to monitor clipboard, deduplicate, and ingest into CopyQ.

import time
import hashlib
import logging
import os
import subprocess
from collections import deque

from supagrok_repo.config import settings
from supagrok_repo.utils.copyq_client import CopyQClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ClipboardIngestionAgent:
    def __init__(self):
        self.copyq_client = CopyQClient()
        self.dedup_hashes = deque(maxlen=settings.MAX_DEDUP_CACHE_SIZE)
        self.poll_interval = settings.POLL_INTERVAL_SECONDS

        settings.LOG_DIR.mkdir(parents=True, exist_ok=True)
        self.audit_log_file = settings.CLIPBOARD_AUDIT_LOG_FILE
        self.rejects_log_file = settings.CLIPBOARD_REJECTS_LOG_FILE

        self._log_to_file(self.audit_log_file, f"📋 Supagrok Clipboard Ingestion Agent started @ {time.strftime('%Y-%m-%d %H:%M:%S')}\n", mode="a")
        self._log_to_file(self.rejects_log_file, f"📛 Supagrok Clipboard Rejects Log started @ {time.strftime('%Y-%m-%d %H:%M:%S')}\n", mode="a")

    def _log_to_file(self, filepath, message, mode="a"):
        try:
            with open(filepath, mode, encoding="utf-8") as f:
                f.write(message + "\n")
        except Exception as e:
            logger.error(f"Failed to write to log file {filepath}: {e}")

    def get_clipboard_content(self):
        """Gets current clipboard content using xclip."""
        try:
            process = subprocess.run(settings.XCLIP_CMD, capture_output=True, text=True, check=True, timeout=2)
            return process.stdout
        except subprocess.CalledProcessError as e:
            # Often means clipboard is empty or xclip had an issue (e.g. no X server if run headless)
            if e.returncode == 1 and not e.stdout and not e.stderr: # Common for empty clipboard
                return ""
            logger.warning(f"xclip command failed with rc {e.returncode}: {e.stderr}")
        except subprocess.TimeoutExpired:
            logger.warning("xclip command timed out.")
        except FileNotFoundError:
            logger.error("xclip command not found. Please ensure it is installed.")
            # This is a fatal error for this agent's current strategy
            raise
        return None

    def run(self):
        logger.info("Starting clipboard monitoring loop...")
        if not self.copyq_client.start_server():
            logger.error("Failed to start CopyQ server. Agent cannot run.")
            return

        while True:
            try:
                clipboard_content = self.get_clipboard_content()

                if clipboard_content is None: # Error getting content
                    time.sleep(self.poll_interval * 2) # Longer sleep on error
                    continue
                
                if not clipboard_content: # Empty clipboard
                    time.sleep(self.poll_interval)
                    continue

                content_hash = hashlib.sha256(clipboard_content.encode('utf-8')).hexdigest()

                if content_hash in self.dedup_hashes:
                    logger.debug(f"Skipping duplicate clipboard item (hash: {content_hash[:8]}...).")
                    time.sleep(self.poll_interval)
                    continue

                logger.info(f"New unique clipboard item detected (hash: {content_hash[:8]}...).")
                
                if self.copyq_client.add_item(clipboard_content):
                    self.dedup_hashes.append(content_hash)
                    log_message = f"✅ [{time.strftime('%Y-%m-%d %H:%M:%S')}] Imported to CopyQ (hash: {content_hash}): {clipboard_content[:100].replace('\n', '⏎')}..."
                    self._log_to_file(self.audit_log_file, log_message)
                    logger.info(f"Successfully added item to CopyQ (hash: {content_hash[:8]}...).")
                else:
                    log_message = f"❌ [{time.strftime('%Y-%m-%d %H:%M:%S')}] Failed to import to CopyQ (hash: {content_hash}): {clipboard_content[:100].replace('\n', '⏎')}..."
                    self._log_to_file(self.rejects_log_file, log_message)
                    logger.error(f"Failed to add item to CopyQ (hash: {content_hash[:8]}...).")

                time.sleep(self.poll_interval)

            except KeyboardInterrupt:
                logger.info("Clipboard ingestion agent stopped by user.")
                break
            except Exception as e:
                logger.exception(f"An unexpected error occurred in the monitoring loop: {e}")
                time.sleep(self.poll_interval * 5) # Longer sleep on unexpected error

if __name__ == "__main__":
    agent = ClipboardIngestionAgent()
    agent.run()