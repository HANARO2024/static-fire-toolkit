# Active Work

This file tracks work currently in progress. Each item uses the structured ISSUE format.

---

## A-006: Docs & Project Asset Restructuring

```yaml
ISSUE: A-006
TYPE: TASK
TITLE: Docs & project asset restructuring
STATUS: IN_PROGRESS
ASSIGNEE: AI Agent (Sisyphus)
PRIORITY: MEDIUM
RELATED_DOCS:
  - README.md
  - docs/img/
  - .claude/skills/
```

**OBJECTIVE**:
  - Restructure project assets: move images to `docs/img/`, update references, add documentation sections, and register AI skill definitions

**CONTEXT**:
  - Logo and diagram images scattered under `docs/` root need consolidation into `docs/img/`
  - README lacks a "Specs & Issue Tracking" section pointing to `docs/`
  - `.claude/skills/` files define AI agent skill configurations for the project
  - IAC paper PDF to be archived under `docs/`

**NEXT_ACTIONS**:
  - Commit B: Image restructuring (`docs/img/`) + README logo path fix
  - Commit C: README "Specs & Issue Tracking" section
  - Commit E1: `.claude/skills/` files
  - Commit E2: IAC paper PDF

---

## A-007: Add Python 3.14 Classifier

```yaml
ISSUE: A-007
TYPE: TASK
TITLE: Add Python 3.14 classifier to pyproject.toml
STATUS: IN_PROGRESS
ASSIGNEE: AI Agent (Sisyphus)
PRIORITY: LOW
RELATED_DOCS:
  - pyproject.toml
```

**OBJECTIVE**:
  - Add `Programming Language :: Python :: 3.14` trove classifier to `pyproject.toml`

**CONTEXT**:
  - Python 3.14 support should be declared in package metadata
  - Single-line addition to the classifiers list

**NEXT_ACTIONS**:
  - Commit D: Add classifier line to `pyproject.toml`

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
