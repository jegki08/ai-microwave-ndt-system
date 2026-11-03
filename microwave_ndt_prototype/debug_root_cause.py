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

scan_pos, time_ax, b_scan_matrix, scan_meta = simulate_b_scan(
    antenna=antenna,
    material=material,
    defect_type="Internal crack",
    defect_x_mm=38.0,
    defect_z_mm=5.0,
    defect_width_mm=4.0,
    scan_start_x_mm=0.0,
    scan_end_x_mm=70.0,
    n_scan_positions=60,
    rng=np.random.default_rng(42),
)

predictor = MicrowaveNDTPredictor()
ai_results = predictor.predict_from_bscan(
    scan_positions=scan_pos,
    time_axis=time_ax,
    b_scan=b_scan_matrix,
    material_thickness_mm=15.0,
    material_eps_r=4.2,
    tau_front_ns=scan_meta["tau_front_ns"],
    tau_back_ns=scan_meta["tau_back_ns"],
)

print(f"Prediction: {ai_results['predicted_class']}")
print(f"Confidence: {ai_results['confidence']*100:.1f}%")
print("Probabilities:")
for c, p in ai_results['probabilities'].items():
    print(f"  {c}: {p*100:.1f}%")
print("\nExtracted features:")
for k, v in ai_results['features'].items():
    print(f"  {k}: {v}")
