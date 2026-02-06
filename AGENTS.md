# PROJECT KNOWLEDGE BASE

**Generated:** 2026-01-19
**Commit:** 987cb61
**Branch:** main

This document serves as the **authoritative reference** for AI agents (Claude Code, Codex, etc.) working on this repository. It combines technical context with workflow rules.

---

## OVERVIEW

CLI toolkit for processing static-fire test data from solid rocket motors. Python 3.10+, src-layout, PyPI-distributed as `static-fire-toolkit`. Entry point: `sft` command.

## STRUCTURE

```
./
├── src/static_fire_toolkit/     # Package source (src-layout)
│   ├── cli.py                   # CLI entry, subcommand routing
│   ├── config_loader.py         # Dynamic config from global_config.py
│   ├── style.py                 # Matplotlib style injection
│   ├── post_process/            # Thrust & pressure processing
│   └── burnrate_calc/           # Burn rate analysis (RK4 + Saint-Robert's Law)
├── examples/                    # Runnable sample data + config templates
├── docs/                        # Authoritative project docs (document-first)
└── dist/                        # Build artifacts (.whl, .tar.gz)
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add CLI subcommand | `src/static_fire_toolkit/cli.py` | Uses argparse, follow existing pattern |
| Modify data processing | `src/static_fire_toolkit/post_process/` | Thrust before pressure (sequential) |
| Change burn rate calc | `src/static_fire_toolkit/burnrate_calc/analyze_burnrate.py` | RK4 solver, curve fitting |
| Update config params | `src/static_fire_toolkit/config_loader.py` | Add to `Config` dataclass + `_load_from_python` |
| Fix plotting style | `src/static_fire_toolkit/style.py` + `hanaro_standard_stylesheet.mplstyle` | |
| Sample data/configs | `examples/` | `config.xlsx`, `global_config.py` templates |
| Project specs/decisions | `docs/` | Document-first: check here before major changes |

## PIPELINE FLOW

```
sft process -> Thrust -> Pressure -> Burnrate
               |          |          |
            _thrust_raw  _pressure_raw  pressure.csv
               |          |          |
            thrust.csv  pressure.csv  burnrate.csv + graphs
```

**Critical**: Pipeline is strictly sequential. Pressure needs thrust output. Burnrate needs pressure output.

## CODE MAP

| Symbol | Location | Role |
|--------|----------|------|
| `ThrustPostProcess` | `post_process/thrust_post_processing.py` | Voltage->thrust, LPF, PCHIP interpolation |
| `PressurePostProcess` | `post_process/pressure_post_processing.py` | Sync with thrust, baseline correction |
| `BurnRateAnalyzer` | `burnrate_calc/analyze_burnrate.py` | RK4 burnrate, Saint-Robert's Law fitting |
| `Config` | `config_loader.py` | Runtime config dataclass |
| `load_global_config()` | `config_loader.py` | Loads `global_config.py` from exec root |
| `apply_default_style()` | `style.py` | Injects matplotlib style |

## CONVENTIONS

### Python
- **Ruff** for lint+format. Google docstrings. Target Python 3.10.
- Run: `ruff check . && ruff format .`
- Ruff rules: `E1, E2, E4, E7, E9, F, W, UP, B, D` (ignore: `D100, D104, D107`)

### Testing
- **pytest** with `-q --color=yes`
- **Coverage** target: 70% minimum (omit `*/__init__.py`)
- Test path: `tests/`

### Git Strategy
- **Trunk-based development**: `main` branch protected
- **NEVER commit directly to `main`**: Always create a feature branch and submit a PR
- PRs required with CI checks passing
- Tag format: `v{major}.{minor}.{patch}` (prerelease: `a`, `b`, `rc`)
- Signed tags by default; annotated tags allowed with `--no-sign`

### Config System
- `global_config.py` in execution root (NOT package) — dynamic Python injection
- `config.xlsx` for per-experiment metadata — "latest row" processed by default
- Backward-compatible aliasing (e.g., `expt_input_voltage` -> `expt_excitation_voltage`)

### I/O Contract
- Raw inputs: `data/_thrust_raw/`, `data/_pressure_raw/`
- Outputs: `results/thrust/`, `results/pressure/`, `results/burnrate/`, `results/*_graph/`
- Filename pattern: `{TYPE}_{YYMMDD}_*.csv`

## ANTI-PATTERNS

| Do NOT | Reason |
|--------|--------|
| Edit raw CSVs in Excel | Alters encoding/delimiters silently |
| Suppress types (`# type: ignore`) | Avoid without justification |
| Skip `load_global_config()` validation | Missing load cell params must raise explicit errors |
| Process pressure before thrust | Pipeline dependency — will fail |
| Edit `expt_file_name` in config.xlsx | Auto-filled from `type` + `date` |

### Deprecated Code
- `integrate_pressure_legacy()` in `analyze_burnrate.py` — use `integrate_pressure()` instead

## COMMANDS

```bash
# Development
ruff check . && ruff format .
pytest -q                           # (tests/ not yet populated)
pre-commit install                  # Enable hooks

# CLI Usage
sft --root examples process         # Full pipeline
sft --root examples thrust          # Thrust only
sft --root examples info            # Show env/config

# Release
./tag_release.sh                    # Signed tag from pyproject.toml version
./tag_release.sh v1.0.2 --no-sign   # Annotated tag
```

## NOTES

- **No tests/ dir yet**: CI skips pytest if `tests/**/*.py` empty
- **CI matrix**: Python 3.10-3.13 x (latest deps, min constraints)
- **PyPI publish**: Only from tags on `main` branch (ancestry check enforced)
- **Load cell params required**: `sensitivity_mv_per_v`, `rated_capacity_kgf`, `gain_internal_resistance_kohm`, `gain_offset` must be set in `global_config.py`

---

# WORKFLOW CONTRACT

This section defines **operational rules** for agents working on this repository.

## Project Management Philosophy

1. **No issue tracker is currently in use**. Do not assume Jira/Trello workflows.
2. The fundamental unit of work is an **ISSUE block in Markdown**, not a ticket.
3. Every non-trivial technical decision must include an explicit **rationale**.
4. Decisions *not* to do something are first-class outcomes.
5. Human explainability always comes before automation convenience.

## Documentation Structure (`docs/`)

All authoritative project documents live under `docs/`. These are **first-class project artifacts**, not auxiliary documentation.

```
docs/
├── 00_context/        # Stable assumptions, constraints, invariants
├── 01_log/            # Decision & experiment logs (highest priority)
│   ├── decision-log.md
│   └── experiment-log.md
├── 02_work/           # Active / planned / completed work (issue tracker substitute)
│   ├── active.md
│   ├── parking-lot.md
│   └── done.md
├── 03_specs/          # PRD, architecture, specifications
├── CHANGELOG.md       # User-facing and release-level change history
├── CODE_OF_CONDUCT.md
├── logo-banner.png
├── logo-square.png
└── README.md
```

**Priority**: Agents MUST prioritize `02_work/` and `01_log/` when reasoning about the project.

## ISSUE Format

All work items MUST follow this structure:

```yaml
---
ISSUE: A-001
TYPE: DESIGN | TASK | SPIKE | DOCS
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

### STATUS Semantics

| STATUS | Meaning |
|--------|---------|
| TODO | Not started |
| IN_PROGRESS | Actively being worked on |
| BLOCKED | Blocked by technical/decision/external factors |
| WAITING | Waiting for input or another task |
| DONE | Completed |

Agents MUST NOT introduce custom status values.

### Agent Behavior Rules

Agents MUST NOT perform work without an associated ISSUE.

#### Issue Lifecycle Process (MANDATORY)

Agents MUST follow this process for **every non-trivial task**:

**Step 1 — Check for Existing Issue**
- Before starting any work, read `docs/02_work/active.md` to check if a relevant ISSUE already exists
- If an existing ISSUE covers the work → use that ISSUE ID, do NOT create a new one

**Step 2 — Create New Issue (if needed)**
- If no existing ISSUE covers the work, **propose a new ISSUE ID and summary to the user and wait for confirmation before proceeding**
- Only after user confirms: create the ISSUE block in `docs/02_work/active.md` with `STATUS: IN_PROGRESS`
- Assign the next sequential `A-###` number (check `done.md` and `active.md` for the latest used ID)

**Step 3 — Work with Issue Association**
- All commits MUST reference the ISSUE ID in the commit message (e.g., `[A-005] docs: ...`)
- To extend existing work: preserve the ISSUE ID
- If scope changes significantly during work, inform the user and update the ISSUE block

**Step 4 — Complete Issue**
- When the work is done, **propose the status change to the user and wait for confirmation before proceeding**
- Only after user confirms: set `STATUS: DONE`, add `COMPLETED_AT` and `OUTPUT` fields
- Move the completed ISSUE block from `docs/02_work/active.md` to `docs/02_work/done.md`
- Ensure `active.md` does not retain stale entries

#### User Confirmation Requirement

| Action | Requires User Confirmation |
|--------|---------------------------|
| Create new ISSUE | **YES** — propose ID + title, wait for approval |
| Change STATUS to IN_PROGRESS | **YES** — confirm before starting |
| Change STATUS to DONE | **YES** — confirm before closing |
| Change STATUS to BLOCKED/WAITING | **YES** — explain reason, wait for approval |
| Update ISSUE fields (objective, context) | No — minor updates are allowed without confirmation |

Agents MUST NOT create or close issues autonomously. The user is the authority on issue lifecycle.

## Decision Log Rules

A decision log entry (`01_log/decision-log.md`) is REQUIRED when:
- Architecture or algorithmic choices are made
- Security- or verification-related decisions occur
- Explicit decisions *not* to pursue an option
- Any decision that may later require legal, audit, or external explanation

### Decision Log Format

```yaml
---
DECISION_ID: D-2026-01-14
RELATED_ISSUES:
  - A-001
DECISION_TYPE: ALGORITHM | ARCHITECTURE | PRODUCT
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

Note:  
Some decisions are foundational and may not originate from a specific ISSUE.
RELATED_ISSUES is optional.

## Experiment Log Rules

All experiments, PoCs, and hypothesis tests MUST be logged in `01_log/experiment-log.md`.

```yaml
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

## Rules for Modifying Specifications
- When editing any document under `03_specs/`:
  - Explicitly reference the related ISSUE and/or DECISION
- If a change conflicts with an existing decision:
  - A new Decision Log entry is REQUIRED

Agents MUST NOT silently override prior decisions.

## Git Commit Message Rules

### Format (MANDATORY)

```
[ISSUE-ID] <verb>: <short summary>
```

Examples:
```
[A-001] design: compare Merkle Tree variants
[A-014] feat: add Merkle root generator
[D-2026-01-14] doc: record Merkle Tree decision
```

### ISSUE-ID Rules
- Must be enclosed in square brackets `[]`
- Allowed ID types: `A-###` (work), `D-YYYY-MM-DD` (decision), `E-YYYY-MM-DD` (experiment)
- Exactly **one ISSUE-ID per commit**

### Allowed Verbs

| Verb | Meaning |
|------|---------|
| feat | Feature addition |
| fix | Bug fix |
| perf | Performance improvement |
| design | Design or architectural change |
| refactor | Structural change without behavior change |
| docs | Documentation change |
| test | Test addition or modification |
| chore | Build, config, or maintenance |
| ci | CI configuration |

Agents MUST NOT use vague verbs (e.g., update, change).

### Short Summary Rules
- Maximum 72 characters
- Imperative mood
- Clearly states *what* was done

### Commit Body (Recommended for non-trivial commits)

```
[ISSUE-ID] <verb>: <short summary>

Context:
- Why this change is needed

Details:
- What was changed and how

Notes:
- Remaining risks or follow-ups
```

## Prohibited Agent Actions

Agents MUST NOT:
- **Commit directly to `main` branch** — always use feature branches and PRs
- **Push to remote without explicit user instruction** — local commits are fine, but `git push` requires explicit approval
- Assume or introduce Jira/Trello workflows prematurely
- Make code or design changes without an ISSUE
- Make decisions justified only by intuition or preference
- Skip Decision Logs for non-trivial judgments
- Silently override prior decisions

## Migration Awareness

To preserve future Jira/Trello migration:
- ISSUE IDs are immutable
- Field names (`ISSUE`, `STATUS`, `TYPE`, etc.) MUST remain exact
- Prefer structured key-value blocks over free-form prose

## Ultimate Objective

> Ensure that a future reader can understand *why* this system exists and *why* it is designed this way, using only Git history and Markdown documents.

This objective supersedes all concerns about speed or automation.
