import numpy as np
from antenna_simulator import MicrowaveAntennaSystem
from signal_simulator import CompositeMaterial, simulate_b_scan, extract_features_from_bscan

def test_depths(guard_ns):
    print(f"\n--- Testing depths with guard_front = {guard_ns:.3f} ns ---")
    dt = 0.00401 # approx
    for z_target in [2.0, 3.0, 5.0, 8.0, 12.0, 13.5]:
        antenna = MicrowaveAntennaSystem(
            frequency_ghz=10.0,
            standoff_distance_mm=10.0, # challenging close standoff
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
            defect_z_mm=z_target,
            defect_width_mm=5.0,
            scan_start_x_mm=10.0,
            scan_end_x_mm=90.0,
            n_scan_positions=50,
            rng=np.random.default_rng(42),
        )

        dt_actual = time_ax[1] - time_ax[0]
        bg = np.median(b_scan, axis=0)
        diff = b_scan - bg

        f_idx = int(np.argmin(np.abs(time_ax - meta["tau_front_ns"])))
        b_idx = int(np.argmin(np.abs(time_ax - meta["tau_back_ns"])))

        g_pts = max(3, int(guard_ns / dt_actual))
        ws = min(len(time_ax) - 3, f_idx + g_pts)
        we = max(ws + 2, b_idx - max(3, int(0.015 / dt_actual)))

        win = np.abs(diff[:, ws:we])
        sp = np.convolve(np.max(win, axis=1), [0.2, 0.6, 0.2], mode="same")
        pk_x = np.argmax(sp)

        trace = win[pk_x, :]
        pk_t = np.argmax(trace)
        t_peak = time_ax[ws + pk_t]

        t_front = time_ax[f_idx]
        delta_t = max(0.0, t_peak - t_front)
        z_est = 0.5 * delta_t * (300.0 / np.sqrt(4.2))

        print(f"Target z={z_target:4.1f} mm -> Est z={z_est:4.1f} mm (Err: {abs(z_est - z_target):4.2f} mm) | peak_val={trace[pk_t]:.4f}")

test_depths(0.025)
test_depths(0.032)
