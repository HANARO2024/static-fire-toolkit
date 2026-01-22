# Vision

## Purpose

Static-Fire Toolkit (SFT) provides a standardized, reproducible workflow for processing static-fire test data from amateur and research solid rocket motors.

## Goals

1. **Standardization**: Establish a consistent data processing pipeline across all HANARO static-fire tests
2. **Reproducibility**: Ensure that any team member can reproduce analysis results given the same raw data
3. **Accessibility**: Provide a CLI-first interface that works without specialized knowledge of Python internals
4. **Extensibility**: Support future additions (new propellant types, sensor configurations) without breaking existing workflows

## Non-Goals

- Real-time data acquisition (SFT processes post-test data only)
- Hardware control or DAQ integration
- Motor design optimization (SFT is analysis-focused)

## Success Criteria

- Any HANARO member can run `sft process` and obtain consistent, publication-ready outputs
- Processing pipeline is documented well enough that external researchers can adapt it
- Results are traceable back to raw data and configuration parameters
