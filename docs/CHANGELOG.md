# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2025-09-19

### Added

- **Initial public release on PyPI**
- CLI entry point provided: the script can now be executed globally via `sft` command

### Changed

- **Project is now open source under the MIT License — contributions are welcome!**

- **Breaking:** Update default data I/O directory structure
  - **Input**
    - was: `_pressure_raw/`, `_thrust_raw/`
    - now: `data/_pressure_raw/`, `data/_thrust_raw/`
  - **Output**
    - was:  
      - `burnrate_calc/burnrate/`  
      - `burnrate_calc/burnrate_graph/`  
      - `pressure_graph/`  
      - `pressure_post_process/`  
      - `thrust_graph/`  
      - `thrust_post_process/`
    - now:  
      - `results/burnrate/`  
      - `results/burnrate_graph/`  
      - `results/pressure/`  
      - `results/pressure_graph/`  
      - `results/thrust/`  
      - `results/thrust_graph/`

- **Breaking:** Rename `config.py` to `global_config.py` to clearly distinguish it from `config.xlsx`

- **Breaking:** Add new configuration options in `global_config` to control raw data parsing:  
  - `thrust_sep`, `pressure_sep`: CSV delimiters  
  - `thrust_header`, `pressure_header`: header row indices

- **Breaking:** Raw thrust/pressure data parsing no longer relies on hardcoded column names/indices.  
  Instead, `global_config` now provides:  
  - `thrust_time_col_idx`, `thrust_col_idx`  
  - `pressure_time_col_idx`, `pressure_col_idx`

- **Breaking:** `global_config` requires explicit load cell parameters for voltage → thrust conversion:  
  - `sensitivity_mv_per_v` (replaces `rated_output`)  
  - `rated_capacity_kgf` (replaces `rated_load`)  
  - `gain_internal_resistance_kohm`  
  - `gain_offset`  

  Missing values will now raise an explicit error. Load cell constants previously hardcoded are now fully parameterized, making the package usable as a public library rather than team-internal only.

- `config.xlsx`: Rename variable `expt_input_voltage [V]` → `expt_excitation_voltage [V]`  
  (legacy alias maintained for backward compatibility)

- Adjust thrust/pressure graph output formatting

### Fixed
- Fixed an issue where `global_config.py` (formerly `config.py`) was not loaded correctly when the tool was executed from certain directories.

### Development

- Migrate to Git-based version control
- Adopt ruff as linter and formatter
- Add project-level Cursor rule sets, ensuring consistency when using AI-based tools like Cursor IDE

## 0.6.0 - 2025-04-06
Updated by Yunseo Kim (yunseo@snu.ac.kr)

### Added

- Add hash-based detection of new/modified files
- Add batch processing feature with tqdm progress bars

### Changed

- Refactor code for better organization and maintainability

## 0.5.0 - 2025-03-06

Updated by Yunseo Kim (yunseo@snu.ac.kr)

### Added

- Add more detailed logging of peak detection for debugging
- Add fallback width value(20) for too small peak widths (< 1.0)
- Add logging of max thrust value and its index
- Add logging of basic statistics (max, min, mean, std) for pressure raw data before processing
- Add logging of maximum pressure value and its index after shifting

### Changed

- Improve the baseline estimation process
- Prevent negative thrust values

## 0.4.0 - 2025-02-17

Updated by Yunseo Kim (yunseo@snu.ac.kr)

### Added

- Add data validation and warning messages to the burn rate analyzer
- Improve error handling and logging throughout
- Add type hints and detailed docstrings to the burn rate analyzer

### Changed

- Refactor burn rate analyzer to object-oriented interface with BurnRateAnalyzer class
- Encapsulate the logger within the class

### Fixed
- To avoid file I/O errors based on the execution environment or current working directory, set the file paths to absolute paths using the OS module

## 0.3.0 - 2025-02-08

Updated by Yunseo Kim (yunseo@snu.ac.kr)

### Added

- Add type hints and detailed docstrings
- Improve error handling and logging throughout
- Add data validation and warning messages
  - Checks for duplicate or non-increasing timestamps and logs warnings
  - Detection for missing or invalid key data

### Fixed

- Check and resolve the part where the deprecation warnings were occurring

## 0.2.0 - 2025-01-22

Updated by Yunseo Kim (yunseo@snu.ac.kr)

### Added

- Add support for the new DAQ's data format
- Add burn rate determination feature

### Changed

- Improve the interpolation algorithm from CubicSpline to PCHIP
- Change output format from .txt(sep=' ') to .csv(sep=',')
- Separate items that vary per test into a config.xlsx file distinct from config.py

## 0.1.0 - 2024-06-18

First written by Jiwan Seo (jiwan0216@snu.ac.kr, Project Manager of Hanaro)

### Added

- Initial implementation of basic post-processing for static-fire test data
- Support parsing raw thrust and chamber pressure data
- Export processed results to CSV/graph outputs

[unreleased]: https://github.com/snu-hanaro/static-fire-toolkit/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/snu-hanaro/static-fire-toolkit/releases/tag/v1.0.0
