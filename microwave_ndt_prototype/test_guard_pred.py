import numpy as np
from antenna_simulator import MicrowaveAntennaSystem
from signal_simulator import CompositeMaterial, simulate_b_scan, extract_features_from_bscan
from prediction import MicrowaveNDTPredictor

antenna = MicrowaveAntennaSystem(
    frequency_ghz=10.0,
    standoff_distance_mm=10.0,
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

# Extract with current guard (0.025 ns)
feats_old = extract_features_from_bscan(scan_pos, time_ax, b_scan, 15.0, 4.2, meta["tau_front_ns"], meta["tau_back_ns"])
res_old = predictor.predict_from_features(feats_old)
print(f"Old guard (0.025 ns) -> Pred: {res_old['predicted_class']} ({res_old['confidence']*100:.1f}%)")

# Now let's test if guard is 0.038 ns
# We can simulate this by temporarily modifying the feature vector or function
