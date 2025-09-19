"""Thrust Data Post Processing Code.

2024.06.18
First written by Jiwan Seo (Project Manager of Rocketry club Hanaro)
E-mail: jiwan0216@snu.ac.kr

2025.01.22. Updated by Yunseo Kim <yunseo@snu.ac.kr>:
- Add the new DAQ's data format
- Improve the interpolation algorithm from CubicSpline to PCHIP
- Change output format from .txt(sep=' ') to .csv(sep=',')

2025.02.08. Updated by Yunseo Kim <yunseo@snu.ac.kr>:
- Added type hints and detailed docstrings
- Improved error handling and logging throughout
- Checks for duplicate or non-increasing timestamps and logs warnings
- Added validations and guidance when key data are missing or invalid
- Check and resolve the part where the deprecation warning occured

2025.02.17. Updated by Yunseo Kim <yunseo@snu.ac.kr>:
- To avoid file I/O errors based on the execution environment or current working directory,
  set the file paths to absolute paths using the OS module
- Encapsulate the logger within the class

2025.03.06. Updated by Yunseo Kim <yunseo@snu.ac.kr>:
- Add prevention of negative thrust values
- Add logging of max thrust value and its index
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from static_fire_toolkit.style import apply_default_style
from scipy.interpolate import PchipInterpolator
from scipy.signal import find_peaks, peak_widths, butter, lfilter
from scipy.ndimage import gaussian_filter1d
from scipy.integrate import simpson
import logging
from static_fire_toolkit.config_loader import load_global_config

# Add parent directory to Python path to import config (kept for backward compatibility of CLI entry)
sys.path.append(os.path.dirname(__file__))


class ThrustPostProcess:
    """End-to-end thrust post-processing pipeline.

    Responsibilities include raw input normalization, interval estimation,
    interpolation to a uniform timestep, filtering, baseline correction,
    metric extraction, plotting, and CSV export.
    """

    # Step 0. Initialize the object
    def __init__(
        self,
        data_raw: pd.DataFrame,
        file_name: str,
        excitation_voltage: float,
        resistance: float,
        execution_root: str | None = None,
    ) -> None:
        """Initialize the ThrustPostProcess object with raw data and configuration parameters.

        Args:
            data_raw (pd.DataFrame): Raw data containing time and thrust measurements.
            file_name (str): File name identifier.
            excitation_voltage (float): Excitation voltage used during measurement.
            resistance (float): Resistance value used during measurement.
            execution_root (str | None): Base directory for logs/ and results/*.
                If None, defaults to current working directory.

        Raises:
            ValueError: If data_raw is not a pandas DataFrame, is empty, or has insufficient columns.
        """
        self._BASE_DIR = os.path.abspath(os.path.dirname(__file__))
        # Use execution root for all I/O (logs/results)
        self._EXEC_ROOT = os.path.abspath(execution_root or os.getcwd())

        # Load configuration parameters explicitly
        self._CFG = load_global_config(self._EXEC_ROOT)
        self._sensitivity_mv_per_v = self._CFG.sensitivity_mv_per_v
        self._rated_capacity_kgf = self._CFG.rated_capacity_kgf
        self._g = 9.80665  # gravitational acceleration, m/s^2
        self._gain_internal_resistance_kohm = self._CFG.gain_internal_resistance_kohm
        self._gain_offset = self._CFG.gain_offset
        self._frequency = self._CFG.frequency
        self._cutoff_frequency = self._CFG.cutoff_frequency
        self._lowpass_order = self._CFG.lowpass_order
        self._gaussian_weak_sigma = self._CFG.gaussian_weak_sigma
        self._gaussian_strong_sigma = self._CFG.gaussian_strong_sigma
        self._start_criteria = self._CFG.start_criteria
        self._end_criteria = self._CFG.end_criteria
        self._thrust_time_col_idx = self._CFG.thrust_time_col_idx
        self._thrust_col_idx = self._CFG.thrust_col_idx

        # Set up logging
        self._logger = logging.getLogger(__name__)
        log_dir = os.path.join(self._EXEC_ROOT, "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_filename = os.path.join(log_dir, f"{file_name}-thrust_processing.log")

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

        self._logger.info("0. Initializing ThrustPostProcess object.")
        if not isinstance(data_raw, pd.DataFrame):
            self._logger.error("data_raw must be a pandas DataFrame.")
            raise ValueError("data_raw must be a pandas DataFrame.")

        if data_raw.empty:
            self._logger.error("Input data_raw DataFrame is empty.")
            raise ValueError("Input data_raw DataFrame is empty.")

        # 데이터 형태 확인
        rows, cols = data_raw.shape
        if cols > rows:  # 기존에 사용하던 구 형식: 호환을 위해 전치 필요
            self._logger.info("   Legacy data format detected: Transpose data")
            data_raw = data_raw.transpose()

        # Ensure enough columns
        if data_raw.shape[1] < 2:
            self._logger.error(
                "Input data must have at least two columns for time and thrust."
            )
            raise ValueError(
                "Input data must have at least two columns for time and thrust."
            )

        # Select columns based on configuration indices
        if (
            self._thrust_time_col_idx >= data_raw.shape[1]
            or self._thrust_col_idx >= data_raw.shape[1]
        ):
            self._logger.error(
                "Configured thrust column indices are out of bounds: time_idx=%d, thrust_idx=%d, cols=%d",
                self._thrust_time_col_idx,
                self._thrust_col_idx,
                data_raw.shape[1],
            )
            raise ValueError("Configured thrust column indices are out of bounds.")

        self._data_raw = data_raw.iloc[
            :, [self._thrust_time_col_idx, self._thrust_col_idx]
        ].copy()
        self._data_raw.columns = ["time", "thrust"]
        self._file_name: str = file_name
        self._excitation_voltage: float = excitation_voltage
        self._resistance: float = resistance

        self._logger.info("0. Initialization complete.")

    def _gaussian_filter(self, data: pd.DataFrame, sigma: float) -> pd.DataFrame:
        """Apply a Gaussian filter to the thrust data.

        Args:
            data (pd.DataFrame): DataFrame containing 'time' and 'thrust' columns.
            sigma (float): Standard deviation for the Gaussian kernel.

        Returns:
            pd.DataFrame: DataFrame with the filtered thrust data.
        """
        self._logger.info("   Applying Gaussian filter with sigma=%s.", sigma)
        try:
            if sigma <= 0:
                self._logger.error(
                    f"   Invalid sigma value: {sigma}. Must be positive."
                )
                raise ValueError(f"Invalid sigma value: {sigma}. Must be positive.")

            thrust_gaussian = gaussian_filter1d(data["thrust"], sigma)
            data_gaussian = pd.DataFrame(
                {"time": data["time"], "thrust": thrust_gaussian}
            )
            self._logger.info("   Gaussian filtering complete.")
            return data_gaussian
        except Exception as e:
            self._logger.error("   Error in Gaussian filtering: %s", e, exc_info=True)
            raise

    # Step 1-1
    def _convert_voltage_to_thrust(self, data: pd.DataFrame) -> pd.DataFrame:
        """Convert voltage to thrust using the provided formula.

        Args:
            data (pd.DataFrame): DataFrame containing 'time' and 'thrust' columns.

        Returns:
            pd.DataFrame: DataFrame with the converted thrust values.
        """
        self._logger.info("   1-1. Converting voltage to thrust.")
        try:
            # Validate required config parameters
            missing_params: list[str] = []
            if self._sensitivity_mv_per_v is None:
                missing_params.append("sensitivity_mv_per_v")
            if self._rated_capacity_kgf is None:
                missing_params.append("rated_capacity_kgf")
            if self._gain_internal_resistance_kohm is None:
                missing_params.append("gain_internal_resistance_kohm")
            if self._gain_offset is None:
                missing_params.append("gain_offset")
            if missing_params:
                self._logger.error(
                    "Missing required load cell config: %s", ", ".join(missing_params)
                )
                raise ValueError(
                    "Missing required load cell configuration: "
                    + ", ".join(missing_params)
                )
            # 전압 값을 추력으로 변환
            # Convert volts -> thrust(N) using sensitivity (mV/V), capacity(kgf), excitation voltage(V),
            # amplifier internal resistance (kOhm) and gain offset.
            # Formula adapted to new config naming; assumes linear behavior.
            data["thrust"] = (
                data["thrust"]
                * 1000
                / (self._sensitivity_mv_per_v * self._excitation_voltage)
                * self._rated_capacity_kgf
                * self._g
                / (
                    self._gain_offset
                    + self._gain_internal_resistance_kohm * 1000 / self._resistance
                )
            )
        except Exception as e:
            self._logger.error("Error converting voltage to thrust: %s", e)
            raise

        # 추력 데이터 부호 확인 후 필요하다면 반전
        if abs(data["thrust"].min()) > abs(data["thrust"].max()):
            self._logger.info(
                "   Inverting thrust values to maintain correct polarity."
            )
            data["thrust"] *= -1

        self._logger.info("   1-1. Voltage to thrust conversion complete.")
        return data

    # Step 1-2
    def _estimate_interval(self, data: pd.DataFrame) -> pd.DataFrame:
        """Estimate meaningful thrust interval by detecting the thrust peak.

        Uses a strong Gaussian filter to smooth the data, then identifies the peak and its width to define
        the start and end indices for the interval.

        Args:
            data (pd.DataFrame): DataFrame with 'time' and 'thrust' columns.

        Returns:
            pd.DataFrame: DataFrame cropped to the estimated interval.

        Raises:
            ValueError: If no peak is detected or if the detected peak width is zero.
        """
        self._logger.info("   1-2. Estimating interval of thrust data.")
        try:
            # Apply strong Gaussian filtering for smoothing.
            strong_filtered = self._gaussian_filter(data, self._gaussian_strong_sigma)
            thrust_max = strong_filtered["thrust"].max()
            peaks, _ = find_peaks(strong_filtered["thrust"], height=thrust_max)
            if len(peaks) == 0:
                self._logger.error("   1-2. No peak detected in the thrust data.")
                raise ValueError("No peak detected in the thrust data.")

            # Use the first detected peak.
            peak_index = peaks[0]
            widths = peak_widths(strong_filtered["thrust"], peaks, rel_height=0.5)
            width_value = widths[0][0]
            if width_value == 0:
                self._logger.error("   1-2. Detected peak width is zero.")
                raise ValueError("Detected peak width is zero.")

            start_index = int(peak_index - 2 * width_value)
            end_index = int(peak_index + 6 * width_value)
            start_index = max(start_index, 0)
            end_index = min(end_index, len(data))
            self._logger.info(
                "       Estimated interval indices: start_index=%d, end_index=%d.",
                start_index,
                end_index,
            )
            interval_data = data.iloc[start_index:end_index].copy()

            # Log time interval statistics.
            dt = np.diff(interval_data["time"].values)
            if np.any(dt <= 0):
                self._logger.warning("   1-2. Time values are not strictly increasing")
                interval_data = (
                    interval_data.groupby("time")["thrust"].mean().reset_index()
                )  # 중복된 시간값에 대해 평균 계산
                dt = np.diff(interval_data["time"].values)
            self._logger.info(
                "       Time interval statistics: min=%.6f, max=%.6f, mean=%.6f",
                dt.min(),
                dt.max(),
                dt.mean(),
            )

            # (Optional) Plot time interval distribution for debugging.
            plt.figure(figsize=(10, 6))
            plt.plot(interval_data["time"].iloc[1:], dt, "b.", markersize=2)
            plt.xlabel("Time (s)")
            plt.ylabel("dt (s)")
            plt.title("Time Interval Distribution")
            plt.grid(True)
            plt.show()

            self._logger.info("   1-2. Interval estimation complete.")
            return interval_data

        except Exception as e:
            self._logger.error(
                "   1-2. Error during interval estimation: %s", e, exc_info=True
            )
            raise

    # Step 1-3: Change to an evenly-spaced data with interpolation
    def _interpolate(self, data: pd.DataFrame) -> pd.DataFrame:
        """Interpolate thrust data using PCHIP to a uniform timestep.

        Args:
            data (pd.DataFrame): DataFrame with 'time' and 'thrust' columns.

        Returns:
            pd.DataFrame: Interpolated DataFrame with evenly spaced time points.

        Raises:
            ValueError: If interpolation fails due to invalid input data.
        """
        self._logger.info("   1-3. Starting interpolation of thrust data.")

        # PCHIP (Piecewise Cubic Hermite Interpolating Polynomial) interpolation
        # https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.PchipInterpolator.html
        #
        # - 단조성 보장: 시간에 따라 증가하거나 감소하는 경향성 유지
        # - 급격한 변화와 이상치에 덜 민감
        # - Cubic Spline과 달리 급격한 변화가 있는 경우에도 과도한 진동(overshooting) 발생하지 않음
        # - 단, 계산 비용은 약간 더 커짐

        try:
            time_interval = 1 / self._frequency
            time_interpolated = np.arange(0, data["time"].max(), time_interval)
            pchip_interp = PchipInterpolator(data["time"], data["thrust"])
            thrust_interpolated = pchip_interp(time_interpolated)
            data_interpolated = pd.DataFrame(
                {"time": time_interpolated, "thrust": thrust_interpolated}
            )
            self._logger.info(
                "   1-3. Interpolation complete. Generated %d data points.",
                len(data_interpolated),
            )
            return data_interpolated
        except Exception as e:
            self._logger.error(
                "   1-3. Error during interpolation: %s", e, exc_info=True
            )
            raise

    # Step 1-4: Low Pass Filter (LPF)
    def _low_pass_filter(self, data: pd.DataFrame) -> pd.DataFrame:
        """Apply a low-pass Butterworth filter to the interpolated thrust data.

        Args:
            data (pd.DataFrame): DataFrame with 'time' and 'thrust' columns.

        Returns:
            pd.DataFrame: Low-pass filtered data.
        """
        self._logger.info("   1-4. Applying low-pass filter to thrust data.")
        try:
            normal_cutoff = 2 * self._cutoff_frequency / self._frequency
            b, a = butter(self._lowpass_order, normal_cutoff, btype="low", analog=False)
            thrust_filtered = lfilter(b, a, data["thrust"])
            data_lpf = pd.DataFrame({"time": data["time"], "thrust": thrust_filtered})
            self._logger.info("   1-4. Low-pass filtering complete.")
            return data_lpf
        except Exception as e:
            self._logger.error(
                "   1-4. Error during low-pass filtering: %s", e, exc_info=True
            )
            raise

    # Step 1
    def _data_preset(self) -> None:
        """Preprocess raw data: interval estimate → interpolate → LPF → Gaussian."""
        self._logger.info("1. Starting data preset process.")
        try:
            self._data_raw = self._convert_voltage_to_thrust(self._data_raw)
            data_interval = self._estimate_interval(self._data_raw)
            data_interval = data_interval.reset_index(drop=True)
            data_interval["time"] = (
                data_interval["time"] - data_interval["time"].iloc[0]
            )
            data_interpolated = self._interpolate(data_interval)
            data_filtered = self._low_pass_filter(data_interpolated)
            self._data = self._gaussian_filter(data_filtered, self._gaussian_weak_sigma)
            self._logger.info("1. Data preset process complete.")
        except Exception as e:
            self._logger.error("Error during data preset: %s", e, exc_info=True)
            raise

    # Subfunction of step 2
    def _check_interval_criteria(
        self, diff: np.ndarray, max_index: int, min_index: int
    ) -> tuple[int, int]:
        """Adjust start/end indices based on predefined threshold criteria.

        Args:
            diff (np.ndarray): Array of differences between consecutive thrust values.
            max_index (int): Index corresponding to the maximum increase.
            min_index (int): Index corresponding to the maximum decrease.

        Returns:
            Tuple[int, int]: (start_index, end_index) after applying the criteria.
        """
        self._logger.info("   2-1. Checking interval criteria for indices.")
        start_index, end_index = max_index, min_index
        try:
            # Adjust start_index: move backward until the ratio is below the start_criteria.
            while (
                start_index > 0
                and diff[start_index] / np.max(diff) > self._start_criteria
            ):
                start_index -= 1
            # Adjust end_index: move forward until the ratio is below the end_criteria.
            while (
                end_index < len(diff) - 1
                and diff[end_index] / np.min(diff) > self._end_criteria
            ):
                end_index += 1
        except Exception as e:
            self._logger.error(
                "   2-1. Error while checking interval criteria: %s", e, exc_info=True
            )
            raise

        self._logger.info(
            "   2-1. Adjusted indices: start_index=%d, end_index=%d.",
            start_index,
            end_index,
        )
        return (start_index, end_index)

    # Step 2: Select meaningful interval
    def _find_interval(self) -> None:
        """Identify and extract a meaningful time interval from processed thrust data."""
        self._logger.info("2. Finding meaningful data interval.")
        try:
            thrust_values = self._data["thrust"].values
            if len(thrust_values) < 2:
                self._logger.error("Insufficient data points for finding interval.")
                raise ValueError("Insufficient data points for finding interval.")

            # Compute the difference between consecutive thrust values.
            diff = np.diff(thrust_values)
            diff_filtered = gaussian_filter1d(diff, self._gaussian_strong_sigma)
            max_index = int(np.argmax(diff_filtered))
            min_index = int(np.argmin(diff_filtered))
            self._logger.info(
                "   Initial max_index=%d, min_index=%d based on diff.",
                max_index,
                min_index,
            )
            start_index, end_index = self._check_interval_criteria(
                diff_filtered, max_index, min_index
            )

            self._data_cut = self._data.iloc[start_index:end_index].copy()
            self._data_cut = self._data_cut.reset_index(drop=True)
            self._data_cut["time"] = (
                self._data_cut["time"] - self._data_cut["time"].iloc[0]
            )
            self._logger.info(
                "2. Found interval from index %d to %d.", start_index, end_index
            )
        except Exception as e:
            self._logger.error("2. Error in finding interval: %s", e, exc_info=True)
            raise

    # Step 3: linear shifting from the start point to the end point
    def _shift(self) -> None:
        """Apply a linear shift to the cut thrust data to remove baseline drift and compute the impulse.

        The impulse is calculated using Simpson's integration.
        """
        self._logger.info("3. Starting thrust data shifting.")
        try:
            if self._data_cut.empty:
                self._logger.error(
                    "_data_cut is empty. Cannot perform shift operation."
                )
                raise ValueError("_data_cut is empty.")

            thrust_initial = self._data_cut["thrust"].iloc[0]
            thrust_final = self._data_cut["thrust"].iloc[-1]
            time_total = self._data_cut["time"].iloc[-1]
            if time_total == 0:
                self._logger.error("Total time is zero. Cannot shift data.")
                raise ValueError("Total time is zero.")

            # Compute the linear baseline.
            slope = (thrust_final - thrust_initial) / time_total
            thrust_shifted = (
                self._data_cut["thrust"]
                - thrust_initial
                - slope * self._data_cut["time"]
            )
            # (2025.03.06.) Remove negative values
            thrust_shifted = thrust_shifted - min(thrust_shifted.min(), 0)

            self._data_shifted = pd.DataFrame(
                {"time": self._data_cut["time"].copy(), "thrust": thrust_shifted}
            )
            self._impulse = simpson(
                self._data_shifted["thrust"], x=self._data_shifted["time"]
            )
            self._max_thrust_index = self._data_shifted["thrust"].idxmax()
            self._logger.info(
                "3. Data shifting complete. Computed impulse: %.3f Ns.", self._impulse
            )
            self._logger.info(
                "3. Max thrust: %f N at time: %.2f s.",
                self._data_shifted["thrust"].iloc[self._max_thrust_index],
                self._data_shifted["time"].iloc[self._max_thrust_index],
            )
            self._logger.info("3. Max thrust index: %d.", self._max_thrust_index)
            self._logger.info(
                "3. Min thrust: %.2f N", self._data_shifted["thrust"].min()
            )
        except Exception as e:
            self._logger.error("3. Error during shifting: %s", e, exc_info=True)
            raise

    # Subfunction of step 4
    def _find_time(self) -> tuple[int, int, int]:
        """Determine key time indices for the thrust curve.

        - start_index: First index where thrust exceeds 10% of the maximum.
        - burn_time_index: Index (moving backward from the max) where thrust exceeds 75% of the maximum.
        - action_time_index: Index (moving backward from the max) where thrust is above 10% of the maximum.

        Returns:
            Tuple[int, int, int]: (start_index, burn_time_index, action_time_index)

        Raises:
            ValueError: If the indices cannot be determined.
        """
        self._logger.info("   4-1. Finding key time indices from shifted data.")
        try:
            thrust_series = self._data_shifted["thrust"]
            max_thrust = thrust_series.max()
            if max_thrust <= 0:
                self._logger.error(
                    "Maximum thrust is non-positive. Invalid data for time index determination."
                )
                raise ValueError("Maximum thrust is non-positive.")

            start_index = 0
            burn_time_index = thrust_series.idxmax()
            action_time_index = thrust_series.idxmax()

            # Find the start index: first index where thrust exceeds 10% of max.
            while (
                start_index < len(thrust_series)
                and thrust_series.iloc[start_index] < 0.05 * max_thrust
            ):
                start_index += 1
            if start_index >= len(thrust_series):
                self._logger.error(
                    "Unable to find start index where thrust exceeds 5%% of max."
                )
                raise ValueError("Start index not found.")

            # Adjust burn_time_index: move backwards until thrust is at least 75% of max.
            while (
                burn_time_index > 0
                and thrust_series.iloc[burn_time_index] < 0.75 * max_thrust
            ):
                burn_time_index -= 1
            if burn_time_index < 0:
                self._logger.error("Unable to determine burn time index.")
                raise ValueError("Burn time index not found.")

            # Adjust action_time_index: move backwards until thrust is above 10% of max.
            while (
                action_time_index > 0
                and thrust_series.iloc[action_time_index] < 0.1 * max_thrust
            ):
                action_time_index -= 1
            if action_time_index < 0:
                self._logger.error("Unable to determine action time index.")
                raise ValueError("Action time index not found.")

            self._logger.info(
                "   4-1. Key time indices found: start_index=%d, burn_time_index=%d, action_time_index=%d.",
                start_index,
                burn_time_index,
                action_time_index,
            )
            return (start_index, burn_time_index, action_time_index)
        except Exception as e:
            self._logger.error(
                "   4-1. Error while finding time indices: %s", e, exc_info=True
            )
            raise

    # Step 4
    def _thrust_plot(self) -> None:
        """Plot the shifted thrust data with annotations and save the plot to a file."""
        # Ensure default style is applied for consistency
        apply_default_style()
        self._logger.info("4. Plotting thrust data.")
        try:
            start_index, burn_time_index, action_time_index = self._find_time()
            total_time = self._data_shifted["time"].iloc[-1]

            max_thrust = max(self._data_shifted["thrust"])
            max_thrust_time = self._data_shifted["time"][self._max_thrust_index]
            x = [max_thrust_time, total_time]
            y = [max_thrust, 0]

            fig, ax = plt.subplots(figsize=(16, 9))
            ax.plot(
                self._data_shifted["time"],
                self._data_shifted["thrust"],
                color="black",
                linewidth=2.5,
                zorder=0,
            )
            ax.scatter(x, y, marker="o", color="red", s=120, zorder=1)

            ax.set_xlim([0, 1.11 * total_time])
            ax.set_ylim([-0.05 * max_thrust, 1.12 * max_thrust])

            ax.annotate(
                "Max Thrust   " + str(round(max_thrust, 2)) + " N",
                xy=(max_thrust_time / total_time * 0.65, 0.94),
                xycoords="axes fraction",
                size=20,
                font="Arial",
            )

            ax.annotate(
                "Total Time\n" + str(round(total_time, 2)) + " s",
                xy=(0.89, 0.12),
                xycoords="axes fraction",
                size=20,
                font="Arial",
            )

            ax.annotate(
                "Impulse                 " + str(round(self._impulse, 2)) + " Ns\n"
                "Excitation Voltage " + str(round(self._excitation_voltage, 2)) + " V\n"
                "Resistance            "
                + str(round(self._resistance, 2))
                + r" $\Omega$",
                xy=(0.67, 0.85),
                xycoords="axes fraction",
                size=20,
                font="Arial",
            )

            ax.set_xlabel("Time [s]", size=20, font="Arial")
            ax.xaxis.set_label_coords(0.5, -0.07)
            ax.set_ylabel("Thrust [N]", size=20, font="Arial")
            ax.yaxis.set_label_coords(-0.07, 0.5)
            fig.suptitle(
                self._file_name + " Thrust Graph",
                y=0.95,
                fontsize=25,
                fontweight="bold",
                font="Arial",
            )
            ax.grid(True)
            ax.tick_params(axis="both", which="major", labelsize=15)
            output_dir = os.path.join(self._EXEC_ROOT, "results", "thrust_graph")
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"{self._file_name}_thrust.png")
            plt.savefig(output_path, bbox_inches=None, pad_inches=0, dpi=500)
            plt.show()
            self._logger.info("4. Thrust plot saved to %s", output_path)
        except Exception as e:
            self._logger.error(
                "4. Error during plotting thrust data: %s", e, exc_info=True
            )
            raise

    # Step 5
    def _data_save(self) -> None:
        """Save processed thrust data to a CSV file."""
        self._logger.info("5. Saving processed thrust data.")
        try:
            output_dir = os.path.join(self._EXEC_ROOT, "results", "thrust")
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, f"{self._file_name}_thrust.csv")
            # self._data_shifted.to_csv('./../thrust_post_process/'+self._file_name+ '_thrust.txt', sep = ' ', index=False)
            self._data_shifted.copy().to_csv(output_file, index=False)
            self._logger.info("5. Data saved successfully to %s", output_file)
        except Exception as e:
            self._logger.error("5. Error saving data: %s", e, exc_info=True)
            raise

    def run(self) -> pd.DataFrame:
        """Run the full thrust data processing pipeline."""
        self._logger.info("Starting thrust data processing pipeline.")
        self._data_preset()
        self._find_interval()
        self._shift()
        self._thrust_plot()
        self._data_save()
        self._logger.info("Thrust data processing pipeline complete.")
        return self._data_shifted


if __name__ == "__main__":
    # Read config.xlsx from execution root
    EXEC_ROOT = os.path.abspath(os.getcwd())
    config_path = os.path.join(EXEC_ROOT, "config.xlsx")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    config = pd.read_excel(config_path, sheet_name=0, header=0, index_col=0)
    idx = len(config) - 1
    expt_file_name = config["expt_file_name"][idx]
    # Backward-compatible: read excitation voltage from new or legacy column
    if "expt_excitation_voltage [V]" in config.columns:
        expt_excitation_voltage = config["expt_excitation_voltage [V]"][idx]
    elif "expt_input_voltage [V]" in config.columns:
        expt_excitation_voltage = config["expt_input_voltage [V]"][idx]
    else:
        raise ValueError(
            "Missing excitation voltage column: expected 'expt_excitation_voltage [V]' or legacy 'expt_input_voltage [V]'"
        )
    expt_resistance = config["expt_resistance [Ohm]"][idx]

    print(f"Loaded configuration for experiment: {expt_file_name}")

    # 파일 경로 설정
    raw_data_path = os.path.join(EXEC_ROOT, "data", "_thrust_raw")
    csv_path = os.path.join(raw_data_path, f"{expt_file_name}_thrust_raw.csv")
    txt_path = os.path.join(raw_data_path, f"{expt_file_name}_thrust_raw.txt")

    # csv 파일이 존재하면 csv 파일을, 아니면 txt 파일을 읽음
    if os.path.exists(csv_path):
        data_file = csv_path
        print(f"Using CSV thrust data file: {csv_path}")
    elif os.path.exists(txt_path):
        data_file = txt_path
        print(f"Using TXT thrust data file: {txt_path}")
    else:
        error_msg = f"No thrust data file found at {csv_path} or {txt_path}"
        print(error_msg)
        raise FileNotFoundError(error_msg)

    from static_fire_toolkit.config_loader import load_global_config

    cfg = load_global_config(EXEC_ROOT)
    thrust_sep = str(getattr(cfg, "thrust_sep", ","))
    thrust_header = getattr(cfg, "thrust_header", 0)
    thrust_data = pd.read_csv(data_file, sep=thrust_sep, header=thrust_header)
    print("Successfully loaded input data file.")

    process = ThrustPostProcess(
        thrust_data, expt_file_name, expt_excitation_voltage, expt_resistance
    )
    _ = process.run()
