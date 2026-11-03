import joblib
import numpy as np
from prediction import MicrowaveNDTPredictor

predictor = MicrowaveNDTPredictor()
pipeline = predictor.classifier
scaler = pipeline.named_steps["scaler"]
rf = pipeline.named_steps["clf"]

feat_names = predictor.feature_names
pk_idx = feat_names.index("peak_lateral_x")
scale_pk = scaler.scale_[pk_idx]
mean_pk = scaler.mean_[pk_idx]

splits = []
for tree in rf.estimators_:
    for nid in range(tree.tree_.node_count):
        if tree.tree_.feature[nid] == pk_idx:
            th_scaled = tree.tree_.threshold[nid]
            th_raw = th_scaled * scale_pk + mean_pk
            splits.append(th_raw)

print(f"Number of splits on peak_lateral_x: {len(splits)}")
print(f"Min split: {min(splits):.2f} mm | Max split: {max(splits):.2f} mm | Median split: {np.median(splits):.2f} mm")
print(f"Splits <= 20.0 mm: {sum(1 for s in splits if s <= 20.0)}")
print(f"Splits <= 25.0 mm: {sum(1 for s in splits if s <= 25.0)}")
