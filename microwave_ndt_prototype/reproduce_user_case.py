import numpy as np
from antenna_simulator import MicrowaveAntennaSystem
from signal_simulator import CompositeMaterial, simulate_b_scan, extract_features_from_bscan
from prediction import MicrowaveNDTPredictor

# User's case:
# Ground truth: Internal crack
# Defect position X: 18 mm
# Defect depth Z: 3 mm
# Crack width: 4 mm
# Scan start X: 0 mm
# Scan end X: 70 mm
# Scan positions: 30

antenna = MicrowaveAntennaSystem(
    frequency_ghz=10.0,
    standoff_distance_mm=20.0,
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
    defect_x_mm=18.0,
    defect_z_mm=3.0,
    defect_width_mm=4.0,
    scan_start_x_mm=0.0,
    scan_end_x_mm=70.0,
    n_scan_positions=30,
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
print("Probabilities:")
for c, p in res["probabilities"].items():
    print(f"  {c}: {p*100:.1f}%")

print(f"Est Pos X: {res['estimated_pos_x_mm']} (Target: 18.0 mm)")
print(f"Est Depth Z: {res['estimated_depth_z_mm']} (Target: 3.0 mm)")
print("\nExtracted features:")
for k, v in res["features"].items():
    print(f"  {k:25s}: {v}")
