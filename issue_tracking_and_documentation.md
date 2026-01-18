# AGENTS.md

## Purpose

This document defines the **operational rules and collaboration contract** for Claude Code, Codex, and any other coding or research agents working on this repository.

The project intentionally **does NOT use Jira, Trello, or any issue tracker at this stage**.
Instead, it follows a **document-first workflow** that is:
- Human-readable and decision-oriented now
- Automatically migratable to Jira/Trello later, without information loss

Agents must treat this file as **authoritative**.

## 1. Project Management Philosophy

Agents MUST follow these principles at all times:
1. **No issue tracker is currently in use**. Do not assume Jira/Trello workflows.
2. The fundamental unit of work is an **ISSUE block in Markdown**, not a ticket.
3. Every non-trivial technical decision must include an explicit **rationale**.
4. Decisions *not* to do something are first-class outcomes.
5. Human explainability always comes before automation convenience.

## 2. Directory Structure Overview

**All authoritative project documents live under `docs/`**. Subdirectories under `docs/` are **first-class project artifacts**, not auxiliary or optional documentation.

Agents MUST treat the contents of `docs/` as the canonical source of truth for project state, decisions, and work tracking.

```
docs/
├── 00_context/        # Stable assumptions, constraints, invariants
│   ├── vision.md
│   ├── constraints.md
│   └── assumptions.md
├── 01_log/            # Decision & experiment logs (highest priority)
│   ├── decision-log.md
│   ├── experiment-log.md
│   └── daily-log/
├── 02_work/           # Active / planned / completed work (issue tracker substitute)
│   ├── active.md
│   ├── parking-lot.md
│   └── done.md
├── 03_specs/          # PRD, architecture, specifications
│   ├── prd.md
│   ├── architecture.md
│   └── glossary.md
└── README.md
```

Agents MUST prioritize **`02_work/`** and **`01_log/`** when reasoning about the project.

## 3. ISSUE Authoring Rules (CRITICAL)

### 3.1 Mandatory ISSUE Format

All work items MUST follow this structure:

```
---
ISSUE: A-001
TYPE: DESIGN | TASK | SPIKE | DOC
TITLE: Clear and concise title
STATUS: TODO | IN_PROGRESS | BLOCKED | WAITING | DONE
ASSIGNEE:
PRIORITY:
RELATED_DOCS:
  - architecture.md
---

OBJECTIVE:
  - What this work aims to achieve

CONTEXT:
  - Why this work is needed

BLOCKERS:
  - Current blocking factors (omit if none)

NEXT_ACTIONS:
  - Concrete next steps
```

### 3.2 Agent Behavior Rules

- To start new work:
  - Create or update an ISSUE block in `02_work/active.md`
- To extend or modify existing work:
  - Preserve the ISSUE ID
- Upon completion:
  - Set `STATUS: DONE`
  - Add `COMPLETED_AT` and `OUTPUT`
  - Move the ISSUE to `02_work/done.md`

Agents MUST NOT perform work without an associated ISSUE.

## 4. STATUS Semantics

| STATUS | Meaning |
| --- | --- |
| TODO | Not started |
| IN_PROGRESS | Actively being worked on |
| BLOCKED | Blocked by technical/decision/external factors |
| WAITING | Waiting for input or another task |
| DONE | Completed |

Agents MUST NOT introduce custom status values.

## 5. Decision Log Rules (`01_log/decision-log.md`)

### 5.1 When to Write a Decision Log

A decision log entry is REQUIRED when any of the following occur:
- Architecture or algorithmic choices
- Security- or verification-related decisions
- Explicit decisions *not* to pursue an option
- Any decision that may later require legal, audit, or external explanation

### 5.2 Decision Log Format

```
---
DECISION_ID: D-2026-01-14
RELATED_ISSUES:
  - A-001
DECISION_TYPE: ARCHITECTURE | SECURITY | PRODUCT
---

DECISION:
  - What was decided

RATIONALE:
  - Why this decision was made

ALTERNATIVES:
  - Considered but rejected options

REVIEW_TRIGGER:
  - Conditions that require re-evaluation
```

Agents MUST NOT record conclusions without rationale.

## 6. Experiment Log Rules (`01_log/experiment-log.md`)

All experiments, PoCs, and hypothesis tests MUST be logged.

```
---
EXPERIMENT_ID: E-2026-01-15
RELATED_ISSUES:
  - A-001
---

HYPOTHESIS:
  - What is being tested

METHOD:
  - How the experiment was conducted

RESULT:
  - Observed outcome

CONCLUSION:
  - Adoption decision and reasoning
```

Failed experiments are equally valuable and MUST be recorded.

## 7. Rules for Modifying Specifications
- When editing any document under `03_specs/`:
  - Explicitly reference the related ISSUE and/or DECISION
- If a change conflicts with an existing decision:
  - A new Decision Log entry is REQUIRED

Agents MUST NOT silently override prior decisions.

## 8. Jira / Trello Migration Awareness

Agents MUST follow these constraints to preserve future migration:
- ISSUE IDs are immutable
- Field names (`ISSUE`, `STATUS`, `TYPE`, etc.) MUST remain exact
- Prefer structured key–value blocks over free-form prose

This guarantees the following future pipeline:

```
Markdown → YAML/JSON → Jira/Trello Issues
```

## 9. Prohibited Agent Actions

Agents MUST NOT:
- Assume or introduce Jira/Trello workflows prematurely
- Make code or design changes without an ISSUE
- Make decisions justified only by intuition or preference
- Skip Decision Logs for non-trivial judgments

## 10. Git Commit Message Rules (ISSUE Integration)

All Git commits MUST comply with the rules below.
These rules apply equally to human developers and automated agents.

### 10.1 Commit Message Format (MANDATORY)

```
[ISSUE-ID] <verb>: <short summary>
```

Examples:

```
[A-001] design: compare Merkle Tree variants
[A-014] feat: add Merkle root generator
[D-2026-01-14] doc: record Merkle Tree decision
```

### 10.2 ISSUE-ID Rules
- Must be enclosed in square brackets `[]`
- Allowed ID types:
  - Work issues: `A-###`
  - Decisions: `D-YYYY-MM-DD`
  - Experiments: `E-YYYY-MM-DD`
- Exactly **one ISSUE-ID per commit**

Commits without an ISSUE-ID are forbidden.

### 10.3 Allowed Verbs

Only the following verbs are permitted:

| Verb | Meaning |
| --- | --- |
| feat | Feature addition |
| fix | Bug fix |
| design | Design or architectural change |
| refactor | Structural change without behavior change |
| doc | Documentation change |
| test | Test addition or modification |
| chore | Build, config, or maintenance |

Agents MUST NOT use vague verbs (e.g., update, change).

### 10.4 Short Summary Rules
- Maximum 72 characters
- Imperative mood
- Clearly states *what* was done

❌ Bad:

```
[A-001] update stuff
```

⭕ Good:

```
[A-001] design: document Merkle Tree trade-offs
```

### 10.5 Commit Body (Recommended)

For non-trivial, design, or security-related commits, include a body:

```
[ISSUE-ID] <verb>: <short summary>

Context:
- Why this change is needed

Details:
- What was changed and how

Notes:
- Remaining risks or follow-ups
```

The body MUST be consistent with Decision and Experiment Logs.

### 10.6 STATUS Synchronization
- Commits are allowed only when the ISSUE is `IN_PROGRESS`
- After the final commit:
  - Update ISSUE `STATUS` to `DONE`
  - Update `COMPLETED_AT` and `OUTPUT` if applicable

Agents MUST NOT leave ISSUE state stale after committing.

### 10.7 Jira Mapping Semantics

Following this commit convention enables automatic mapping:

| Git | Jira |
| --- | --- |
| [A-001] | Issue Key / External ID |
| Verb | Change Type / Activity |
| Commit Body | Issue Comment |

## 11. Ultimate Agent Objective

> Ensure that a future reader can understand *why* this system exists and *why* it is designed this way, using only Git history and Markdown documents.

This objective supersedes all concerns about speed or automation.
