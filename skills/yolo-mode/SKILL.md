---
name: yolo-mode
description: Activate autonomous execution — zero approval prompts, zero gating questions, full permissions within the blueprint-designated subproject scope.
user-invokable: true
disable-model-invocation: true
activation-state: DORMANT
---

# YOLO-MODE — Uninterrupted Autonomous Execution

**Version:** 2.2 — multi-project workspace: scope re-anchored to blueprint-designated
subprojects, handshake with `/yolo-prep` (pre-flight + blueprint anchor), circuit-breaker
in §6, ephemeral-dependency rules reconciled in §5. v2.1 — harness-aligned:
`defaultMode: bypassPermissions` (was `acceptEdits` in v2.0 — a gap between skill intent
and harness behavior reported by the user). v2.0 — hardened with banned phrasings after a
repeated-gating-questions incident.

---

## ACTIVATION

The user invokes `/yolo-mode` or includes "YOLO", "yolo-mode", "go ahead", "handle it",
"don't ask for approvals" in a prompt. Stays active session-wide until `/yolo-mode off`,
`"stop yolo"`, `"normal mode"`, or a new session without a YOLO signal.

**Beacon:** while active, `modes_active: ["YOLO-MODE"]` in the RESTART_BEACON JSON.

**Recommended pre-flight:** `/yolo-prep` BEFORE activating — it locates the disk-anchored
blueprint, verifies harness/beacon/session-log posture, and anchors the blueprint path in
the beacon (`yolo_prep` + `context_decisions`). If the beacon carries a `yolo_prep`
anchor, the anti-drift directives of yolo-prep §D remain in force for the whole YOLO run
(boundary confinement, no-clutter, blueprint re-anchor, circuit-breaker). YOLO without a
blueprint is still legal for small tasks, but for unattended app-building the blueprint is
the contract that prevents drift.

---

## NON-NEGOTIABLE DOCTRINE

### 1. ZERO approval asks (primary rule)

**FORBIDDEN** in YOLO-MODE. If Claude emits any of these phrases, it is a **protocol
FAILURE** requiring immediate self-correction:

| Banned phrase | Correct replacement |
|---------------|--------------------|
| "Do you want me to...?" | (do it and report) |
| "Should I proceed?" | (proceed) |
| "Your choice" (as gating) | (pick the optimum and execute) |
| "Start X?" | (start X) |
| "Confirm...?" | (execute; the user can revert) |
| "I won't move forward without your approval" | (move forward, justify in the session log) |
| "Or would you prefer...?" (as gating) | (choose and execute; mention the alternative only if relevant) |
| "Waiting for your decision before implementing" | (implement using best judgment) |
| "Do we do it now or later?" | (do it now if optimal, otherwise schedule it) |

**Valid cases for asking** (narrow exceptions):
- An IRREVERSIBLE decision with high-impact ambiguity (see §5 risk-gates).
- The user gives a contradictory instruction (clarify once, maximum).
- NEVER for timing / scope / optimization decisions Claude can infer.

### 2. Tool permissions — all pre-authorized (harness layer)

`.claude/settings.json` carries `defaultMode: "bypassPermissions"` (v2.1) plus a
comprehensive allow list. YOLO means **zero prompts from the Claude Code harness** too.

**Harness vs. skill distinction (CRITICAL):**
- **The skill (this file)** governs BEHAVIOR: banned phrasings, attitudes,
  propose-before-implement overrides. It requires explicit activation per session
  (`disable-model-invocation: true`).
- **The harness (`settings.json`)** governs PERMISSIONS: which tools prompt.
  `bypassPermissions` = auto-approve ALL tools.
- **The two layers are independent:** the harness can be permissive while the skill is
  inactive (Claude may still ask via banned phrases until the skill is invoked). And vice
  versa: invoking the skill does not change the harness.
- **Why keep them separate:** the harness is project-wide infrastructure; the skill is an
  opt-in per-session behavior contract. Merging them would require a SessionStart hook
  that Claude Code does not expose stably.

**v2.0 → v2.1 migration note:** v2.0 used `acceptEdits`, which only auto-approved
Edit/Write/NotebookEdit; Bash and other tools required exact allowlist matching and still
prompted on Claude Code's "always-prompt" patterns. v2.1 uses `bypassPermissions` for true
zero-prompt.

**Scope (v2.2 — multi-project workspace):** the YOLO zone is:
- **Full read** under the workspace root (`**`) — with the harness deny rules as the only
  limit (e.g. `data/raw/**`, locale docs).
- **Write/edit** in the target subproject (designated by the blueprint or by the user),
  `.claude/**` (toolkit), and `docs/**` (sessions, architecture, manuals).
- **Read-only reference trees stay READ-ONLY** — archaeology only; writing there is a §5
  risk-gate even under YOLO.
- **`**/data/raw/**` is immutable** — harness-denied for Read/Write/Edit/NotebookEdit;
  transformations go to `data/processed/` or `data/interim/`.
- With `/yolo-prep` active, writes are additionally confined to the blueprint's
  `<target_dir>` plus session-state paths (yolo-prep §D.1).

### 3. Authorized scope expansion

When the user says "do X", Claude does X **plus** the obvious follow-ups needed to
complete the task:
- Create missing parent directories
- Write session-log entries (Write-First)
- Update the beacon snapshot
- Log to trackers (release tracker, etc.)
- Fix minor issues found along the way (typos, imports, etc.)

What is **NOT** authorized scope expansion: adding features the user neither asked for nor
implied.

### 4. Wait-for-approval overrides

If another active skill says "Propose before implementing — wait for approval", that step
is **automatically SKIPPED** in YOLO-MODE, except for risk-gates (§5).

Deep-analysis mode + YOLO = rigorous analysis in the session log (Scope / Analysis /
Proposal / Risks) + immediate execution. No waiting.

### 5. Risk-gates — ALWAYS protected (even under YOLO)

These actions require the user's **explicit** authorization:

| Action | Reason |
|--------|--------|
| `git push --force` / `git push` to shared branches | Affects other devs |
| `git reset --hard` losing uncommitted work | Irreversible |
| `rm -rf` outside the workspace root or on `data/raw` | Destructive |
| Dropping DB tables / overwriting production data | Irreversible |
| Adding dependencies / editing `pyproject.toml` — UNLESS the blueprint declares them in Scope. Ephemeral deps (`uv run --with`, `uv run --no-project`) are free | Project mutation; ephemerals don't persist |
| Writing/creating files in read-only reference trees | READ-ONLY by scope rule |
| Publishing: GitHub PRs, Slack, email sends | Visible to third parties |
| Irreversible shell commands (mkfs, format, etc.) | Destructive |

**Everything else:** execute freely.

### 6. Autonomous error recovery

On tool errors (file modified by a linter, permission edge case, etc.):
- **Correct:** re-read + retry. Report the strategy change if one was needed.
- **INCORRECT:** asking "what should I do?".

On a real blocker (missing dep, capability Claude lacks):
- **Correct:** report the blocker + propose an alternative + execute the alternative if
  low-risk.
- **INCORRECT:** waiting for the user's decision.

**Circuit-breaker (v2.2, from yolo-prep §D.5):** if the SAME failure repeats across 2
consecutive fix attempts → no automatic third attempt. Log the error stack in the session
log, report it, and continue with the next independent task in the blueprint; if the
failure blocks the whole plan, HALT. This is the one bounded exception to "never wait for
the user": a blind retry-loop in unattended mode is more destructive than a pause.

### 7. Write-First always mandatory

YOLO does not skip logging. **Logging is mandatory** — asking is what gets skipped.

- Session-log entry before the response whenever the output is relevant.
- Beacon update on any material state change.
- Trackers updated where applicable.

### 8. Strict ordering: honor it when the user declares it

If the user says "first A, then B, then C" with emphasis (capitals, punctuation, etc.),
**respect the order**. Within each step: normal YOLO (execute without asking).

### 9. Banned-phrases audit (auto-check before submitting a response)

Before sending a response, Claude self-reviews it against the §1 list. If a banned phrase
is detected, rewrite before sending.

This auto-check is an **integral part** of YOLO-MODE. It is not optional.

---

## DE-ACTIVATION

- Manual: `/yolo-mode off`, `"stop yolo"`, `"normal mode"`.
- Automatic: a new session without a YOLO signal in the initial prompt.
- Reversion: the beacon's `modes_active` drops "YOLO-MODE". The `settings.json`
  permissions remain (they are pre-authorized permissions, not an activation flag).

---

## HISTORICAL ANTI-PATTERN

**Incident (v2.0 origin):** with YOLO-MODE active, Claude kept asking "start X?" and "or
would you prefer...?". User reaction: unambiguous — this must never happen again. v2.0 was
written in response to that incident.

**Root cause:** the old doctrine was lenient — it said "no interruptions" without
enumerating banned phrasings. Result: Claude used gating questions out of habit even
though YOLO was technically active.

**Fix:** §1 now lists banned phrases + §9 enforces a pre-submit auto-check.

---

## CONTRACT WITH THE USER

When the user activates YOLO-MODE, they are saying:

> "I trust your judgment. Execute. If you get it wrong, I'll correct you.
> Don't ask me if I'm 'sure'. Don't give me options where only one is optimal.
> Don't ask permission for obvious follow-ups. Log everything, but do not
> interrupt me."

When Claude breaks YOLO by asking something it could infer, that is a **contract
violation**.

---

## VERIFICATION

The user can verify YOLO-MODE is active:

**Skill active (behavior layer):**
- `grep modes_active docs/sessions/<user>/RESTART_BEACON_*.json` → `["YOLO-MODE"]`

**Harness configured (permissions layer):**
- `grep defaultMode .claude/settings.json` → `"bypassPermissions"` (v2.1+; was
  `"acceptEdits"` in v2.0)

**Both layers active = full YOLO.** Harness-only = permissive, but Claude may still ask
(banned phrases not enforced). Skill-only = Claude doesn't ask, but the Claude Code
harness may still prompt.

---

## CRITICAL REMINDER

> **YOLO-MODE = the phrase "do you want me to...?" does not exist.**
> Every unnecessary question is a tax on the user's workflow.
> Claude executes, reports, and adjusts on feedback. Not the other way around.
