import numpy as np
from antenna_simulator import MicrowaveAntennaSystem
from signal_simulator import CompositeMaterial, simulate_b_scan
from prediction import MicrowaveNDTPredictor

antenna = MicrowaveAntennaSystem(
    frequency_ghz=10.0,
    standoff_distance_mm=10.0,
    antenna_separation_mm=13.0,
    directivity_n=4.0,
    signal_amplitude=1.0,
    noise_level=0.030,
)
material = CompositeMaterial(name="GFRP", thickness_mm=15.0, relative_permittivity=4.2, loss_tangent=0.020)

scan_pos, time_ax, b_scan, meta = simulate_b_scan(
    antenna=antenna,
    material=material,
    defect_type="Internal crack",
    defect_x_mm=50.0,
    defect_z_mm=5.0,
    defect_width_mm=5.0,
    scan_start_x_mm=10.0,
    scan_end_x_mm=90.0,
    n_scan_positions=50,
    rng=np.random.default_rng(42),
)

dt = time_ax[1] - time_ax[0]
bg_ascan = np.median(b_scan, axis=0)
diff_scan = b_scan - bg_ascan

front_idx = int(np.argmin(np.abs(time_ax - meta["tau_front_ns"])))
back_idx = int(np.argmin(np.abs(time_ax - meta["tau_back_ns"])))

for guard_ns in [0.025, 0.035, 0.040, 0.045]:
    guard_front_pts = max(3, int(guard_ns / dt))
    w_start = front_idx + guard_front_pts
    w_end = back_idx - max(3, int(0.015 / dt))
    
    defect_diff_window = diff_scan[:, w_start:w_end]
    defect_diff_abs = np.abs(defect_diff_window)
    spatial_prof_raw = np.max(defect_diff_abs, axis=1)
    kernel = np.array([0.2, 0.6, 0.2])
    spatial_prof_smooth = np.convolve(spatial_prof_raw, kernel, mode="same")
    scan_idx_peak = int(np.argmax(spatial_prof_smooth))

    ascan_peak_trace = defect_diff_abs[scan_idx_peak, :]
    time_idx_peak = int(np.argmax(ascan_peak_trace))
    peak_time_ns = float(time_ax[w_start + time_idx_peak])
    delta_t = max(0.0, peak_time_ns - time_ax[front_idx])
    inf_depth = 0.5 * delta_t * (300.0 / np.sqrt(4.2))

    print(f"guard={guard_ns:.3f} ns: peak_time={peak_time_ns:.4f} ns | inf_depth={inf_depth:.2f} mm | peak_val={ascan_peak_trace[time_idx_peak]:.4f}")
