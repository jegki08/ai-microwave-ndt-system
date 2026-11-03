import numpy as np
from antenna_simulator import MicrowaveAntennaSystem
from signal_simulator import CompositeMaterial, simulate_b_scan
from prediction import MicrowaveNDTPredictor

antenna = MicrowaveAntennaSystem(
    frequency_ghz=10.0,
    standoff_distance_mm=20.0,
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

pipeline = predictor.classifier
scaler = pipeline.named_steps["scaler"]
rf = pipeline.named_steps["clf"]

features = res["features"]
feat_names = predictor.feature_names
raw_x = np.array([features[name] for name in feat_names]).reshape(1, -1)
scaled_x = scaler.transform(raw_x)

reasons = {}
for tree in rf.estimators_:
    pred = tree.predict(scaled_x)[0]
    if pred == 0: # Voted No defect
        node_indicator = tree.decision_path(scaled_x)
        node_index = node_indicator.indices[node_indicator.indptr[0]:node_indicator.indptr[1]]
        for nid in node_index:
            f_idx = tree.tree_.feature[nid]
            if f_idx >= 0:
                fn = feat_names[f_idx]
                reasons[fn] = reasons.get(fn, 0) + 1

print("Features causing votes for 'No defect' when crack is at x=18, z=3:")
for fn, cnt in sorted(reasons.items(), key=lambda x: x[1], reverse=True)[:10]:
    val = features[fn]
    z_sc = scaled_x[0, feat_names.index(fn)]
    print(f"  {fn:25s}: in {cnt:3d} trees | raw={val:9.4f} | z-score={z_sc:6.2f}")
