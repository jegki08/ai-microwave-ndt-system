import numpy as np
from scipy.signal import hilbert
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

for z_target in [2.0, 3.0, 5.0, 8.0, 12.0, 13.5]:
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

    dt = time_ax[1] - time_ax[0]
    bg = np.median(b_scan, axis=0)
    diff = b_scan - bg

    f_idx = int(np.argmin(np.abs(time_ax - meta["tau_front_ns"])))
    b_idx = int(np.argmin(np.abs(time_ax - meta["tau_back_ns"])))

    g_pts = max(3, int(0.030 / dt))
    ws = min(len(time_ax) - 3, f_idx + g_pts)
    we = max(ws + 2, b_idx - max(3, int(0.015 / dt)))

    diff_win = diff[:, ws:we]
    # Smooth along time with a small Gaussian window of pulse_sigma width to smooth out carrier cycles
    kernel_t = np.exp(-np.linspace(-2, 2, 9)**2 / 2.0)
    kernel_t /= np.sum(kernel_t)
    
    # 2D smoothed envelope
    diff_abs = np.abs(diff_win)
    diff_smooth = np.apply_along_axis(lambda m: np.convolve(m, kernel_t, mode='same'), axis=1, arr=diff_abs)

    sp = np.convolve(np.max(diff_smooth, axis=1), [0.2, 0.6, 0.2], mode="same")
    pk_x = np.argmax(sp)

    trace = diff_smooth[pk_x, :]
    pk_t = np.argmax(trace)
    t_peak = time_ax[ws + pk_t]

    t_front = time_ax[f_idx]
    delta_t = max(0.0, t_peak - t_front)
    z_est = 0.5 * delta_t * (300.0 / np.sqrt(4.2))

    print(f"Target z={z_target:4.1f} mm -> Smoothed Env Est z={z_est:4.1f} mm (Err: {abs(z_est - z_target):4.2f} mm)")
