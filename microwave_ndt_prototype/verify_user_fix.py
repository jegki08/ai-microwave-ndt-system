import numpy as np
from antenna_simulator import MicrowaveAntennaSystem
from signal_simulator import CompositeMaterial, simulate_b_scan
from prediction import MicrowaveNDTPredictor

predictor = MicrowaveNDTPredictor()

# Today's scenario from the screenshot:
# f = 20 GHz, standoff = 38 mm, directivity = 8.0, amp = 2.0 V, noise = 0.08, def_x = 15.0, def_z = 2.0
antenna_today = MicrowaveAntennaSystem(
    frequency_ghz=20.0,
    standoff_distance_mm=38.0,
    antenna_separation_mm=13.0,
    directivity_n=8.0,
    signal_amplitude=2.0,
    noise_level=0.08,
)
material = CompositeMaterial(name="GFRP", thickness_mm=15.0, relative_permittivity=4.2, loss_tangent=0.020)

print("=" * 70)
print("TODAY'S REPORTED USER CASE: 20 GHz, 38mm Standoff, Amp=2.0V, Noise=0.08")
print("=" * 70)
for condition in ["Internal crack", "Air void", "No defect"]:
    scan_pos, time_ax, b_scan, meta = simulate_b_scan(
        antenna=antenna_today,
        material=material,
        defect_type=condition,
        defect_x_mm=15.0,
        defect_z_mm=2.0,
        defect_width_mm=6.0 if condition == "Internal crack" else 8.0,
        scan_start_x_mm=10.0,
        scan_end_x_mm=90.0,
        n_scan_positions=50,
        rng=np.random.default_rng(42),
    )
    res = predictor.predict_from_bscan(
        scan_pos, time_ax, b_scan, 15.0, 4.2, meta["tau_front_ns"], meta["tau_back_ns"]
    )
    print(f"Ground Truth: {condition:15s} -> Predicted: {res['predicted_class']:15s} (Confidence: {res['confidence']*100:.1f}%)")
    print(f"  Estimated Position x: {res['estimated_pos_x_mm']} mm, Estimated Depth z: {res['estimated_depth_z_mm']} mm")
    print(f"  Class Probabilities: {res['probabilities']}")
    print("-" * 70)
