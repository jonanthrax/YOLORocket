"""
UserPromptSubmit Hook: Prompt Logger
=====================================
Captures user prompts to a per-session JSONL file for voice-style analysis
and historical record. Produces NO stdout (invisible to Claude).

Output: .claude/hooks/prompt_log_{SID}.jsonl
Format: {"ts":"...","sid":"...","pnum":N,"prompt":"..."}
Lifecycle: Created on first prompt, exported to .md at /end-session, then deleted.
"""

import io
import json
import sys
from pathlib import Path

# Force UTF-8 stdin on Windows (prevents CP1252 mojibake)
if hasattr(sys.stdin, 'buffer'):
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8', errors='replace')

# Import shared beacon utilities (fail-safe: fallback to inline if unavailable)
try:
    _hooks_dir = str(Path(__file__).parent)
    if _hooks_dir not in sys.path:
        sys.path.insert(0, _hooks_dir)
    from beacon_utils import get_session_id, get_timestamp, get_pnum, COUNTER_DIR
except ImportError:
    from datetime import datetime, timezone, timedelta
    _HOOKS_DIR_FB = Path(__file__).resolve().parent
    _PROJECT_ROOT_FB = _HOOKS_DIR_FB.parent.parent
    COUNTER_DIR = _HOOKS_DIR_FB
    _TZ = timezone(timedelta(hours=-5))
    _SDIR_FB = _PROJECT_ROOT_FB / "docs" / "sessions" / "your-username"
    def get_session_id():
        try:
            bs = sorted(_SDIR_FB.glob("RESTART_BEACON_S*.json"))
            if not bs: return "S_"
            return json.loads(bs[-1].read_text(encoding="utf-8")).get("session_id", "S_")
        except Exception: return "S_"
    def get_timestamp():
        n = datetime.now(_TZ)
        ms = f"{n.microsecond // 1000:03d}"
        tf = n.strftime("%Y-%m-%dT%H:%M:%S.") + ms
        return n.strftime("%Y_%m_%d"), n.strftime("%Y-%m-%d"), n.strftime("%H:%M:%S.") + ms, tf
    def get_pnum(sid):
        cf = COUNTER_DIR / f"prompt_counter_{sid}.txt"
        try:
            return int(cf.read_text().strip())
        except Exception:
            return 0


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return

        data = json.loads(raw)
        prompt = data.get("prompt", "").strip()
        if not prompt:
            return

        sid = get_session_id()
        _, _, hora, ts_full = get_timestamp()

        # R1 fix v2 (P13 2026-05-26): use max(counter, line_count+1) to be robust
        # against parallel hook execution order. If write_first_reminder has not yet
        # committed its counter increment, get_pnum returns the OLD value. The line-
        # count derivation always reflects "this entry's natural position". Taking
        # the max guarantees forward progress regardless of hook race.
        log_file = COUNTER_DIR / f"prompt_log_{sid}.jsonl"
        counter_pnum = get_pnum(sid)
        try:
            existing = log_file.read_text(encoding="utf-8").strip().split("\n")
            line_pnum = len([l for l in existing if l.strip()]) + 1
        except Exception:
            line_pnum = 1
        pnum = max(counter_pnum, line_pnum)

        entry = json.dumps(
            {"ts": ts_full, "sid": sid, "pnum": pnum, "prompt": prompt},
            ensure_ascii=False,
        )
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(entry + "\n")

        # NO stdout — this hook is invisible to Claude

    except Exception:
        # Fail-safe: never crash, never block. Silent failure.
        pass


if __name__ == "__main__":
    main()
