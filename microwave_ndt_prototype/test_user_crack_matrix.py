import numpy as np
from antenna_simulator import MicrowaveAntennaSystem
from signal_simulator import CompositeMaterial, simulate_b_scan
from prediction import MicrowaveNDTPredictor

predictor = MicrowaveNDTPredictor()

print("Testing user crack case (x=18, z=3, w=4, scan=0-70, 30 steps) across different noise seeds & frequencies:")
for seed in [1, 7, 42, 99, 123]:
    for freq in [8.0, 10.0, 12.0, 15.5]:
        antenna = MicrowaveAntennaSystem(
            frequency_ghz=freq,
            standoff_distance_mm=20.0,
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
            defect_x_mm=18.0,
            defect_z_mm=3.0,
            defect_width_mm=4.0,
            scan_start_x_mm=0.0,
            scan_end_x_mm=70.0,
            n_scan_positions=30,
            rng=np.random.default_rng(seed),
        )
        res = predictor.predict_from_bscan(
            scan_positions=scan_pos,
            time_axis=time_ax,
            b_scan=b_scan,
            material_thickness_mm=15.0,
            material_eps_r=4.2,
            tau_front_ns=meta["tau_front_ns"],
            tau_back_ns=meta["tau_back_ns"],
        )
        pred = res["predicted_class"]
        conf = res["confidence"] * 100
        p_no = res["probabilities"]["No defect"] * 100
        p_crk = res["probabilities"]["Internal crack"] * 100
        p_void = res["probabilities"]["Air void"] * 100
        print(f"seed={seed:3d} | f={freq:4.1f} GHz -> Pred: {pred:15s} (Conf: {conf:4.1f}%) | NoDef: {p_no:4.1f}% | Crk: {p_crk:4.1f}% | Void: {p_void:4.1f}% | EstX: {res['estimated_pos_x_mm']:4.1f} | EstZ: {res['estimated_depth_z_mm']:4.1f}")
