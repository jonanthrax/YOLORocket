---
name: checkpoint
description: Quick state save to the active session log — an instant restore point without closing the session.
user-invokable: true
disable-model-invocation: true
activation-state: DORMANT
---

# Checkpoint — Quick State Save

Append a compact restore point to the active session log. No summary generation, no
session close — just enough state that a fresh context window (after `/clear`,
`/compact`, or a crash) can pick up exactly where you left off.

---

## LOCATION — ABSOLUTE RULE

The checkpoint is written **ONLY** to your active session log:
```
docs/sessions/<user>/YYYY_MM_DD_INTERACTIVE_BITACORE_SESSION.md   (workspace root)
```
**NEVER** inside `.claude/skills/`, **NEVER** inside read-only reference trees.

---

## Immediate Action

1. **Append** to the active session log:
   ```markdown
   ---
   ### [${SID}/CLAUDE] YYYY-MM-DD HH:MM:SS.mmm - CHECKPOINT

   **Active subproject:** [<project dir> | N/A]

   **Saved state:**
   - Last action: [description]
   - Pending proposed changes: [list]
   - Suggested next step: [action]

   ---
   ```

2. **Confirm** to the user:
   ```markdown
   Checkpoint saved - [timestamp]
   - Session log updated in docs/sessions/<user>/
   ```

---

## When to Suggest a Checkpoint

Claude suggests a checkpoint proactively when:

| Situation | Reason |
|-----------|--------|
| ~5 interactions without saving | Prevent context loss |
| Significant code proposed | Preserve work |
| User hints at closing soon | Anticipate shutdown |
| Before a long-running operation | Restore point |
| Topic or subproject switch | Close out prior context |
| A pipeline phase completes | Preserve pipeline state |

---

## Difference vs. a Session-Close Routine

| Aspect | Checkpoint | Session close |
|--------|------------|---------------|
| Closing summary | Not generated | Generated |
| Session status | Stays ACTIVE | Set to CLOSED |
| Restart beacon | Kept | Removed |
| Speed | Instant | Full process |
| Use | During work | At the end |
| Documentation check | No | Yes |
