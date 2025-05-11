#!/usr/bin/env python3
# PRF-SUPAGROK-UTIL-COPYQ-CLIENT-2025-05-08
# UUID: b3c5d6e7-8f9a-0b1c-2d3e-4f5a6b7c8d9e
# Timestamp: 2025-05-08T17:10:00Z
# Description: Python client for interacting with CopyQ (Flatpak).

import os
import logging
from supagrok_repo.config import settings
from supagrok_repo.utils.command_runner import run_command

logger = logging.getLogger(__name__)

class CopyQClient:
    def __init__(self):
        self.flatpak_id = settings.COPYQ_FLATPAK_ID
        self._ensure_env()

    def _ensure_env(self):
        """Ensure necessary environment variables are set for Flatpak DBus interaction."""
        self.env = os.environ.copy()
        if "DBUS_SESSION_BUS_ADDRESS" not in self.env:
            user_id = os.geteuid()
            dbus_path = f"unix:path=/run/user/{user_id}/bus"
            if os.path.exists(dbus_path.split("=")[1]):
                self.env["DBUS_SESSION_BUS_ADDRESS"] = dbus_path
                logger.info(f"DBUS_SESSION_BUS_ADDRESS set to {dbus_path}")
            else:
                logger.warning(f"DBUS_SESSION_BUS_ADDRESS not found at {dbus_path} and not in env.")
        
        if "XDG_RUNTIME_DIR" not in self.env:
            user_id = os.geteuid()
            xdg_path = f"/run/user/{user_id}"
            if os.path.exists(xdg_path):
                self.env["XDG_RUNTIME_DIR"] = xdg_path
                logger.info(f"XDG_RUNTIME_DIR set to {xdg_path}")
            else:
                logger.warning(f"XDG_RUNTIME_DIR not found at {xdg_path} and not in env.")

    def _run_copyq_command(self, *args, check_server=True):
        if check_server:
            self.start_server() # Ensure server is running before most commands
        
        base_command = ["flatpak", "run", self.flatpak_id]
        full_command = base_command + list(args)
        stdout, stderr, rc = run_command(full_command, env=self.env)
        if rc != 0 and stderr and "Cannot connect to server" in stderr:
            logger.warning("CopyQ server connection error, attempting restart and retry.")
            self.start_server(force_restart=True) # Force restart if connection failed
            stdout, stderr, rc = run_command(full_command, env=self.env) # Retry
        return stdout, stderr, rc

    def start_server(self, force_restart=False):
        """Ensures the CopyQ server is running."""
        # Check if server is responsive first
        _, _, rc_eval = self._run_copyq_command("eval", "exit(0)", check_server=False)
        if rc_eval == 0 and not force_restart:
            logger.debug("CopyQ server already responsive.")
            return True

        logger.info("Starting CopyQ server...")
        # Use a non-blocking call for --start-server or it might hang
        # Forcing a new instance might be needed if pgrep is unreliable with flatpak
        run_command(["flatpak", "run", self.flatpak_id, "--start-server"], timeout=5, env=self.env)
        
        # Verify server started
        for _ in range(5): # Retry for 5 seconds
            _, _, rc_eval_check = self._run_copyq_command("eval", "exit(0)", check_server=False)
            if rc_eval_check == 0:
                logger.info("CopyQ server started successfully.")
                return True
            os.system("sleep 1") # Python's time.sleep
        logger.error("Failed to start or connect to CopyQ server after retries.")
        return False

    def add_item(self, content):
        """Adds an item to CopyQ."""
        stdout, stderr, rc = self._run_copyq_command("add", "--", content)
        if rc == 0:
            logger.debug(f"Added item to CopyQ (first 50 chars): {content[:50].replace('\n', ' ')}")
            return True
        logger.error(f"Failed to add item to CopyQ. RC: {rc}, Stderr: {stderr}")
        return False

    def get_size(self):
        """Gets the number of items in CopyQ."""
        stdout, stderr, rc = self._run_copyq_command("eval", "print(size())")
        if rc == 0 and stdout:
            try:
                return int(stdout.strip())
            except ValueError:
                logger.error(f"Could not parse CopyQ size from output: {stdout}")
        logger.error(f"Failed to get CopyQ size. RC: {rc}, Stderr: {stderr}")
        return None

    def list_items_formatted(self):
        """Lists all items in CopyQ, formatted similarly to copyq-list."""
        js_command = "var out = ''; for (var i = 0; i < size(); ++i) { var content = str(read(i)).replace(/\\n/g, '⏎'); out += i + ': ' + content + '\\n'; } print(out);"
        stdout, stderr, rc = self._run_copyq_command("eval", "--", js_command)
        if rc == 0:
            return stdout
        logger.error(f"Failed to list CopyQ items. RC: {rc}, Stderr: {stderr}")
        return None