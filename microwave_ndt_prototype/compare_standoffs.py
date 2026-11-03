import numpy as np
from antenna_simulator import MicrowaveAntennaSystem
from signal_simulator import CompositeMaterial, simulate_b_scan, extract_features_from_bscan
from prediction import MicrowaveNDTPredictor

# Standoff 10mm vs Standoff 20mm
ant10 = MicrowaveAntennaSystem(frequency_ghz=10.0, standoff_distance_mm=10.0, antenna_separation_mm=13.0, noise_level=0.030)
ant20 = MicrowaveAntennaSystem(frequency_ghz=10.0, standoff_distance_mm=20.0, antenna_separation_mm=13.0, noise_level=0.030)
mat = CompositeMaterial(name="GFRP", thickness_mm=15.0, relative_permittivity=4.2, loss_tangent=0.020)

_, t_ax, b10, m10 = simulate_b_scan(ant10, mat, "Internal crack", 50.0, 5.0, 5.0, 10.0, 90.0, 50, rng=np.random.default_rng(42))
s_pos, _, b20, m20 = simulate_b_scan(ant20, mat, "Internal crack", 50.0, 5.0, 5.0, 10.0, 90.0, 50, rng=np.random.default_rng(42))

feats10 = extract_features_from_bscan(s_pos, t_ax, b10, 15.0, 4.2, m10["tau_front_ns"], m10["tau_back_ns"])
feats20 = extract_features_from_bscan(s_pos, t_ax, b20, 15.0, 4.2, m20["tau_front_ns"], m20["tau_back_ns"])

predictor = MicrowaveNDTPredictor()
scaler = predictor.classifier.named_steps["scaler"]
rf = predictor.classifier.named_steps["clf"]

fn = predictor.feature_names
print("Comparing Features: Standoff 10mm (Pred: No defect) vs Standoff 20mm (Pred: Internal crack)")
print("-" * 80)
for i, name in enumerate(fn):
    v10 = feats10[i]
    v20 = feats20[i]
    mean_tr = scaler.mean_[i]
    scale_tr = scaler.scale_[i]
    z10 = (v10 - mean_tr) / scale_tr
    z20 = (v20 - mean_tr) / scale_tr
    diff_z = abs(z10 - z20)
    flag = " <--- MAJOR SHIFT" if diff_z > 1.0 else ""
    print(f"  {name:25s}: 10mm={v10:9.4f} (z={z10:5.2f}) | 20mm={v20:9.4f} (z={z20:5.2f}){flag}")
