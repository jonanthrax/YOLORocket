# YOLORocket 🚀🔥✨

**Rigid preparation for fearless, token-efficient autonomous coding.**

Everyone wants YOLO mode — the AI running fast, with no step-by-step babysitting. Pure
YOLO is also how you get catastrophic refactors, token bleeding, and a broken main branch.
YOLORocket resolves that paradox the way aerospace does: **you don't babysit a rocket in
flight — you earn the launch on the gantry.**

A deliberately small, production-tested set of Claude Code skills, agents, and hooks for
data-science and ML codebases — built and hardened over months of daily use on a real
scientific analysis platform. Not a grab-bag: every tool here survived a curation pass, and
together they tell one story — *negotiate the contract on the gantry, launch unattended,
verify the orbit with fresh eyes*.

---

## The Headline: Gantry → Launch → Mission Control

The secret to safe autonomy isn't monitoring the AI while it runs; it's the **negotiation
and alignment before it takes off**. And when it lands, asking the same agent "did you
finish?" is worthless — it grades its own homework with the same context that produced the
mistakes.

YOLORocket ships a complete autonomous-execution cycle with hard guardrails at both ends:

```
   THE GANTRY                 THE LAUNCH                   MISSION CONTROL
   (negotiate the contract)   (curated YOLO)               (fresh-context audit)
┌─────────────────┐         ┌─────────────────┐          ┌──────────────────────┐
│    BLUEPRINT    │  READY  │   /yolo-mode    │ shipped  │  /audit-completion   │
│  (plan on disk) │────────►│                 │─────────►│                      │
│                 │         │ zero approval   │          │ spawns a subagent    │
│   /yolo-prep    │         │ prompts, zero   │          │ with NO access to    │
│ pre-flight audit│         │ gating questions│          │ the executor's       │
│ by a fresh      │         │ within blueprint│          │ context — verifies   │
│ subagent        │         │ scope, explicit │          │ against machine-     │
└────────┬────────┘         │ risk-gates for  │          │ runnable acceptance  │
         │                  │ irreversible ops│          │ criteria             │
         │ NOT-READY:       └────────┬────────┘          └──────────┬───────────┘
         ▼ rocket stays locked       │                              │
   fix gaps, retry             /checkpoint at                 GREEN / RED
   (missing blueprint,        every milestone —              (RED verdicts are
   wrong harness mode,        instant restore point           non-overridable)
   dirty tree...)             for crash recovery
```

The four stages, and why each exists:

1. **The flight plan** — the blueprint: one or more markdown documents carrying your
   *refined* workplan — objectives and what "done" looks like, architecture, feature
   engineering, packages/dependencies, scope boundary, phases, and a runnable
   verification command. It lives *on disk*, not in the conversation: if context is lost
   mid-run, the plan isn't. Naming convention:
   `<target>/docs/blueprints/YYYYMMDD_HHMM_<slug>.md` — timestamp-prefixed, because the
   gantry always locks onto the newest (see [`yolo-prep` Phase 1](skills/yolo-prep/SKILL.md)).
   Start from the included
   [`BLUEPRINT_TEMPLATE.md`](skills/yolo-prep/BLUEPRINT_TEMPLATE.md).
2. **The gantry — [`/yolo-prep`](skills/yolo-prep/SKILL.md)**: like the tower that holds a
   rocket locked until every parameter is green, a *fresh-context*
   [auditor subagent](agents/yolo-prep.md) verifies readiness with evidence: blueprint
   valid, permissions posture correct, guardrail deny-rules present, git tree state known.
   It returns READY or NOT-READY — and the rocket does not launch on NOT-READY. This
   preparation is a genuine *negotiation*: the system surfaces the gaps, missing
   configurations, and risks up front, so the run burns tokens on the mission, not on
   mistakes.
3. **The launch — [`/yolo-mode`](skills/yolo-mode/SKILL.md)**: once released, the flight is
   genuinely autonomous. Gating phrases ("should I proceed?") are banned outright, but a
   non-negotiable risk-gate list survives (force-push, `rm -rf` outside workspace,
   dependency changes outside scope, anything visible to third parties).
   [`/checkpoint`](skills/checkpoint/SKILL.md) drops restore points at every milestone —
   telemetry you can recover from.
4. **Mission control — [`/audit-completion`](skills/audit-completion/SKILL.md)**: did the
   payload reach the intended orbit? A [completion-auditor](agents/completion-auditor.md)
   subagent that *never saw the executor's context* re-verifies every claim against
   machine-runnable acceptance criteria. RED verdicts cannot be talked around.

The executor never grades its own work. That single design decision is what makes the
"YOLO" part safe enough to use daily — not zero-risk (nothing autonomous is), but
risk-gated, contract-bound, and independently verified.

### Where YOLORocket sits in the ecosystem

The Claude Code community already has excellent structured-development frameworks
(e.g. [obra/superpowers](https://github.com/obra/superpowers) enforces TDD discipline) and
solid defensive hook collections (dangerous-command blocking, lint-on-save). YOLORocket
attacks a different pain: **the contract negotiated *before* an unattended run, and the
independent audit *after* it** — aimed at data-science and ML workflows, where the failure
modes are token-devouring data files, drifting long sessions, and confidently wrong
"done" claims.

---

## Flight Manual — Your First Mission

Once installed (see [Installation](#installation)), a mission looks like this:

1. **Write the flight plan.** Copy
   [`BLUEPRINT_TEMPLATE.md`](skills/yolo-prep/BLUEPRINT_TEMPLATE.md) to
   `<your-project>/docs/blueprints/YYYYMMDD_HHMM_<slug>.md` and fill it in. Be generous
   here — every minute on the gantry saves ten in orbit.
2. **`/yolo-prep`** — run the gantry audit. It verifies the blueprint, permissions
   posture, guardrails, and tree state, then reports READY or NOT-READY with evidence.
   Fix the gaps it surfaces and re-run until green.
3. **`/yolo-mode`** — release the rocket. Claude executes the blueprint autonomously,
   dropping [`/checkpoint`](skills/checkpoint/SKILL.md) restore points at milestones.
4. **Review the landing — and refine at full speed.** `/yolo-mode` stays active
   session-wide *by design*: when you want extra polish ("tighten X", "add tests for Y"),
   just say it — the refinement runs with the same autonomy, no re-negotiation needed.
   When you're satisfied, power down with **`/yolo-mode off`**.
5. **`/audit-completion`** — call mission control. A fresh-context auditor verifies every
   "done" claim against the blueprint's acceptance criteria. GREEN = merge with
   confidence.

Each skill's `SKILL.md` is its full reference manual — the commands above are the whole
day-to-day surface.

---

## What's Inside

**5 skills, 5 agents, 5 hooks.** Curated down from 70+ internal tools — what's published is
the subset that is genuinely reusable outside the workspace it grew up in.

### The YOLO Pipeline (Tier A)

| Tool | Kind | Purpose |
|------|------|---------|
| [`yolo-prep`](skills/yolo-prep/SKILL.md) | skill | Pre-flight: locates the disk-anchored blueprint, verifies harness posture, anchors context |
| [`yolo-prep`](agents/yolo-prep.md) | agent | The fresh-context auditor the skill spawns — returns a READY/NOT-READY report with evidence |
| [`yolo-mode`](skills/yolo-mode/SKILL.md) | skill | Zero approval prompts within blueprint scope, explicit risk-gates for irreversible actions |
| [`checkpoint`](skills/checkpoint/SKILL.md) | skill | Instant restore point to the session log — crash insurance during long autonomous runs |
| [`audit-completion`](skills/audit-completion/SKILL.md) | skill | Auto-invokes when plan items are closed; verifies against machine-runnable acceptance criteria |
| [`completion-auditor`](agents/completion-auditor.md) | agent | Fresh-context verification of completion claims — non-overridable RED verdicts |

### Code Archaeology (DS legacy exploration)

For the data scientist who inherits 40,000 lines of someone else's notebooks and scripts.
Each archaeologist explores read-only reference code via subagents **without flooding your
main context** — they share a single anti-token-overflow protocol
([`agents/_shared/archaeology_protocol.md`](agents/_shared/archaeology_protocol.md)): never
dump full files into main context, delegate heavy reads, write findings to output files.

| Agent | Purpose |
|-------|---------|
| [`math-archaeologist`](agents/math-archaeologist.md) | Discovers algorithms, statistical functions, ML pipelines, numerical edge cases |
| [`design-archaeologist`](agents/design-archaeologist.md) | Discovers visual patterns — chart geometry, layouts, typography, palettes in legacy code/PDFs |
| [`web-archaeologist`](agents/web-archaeologist.md) | Three-phase web research (Discovery/Extraction/Synthesis) with source credibility ranking |

### Meta-QA

| Skill | Purpose |
|-------|---------|
| [`skill-comply`](skills/skill-comply/SKILL.md) | Do your agents actually follow the rules you wrote? Auto-generates scenarios at 3 strictness levels, runs agents, reports compliance rates with full tool-call timelines |

### Hooks (System-Enforced)

Skills are hints; hooks are guarantees. These five enforce the Write-First doctrine and
session recovery at the harness level. Together they are the mission's **black box**: every
prompt you send and every significant output Claude produces is captured to an on-disk
session log — documented context that survives crashes, compaction, and time.

| Hook | Event | Purpose |
|------|-------|---------|
| [`write_first_reminder.py`](hooks/write_first_reminder.py) | `UserPromptSubmit` | Injects a Write-First reminder before every response; detects day-rollover drift |
| [`insight_logger.py`](hooks/insight_logger.py) | `Stop` | Safety net that captures important outputs Claude forgets to log |
| [`prompt_logger.py`](hooks/prompt_logger.py) | `UserPromptSubmit` | Appends each prompt to a per-session JSONL log |
| [`post_compact_signal.py`](hooks/post_compact_signal.py) | `PostCompact` | Re-injects session anchors after context compaction |
| [`beacon_utils.py`](hooks/beacon_utils.py) | (shared lib) | Read/write helpers for the restart-beacon JSON snapshot |

### Doctrine (Documented Patterns)

| Pattern | Description |
|---------|-------------|
| [Write-First Doctrine](docs/WRITE_FIRST_PATTERN.md) | 2-layer defense against losing AI outputs |
| [Multi-Model Orchestration](docs/MULTI_MODEL_ORCHESTRATION.md) | Haiku-as-Scout, cascading pipelines, capability matrix |
| [Skill Development Doctrine](docs/SKILL_DEVELOPMENT_DOCTRINE.md) | 4-primitive model, activation-state classification, plan-contract acceptance criteria, 7 generalized post-mortems |

---

## Why So Few Tools?

Because curation is the product. The bar for inclusion is simple: if a tool isn't
genuinely reusable in **your** project within an hour of copying it, it doesn't belong in
a public toolkit. Five skills, five agents, and five hooks that interlock into one
workflow beat a hundred loose utilities you'd have to evaluate one by one — the tools you
don't have to think about are the tools that make autonomy trustworthy.

---

## Roadmap

The current release covers the two layers unattended agent loops depend on: context
discipline (the blueprint contract, scope boundaries, token guardrails) and harness
discipline (risk-gates, a circuit-breaker on repeated failures, fresh-context
verification). If you're experimenting with
[loop-style workflows](https://addyosmani.com/blog/loop-engineering/) — agents iterating
toward a goal with minimal supervision — these are the pieces that keep a loop from
drifting, thrashing, or grading its own homework.

Planned next, in order of intent:

- **Worktree isolation** — ephemeral git worktrees for unattended runs, so failed
  iterations are discarded without ever touching your working tree.
- **Amnesia-resistant continuity** — extending the Write-First doctrine so a session can
  be compacted, cleared, or restarted without losing mission context. The seeds already
  ship (beacon snapshots, post-compaction re-injection); the next step is making recovery
  fully automatic.
- **Context-rot countermeasures** — skills that actively manage degradation as context
  grows ([a measured failure mode for coding agents](https://www.trychroma.com/research/context-rot)),
  building on the prompt-counter health zones already in the hooks.

No dates, no promises — items ship when they meet the same bar as everything else here.

---

## Key Innovations

### 1. Write-First Doctrine

**Problem:** Claude produces valuable analysis, then "forgets" to save it — especially
after `/compact` or long sessions.

**Solution:** A 2-layer defense system:
- **Layer 1 (Proactive):** Claude evaluates relevance → writes to log file FIRST → shows summary in chat
- **Layer 2 (Safety net):** Stop hook detects keywords → auto-appends if Layer 1 missed

```
Layer 1: Claude → Edit log → Chat shows summary
Layer 2: Stop hook → Keyword detection → Append [HOOK] entry as backup
```

### 2. Fresh-Context Verification

The recurring trick behind both ends of the YOLO pipeline: **never let the context that did
the work also judge the work.** Pre-flight readiness and completion claims are each checked
by a subagent with zero session history. Cheap to run, and it catches the failure mode that
matters most in autonomous execution — confident, contextually-reinforced wrongness.

### 3. Multi-Model Orchestration

**Pattern:** Use the right model for the right task:

```
Haiku (scout) → scans 50 files, filters to 8 by STRUCTURE
    ↓
Sonnet (analyst) → reads 8 files, evaluates SEMANTICALLY
    ↓
Opus/Fable (reviewer) → validates critical decisions, deep architecture work
```

**Golden rule:** Haiku filters by FORM (structure), never by CONTENT (meaning).

Result: ~6x cost reduction with same quality.

### 4. Prompt Counter as Health Indicator

The `UserPromptSubmit` hook tracks prompts per session:
- **P1-P10:** Green — fresh context, full coherence
- **P11-P20:** Yellow — context filling, watch for drift
- **P20+:** Red — context saturated, recommend new session

### 5. YOLO-Mode with Risk-Gates

Autonomous execution (zero approval-asking) is only safe with hard boundaries. `yolo-mode`
bans gating phrases ("should I proceed?", "your choice?") entirely, but keeps an explicit,
non-negotiable risk-gate list: force-push, `git reset --hard`, `rm -rf` outside workspace,
dropping DB tables, dependency changes outside declared scope, and anything visible to
third parties (PRs, Slack, email). `yolo-prep` is the mandatory pre-flight — it refuses to
let YOLO run without a disk-anchored blueprint.

---

## Installation

### 1. Copy files to your project

```bash
# Skills (directory format required!)
cp -r skills/yolo-prep/ .claude/skills/yolo-prep/
cp -r skills/yolo-mode/ .claude/skills/yolo-mode/
cp -r skills/checkpoint/ .claude/skills/checkpoint/
cp -r skills/audit-completion/ .claude/skills/audit-completion/
# ...repeat for any other skill you want

# Agents (flat file format)
cp agents/yolo-prep.md agents/completion-auditor.md .claude/agents/
cp agents/math-archaeologist.md .claude/agents/
cp -r agents/_shared .claude/agents/_shared   # required by the *-archaeologist agents

# Hooks
cp hooks/*.py .claude/hooks/
```

### 2. Configure hooks in `.claude/settings.json`

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python .claude/hooks/insight_logger.py"
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python .claude/hooks/write_first_reminder.py"
          }
        ]
      }
    ]
  }
}
```

### 3. Customize for your project

- **Hooks**: update `SESSIONS_DIR` / session-log path patterns and timezone to match your
  docs layout.
- **Blueprint**: copy [`skills/yolo-prep/BLUEPRINT_TEMPLATE.md`](skills/yolo-prep/BLUEPRINT_TEMPLATE.md)
  into `<your-project>/docs/blueprints/` and fill it in — the YOLO pipeline refuses to run
  without one.

---

## Gotchas We Discovered (So You Don't Have To)

| # | Gotcha | Impact |
|---|--------|--------|
| 1 | Flat `.md` files in `.claude/skills/` are **silently ignored** | Skills require `skills/<name>/SKILL.md` (directory format) |
| 2 | `skill.md` (lowercase) is **silently ignored** | Must be `SKILL.md` (uppercase) |
| 3 | `user-invocable` (with C) is **silently ignored** | Must be `user-invokable` (with K) |
| 4 | Multi-line YAML `description:` is **silently dropped** | Use single-line descriptions only |
| 5 | `model:` in skill frontmatter accepts `sonnet`/`opus`/`haiku`/`fable`/`inherit` | Scalar only — no per-skill fallback chain (use the workspace-level `fallbackModel` array instead) |
| 6 | UTF-8 on Windows hooks: CP1252 pipe corruption | Force UTF-8 stdin (see `insight_logger.py`) |
| 7 | `disable-model-invocation: false` = permission, NOT execution | Skills are hints, not triggers. Hooks are guaranteed. |

Related GitHub issues we filed:
- [#34538](https://github.com/anthropics/claude-code/issues/34538) — Silent skill format failure (BUG)
- [#34553](https://github.com/anthropics/claude-code/issues/34553) — effortLevel in frontmatter (FEATURE)
- [#34558](https://github.com/anthropics/claude-code/issues/34558) — Multi-model orchestration (FEATURE)

---

## Context

These patterns emerged from real pain points — lost outputs, encoding bugs, model
confusion, context drift across long sessions — and were validated empirically over months
of intensive Claude Code usage.

Some components reference a session-log convention (`docs/sessions/<user>/`) — these are
just markdown files the skills read/write; no external service required. Adapt the paths
to your own docs layout.

## License

MIT — see [LICENSE](LICENSE)
