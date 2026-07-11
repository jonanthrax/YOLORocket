"""
Beacon Utilities — Shared module for session hooks.
=====================================================
Centralizes beacon reading, session ID extraction, timestamp generation,
and staleness detection. Used by write_first_reminder.py and insight_logger.py.

All functions are fail-safe: they return safe defaults on any exception.
No external dependencies beyond stdlib.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Lima/Bogota timezone (UTC-5)
TZ_LIMA = timezone(timedelta(hours=-5))

# Self-locating paths: derive project root from this file's location.
# This works regardless of CWD (fixes silent failure when Claude Code
# is launched from a parent directory).
_HOOKS_DIR = Path(__file__).resolve().parent        # .claude/hooks/
_PROJECT_ROOT = _HOOKS_DIR.parent.parent            # <your-project-root>/
SESSIONS_DIR = _PROJECT_ROOT / "docs" / "sessions" / "your-username"
COUNTER_DIR = _HOOKS_DIR


def get_timestamp():
    """Single-source OS timestamp with millisecond precision.

    Returns:
        tuple: (FECHA_FILE, FECHA_ISO, HORA, TS_FULL)
            - FECHA_FILE: "2026_03_15" (for filenames)
            - FECHA_ISO:  "2026-03-15" (for entries)
            - HORA:       "12:20:46.123" (for bitacora + beacon)
            - TS_FULL:    "2026-03-15T12:20:46.123" (for beacon JSON)
    """
    now = datetime.now(TZ_LIMA)
    ms = f"{now.microsecond // 1000:03d}"
    ts_full = now.strftime("%Y-%m-%dT%H:%M:%S.") + ms
    fecha_file = now.strftime("%Y_%m_%d")
    fecha_iso = now.strftime("%Y-%m-%d")
    hora = now.strftime("%H:%M:%S.") + ms
    return fecha_file, fecha_iso, hora, ts_full


def read_beacon():
    """Read and parse the newest RESTART_BEACON JSON.

    Returns:
        dict or None: Parsed beacon data, or None if no beacon / parse error.
    """
    try:
        beacons = sorted(SESSIONS_DIR.glob("RESTART_BEACON_S*.json"))
        if not beacons:
            return None
        return json.loads(beacons[-1].read_text(encoding="utf-8"))
    except Exception:
        return None


def get_session_id():
    """Extract session_id from the newest beacon.

    Returns:
        str: Session ID (e.g., "S20260315-1220") or "S?" if unavailable.
    """
    beacon = read_beacon()
    if beacon:
        return beacon.get("session_id", "S?")
    return "S?"


def beacon_age_hours(beacon):
    """Compute hours since beacon's last_updated timestamp.

    Args:
        beacon: dict with "last_updated" key in ISO format.

    Returns:
        float: Age in hours, or 9999.0 if unparseable.
    """
    try:
        last_updated = beacon.get("last_updated", "")
        # Handle both with and without milliseconds
        for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
            try:
                dt = datetime.strptime(last_updated, fmt)
                dt = dt.replace(tzinfo=TZ_LIMA)
                now = datetime.now(TZ_LIMA)
                delta = now - dt
                return delta.total_seconds() / 3600.0
            except ValueError:
                continue
        return 9999.0
    except Exception:
        return 9999.0


def parse_context_date(entry):
    """Extract the [YYYY-MM-DD] prefix from a context_decision string.

    Args:
        entry: str like "[2026-03-13] 3-tier: QUICK/STANDARD/DEEP"

    Returns:
        str or None: The date string "2026-03-13", or None if no prefix.
    """
    try:
        m = re.match(r"^\[(\d{4}-\d{2}-\d{2})\]\s", entry)
        return m.group(1) if m else None
    except Exception:
        return None


def truncate(text, max_len=60):
    """Truncate text to max_len chars, adding '...' if needed. ASCII-safe."""
    if not text:
        return ""
    # Strip any non-ASCII for hook output safety
    clean = text.encode("ascii", "replace").decode("ascii")
    if len(clean) <= max_len:
        return clean
    return clean[:max_len - 3] + "..."


def get_pnum(session_id):
    """Read current prompt counter value without incrementing.

    Returns 0 if file missing or unparseable. Used by hooks that need
    to know the current pnum but don't own the counter.
    """
    counter_file = COUNTER_DIR / f"prompt_counter_{session_id}.txt"
    try:
        return int(counter_file.read_text().strip())
    except Exception:
        return 0


def increment_pnum(session_id):
    """Atomically increment the prompt counter file and return new value.

    Single source of truth for pnum (R1 P3 2026-05-26). Consumed by
    write_first_reminder.py (owner: increments) and prompt_logger.py
    (consumer: reads via get_pnum). Uses temp file + os.replace for
    atomicity on Windows + POSIX. Falls back to direct write if temp+
    replace fails (cosmetic — race may produce off-by-one P# on next prompt).
    """
    counter_file = COUNTER_DIR / f"prompt_counter_{session_id}.txt"
    try:
        current = int(counter_file.read_text().strip())
    except Exception:
        current = 0
    new_val = current + 1
    tmp = counter_file.with_suffix(f".tmp.{os.getpid()}")
    try:
        tmp.write_text(str(new_val))
        os.replace(tmp, counter_file)
    except Exception:
        try:
            if tmp.exists():
                tmp.unlink()
        except Exception:
            pass
        try:
            counter_file.write_text(str(new_val))
        except Exception:
            pass
    return new_val
