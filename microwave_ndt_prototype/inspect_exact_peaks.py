import numpy as np
from antenna_simulator import MicrowaveAntennaSystem
from signal_simulator import CompositeMaterial, simulate_single_ascan

antenna = MicrowaveAntennaSystem(
    frequency_ghz=10.0,
    standoff_distance_mm=10.0,
    antenna_separation_mm=13.0,
    directivity_n=4.0,
    signal_amplitude=1.0,
    noise_level=0.001, # zero noise to see exact physics
)
material = CompositeMaterial(name="GFRP", thickness_mm=15.0, relative_permittivity=4.2, loss_tangent=0.020)

time_ns, sig, info = simulate_single_ascan(
    antenna=antenna,
    material=material,
    scan_x_mm=50.0,
    defect_type="Internal crack",
    defect_x_mm=50.0,
    defect_z_mm=5.0,
    defect_width_mm=5.0,
    n_points=600,
    time_window_ns=1.6,
)

print(f"Info from simulation:")
for k, v in info.items():
    print(f"  {k}: {v}")

# Find top 5 peaks in abs(sig)
from scipy.signal import find_peaks
peaks, _ = find_peaks(np.abs(sig), height=0.05, distance=10)
print("\nPeaks found in |signal|:")
for p in peaks:
    t = time_ns[p]
    amp = np.abs(sig[p])
    print(f"  idx {p:3d} (t={t:.4f} ns): amp={amp:.4f}")
