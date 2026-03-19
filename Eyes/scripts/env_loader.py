#!/usr/bin/env python3
"""
Lightweight .env loader for YMOS scripts.

No third-party dependencies. Reads key=value pairs from a .env file
and sets them as environment variables (without overriding existing ones).

Usage:
    from env_loader import load_dotenv
    load_dotenv()  # auto-finds YMOS/.env
"""

import os
from pathlib import Path


def load_dotenv(env_path=None):
    """Load environment variables from a .env file.

    Args:
        env_path: Path to .env file. If None, auto-detects YMOS/.env
                  by walking up from this script's location.

    Rules:
        - Skips blank lines and comments (lines starting with #)
        - Does NOT override variables already set in os.environ
        - Strips whitespace from keys and values
        - Supports KEY=VALUE format (no quoting logic needed for YMOS use case)
    """
    if env_path is None:
        # Eyes/scripts/ -> Eyes/ -> YMOS/
        env_path = Path(__file__).resolve().parents[2] / ".env"
    else:
        env_path = Path(env_path)

    if not env_path.exists():
        return

    loaded = []
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if key and key not in os.environ:
            os.environ[key] = value
            loaded.append(key)

    if loaded:
        # Quiet by default; only prints when something was actually loaded
        pass
