---
name: yolo-prep
description: Pre-flight for YOLO-Mode — locates the disk-anchored blueprint, verifies harness posture, anchors context in the beacon, and activates the anti-drift directives. Invoke BEFORE /yolo-mode.
user-invokable: true
disable-model-invocation: true
activation-state: DORMANT
---

# YOLO-PREP — Autonomous-Execution Pre-Flight

**Version:** 1.0 — born from the audit of the original yolo-prep agent: the behavior
layer MUST be a skill (main session); the `yolo-prep` subagent remains a read-only,
fresh-context auditor.

**Relation to yolo-mode:** yolo-prep does NOT activate YOLO. It prepares and verifies.
The canonical flow is `/yolo-prep` → (READY) → `/yolo-mode`. The §D directives remain in
force for the entire subsequent YOLO run.

---

## FLOW

### Phase 0 — Target resolution
Target = the subproject the user names; if none is named, infer it from conversation
context; if there is no signal, pick the project root with the most recent mtime (and
declare the inference). Read-only reference trees are never a target (archaeology only).

### Phase 1 — Blueprint localization (disk-anchored plan)
1. Glob `<target>/docs/blueprints/*.md` → newest by `YYYYMMDD[_HHMM]_*` prefix
   (fallback: mtime).
2. Read the blueprint in full. Minimum sections: Objective, Scope boundary, Phases,
   Verification command.
3. **If NO blueprint exists → HALT.** This is the protocol's only valid gating question
   (missing input — the narrow exception yolo-mode §1 allows): inform the user that YOLO
   without a disk-anchored plan is forbidden, and offer to scaffold one from
   `BLUEPRINT_TEMPLATE.md` using the current task description. A scaffolded blueprint
   requires the user's explicit OK before READY.

For large repos, or when the user asks for fresh eyes: delegate Phases 1–2 to the
`yolo-prep` subagent (read-only, clean context) and consume its report.

### Phase 2 — Pre-flight report (exact schema)

```
[TARGET DIR]        <absolute path> (declared | inferred)
[ACTIVE BLUEPRINT]  <filename> (mtime <ts>)
[CONTEXT ANCHOR]    <absolute blueprint path — re-read at every phase transition>
[HARNESS]           defaultMode | deny guardrails | beacon SID | session-log status
[TREE STATE]        clean | N uncommitted (revertability warning)
[BLOCKERS]          list, or "none"
[READY TO DEPLOY]   YES | NO — reason
```

No code changes and no script execution during prep (reads and read-only commands only).
"READY: YES" requires: valid blueprint + `bypassPermissions` harness + active beacon +
active session log + zero blockers.

### Phase 3 — Beacon anchoring (mechanizes the "context flush")
Update the active RESTART_BEACON:
- `yolo_prep`: `{ "blueprint": "<path>", "target_dir": "<path>", "verified": "<TS>" }`
- Prepend to `context_decisions`: `"[<ISO date>] YOLO anchor: <blueprint path> — re-read
  at phase transitions"`

This is what makes the re-anchoring REAL: `write_first_reminder.py` re-injects the
beacon's `context_decisions` in the yellow/red context zone (P11+) and after compaction
(post-compaction boost). The anchor survives compactions without any magic mechanisms.

---

## §D ANTI-DRIFT DIRECTIVES (in force during the YOLO run)

1. **Boundary confinement:** writes are confined to the blueprint-designated
   `<target_dir>`, PLUS the session-state paths Write-First requires:
   `docs/sessions/<user>/` (session log, beacon, backlog), `.claude/cache/`, and the
   harness scratchpad. Everything else under the workspace root is out-of-bounds for
   writing. (Without this carve-out, the original directive contradicted yolo-mode §7.)

2. **Implicit Write-First:** zero approval proposals; fix + test + compact report.
   Identical to yolo-mode §1/§7 — no changes.

3. **No clutter:** no temp scripts, unsolicited debug logs, or scratch code inside the
   project dir. Temporaries → the harness scratchpad. Test code → the project's standard
   test suite (`<target>/tests/`).

4. **Context re-anchor (the honest version of a "context flush"):** before entering
   testing, verification, or packaging of each sub-task, **re-read the blueprint from
   disk**. If conversational memory contradicts the blueprint, the blueprint wins. (There
   is no "attention-weight purge" — the real mechanism is re-read + the Phase 3 beacon
   injection.)

5. **Circuit-breaker (amendment to yolo-mode §6):** if the SAME failure repeats across 2
   consecutive fix attempts → STOP that avenue: no automatic third attempt. Log the exact
   error stack in the session log (Write-First), report it in chat, and (a) if the
   blueprint has independent tasks, continue with the next one; (b) if the failure blocks
   the whole plan, HALT and wait for the user. This does NOT violate yolo-mode §6
   (autonomous error recovery): an infinite retry-loop with no human observer is more
   destructive than a pause.

6. **Dependencies (reconciliation with yolo-mode §5):** ephemeral deps via
   `uv run --with <pkg>` / `uv run --no-project` → free (they don't mutate pyproject).
   `uv add` / editing `pyproject.toml` → remains a risk-gate: it requires the blueprint to
   declare them explicitly in Scope, or the user's authorization.

---

## DE-ACTIVATION

The §D directives expire with the YOLO run: `/yolo-mode off`, a new session without a
YOLO signal, or the blueprint marked as completed. The beacon's `yolo_prep` field is
cleared by your session-close routine.
