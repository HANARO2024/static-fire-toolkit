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

    rated_output: float = 2.0  # mV/V or sensor unit (example default)
    rated_load: float = 100.0  # kg or sensor unit (example default)
    g: float = 9.80665
    frequency: float = 100.0  # Hz (Δt = 0.01 s)
    cutoff_frequency: float = 10.0  # Hz for LPF
    lowpass_order: int = 2
    gaussian_weak_sigma: float = 2.0
    gaussian_strong_sigma: float = 8.0
    start_criteria: float = 0.15
    end_criteria: float = 0.15


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
        return Config(
            rated_output=float(_read_attr(mod, "rated_output", base.rated_output)),
            rated_load=float(_read_attr(mod, "rated_load", base.rated_load)),
            g=float(_read_attr(mod, "g", base.g)),
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
