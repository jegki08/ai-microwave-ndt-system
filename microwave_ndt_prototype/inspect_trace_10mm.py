import numpy as np
import matplotlib.pyplot as plt
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
bg_ascan = np.median(b_scan, axis=0)
diff_scan = b_scan - bg_ascan

front_idx = int(np.argmin(np.abs(time_ax - meta["tau_front_ns"])))
back_idx = int(np.argmin(np.abs(time_ax - meta["tau_back_ns"])))

center_idx = 25 # x = 50 mm
trace = np.abs(diff_scan[center_idx, :])

tau_front = meta["tau_front_ns"]
tau_defect_expected = tau_front + 2.0 * 5.0 / (300.0 / np.sqrt(4.2))

print(f"tau_front:           {tau_front:.4f} ns (idx {front_idx})")
print(f"tau_defect_expected: {tau_defect_expected:.4f} ns (idx {int(np.argmin(np.abs(time_ax - tau_defect_expected)))})")
print(f"tau_back:            {meta['tau_back_ns']:.4f} ns (idx {back_idx})")

# Look at peaks in trace between front_idx and back_idx
window = trace[front_idx:back_idx]
print(f"\nTrace values around front wall (front_idx to front_idx + 25):")
for i in range(front_idx, front_idx + 25):
    t = time_ax[i]
    val = trace[i]
    is_exp = abs(t - tau_defect_expected) < 0.005
    mark = " <-- EXPECTED DEFECT PEAK" if is_exp else ""
    print(f"  idx {i:2d} (t={t:.4f} ns): amp = {val:.4f}{mark}")
