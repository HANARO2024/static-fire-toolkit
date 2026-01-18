# Experiment Log

This document records experiments, PoCs, and hypothesis tests.

Each entry must include:
- **HYPOTHESIS**: What is being tested
- **METHOD**: How the experiment was conducted
- **RESULT**: Observed outcome
- **CONCLUSION**: Adoption decision and reasoning

Failed experiments are equally valuable and MUST be recorded.

---

## E-2025-09-10: Butterworth vs Gaussian Filter for Thrust

```yaml
EXPERIMENT_ID: E-2025-09-10
RELATED_ISSUES: []
```

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

---

## E-2025-10-05: PCHIP vs Linear Interpolation for Resampling

```yaml
EXPERIMENT_ID: E-2025-10-05
RELATED_ISSUES: []
```

**HYPOTHESIS**: PCHIP (Piecewise Cubic Hermite Interpolating Polynomial) better preserves signal characteristics during resampling compared to linear interpolation.

**METHOD**:
1. Resampled thrust data from variable timesteps to uniform 0.01s using linear interpolation
2. Resampled same data using PCHIP
3. Compared reconstructed signals against original high-frequency reference

**RESULT**:
- Linear interpolation introduced visible artifacts at rapid signal changes
- PCHIP maintained smoother curves without overshooting
- Computational cost difference negligible for typical dataset sizes

**CONCLUSION**: Adopted PCHIP for all resampling operations.

---

## E-2025-11-20: RK4 vs Euler for Burn Rate Integration

```yaml
EXPERIMENT_ID: E-2025-11-20
RELATED_ISSUES: []
```

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
