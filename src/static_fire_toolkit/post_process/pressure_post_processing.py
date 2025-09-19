"""Pressure Data Post Processing Code.

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
- Added data validation and warning messages

2025.02.17. Updated by Yunseo Kim <yunseo@snu.ac.kr>:
- To avoid file I/O errors based on the execution environment or current working directory,
  set the file paths to absolute paths using the OS module
- Encapsulate the logger within the class

2025.03.06. Updated by Yunseo Kim <yunseo@snu.ac.kr>:
- Improve the baseline estimation process
- Add more detailed logging of peak detection for debugging
- Add fallback width value(20) for too small peak widths (< 1.0)
- Add logging of basic statistics (max, min, mean, std) for pressure raw data before processing
- Add logging of maximum pressure value and its index after shifting
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from static_fire_toolkit.style import apply_default_style
from scipy.interpolate import PchipInterpolator
from scipy.signal import find_peaks, peak_widths
from scipy.integrate import simpson
import logging
from static_fire_toolkit.config_loader import load_global_config

# Add parent directory to Python path to import config
sys.path.append(os.path.dirname(__file__))


class PressurePostProcess:
    """Pressure post-processing pipeline for static-fire data.

    Handles interval estimation, interpolation to a uniform timestep, baseline
    normalization, metrics, plotting, and CSV export. Synchronizes to thrust
    data for consistent time windows.
    """

    def __init__(
        self,
        pressure_data_raw: pd.DataFrame,
        thrust_data: pd.DataFrame,
        file_name: str,
        execution_root: str | None = None,
    ) -> None:
        """Initialize the PressurePostProcess object with raw pressure data and configuration parameters.

        Args:
            pressure_data_raw (pd.DataFrame): Raw data containing time and pressure measurements
            thrust_data (pd.DataFrame): Processed thrust data for synchronization
            file_name (str): File name identifier for logging and output
            execution_root (str | None): Base directory for logs/ and results/*.
                If None, defaults to current working directory.

        Raises:
            ValueError: If input data is invalid or missing required columns
        """
        self._BASE_DIR = os.path.abspath(os.path.dirname(__file__))
        # Use execution root for all I/O (logs/results)
        self._EXEC_ROOT = os.path.abspath(execution_root or os.getcwd())
        # Load global configuration from execution root
        self._CFG = load_global_config(self._EXEC_ROOT)
        self._frequency = self._CFG.frequency
        self._pressure_time_col_idx = self._CFG.pressure_time_col_idx
        self._pressure_col_idx = self._CFG.pressure_col_idx

        # Set up logging
        self._logger = logging.getLogger(__name__)
        log_dir = os.path.join(self._EXEC_ROOT, "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_filename = os.path.join(log_dir, f"{file_name}-pressure_processing.log")

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

        self._logger.info("0. Initializing PressurePostProcess object")

        # Validate inputs
        if not isinstance(pressure_data_raw, pd.DataFrame):
            self._logger.error("pressure_data_raw must be a pandas DataFrame")
            raise ValueError("pressure_data_raw must be a pandas DataFrame")

        if not isinstance(thrust_data, pd.DataFrame):
            self._logger.error("thrust_data must be a pandas DataFrame")
            raise ValueError("thrust_data must be a pandas DataFrame")

        if pressure_data_raw.empty or thrust_data.empty:
            self._logger.error("Input DataFrames cannot be empty")
            raise ValueError("Input DataFrames cannot be empty")

        self._thrust_data = thrust_data
        self._file_name = file_name

        # Process raw pressure data
        try:
            # Ensure enough columns
            if pressure_data_raw.shape[1] < 2:
                self._logger.error(
                    "Input data must have at least two columns for time, pressure"
                )
                raise ValueError(
                    "Input data must have at least two columns for time, pressure"
                )

            # Bounds check for configured indices
            if (
                self._pressure_time_col_idx >= pressure_data_raw.shape[1]
                or self._pressure_col_idx >= pressure_data_raw.shape[1]
            ):
                self._logger.error(
                    "Configured pressure column indices are out of bounds: time_idx=%d, pressure_idx=%d, cols=%d",
                    self._pressure_time_col_idx,
                    self._pressure_col_idx,
                    pressure_data_raw.shape[1],
                )
                raise ValueError(
                    "Configured pressure column indices are out of bounds."
                )

            self._data_raw = pressure_data_raw.iloc[
                :, [self._pressure_time_col_idx, self._pressure_col_idx]
            ].copy()
            self._data_raw.columns = ["time", "pressure"]
            self._data_raw["pressure"] = pd.to_numeric(
                self._data_raw["pressure"], errors="coerce"
            )

            # Check for NaN values after conversion
            if self._data_raw["pressure"].isna().any():
                self._logger.warning(
                    "Some pressure values could not be converted to numeric format"
                )
                # Clean NaN values by forward fill, then backward fill
                self._data_raw["pressure"].fillna(method="ffill").fillna(
                    method="bfill", inplace=True
                )

            self._logger.info("0. Successfully initialized pressure data processing")

        except Exception as e:
            self._logger.error(f"Error processing raw pressure data: {str(e)}")
            raise

    # Step 1-1
    def _estimate_interval(self, data: pd.DataFrame) -> pd.DataFrame:
        """Estimate the meaningful interval of pressure data based on peak detection.

        Args:
            data (pd.DataFrame): DataFrame containing 'time' and 'pressure' columns

        Returns:
            pd.DataFrame: Subset of data containing the estimated interval

        Raises:
            ValueError: If required columns are missing or peak detection fails
        """
        self._logger.info("   1-1. Estimating interval of pressure data")
        try:
            pressure_max = data["pressure"].max()  # maximum pressure
            # peaks, _ = find_peaks(data['pressure'], height=pressure_max)
            # (2025.03.06.) 피크 감지 개선: 초기 탐색에서는 상대적인 높이를 사용하고, 피크 인식 기준을 완화하여 더 많은 피크를 찾도록 함
            # 이는 여러 개의 피크가 존재하는 데이터에 대해 보다 강건한(robust) 피크 탐색 및 유사시 수월한 디버깅을 가능하도록 하기 위함임.
            pressure_min = data["pressure"].min()
            # 피크 감지 기준 설정: 1 이상이면서, 최대 압력 피크의 0.5배 이상이어야 함
            pressure_height = max(0.5 * (pressure_max - pressure_min), 1)

            peaks, peak_properties = find_peaks(
                data["pressure"], height=pressure_min + pressure_height, distance=5
            )  # 최소 피크 간격

            if len(peaks) == 0:
                self._logger.error("   1-1. No peak detected in the pressure data")
                raise ValueError("No peak detected in the pressure data")

            # (2025.03.06.) 첫 번째 피크가 아닌 가장 높은 피크를 사용하도록 변경.
            # 이는 여러 개의 피크가 존재하는 데이터에 대해 보다 강건한(robust) 피크 탐색 및 유사시 수월한 디버깅을 가능하도록 하기 위함임.
            # peak_index = peaks[0]
            peak_heights = peak_properties["peak_heights"]
            max_peak_idx = np.argmax(peak_heights)
            peak_index = peaks[max_peak_idx]

            # 탐지한 피크 목록 및 최대 피크 기록
            self._logger.info("   1-1. Detected %d peaks.", len(peaks))
            for i, peak in enumerate(peaks):
                self._logger.info(
                    "      - Peak %d: index %d, height %.2f", i, peak, peak_heights[i]
                )
            self._logger.info(
                "   1-1. Using highest peak at index %d with value %.2f",
                peak_index,
                data["pressure"].iloc[peak_index],
            )

            # 피크의 폭 계산
            widths = peak_widths(data["pressure"], [peak_index], rel_height=0.5)
            width_value = widths[0][0]
            self._logger.info("   1-1. Detected peak width: %.2f", width_value)
            if width_value == 0 or width_value < 1.0:
                self._logger.warning(
                    "   1-1. Detected peak width is very small: %.2f. Using fallback default width(20).",
                    width_value,
                )
                width_value = 20.0  # fallback default width

            # Calculate indices with bounds checking
            start_index = max(0, int(peak_index - 2 * width_value))
            end_index = min(len(data), int(peak_index + 6 * width_value))

            self._logger.info(
                "       Estimated interval indices: start_index=%d, end_index=%d.",
                start_index,
                end_index,
            )
            interval_data = data[start_index:end_index].copy()

            # Debug plotting of interval_data
            """
            import matplotlib.pyplot as plt
            plt.figure()
            plt.plot(interval_data['time'], interval_data['pressure'], marker='o', linestyle='-')
            plt.title('Interval Data Plot')
            plt.xlabel('Time (s)')
            plt.ylabel('Pressure')
            plt.show()
            """

            # Log time interval statistics.
            dt = np.diff(interval_data["time"].values)
            if np.any(dt <= 0):
                self._logger.warning("   1-1. Time values are not strictly increasing")
                # 중복된 시간값 처리: 그룹화 후 평균 계산
                interval_data = (
                    interval_data.groupby("time")["pressure"].mean().reset_index()
                )
                dt = np.diff(interval_data["time"].values)
            self._logger.info(
                "       Time interval statistics: min=%.6f, max=%.6f, mean=%.6f",
                dt.min(),
                dt.max(),
                dt.mean(),
            )

            return interval_data

        except Exception as e:
            self._logger.error(
                "  1-1. Error during interval estimation: %s", e, exc_info=True
            )
            raise

    # Step 1-2: Change to an evenly-spaced data with spline interpolation
    def _interpolate(self, data: pd.DataFrame) -> pd.DataFrame:
        """Interpolate pressure data using PCHIP to uniform timesteps.

        Args:
            data (pd.DataFrame): DataFrame containing 'time' and 'pressure' columns

        Returns:
            pd.DataFrame: Interpolated data with evenly spaced time points

        Raises:
            ValueError: If required columns are missing or interpolation fails
        """
        self._logger.info("   1-2. Starting interpolation of pressure data.")
        try:
            time_interval = 1 / self._frequency

            # PCHIP interpolation
            spline_function = PchipInterpolator(data["time"], data["pressure"])
            time_interpolated = np.arange(0, data["time"].max(), time_interval)
            pressure_interpolated = spline_function(time_interpolated)
            data_interpolated = pd.DataFrame(
                {"time": time_interpolated, "pressure": pressure_interpolated}
            )

            self._logger.info(
                "   1-2. Interpolation complete. Generated %d data points.",
                len(data_interpolated),
            )
            return data_interpolated

        except Exception as e:
            self._logger.error(
                "   1-2. Error during interpolation: %s", e, exc_info=True
            )
            raise

    # Step 1
    def _data_preset(self) -> None:
        """Prepare raw pressure data by estimating interval and interpolating.

        This method combines interval estimation and interpolation steps.

        Raises:
            ValueError: If data processing fails at any step
        """
        self._logger.info("1. Starting data preset process.")
        try:
            # data validation
            if (
                "time" not in self._data_raw.columns
                or "pressure" not in self._data_raw.columns
            ):
                self._logger.error("1. Missing required columns in raw data")
                raise ValueError(
                    "Missing required columns 'time' or 'pressure' in raw data"
                )

            # initial statistics of pressure raw data
            pressure_stats = self._data_raw["pressure"].describe()
            self._logger.info(
                "1. Pressure data statistics: min=%.3f, max=%.3f, mean=%.3f, std=%.3f",
                pressure_stats["min"],
                pressure_stats["max"],
                pressure_stats["mean"],
                pressure_stats["std"],
            )

            try:
                # Convert time strings to seconds more efficiently using vectorized operations
                self._data_raw["time"] = pd.to_datetime(self._data_raw["time"])
                data_time_zero = self._data_raw["time"].iloc[0]
                self._data_raw["time"] = (
                    self._data_raw["time"] - data_time_zero
                ).dt.total_seconds()

                # Round to microsecond precision to avoid floating point errors
                self._data_raw["time"] = self._data_raw["time"].round(6)

            except ValueError as e:
                self._logger.error(f"1. Error parsing time format: {str(e)}")
                raise

            # 구간 추정 및 데이터 보간
            data_interval = self._estimate_interval(self._data_raw)
            data_interval = data_interval.reset_index(drop=True)

            self._data = self._interpolate(data_interval)
            self._logger.info("1. Data preset process complete.")

        except Exception as e:
            self._logger.error("1. Error during data preset: %s", e, exc_info=True)
            raise

    # Step 2: Select meaningful interval
    def _find_interval(self) -> None:
        """Select meaningful interval synchronized with thrust data.

        This aligns pressure data with thrust data based on peak locations.

        Raises:
            ValueError: If synchronization fails
        """
        self._logger.info("2. Finding interval synchronized with thrust data")
        try:
            if "thrust" not in self._thrust_data.columns:
                self._logger.error("2. Thrust data must contain 'thrust' column")
                raise ValueError("Thrust data must contain 'thrust' column")

            max_thrust_index = self._thrust_data["thrust"].idxmax()
            increase_length = max_thrust_index
            decrease_length = len(self._thrust_data["thrust"]) - max_thrust_index

            max_pressure_index = self._data["pressure"].idxmax()

            # Calculate indices with bounds checking
            start_index = max(0, max_pressure_index - increase_length)
            end_index = min(len(self._data), max_pressure_index + decrease_length)

            self._data_cut = self._data[start_index:end_index].copy()
            self._data_cut = self._data_cut.reset_index(drop=True)
            self._data_cut["time"] -= self._data_cut["time"][0]

            self._logger.info("2. Successfully synchronized intervals")

        except Exception as e:
            self._logger.error(f"2. Error in interval synchronization: {str(e)}")
            raise

    # Step 3: linear shifting from the start point to the end point
    def _shift(self) -> None:
        """Apply linear shift to normalize baseline pressure.

        Calculates the difference between initial local pressure and standard
        atmosphere (1.013 bar) and shifts the series accordingly.

        Raises:
            ValueError: If shifting operation fails.
        """
        self._logger.info("3. Starting pressure data shifting.")
        try:
            if self._data_raw.empty or self._data_cut.empty:
                self._logger.error("Data not properly initialized for shifting")
                raise ValueError("Data not properly initialized for shifting")

            # shifted_value = self._data_raw['pressure'][0] - 1.013
            # (2025.03.06.) 표준대기압으로 보정 시 처음 10개 데이터포인트의 평균을 사용하여 베이스라인 계산
            # 이는 첫 번째 데이터 포인트에만 의존하는 것보다 더 안정적임
            baseline_samples = min(10, len(self._data_raw))
            baseline = self._data_raw["pressure"].iloc[:baseline_samples].mean()
            shifted_value = baseline - 1.013

            pressure_shifted = self._data_cut["pressure"] - shifted_value

            self._data_shifted = pd.DataFrame(
                {"time": self._data_cut["time"].copy(), "pressure": pressure_shifted}
            )

            self._max_pressure_index = self._data_shifted["pressure"].idxmax()
            self._logger.info(
                "3. Data shifting complete. (shift value: %.3f [bar])", -shifted_value
            )

            # 최대 압력 위치 기록
            self._max_pressure_index = self._data_shifted["pressure"].idxmax()
            max_pressure = self._data_shifted["pressure"].max()
            self._logger.info(
                f"3. Maximum pressure: {max_pressure:.2f} bar at index {self._max_pressure_index}"
            )

        except Exception as e:
            self._logger.error(f"3. Error during shifting: {str(e)}")
            raise

    # Step 4
    def _pressure_plot(self) -> None:
        """Plot the shifted pressure data with annotations and save the plot as an image file."""
        # Ensure default style is applied for consistency
        apply_default_style()
        self._logger.info("4. Plotting pressure data.")
        try:
            # Calculate key metrics
            pressure_integral = simpson(
                self._data_shifted["pressure"], x=self._data_shifted["time"]
            )
            total_time = self._data_shifted["time"].max()
            average_pressure = pressure_integral / total_time
            max_pressure = self._data_shifted["pressure"].max()
            max_pressure_time = self._data_shifted["time"][self._max_pressure_index]

            # Create plot
            fig, ax = plt.subplots(figsize=(16, 9))

            # Plot main data
            ax.plot(
                self._data_shifted["time"],
                self._data_shifted["pressure"],
                color="black",
                linewidth=2.5,
                zorder=0,
            )

            # Add key points
            x = [max_pressure_time, total_time]
            y = [max_pressure, self._data_shifted["pressure"].iloc[-1]]
            ax.scatter(x, y, marker="o", color="red", s=120, zorder=1)

            # Set limits
            ax.set_xlim([0, 1.11 * total_time])
            ax.set_ylim([-0.05 * max_pressure, 1.12 * max_pressure])

            # Add annotations
            ax.annotate(
                f"Max Pressure   {max_pressure:.2f} Bar",
                xy=(max_pressure_time / total_time * 0.65, 0.94),
                xycoords="axes fraction",
                size=20,
                font="Arial",
            )

            ax.annotate(
                f"Total Time\n{total_time:.2f} s",
                xy=(0.89, 0.12),
                xycoords="axes fraction",
                size=20,
                font="Arial",
            )

            ax.annotate(
                f"Average Pressure   {average_pressure:.2f} Bar",
                xy=(0.69, 0.94),
                xycoords="axes fraction",
                size=20,
                font="Arial",
            )

            # Set labels and title
            ax.set_xlabel("Time [s]", size=20, font="Arial")
            ax.xaxis.set_label_coords(0.5, -0.07)
            ax.set_ylabel("Pressure [Bar]", size=20, font="Arial")
            ax.yaxis.set_label_coords(-0.07, 0.5)

            fig.suptitle(
                f"{self._file_name} Pressure Graph",
                y=0.95,
                fontsize=25,
                fontweight="bold",
                font="Arial",
            )

            # Customize grid and ticks
            ax.grid(True)
            ax.tick_params(axis="both", which="major", labelsize=15)

            # Save and display
            save_path = os.path.join(
                self._EXEC_ROOT,
                "results",
                "pressure_graph",
                f"{self._file_name}_pressure.png",
            )
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            plt.savefig(save_path, bbox_inches=None, pad_inches=0, dpi=500)
            plt.show()

            self._logger.info("4. Pressure plot saved to %s", save_path)

        except Exception as e:
            self._logger.error(
                "4. Error during plotting pressure data: %s", e, exc_info=True
            )
            raise

    # Step 5
    def _data_save(self) -> None:
        """Save processed pressure data to CSV file."""
        self._logger.info("5. Saving processed pressure data")
        try:
            save_dir = os.path.join(self._EXEC_ROOT, "results", "pressure")
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, f"{self._file_name}_pressure.csv")

            self._data_shifted.to_csv(save_path, index=False)
            self._logger.info(f"5. Data saved successfully to {save_path}")

        except Exception as e:
            self._logger.error(f"5. Error saving data: {str(e)}")
            raise

    def run(self) -> pd.DataFrame:
        """Run the full pressure data processing pipeline."""
        self._logger.info("Starting pressure data processing pipeline.")
        self._data_preset()
        self._find_interval()
        self._shift()
        self._pressure_plot()
        self._data_save()
        self._logger.info("Pressure data processing pipeline complete.")
        return self._data_shifted


if __name__ == "__main__":
    # Read config.xlsx from execution root
    EXEC_ROOT = os.path.abspath(os.getcwd())
    config_path = os.path.join(EXEC_ROOT, "config.xlsx")
    if not os.path.exists(config_path):
        print(f"Configuration file not found: {config_path}")
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    config = pd.read_excel(config_path, sheet_name=0, header=0, index_col=0)
    idx = len(config) - 1
    expt_file_name = config["expt_file_name"][idx]
    print(f"Loaded configuration for experiment: {expt_file_name}")

    # Set up file paths
    thrust_dir = os.path.join(EXEC_ROOT, "results", "thrust")
    pressure_raw_dir = os.path.join(EXEC_ROOT, "data", "_pressure_raw")

    # Define file paths
    thrust_csv_path = os.path.join(thrust_dir, f"{expt_file_name}_thrust.csv")
    thrust_txt_path = os.path.join(thrust_dir, f"{expt_file_name}_thrust.txt")
    pressure_csv_path = os.path.join(
        pressure_raw_dir, f"{expt_file_name}_pressure_raw.csv"
    )
    pressure_txt_path = os.path.join(
        pressure_raw_dir, f"{expt_file_name}_pressure_raw.txt"
    )

    # Find pressure data file
    if os.path.exists(pressure_csv_path):
        pressure_data_file = pressure_csv_path
        print(f"Using CSV pressure data file: {pressure_csv_path}")
    elif os.path.exists(pressure_txt_path):
        pressure_data_file = pressure_txt_path
        print(f"Using TXT pressure data file: {pressure_txt_path}")
    else:
        error_msg = (
            f"No pressure data file found at {pressure_csv_path} or {pressure_txt_path}"
        )
        print(error_msg)
        raise FileNotFoundError(error_msg)

    # Find thrust data file
    if os.path.exists(thrust_csv_path):
        thrust_data_file = thrust_csv_path
        print(f"Using CSV thrust data file: {thrust_csv_path}")
    elif os.path.exists(thrust_txt_path):
        thrust_data_file = thrust_txt_path
        print(f"Using TXT thrust data file: {thrust_txt_path}")
    else:
        error_msg = (
            f"No thrust data file found at {thrust_csv_path} or {thrust_txt_path}"
        )
        print(error_msg)
        raise FileNotFoundError(error_msg)

    # Read and process data
    from static_fire_toolkit.config_loader import load_global_config

    cfg = load_global_config(EXEC_ROOT)
    pressure_sep = str(getattr(cfg, "pressure_sep", ","))
    pressure_header = getattr(cfg, "pressure_header", 0)
    pressure_data = pd.read_csv(
        pressure_data_file, sep=pressure_sep, header=pressure_header, engine="python"
    )
    # Processed thrust CSV is always saved with comma separator by toolkit
    thrust_data = pd.read_csv(thrust_data_file)
    print("Successfully loaded input data files.")

    # Initialize processor and run processing steps
    process = PressurePostProcess(pressure_data, thrust_data, expt_file_name)
    _ = process.run()
