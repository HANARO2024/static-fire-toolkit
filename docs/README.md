# Project Documentation Index

This directory (`docs/`) contains **all authoritative, first-class project documentation**.

> **Important**
>
> Documents under /docs are **not auxiliary references**.
> They define the current state, intent, and rationale of the project and must be treated as the single source of truth.

This applies equally to **human contributors** and **automated agents** (see [`AGENTS.md`](../AGENTS.md)).

## Directory Overview

```
docs/
├── 00_context/        # Stable assumptions, constraints, invariants
├── 01_log/            # Decision & experiment logs (critical)
├── 02_work/           # Active / planned / completed work (issue tracker substitute)
├── 03_specs/          # PRD, architecture, specifications
│
├── CHANGELOG.md       # User-facing and release-level change history
├── CODE_OF_CONDUCT.md
├── logo-banner.png
├── logo-square.png
└── README.md          # You are here
```

## 1. `00_context/` — Project Assumptions & Invariants

This directory captures **facts that are assumed to be true unless explicitly revised**.

Typical contents:
- Vision and long-term intent
- Non-negotiable constraints (legal, technical, operational)
- Explicit assumptions

These documents change **infrequently**, but when they do, the impact is usually broad.

> If a change contradicts context/, a new Decision Log entry is required.

## 2. `01_log/` — Decision & Experiment Logs (Most Important)

This is the **intellectual backbone of the project**.

### `decision-log.md`

Records:
- Architectural / algorithmic decisions
- Security / cryptographic / verification choices
- Explicit decisions *not* to pursue an option

Each decision must include rationale and re-evaluation triggers.

### experiment-log.md

Records:
- Experiments, PoCs, and hypothesis testing
- Failed experiments (equally important)

If you wonder *“Why is this designed this way?”*, start here.

## 3. `02_work/` — Work Tracking (Issue Tracker Replacement)

This directory replaces Jira/Trello during the current phase.

Typical files:
- `active.md` — Work currently in progress
- `parking-lot.md` — Deferred or undecided work
- `done.md` — Completed work

Each work item is represented by a structured **ISSUE block**.

> No work should exist without a corresponding ISSUE.

⸻

## 4. `03_specs/` — Specifications & Design Artifacts

Contains formalized descriptions of the system:
- PRD (Product Requirements Document)
- Architecture descriptions
- Protocol or data-format specifications

Specifications **must align with decisions recorded in `01_log/`**.

## 5. CHANGELOG.md

`CHANGELOG.md` tracks **externally visible, release-level changes**.

Guidelines:
- Focus on user-facing or API-visible changes
- Do not duplicate internal decision or experiment logs

Internal rationale belongs in `01_log/`, not in the changelog.

## 6. CODE_OF_CONDUCT.md

Defines behavioral expectations for contributors.

This applies to:
- Human collaborators
- Maintainers
- External contributors

## How to Navigate This Documentation

If you are new to the project:
1. Read this file (`docs/README.md`)
2. Review `context/` to understand assumptions
3. Read recent entries in `log/`
4. Check `work/active.md` for current activity
5. Refer to `specs/` for formal definitions

If you are modifying the project:
- Start by locating the relevant **ISSUE** in `work/`
- Verify consistency with existing **Decision Logs**
- Update logs and specs as required

## Final Note

> This project prioritizes **traceable reasoning over raw velocity**.

If a future reader can understand *why* the system looks the way it does by reading `/docs`, then this documentation is doing its job.