# Skill / Agent / Hook Development Doctrine

Generic doctrine for designing, classifying, and auditing the three Claude Code
instrumentation primitives (Skills, Agents, Hooks). It applies to any project using this
toolkit — it does not depend on any specific domain, legacy project, or workspace name.
Where this document cites concrete examples, they are illustrative, not prescriptive.

**Origin:** doctrine consolidated from ~4 months of daily skill/agent/hook development
practice. It replaces any prior instrumentation documentation tied to already-migrated
projects — those trees remain archaeology references only, not active sources.

---

## 1. The 4 primitives and when to use each

There are 4 primitives with distinct invocation semantics. Confusing them is the most
common design error when instrumenting a project.

| Primitive | What it is | Who invokes it | File format |
|-----------|-----------|----------------|-------------|
| **Skill** | Reusable prompt with frontmatter | The user (`/name`) or the model automatically | `skills/<name>/SKILL.md` |
| **Agent** | Autonomous subprocess with its own tool set | The model, via the agent-invocation tool | `agents/<name>.md` |
| **Hook** | Script the SYSTEM executes on lifecycle events | The system (automatic, guaranteed — does not depend on the model "remembering") | Registered in `settings.json` → `hooks` |

**Golden rule (mnemonic):**
```
SKILLS = you invoke them with /name (or the model auto-invokes them)
AGENTS = the model launches them as autonomous subprocesses
HOOKS  = the SYSTEM executes them automatically (guaranteed)
```

**"What do I need" decision table:**

| I need... | Use |
|-----------|-----|
| A reusable prompt the user invokes explicitly | Skill (`user-invokable: true`) |
| A prompt the model invokes on its own, no intervention (self-evaluation) | Skill with `user-invokable: false` / auto-invoked |
| An autonomous subprocess that reads/searches/analyzes and returns a summary | Agent |
| A guaranteed post-event action (logging, state snapshots) — must not depend on the model "remembering" | Hook (`type: command`) |
| A per-invocation model switch | The `model:` field in skill frontmatter (if the harness supports it) |

**Critical structural difference between Skills and Agents:** Skills demand the
`directory + uppercase-filename` format (`SKILL.md`), while Agents accept flat files. This
asymmetry is not intuitive and produces silent failures if you assume both primitives
share a file convention — never assume; always verify the exact convention of the harness
in use.

---

## 2. Anatomy of a well-designed Skill

### 2.1 File structure — non-negotiable rule

```
skills/<name>/SKILL.md     <-- CORRECT
skills/<name>.md           <-- may be silently ignored by the harness
skills/<name>/skill.md     <-- may be silently ignored (case-sensitivity)
```

**General principle:** when a harness demands a specific file-naming convention,
non-compliance does NOT produce an error — it produces silent failure (the skill simply
never appears). This turns "follow the exact convention to the letter" into a mandatory
validation step, not an optional one, after creating any new skill.

### 2.2 Frontmatter — typical fields and their function

```yaml
---
name: my-skill
description: One line. Multi-line descriptions may be silently dropped
             depending on the harness version/parser — verify empirically.
user-invokable: true          # beware of spelling variants (see 2.3)
disable-model-invocation: false
model: sonnet                  # optional: forces the model for this invocation
context:                       # optional: files auto-loaded on invocation
  - path/to/file.md
allowed-tools: [...]           # optional: restricts which tools are available
---
```

**Key design principle — declare, don't assume:** a skill must explicitly declare its
activation model (auto vs. manual), and any context files it needs, instead of relying on
the model "remembering" to read them. The `context:` field (auto-loading files on
activation) is strictly more reliable than trusting the model to read a file on its own
initiative.

### 2.3 Cross-cutting frontmatter gotchas

Risk category: **frontmatter fields with similar names but binary behavior (works /
silently ignored)**. When a harness has multiple fields with ambiguous naming or plausible
spelling variants, ALWAYS verify against current official documentation (not against
memory/habit), because:
- The field may have a "reasonable but wrong" spelling variant the parser ignores without
  warning.
- The field may look supported but not be in the current harness version (or vice versa).
- Multi-line content in "free text" fields may be truncated — assume single-line unless
  verified otherwise.

**Frontmatter verification checklist before considering a field supported:**
1. Is there recent official documentation confirming it?
2. Has it been tested empirically (the skill behaves as expected after invoking it)?
3. Does the field show up in the harness's autocomplete / skill listing?

### 2.4 Minimal skill template

```markdown
---
name: my-skill
description: One-line description
user-invokable: true
---

# My Skill

Prompt content / instructions.

## Task:

$ARGUMENTS
```

---

## 3. Anatomy of an Agent

### 3.1 Typical frontmatter

```yaml
---
name: my-agent
description: Agent description — what it does and when it should be used
model: sonnet
tools: [Read, Grep, Glob]
hooks:                        # agent-specific hooks (optional, additive to globals)
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: ".../hooks/guard.sh"
---
```

### 3.2 Model precedence

When multiple levels can set an agent's model, the precedence (highest to lowest priority)
is:

```
1. Explicit override at agent-launch time (parameter passed by the invoker)
2. Default declared in the agent's own frontmatter
3. Model inherited from the parent session/context
```

Documenting this cascade explicitly removes ambiguity about "why did it run with that
model" and makes fallback reasoning tractable.

### 3.3 Rate-limit fallback — Skills vs. Agents asymmetry

| Aspect | Skills (with `model:` in frontmatter) | Agents |
|--------|----------------------------------------|--------|
| Who orchestrates the model switch | The platform/harness, BEFORE the model sees the prompt | The model itself, via the agent-invocation parameter |
| Can the model retry after a failure? | NO — the error goes straight to the user | YES — the model can detect the failure and relaunch with another model |
| Is fallback possible? | NO (unless the harness supports it explicitly — see `fallbackModel` in `settings.json`) | YES — by passing a different model on the next attempt |

**Lesson:** when the model switch happens "outside" the model's control (at platform
level), there is no interception point for error handling — the failure is terminal for
that invocation. Design your agent system assuming model/rate-limit failures WILL happen,
and prefer mechanisms where the failure is observable and recoverable.

### 3.4 The "cheap scout, expensive analyst" pattern (cost-cascading models)

```
Cheap/fast model (scout)   --> filters a large candidate universe down to a small subset, by FORM (structure)
    |
Mid-tier model (analyst)   --> reads the filtered subset, evaluates SEMANTICALLY
    |
Expensive model (reviewer) --> validates only the critical decisions
```

**Golden rule:** the cheapest/most limited model filters by FORM (structure, syntax,
name/file patterns), never by CONTENT (meaning, semantic correctness, architectural
judgment).

| Task type | Suitable for a cheap model? |
|-----------|------------------------------|
| Finding files by name pattern | Yes — good |
| Validating syntax | Yes — good |
| Counting lines/classes/occurrences | Yes — good |
| Semantic code review | No — needs a more capable model |
| Architectural decisions | No — needs a more capable model |
| Interpreting results/data | No — needs a more capable model |

Expected result: significant cost reduction (empirical reference: ~6x cheaper than using
the expensive model to scan everything) while keeping final quality.

**Typical "scout" model limitations:** smaller context window, possible lack of extended
"effort/thinking" support, and missing support for certain advanced tool-use blocks.
Declare these limitations explicitly in its instructions.

### 3.5 Anti-Token-Overflow protocol for exploration agents

```
R1: NEVER return full file contents to the main context (the one that invoked the agent)
R2: Write findings directly to an output file
R3: To the main context, return ONLY a summary: "Wrote section X, ~N lines, M patterns"
R4: Cap simultaneous file reads (bounded parallelism)
R5: Line cap if data MUST return to the main context (e.g., max 10 lines)
R6: Never read files above a certain size verbatim — always summarize
```

Applicable to any agent exploring large codebases/documents. The essence: **an exploration
agent's output to its invoker must be an actionable summary, never a dump.**

---

## 4. Hooks — the "guarantee" primitive, not the "trust" primitive

### 4.1 What sets them apart

Hooks are executed by the SYSTEM, not the model. They do not depend on the model deciding
to invoke them — they are the only truly deterministic/guaranteed lifecycle primitive.

**Design rule:** any behavior that must happen ALWAYS, without exception, and whose
omission is unacceptable (audit logging, state snapshots, safety invariants) must be
implemented as a hook — not as a prompt instruction, not as an auto-invoked skill. Prompt
instructions are probabilistic, not guaranteed.

### 4.2 Hook types by execution mechanism

| Type | What it does | Latency | Cost |
|------|--------------|---------|------|
| `command` | Runs a script (shell/Python/etc.) | Low/none (can be async) | Zero — consumes no LLM tokens |
| `prompt` | Invokes the LLM with a specific prompt | Medium | Consumes tokens |
| `agent` | Launches a full subagent with its own tools | High | Tokens + tool costs |

**Recommendation:** prefer `command` hooks for logging/snapshots/beacons (no reasoning
required). Reserve `prompt`/`agent` for hooks whose task genuinely needs reasoning.

### 4.3 Lifecycle events — generic categories to cover

- **On user input** — inject context or reminders.
- **Before/after a tool runs** — validation, vetoing dangerous actions, recording.
- **On tool failure or API error** — recovery or notification.
- **When a model response finishes (Stop)** — post-hoc safety net.
- **On subagent start/stop** — validate outputs or clean up resources.
- **On session start/end** — initialization and orderly shutdown.
- **Before/after context compaction** — preserve critical state or inject fresh context.
- **On permission requests** — an additional security layer.

**Blocking vs. non-blocking principle:** some events allow the hook to BLOCK the action;
others are purely informational. When designing a hook, identify the contract explicitly:
a blocking hook must be fast and reliable (deliberate fail-open or fail-closed); a
non-blocking one can tolerate more latency.

### 4.4 Robustness contract for `command` hooks

```python
def main():
    try:
        raw = read_stdin()
        data = parse_json(raw) if raw else {}
        # --- hook logic ---
    except Exception:
        # CRITICAL: never crash, never block the harness flow.
        pass
```

**Non-negotiable principles:**
1. **It must never crash the parent process** — a wide wrapping try/except with silent
   fallback.
2. **It must never block indefinitely** — especially on high-frequency events. Hooks must
   be fast or asynchronous.
3. **It must tolerate burst execution without accumulating noise** — respect any "already
   active" flag to avoid recursion/loops.
4. **Isolate hooks from one another** — each must be able to fail independently without
   taking the others down.

### 4.5 Component-level hooks (skill/agent) vs. global hooks

| Scope | When to use it |
|-------|----------------|
| **Global** | The hook must fire for ALL sessions/invocations without exception |
| **Per-skill** | Only relevant while that specific skill is active |
| **Per-agent** | Only relevant while that specific agent runs |

Per-component hooks are **additive** to global ones, not replacements, and clean up
automatically when the component finishes. Their execution relative to global hooks is
non-deterministic (do not assume ordering).

---

## 5. The Activation Pattern — 4 states and a decision tree

An explicit model of **when something should fire on its own vs. when it should require
human intervention**, with a cognitive-load heuristic for deciding.

### 5.1 The 4 states

| State | Trigger mechanism | User cognitive load | Reliability |
|-------|-------------------|---------------------|-------------|
| **ACTIVE-HOOKED** | Hook firing on every lifecycle event | Zero (background) | Deterministic |
| **VIGILANT-SCHEDULED** | Auto-fired at session start or on a cadence window | Zero (background) | Deterministic |
| **AUTO-CONDITIONAL** | The model decides autonomously whether to invoke, by `description`↔context match | Zero (but variable) | Variable |
| **DORMANT** | The user invokes explicitly (`/slash-command`) | High (must remember the command) | Deterministic (if they remember to invoke it) |

**Central insight:** the cognitive-load bottleneck lives in the DORMANT bucket. Moving
something to VIGILANT-SCHEDULED or AUTO-CONDITIONAL reduces "things the user must
remember" — but not every action should be promoted.

### 5.2 When each state is correct

**ACTIVE-HOOKED** — per-response invariants: structured logging, state snapshots, context
injection, post-response synthesis. Must tolerate noise and must not block.

**VIGILANT-SCHEDULED** — batch operations with synthesized review: reviewing prior
artifacts, external-dependency monitoring, maintenance sweeps. Runs at natural reflection
points (session start). Must have a queryable cadence and be non-destructive by default
(propose, don't blindly apply).

**AUTO-CONDITIONAL** — reminders that prevent known errors in specific domains. The
`description` must be specific enough that false positives are rare. Do not use it for
invariants that MUST always fire. Avoid it if the description overlaps with more than 1–2
existing skills/agents.

**DORMANT** — when the user's intent IS the correct trigger: scaffolding, deliberate
research, mode toggles, queries, session start/end rituals. Cases where DORMANT is the
correct choice (not an "I didn't classify it"):
- Research flows where the user deliberately chooses what to explore.
- Deliberate scaffolding/artifact creation.
- Mode toggles.
- Session rituals (endpoints, not something continuous).
- User-directed writes/queries against a curated knowledge store.

### 5.3 Classification decision tree

```
Q1. Is it a per-response invariant (runs every cycle, does logging/snapshots)?
    YES → ACTIVE-HOOKED
    NO  → continue

Q2. Does it benefit from batch/synthesized review (daily/weekly/at-session-start)?
    YES → VIGILANT-SCHEDULED
    NO  → continue

Q3. Is there a specific, low-ambiguity description trigger for the model to decide
    on its own?
    YES → AUTO-CONDITIONAL
    NO  → continue

Q4. Does the action require the user's explicit intent (scaffold, research, mode,
    query, ritual)?
    YES → DORMANT (correct by design, NOT a lazy fallback)
    NO  → return to Q3 and re-examine whether the description can be made more specific
```

### 5.4 Red flags — when NOT to promote out of DORMANT

Do not promote to VIGILANT or AUTO-CONDITIONAL if:
- The action has irreversible side effects (delete, publish, send, commit).
- The trigger context is ambiguous → high false-positive probability.
- The user must semantically approve each invocation.

Specific reasons NOT to assign AUTO-CONDITIONAL:
- The description overlaps with more than ~2 existing skills/agents.
- The action MUST fire without exception (use hooked/scheduled instead).
- A reliability slip would be unacceptable.

### 5.5 Maintenance rules for the activation system

1. Every new skill/agent must declare its activation state explicitly.
2. Promoting from DORMANT to another state requires auditing description specificity and
   false-positive risk; document the reasoning.
3. Every VIGILANT-SCHEDULED state MUST have a queryable cadence field + a "skip if the
   interval hasn't elapsed" check.
4. Every ACTIVE-HOOKED state MUST be non-blocking.
5. Periodically verify that the declared state still matches observed behavior.
6. Changing a component's activation state is a disruptive change — update
   cross-references.

### 5.6 Component interaction matrix

As the system grows, explicitly document the known interactions between
skills/agents/hooks: who triggers whom, who overrides whom, which orchestrator
conditionally invokes which others. This prevents surprises when two components with
independent logic interact in non-obvious ways.

---

## 6. Namespace — collisions with harness built-ins

### 6.1 The structural problem

A harness vendor continuously ships new "factory" commands/skills. Recurring risks:
1. A new built-in takes exactly the same name as one of yours → real collision.
2. A new built-in conceptually covers the same ground under a different name → conceptual
   overlap (decide: deprecate yours? keep both with differentiated roles?).

**This is NOT a one-time event — it is a recurring pattern.** Every time the harness ships
a new version with new commands/skills, re-run the namespace audit.

### 6.2 Audit method (repeatable)

1. List all of the project's own skills/commands.
2. List all known harness built-in commands at the current version.
3. Build a collision matrix by EXACT name.
4. Document CONCEPTUAL overlaps separately, with an explicit recommendation for each.
5. Trigger for the next re-audit: "the next harness version that introduces a new
   command/skill" (tied to the release tracker, §6.4).

### 6.3 What to do on a real name collision

- Evaluate whether the built-in is functionally superior or equivalent → consider
  deprecating your own.
- If your component has a more specific scope, document why it stays, and consider
  renaming it.
- Check whether the harness offers an opt-out mechanism for specific built-ins.

### 6.4 Upstream monitoring as namespace-audit input

Keep a living tracker of harness changes (new versions, capabilities, deprecations,
security fixes), consulted on a cadence (e.g., daily at session start). It serves as:
- Direct input for the namespace re-audit.
- Duplicate-effort prevention: before building a workaround, check whether the harness
  already offers it natively.
- Detection of security fixes relevant to your own permission model.
- Detection of keywords the harness starts interpreting specially.

---

## 7. Plan Contract — making "done" verifiable

### 7.1 The problem it solves

A language model's self-declaration of "this is done" is structurally unreliable:

| Failure mode | Description |
|---|---|
| **Over-declaration** | "Completed" is claimed with open, unresolved pending items |
| **Faulty recall** | A confident claim is contradicted by later audit |
| **Cognitive drift** | Items get "forgotten" after context compaction or long sessions |
| **Semantic ambiguity of "done"** | "Delivered" ≠ "tested" ≠ "wired into the real flow" |

### 7.2 The solution: machine-verifiable acceptance criteria

Every plan item must declare **machine-runnable acceptance criteria**, not just prose. An
auditor agent with fresh context (one that did not participate in the implementation) runs
those criteria; only if ALL pass is the item considered done.

### 7.3 Acceptance-criterion types

| Type | Purpose |
|------|---------|
| `file_exists` / `file_does_not_exist` | Presence or absence of a file/directory |
| `grep_contains` / `grep_absent` | Presence/absence of a pattern in a file |
| `import_wired` | The symbol is actually connected in the real pipeline, not just defined |
| `tests_pass` | The suite passes AND a minimum number of tests actually ran |
| `custom_bash` | Arbitrary command whose stdout/exit code is inspected |
| `doc_updated` | The document contains a specific update marker |
| `manual_verified` | Escape hatch — a human certified manually (requires verifier + date + evidence; NEVER the default) |

### 7.4 Design rules for a good contract

1. Every "completed" declaration must have at least ~3 criteria, covering existence +
   tested behavior + real wiring.
2. A "tests pass" criterion is practically mandatory for code — grep alone risks false
   negatives.
3. `file_exists` alone is NEVER sufficient.
4. `manual_verified` is an escape hatch, not a default — it demands a named verifier,
   date, and evidence.
5. **Idempotency:** re-running the auditor on the same item must deterministically yield
   the same result.

### 7.5 Status vocabulary

| Status | Meaning | What the auditor does |
|--------|---------|----------------------|
| `pending` | Not started | Skips it |
| `in_progress` | Work underway | Skips it |
| `shipped` / `done` | Code + tests + wiring + docs complete | Runs ALL criteria; must be green |
| `blocked` | Waiting on an external dependency | Verifies the blocker still holds |
| `closed_no_fix` | An explicit decision was made not to change code | Verifies evidence of that decision |

### 7.6 Anti-patterns when writing contracts

| Anti-pattern | Why it's bad | Fix |
|--------------|--------------|-----|
| Criterion as a free-form string | Not machine-verifiable | Use typed blocks (§7.3) |
| Only `file_exists` | An empty/orphan file would pass | Also require `tests_pass` |
| Overly lax search pattern | Trivial false positive | Specific substrings/patterns |
| Minimum test threshold too low | False negatives | Calibrate to the item's real size |
| Running the full suite unfiltered | Slow and sensitive to unrelated failures | Bound it with a filter/keyword |

### 7.7 Contract lifecycle governance

- **The item's author writes the contract WHEN adding it to the plan, not when declaring
  it done** — this prevents retrofitting criteria known to pass.
- Pre-existing items without contracts are retrofitted only when they are about to be
  audited.
- The auditor runs with fresh context, ideally as a separate subagent.
- The output is a readable artifact with a global verdict, a per-item matrix with
  evidence, a failure list, and recommendations.

### 7.8 Definition of Done by artifact type

| Artifact type | Minimum acceptance criteria |
|---------------|------------------------------|
| New, pure code module | existence + tests (several) + connection/wiring |
| Extension of an existing module | new pattern present + tests + wiring |
| New interface/CLI | existence + smoke command + pattern present |
| Documentation-only update | specific marker + changelog entry |
| Deliberate deletion | file absent + no dangling references + tests still pass |
| Refactor | tests pass (same count or more) + new-signature pattern |
| New schema/contract | existence + keys present + at least one test using it |

---

## 8. Checklist for creating a new instrument (skill / agent / hook)

### 8.1 Decision tree: which type to create?

```
Is it behavior the model must ALWAYS execute, without depending on it "remembering"?
├── YES → Does it require executable code?
│   ├── YES → HOOK
│   └── NO  → auto-invoked SKILL (user-invokable: false)
└── NO → Does the USER invoke it explicitly with /?
    ├── YES → user-invokable SKILL (user-invokable: true)
    └── NO → Is it research/exploration delegable to a subprocess?
        ├── YES → AGENT
        └── NO  → It probably doesn't need a dedicated instrument
```

### 8.2 Creating a Skill

**Prerequisites:**
- [ ] Clear one-sentence purpose.
- [ ] Verify it doesn't duplicate an existing skill.
- [ ] Decide: user-invokable or auto-invoked?
- [ ] If it needs a model switch, plan the frontmatter field.

**Steps:**
1. Create the file structure the harness demands.
2. Write the complete frontmatter.
3. Validate: invoke the skill and confirm it appears in the harness listing. If it does
   NOT appear, check in order: file format, exact naming convention, single-line
   description.
4. Document: central catalog + development guide + project history.

### 8.3 Creating an Agent

**Prerequisites:**
- [ ] Define the research/task domain (the "where" must be explicit, never assumed by
      default).
- [ ] Pick the appropriate model (structural/cheap vs. semantic/complex — §3.4).
- [ ] Define the minimal tool set (least-privilege principle).

**Steps:**
1. Create the agent file (verify flat file vs. directory).
2. Write frontmatter + instructions, including the anti-overflow protocol (§3.5) if it
   explores massive content.
3. If it uses a cheap "scout" model, include its limitations and the form-not-content
   rule.
4. Validate: invoke it, confirm the expected model, confirm it does NOT return full
   contents to the main context.
5. Document in the central catalog and development guide.

### 8.4 Creating a Hook

**Prerequisites:**
- [ ] Define the exact trigger event.
- [ ] Define the type (`command` / `prompt` / `agent`).
- [ ] Define the scope: global vs. per-component.
- [ ] Decide whether it needs to run "exactly once" (check harness support).
- [ ] The hook must NEVER block the harness flow indefinitely.

**Steps:**
1. Create the script.
2. Apply the robustness contract (§4.4).
3. Register it in the harness's central configuration.
4. Apply known platform gotchas (e.g., encoding — §10).
5. Validate: it runs without error, does NOT block, and an internal exception does not
   take down the session.
6. Document in the central catalog and development guide.

### 8.5 Universal post-creation checklist

- [ ] It works when invoked/triggered (real functional validation).
- [ ] Documented in the end-user-facing usage guide.
- [ ] Documented in the maintainer-facing development guide.
- [ ] Recorded as a state change in the project's session log.
- [ ] If it's a new reusable pattern, captured in your project's pattern registry.
- [ ] Cross-references updated.

---

## 9. Generalizable post-mortems (cross-cutting failure patterns)

### 9.1 Silent failures from unmet file/naming conventions

A harness that demands a strict convention can fail completely WITHOUT showing an error.
**Always validate functionally after creating a new component; never assume "no error
means it worked."**

### 9.2 Timestamps and IDs — never invent, never recycle

- **Never generate timestamps by guessing** — always compute them from the system's real
  time source.
- **Never use simple sequential IDs for identifiers that can be deleted and recreated** —
  if the associated state is removed and the ID gets reused, counter files that survived
  become orphaned or contaminated. Use identifiers unique by construction (timestamps with
  sufficient granularity).

### 9.3 Never delete state without persisting the critical parts first

Any "session end / temp-state cleanup" routine must, as its first step, explicitly persist
any relevant data to a durable store — and only THEN delete the temporary state.

### 9.4 Temporal metadata on decisions — never store without a date

Context/decision entries without temporal metadata become indistinguishable between
"valid" and "stale". Every persistent entry must carry an explicit date + an age-review
rule.

### 9.5 Decisions under incomplete information — "auto-classify + non-blocking correction"

When the system must decide without enough information to be 100% sure: apply the best
heuristic automatically, execute the full action, and attach a non-blocking correction
note ("Assuming X. If you preferred Y, say so.") without stopping the flow.

**Why it beats blocking:** same number of exchanges (1 round-trip) as pure
auto-classification; it doesn't interrupt high-autonomy flows; the user corrects the
residual error in their next natural message at no extra round-trip cost.
Pareto-superior in intermediate uncertainty zones.

### 9.6 Threshold heuristics with zones, not single hard limits

```
value < low_threshold              → high-confidence automatic classification (no note)
low_threshold ≤ value < high_threshold → automatic classification + correction note (§9.5)
value ≥ high_threshold             → a different automatic action (e.g., archive/clean up)
```

This avoids "cliff effects" where a tiny input change produces an abrupt behavior change.

### 9.7 Fixed labels for context-dependent decisions — an anti-pattern

Using a fixed label/title for the outcome of a classification that actually depends on
context produces systematically wrong classifications. Any decision that depends on
evaluating real context must generate its label dynamically, never via a fixed template.

---

## 10. Cross-platform gotcha — encoding in multi-platform pipelines

In systems where a script/hook receives text via stdin generated by a UTF-8 process, but
the OS/runtime decodes with a different default encoding, the result is corruption of
non-ASCII characters ("mojibake").

**Two-layer mitigation:**
1. **Preventive:** explicitly force UTF-8 decoding of the input stream at the start of the
   script.
2. **Recovery (fallback):** if the text already arrived corrupted, apply a function that
   re-encodes with the assumed wrong code page and re-decodes as UTF-8 — it is critical to
   use the EXACT code page that caused the corruption, not an approximation.

**General lesson:** when a pipeline crosses process/OS boundaries with non-ASCII text,
never assume UTF-8 by default on every platform — validate it explicitly.
