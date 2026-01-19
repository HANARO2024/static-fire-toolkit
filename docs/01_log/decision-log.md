# Decision Log

This document records significant architectural, algorithmic, and product decisions.

Each entry must include:
- **DECISION**: What was decided
- **RATIONALE**: Why this decision was made
- **ALTERNATIVES**: Options that were considered but rejected
- **REVIEW_TRIGGER**: Conditions that would require re-evaluation

- - -

## D-2025-01-21: Experiment Configuration in xlsx Format

---
DECISION_ID: D-2025-01-21
DECISION_TYPE: ARCHITECTURE
---

**DECISION**: Use `config.xlsx` (Excel workbook) for per-experiment configuration instead of `config.ini` or CSV.

**RATIONALE**:
- **Preserves historical data**: Previously, `config.ini` was overwritten each experiment, losing past parameter values. Recovering old values required searching through chat logs or notes.
- **Structured record-keeping**: Each experiment gets its own row, enabling systematic tracking of grain/motor parameters (OuterDiameter, InnerDiameter, SingleGrainHeight, TotalMass, Segment) that vary per test.
- **Batch processing ready**: Row-based structure anticipates future multi-experiment processing.
- **Encoding stability**: CSV files opened and saved in Excel on Windows often have encoding issues (UTF-8 → CP949/ANSI corruption). xlsx format avoids this problem since it's a binary format with consistent encoding.
- **Human-editable**: Configuration must be manually entered by operators — xlsx provides a familiar spreadsheet interface.

**ALTERNATIVES**:
- `config.ini` (rejected: overwrites lose history, no batch capability)
- CSV (rejected: encoding corruption when edited in Excel on Windows)
- TOML/YAML (rejected: less familiar to non-developer users)

**REVIEW_TRIGGER**: If automated configuration generation from external systems is required.

- - -

## D-2025-01-21-B: Generic Configuration Filename

---
DECISION_ID: D-2025-01-21-B
DECISION_TYPE: ARCHITECTURE
---

**DECISION**: Use generic filename `config.xlsx` rather than project-specific names (e.g., `KHAOS_grain.xlsx`).

**RATIONALE**:
- **Separation of config and code**: When switching projects, users copy the `examples/` directory structure and replace contents. Hardcoded filenames like `KHAOS_grain.xlsx` would require source code edits to change to `Identity3_grain.xlsx`.
- **Minimize code modifications**: Code changes should be limited to improvements and bug fixes, not per-project customization.
- **PEP 8 compliance**: Lowercase filename with underscores follows Python naming conventions.

**ALTERNATIVES**:
- Project-specific filenames (rejected: requires code changes per project)
- Environment variable for filename (rejected: unnecessary complexity for simple use case)

**REVIEW_TRIGGER**: If multiple config files per project become necessary.

- - -

## D-2025-09-13: src-layout Package Structure

---
DECISION_ID: D-2025-09-13
DECISION_TYPE: ARCHITECTURE
---

**DECISION**: Use src-layout (`src/static_fire_toolkit/`) instead of flat layout.

**RATIONALE**:
- Prevents accidental imports from project root during development
- Ensures installed package behavior matches development behavior
- Aligns with modern Python packaging best practices (PEP 621)

**ALTERNATIVES**:
- Flat layout (rejected: import confusion during development)
- Namespace packages (rejected: unnecessary complexity for single package)

**REVIEW_TRIGGER**: If monorepo structure is adopted with multiple packages.

- - -

## D-2025-09-01: Dynamic Python Configuration

---
DECISION_ID: D-2025-09-01-B
DECISION_TYPE: ARCHITECTURE
---

**DECISION**: Use `global_config.py` (Python module) for runtime configuration instead of TOML/YAML.

**RATIONALE**:
- Allows Python expressions (e.g., gain calculations based on resistance values)
- Users can import and extend configuration programmatically
- No additional parsing dependencies required

**ALTERNATIVES**:
- TOML configuration (rejected: cannot express computed values)
- Environment variables (rejected: poor UX for complex multi-parameter config)

**REVIEW_TRIGGER**: If configuration needs to be shared with non-Python tools.

- - -

## D-2025-09-15: Sequential Pipeline Architecture

---
DECISION_ID: D-2025-09-15
DECISION_TYPE: ARCHITECTURE
---

**DECISION**: Implement processing as strictly sequential stages: Thrust -> Pressure -> Burnrate.

**RATIONALE**:
- Each stage depends on outputs from the previous stage
- Pressure windowing requires processed thrust data
- Burnrate analysis requires synchronized pressure data
- Simplifies debugging and intermediate inspection

**ALTERNATIVES**:
- Parallel processing (rejected: data dependencies prevent true parallelism)
- Single monolithic function (rejected: harder to debug and extend)

**REVIEW_TRIGGER**: If real-time processing requirements emerge.

- - -

## D-2026-01-19: Unified Agent Rules Document

---
DECISION_ID: D-2026-01-19
DECISION_TYPE: ARCHITECTURE
---

**DECISION**: Consolidate all AI agent configuration into single `AGENTS.md` file.

**RATIONALE**:
- Single source of truth prevents inconsistencies
- Reduces maintenance burden across multiple config files
- AI agents load fewer files, reducing context fragmentation

**ALTERNATIVES**:
- Multiple specialized files (rejected: sync burden, duplication risk)
- Embedded in code comments (rejected: not discoverable by agents)

**REVIEW_TRIGGER**: If AGENTS.md exceeds 600 lines or tool-specific rules diverge significantly.
