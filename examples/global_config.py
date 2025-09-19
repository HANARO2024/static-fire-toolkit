# global_config.py
# ------------------ Required ------------------
# ------------ Load Cell Parameters ------------
# gain = gain_offset + (gain_internal_resistance_kohm * 1000)[Ω] / gain_resistance[Ω]
# bridge_output_mv [mV] = sensitivity_mv_per_v[mV/V] * excitation_voltage[V] * thrust[N] / (rated_capacity_kgf[kgf] * g[N/kgf])
# measured_output_v = (bridge_output_mv / 1000)[V] * gain
# thrust[N] = (bridge_output_mv / sensitivity_mv_per_v)[V] / excitation_voltage[V] * (rated_capacity_kgf * g)[N]
#           = (measured_output_v * 1000 / gain)[mV] / sensitivity_mv_per_v[mV/V] / excitation_voltage[V]
#              * (rated_capacity_kgf * g)[N]
rated_capacity_kgf = 500  # 정격하중: rated capacity of load cell, kgf
sensitivity_mv_per_v = 3  # 감도: sensitivity of load cell, mV/V
gain_internal_resistance_kohm = (
    49.4  # amplifier-specific internal resistor of load cell, kΩ
)
gain_offset = 1  # gain offset of load cell, V

# ------------------ Optional ------------------
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
frequency = 100  # Sampling rate, Hz
cutoff_frequency = 30  # LPF, Hz
gaussian_strong_sigma = 10  # sigma for strong gaussian filter
start_criteria = 0.2  # Criteria for the starting point of a meaningful interval in thrust data processing
end_criteria = 0.1  # Criteria for the ending point of a meaningful interval in thrust data processing
lowpass_order = 5  # order for lowpass filter
gaussian_weak_sigma = 1.5  # sigma for weak gaussian filter
