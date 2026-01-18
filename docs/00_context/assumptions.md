# Assumptions

## Data Acquisition

### Thrust Measurement
- Load cell output is a voltage signal linearly proportional to applied force
- Voltage-to-force conversion follows the standard formula:
  ```
  gain = gain_offset + (gain_internal_resistance_kohm * 1000) / potentiometer_resistance
  thrust[N] = (measured_voltage * 1000 / gain) / sensitivity_mv_per_v / excitation_voltage * (rated_capacity_kgf * g)
  ```
- Raw thrust data is sampled at a rate that can be resampled to 100 Hz without aliasing

### Pressure Measurement
- Pressure sensor outputs absolute pressure in bar
- Pressure data timestamps are parseable by `pandas.to_datetime()`
- Pressure changes are gradual enough that filtering is optional (unlike thrust)

### Time Synchronization
- Thrust and pressure data are recorded during the same test event
- The combustion window can be detected from thrust data and applied to pressure data

## Processing

### Signal Processing
- Butterworth low-pass filter is appropriate for thrust noise reduction
- PCHIP interpolation preserves signal characteristics when resampling to uniform time steps
- Gaussian smoothing is suitable for derivative estimation

### Burn Rate Analysis
- Saint-Robert's Law (`r = a * P^n`) describes propellant burn rate adequately
- RK4 integration provides sufficient accuracy for regression rate calculations
- Grain geometry is cylindrical with known inner/outer diameters

## Environment

### File System
- Execution root contains `config.xlsx`, `global_config.py`, `data/`, and `results/`
- Raw data files follow naming convention: `{TYPE}_{YYMMDD}_*_raw.csv`
- User has write permissions to `results/` directory

### Configuration
- `config.xlsx` contains one row per experiment; latest row is processed by default
- `global_config.py` is a valid Python module with required load cell parameters
