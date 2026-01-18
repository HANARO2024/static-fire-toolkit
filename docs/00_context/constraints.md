# Constraints

## Technical Constraints

### Python Version
- **Minimum**: Python 3.10
- **Tested**: Python 3.10, 3.11, 3.12, 3.13
- **Rationale**: Modern type hints, structural pattern matching, and dependency compatibility

### Dependencies
Core dependencies are intentionally minimal:
- `numpy>=2.0` - Numerical operations
- `scipy>=1.10` - Signal processing (filters, interpolation)
- `pandas>=2.0` - Data manipulation, Excel I/O
- `matplotlib>=3.10` - Visualization
- `openpyxl>=3.1` - Excel file support for pandas

### Package Layout
- **src-layout**: All package code under `src/static_fire_toolkit/`
- **Rationale**: Prevents accidental imports from the project root during development

### Configuration
- `global_config.py` must exist in execution root (NOT in the package)
- Load cell parameters are **required** and must be explicitly set:
  - `sensitivity_mv_per_v`
  - `rated_capacity_kgf`
  - `gain_internal_resistance_kohm`
  - `gain_offset`

## Operational Constraints

### Pipeline Order
Processing stages **must** run in order:
1. Thrust (raw voltage to force conversion)
2. Pressure (synchronization with thrust window)
3. Burnrate (analysis using pressure data)

Skipping or reordering stages will cause failures.

### Data Integrity
- Raw CSV files must not be edited in Excel (encoding/delimiter corruption)
- `expt_file_name` in `config.xlsx` is auto-generated; do not manually edit

## Distribution Constraints

### PyPI
- Package name: `static-fire-toolkit`
- Entry point: `sft` command
- Releases only from tags on `main` branch

### Versioning
- Follows Semantic Versioning (SemVer)
- Tag format: `v{major}.{minor}.{patch}`
- Prerelease suffixes: `a`, `b`, `rc`
