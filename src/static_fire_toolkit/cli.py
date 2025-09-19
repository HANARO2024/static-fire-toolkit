"""Command-line interface for Static-Fire Toolkit.

Provides subcommands to run thrust/pressure post-processing and burnrate analysis.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any, TYPE_CHECKING

import sys
import platform

from static_fire_toolkit import __version__
from static_fire_toolkit.config_loader import load_global_config

if TYPE_CHECKING:  # Only for type checkers; avoids importing pandas at runtime here
    from pandas import DataFrame


def _load_config(execution_root: Path, expt_name: str | None) -> dict[str, Any]:
    """Load configuration row from config.xlsx.

    Args:
        execution_root: Root directory where config.xlsx and data/results folders exist.
        expt_name: Optional experiment base name to filter the latest matching row.

    Returns:
        dict: Configuration mapping including expt_file_name, thrust params, and grain.
    """
    import pandas as pd

    config_path = execution_root / "config.xlsx"
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    config = pd.read_excel(config_path, sheet_name=0, header=0, index_col=0)
    if len(config) == 0:
        raise ValueError(f"Configuration file is empty: {config_path}")

    idx = len(config) - 1
    if expt_name:
        matches = config[config["expt_file_name"].str.contains(expt_name, case=False)]
        if not matches.empty:
            idx = matches.index[-1]

    required_columns = [
        "Outerdiameter [mm]",
        "Innerdiameter [mm]",
        "singlegrainheight [mm]",
        "expt_file_name",
        "totalmass [g]",
        "Nozzlediameter [mm]",
        "segment",
        # Accept both legacy and new column names for excitation voltage
        # either "expt_excitation_voltage [V]" or legacy "expt_input_voltage [V]"
        "expt_excitation_voltage [V]",
        "expt_resistance [Ohm]",
    ]
    missing = [col for col in required_columns if col not in config.columns]
    # Backward-compat: if the only missing item is the new excitation voltage column,
    # but the legacy column exists, treat as satisfied.
    if (
        "expt_excitation_voltage [V]" in missing
        and "expt_input_voltage [V]" in config.columns
    ):
        missing = [col for col in missing if col != "expt_excitation_voltage [V]"]
    if missing:
        raise ValueError(f"Missing columns in configuration: {missing}")

    # Backward-compatible read for excitation voltage
    if "expt_excitation_voltage [V]" in config.columns:
        expt_excitation_voltage = config["expt_excitation_voltage [V]"][idx]
    elif "expt_input_voltage [V]" in config.columns:
        expt_excitation_voltage = config["expt_input_voltage [V]"][idx]
    else:
        raise ValueError(
            "Missing excitation voltage column in configuration: expected 'expt_excitation_voltage [V]' or legacy 'expt_input_voltage [V]'"
        )

    return {
        "expt_file_name": config["expt_file_name"][idx],
        "expt_excitation_voltage": expt_excitation_voltage,
        "expt_resistance": config["expt_resistance [Ohm]"][idx],
        "grain": {
            "OD": float(config["Outerdiameter [mm]"][idx]),
            "ID": float(config["Innerdiameter [mm]"][idx]),
            "Height": float(config["singlegrainheight [mm]"][idx]),
            "Mass": float(config["totalmass [g]"][idx]),
            "Nozzlediameter": float(config["Nozzlediameter [mm]"][idx]),
            "N_Segment": float(config["segment"][idx]),
        },
    }


def _read_thrust_raw(execution_root: Path, expt_file_name: str) -> DataFrame:
    """Read raw thrust data (csv or txt) for the given experiment name."""
    raw_dir = execution_root / "data" / "_thrust_raw"
    csv_path = raw_dir / f"{expt_file_name}_thrust_raw.csv"
    txt_path = raw_dir / f"{expt_file_name}_thrust_raw.txt"
    if csv_path.exists():
        data_file = csv_path
    elif txt_path.exists():
        data_file = txt_path
    else:
        raise FileNotFoundError(
            f"No thrust data file found for {expt_file_name}: {csv_path} or {txt_path}"
        )
    import pandas as pd

    cfg = load_global_config(execution_root)
    sep = str(getattr(cfg, "thrust_sep", ","))
    header = getattr(cfg, "thrust_header", 0)
    return pd.read_csv(data_file, sep=sep, header=header, engine="python")


def _read_pressure_raw(execution_root: Path, expt_file_name: str) -> DataFrame:
    """Read raw pressure data (csv expected with ';' delimiter)."""
    raw_dir = execution_root / "data" / "_pressure_raw"
    csv_path = raw_dir / f"{expt_file_name}_pressure_raw.csv"
    txt_path = raw_dir / f"{expt_file_name}_pressure_raw.txt"
    if csv_path.exists():
        data_file = csv_path
    elif txt_path.exists():
        data_file = txt_path
    else:
        raise FileNotFoundError(
            f"No pressure data file found for {expt_file_name}: {csv_path} or {txt_path}"
        )
    import pandas as pd

    cfg = load_global_config(execution_root)
    sep = str(getattr(cfg, "pressure_sep", ","))
    header = getattr(cfg, "pressure_header", 0)
    return pd.read_csv(data_file, sep=sep, header=header, engine="python")


def cmd_thrust(args: argparse.Namespace) -> None:
    """Run thrust post-processing for a single experiment."""
    exec_root = Path(args.root or os.getcwd()).resolve()
    cfg = _load_config(exec_root, args.expt)
    from static_fire_toolkit.post_process.thrust_post_processing import (
        ThrustPostProcess,
    )

    thrust_raw = _read_thrust_raw(exec_root, cfg["expt_file_name"])
    proc = ThrustPostProcess(
        data_raw=thrust_raw,
        file_name=cfg["expt_file_name"],
        excitation_voltage=cfg["expt_excitation_voltage"],
        resistance=cfg["expt_resistance"],
        execution_root=str(exec_root),
    )
    _ = proc.run()


def cmd_pressure(args: argparse.Namespace) -> None:
    """Run pressure post-processing for a single experiment."""
    exec_root = Path(args.root or os.getcwd()).resolve()
    cfg = _load_config(exec_root, args.expt)
    import pandas as pd
    from static_fire_toolkit.post_process.pressure_post_processing import (
        PressurePostProcess,
    )

    pressure_raw = _read_pressure_raw(exec_root, cfg["expt_file_name"])

    # Load processed thrust output generated earlier
    thrust_csv = (
        exec_root / "results" / "thrust" / f"{cfg['expt_file_name']}_thrust.csv"
    )
    if not thrust_csv.exists():
        raise FileNotFoundError(
            f"Processed thrust CSV not found (expected first): {thrust_csv}"
        )
    # Local import to avoid importing pandas for lightweight commands
    thrust_data = pd.read_csv(thrust_csv)

    proc = PressurePostProcess(
        pressure_data_raw=pressure_raw,
        thrust_data=thrust_data,
        file_name=cfg["expt_file_name"],
        execution_root=str(exec_root),
    )
    _ = proc.run()


def cmd_burnrate(args: argparse.Namespace) -> None:
    """Run burnrate analysis for a single experiment using processed pressure CSV."""
    exec_root = Path(args.root or os.getcwd()).resolve()
    cfg = _load_config(exec_root, args.expt)

    pressure_csv = (
        exec_root / "results" / "pressure" / f"{cfg['expt_file_name']}_pressure.csv"
    )
    if not pressure_csv.exists():
        raise FileNotFoundError(
            f"Processed pressure CSV not found (expected after pressure step): {pressure_csv}"
        )
    import pandas as pd

    # Local import to avoid importing pandas for lightweight commands
    pressure_data = pd.read_csv(pressure_csv)

    from static_fire_toolkit.burnrate_calc.analyze_burnrate import BurnRateAnalyzer

    analyzer = BurnRateAnalyzer(
        pressure_data=pressure_data,
        grain=cfg["grain"],
        file_name=cfg["expt_file_name"],
        execution_root=str(exec_root),
    )
    analyzer.run()


def cmd_process(args: argparse.Namespace) -> None:
    """Run the end-to-end pipeline: thrust -> pressure -> burnrate."""
    exec_root = Path(args.root or os.getcwd()).resolve()
    cfg = _load_config(exec_root, args.expt)
    from static_fire_toolkit.post_process.thrust_post_processing import (
        ThrustPostProcess,
    )

    # 1) Thrust
    thrust_raw = _read_thrust_raw(exec_root, cfg["expt_file_name"])
    thrust_proc = ThrustPostProcess(
        data_raw=thrust_raw,
        file_name=cfg["expt_file_name"],
        excitation_voltage=cfg["expt_excitation_voltage"],
        resistance=cfg["expt_resistance"],
        execution_root=str(exec_root),
    )
    thrust_df = thrust_proc.run()

    # 2) Pressure
    pressure_raw = _read_pressure_raw(exec_root, cfg["expt_file_name"])
    from static_fire_toolkit.post_process.pressure_post_processing import (
        PressurePostProcess,
    )

    pressure_proc = PressurePostProcess(
        pressure_data_raw=pressure_raw,
        thrust_data=thrust_df,
        file_name=cfg["expt_file_name"],
        execution_root=str(exec_root),
    )
    pressure_df = pressure_proc.run()

    # 3) Burnrate
    from static_fire_toolkit.burnrate_calc.analyze_burnrate import BurnRateAnalyzer

    analyzer = BurnRateAnalyzer(
        pressure_data=pressure_df,
        grain=cfg["grain"],
        file_name=cfg["expt_file_name"],
        execution_root=str(exec_root),
    )
    analyzer.run()


def cmd_info(args: argparse.Namespace) -> None:
    """Show environment and package information useful for bug reports."""
    exec_root = Path(args.root or os.getcwd()).resolve()
    config_path = exec_root / "config.xlsx"

    print("\nStatic-Fire Toolkit\n")
    print("(c) 2025 SNU Rocket Team HANARO. Licensed under the MIT License.\n")
    print("================================================================")
    print(f"  exec_root      : {exec_root}")
    print(f"  config.xlsx    : {'present' if config_path.exists() else 'missing'}")
    print("================================================================")
    print(f"  version        : {__version__}")
    print(f"  python         : {sys.version.split()[0]}")
    print(f"  platform       : {platform.platform()}")
    # Lazy import heavy libs only when info is requested
    import numpy as np
    import pandas as pd
    import scipy
    import matplotlib

    print(f"  numpy          : {np.__version__}")
    print(f"  pandas         : {pd.__version__}")
    print(f"  scipy          : {scipy.__version__}")
    print(f"  matplotlib     : {matplotlib.__version__}")
    print("================================================================")


def build_parser() -> argparse.ArgumentParser:
    """Create an argparse parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="sft",
        description="Static-Fire Toolkit CLI",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show CLI and package version",
    )
    parser.add_argument(
        "--root",
        help="Execution root containing config.xlsx, data/, results/ (default: CWD)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # sft thrust
    p_thrust = sub.add_parser("thrust", help="Run thrust post-processing")
    p_thrust.add_argument(
        "--expt",
        help="Experiment base name (e.g., KNSB_250220)",
    )
    p_thrust.set_defaults(func=cmd_thrust)

    # sft pressure
    p_pressure = sub.add_parser("pressure", help="Run pressure post-processing")
    p_pressure.add_argument(
        "--expt",
        help="Experiment base name (e.g., KNSB_250220, requires thrust step be completed)",
    )
    p_pressure.set_defaults(func=cmd_pressure)

    # sft burnrate
    p_burnrate = sub.add_parser("burnrate", help="Run burnrate analysis")
    p_burnrate.add_argument(
        "--expt",
        help="Experiment base name (e.g., KNSB_250220, requires pressure step be completed)",
    )
    p_burnrate.set_defaults(func=cmd_burnrate)

    # sft process
    p_proc = sub.add_parser(
        "process", help="Run end-to-end pipeline: thrust -> pressure -> burnrate"
    )
    p_proc.add_argument(
        "--expt",
        help="Experiment base name to process end-to-end (e.g., KNSB_250220)",
    )
    p_proc.set_defaults(func=cmd_process)

    # sft info
    p_info = sub.add_parser("info", help="Show environment and package information")
    p_info.set_defaults(func=cmd_info)

    return parser


def main() -> None:
    """Entry point for the sft CLI."""
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
