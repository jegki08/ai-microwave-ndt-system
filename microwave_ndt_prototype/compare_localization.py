import numpy as np
from antenna_simulator import MicrowaveAntennaSystem
from signal_simulator import CompositeMaterial, simulate_b_scan
from prediction import MicrowaveNDTPredictor

predictor = MicrowaveNDTPredictor()
errs_reg_x = []
errs_phy_x = []
errs_reg_z = []
errs_phy_z = []

rng = np.random.default_rng(42)

for i in range(20):
    x_true = float(rng.uniform(15.0, 75.0))
    z_true = float(rng.uniform(2.5, 12.0))
    w_true = float(rng.uniform(3.0, 8.0))
    d_type = rng.choice(["Internal crack", "Air void"])
    scan_s = float(rng.choice([0.0, 10.0]))
    scan_e = float(rng.choice([70.0, 90.0, 100.0]))
    if x_true < scan_s + 5.0 or x_true > scan_e - 5.0:
        continue

    antenna = MicrowaveAntennaSystem(
        frequency_ghz=10.0,
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
        defect_type=d_type,
        defect_x_mm=x_true,
        defect_z_mm=z_true,
        defect_width_mm=w_true,
        scan_start_x_mm=scan_s,
        scan_end_x_mm=scan_e,
        n_scan_positions=40,
        rng=rng,
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

    x_reg = res["estimated_pos_x_mm"]
    z_reg = res["estimated_depth_z_mm"]
    x_phy = res["features"]["peak_lateral_x"]
    z_phy = res["features"]["inferred_depth_mm"]

    errs_reg_x.append(abs(x_reg - x_true))
    errs_phy_x.append(abs(x_phy - x_true))
    errs_reg_z.append(abs(z_reg - z_true))
    errs_phy_z.append(abs(z_phy - z_true))

print("Localization Comparison across 20 diverse cases:")
print(f"Position X Error -> Regressor MAE: {np.mean(errs_reg_x):.2f} mm | Physics Feature MAE: {np.mean(errs_phy_x):.2f} mm")
print(f"Depth Z Error    -> Regressor MAE: {np.mean(errs_reg_z):.2f} mm | Physics Feature MAE: {np.mean(errs_phy_z):.2f} mm")
