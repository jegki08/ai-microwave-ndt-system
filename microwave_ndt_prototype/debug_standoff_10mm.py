import numpy as np
from antenna_simulator import MicrowaveAntennaSystem
from signal_simulator import CompositeMaterial, simulate_b_scan, extract_features_from_bscan
from prediction import MicrowaveNDTPredictor

# Test standoff = 10.0 mm
antenna = MicrowaveAntennaSystem(
    frequency_ghz=10.0,
    standoff_distance_mm=10.0, # CLOSE STANDOFF
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
    defect_z_mm=5.0,
    defect_width_mm=5.0,
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

print(f"Standoff 10mm -> Prediction: {res['predicted_class']} (Confidence: {res['confidence']*100:.1f}%)")
print("Probabilities:")
for c, p in res["probabilities"].items():
    print(f"  {c}: {p*100:.1f}%")

print(f"\ntau_front_ns: {meta['tau_front_ns']:.4f} ns")
print(f"tau_back_ns:  {meta['tau_back_ns']:.4f} ns")
print("Features:")
for k, v in res["features"].items():
    print(f"  {k:25s}: {v}")
