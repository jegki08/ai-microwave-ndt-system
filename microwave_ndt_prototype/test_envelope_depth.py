import numpy as np
from scipy.signal import hilbert
from antenna_simulator import MicrowaveAntennaSystem
from signal_simulator import CompositeMaterial, simulate_b_scan

antenna = MicrowaveAntennaSystem(
    frequency_ghz=10.0,
    standoff_distance_mm=10.0, # close standoff 10mm
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
    defect_z_mm=5.0, # True depth = 5.0 mm
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

guard_front_pts = max(4, int(0.035 / dt)) # 0.035 ns guard to clear front-wall main lobe
guard_back_pts = max(3, int(0.015 / dt))
w_start = min(len(time_ax) - 3, front_idx + guard_front_pts)
w_end = max(w_start + 2, back_idx - guard_back_pts)

defect_diff_window = diff_scan[:, w_start:w_end]

# Compute envelope using Hilbert transform on each A-scan
analytic_diff = np.abs(hilbert(defect_diff_window, axis=1))

# Spatial peak
spatial_prof = np.max(analytic_diff, axis=1)
scan_idx_peak = np.argmax(spatial_prof)

ascan_env = analytic_diff[scan_idx_peak, :]
time_idx_peak = np.argmax(ascan_env)
peak_time_ns = time_ax[w_start + time_idx_peak]

tau_front_time = time_ax[front_idx]
delta_t = max(0.0, peak_time_ns - tau_front_time)
v_mat = 300.0 / np.sqrt(4.2)
inferred_depth = 0.5 * delta_t * v_mat

print(f"Target Depth: 5.00 mm")
print(f"tau_front:    {tau_front_time:.4f} ns")
print(f"peak_time:    {peak_time_ns:.4f} ns")
print(f"delta_t:      {delta_t:.4f} ns")
print(f"Inferred Depth with Analytic Envelope: {inferred_depth:.2f} mm (Error: {abs(inferred_depth - 5.0):.2f} mm)")
