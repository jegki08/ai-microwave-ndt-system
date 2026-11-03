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

bg_ascan = np.median(b_scan, axis=0)
diff_scan = b_scan - bg_ascan

front_idx = int(np.argmin(np.abs(time_ax - meta["tau_front_ns"])))
print(f"front_idx={front_idx} (t={time_ax[front_idx]:.4f} ns)")

# Print spatial profile of diff_scan at various time indices from front_idx to front_idx + 25
print("Spatial variation (std across x) for each time index:")
for i in range(front_idx, front_idx + 35):
    t = time_ax[i]
    std_x = np.std(diff_scan[:, i])
    max_x = np.max(np.abs(diff_scan[:, i]))
    pk_x_idx = np.argmax(np.abs(diff_scan[:, i]))
    print(f"  idx {i:2d} (t={t:.4f} ns): std_x={std_x:.4f} | max={max_x:.4f} at x={scan_pos[pk_x_idx]:.1f} mm")
