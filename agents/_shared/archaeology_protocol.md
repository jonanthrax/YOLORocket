# Archaeology Protocol (shared across all archaeologist agents)

**Used by:** design-archaeologist, math-archaeologist, oracle-archaeologist

This document is the single-source-of-truth for rules that apply to ALL archaeologist
agents. When a rule here conflicts with an older copy in an individual agent file, THIS
document wins. Update here ONLY; agent files inherit via their Protocol reference line.

---

## ANTI-TOKEN-OVERFLOW PROTOCOL (R1-R7)

These rules are MANDATORY for all exploration work:

**R1: NEVER return full file contents** to the main context. Summarize findings.

**R2: Write findings DIRECTLY** to the designated output file. The main context receives
only a confirmation: "Written section X, ~N lines, M patterns found."

**R3: Output file location** — write to:
`docs/arq/archaeology/YYYY_MM_DD_<TEMA>_<DOMAIN>.md`
where `<DOMAIN>` is the suffix declared in the individual agent (DESIGN, MATH, ORACLE,
etc.). If findings relate to an existing living doc (e.g., `MATH_AUDIT.md`), append to
it instead of creating a new file; ask the main context which approach to use.

**R4: Parallelize** when exploring multiple directories/projects. Max 4 sub-searches.

**R5: Condensation** — if you MUST return data to main context, max 10 lines summary.

**R6: Never read files >50 LOC into your response verbatim**. Extract signatures,
measurements, quotes, or patterns relevant to your domain — never raw file dumps.

**R7: Honor explicit exclusions.** If the user or project doctrine marks a path as
off-limits for exploration (deprecated fork, prohibited legacy tree, etc.), respect it
verbatim and state which rule/decision excludes it. Never read/grep/glob an excluded
path — not even to confirm it exists. Historical references to excluded paths in past
session logs are preserved as evidence, but must not be re-explored.

---

## WHERE TO SEARCH

**NEVER assume a default path.** The search location is:

1. **Explicit** — user provides a path or names the target codebase/document set
2. **Inferred** — conversation already established the target
3. **Asked** — if ambiguous, ASK: "Where should I excavate? Provide the path."

You are an archaeologist anywhere. You gain experience, but you don't settle in one place.
