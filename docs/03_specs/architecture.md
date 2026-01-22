# Architecture

## Overview

Static-Fire Toolkit follows a **pipeline architecture** with three sequential processing stages, orchestrated by a CLI interface.

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLI Layer                               │
│                        (cli.py)                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │ thrust   │  │ pressure │  │ burnrate │  │ process  │         │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘         │
└───────┼─────────────┼─────────────┼─────────────┼───────────────┘
        │             │             │             │
        ▼             ▼             ▼             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Processing Layer                               │
│                                                                     │
│  ┌──────────────────┐   ┌───────────────────┐   ┌─────────────────┐ │
│  │ ThrustPostProcess│──▶│PressurePostProcess│──▶│ BurnRateAnalyzer│ │
│  └──────────────────┘   └───────────────────┘   └─────────────────┘ │
│          │                     │                     │              │
│          ▼                     ▼                     ▼              │
│     thrust.csv           pressure.csv            burnrate.csv       │
│     thrust.png           pressure.png            burnrate.png       │
└─────────────────────────────────────────────────────────────────────┘
        ▲                                               
        │                                               
┌───────┴────────────────────────────────────────────────────────────┐
│                    Configuration Layer                             │
│                                                                    │
│  ┌──────────────────┐         ┌─────────────────┐                  │
│  │ global_config.py │         │   config.xlsx   │                  │
│  │ (runtime params) │         │(per-test params)│                  │
│  └──────────────────┘         └─────────────────┘                  │
│           │                          │                             │
│           ▼                          ▼                             │
│  ┌──────────────────────────────────────────────┐                  │
│  │              config_loader.py                │                  │
│  │         (Config dataclass + loader)          │                  │
│  └──────────────────────────────────────────────┘                  │
└────────────────────────────────────────────────────────────────────┘
```

## Components

### CLI Layer (`cli.py`)

Entry point for all user interactions. Provides subcommands:
- `sft thrust` - Run thrust processing only
- `sft pressure` - Run pressure processing only
- `sft burnrate` - Run burn rate analysis only
- `sft process` - Run full pipeline (thrust -> pressure -> burnrate)
- `sft info` - Display environment and configuration info

### Processing Layer

#### ThrustPostProcess (`post_process/thrust_post_processing.py`)

**Input**: Raw voltage data from load cell

**Processing Steps**:
1. Parse CSV with configurable delimiter/header
2. Convert voltage to force using load cell calibration
3. Detect combustion window (start/end) using gradient criteria
4. Resample to uniform time steps (PCHIP interpolation)
5. Apply Butterworth low-pass filter
6. Apply Gaussian smoothing for derivative estimation

**Output**: `thrust.csv`, `thrust.png`

#### PressurePostProcess (`post_process/pressure_post_processing.py`)

**Input**: Raw pressure data + processed thrust data

**Processing Steps**:
1. Parse CSV with configurable delimiter/header
2. Align pressure data to thrust combustion window
3. Resample to uniform time steps (PCHIP interpolation)
4. Apply atmospheric pressure correction
5. Optional low-pass filtering

**Output**: `pressure.csv`, `pressure.png`

#### BurnRateAnalyzer (`burnrate_calc/analyze_burnrate.py`)

**Input**: Processed pressure data + grain geometry

**Processing Steps**:
1. Load pressure data and grain parameters
2. Compute regression rate using RK4 integration
3. Fit Saint-Robert's Law (`r = a * P^n`) to data
4. Generate burn rate vs. pressure curves
5. Create animated visualization of grain regression

**Output**: `burnrate.csv`, burn rate plots, animation GIF

### Configuration Layer

#### `global_config.py`

Python module loaded at runtime. Contains:
- Load cell calibration parameters (required)
- Signal processing parameters (optional, with defaults)
- CSV parsing options (optional, with defaults)

#### `config.xlsx`

Excel workbook with per-experiment metadata:
- Test date and propellant type
- Grain geometry (OD, ID, height, segments)
- DAQ settings (excitation voltage, resistance)

#### `config_loader.py`

Loads and validates configuration:
- Parses `global_config.py` using `importlib`
- Supports legacy attribute names for backward compatibility
- Returns frozen `Config` dataclass

## Data Flow

```
Raw Data                    Processed Data              Analysis Output
─────────────────────────────────────────────────────────────────────────
data/_thrust_raw/     ──▶   results/thrust/       ──▶   (used by pressure)
  KNSB_250220_*.csv         KNSB_250220_thrust.csv
                            KNSB_250220_thrust.png

data/_pressure_raw/   ──▶   results/pressure/     ──▶   (used by burnrate)
  KNSB_250220_*.csv         KNSB_250220_pressure.csv
                            KNSB_250220_pressure.png

                            results/burnrate/
                              KNSB_250220_burnrate.csv
                            results/burnrate_graph/
                              KNSB_250220_burnrate.png
                              KNSB_250220_burnrate_animation.gif
```

## Key Design Decisions

See `docs/01_log/decision-log.md` for rationale on:
- D-2025-09-01: src-layout package structure
- D-2025-09-01-B: Python-based configuration
- D-2025-09-15: Sequential pipeline architecture
