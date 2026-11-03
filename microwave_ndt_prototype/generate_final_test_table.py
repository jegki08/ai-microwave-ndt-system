import numpy as np
from typing import Dict, Any, List
from antenna_simulator import MicrowaveAntennaSystem
from signal_simulator import CompositeMaterial, simulate_b_scan
from prediction import MicrowaveNDTPredictor

predictor = MicrowaveNDTPredictor()

test_cases = [
    # Ground Truth, Defect X, Depth Z, Width, Scan Start, Scan End, Steps, Freq, Standoff, Noise, Case Description
    ("Internal crack", 18.0, 3.0, 4.0, 0.0, 70.0, 30, 10.0, 20.0, 0.030, "User Reported Case: Crack x=18 z=3"),
    ("Internal crack", 85.0, 13.5, 4.0, 0.0, 70.0, 60, 15.5, 11.0, 0.030, "User Case: Crack x=85 z=13.5 outside 0-70"),
    ("Internal crack", 85.0, 13.5, 4.0, 10.0, 90.0, 50, 15.5, 11.0, 0.030, "User Case: Crack x=85 z=13.5 inside 10-90"),
    ("No defect", -1.0, -1.0, 0.0, 10.0, 90.0, 50, 10.0, 20.0, 0.030, "Type: Pristine healthy specimen"),
    ("Internal crack", 50.0, 6.0, 5.0, 10.0, 90.0, 50, 10.0, 20.0, 0.030, "Type: Standard internal crack"),
    ("Air void", 50.0, 6.0, 8.0, 10.0, 90.0, 50, 10.0, 20.0, 0.030, "Type: Standard volumetric air void"),
    ("Internal crack", 15.0, 5.0, 4.0, 10.0, 90.0, 50, 10.0, 20.0, 0.030, "Pos: Near start boundary x=15"),
    ("Internal crack", 50.0, 5.0, 4.0, 10.0, 90.0, 50, 10.0, 20.0, 0.030, "Pos: Centered specimen x=50"),
    ("Internal crack", 85.0, 5.0, 4.0, 10.0, 90.0, 50, 10.0, 20.0, 0.030, "Pos: Near end boundary x=85"),
    ("Internal crack", 37.3, 5.0, 4.0, 10.0, 90.0, 50, 10.0, 20.0, 0.030, "Pos: Inter-grid position x=37.3"),
    ("Internal crack", 95.0, 5.0, 4.0, 10.0, 90.0, 50, 10.0, 20.0, 0.030, "Pos: Defect outside scan x=95 (10-90)"),
    ("Internal crack", 45.0, 2.5, 4.0, 10.0, 90.0, 50, 10.0, 20.0, 0.030, "Depth: Near-surface shallow z=2.5"),
    ("Internal crack", 45.0, 7.0, 4.0, 10.0, 90.0, 50, 10.0, 20.0, 0.030, "Depth: Mid-depth z=7.0"),
    ("Internal crack", 45.0, 12.5, 4.0, 10.0, 90.0, 50, 10.0, 20.0, 0.030, "Depth: Deep backwall boundary z=12.5"),
    ("Internal crack", 50.0, 5.0, 2.5, 10.0, 90.0, 50, 10.0, 20.0, 0.030, "Width: Fine hairline crack w=2.5"),
    ("Internal crack", 50.0, 5.0, 10.0, 10.0, 90.0, 50, 10.0, 20.0, 0.030, "Width: Wide delamination w=10.0"),
    ("Air void", 50.0, 5.0, 4.0, 10.0, 90.0, 50, 10.0, 20.0, 0.030, "Void: Small pore cavity w=4.0"),
    ("Air void", 50.0, 5.0, 14.0, 10.0, 90.0, 50, 10.0, 20.0, 0.030, "Void: Large air blister w=14.0"),
    ("Internal crack", 50.0, 5.0, 4.0, 10.0, 90.0, 25, 10.0, 20.0, 0.030, "Scan: Coarse resolution (25 steps)"),
    ("Internal crack", 50.0, 5.0, 4.0, 10.0, 90.0, 75, 10.0, 20.0, 0.030, "Scan: Fine resolution (75 steps)"),
    ("Internal crack", 35.0, 5.0, 4.0, 0.0, 70.0, 45, 10.0, 20.0, 0.030, "Scan: Custom range 0-70 mm"),
    ("Internal crack", 60.0, 5.0, 4.0, 20.0, 100.0, 45, 10.0, 20.0, 0.030, "Scan: Custom range 20-100 mm"),
    ("Internal crack", 50.0, 5.0, 5.0, 10.0, 90.0, 50, 6.0, 20.0, 0.030, "Antenna: C-band frequency 6.0 GHz"),
    ("Internal crack", 50.0, 5.0, 5.0, 10.0, 90.0, 50, 16.0, 20.0, 0.030, "Antenna: Ku-band frequency 16.0 GHz"),
    ("Internal crack", 50.0, 5.0, 5.0, 10.0, 90.0, 50, 10.0, 10.0, 0.030, "Antenna: Close standoff 10 mm"),
    ("Internal crack", 50.0, 5.0, 5.0, 10.0, 90.0, 50, 10.0, 35.0, 0.030, "Antenna: Far standoff 35 mm"),
    ("Internal crack", 50.0, 5.0, 5.0, 10.0, 90.0, 50, 10.0, 20.0, 0.060, "Antenna: Severe noise sigma=0.060"),
]

print("| Ground Truth | Defect X | Depth Z | Width | Scan Range | Predicted Class | Result | Notes |")
print("|---|---:|---:|---:|---|---|---|---|")

passed_cnt = 0
for tc in test_cases:
    gt_type, dx, dz, dw, ss, se, steps, f_ghz, stand, noise, desc = tc
    
    ant = MicrowaveAntennaSystem(
        frequency_ghz=f_ghz,
        standoff_distance_mm=stand,
        antenna_separation_mm=13.0,
        directivity_n=4.0,
        signal_amplitude=1.0,
        noise_level=noise,
    )
    mat = CompositeMaterial(name="GFRP", thickness_mm=15.0, relative_permittivity=4.2, loss_tangent=0.020)

    sp, ta, bscan, meta = simulate_b_scan(
        antenna=ant,
        material=mat,
        defect_type=gt_type,
        defect_x_mm=dx if gt_type != "No defect" else 50.0,
        defect_z_mm=dz if gt_type != "No defect" else 7.5,
        defect_width_mm=dw,
        scan_start_x_mm=ss,
        scan_end_x_mm=se,
        n_scan_positions=steps,
        rng=np.random.default_rng(42),
    )

    res = predictor.predict_from_bscan(
        scan_positions=sp,
        time_axis=ta,
        b_scan=bscan,
        material_thickness_mm=15.0,
        material_eps_r=4.2,
        tau_front_ns=meta["tau_front_ns"],
        tau_back_ns=meta["tau_back_ns"],
    )

    pred = res["predicted_class"]
    conf = res["confidence"] * 100
    est_x = res["estimated_pos_x_mm"]
    est_z = res["estimated_depth_z_mm"]

    is_in_scan = (ss <= dx <= se) if gt_type != "No defect" else True
    eff_gt = gt_type if is_in_scan else "No defect"

    passed = (pred == eff_gt)
    if passed:
        passed_cnt += 1
    res_str = "PASS" if passed else "FAIL"

    dx_str = f"{dx:.1f}" if gt_type != "No defect" else "N/A"
    dz_str = f"{dz:.1f}" if gt_type != "No defect" else "N/A"
    dw_str = f"{dw:.1f}" if gt_type != "No defect" else "N/A"
    sr_str = f"{ss:.0f}–{se:.0f} mm"

    notes = ""
    if not is_in_scan:
        notes = f"Defect outside scan [{ss:.0f}–{se:.0f}]. Pristine scan."
    elif est_x is not None and est_z is not None:
        notes = f"Est: x={est_x:.1f}mm, z={est_z:.1f}mm (Conf: {conf:.1f}%)"
    else:
        notes = f"Conf: {conf:.1f}%"

    print(f"| {gt_type} | {dx_str} | {dz_str} | {dw_str} | {sr_str} | {pred} | {res_str} | {notes} |")

print(f"\nTotal: {passed_cnt}/{len(test_cases)} ({passed_cnt/len(test_cases)*100:.1f}%)")
