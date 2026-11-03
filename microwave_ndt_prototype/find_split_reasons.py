import numpy as np
from prediction import MicrowaveNDTPredictor
from debug_root_cause import ai_results

predictor = MicrowaveNDTPredictor()
pipeline = predictor.classifier
scaler = pipeline.named_steps["scaler"]
rf = pipeline.named_steps["clf"]

feat_names = predictor.feature_names
raw_x = np.array([ai_results["features"][name] for name in feat_names]).reshape(1, -1)
scaled_x = scaler.transform(raw_x)

reasons = {}

for tree_idx, tree in enumerate(rf.estimators_):
    pred = tree.predict(scaled_x)[0]
    if pred == 0: # voted No defect
        node_indicator = tree.decision_path(scaled_x)
        node_index = node_indicator.indices[node_indicator.indptr[0]:node_indicator.indptr[1]]
        for nid in node_index:
            f_idx = tree.tree_.feature[nid]
            if f_idx >= 0:
                fn = feat_names[f_idx]
                th = tree.tree_.threshold[nid]
                val = scaled_x[0, f_idx]
                raw_th = th * scaler.scale_[f_idx] + scaler.mean_[f_idx]
                raw_val = raw_x[0, f_idx]
                reasons[fn] = reasons.get(fn, 0) + 1

print("Top features leading to 'No defect' votes in the ensemble:")
for fn, cnt in sorted(reasons.items(), key=lambda x: x[1], reverse=True)[:10]:
    raw_v = ai_results["features"][fn]
    print(f"  {fn:25s}: used in {cnt} splits | current raw value = {raw_v:.4f}")
