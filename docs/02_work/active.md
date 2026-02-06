# Active Work

This file tracks work currently in progress. Each item uses the structured ISSUE format.

---

## A-005: Past Issues Alignment Review

```yaml
ISSUE: A-005
TYPE: DOCS
TITLE: Align docs/ with past-issues-temp.md findings
STATUS: IN_PROGRESS
ASSIGNEE: AI Agent (Sisyphus)
PRIORITY: MEDIUM
RELATED_DOCS:
  - docs/past-issues-temp.md
  - docs/01_log/decision-log.md
  - docs/02_work/parking-lot.md
  - docs/CHANGELOG.md
```

**OBJECTIVE**:
  - Cross-reference `docs/past-issues-temp.md` against formal `docs/` documents and fix any gaps or errors

**CONTEXT**:
  - `past-issues-temp.md` contains the canonical history of project issues and decisions in informal format
  - Formal docs (`decision-log.md`, `CHANGELOG.md`, `parking-lot.md`) should reflect all items from this source
  - Review identified two gaps: missing D-2026-01-11 decision log entry and missing Zenodo DOI in CHANGELOG `[Unreleased]`

**NEXT_ACTIONS**:
  - PR #37 under review — merge upon approval
  - After merge, move this issue to `done.md`

<!-- 
Template for new issues:

---
ISSUE: A-XXX
TYPE: TASK
TITLE: 
STATUS: IN_PROGRESS
ASSIGNEE: 
PRIORITY: 
RELATED_DOCS: []
---

OBJECTIVE:
  - 

CONTEXT:
  - 

NEXT_ACTIONS:
  - 

-->
