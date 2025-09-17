"""Burnrate Calculation Code.

2025.01.22. Written by Yunseo Kim <yunseo@snu.ac.kr>
HANARO, Seoul National University Rocket Team

2025.02.16. Updated by Yunseo Kim <yunseo@snu.ac.kr>:
- Refactored to object-oriented interface with BurnRateAnalyzer class
- Added type hints and detailed docstrings
- Improved error handling and logging throughout
- Added data validation and warning messages
"""

from __future__ import annotations

import os
import logging
import pandas as pd
import numpy as np
from scipy.integrate import simpson
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from scipy.optimize import curve_fit
from static_fire_toolkit.style import apply_default_style

# Apply style after all imports to satisfy import-order rules.
apply_default_style()


class BurnRateAnalyzer:
    """A class for analyzing the burnrate of a solid rocket motor fuel based on pressure data."""

    def __init__(
        self,
        pressure_data: pd.DataFrame,
        grain: dict,
        file_name: str,
        execution_root: str | None = None,
    ) -> None:
        """Initialize the analyzer with pressure data, grain parameters, and file metadata.

        Parameters:
            pressure_data (pd.DataFrame): Dataframe containing pressure and time data.
            grain (dict): Dictionary containing grain parameters.
            file_name (str): File name identifier for logging and output.
        """
        # Define file paths
        self._BASE_DIR = os.path.abspath(os.path.dirname(__file__))
        # Use execution root for all I/O (logs/results)
        self._EXEC_ROOT = os.path.abspath(execution_root or os.getcwd())
        self.output_data_dir = os.path.join(self._EXEC_ROOT, "results", "burnrate")
        self.output_graph_dir = os.path.join(
            self._EXEC_ROOT, "results", "burnrate_graph"
        )

        # Set up logging
        self._logger = logging.getLogger(__name__)
        self._BASE_DIR = os.path.abspath(os.path.dirname(__file__))
        log_dir = os.path.join(self._EXEC_ROOT, "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_filename = os.path.join(log_dir, f"{file_name}-burnrate_analysis.log")

        # Configure file handler
        file_handler = logging.FileHandler(log_filename)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )

        # Configure console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))

        # Set up logger
        self._logger.setLevel(logging.INFO)
        self._logger.addHandler(file_handler)
        self._logger.addHandler(console_handler)

        # Store input parameters
        self.pressure_data = pressure_data
        self.grain = grain
        self.file_name = file_name
        self.g = 9.80665  # gravitational acceleration (m/s^2)

        self._logger.info("0. Initializing BurnRateAnalyzer.")

    # Step 1: Normalize pressure data
    def normalize_pressure_data(self) -> None:
        """Normalize the pressure data to SI units."""
        self._logger.info("1. Normalizing pressure data.")

        if "pressure" not in self.pressure_data.columns:
            self._logger.error(
                "1. Required column 'pressure' not found in the pressure data file."
            )
            raise ValueError("Missing 'pressure' column in the data.")

        try:
            pressure_Pa = self.pressure_data["pressure"] * 1e5  # convert from bar to Pa
            self.pressure_data["pressure_Pa"] = pressure_Pa
            self.pressure_data["pressure_gauge"] = (
                pressure_Pa - 1.013 * 1e5
            )  # subtract atmospheric pressure
            self._logger.info("1. Pressure data successfully normalized.")
        except Exception as e:
            self._logger.error(
                "1. Error Normalizing pressure data: %s", e, exc_info=True
            )
            raise

    # Note: Configuration loading is now handled in __init__

    # Deprecated: Use integrate_pressure instead.
    @staticmethod
    def integrate_pressure_legacy(pressure_data: pd.DataFrame) -> float:
        """Integrate the pressure-time data using the trapezoidal rule.

        (Same as the method used in nakka-rocketry.net/ptburn.html.)

        Parameters:
            pressure_data (pd.DataFrame): The pressure data.

        Returns:
            float: The integrated pressure (Pa·s).
        """
        dt = 0.01
        integral_P = pressure_data["pressure_gauge"].sum() * dt  # 단위: Pa*s
        return integral_P

    # Step 2-1: Pressure integration using Simpson's rule
    def integrate_pressure(self, pressure_data: pd.DataFrame) -> float:
        """Integrate the pressure-time data using Simpson's rule.

        Parameters:
            pressure_data (pandas.DataFrame): The pressure data.

        Returns:
            float: The integrated pressure (Pa·s).
        """
        try:
            time = pressure_data["time"].values
            pressure = pressure_data["pressure_gauge"].values
            integral_pressure = simpson(pressure, time)
            self._logger.info(
                f"   2-1. Pressure integrated using Simpson's rule: {integral_pressure:.2f} Pa·s"
            )
            return integral_pressure
        except Exception as e:
            self._logger.error(
                "   2-1. Error during pressure integration: %s", e, exc_info=True
            )
            raise

    def burning_area(self, s: float, grain_data: dict) -> float:
        """Calculate the burning area (in m^2) for a given regression distance s (in mm).

        Uses a BATES grain geometry.

        Parameters:
            s (float): Regression distance (mm).
            grain_data (dict): Grain parameters.

        Returns:
            float: Burning area in m^2.
        """
        try:
            area = (
                np.pi
                * grain_data["N_Segment"]
                * (
                    ((grain_data["OD"] ** 2 - (grain_data["ID"] + 2 * s) ** 2) / 2)
                    + (grain_data["Height"] - 2 * s) * (grain_data["ID"] + 2 * s)
                )
                * 1e-6
            )
            return area
        except Exception as e:
            self._logger.error("Error computing burning area: %s", e, exc_info=True)
            raise

    @staticmethod
    def saint_roberts_law(
        P: float | np.ndarray, a: float, n: float
    ) -> float | np.ndarray:
        """Saint Robert's Law (Vieille's Law): r = a * P^n.

        Parameters:
            P (float or np.ndarray): Pressure in MPa.
            a (float): Coefficient (experimentally determined).
            n (float): Exponent (experimentally determined).

        Returns:
            float or np.ndarray: Burn rate in mm/s.
        """
        return a * np.power(P, n)

    # Step 2: Calculate burnrate
    def calc_burnrate(
        self, pressure_data: pd.DataFrame
    ) -> tuple[np.ndarray, np.ndarray, float | None, float | None]:
        """Calculate burnrate using RK4 and fit an ideal burnrate curve.

        The ideal curve is computed using Saint Robert's Law.

        Parameters:
            pressure_data (pandas.DataFrame): The preprocessed pressure data.

        Returns:
            tuple: (burnrate, burnrate_ideal, a_fit, n_fit)
                burnrate (np.ndarray): Calculated burnrate at each time step (mm/s).
                burnrate_ideal (np.ndarray): Ideal burnrate from curve fitting (mm/s).
                a_fit (float): Fitted coefficient a.
                n_fit (float): Fitted exponent n.
        """
        self._logger.info("2. Starting burnrate calculation.")
        try:
            grain_data = self.grain
            integral_P = self.integrate_pressure(pressure_data)
            density = (
                1e6
                * grain_data["Mass"]
                / (
                    np.pi
                    * (grain_data["OD"] ** 2 - grain_data["ID"] ** 2)
                    / 4
                    * grain_data["Height"]
                    * grain_data["N_Segment"]
                )
            )  # 단위: kg/m^3
            self._logger.info(f"   2-2. Grain density calculated: {density:.2f} kg/m^3")
        except Exception as e:
            self._logger.error(
                "2. Error during initial burnrate setup: %s", e, exc_info=True
            )
            raise

        def burning_rate(t: float, s: float) -> float:
            """Calculate the instantaneous burn rate at time t and regression distance s."""
            # Linear interpolation of pressure at time t
            try:
                if t <= pressure_data["time"].iloc[0]:
                    p = pressure_data["pressure_gauge"].iloc[0]
                elif t >= pressure_data["time"].iloc[-1]:
                    p = pressure_data["pressure_gauge"].iloc[-1]
                else:
                    idx = np.searchsorted(pressure_data["time"], t)
                    t0, t1 = (
                        pressure_data["time"].iloc[idx - 1],
                        pressure_data["time"].iloc[idx],
                    )
                    p0, p1 = (
                        pressure_data["pressure_gauge"].iloc[idx - 1],
                        pressure_data["pressure_gauge"].iloc[idx],
                    )
                    p = p0 + (t - t0) * (p1 - p0) / (t1 - t0)
                return (
                    p
                    * grain_data["Mass"]
                    / (self.burning_area(s, grain_data) * density * integral_P)
                )
            except Exception as e_inner:
                self._logger.error(
                    "      Error computing instantaneous burn rate at t=%s, s=%s: %s",
                    t,
                    s,
                    e_inner,
                    exc_info=True,
                )
                raise

        time = pressure_data["time"].values
        dt = np.diff(time)[0]  # assume constant time step

        s = np.zeros(len(time))  # regression distance array
        burnrate = np.zeros(len(time))  # burnrate array

        # RK4 integration
        self._logger.info("   2-3. Starting RK4 integration.")
        for i in range(len(time) - 1):
            t = time[i]

            k1 = burning_rate(t, s[i])
            k2 = burning_rate(t + dt / 2, s[i] + dt * k1 / 2)
            k3 = burning_rate(t + dt / 2, s[i] + dt * k2 / 2)
            k4 = burning_rate(t + dt, s[i] + dt * k3)

            s[i + 1] = s[i] + (dt / 6) * (k1 + 2 * k2 + 2 * k3 + k4)
            burnrate[i] = (k1 + 2 * k2 + 2 * k3 + k4) / 6
        burnrate[-1] = burning_rate(time[-1], s[-1])
        self._logger.info("   2-3. RK4 integration done.")

        # Prepare data for fitting using grouping by pressure
        burnrate_df = pd.DataFrame(
            {
                "pressure_MPa": pressure_data["pressure_gauge"] * 1e-6,
                "burnrate": burnrate,
            }
        )
        burnrate_mean = (
            burnrate_df.groupby("pressure_MPa")["burnrate"].mean().reset_index()
        )

        # Only use data with pressure >= 4 MPa for fitting
        mask = burnrate_mean["pressure_MPa"] >= 4
        pressure_fit = burnrate_mean[mask]["pressure_MPa"]
        burnrate_fit = burnrate_mean[mask]["burnrate"]

        # curve_fit을 사용하여 a와 n 계수 찾기
        try:
            popt, pcov = curve_fit(
                self.saint_roberts_law,
                pressure_fit,
                burnrate_fit,
                p0=[1.0, 0.5],  # 초기 추정값
                bounds=([0, 0], [100, 2]),
            )  # 물리적으로 의미 있는 범위로 제한
            a_fit, n_fit = popt
            perr = np.sqrt(np.diag(pcov))
            a_err, n_err = perr

            self._logger.info("   2-4. Saint Robert's Law fitting results (P ≥ 4 MPa):")
            self._logger.info(f"      a = {a_fit:.4f} ± {a_err:.4f}")
            self._logger.info(f"      n = {n_fit:.4f} ± {n_err:.4f}")
            self._logger.info(f"      r = {a_fit:.4f} P^{n_fit:.4f}")

            # Calculate ideal burnrate with fitted a and n
            p_min = pressure_data["pressure_gauge"].min() * 1e-6
            p_max = pressure_data["pressure_gauge"].max() * 1e-6
            pressure_axis = np.linspace(
                p_min, p_max * 1.1, len(pressure_data["pressure_gauge"])
            )
            burnrate_ideal = self.saint_roberts_law(pressure_axis, a_fit, n_fit)

        except RuntimeError:
            self._logger.warning("   2-4. Saint Robert's Law fitting failed.")
            burnrate_ideal = np.zeros_like(burnrate)
            a_fit, n_fit = None, None

        return burnrate, burnrate_ideal, a_fit, n_fit

    # Step 3: Output results
    def output_result(
        self,
        filename: str,
        pressure_data: pd.DataFrame,
        burnrate: np.ndarray,
        burnrate_ideal: np.ndarray,
        a_fit: float,
        n_fit: float,
    ) -> None:
        """Save the processed data and generate graphs and animations.

        Parameters:
            filename (str): Original pressure data filename.
            pressure_data (pandas.DataFrame): The pressure data.
            burnrate (np.array): Calculated burnrate values.
            burnrate_ideal (np.array): Ideal burnrate values from curve fitting.
            a_fit (float): Fitted coefficient a.
            n_fit (float): Fitted exponent n.
        """
        # Create output directories if they don't exist
        self._logger.info("3. Saving results.")
        self._logger.info("   3-1. Creating output directories if they don't exist.")
        try:
            os.makedirs(self.output_data_dir, exist_ok=True)
        except OSError as e:
            self._logger.error(f"   3-1. Error creating output data directory: {e}")
            raise
        try:
            os.makedirs(self.output_graph_dir, exist_ok=True)
        except OSError as e:
            self._logger.error(f"   3-1. Error creating output graph directory: {e}")
            raise
        rp_dir = os.path.join(self.output_graph_dir, "Burnrate-Pressure")
        rt_dir = os.path.join(self.output_graph_dir, "Burnrate-Time")
        rp_anim_dir = os.path.join(rp_dir, "animation")
        try:
            os.makedirs(rp_dir, exist_ok=True)
        except OSError as e:
            self._logger.error(
                f"   3-1. Error creating output Burnrate-Pressure directory: {e}"
            )
            raise
        try:
            os.makedirs(rt_dir, exist_ok=True)
        except OSError as e:
            self._logger.error(
                f"   3-1. Error creating output Burnrate-Time directory: {e}"
            )
            raise
        try:
            os.makedirs(rp_anim_dir, exist_ok=True)
        except OSError as e:
            self._logger.error(
                f"   3-1. Error creating output Burnrate-Pressure animation directory: {e}"
            )
            raise

        # Construct base name from the filename (assumes a '_' separated filename)
        try:
            base_name = filename.split("_")[0] + "_" + filename.split("_")[1]
            output_data_path = os.path.join(
                self.output_data_dir, base_name + "_burnrate.csv"
            )
            output_RP_graph_path = os.path.join(rp_dir, base_name + "_burnrate.png")
            output_RT_graph_path = os.path.join(rt_dir, base_name + "_burnrate.png")
            output_RP_anim_path = os.path.join(
                rp_anim_dir, base_name + "_burnrate_animation.gif"
            )
        except Exception as e:
            self._logger.error(f"   3-1. Error parsing filename: {e}")
            raise

        # Save the calculated data to CSV
        self._logger.info("   3-2. Saving calculated data to CSV.")
        try:
            output_data = pd.DataFrame(
                {
                    "time[s]": pressure_data["time"],
                    "pressure[MPa]": pressure_data["pressure_gauge"] * 1e-6,
                    "burnrate[mm/s]": burnrate,
                    "burnrate_ideal[mm/s]": burnrate_ideal,
                }
            )
            output_data.to_csv(output_data_path, index=False)
        except Exception as e:
            self._logger.error(f"   3-2. Error saving calculated data to CSV: {e}")
            raise

        # ----------------------------
        # Pressure-Burnrate Graph
        # ----------------------------
        self._logger.info("   3-3. Saving Pressure-Burnrate graph.")
        try:
            fig, ax = plt.subplots()
            ax.plot(
                output_data["pressure[MPa]"],
                output_data["burnrate[mm/s]"],
                "k+",
                label="Measured",
                zorder=1,
            )
            p_min = output_data["pressure[MPa]"].min()
            p_max = output_data["pressure[MPa]"].max()
            p_axis = np.linspace(p_min, p_max * 1.1, len(output_data["pressure[MPa]"]))
            ax.plot(p_axis, burnrate_ideal, "r--", label="Ideal (> 4 MPa)", zorder=0)
            max_idx = output_data["burnrate[mm/s]"].idxmax()
            x = output_data["pressure[MPa]"][max_idx]
            y = output_data["burnrate[mm/s]"][max_idx]
            ax.scatter(x, y, marker="o", color="red", s=120, zorder=1)
            ax.annotate(
                "Peak: "
                + str(round(p_max, 2))
                + " MPa, \n          "
                + str(round(output_data["burnrate[mm/s]"].max(), 2))
                + " mm/s, \n          "
                + str(round(output_data["time[s]"][max_idx], 2))
                + " s",
                xy=(0.8, 0.87),
                xycoords="axes fraction",
            )
            text_x = p_max * 0.8
            text_y = (
                self.saint_roberts_law(text_x, a_fit, n_fit) * 0.9
                if a_fit is not None
                else 0
            )
            ax.text(
                text_x,
                text_y,
                f"r = {a_fit:.3f} P^({n_fit:.3f})" if a_fit is not None else "",
                color="red",
                zorder=3,
            )
            ax.set_xlabel("Chamber Pressure (MPa)")
            ax.set_ylabel("Burnrate (mm/s)")
            fig.suptitle(base_name + " Burnrate-Pressure graph", y=0.95)
            ax.set_xlim(0, p_max * 1.11)
            ax.set_ylim(
                0,
                max(
                    output_data["burnrate[mm/s]"].max(),
                    burnrate_ideal.max() if burnrate_ideal.size > 0 else 0,
                )
                * 1.15,
            )
            plt.savefig(output_RP_graph_path)
            plt.close()
        except Exception as e:
            self._logger.error(f"   3-3. Error saving Pressure-Burnrate graph: {e}")
            raise

        # ----------------------------
        # Time-Burnrate Graph
        # ----------------------------
        self._logger.info("   3-4. Saving Time-Burnrate graph.")
        try:
            fig, ax = plt.subplots()
            ax.plot(
                output_data["time[s]"],
                output_data["burnrate[mm/s]"],
                color="black",
                zorder=0,
            )
            max_idx = output_data["burnrate[mm/s]"].idxmax()
            x_points = [output_data["time[s]"][max_idx], output_data["time[s]"].max()]
            y_points = [output_data["burnrate[mm/s]"][max_idx], 0]
            ax.scatter(x_points, y_points, marker="o", color="red", s=120, zorder=1)
            ax.annotate(
                "Peak: " + str(round(output_data["burnrate[mm/s]"].max(), 2)) + " mm/s",
                xy=(
                    output_data["time[s]"][max_idx]
                    / output_data["time[s]"].max()
                    * 0.65,
                    0.94,
                ),
                xycoords="axes fraction",
            )
            ax.annotate(
                "Total Time:\n" + str(round(output_data["time[s]"].max(), 2)) + " s",
                xy=(0.89, 0.12),
                xycoords="axes fraction",
            )
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Burnrate (mm/s)")
            fig.suptitle(base_name + " Burnrate-Time graph", y=0.95)
            ax.set_ylim(
                [
                    -0.05 * output_data["burnrate[mm/s]"].max(),
                    1.12 * output_data["burnrate[mm/s]"].max(),
                ]
            )
            ax.set_xlim([0, output_data["time[s]"].max() * 1.11])
            plt.savefig(output_RT_graph_path)
            plt.close()
        except Exception as e:
            self._logger.error(f"   3-4. Error saving Time-Burnrate graph: {e}")
            raise

        # ----------------------------
        # Pressure-Burnrate Animation
        # ----------------------------
        self._logger.info("   3-5. Saving Pressure-Burnrate animation.")
        try:
            fig, ax = plt.subplots()
            (line,) = ax.plot([], [], "k+", label="Measured")
            (trail,) = ax.plot([], [], "k+")
            (ideal_line,) = ax.plot(
                p_axis, burnrate_ideal, "r--", label="Ideal (> 4 MPa)", zorder=0
            )
            time_text = ax.text(0.02, 0.95, "", transform=ax.transAxes)
            text_x = p_max * 0.8
            text_y = (
                self.saint_roberts_law(text_x, a_fit, n_fit) * 0.9
                if a_fit is not None
                else 0
            )
            ax.text(
                text_x,
                text_y,
                f"r = {a_fit:.3f} P^({n_fit:.3f})" if a_fit is not None else "",
                color="red",
            )
            max_idx = output_data["burnrate[mm/s]"].idxmax()
            x_peak = output_data["pressure[MPa]"][max_idx]
            y_peak = output_data["burnrate[mm/s]"][max_idx]
            ax.scatter(x_peak, y_peak, marker="o", color="red", s=120, zorder=2)
            ax.annotate(
                "Peak: "
                + str(round(p_max, 2))
                + " MPa, \n          "
                + str(round(output_data["burnrate[mm/s]"].max(), 2))
                + " mm/s, \n          "
                + str(round(output_data["time[s]"][max_idx], 2))
                + " s",
                xy=(0.8, 0.87),
                xycoords="axes fraction",
            )
            ax.set_xlabel("Chamber Pressure (MPa)")
            ax.set_ylabel("Burnrate (mm/s)")
            fig.suptitle(base_name + " Burnrate-Pressure Animation", y=0.95)
            ax.legend()
            ax.set_xlim(0, p_max * 1.11)
            ax.set_ylim(
                0,
                max(
                    output_data["burnrate[mm/s]"].max(),
                    burnrate_ideal.max() if burnrate_ideal.size > 0 else 0,
                )
                * 1.15,
            )

            def init():
                line.set_data([], [])
                trail.set_data([], [])
                time_text.set_text("")
                return line, trail, time_text

            def animate(frame):
                idx = frame * 2  # Use every 2nd data point
                data = output_data.iloc[: idx + 1]
                line.set_data(
                    [data["pressure[MPa]"].iloc[-1]], [data["burnrate[mm/s]"].iloc[-1]]
                )
                trail.set_data(data["pressure[MPa]"], data["burnrate[mm/s]"])
                time_text.set_text(f"Time: {data['time[s]'].iloc[-1]:.2f} s")
                return line, trail, time_text

            frames = len(output_data) // 2
            interval = 50  # milliseconds
            anim = animation.FuncAnimation(
                fig,
                animate,
                init_func=init,
                frames=frames,
                interval=interval,
                blit=True,
            )
            anim.save(output_RP_anim_path, writer="pillow", dpi=100)
            plt.close()
        except Exception as e:
            self._logger.error(f"   3-5. Error saving Pressure-Burnrate animation: {e}")
            raise

    def run(self) -> None:
        """Process a given pressure data.

        Loads the data, calculates burnrate, and outputs CSV/graphs/animation.
        """
        self._logger.info("Starting burnrate analysis for file: %s", self.file_name)
        self.normalize_pressure_data()
        burnrate, burnrate_ideal, a_fit, n_fit = self.calc_burnrate(self.pressure_data)
        self.output_result(
            self.file_name, self.pressure_data, burnrate, burnrate_ideal, a_fit, n_fit
        )
        self._logger.info("Burnrate analysis completed for file: %s", self.file_name)


if __name__ == "__main__":
    # Read config.xlsx from execution root
    EXEC_ROOT = os.path.abspath(os.getcwd())
    config_path = os.path.join(EXEC_ROOT, "config.xlsx")
    if not os.path.exists(config_path):
        print(f"Configuration file not found: {config_path}")
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    config = pd.read_excel(config_path, sheet_name=0, header=0, index_col=0)
    idx = len(config) - 1
    if idx < 0:
        print(f"Configuration file is empty: {config_path}")
        raise ValueError(f"Configuration file is empty: {config_path}")

    # Ensure that all required columns are present.
    required_columns = [
        "Outerdiameter [mm]",
        "Innerdiameter [mm]",
        "singlegrainheight [mm]",
        "expt_file_name",
        "totalmass [g]",
        "Nozzlediameter [mm]",
        "segment",
    ]
    missing = [col for col in required_columns if col not in config.columns]
    if missing:
        raise ValueError(f"Missing columns in configuration: {missing}")

    # Load the grain parameters from the configuration
    grain = {
        "OD": float(config["Outerdiameter [mm]"][idx]),
        "ID": float(config["Innerdiameter [mm]"][idx]),
        "Height": float(config["singlegrainheight [mm]"][idx]),
        "Mass": float(config["totalmass [g]"][idx]),
        "Nozzlediameter": float(config["Nozzlediameter [mm]"][idx]),
        "N_Segment": float(config["segment"][idx]),
    }
    expt_file_name = config["expt_file_name"][idx]
    print(f"Loaded configuration for experiment: {expt_file_name}")

    # Determine the file to process using the configuration file
    pressure_data_dir = os.path.join(EXEC_ROOT, "results", "pressure")
    filename_csv = expt_file_name + "_pressure.csv"
    filename_txt = expt_file_name + "_pressure.txt"

    if os.path.exists(os.path.join(pressure_data_dir, filename_csv)):
        filename = filename_csv
    elif os.path.exists(os.path.join(pressure_data_dir, filename_txt)):
        filename = filename_txt
    else:
        raise FileNotFoundError(
            f"{filename_csv} or {filename_txt} does not exist. Please check the file path and name."
        )

    # Read and process data
    pressure_data = pd.read_csv(
        os.path.join(pressure_data_dir, filename), sep="[, ]", engine="python"
    )
    print("Successfully loaded input data file.")

    # Initialize the analyzer and process the file
    analyzer = BurnRateAnalyzer(pressure_data, grain, filename)
    analyzer.run()
