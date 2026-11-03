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
kernel = np.array([0.2, 0.6, 0.2])
spatial_prof_smooth = np.convolve(spatial_prof_raw, kernel, mode="same")

pk_idx = np.argmax(spatial_prof_smooth)
pk_val = spatial_prof_smooth[pk_idx]
half_val = pk_val / 2.0

l_idx = pk_idx
while l_idx > 0 and spatial_prof_smooth[l_idx] >= half_val:
    l_idx -= 1
r_idx = pk_idx
while r_idx < len(spatial_prof_smooth) - 1 and spatial_prof_smooth[r_idx] >= half_val:
    r_idx += 1

print(f"Smooth peak at index {pk_idx} (x={scan_pos[pk_idx]:.2f} mm), val={pk_val:.4f}, half_val={half_val:.4f}")
print(f"l_idx={l_idx} (x={scan_pos[l_idx]:.2f}), val={spatial_prof_smooth[l_idx]:.4f}")
print(f"r_idx={r_idx} (x={scan_pos[r_idx]:.2f}), val={spatial_prof_smooth[r_idx]:.4f}")
print(f"FWHM = {scan_pos[r_idx] - scan_pos[l_idx]:.2f} mm")

print("\nValues near left walk:")
for i in range(max(0, l_idx - 2), min(len(scan_pos), l_idx + 8)):
    print(f"  idx {i:2d} (x={scan_pos[i]:5.2f} mm): smooth={spatial_prof_smooth[i]:.4f} (>= half_val? {spatial_prof_smooth[i] >= half_val})")
