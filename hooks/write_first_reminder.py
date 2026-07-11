"""
UserPromptSubmit Hook: Write-First Reminder
============================================
Injects context-aware reminder into Claude's context before every prompt.
Claude sees this as <user-prompt-submit-hook> (treated as user input).
The user does NOT see this output.

Provides:
  - Session ID (from active beacon)
  - Prompt counter with health indicator
  - Write-First trigger + entry format template
  - Progressive context injection (yellow/red zones)
  - Stale beacon warning (>36h)
"""

import sys
from pathlib import Path

# Import shared beacon utilities (fail-safe: fallback to inline if unavailable)
try:
    _hooks_dir = str(Path(__file__).parent)
    if _hooks_dir not in sys.path:
        sys.path.insert(0, _hooks_dir)
    from beacon_utils import (
        get_session_id, read_beacon, beacon_age_hours,
        get_timestamp, truncate, COUNTER_DIR, increment_pnum,
    )
except ImportError:
    # Fallback: minimal inline implementations (self-locating paths)
    import json
    from datetime import datetime, timezone, timedelta
    _HOOKS_DIR_FB = Path(__file__).resolve().parent
    _PROJECT_ROOT_FB = _HOOKS_DIR_FB.parent.parent
    COUNTER_DIR = _HOOKS_DIR_FB
    _TZ = timezone(timedelta(hours=-5))
    _SDIR = _PROJECT_ROOT_FB / "docs" / "sessions" / "your-username"
    def get_session_id():
        try:
            bs = sorted(_SDIR.glob("RESTART_BEACON_S*.json"))
            if not bs: return "S?"
            return json.loads(bs[-1].read_text(encoding="utf-8")).get("session_id", "S?")
        except Exception: return "S?"
    def read_beacon():
        try:
            bs = sorted(_SDIR.glob("RESTART_BEACON_S*.json"))
            if not bs: return None
            return json.loads(bs[-1].read_text(encoding="utf-8"))
        except Exception: return None
    def beacon_age_hours(b):
        return 0.0
    def get_timestamp():
        n = datetime.now(_TZ)
        ms = f"{n.microsecond // 1000:03d}"
        tf = n.strftime("%Y-%m-%dT%H:%M:%S.") + ms
        return n.strftime("%Y_%m_%d"), n.strftime("%Y-%m-%d"), n.strftime("%H:%M:%S.") + ms, tf
    def truncate(t, m=60):
        c = t.encode("ascii", "replace").decode("ascii")
        return c[:m-3] + "..." if len(c) > m else c
    def increment_pnum(sid):
        cf = COUNTER_DIR / f"prompt_counter_{sid}.txt"
        try:
            c = int(cf.read_text().strip()) + 1
        except Exception:
            c = 1
        cf.write_text(str(c))
        return c


def health_indicator(prompt_num):
    """Deprecated: restart-suggestion mechanism removed per user directive
    P45 2026-05-11. User owns restart timing exclusively. Returned value is
    kept empty so line-1 output drops the color/alert field entirely.
    """
    return ""


def main():
    try:
        # Read stdin (UserPromptSubmit sends JSON with user prompt)
        raw = sys.stdin.read()
        # We don't need the prompt content, just the event trigger

        # Read beacon once (used for session_id + progressive injection)
        beacon = read_beacon()
        session_id = beacon.get("session_id", "S?") if beacon else get_session_id()
        prompt_num = increment_pnum(session_id)
        health = health_indicator(prompt_num)

        _, fecha_iso, hora, _ = get_timestamp()

        # Check for post-compaction signal (from post_compact_signal.py)
        compaction_signal = COUNTER_DIR / "compaction_signal.json"
        post_compact = False
        if compaction_signal.exists():
            try:
                compaction_signal.unlink()  # Consume signal (one-shot)
                post_compact = True
            except Exception:
                pass

        # Line 1: Status bar (health field removed P45 2026-05-11 — user owns restart timing)
        # Use ASCII only (no em-dash) to avoid Windows cp1252 pipe corruption
        tag = "POST-COMPACTION BOOST" if post_compact else "Write-First ACTIVE"
        print(f"[{session_id} | P{prompt_num} | {tag}]")

        # Line 2: Write-First trigger
        print("If the response contains a relevant insight/output -> session log FIRST (Edit before SESSION_STATUS).")

        # Line 3: Entry format template
        print(f"Format: ### [{session_id}/CLAUDE] {fecha_iso} {hora} -- Title")

        # POST-COMPACTION BOOST: re-inject critical context after compaction
        if post_compact and beacon:
            print("POST-COMPACTION: Context was compacted. Write-First doctrine MUST be re-applied.")
            print("CRITICAL: Outputs/insights go to bitacora FIRST (Edit before SESSION_STATUS), chat shows only reference.")
            contexts = beacon.get("context_decisions", [])
            if contexts:
                ctx_parts = [truncate(c, 60) for c in contexts[:5]]
                print(f"CONTEXT (refreshed): {' | '.join(ctx_parts)}")
            pendings = beacon.get("pending_immediate", [])
            if pendings:
                pend_parts = [truncate(p, 60) for p in pendings[:3]]
                print(f"PENDINGS (refreshed): {' | '.join(pend_parts)}")

        # Progressive context injection based on health zone
        if beacon and prompt_num > 10:
            # Yellow zone (P11-P20): inject top-3 context decisions
            contexts = beacon.get("context_decisions", [])
            if contexts:
                ctx_parts = [truncate(c, 60) for c in contexts[:3]]
                print(f"CONTEXT: {' | '.join(ctx_parts)}")

            # Red zone (P20+): also inject top-2 pendings
            if prompt_num > 20:
                pendings = beacon.get("pending_immediate", [])
                if pendings:
                    pend_parts = [truncate(p, 60) for p in pendings[:2]]
                    print(f"PENDINGS: {' | '.join(pend_parts)}")

                # Stale beacon warning removed P45 2026-05-11 — user owns restart timing

    except Exception:
        # Fail-safe: never crash, never block. Empty stdout = no reminder.
        pass


if __name__ == "__main__":
    main()
