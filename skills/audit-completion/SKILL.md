---
name: audit-completion
description: Plan-completion audit — Claude AUTO-INVOKES (v2 P5 2026-04-22) after any implementation iteration that transitions plan items to shipped/closed_no_fix. Spawns completion-auditor subagent (fresh context) to verify against machine-runnable acceptance_criteria (PLAN_CONTRACT v1.0). Writes report to docs/audit_logs/. Non-overridable RED verdicts.
model: inherit
user-invokable: true
disable-model-invocation: false
activation-state: AUTO-CONDITIONAL
---

# /audit-completion — Plan-Completion Governance (v2 auto-invoke)

Invoke this skill to get **independent verification** that plan items claimed as `shipped` or `closed_no_fix` actually satisfy their declared `acceptance_criteria` (PLAN_CONTRACT v1.0). This is the safety valve against the 4 failure modes documented in `docs/arq/instrumentation/PLAN_CONTRACT.md`:

- **F1** Over-claim ("ejecución completa" with pendings open)
- **F2** Mis-remember (confident assertion contradicted by audit)
- **F3** Cognitive drift across long sessions
- **F4** Semantic fuzziness ("shipped" ≠ "tested" ≠ "wired")

## v2 Auto-invoke policy (P5 2026-04-22)

**Claude AUTO-INVOKES this skill** post-implementation/iteration. User no longer needs to trigger manually. See `memory/feedback_plan_completion_governance.md` (v2) for the full policy.

**Auto-invoke TRIGGERS (Claude fires this skill when any apply):**

1. **SHIPPED bump** — Claude updates any YAML `status: pending|in_progress → shipped|closed_no_fix` → auto-invoke with `items=<bumped-id>`.
2. **Sprint/batch closure** — Claude declares a sprint closed → auto-invoke for all items in sprint.
3. **New contract + first ship** — Claude writes new `acceptance_criteria` and ships the first item → auto-invoke for that item.
4. **Session refresh** — if the session log references items shipped in a prior session that lack an audit log → auto-invoke to recalibrate.

**SKIP auto-invoke when:**

- Exploration / reads only (no mutations).
- Archaeology / research reports (no status transitions).
- Pure-doc edits without status changes.
- Rate-limit: once per sprint-batch per session.
- User's explicit "skip audit for this turn" directive.

## Usage (manual invocation still supported)

```
/audit-completion <sprint-or-section-id> [items=PF-1,PF-2,...] [plan=<path>]
```

**Shortcuts:**
- No args → defaults to `CHRONICLER_IMPLEMENTATION_PLAN.md §18 Active Pending Fixes`, items with status `shipped | closed_no_fix`.
- `§18` / `§20` alone → same default plan doc, audit items in that section.
- `items=<comma-list>` → restrict to specific item IDs.
- `plan=<path>` → override plan doc.

## What Claude must do when this skill is invoked (manual OR auto)

1. **Parse arguments** (positional `$ARGUMENTS` or auto-derived from recent iteration).
2. **Resolve plan document path** (default: `docs/arq/apps/chronicler/CHRONICLER_IMPLEMENTATION_PLAN.md`).
3. **Resolve section anchor** (default: `§18 Active Pending Fixes (Axis 1)`; accept any `§N` or named anchor).
4. **Resolve items-to-audit list**:
   - If `items=<list>` provided → use it.
   - Else → read the section and enumerate every item whose YAML `status` is `shipped` or `closed_no_fix`.
5. **Spawn the `completion-auditor` agent** (via `Agent` tool with `subagent_type: completion-auditor`).
   - Prompt MUST include:
     - `plan_doc_path` (absolute)
     - `section_anchor`
     - `items_to_audit` (explicit list)
     - `repo_root` (absolute path of the subproject being audited, e.g. `003_AUTOCV/autocv_dev`)
   - Request: "Return audit matrix per PLAN_CONTRACT v1.0 protocol. ≤ 400 words."
6. **Receive agent matrix.**
7. **Write the report** to `docs/audit_logs/YYYY_MM_DD_audit_<sprint-id>.md`.
8. **Summarize in chat** (≤ 150 words): verdict + per-item pass/fail + link + RED failures.
9. **If verdict is RED**, Claude MUST remediate before closing iteration.
10. **If auto-invoked**, log "AUDIT <verdict> (auto-invoked)" to the session log + update iteration status.

## Claude's closing sequence after an iteration

```
1. Complete implementation.
2. Identify items that transitioned status this turn.
3. Invoke this skill (via Skill tool).
4. Read verdict.
5. GREEN → log in the session log + close iteration.
6. AMBER → document unknowns + add to PENDING_BACKLOG + close.
7. RED → remediate + re-audit until GREEN.
```

## Report file format

Save at `docs/audit_logs/YYYY_MM_DD_audit_<sprint-id>.md` (use system date via `date +%Y_%m_%d`).

```markdown
# Audit report — <sprint-id>
**Date:** YYYY-MM-DD HH:MM
**Session:** <SID>
**Invoked by:** claude-auto | user ( /audit-completion )
**Plan doc:** <path>
**Section:** <anchor>
**Items audited:** <comma-separated>
**Verdict:** GREEN | AMBER | RED

## Matrix
| id | claimed | result | evidence |
|----|---------|--------|----------|

## Failures
...

## Recommendations
...
```

## Policy (v2)

- **Auto-invoke is the default path.** Manual invocation remains supported for user-initiated audits.
- **Non-overridable RED.** Claude cannot self-certify around a RED verdict. Remediate, re-audit, then close.
- **Fresh context always.** Auditor runs in a fresh subagent context — no memory of Claude's claims.
- **Exception:** items clearly `pending`/`in_progress` (no claim) don't need auditing.

## Canary calibration

Canary target: `§18` with items `[PF-1, PF-2, PF-3]`. Expected **GREEN**. Five consecutive GREEN established 2026-04-22 (00:13, 00:29, 11:57, 12:27, future). If a canary reports RED without clear evidence, the auditor or contract has a bug — halt and flag.

## Why `model: inherit`

Skill runs in main conversation's model; HEAVY lifting delegated to `completion-auditor` subagent (sonnet default, fresh context). Cost-bounded + independent.

## Anti-patterns

- **DON'T** re-invoke on every prompt — rate-limit: once per sprint-batch per session.
- **DON'T** skip the canary before trusting auditor verdicts on new sprints.
- **DON'T** let auditor RED verdicts be overridden by Claude's own opinion.
- **DON'T** auto-invoke on exploration/archaeology turns (no status transitions).

## Changelog

| Version | Date | Session | Summary |
|---------|------|---------|---------|
| 2.0 | 2026-04-22 | S20260422-1150 P5 | **v2 policy**: Claude auto-invokes post-iteration. `disable-model-invocation: false`. Removed user-in-loop step. Supersedes v1 "Claude recommends, user invokes". |
| 1.0 | 2026-04-21 | S20260418-1017 P101 | Initial skill. Pairs with completion-auditor agent + PLAN_CONTRACT v1.0. |
