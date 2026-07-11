# BLUEPRINT — <app/feature name>

**File:** `<target>/docs/blueprints/YYYYMMDD_HHMM_<slug>.md` (timestamp prefix REQUIRED — yolo-prep sorts by it)
**Status:** DRAFT | APPROVED | COMPLETED
**Target dir:** `<absolute path of the subproject>`

## Objective

<1-3 sentences: what exists at the end that didn't exist before, and what "done" looks like>

## Scope boundary

- **May touch:** `<target>/src/**`, `<target>/tests/**`, `<target>/docs/**`
- **May NOT touch:** <explicit paths — e.g. data/raw (harness-denied), other subprojects>
- **New deps in pyproject:** <none | explicit list — this is what unlocks `uv add` without a risk-gate>

## Phases

1. <phase 1 — concrete deliverable>
2. <phase 2 — concrete deliverable>
3. <...>

Each phase ends with: a re-read of this blueprint + the verification command green + a session-log entry.

## Verification command

```bash
# exact command(s) that define "green" — runnable without intervention
uv run --no-project pytest <target>/tests/ -x -q
```

## Risk notes

<known irreversibilities, data that must not be touched, decisions already made that are NOT re-litigated>
