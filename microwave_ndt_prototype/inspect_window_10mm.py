import numpy as np
from antenna_simulator import MicrowaveAntennaSystem
from signal_simulator import CompositeMaterial, simulate_b_scan

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
n_scans, n_times = b_scan.shape
bg_ascan = np.median(b_scan, axis=0)
diff_scan = b_scan - bg_ascan

front_idx = int(np.argmin(np.abs(time_ax - meta["tau_front_ns"])))
back_idx = int(np.argmin(np.abs(time_ax - meta["tau_back_ns"])))

guard_front_pts = max(3, int(0.025 / dt))
guard_back_pts = max(3, int(0.015 / dt))
w_start = min(n_times - 3, front_idx + guard_front_pts)
w_end = max(w_start + 2, back_idx - guard_back_pts)

print(f"dt = {dt:.5f} ns")
print(f"front_idx: {front_idx} (t={time_ax[front_idx]:.4f} ns)")
print(f"guard_front_pts: {guard_front_pts} ({guard_front_pts * dt:.4f} ns)")
print(f"w_start: {w_start} (t={time_ax[w_start]:.4f} ns)")
print(f"back_idx: {back_idx} (t={time_ax[back_idx]:.4f} ns)")
print(f"w_end: {w_end} (t={time_ax[w_end]:.4f} ns)")

defect_diff_window = diff_scan[:, w_start:w_end]
defect_diff_abs = np.abs(defect_diff_window)
spatial_prof_raw = np.max(defect_diff_abs, axis=1)
kernel = np.array([0.2, 0.6, 0.2])
spatial_prof_smooth = np.convolve(spatial_prof_raw, kernel, mode="same")
scan_idx_peak = int(np.argmax(spatial_prof_smooth))

ascan_peak_trace = defect_diff_abs[scan_idx_peak, :]
time_idx_peak = int(np.argmax(ascan_peak_trace))
peak_time_ns = float(time_ax[w_start + time_idx_peak])
print(f"scan_idx_peak: {scan_idx_peak} (x={scan_pos[scan_idx_peak]:.2f} mm)")
print(f"time_idx_peak: {time_idx_peak} -> peak_time_ns = {peak_time_ns:.4f} ns")
print(f"A-scan window peak value = {ascan_peak_trace[time_idx_peak]:.4f}")

# What is happening in ascan_peak_trace?
print("\nA-scan peak trace points:")
for i in range(len(ascan_peak_trace)):
    t = time_ax[w_start + i]
    val = ascan_peak_trace[i]
    print(f"  i={i:2d} (t={t:.4f} ns, z={(t - time_ax[front_idx])*0.5*300/np.sqrt(4.2):.2f} mm): val={val:.4f}")
