# PROJECT KNOWLEDGE BASE

**Generated:** 2026-01-19
**Commit:** 987cb61
**Branch:** main

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
sft process → Thrust → Pressure → Burnrate
              ↓          ↓          ↓
           _thrust_raw  _pressure_raw  pressure.csv
              ↓          ↓          ↓
           thrust.csv  pressure.csv  burnrate.csv + graphs
```

**Critical**: Pipeline is strictly sequential. Pressure needs thrust output. Burnrate needs pressure output.

## CODE MAP

| Symbol | Location | Role |
|--------|----------|------|
| `ThrustPostProcess` | `post_process/thrust_post_processing.py` | Voltage→thrust, LPF, PCHIP interpolation |
| `PressurePostProcess` | `post_process/pressure_post_processing.py` | Sync with thrust, baseline correction |
| `BurnRateAnalyzer` | `burnrate_calc/analyze_burnrate.py` | RK4 burnrate, Saint-Robert's Law fitting |
| `Config` | `config_loader.py` | Runtime config dataclass |
| `load_global_config()` | `config_loader.py` | Loads `global_config.py` from exec root |
| `apply_default_style()` | `style.py` | Injects matplotlib style |

## CONVENTIONS

### Python
- **Ruff** for lint+format. Google docstrings. Target Python 3.10.
- Run: `ruff check . && ruff format .`

### Config System
- `global_config.py` in execution root (NOT package) — dynamic Python injection
- `config.xlsx` for per-experiment metadata — "latest row" processed by default
- Backward-compatible aliasing (e.g., `expt_input_voltage` → `expt_excitation_voltage`)

### I/O Contract
- Raw inputs: `data/_thrust_raw/`, `data/_pressure_raw/`
- Outputs: `results/thrust/`, `results/pressure/`, `results/burnrate/`, `results/*_graph/`
- Filename pattern: `{TYPE}_{YYMMDD}_*.csv`

## ANTI-PATTERNS

| Do NOT | Reason |
|--------|--------|
| Edit raw CSVs in Excel | Alters encoding/delimiters silently |
| Suppress types (`as any`, `@ts-ignore`) | N/A (Python) but avoid `# type: ignore` without justification |
| Skip `load_global_config()` validation | Missing load cell params must raise explicit errors |
| Process pressure before thrust | Pipeline dependency — will fail |
| Edit `expt_file_name` in config.xlsx | Auto-filled from `type` + `date` |

### Deprecated Code
- `integrate_pressure_legacy()` in `analyze_burnrate.py` — use `integrate_pressure()` instead

## UNIQUE STYLES

- **Document-first**: `docs/` is authoritative. Check `docs/01_log/` for decision rationale.
- **Dynamic config**: `global_config.py` allows Python expressions (e.g., gain calculations)
- **Excel as DB**: `config.xlsx` stores experiment metadata; CLI processes "latest row"
- **Signed releases**: `tag_release.sh` creates signed tags with structured messages

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
- **CI matrix**: Python 3.10–3.13 × (latest deps, min constraints)
- **PyPI publish**: Only from tags on `main` branch (ancestry check enforced)
- **Load cell params required**: `sensitivity_mv_per_v`, `rated_capacity_kgf`, `gain_internal_resistance_kohm`, `gain_offset` must be set in `global_config.py`
