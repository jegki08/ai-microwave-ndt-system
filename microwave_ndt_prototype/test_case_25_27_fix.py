import numpy as np
from antenna_simulator import MicrowaveAntennaSystem
from signal_simulator import CompositeMaterial, simulate_b_scan
from prediction import MicrowaveNDTPredictor

def test_case_25_and_27(guard_front_ns=0.030):
    dt = 0.00401

    # Case 25: Standoff 10mm
    ant25 = MicrowaveAntennaSystem(frequency_ghz=10.0, standoff_distance_mm=10.0, antenna_separation_mm=13.0, noise_level=0.030)
    mat = CompositeMaterial(name="GFRP", thickness_mm=15.0, relative_permittivity=4.2, loss_tangent=0.020)
    s_pos, t_ax, b25, m25 = simulate_b_scan(ant25, mat, "Internal crack", 50.0, 5.0, 5.0, 10.0, 90.0, 50, rng=np.random.default_rng(42))

    # Case 27: High noise 0.060
    ant27 = MicrowaveAntennaSystem(frequency_ghz=10.0, standoff_distance_mm=20.0, antenna_separation_mm=13.0, noise_level=0.060)
    _, _, b27, m27 = simulate_b_scan(ant27, mat, "Internal crack", 50.0, 5.0, 5.0, 10.0, 90.0, 50, rng=np.random.default_rng(42))

    predictor = MicrowaveNDTPredictor()

    for name, b_scan, meta in [("Case 25 (Standoff 10mm)", b25, m25), ("Case 27 (High Noise 0.060)", b27, m27)]:
        n_scans, n_times = b_scan.shape
        dt_act = t_ax[1] - t_ax[0]
        v_mat = 300.0 / np.sqrt(4.2)
        bg = np.median(b_scan, axis=0)
        diff = b_scan - bg

        f_idx = int(np.argmin(np.abs(t_ax - meta["tau_front_ns"])))
        b_idx = int(np.argmin(np.abs(t_ax - meta["tau_back_ns"])))

        g_pts = max(3, int(guard_front_ns / dt_act))
        ws = min(n_times - 3, f_idx + g_pts)
        we = max(ws + 2, b_idx - max(3, int(0.015 / dt_act)))

        win = diff[:, ws:we]
        win_abs = np.abs(win)

        max_amp = float(np.max(win_abs))
        energy = float(np.sum(win**2) / (win.size + 1e-6))
        front_amp = float(np.max(np.abs(b_scan[:, max(0, f_idx - 10) : f_idx + 10])))
        defect_to_front = float(max_amp / (front_amp + 1e-6))

        back_prof = np.max(np.abs(b_scan[:, max(0, b_idx - 10) : min(n_times, b_idx + 10)]), axis=1)
        base_bw = float(np.percentile(back_prof, 80))
        min_bw = float(np.min(back_prof))
        bw_drop = float(np.clip(1.0 - (min_bw / (base_bw + 1e-6)), 0.0, 1.0))

        bw_def = np.maximum(0.0, base_bw - back_prof)
        sh_idx = int(np.argmax(bw_def))
        sh_pk_x = float(s_pos[sh_idx])

        sp_raw = np.max(win_abs, axis=1)
        sp_smooth = np.convolve(sp_raw, [0.2, 0.6, 0.2], mode="same")
        pk_x_idx = int(np.argmax(sp_smooth))
        pk_lat_x = float(s_pos[pk_x_idx])

        ascan_raw = win_abs[pk_x_idx, :]
        k_time = np.array([0.05, 0.15, 0.60, 0.15, 0.05])
        ascan_trace = np.convolve(ascan_raw, k_time, mode="same")
        pk_t_idx = int(np.argmax(ascan_trace))
        pk_time = float(t_ax[ws + pk_t_idx])

        t_front = float(t_ax[f_idx])
        delta_t = max(0.0, pk_time - t_front)
        inf_depth = float(np.clip(0.5 * delta_t * v_mat, 0.0, 15.0))

        pk_v = sp_smooth[pk_x_idx]
        n_fl = float(np.percentile(sp_smooth, 30))
        h_v = n_fl + 0.5 * max(1e-4, pk_v - n_fl)
        l_i = pk_x_idx
        while l_i > 0 and sp_smooth[l_i] >= h_v:
            l_i -= 1
        r_i = pk_x_idx
        while r_i < len(sp_smooth) - 1 and sp_smooth[r_i] >= h_v:
            r_i += 1
        fwhm = float(s_pos[r_i] - s_pos[l_i])

        std_w = float(np.std(win))
        d_flat = win.flatten() - np.mean(win)
        m2 = np.mean(d_flat**2) + 1e-9
        m3 = np.mean(d_flat**3)
        m4 = np.mean(d_flat**4)
        skew = float(m3 / (m2**1.5))
        kurt = float(m4 / (m2**2.0) - 3.0)

        pk_ascan = diff[pk_x_idx, :]
        fft_m = np.abs(np.fft.rfft(pk_ascan))
        frqs = np.fft.rfftfreq(len(pk_ascan), d=dt_act)
        spec_cent = float(np.sum(frqs * fft_m) / (np.sum(fft_m) + 1e-6))

        sp_grad = float(np.max(np.abs(np.diff(sp_smooth))))
        tot_e = float(np.sum(diff**2) + 1e-6)
        area_rat = float(np.sum(win**2) / tot_e)

        g_max = ascan_trace[pk_t_idx] + 1e-6
        g_h = 0.5 * g_max
        tl = pk_t_idx
        while tl > 0 and ascan_trace[tl] >= g_h:
            tl -= 1
        tr = pk_t_idx
        while tr < len(ascan_trace) - 1 and ascan_trace[tr] >= g_h:
            tr += 1
        p_spread = float((tr - tl) * dt_act)

        tr_slice = ascan_trace[pk_t_idx + max(2, int(0.020 / dt_act)) :]
        tr_rat = float(np.max(tr_slice) / g_max) if len(tr_slice) > 3 else 0.0

        sh_h = bw_def[sh_idx] / 2.0
        sl = sh_idx
        while sl > 0 and bw_def[sl] >= sh_h:
            sl -= 1
        sr = sh_idx
        while sr < len(bw_def) - 1 and bw_def[sr] >= sh_h:
            sr += 1
        sh_ext = float(s_pos[sr] - s_pos[sl])

        feats = np.array([
            max_amp, energy, defect_to_front, bw_drop, pk_lat_x, pk_time, inf_depth, fwhm,
            std_w, skew, kurt, spec_cent, sp_grad, area_rat, p_spread, tr_rat, sh_ext, sh_pk_x
        ])

        res = predictor.predict_from_features(feats)
        print(f"{name}: Pred={res['predicted_class']} ({res['confidence']*100:.1f}%) | inf_depth={inf_depth:.2f} mm | fwhm={fwhm:.2f} mm | tr_rat={tr_rat:.3f}")

test_case_25_and_27(0.030)
