import numpy as np
from prediction import MicrowaveNDTPredictor
from debug_root_cause import ai_results

predictor = MicrowaveNDTPredictor()
features = dict(ai_results["features"])

print("--- With old FWHM = 46.27 mm ---")
res_old = predictor.predict_from_features(np.array([features[name] for name in predictor.feature_names]))
print(f"Pred: {res_old['predicted_class']} ({res_old['confidence']*100:.1f}%)")
for c, p in res_old['probabilities'].items():
    print(f"  {c}: {p*100:.1f}%")

print("\n--- With corrected baseline FWHM = 4.75 mm ---")
features["spatial_fwhm_mm"] = 4.75
res_new = predictor.predict_from_features(np.array([features[name] for name in predictor.feature_names]))
print(f"Pred: {res_new['predicted_class']} ({res_new['confidence']*100:.1f}%)")
for c, p in res_new['probabilities'].items():
    print(f"  {c}: {p*100:.1f}%")
print(f"Est pos x: {res_new['estimated_pos_x_mm']:.1f} mm (Target: 38.0 mm)")
print(f"Est depth z: {res_new['estimated_depth_z_mm']:.1f} mm (Target: 5.0 mm)")
