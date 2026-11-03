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

print(f"tau_front = {meta['tau_front_ns']:.4f} ns (front_idx = {front_idx})")
print(f"tau_back = {meta['tau_back_ns']:.4f} ns (back_idx = {back_idx})")
print(f"time resolution dt = {dt:.5f} ns")

# Let's inspect diff_scan at x=0 mm (no defect) vs x=38 mm (defect)
idx_nodefect = 0
idx_defect = np.argmin(np.abs(scan_pos - 38.0))

print("\nAt x = 0.0 mm (healthy region):")
print(f"  diff_scan max in internal window: {np.max(np.abs(diff_scan[idx_nodefect, front_idx+5:back_idx-5])):.4f}")
print(f"  diff_scan std in internal window: {np.std(diff_scan[idx_nodefect, front_idx+5:back_idx-5]):.4f}")

# Where are the large values in diff_scan coming from at x=0?
diff_trace = np.abs(diff_scan[idx_nodefect, :])
top_times = np.argsort(diff_trace)[::-1][:10]
print("Top 10 diff points in time for x=0:")
for t_idx in top_times:
    print(f"  t={time_ax[t_idx]:.4f} ns (idx {t_idx}): diff={diff_trace[t_idx]:.4f} | dist from front={t_idx - front_idx} pts")
