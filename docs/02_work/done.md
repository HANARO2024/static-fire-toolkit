# Completed Work

This file archives completed issues. Each entry includes completion date and outputs.

---

## A-001: Initial v1.0.0 Release

```yaml
ISSUE: A-001
TYPE: TASK
TITLE: Prepare initial public release
STATUS: DONE
COMPLETED_AT: 2025-09-15
```

**OBJECTIVE**: Package and release Static-Fire Toolkit v1.0.0 to PyPI.

**OUTPUT**:
- PyPI package: `static-fire-toolkit==1.0.0`
- GitHub release with source distribution
- README with usage documentation

---

## A-002: v1.0.1 Hotfix Release

```yaml
ISSUE: A-002
TYPE: TASK
TITLE: Release v1.0.1 with minor fixes
STATUS: DONE
COMPLETED_AT: 2026-01-15
```

**OBJECTIVE**: Address minor issues discovered after v1.0.0 release.

**OUTPUT**:
- PyPI package: `static-fire-toolkit==1.0.1`
- Zenodo DOI integration
- Citation files added

---

## A-003: Unified Agent Documentation

```yaml
ISSUE: A-003
TYPE: DOC
TITLE: Consolidate AI agent rules into AGENTS.md
STATUS: DONE
COMPLETED_AT: 2026-01-19
```

**OBJECTIVE**: Create single authoritative reference for AI coding agents.

**OUTPUT**:
- `AGENTS.md` with PROJECT KNOWLEDGE BASE + WORKFLOW CONTRACT
- `CLAUDE.md` and `.cursor/rules/hanaro-sft.mdc` redirects
- PR #35 merged

---

## A-004: Documentation Backfill and Records Alignment

```yaml
ISSUE: A-004
TYPE: DOCS
TITLE: Consolidate historical documentation and release references
STATUS: DONE
COMPLETED_AT: 2026-01-23
```

**OBJECTIVE**: Consolidate historical decisions/experiments and align release references with project documentation.

**OUTPUT**:
- `docs/CHANGELOG.md` references added for releases with related logs
- `docs/01_log/decision-log.md` backfill and DECISION_TYPE corrections
- `docs/01_log/experiment-log.md` backfill entries aligned with releases
- `docs/02_work/parking-lot.md` items added for animation toggle, numba, uv
- `docs/03_specs/architecture.md` diagram alignment cleanup
- `AGENTS.md` updates for structure and type definitions

---

## A-005: Past Issues Alignment Review

```yaml
ISSUE: A-005
TYPE: DOCS
TITLE: Align docs/ with past-issues-temp.md findings
STATUS: DONE
COMPLETED_AT: 2026-02-07
```

**OBJECTIVE**: Cross-reference `docs/past-issues-temp.md` against formal `docs/` documents and fix any gaps or errors.

**OUTPUT**:
- `docs/01_log/decision-log.md`: Added D-2026-01-11 (TOML Migration) entry
- `docs/02_work/parking-lot.md`: Added D-2026-01-11 cross-reference to P-002
- `docs/CHANGELOG.md`: Added Zenodo DOI to `[Unreleased]` section
- `docs/03_specs/architecture.md`: Fixed 3 incorrect Decision ID references (PR #38)
- PR #37, PR #38 merged
