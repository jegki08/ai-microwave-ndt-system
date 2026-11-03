import numpy as np
from antenna_simulator import MicrowaveAntennaSystem
from signal_simulator import CompositeMaterial, simulate_b_scan

antenna = MicrowaveAntennaSystem(
    frequency_ghz=15.5,
    standoff_distance_mm=11.0,
    antenna_separation_mm=13.0,
    directivity_n=4.0,
    signal_amplitude=1.0,
    noise_level=0.030,
)

material = CompositeMaterial(
    name="GFRP",
    thickness_mm=15.0,
    relative_permittivity=4.2,
    loss_tangent=0.020,
)

scan_pos, time_ax, b_scan, meta = simulate_b_scan(
    antenna=antenna,
    material=material,
    defect_type="Internal crack",
    defect_x_mm=38.0,
    defect_z_mm=5.0,
    defect_width_mm=4.0,
    scan_start_x_mm=0.0,
    scan_end_x_mm=70.0,
    n_scan_positions=60,
    rng=np.random.default_rng(42),
)

dt = time_ax[1] - time_ax[0]
bg_ascan = np.median(b_scan, axis=0)
diff_scan = b_scan - bg_ascan
front_idx = int(np.argmin(np.abs(time_ax - meta["tau_front_ns"])))
back_idx = int(np.argmin(np.abs(time_ax - meta["tau_back_ns"])))

guard_front_pts = max(3, int(0.025 / dt))
guard_back_pts = max(3, int(0.015 / dt))
w_start = min(len(time_ax) - 3, front_idx + guard_front_pts)
w_end = max(w_start + 2, back_idx - guard_back_pts)

defect_diff_window = diff_scan[:, w_start:w_end]
defect_diff_abs = np.abs(defect_diff_window)
spatial_prof_raw = np.max(defect_diff_abs, axis=1)

print("Scan positions (x) and spatial profile amplitude:")
for pos, val in zip(scan_pos[::4], spatial_prof_raw[::4]):
    bar = "#" * int(val * 150)
    print(f"  x={pos:5.1f} mm | amp={val:6.4f} | {bar}")

pk_idx = np.argmax(spatial_prof_raw)
print(f"\nPeak at x={scan_pos[pk_idx]:.1f} mm with amp={spatial_prof_raw[pk_idx]:.4f}")
half_val = spatial_prof_raw[pk_idx] / 2.0
print(f"Half value = {half_val:.4f}")
l_idx = pk_idx
while l_idx > 0 and spatial_prof_raw[l_idx] >= half_val:
    l_idx -= 1
r_idx = pk_idx
while r_idx < len(spatial_prof_raw) - 1 and spatial_prof_raw[r_idx] >= half_val:
    r_idx += 1
print(f"l_idx={l_idx} (x={scan_pos[l_idx]:.1f}), r_idx={r_idx} (x={scan_pos[r_idx]:.1f})")
print(f"FWHM = {scan_pos[r_idx] - scan_pos[l_idx]:.1f} mm")
