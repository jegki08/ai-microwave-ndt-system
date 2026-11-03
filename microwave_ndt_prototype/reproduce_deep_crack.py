import numpy as np
from antenna_simulator import MicrowaveAntennaSystem
from signal_simulator import CompositeMaterial, simulate_b_scan
from prediction import MicrowaveNDTPredictor

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

# User's case 2 from image: x = 85.0 mm, z = 13.5 mm
scan_pos, time_ax, b_scan, meta = simulate_b_scan(
    antenna=antenna,
    material=material,
    defect_type="Internal crack",
    defect_x_mm=85.0,
    defect_z_mm=13.5,
    defect_width_mm=4.0,
    scan_start_x_mm=10.0,
    scan_end_x_mm=90.0,
    n_scan_positions=50,
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

print(f"Prediction: {res['predicted_class']} (Confidence: {res['confidence']*100:.1f}%)")
for c, p in res["probabilities"].items():
    print(f"  {c}: {p*100:.1f}%")
print(f"Est Pos X: {res['estimated_pos_x_mm']} (Target: 85.0 mm)")
print(f"Est Depth Z: {res['estimated_depth_z_mm']} (Target: 13.5 mm)")
print(f"Inferred depth feature: {res['features']['inferred_depth_mm']} mm")
print(f"Peak time ns: {res['features']['peak_time_ns']} ns")
print(f"tau_front_ns: {meta['tau_front_ns']} ns")
print(f"tau_back_ns: {meta['tau_back_ns']} ns")
print(f"defect_window_max_amp: {res['features']['defect_window_max_amp']}")
print(f"defect_to_front_ratio: {res['features']['defect_to_front_ratio']}")
print(f"backwall_drop_ratio: {res['features']['backwall_drop_ratio']}")
