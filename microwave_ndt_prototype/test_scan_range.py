import numpy as np
from antenna_simulator import MicrowaveAntennaSystem
from signal_simulator import CompositeMaterial, simulate_b_scan
from prediction import MicrowaveNDTPredictor

def run(start_x, end_x, n_pts, freq=15.5, standoff=11.0):
    antenna = MicrowaveAntennaSystem(
        frequency_ghz=freq,
        standoff_distance_mm=standoff,
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
        scan_start_x_mm=start_x,
        scan_end_x_mm=end_x,
        n_scan_positions=n_pts,
        rng=np.random.default_rng(42),
    )

    predictor = MicrowaveNDTPredictor()
    res = predictor.predict_from_bscan(
        scan_positions=scan_pos,
        time_axis=time_ax,
        b_scan=b_scan,
        material_thickness_mm=15.0,
        material_eps_r=4.2,
        tau_front_ns=meta["tau_front_ns"],
        tau_back_ns=meta["tau_back_ns"],
    )
    print(f"Scan [{start_x:.0f} - {end_x:.0f} mm, {n_pts} pts, f={freq} GHz, standoff={standoff} mm]:")
    print(f"  Pred: {res['predicted_class']} ({res['confidence']*100:.1f}%) | "
          f"No defect: {res['probabilities']['No defect']*100:.1f}%, "
          f"Crack: {res['probabilities']['Internal crack']*100:.1f}%, "
          f"Void: {res['probabilities']['Air void']*100:.1f}%")
    print(f"  backwall_drop: {res['features']['backwall_drop_ratio']:.3f} | spatial_fwhm: {res['features']['spatial_fwhm_mm']:.1f} mm | energy: {res['features']['defect_window_energy']:.5f}")

# 1. User's exact case (0 to 70 mm, 60 pts)
run(0.0, 70.0, 60, freq=15.5, standoff=11.0)

# 2. Standard full scan (10 to 90 mm, 50 pts)
run(10.0, 90.0, 50, freq=15.5, standoff=11.0)

# 3. Standard frequency 10 GHz (0 to 70 mm)
run(0.0, 70.0, 60, freq=10.0, standoff=20.0)

# 4. Standard frequency 10 GHz (10 to 90 mm)
run(10.0, 90.0, 50, freq=10.0, standoff=20.0)
