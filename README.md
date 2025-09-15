# HANARO SFT (Static-Fire Toolkit)

![HANARO SFT Logo](./docs/logo.svg)

**HANARO SFT (Static-Fire Toolkit)** is an open-source command-line toolkit developed by the [Seoul National University Rocket Team **HANARO**](https://hanaro.snu.ac.kr/).  
It provides a standardized workflow for processing **static-fire test data** from amateur and research rocket motors, focusing on **data cleaning, performance analysis, burn rate estimation, and visualization**.

While the library can later be imported in Python, the **initial releases focus on the CLI interface**, making it straightforward to use as a standalone tool in test workflows.

## Features
- **CLI-based workflow** — run analysis directly from the terminal  
- **Data processing** — clean and normalize raw thrust/pressure sensor logs  
- **Performance metrics** — compute impulse, burn time, chamber pressure statistics  
- **Burn rate estimation** — regression-based analysis for solid propellants  
- **Visualization** — generate thrust/pressure plots for reports and documentation  

## Installation

From PyPI:

```bash
pip install static-fire-toolkit
```

Or install from source:

```bash
git clone https://github.com/snu-hanaro/static-fire-toolkit.git
cd static-fire-toolkit
pip install -e .
```

## Usage

### Recommended Directory Layout

```sh
root/                        # run sft here
├─ config.xlsx
├─ data/
│  ├─ _pressure_raw/         # input pressure raw CSVs (semicolon-delimited)
│  └─ _thrust_raw/           # input thrust raw CSVs
├─ results/
│  ├─ burnrate/              # calculated burnrate CSVs
│  ├─ burnrate_graph/        # burnrate PNG/GIF plots
│  ├─ pressure/              # processed pressure CSVs
│  ├─ pressure_graph/        # pressure PNG plots
│  ├─ thrust/                # processed thrust CSVs
│  └─ thrust_graph/          # thrust PNG plots
└─ logs/
```

The manual assumes a “ground test” directory that contains `data/_pressure_raw`, `data/_thrust_raw`, and `config.xlsx`.

### Requirements
- Python 3 (3.9+ recommended)
- Packages:
  - numpy (>=2.0)
  - scipy (>=1.10)
  - pandas (>=2.0)
  - matplotlib (>=3.7)

### CLI
Basic workflow:

```bash
# Process raw static-fire CSV data and compute performance metrics
sft process KNSB_250220 --output results/

# Estimate burn rate
sft burnrate KNSB_250220

# Estimate burn rate from multiple tests
sft burnrate raw_data/*.csv --propellant knsb --output burnrate_report.csv
```

Run sft --help for a full list of commands and options.

### Data I/O Format & Processing Pipeline
- **Inputs**:
  - Raw Thrust Data: CSV
  - Raw Pressure Data: CSV
- **Outputs**:
  - Uniform-step processed CSVs at Δt = 0.01 s: `time` + `thrust [N]` or `pressure [bar]`
  - PNG plots of thrust and pressure curves
- **Filtering**:
  - Thrust → low-pass filter + Gaussian smoothing
  - Pressure → no filter (typically smooth enough)
- **Pressure Normalization**: adjust for local vs. standard atmospheric pressure at test time
- **Config**: `config.xlsx` stores test conditions (date/nozzle/grain, etc.)

> [!NOTE]
> **File-Naming Summary**:
> - Thrust raw: `TYPE_YYMMDD_thrust_raw.csv`
> - Thrust outputs: `TYPE_YYMMDD_thrust.csv`, `TYPE_YYMMDD_thrust.png`
> - Pressure raw: `TYPE_YYMMDD_pressure_raw.csv`
> - Pressure outputs: `TYPE_YYMMDD_pressure.csv`, `TYPE_YYMMDD_pressure.png`

### Thrust Data Processing
#### Thrust raw (`data/_thrust_raw/`)
- Filename: `TYPE_YYMMDD_thrust_raw.csv` (e.g., `KNSB_250220_thrust_raw.csv`)
- Format: comma-separated, 2 columns
	1. time (s)
    2. voltage (V) (pre-calibration, 1:1 to thrust after calibration)
- Important: treat raw CSV as read-only. Re-saving in third-party editor such as Excel may change encoding/separators.

Example (excerpt):

```csv
246.42052460007835,1.34765625
246.42483200004790,1.455078125
```

#### Pipeline
1. Read the latest test row from config.xlsx
2. Load the matching raw thrust CSV from _thrust_raw/
3. Extract combustion window; handle spikes/outliers
4. PCHIP interpolation to Δt=0.01 s
5. Apply low-pass + Gaussian filters
6. Save processed thrust CSV → thrust_post_process/TYPE_YYMMDD_thrust.csv
7. Save thrust plot PNG → thrust_graph/TYPE_YYMMDD_thrust.png

#### Output CSV schema

| time [s] | thrust [N] |
| :--- | :--- |
| 0.00 | 2.757… |
| 0.01 | 16.772… |
| 0.02 | 32.070… |
| … | … |

### Pressure Data Processing
#### Pressure raw (`data/_pressure_raw/`)
- Filename: `TYPE_YYMMDD_pressure_raw.csv`
- Format: semicolon-separated, 4 columns
Header: Datetime;Battery Level (%);5600 Pressure (Bar);5600 Temperature (°C)
This project uses Datetime and Pressure (Bar).
- Important: delimiter is semicolon (`;`).

Example (header + excerpt):

```csv
Datetime;Battery Level (%);5600 Pressure (Bar);5600 Temperature (°C)
2025.2.20 22:34;100;1.159;0.7
2025.2.20 22:34;100;1.132;0.7
```

#### Pipeline
1. Read the latest test row from config.xlsx
2. Load the matching raw pressure CSV from _pressure_raw/ (semicolon delimiter)
3. Load the processed thrust CSV to synchronize burn window
4. PCHIP interpolation to Δt=0.01 s
5. Atmospheric correction: adjust for local vs. standard atmospheric pressure at test time
6. No filtering (pressure changes are typically smooth)
7. Save processed pressure CSV → pressure_post_process/TYPE_YYMMDD_pressure.csv
8. Save pressure plot PNG → pressure_graph/TYPE_YYMMDD_pressure.png

#### Output CSV schema

| time [s] | pressure [bar] |
| :--- | :--- |
| 0.00 | 1.447… |
| 0.01 | 1.500… |
| 0.02 | 1.560… |
| … | … |

### Configuration: `config.xlsx`
Record one row per test; the latest row is processed by default. Suggested columns:

| Column | Description | Example |
| :--- | :--- | :--- |
| index | Zero-based test index	| 17 |
| date | Date in YYMMDD | 250220 |
| type | Propellant type | KNSB |
| expt_input_voltage [V] | DAQ input voltage | 11.94 |
| expt_resistance [Ohm] | DAQ potentiometer resistance | 200.6 |
| totalmass [g] | Propellant total mass | 5014.5 |
| Nozzlediameter [mm] | Throat diameter | 20 |
| Outerdiameter [mm] | Grain OD | 89 |
| Innerdiameter [mm] | Grain ID | 30 |
| singlegrainheight [mm] | Single grain height | 106.3 |
| segment | Grain count | 5 |

expt_file_name (if present) is auto-filled — do not edit. Notes/remarks are optional.

## Troubleshooting & Best Practices
- Never edit raw CSVs. Excel re-save can alter encoding/delimiters → corrupted data. Keep raw files read-only.
- Remember the pressure delimiter is ;. Configure your CSV reader accordingly.
- “Latest row” logic. The scripts process the most recent test by default. To reprocess an older test, update config.xlsx or pass CLI arguments.
- Debugging order: follow the stage order — load → windowing → interpolation → filters → correction → save. Most issues are path/filename mismatches, delimiter/headers, or NaNs from partial rows.
- Reproducibility: do not overwrite raw CSVs; version config.xlsx; keep outputs auto-versioned by type/date in filenames.

## FAQ
### Q1. Why filter thrust but not pressure?
Thrust often contains transient spikes/noise (mechanical shocks, DAQ artifacts), so smoothing helps. Pressure changes are typically gradual; avoiding filters prevents distortion of real variations.

### Q2. What does the pressure correction do?
It compensates for the difference between local atmospheric pressure at test time and standard atmosphere, enabling apples-to-apples comparisons across sessions.

## Development

### Tools used
- Ruff: linting & formatting
- pytest: testing
- coverage: test coverage reports
- pre-commit — enforce style checks before commits
- GitHub Actions — CI/CD (matrix testing across Python 3.9–3.13)

### Local setup

```bash
# Run linting
ruff check .
ruff format .

# Run tests
pytest -q
```

### CI/CD Strategy
- Branching: trunk-based development (main protected)
- Matrix testing: Python 3.9–3.13, both latest and minimum dependencies
- Tags:
  - Signed tags by default
  - Annotated tags allowed with --no-sign
  - Structured tag messages including Summary / Highlights / Breaking / Fixes / Docs / Thanks / Artifacts

## Contributing

Please use Issues/PRs with templates. Recommended:
- Feature request & bug report templates
- Code style (e.g., black, ruff) & type hints
- Sample data policy (strip sensitive metadata)

## Authors & Maintainers
- Authors: Seoul National University Rocket Team HANARO
- Main Maintainer: @yunseo-kim

## License

This project is licensed under the [MIT License](/LICENSE).
