# Decision Log

This document records significant architectural, algorithmic, and product decisions.

Each entry must include:
- **DECISION**: What was decided
- **RATIONALE**: Why this decision was made
- **ALTERNATIVES**: Options that were considered but rejected
- **REVIEW_TRIGGER**: Conditions that would require re-evaluation

---

## D-2025-09-01: src-layout Package Structure

```yaml
DECISION_ID: D-2025-09-01
DECISION_TYPE: ARCHITECTURE
```

**DECISION**: Use src-layout (`src/static_fire_toolkit/`) instead of flat layout.

**RATIONALE**:
- Prevents accidental imports from project root during development
- Ensures installed package behavior matches development behavior
- Aligns with modern Python packaging best practices (PEP 621)

**ALTERNATIVES**:
- Flat layout (rejected: import confusion during development)
- Namespace packages (rejected: unnecessary complexity for single package)

**REVIEW_TRIGGER**: If monorepo structure is adopted with multiple packages.

---

## D-2025-09-01: Dynamic Python Configuration

```yaml
DECISION_ID: D-2025-09-01-B
DECISION_TYPE: ARCHITECTURE
```

**DECISION**: Use `global_config.py` (Python module) for runtime configuration instead of TOML/YAML.

**RATIONALE**:
- Allows Python expressions (e.g., gain calculations based on resistance values)
- Users can import and extend configuration programmatically
- No additional parsing dependencies required

**ALTERNATIVES**:
- TOML configuration (rejected: cannot express computed values)
- Environment variables (rejected: poor UX for complex multi-parameter config)

**REVIEW_TRIGGER**: If configuration needs to be shared with non-Python tools.

---

## D-2025-09-15: Sequential Pipeline Architecture

```yaml
DECISION_ID: D-2025-09-15
DECISION_TYPE: ARCHITECTURE
```

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

---

## D-2026-01-19: Unified Agent Rules Document

```yaml
DECISION_ID: D-2026-01-19
DECISION_TYPE: ARCHITECTURE
```

**DECISION**: Consolidate all AI agent configuration into single `AGENTS.md` file.

**RATIONALE**:
- Single source of truth prevents inconsistencies
- Reduces maintenance burden across multiple config files
- AI agents load fewer files, reducing context fragmentation

**ALTERNATIVES**:
- Multiple specialized files (rejected: sync burden, duplication risk)
- Embedded in code comments (rejected: not discoverable by agents)

**REVIEW_TRIGGER**: If AGENTS.md exceeds 600 lines or tool-specific rules diverge significantly.
