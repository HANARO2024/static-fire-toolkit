"""Configuration loader for Static-Fire Toolkit runtime parameters.

This module centralizes loading of global runtime parameters that were
previously imported via wildcard imports. It prefers a user-provided
``global_config.py`` file in the current working directory (the execution
root), but falls back to safe defaults if none is found.

Supported source (searched in the execution root):
- global_config.py  (module with uppercase or lowercase attribute names)

Future extension: TOML/YAML support can be added when a stable schema is
finalized for non-code configuration.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Config:
    """Runtime configuration values used by processing modules."""

    # Load cell & acquisition (must be explicitly set by user)
    sensitivity_mv_per_v: float | None = None  # load cell sensitivity (mV/V)
    rated_capacity_kgf: float | None = None  # load cell rated capacity (kgf)
    gain_internal_resistance_kohm: float | None = (
        None  # amplifier internal resistance (kOhm)
    )
    gain_offset: float | None = None  # amplifier gain offset (volts)
    # Other parameters
    frequency: float = 100.0  # Sampling rate, Hz (Δt = 0.01 s)
    cutoff_frequency: float = 30.0  # Hz for LPF
    lowpass_order: int = 5  # order for lowpass filter
    gaussian_weak_sigma: float = 1.5  # sigma for weak gaussian filter
    gaussian_strong_sigma: float = 10.0  # sigma for strong gaussian filter
    start_criteria: float = 0.2  # Criteria for the starting point of a meaningful interval in thrust data processing
    end_criteria: float = 0.1  # Criteria for the ending point of a meaningful interval in thrust data processing
    thrust_sep: str = ","  # separator for thrust data, character or Regex
    thrust_header: int | None = 0  # header for thrust data (row number or None)
    thrust_time_col_idx: int = 0  # index of time column
    thrust_col_idx: int = 1  # index of thrust column
    pressure_sep: str = ","  # separator for pressure data, character or Regex
    pressure_header: int | None = 0  # header for pressure data (row number or None)
    pressure_time_col_idx: int = 0  # index of datetime column
    pressure_col_idx: int = 1  # index of pressure column


def _read_attr(cfg: Any, name: str, default: Any) -> Any:
    # Accept both lowercase and uppercase attribute names
    if hasattr(cfg, name):
        return getattr(cfg, name)
    upper = name.upper()
    if hasattr(cfg, upper):
        return getattr(cfg, upper)
    return default


def _load_from_python(path: Path, base: Config) -> Config:
    spec = spec_from_file_location("user_global_config", path)
    if spec and spec.loader:
        mod = module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[reportAttributeAccessIssue]
        # Backward-compatible mapping from legacy names
        sensitivity = _read_attr(mod, "sensitivity_mv_per_v", base.sensitivity_mv_per_v)
        if sensitivity == base.sensitivity_mv_per_v:
            sensitivity = _read_attr(mod, "rated_output", sensitivity)

        rated_capacity = _read_attr(mod, "rated_capacity_kgf", base.rated_capacity_kgf)
        if rated_capacity == base.rated_capacity_kgf:
            rated_capacity = _read_attr(mod, "rated_load", rated_capacity)

        gain_internal_res_kohm = _read_attr(
            mod, "gain_internal_resistance_kohm", base.gain_internal_resistance_kohm
        )
        gain_offset = _read_attr(mod, "gain_offset", base.gain_offset)

        return Config(
            sensitivity_mv_per_v=(None if sensitivity is None else float(sensitivity)),
            rated_capacity_kgf=(
                None if rated_capacity is None else float(rated_capacity)
            ),
            gain_internal_resistance_kohm=(
                None
                if gain_internal_res_kohm is None
                else float(gain_internal_res_kohm)
            ),
            gain_offset=(None if gain_offset is None else float(gain_offset)),
            frequency=float(_read_attr(mod, "frequency", base.frequency)),
            cutoff_frequency=float(
                _read_attr(mod, "cutoff_frequency", base.cutoff_frequency)
            ),
            lowpass_order=int(_read_attr(mod, "lowpass_order", base.lowpass_order)),
            gaussian_weak_sigma=float(
                _read_attr(mod, "gaussian_weak_sigma", base.gaussian_weak_sigma)
            ),
            gaussian_strong_sigma=float(
                _read_attr(mod, "gaussian_strong_sigma", base.gaussian_strong_sigma)
            ),
            start_criteria=float(
                _read_attr(mod, "start_criteria", base.start_criteria)
            ),
            end_criteria=float(_read_attr(mod, "end_criteria", base.end_criteria)),
            thrust_sep=str(_read_attr(mod, "thrust_sep", base.thrust_sep)),
            thrust_header=_read_attr(mod, "thrust_header", base.thrust_header),
            thrust_time_col_idx=int(
                _read_attr(mod, "thrust_time_col_idx", base.thrust_time_col_idx)
            ),
            thrust_col_idx=int(_read_attr(mod, "thrust_col_idx", base.thrust_col_idx)),
            pressure_sep=str(_read_attr(mod, "pressure_sep", base.pressure_sep)),
            pressure_header=_read_attr(mod, "pressure_header", base.pressure_header),
            pressure_time_col_idx=int(
                _read_attr(mod, "pressure_time_col_idx", base.pressure_time_col_idx)
            ),
            pressure_col_idx=int(
                _read_attr(mod, "pressure_col_idx", base.pressure_col_idx)
            ),
        )
    return base


def load_global_config(execution_root: str | Path | None = None) -> Config:
    """Load global runtime configuration from the execution root.

    The search order currently supports only ``global_config.py``. If none is
    found, a default :class:`Config` is returned.

    Args:
        execution_root: Directory to search. Defaults to current working dir.

    Returns:
        Config: Loaded configuration values.
    """
    root = Path(execution_root or ".").resolve()
    defaults = Config()

    py_cfg = root / "global_config.py"
    if py_cfg.exists():
        try:
            return _load_from_python(py_cfg, defaults)
        except Exception:
            # Fall back to defaults if user config fails to load
            return defaults

    return defaults
