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

# Test if scan range was 0 to 70 mm while defect was at 85 mm!
scan_pos, time_ax, b_scan, meta = simulate_b_scan(
    antenna=antenna,
    material=material,
    defect_type="Internal crack",
    defect_x_mm=85.0,
    defect_z_mm=13.5,
    defect_width_mm=4.0,
    scan_start_x_mm=0.0,
    scan_end_x_mm=70.0,
    n_scan_positions=60,
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

print(f"When scan is 0-70 mm and defect is at x=85 mm:")
print(f"  Prediction: {res['predicted_class']} (Confidence: {res['confidence']*100:.1f}%)")
for c, p in res["probabilities"].items():
    print(f"    {c}: {p*100:.1f}%")
print(f"  Defect Gate Peak Amplitude: {res['features']['defect_window_max_amp']:.4f} V")
print(f"  Defect-to-Front Ratio: {res['features']['defect_to_front_ratio']:.3f}")
print(f"  Backwall Echo Drop Ratio: {res['features']['backwall_drop_ratio']*100:.1f}%")
print(f"  Time-of-Flight Inferred Depth: {res['features']['inferred_depth_mm']:.2f} mm")
print(f"  Spatial Echo Width (FWHM): {res['features']['spatial_fwhm_mm']:.2f} mm")
