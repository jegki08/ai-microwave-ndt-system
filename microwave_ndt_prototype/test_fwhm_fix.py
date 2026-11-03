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

# Method A: Current faulty threshold (relative to zero)
half_val_faulty = pk_val / 2.0
l_a = pk_idx
while l_a > 0 and spatial_prof_smooth[l_a] >= half_val_faulty:
    l_a -= 1
r_a = pk_idx
while r_a < len(spatial_prof_smooth) - 1 and spatial_prof_smooth[r_a] >= half_val_faulty:
    r_a += 1
fwhm_a = scan_pos[r_a] - scan_pos[l_a]

# Method B: Proper baseline-subtracted FWHM
noise_floor = float(np.percentile(spatial_prof_smooth, 30))
half_val_correct = noise_floor + 0.5 * max(1e-4, pk_val - noise_floor)
l_b = pk_idx
while l_b > 0 and spatial_prof_smooth[l_b] >= half_val_correct:
    l_b -= 1
r_b = pk_idx
while r_b < len(spatial_prof_smooth) - 1 and spatial_prof_smooth[r_b] >= half_val_correct:
    r_b += 1
fwhm_b = scan_pos[r_b] - scan_pos[l_b]

print(f"Peak: {pk_val:.4f} at x={scan_pos[pk_idx]:.1f} mm")
print(f"Noise floor (30th pct): {noise_floor:.4f}")
print(f"Method A (Current threshold {half_val_faulty:.4f}): FWHM = {fwhm_a:.2f} mm")
print(f"Method B (Baseline-subtracted threshold {half_val_correct:.4f}): FWHM = {fwhm_b:.2f} mm")
