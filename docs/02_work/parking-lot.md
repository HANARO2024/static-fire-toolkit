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
