# Parking Lot

This file contains deferred, undecided, or low-priority work items.

Items here are not actively being worked on but may be promoted to `active.md` in the future.

---

## Future Enhancements

### Batch Processing Mode

```yaml
ISSUE: P-001
TYPE: TASK
TITLE: Add batch processing for multiple experiments
STATUS: TODO
PRIORITY: LOW
```

**OBJECTIVE**: Allow processing multiple experiments in a single command.

**CONTEXT**: Currently, each experiment must be processed individually via `--expt` flag or by updating `config.xlsx` to change the "latest row."

**NOTES**: Consider `sft process --all` or date range filtering.

---

### TOML Configuration Support

```yaml
ISSUE: P-002
TYPE: SPIKE
TITLE: Evaluate TOML as alternative to global_config.py
STATUS: TODO
PRIORITY: LOW
```

**OBJECTIVE**: Assess feasibility of TOML configuration for non-Python users.

**CONTEXT**: Some users may prefer declarative config over Python. However, computed values (e.g., gain calculations) would need special handling.

**NOTES**: See Decision D-2025-09-01-B for current rationale.

---

### Real-time Preview Mode

```yaml
ISSUE: P-003
TYPE: SPIKE
TITLE: Investigate real-time data preview during acquisition
STATUS: TODO
PRIORITY: LOW
```

**OBJECTIVE**: Explore feasibility of live plotting during data acquisition.

**CONTEXT**: Currently out of scope (SFT is post-processing only), but may be useful for future DAQ integration.

**NOTES**: Would require significant architecture changes.

---

### TOML Configuration Migration

```yaml
ISSUE: P-004
TYPE: TASK
TITLE: Migrate global_config.py to global_config.toml
STATUS: TODO
PRIORITY: MEDIUM
RELATED_DECISIONS:
  - D-2025-09-16-B
```

**OBJECTIVE**: Replace Python module configuration with TOML format.

**CONTEXT**:
- Using Python modules for configuration conflates code and data
- TOML provides clear separation and is human-readable
- Security concern: Python config allows arbitrary code execution
- Decided 2026-01-11 to migrate; `global_config.py` to be deprecated but maintained for backward compatibility

**NOTES**: 
- Computed values (e.g., gain calculations) need special handling in TOML
- Must maintain backward compatibility with existing `global_config.py` users
- See P-002 for related discussion on TOML evaluation

---

### Hash-Based Change Detection (Re-implementation)

```yaml
ISSUE: P-005
TYPE: TASK
TITLE: Re-implement SHA256 hash-based data change detection
STATUS: TODO
PRIORITY: MEDIUM
```

**OBJECTIVE**: Restore hash-based change detection for batch processing.

**CONTEXT**:
- Feature existed in v0.6.0: `hash/` directory stored SHA256 hashes of raw data
- Hash comparison detected added/modified data for selective reprocessing
- Feature lost during v1.0.0 restructuring (low priority at the time)
- Original implementation: 2025-04-06

**NOTES**: Consider whether to store hashes in separate directory or metadata file.

---

### Statistical Analysis for Standard Propellant Specs

```yaml
ISSUE: P-006
TYPE: TASK
TITLE: Add statistical processing for repeated experiment data
STATUS: TODO
PRIORITY: LOW
```

**OBJECTIVE**: Compute standard specifications (mean, confidence intervals, error bounds) from repeated tests of same propellant.

**CONTEXT**:
- Multiple controlled tests exist for identical propellant configurations
- Need to derive representative values with statistical significance
- Proposed 2024-12-18, deferred due to lower priority

**NOTES**: 
- Requires multiple experiments with controlled variables
- Output should include mean, standard deviation, confidence intervals
- Consider visualization of distribution
