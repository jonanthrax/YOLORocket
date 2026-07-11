"""
Stop Hook: Insight Logger
=========================
Async post-response hook that evaluates Claude's last response for loggable
insights/outputs and appends them to the active INTERACTIVE SESSION bitacora.

Receives JSON on stdin from Claude Code Stop event:
  {
    "session_id": "...",
    "last_assistant_message": "...",
    "transcript_path": "...",
    "stop_hook_active": true/false,
    "cwd": "..."
  }

Runs async (fire-and-forget) — zero latency for the user.
"""

import json
import os
import sys
import io
import re
from datetime import datetime, timezone, timedelta

# Force UTF-8 stdin on Windows (prevents CP1252 mojibake)
if hasattr(sys.stdin, 'buffer'):
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8', errors='replace')
from pathlib import Path

# Import shared beacon utilities (fail-safe: fallback to inline if unavailable)
try:
    _hooks_dir = str(Path(__file__).parent)
    if _hooks_dir not in sys.path:
        sys.path.insert(0, _hooks_dir)
    from beacon_utils import get_session_id, get_timestamp, TZ_LIMA
    _HAS_BEACON_UTILS = True
except ImportError:
    _HAS_BEACON_UTILS = False
    # Fallback: inline constants
    TZ_LIMA = timezone(timedelta(hours=-5))

# Keywords that signal a loggable insight in Claude's response
INSIGHT_KEYWORDS = [
    # Explicit insight markers (Spanish + English)
    "**Tipo:** Decision",
    "**Tipo:** Hallazgo",
    "**Tipo:** Bug",
    "**Tipo:** Patron",
    "**Tipo:** Cambio-de-Estado",
    "**Tipo:** Doctrina",
    "**Tipo:** Output",
    # Structural markers
    "[Depth: DEEP]",
    "## Proposal",
    "## Analysis",
    "#### HALLAZGO",
    "#### IMPLEMENTATION PLAN",
    # Decision language
    "CONFIRMO",
    "DESCONFIRMO",
    "Doctrina Write-First",
    # High-precision completion phrases
    "sweep complete",
    "implementation complete",
    "migration complete",
    "all edits applied",
]

# Structural heuristic: detect significant-work responses
# Matches file paths like DEVELOPMENT_GUIDE.md, insight_logger.py, etc.
_FILE_PATH_PATTERN = re.compile(r'[\w./\\-]+\.(?:py|md|json|yaml|toml|txt)\b')

# Action verbs indicating work was DONE (not planned)
_ACTION_WORDS = frozenset({
    "updated", "modified", "created", "applied", "edited", "fixed",
    "implemented", "completed", "deleted", "removed", "added",
    "actualizado", "modificado", "creado", "aplicado", "editado",
    "corregido", "implementado", "completado", "eliminado", "agregado",
})

# Keywords that signal this is NOT worth logging
SKIP_KEYWORDS = [
    "Full output: bitacora",       # Already written via Write-First
    "ver bitácora",                 # Reference to existing entry
    "Full output: bitácora",       # Already written via Write-First
]

# Minimum response length to even consider (short responses = not insights)
MIN_RESPONSE_LENGTH = 200


def get_bitacora_path(cwd: str) -> Path | None:
    """Find today's active INTERACTIVE SESSION bitacora.

    Uses SESSIONS_DIR from beacon_utils (self-locating) as primary.
    Falls back to cwd-based path if beacon_utils is unavailable.
    """
    if _HAS_BEACON_UTILS:
        today, _, _, _ = get_timestamp()
        from beacon_utils import SESSIONS_DIR as _sd
        bitacora = _sd / f"{today}_INTERACTIVE_BITACORE_SESSION.md"
        if bitacora.exists():
            return bitacora
    # Fallback: try cwd-based path
    today_fb = datetime.now(TZ_LIMA).strftime("%Y_%m_%d")
    sessions_dir = Path(cwd) / "docs" / "sessions" / "your-username"
    bitacora = sessions_dir / f"{today_fb}_INTERACTIVE_BITACORE_SESSION.md"
    if bitacora.exists():
        return bitacora
    return None


def has_significant_work(message: str) -> bool:
    """Detect responses describing significant file modifications.

    Triggers when 2+ unique file paths AND 2+ action verbs are present.
    This catches work-summary responses that lack explicit insight markers.
    """
    files = set(_FILE_PATH_PATTERN.findall(message))
    if len(files) < 2:
        return False
    msg_lower = message.lower()
    action_count = sum(1 for w in _ACTION_WORDS if w in msg_lower)
    return action_count >= 2


def should_log(message: str) -> bool:
    """Heuristic: does this response contain a loggable insight?"""
    if len(message) < MIN_RESPONSE_LENGTH:
        return False

    # Skip if already written via Write-First
    for skip in SKIP_KEYWORDS:
        if skip in message:
            return False

    # Layer A: Explicit insight keywords
    for keyword in INSIGHT_KEYWORDS:
        if keyword in message:
            return True

    # Layer B: Significant-work heuristic (structural detection)
    if has_significant_work(message):
        return True

    return False


def extract_title(message: str) -> str:
    """Extract a title from the response for the bitacora entry."""
    SKIP_HEADERS = {
        "Scope", "Analysis", "Proposal", "Risks",
        "Resumen", "Summary", "Output format:",
    }

    # Look for markdown headers (skip generic ones)
    headers = re.findall(r'^#{1,4}\s+(.+)$', message, re.MULTILINE)
    for h in headers:
        clean = h.strip().rstrip(':')
        if clean not in SKIP_HEADERS and len(clean) > 5:
            return clean[:80]

    # Look for **Tipo:** line to identify the insight type
    tipo = re.search(r'\*\*Tipo:\*\*\s*(.+)', message)
    if tipo:
        return tipo.group(1).strip()[:80]

    # Look for **bold** opening (skip Tipo/Contexto/etc)
    bold = re.findall(r'\*\*(.+?)\*\*', message)
    for b in bold:
        if b not in ("Tipo:", "Contexto:", "Insight:", "Impacto:", "Nota:"):
            return b[:80]

    # Fallback: first substantive line
    for line in message.split('\n'):
        line = line.strip()
        if line and not line.startswith('[') and not line.startswith('#') and len(line) > 10:
            return line[:80]

    return "Insight detectado por Stop hook"


if not _HAS_BEACON_UTILS:
    def get_session_id() -> str:
        """Fallback: Read active beacon to get session ID."""
        _fb_hooks = Path(__file__).resolve().parent
        _fb_root = _fb_hooks.parent.parent
        sessions_dir = _fb_root / "docs" / "sessions" / "your-username"
        beacons = sorted(sessions_dir.glob("RESTART_BEACON_S*.json"))
        if not beacons:
            return "S?"
        try:
            data = json.loads(beacons[-1].read_text(encoding="utf-8"))
            return data.get("session_id", "S?")
        except Exception:
            return "S?"


def sanitize_encoding(text: str) -> str:
    """Fix common UTF-8 mojibake from Windows cp1252 pipe corruption.

    When Claude's response passes through stdin on Windows, multi-byte
    UTF-8 characters (em-dash, curly quotes, accented chars) sometimes get
    re-interpreted as cp1252, producing mojibake sequences like
    'Ã¡' instead of 'á', or 'â€"' instead of '—'.

    Strategy: re-encode as cp1252 bytes, then decode as UTF-8.
    Must use cp1252 (NOT latin-1) because cp1252 has characters in the
    0x80-0x9F range (€, ", ", —) that latin-1 does not, and these are
    the exact characters that appear in mojibake from em-dash, smart
    quotes, and other multi-byte UTF-8 sequences on Windows.
    """
    try:
        return text.encode("cp1252").decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError):
        # If the round-trip fails, the text is either already clean
        # or corrupted beyond simple reversal. Return as-is.
        return text


def append_to_bitacora(bitacora: Path, message: str) -> None:
    """Append a hook-detected insight entry to the bitacora (full content, no HTML).

    Assumes 'message' has already been sanitized via sanitize_encoding().
    Uses an atomic temp-file + os.replace() write to avoid racing with
    Claude's own Edit-tool writes to the same bitacora file.
    """
    if _HAS_BEACON_UTILS:
        _, now_date, now_time, _ = get_timestamp()
    else:
        _now = datetime.now(TZ_LIMA)
        now_date = _now.strftime("%Y-%m-%d")
        now_time = _now.strftime("%H:%M:%S.") + f"{_now.microsecond // 1000:03d}"
    title = extract_title(message)
    session_id = get_session_id()

    # message is already encoding-clean (sanitized in main() before this call).
    # Cap at 80 lines to prevent truly massive entries.
    lines = message.strip().split('\n')
    if len(lines) > 80:
        content_body = '\n'.join(lines[:80])
        content_body += f"\n\n... [{len(lines) - 80} more lines truncated by safety-net]"
    else:
        content_body = message.strip()

    entry = f"""
### [{session_id}/HOOK] {now_date} {now_time} — Safety-net: {title}

**Type:** Hook-detected (insight-scribe safety net)
**Note:** Claude did not write this output via Write-First. The Stop hook captured it.

{content_body}

---
"""

    file_content = bitacora.read_text(encoding="utf-8")
    # Insert before SESSION_STATUS marker
    marker = "## SESSION_STATUS: ACTIVE"
    if marker not in file_content:
        return

    new_content = file_content.replace(marker, entry + marker, 1)

    # Atomic write: write to a sibling temp file, then os.replace() into place.
    # os.replace() is atomic on both POSIX and Windows (Python 3.3+), so a
    # concurrent reader always sees either the old or the new complete file.
    tmp_path = bitacora.with_suffix(f".tmp.{os.getpid()}")
    try:
        tmp_path.write_text(new_content, encoding="utf-8")
        os.replace(str(tmp_path), str(bitacora))
    finally:
        # Clean up temp file if os.replace() failed (e.g., permission error).
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except OSError:
            pass


def _locked_append(bitacora: Path, message: str) -> None:
    """Serialize concurrent Stop-hook writers across parallel sessions.

    Two sessions on the same day share one bitacora. append_to_bitacora()
    is atomic (temp + os.replace) but read-modify-write: simultaneous hook
    invocations could lose the earlier entry (last replace wins). An
    fcntl.flock on a sidecar .lock file closes that window. The kernel
    releases the advisory lock automatically if the hook dies, so no stale
    lock is possible; the sidecar is never unlinked (unlink+flock races).
    Fail-open: platforms without fcntl fall back to the unlocked atomic write.
    """
    lock_fh = None
    try:
        import fcntl
        lock_fh = open(bitacora.with_suffix(".lock"), "a")
        fcntl.flock(lock_fh.fileno(), fcntl.LOCK_EX)
    except Exception:
        lock_fh = None
    try:
        append_to_bitacora(bitacora, message)
    finally:
        if lock_fh is not None:
            try:
                import fcntl
                fcntl.flock(lock_fh.fileno(), fcntl.LOCK_UN)
            except Exception:
                pass
            try:
                lock_fh.close()
            except Exception:
                pass


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return

        data = json.loads(raw)

        # Guard: prevent infinite loops
        if data.get("stop_hook_active", False):
            return

        message = data.get("last_assistant_message", "")
        cwd = data.get("cwd", ".")

        if not message:
            return

        # ISSUE-4 fix: sanitize encoding BEFORE should_log() so that
        # skip-keywords with accented chars (e.g. "ver bitacora") match
        # correctly even when the pipe delivers cp1252-corrupted mojibake.
        message = sanitize_encoding(message)

        if not should_log(message):
            return

        bitacora = get_bitacora_path(cwd)
        if not bitacora:
            return

        _locked_append(bitacora, message)

    except Exception:
        # Fire-and-forget: never crash, never block
        pass


if __name__ == "__main__":
    main()
