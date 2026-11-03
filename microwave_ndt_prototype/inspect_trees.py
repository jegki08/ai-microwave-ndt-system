import joblib
import numpy as np
from prediction import MicrowaveNDTPredictor

predictor = MicrowaveNDTPredictor()
pipeline = predictor.classifier
scaler = pipeline.named_steps["scaler"]
rf = pipeline.named_steps["clf"]

# Load features from debug
from debug_root_cause import ai_results

features = ai_results["features"]
feat_names = predictor.feature_names
raw_x = np.array([features[name] for name in feat_names]).reshape(1, -1)
scaled_x = scaler.transform(raw_x)

print("Classifier classes:", rf.classes_)
tree_votes = [tree.predict(scaled_x)[0] for tree in rf.estimators_]
print("Tree vote counts:")
for cls_idx in range(len(rf.classes_)):
    cnt = sum(1 for v in tree_votes if v == cls_idx)
    print(f"  Class {cls_idx} ({predictor.class_names[cls_idx]}): {cnt} / {len(tree_votes)} ({cnt/len(tree_votes)*100:.1f}%)")

# Let's inspect which features differ most from the training distribution
print("\nFeature comparisons (Raw value vs Scaled value):")
for i, name in enumerate(feat_names):
    mean_val = scaler.mean_[i]
    scale_val = scaler.scale_[i]
    val = raw_x[0, i]
    s_val = scaled_x[0, i]
    print(f"  {name:25s}: raw={val:9.4f} | mean={mean_val:9.4f} | std={scale_val:9.4f} | z-score={s_val:6.2f}")
