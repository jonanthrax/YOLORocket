"""
PostCompact Hook: Compaction Signal
====================================
Fires after context compaction completes. Writes a signal file that
write_first_reminder.py detects on the next UserPromptSubmit to inject
a POST-COMPACTION BOOST (stronger Write-First reminder + context refresh).

PostCompact cannot inject additionalContext — it's observability-only.
The signal file bridges PostCompact -> UserPromptSubmit for context re-injection.

Receives JSON on stdin:
  {
    "session_id": "...",
    "transcript_path": "...",
    "cwd": "...",
    "hook_event_name": "PostCompact",
    "trigger": "manual" | "auto",
    "compact_summary": "..."
  }
"""

import json
import sys
import io
from pathlib import Path

# Force UTF-8 stdin on Windows
if hasattr(sys.stdin, 'buffer'):
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8', errors='replace')

# Signal file location (self-locating, consumed by write_first_reminder.py)
SIGNAL_FILE = Path(__file__).resolve().parent / "compaction_signal.json"


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return

        data = json.loads(raw)

        # Write signal file for write_first_reminder.py to consume
        signal = {
            "event": "PostCompact",
            "trigger": data.get("trigger", "unknown"),
            "session_id": data.get("session_id", ""),
            "timestamp": __import__("datetime").datetime.now().isoformat(),
        }

        SIGNAL_FILE.write_text(
            json.dumps(signal, indent=2),
            encoding="utf-8"
        )

    except Exception:
        # Fire-and-forget: never crash, never block
        pass


if __name__ == "__main__":
    main()
