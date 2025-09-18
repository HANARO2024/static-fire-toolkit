# ----------- Thrust Data Processing -----------
thrust_sep = "[,\t]"  # separator for thrust data, character or Regex
thrust_header = None  # header for thrust data (row number or None)
thrust_time_col_idx = 0  # index of time column
thrust_col_idx = 1  # index of thrust column
# ---------- Pressure Data Processing ----------
pressure_sep = ";"  # separator for pressure data, character or Regex
pressure_header = 0  # header for pressure data (row number or None)
pressure_time_col_idx = 0  # index of datetime column
pressure_col_idx = 2  # index of pressure column
# ------------ Global Configuration ------------
g = 9.80665  # gravitational acceleration, m/s^2
rated_load = 500  # rated load of load cell, kgf
rated_output = 3  # rated output of load cell, V
frequency = 100  # Sampling rate, Hz
cutoff_frequency = 30  # LPF, Hz
gaussian_strong_sigma = 10  # sigma for strong gaussian filter
start_criteria = 0.2  # Criteria for the starting point of a meaningful interval in thrust data processing
end_criteria = 0.1  # Criteria for the ending point of a meaningful interval in thrust data processing
lowpass_order = 5  # order for lowpass filter
gaussian_weak_sigma = 1.5  # sigma for weak gaussian filter
