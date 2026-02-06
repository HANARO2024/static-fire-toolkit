# Decision Log

This document records significant architectural, algorithmic, and product decisions.

Each entry must include:
- **DECISION**: What was decided
- **RATIONALE**: Why this decision was made
- **ALTERNATIVES**: Options that were considered but rejected
- **REVIEW_TRIGGER**: Conditions that would require re-evaluation


## D-2024-10-22: Burn Rate Analysis Module Development

---
DECISION_ID: D-2024-10-22
DECISION_TYPE: PRODUCT
---

**DECISION**: Develop a Python-based burn rate analysis module to characterize propellant properties from static-fire test data.

**RATIONALE**:
- Beyond thrust/pressure data, understanding propellant-specific properties (Isp, characteristic velocity, burn rate, c*, thrust coefficient) is essential for nozzle optimization
- Initial proposal on 2024-10-08, re-emphasized on 2024-10-22: theory-based analysis should determine choking conditions, rather than empirical trial-and-error with nozzle throat sizing
- Richard Nakka's spreadsheet exists but has operational limitations: poor integration with existing Python pipeline, limited automation/extensibility, numerical accuracy constraints
- Roadmap established 2024-11-21: complete burn rate analysis code by February 2025

**ALTERNATIVES**:
- Continue using Nakka's spreadsheet (rejected: poor Python integration, limited extensibility)
- Manual calculations (rejected: not scalable, error-prone)

**REVIEW_TRIGGER**: If commercial or standardized burn rate analysis tools become available with better integration.

**COMMITS**:
- Development started: 2024-12-20
- Nakka spreadsheet reproduction verified: 2025-01-01
- RK4/Simpson rule improvements: 2025-01-20


## D-2024-12-29: Sequential Pipeline Architecture

---
DECISION_ID: D-2024-12-29
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


## D-2025-01-18: Duplicate Timestamp Handling in Thrust Data

---
DECISION_ID: D-2025-01-18
DECISION_TYPE: ALGORITHM
---

**DECISION**: When duplicate timestamps are detected in input data, average the corresponding thrust values and log a warning.

**RATIONALE**:
- After DAQ replacement (NI LabView → Arduino/pySerial), intermittent timestamp resolution degradation observed (up to 16ms delays)
- Root cause: Python `<3.7` on Windows had known time resolution issues
- Two approaches tested:
  1. Average thrust values at duplicate timestamps
  2. Redistribute timestamps via linspace assuming uniform degradation
- Analysis showed degradation is **intermittent, not uniform**, invalidating approach 2
- Averaging (approach 1) better reflects actual scenario
- DAQ-side fix completed 2025-01-22, but robustness maintained for edge cases

**ALTERNATIVES**:
- Linspace redistribution (rejected: assumption of uniform degradation invalid)
- Reject data with duplicates (rejected: loses valuable test data)
- Ignore duplicates (rejected: causes interpolation errors)

**REVIEW_TRIGGER**: If a better method for handling duplicate timestamps is discovered.

**COMMITS**:
- Implemented in v0.3.0+


## D-2025-01-21-A: Experiment Configuration in xlsx Format

---
DECISION_ID: D-2025-01-21-A
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


## D-2025-01-22: Absolute Path Handling for File I/O

---
DECISION_ID: D-2025-01-22
DECISION_TYPE: ARCHITECTURE
---

**DECISION**: Use `os` module for absolute path resolution instead of relative paths in file I/O operations.

**RATIONALE**:
- Execution context varies: double-click from file explorer vs. IDE vs. terminal
- Relative paths break when current working directory differs from expected location
- Discovered during DAQ code debugging (outside this project scope) but applies universally
- Absolute paths ensure consistent behavior regardless of execution method

**ALTERNATIVES**:
- Relative paths with documentation (rejected: still error-prone)
- Environment variables for paths (rejected: adds configuration burden)

**REVIEW_TRIGGER**: N/A — this is a permanent best practice.

**COMMITS**:
- Applied from v0.4.0+


## D-2025-05-06: Open Source Release and Public Distribution

---
DECISION_ID: D-2025-05-06
DECISION_TYPE: PRODUCT
---

**DECISION**: Open-source the static-fire data processing toolkit and distribute publicly via PyPI.

**RATIONALE**:
- Tech reports show many university rocket teams maintain similar post-processing code independently
- Public release enables:
  - Citation in research papers with version-specific reproducibility
  - Contribution to amateur rocketry community (domestic and international)
  - Proper version control (git) replacing loose internal management
  - Structured handover to future team members
- GitHub public repository created 2025-09-13
- First PyPI release (v1.0.0) published 2025-09-19

**ALTERNATIVES**:
- Keep internal only (rejected: limits reproducibility, no community contribution)
- Release without PyPI (rejected: harder installation, no version management)

**REVIEW_TRIGGER**: If legal/IP concerns arise or if maintained tooling becomes available elsewhere.

**COMMITS**:
- Repository created: 2025-09-13
- v1.0.0 PyPI release: [`8220dc3`](https://github.com/snu-hanaro/static-fire-toolkit/commit/8220dc3)


## D-2025-09-03: Trunk-Based Development Strategy

---
DECISION_ID: D-2025-09-03
DECISION_TYPE: ARCHITECTURE
---

**DECISION**: Adopt trunk-based development with protected `main` branch.

**RATIONALE**:
- Initial consideration: main + version-specific release branches
  - Rejected: branch proliferation, backport/cherry-pick overhead unsuitable for hardware-focused team
  - Git Flow similarly rejected for same reasons
- Final strategy (2025-09-13):
  - `main` as protected branch: CI must pass, PRs required, no force-push, no direct commits
  - Short-lived feature branches (`feat/`, `fix/`, `chore/`) merged immediately after completion
  - SemVer releases via tags, GitHub Actions auto-publish to PyPI on tag push
  - TestPyPI verification before production release
  - Conventional Commits message format
- Single maintainer currently → require 1 approval (adjustable if team grows)

**ALTERNATIVES**:
- Git Flow (rejected: too complex for team size and domain focus)
- Release branches (rejected: maintenance overhead)
- No branch protection (rejected: risk of accidental main corruption)

**REVIEW_TRIGGER**: If team size grows significantly or multiple major versions need parallel maintenance.

**COMMITS**:
- Branch protection configured: 2025-09-13


## D-2025-09-13-A: Project Naming

---
DECISION_ID: D-2025-09-13-A
DECISION_TYPE: PRODUCT
---

**DECISION**: Name the project `static-fire-toolkit` (repository/package) with display name "HANARO SFT".

**RATIONALE**:
- Previously unnamed internally ("후처리 코드", "후퇴율 분석 코드")
- Open-source release requires official name
- Criteria: concise, relevant to function, reflects team identity (HANARO)
- Logo created using HANARO club colors (black, yellow, white) in square and banner variants

**ALTERNATIVES**:
- Generic names like "rocket-data-processor" (rejected: too generic, no team identity)
- Korean-only names (rejected: limits international adoption)

**REVIEW_TRIGGER**: N/A — naming is permanent.

**COMMITS**:
- Logo and naming: [`404d0d6`](https://github.com/snu-hanaro/static-fire-toolkit/commit/404d0d6)


## D-2025-09-13-B: src-layout Package Structure

---
DECISION_ID: D-2025-09-13-B
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


## D-2025-09-13-C: PyPI Package Distribution

---
DECISION_ID: D-2025-09-13-C
DECISION_TYPE: ARCHITECTURE
---

**DECISION**: Distribute via PyPI following PEP 517/518/621 standards with `pyproject.toml`.

**RATIONALE**:
- Standard Python packaging ensures compatibility with pip ecosystem
- `pyproject.toml` consolidates build/metadata configuration (modern best practice)
- Enables simple installation: `pip install static-fire-toolkit`

**ALTERNATIVES**:
- Manual distribution (rejected: no version management, difficult installation)
- conda-only (rejected: smaller user base for this domain)

**REVIEW_TRIGGER**: If conda distribution becomes necessary for specific dependencies.

**COMMITS**:
- `pyproject.toml` created: [`470fe36`](https://github.com/snu-hanaro/static-fire-toolkit/commit/470fe36)


## D-2025-09-14: Ruff as Linter and Formatter

---
DECISION_ID: D-2025-09-14
DECISION_TYPE: ARCHITECTURE
---

**DECISION**: Adopt Ruff for linting and formatting with pre-commit hooks.

**RATIONALE**:
- Ruff provides dozens of lint rules in a single tool (replaces flake8, isort, pyupgrade, etc.)
- Extremely fast execution (Rust-based)
- Low configuration barrier
- Pre-commit integration ensures quality before commits reach repository

**ALTERNATIVES**:
- flake8 + black + isort (rejected: multiple tools, slower, more config)
- No linting (rejected: code quality degradation over time)

**REVIEW_TRIGGER**: If Ruff development stalls or better alternatives emerge.

**COMMITS**:
- Pre-commit + Ruff setup: [`c12e09b`](https://github.com/snu-hanaro/static-fire-toolkit/commit/c12e09b)


## D-2025-09-15-A: Tag Release Helper Script

---
DECISION_ID: D-2025-09-15-A
DECISION_TYPE: ARCHITECTURE
---

**DECISION**: Create `tag_release.sh` helper script for consistent annotated tag creation.

**RATIONALE**:
- Consistent tag message format across releases
- Lowers barrier for future maintainers during handover
- Supports both signed (default) and annotated (`--no-sign`) tags

**ALTERNATIVES**:
- Manual tag creation (rejected: inconsistent format, error-prone)
- CI-only tagging (rejected: removes maintainer control)

**REVIEW_TRIGGER**: If release process changes significantly.

**COMMITS**:
- Script added: [`6728d91`](https://github.com/snu-hanaro/static-fire-toolkit/commit/6728d91)


## D-2025-09-15-B: AI Development Tool Guidelines

---
DECISION_ID: D-2025-09-15-B
DECISION_TYPE: ARCHITECTURE
---

**DECISION**: Create `.cursor/rules` directory with project-specific AI coding guidelines.

**RATIONALE**:
- AI tools (Cursor, Copilot) should follow same conventions as human developers
- Rules for linting, testing, versioning, and commit messages need consistent enforcement
- Version-controlled rules ensure all contributors (human and AI) use same guidelines

**ALTERNATIVES**:
- No AI-specific rules (rejected: inconsistent AI-generated code)
- Inline comments only (rejected: not discoverable by AI tools)

**REVIEW_TRIGGER**: If AI tooling conventions change or new tools are adopted.

**COMMITS**:
- Rules added: [`a7d6998`](https://github.com/snu-hanaro/static-fire-toolkit/commit/a7d6998)
- Superseded by: [`AGENTS.md`](https://github.com/snu-hanaro/static-fire-toolkit/blob/main/AGENTS.md) (D-2026-01-19)


## D-2025-09-15-C: Remove Wildcard Imports

---
DECISION_ID: D-2025-09-15-C
DECISION_TYPE: ARCHITECTURE
---

**DECISION**: Eliminate `from module import *` patterns; use explicit imports only.

**RATIONALE**:
- Wildcard imports make namespace pollution unpredictable
- Explicit imports improve code readability and maintenance
- Static analysis tools work better with explicit imports

**ALTERNATIVES**:
- Continue with wildcards (rejected: maintenance nightmare)
- `__all__` management (rejected: still requires discipline, easily broken)

**REVIEW_TRIGGER**: N/A — permanent best practice.

**COMMITS**:
- Wildcard removal: [`dc26641`](https://github.com/snu-hanaro/static-fire-toolkit/commit/dc26641)

---

## D-2025-09-15-D: Unified I/O Directory Structure

---
DECISION_ID: D-2025-09-15-D
DECISION_TYPE: ARCHITECTURE
---

**DECISION**: Consolidate I/O paths to `data/` (inputs) and `results/` (outputs) with type-specific subdirectories.

**RATIONALE**:
- Previous scattered paths caused confusion during operation
- Two top-level directories (`data/`, `results/`) provide clear mental model
- Subdirectories (`_thrust_raw/`, `thrust/`, `thrust_graph/`, etc.) organize by data type and stage

**ALTERNATIVES**:
- Flat structure (rejected: mixing inputs/outputs causes confusion)
- Deep nesting (rejected: too many levels to navigate)

**REVIEW_TRIGGER**: If additional data types require new organization patterns.

**COMMITS**:
- Path unification: [`383313d`](https://github.com/snu-hanaro/static-fire-toolkit/commit/383313d)

---

## D-2025-09-16-A: CLI Interface Introduction

---
DECISION_ID: D-2025-09-16-A
DECISION_TYPE: ARCHITECTURE
---

**DECISION**: Introduce `sft` CLI with subcommands for all processing operations.

**RATIONALE**:
- Previous workflow: run individual `.py` files directly with `python`
- Package-based installation (`pip install`) requires CLI entry point
- Subcommand structure mirrors processing stages:
  - `sft thrust` — thrust processing
  - `sft pressure` — pressure processing
  - `sft burnrate` — burn rate analysis
  - `sft process` — full pipeline (thrust → pressure → burnrate)
  - `sft info` — environment/version info for debugging
- Options: `--help`, `--version`, `--root ROOT`

**ALTERNATIVES**:
- Continue with direct script execution (rejected: incompatible with package distribution)
- Single command with flags (rejected: less intuitive for stage-specific runs)

**REVIEW_TRIGGER**: If significant new processing stages are added.

**COMMITS**:
- CLI introduction: [`d273649`](https://github.com/snu-hanaro/static-fire-toolkit/commit/d273649)


## D-2025-09-16-B: Rename Runtime Config from `config.py` to `global_config.py`

---
DECISION_ID: D-2025-09-16-B
DECISION_TYPE: ARCHITECTURE
---

**DECISION**: Rename runtime configuration file from `config.py` to `global_config.py`.

**RATIONALE**:
- Name collision with per-experiment `config.xlsx` caused confusion
- `global_config.py` clearly indicates scope (runtime/global vs. per-experiment)

**ALTERNATIVES**:
- Keep `config.py` with documentation (rejected: collision still confusing)

**REVIEW_TRIGGER**: When TOML migration is implemented (see [P-002](../02_work/parking-lot.md#p-002-toml-configuration-migration)).

**NOTES**:
- Python module format for configuration is technical debt inherited from early development (path dependency)
- TOML migration planned but deferred — see [P-002](../02_work/parking-lot.md#p-002-toml-configuration-migration)

**COMMITS**:
- Renaming handled in config loader refactor: [`dc26641`](https://github.com/snu-hanaro/static-fire-toolkit/commit/dc26641)


## D-2025-09-17: Lazy Import Optimization

---
DECISION_ID: D-2025-09-17
DECISION_TYPE: ARCHITECTURE
---

**DECISION**: Lazy-import heavy modules (pandas, scipy, matplotlib) only when needed.

**RATIONALE**:
- `sft --help` and `sft info` don't need full processing stack
- Eager imports add 2-3 seconds to startup time
- Lazy imports load modules only for commands that use them

**ALTERNATIVES**:
- Eager imports everywhere (rejected: poor CLI responsiveness)
- Separate lightweight CLI package (rejected: maintenance overhead)

**REVIEW_TRIGGER**: If startup time becomes acceptable with eager imports (e.g., faster hardware baseline).

**COMMITS**:
- Lazy import optimization: [`15d2003`](https://github.com/snu-hanaro/static-fire-toolkit/commit/15d2003)


## D-2025-09-18-A: Configurable CSV Delimiters and Headers

---
DECISION_ID: D-2025-09-18-A
DECISION_TYPE: ARCHITECTURE
---

**DECISION**: Add `thrust_sep`, `pressure_sep`, `thrust_header`, `pressure_header` parameters to `global_config.py`.

**RATIONALE**:
- Raw data formats vary by DAQ system and institution
- Hardcoded delimiters/headers prevented use with different data sources
- Configurable parsing enables broader adoption

**ALTERNATIVES**:
- Automatic format detection (rejected: unreliable, magic behavior)
- Strict format requirements (rejected: limits usability)

**REVIEW_TRIGGER**: If additional parsing options are frequently requested.

**COMMITS**:
- Sep/header configuration: [`1b1ce20`](https://github.com/snu-hanaro/static-fire-toolkit/commit/1b1ce20)


## D-2025-09-18-B: Parameterized Load Cell Conversion

---
DECISION_ID: D-2025-09-18-B
DECISION_TYPE: ARCHITECTURE
---

**DECISION**: Require explicit load cell parameters in `global_config.py`; fail loudly if missing.

**RATIONALE**:
- Previous code hardcoded voltage-to-thrust conversion for specific load cell
- Changing load cell required code modification — unacceptable for public release
- Required parameters: `sensitivity_mv_per_v`, `rated_capacity_kgf`, `gain_internal_resistance_kohm`, `gain_offset`
- Legacy parameter names supported for backward compatibility

**ALTERNATIVES**:
- Continue hardcoding (rejected: unusable for other setups)
- Optional with defaults (rejected: silent wrong results worse than loud failure)

**REVIEW_TRIGGER**: If universal load cell interface emerges.

**COMMITS**:
- Mandatory load cell params: [`bba59fa`](https://github.com/snu-hanaro/static-fire-toolkit/commit/bba59fa)


## D-2025-09-19: Version Single Source of Truth

---
DECISION_ID: D-2025-09-19
DECISION_TYPE: ARCHITECTURE
---

**DECISION**: Read `__version__` dynamically from package metadata via `importlib.metadata` instead of hardcoding.

**RATIONALE**:
- v1.0.0 release had version mismatch: `__init__.py` showed old version
- Dynamic reading from `pyproject.toml` metadata ensures single source of truth
- `pyproject.toml` version is authoritative; code reads it at runtime

**ALTERNATIVES**:
- Manual sync (rejected: human error as demonstrated)
- Build-time injection (rejected: more complex tooling)

**REVIEW_TRIGGER**: If Python packaging standards change.

**COMMITS**:
- Dynamic version fix in v1.0.1 hotfix: [`23e3c0a`](https://github.com/snu-hanaro/static-fire-toolkit/commit/23e3c0a)


## D-2025-09-20-A: Savitzky-Golay Filter for Thrust Smoothing

---
DECISION_ID: D-2025-09-20-A
DECISION_TYPE: ALGORITHM
---

**DECISION**: Replace weak Gaussian filter with Savitzky-Golay filter for thrust data smoothing.

**RATIONALE**:
- Previous Gaussian filter (weak sigma) lacked theoretical justification
- Gaussian can dull edges and peaks, causing over-smoothing
- Savitzky-Golay preserves:
  - Peak height and width
  - Total impulse (area under curve)
  - Derivative stability (important for downstream burn rate analysis)
- Strong Gaussian filter retained only for combustion window detection (not applied to output)

**ALTERNATIVES**:
- Continue Gaussian (rejected: theoretical weakness, peak distortion)
- No smoothing (rejected: noise affects downstream analysis)

**REVIEW_TRIGGER**: If signal characteristics change significantly with new DAQ systems.


## D-2025-09-20-B: Zero-Phase Butterworth Filter

---
DECISION_ID: D-2025-09-20-B
DECISION_TYPE: ALGORITHM
---

**DECISION**: Replace `lfilter` (forward IIR) with `sosfiltfilt` (zero-phase, bidirectional) for low-pass filtering.

**RATIONALE**:
- Forward-only IIR filtering introduces phase shift
- Phase shift delays timing markers (ignition, burnout) in processed data
- `sosfiltfilt` applies filter forward then backward, canceling phase distortion
- Essential for accurate timing analysis

**ALTERNATIVES**:
- Continue with `lfilter` (rejected: timing errors unacceptable)
- FIR filter (rejected: requires longer filter for same cutoff, more complex)

**REVIEW_TRIGGER**: If computational cost becomes concern for real-time applications.


## D-2025-09-20-C: LPF Before Resampling

---
DECISION_ID: D-2025-09-20-C
DECISION_TYPE: ALGORITHM
---

**DECISION**: Apply low-pass filter before PCHIP resampling (previously reversed).

**RATIONALE**:
- Downsampling without prior anti-aliasing filter causes aliasing artifacts
- Correct order: LPF (remove high frequencies) → resample (reduce sample rate)
- Previous implementation resampled first, risking aliased data

**ALTERNATIVES**:
- Keep original order (rejected: aliasing is mathematically incorrect)
- No resampling (rejected: variable timestep data harder to analyze)

**REVIEW_TRIGGER**: N/A — this is signal processing fundamentals.


## D-2025-09-20-D: Zenodo DOI Assignment

---
DECISION_ID: D-2025-09-20-D
DECISION_TYPE: PRODUCT
---

**DECISION**: Integrate with Zenodo for DOI assignment; add `CITATION.bib` and `CITATION.cff`.

**RATIONALE**:
- Academic use case requires citable references
- DOI enables precise version citation in papers
- Zenodo auto-archives GitHub releases with persistent identifiers
- Citation files in standard formats (BibTeX, CFF) ease reference management

**ALTERNATIVES**:
- No DOI (rejected: limits academic credibility)
- Self-hosted DOI (rejected: infrastructure overhead)

**REVIEW_TRIGGER**: If alternative archival services offer better features.

**COMMITS**:
- Zenodo integration: 2025-09-28
- Citation files: [`40a58ed`](https://github.com/snu-hanaro/static-fire-toolkit/commit/40a58ed)


## D-2025-09-21-A: Combustion Window Detection - Threshold Criteria

---
DECISION_ID: D-2025-09-21-A
DECISION_TYPE: ALGORITHM
---

**DECISION**: Add maximum-value-ratio threshold to combustion window detection, combined with existing gradient criteria.

**RATIONALE**:
- Previous gradient-based detection was sensitive to data scale and noise
- Standard practice: define combustion start/end at fixed percentage of peak (e.g., 5%, 10%)
- Combined with OR logic: either gradient OR threshold triggers boundary
- Resolves issue observed 2025-01-04 where window was incorrectly truncated

**ALTERNATIVES**:
- Gradient-only (rejected: scale-sensitive, failed on some datasets)
- Threshold-only (rejected: misses gradual ignition profiles)
- Fixed time windows (rejected: not adaptive to actual burn duration)

**REVIEW_TRIGGER**: If propulsion engineering community establishes different standard criteria.


## D-2025-09-21-B: Multi-Peak Combustion Window Handling

---
DECISION_ID: D-2025-09-21-B
DECISION_TYPE: ALGORITHM
---

**DECISION**: Extend boundary search with configurable window to handle multi-peak combustion (e.g., chuffing).

**RATIONALE**:
- Original algorithm assumed single peak — failed completely on unstable combustion data (2024-11-19 test)
- Chuffing and other instabilities produce multiple peaks
- New logic: when boundary condition met, continue searching within window size; only finalize if condition persists
- Enables processing of "failed" tests that still contain valuable data

**ALTERNATIVES**:
- Reject multi-peak data (rejected: loses valuable failure analysis data)
- Manual boundary specification (rejected: not scalable, defeats automation purpose)

**REVIEW_TRIGGER**: If unstable combustion patterns become more varied than current window approach handles.


## D-2026-01-11: TOML Configuration Migration

---
DECISION_ID: D-2026-01-11
RELATED_ISSUES:
  - P-002
DECISION_TYPE: ARCHITECTURE
---

**DECISION**: Migrate `global_config.py` to `global_config.toml` format. Maintain `global_config.py` as deprecated legacy fallback for backward compatibility.

**RATIONALE**:
- Using a Python module (`.py`) as a configuration file conflates executable code with declarative data:
  - Arbitrary code execution risk: a Python config file can import modules, run side effects, or contain logic errors that affect runtime behavior in unpredictable ways
  - Blurs the boundary between "what the user configures" and "what the program does," making it harder for non-developer users to safely edit settings
  - Static analysis tools and editors cannot validate Python config files against an expected schema
- TOML provides clear separation between configuration data and application code:
  - Human-readable and easy to edit without programming knowledge
  - Deterministic parsing with no execution side effects
  - Standard format with broad tooling support (PEP 680 added `tomllib` to Python 3.11 stdlib)
- Current Python module format is technical debt inherited from early development (path dependency), identified since D-2025-09-16-B

**ALTERNATIVES**:
- Keep `global_config.py` as-is (rejected: conflates code and data, security concern, poor separation of concerns)
- YAML (rejected: implicit typing pitfalls, less strict than TOML)
- JSON (rejected: no comments, less human-friendly for manual editing)
- INI/ConfigParser (rejected: limited type support, no nested structures)

**REVIEW_TRIGGER**: If computed configuration values (e.g., gain calculations) prove difficult to express in TOML and require a more expressive format.

**NOTES**:
- Currently deferred (parking lot P-002); assign ISSUE ID when work begins
- Must handle computed values (e.g., gain calculations) that currently use Python expressions
- Backward compatibility with existing `global_config.py` users is mandatory during transition


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
