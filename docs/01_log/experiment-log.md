# Experiment Log

This document records experiments, PoCs, and hypothesis tests.

Each entry must include:
- **HYPOTHESIS**: What is being tested
- **METHOD**: How the experiment was conducted
- **RESULT**: Observed outcome
- **CONCLUSION**: Adoption decision and reasoning

Failed experiments are equally valuable and MUST be recorded.

- - -

## E-2025-01-19: PCHIP vs Cubic Spline for Resampling

---
EXPERIMENT_ID: E-2025-01-19
RELATED_ISSUES: []
---

**HYPOTHESIS**: PCHIP (Piecewise Cubic Hermite Interpolating Polynomial) better preserves signal characteristics during resampling compared to cubic spline.

**METHOD**:
1. Resampled thrust data from variable timesteps to uniform 0.01s using linear interpolation
2. Resampled same data using PCHIP
3. Compared reconstructed signals against original high-frequency reference

**RESULT**:
- Linear interpolation introduced visible artifacts at rapid signal changes
- PCHIP maintained smoother and monotonic curves without overshooting
- Computational cost difference negligible for typical dataset sizes

**CONCLUSION**: Adopted PCHIP for all resampling operations.

- - -

## E-2025-01-20: RK4 vs Euler for Burn Rate Integration

---
EXPERIMENT_ID: E-2025-01-20
RELATED_ISSUES: []
---

**HYPOTHESIS**: RK4 integration provides significantly more accurate burn rate calculations than Euler method for the same time step.

**METHOD**:
1. Implemented both RK4 and Euler integration for regression rate
2. Compared against analytical solution for simplified cases
3. Measured error accumulation over typical burn duration

**RESULT**:
- RK4 error: O(h^4), Euler error: O(h)
- For dt=0.01s over 5s burn: RK4 accumulated ~0.01% error vs ~2% for Euler
- RK4 overhead negligible for our use case

**CONCLUSION**: Adopted RK4 for all integration in burn rate analysis.

- - -

## E-2025-09-10: Butterworth vs Gaussian Filter for Thrust

---
EXPERIMENT_ID: E-2025-09-10
RELATED_ISSUES: []
---

**HYPOTHESIS**: Butterworth low-pass filter provides better noise reduction than pure Gaussian smoothing for thrust data while preserving signal edges.

**METHOD**:
1. Applied Gaussian filter (sigma=10) to raw thrust data
2. Applied Butterworth LPF (order=5, cutoff=30Hz) to same data
3. Compared:
   - Edge preservation (ignition/burnout transitions)
   - Noise floor in steady-state region
   - Phase shift artifacts

**RESULT**:
- Butterworth preserved sharper transitions at ignition/burnout
- Gaussian introduced visible smoothing at edges, underestimating peak thrust
- Both achieved comparable noise reduction in steady-state

**CONCLUSION**: Adopted Butterworth LPF as primary filter. Gaussian retained only for derivative estimation where edge preservation is less critical.

- - -

## E-2025-01-18: Duplicate Timestamp Handling Methods

---
EXPERIMENT_ID: E-2025-01-18
RELATED_ISSUES: []
---

**HYPOTHESIS**: Two approaches to handling duplicate timestamps in thrust data yield different accuracy profiles depending on the nature of the degradation.

**METHOD**:
1. After DAQ replacement (NI LabView → Arduino/pySerial), intermittent timestamp resolution degradation observed
2. Tested two handling approaches:
   - **Approach A**: Average thrust values at duplicate timestamps
   - **Approach B**: Redistribute timestamps via `linspace`, assuming uniform degradation
3. Analyzed raw data patterns to characterize degradation behavior
4. Compared processed outputs from both approaches against expected physical behavior

**RESULT**:
- Data analysis revealed degradation is **intermittent, not uniform**
- Delays occurred sporadically, up to 16ms maximum
- Approach B's assumption (uniform degradation) was invalid
- Approach A produced results closer to expected physical behavior
- Root cause traced to Python <3.7 time resolution issues on Windows

**CONCLUSION**: Adopted Approach A (averaging). The assumption underlying Approach B was empirically disproven. Decision recorded in D-2025-01-18.

- - -

## E-2024-11-19: Multi-Peak Combustion Data Processing Failure

---
EXPERIMENT_ID: E-2024-11-19
RELATED_ISSUES: []
---

**HYPOTHESIS**: Existing combustion window detection algorithm should handle all combustion patterns.

**METHOD**:
1. Attempted to process thrust data from metal-mixture propellant test
2. Observed chuffing (unstable combustion) pattern with multiple peaks
3. Applied standard processing pipeline

**RESULT**:
- Complete failure to detect any meaningful combustion window
- Algorithm returned no valid start/end points
- Data could not be processed at all
- Root cause not identified at the time

**CONCLUSION**: FAILED. Issue deferred for later investigation. Root cause later identified (2025-09-21) as single-peak assumption in algorithm. Fix implemented in D-2025-09-21-B.
