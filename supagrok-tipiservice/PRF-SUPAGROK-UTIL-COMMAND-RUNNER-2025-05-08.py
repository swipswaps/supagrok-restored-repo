#!/usr/bin/env python3
# PRF-SUPAGROK-UTIL-COMMAND-RUNNER-2025-05-08
# UUID: a2b4c5d6-7e8f-9a0b-1c2d-3e4f5a6b7c8d
# Timestamp: 2025-05-08T17:05:00Z
# Description: Utility for running shell commands and capturing output.

import subprocess
import logging

logger = logging.getLogger(__name__)

def run_command(command_parts, timeout=10, check=False, env=None):
    """
    Runs a shell command and returns its output.
    Args:
        command_parts (list): The command and its arguments as a list.
        timeout (int): Timeout in seconds.
        check (bool): If True, raise CalledProcessError on non-zero exit.
        env (dict, optional): Environment variables for the subprocess.
    Returns:
        tuple: (stdout, stderr, returncode)
    """
    try:
        process = subprocess.run(
            command_parts,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=check,
            env=env
        )
        return process.stdout, process.stderr, process.returncode
    except subprocess.CalledProcessError as e:
        logger.error(f"Command '{' '.join(command_parts)}' failed with exit code {e.returncode}: {e.stderr}")
        if check:
            raise
        return e.stdout, e.stderr, e.returncode
    except subprocess.TimeoutExpired:
        logger.error(f"Command '{' '.join(command_parts)}' timed out after {timeout} seconds.")
        return None, "TimeoutExpired", -1 # Using -1 as a custom timeout indicator for returncode
    except FileNotFoundError:
        logger.error(f"Command not found: {command_parts[0]}")
        return None, "FileNotFound", -2 # Custom indicator