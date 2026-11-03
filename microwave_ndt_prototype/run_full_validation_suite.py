"""
Comprehensive Automated Test Suite for Microwave NDT System.
Tests:
A. Defect Type Tests (No defect, Internal crack, Air void)
B. Defect Position Tests (Near start, middle, near end, between steps, outside range)
C. Defect Depth Tests (Shallow, medium, deep)
D. Crack Width Tests (Narrow, medium, wide)
E. Scanning Range Tests (Small, large, low/high steps)
F. Antenna Configuration Tests (Frequency, standoff, amplitude, noise)
G. User-Reported Edge Cases
"""

import numpy as np
from typing import Dict, Any, List
from antenna_simulator import MicrowaveAntennaSystem
from signal_simulator import CompositeMaterial, simulate_b_scan
from prediction import MicrowaveNDTPredictor

def run_single_test(
    case_name: str,
    gt_type: str,
    defect_x: float,
    defect_z: float,
    defect_w: float,
    scan_start: float = 10.0,
    scan_end: float = 90.0,
    n_steps: int = 50,
    freq_ghz: float = 10.0,
    standoff_mm: float = 20.0,
    noise_level: float = 0.030,
    seed: int = 42,
    predictor: MicrowaveNDTPredictor = None,
) -> Dict[str, Any]:
    predictor = predictor or MicrowaveNDTPredictor()

    antenna = MicrowaveAntennaSystem(
        frequency_ghz=freq_ghz,
        standoff_distance_mm=standoff_mm,
        antenna_separation_mm=13.0,
        directivity_n=4.0,
        signal_amplitude=1.0,
        noise_level=noise_level,
    )
    material = CompositeMaterial(
        name="GFRP",
        thickness_mm=15.0,
        relative_permittivity=4.2,
        loss_tangent=0.020,
    )

    scan_pos, time_ax, b_scan, meta = simulate_b_scan(
        antenna=antenna,
        material=material,
        defect_type=gt_type,
        defect_x_mm=defect_x,
        defect_z_mm=defect_z,
        defect_width_mm=defect_w,
        scan_start_x_mm=scan_start,
        scan_end_x_mm=scan_end,
        n_scan_positions=n_steps,
        rng=np.random.default_rng(seed),
    )

    res = predictor.predict_from_bscan(
        scan_positions=scan_pos,
        time_axis=time_ax,
        b_scan=b_scan,
        material_thickness_mm=15.0,
        material_eps_r=4.2,
        tau_front_ns=meta["tau_front_ns"],
        tau_back_ns=meta["tau_back_ns"],
    )

    pred_class = res["predicted_class"]
    confidence = res["confidence"]
    est_x = res["estimated_pos_x_mm"]
    est_z = res["estimated_depth_z_mm"]

    # Determine ground truth within the scanned region
    is_in_scan = (scan_start <= defect_x <= scan_end) if gt_type != "No defect" else True
    effective_gt = gt_type if is_in_scan else "No defect"

    # Evaluation
    class_match = (pred_class == effective_gt)
    
    pos_err = abs(est_x - defect_x) if (effective_gt != "No defect" and est_x is not None) else 0.0
    depth_err = abs(est_z - defect_z) if (effective_gt != "No defect" and est_z is not None) else 0.0

    passed = class_match

    return {
        "case_name": case_name,
        "gt_type": gt_type,
        "effective_gt": effective_gt,
        "pred_class": pred_class,
        "confidence": confidence,
        "defect_x": defect_x,
        "est_x": est_x,
        "pos_err": pos_err,
        "defect_z": defect_z,
        "est_z": est_z,
        "depth_err": depth_err,
        "defect_w": defect_w,
        "scan_range": f"{scan_start:.0f}-{scan_end:.0f}",
        "n_steps": n_steps,
        "freq_ghz": freq_ghz,
        "passed": passed,
    }

if __name__ == "__main__":
    predictor = MicrowaveNDTPredictor()

    test_cases = [
        # User Reported Case 1: Crack at x=18, z=3, w=4, scan 0-70, 30 steps
        ("User Case: Crack x=18 z=3", "Internal crack", 18.0, 3.0, 4.0, 0.0, 70.0, 30, 10.0, 20.0),
        # User Reported Case 2: Crack at x=85, z=13.5 (outside 0-70 scan)
        ("User Case: Crack x=85 z=13.5 outside 0-70", "Internal crack", 85.0, 13.5, 4.0, 0.0, 70.0, 60, 15.5, 11.0),
        # User Reported Case 3: Crack at x=85, z=13.5 (inside 10-90 scan)
        ("User Case: Crack x=85 z=13.5 inside 10-90", "Internal crack", 85.0, 13.5, 4.0, 10.0, 90.0, 50, 15.5, 11.0),

        # Group A: Defect Type Tests
        ("Type: No defect standard", "No defect", 50.0, 7.5, 0.0, 10.0, 90.0, 50, 10.0, 20.0),
        ("Type: Internal crack standard", "Internal crack", 50.0, 6.0, 5.0, 10.0, 90.0, 50, 10.0, 20.0),
        ("Type: Air void standard", "Air void", 50.0, 6.0, 8.0, 10.0, 90.0, 50, 10.0, 20.0),

        # Group B: Defect Position Tests
        ("Pos: Near start x=15", "Internal crack", 15.0, 5.0, 4.0, 10.0, 90.0, 50, 10.0, 20.0),
        ("Pos: Middle x=50", "Internal crack", 50.0, 5.0, 4.0, 10.0, 90.0, 50, 10.0, 20.0),
        ("Pos: Near end x=85", "Internal crack", 85.0, 5.0, 4.0, 10.0, 90.0, 50, 10.0, 20.0),
        ("Pos: Non-grid x=37.3", "Internal crack", 37.3, 5.0, 4.0, 10.0, 90.0, 50, 10.0, 20.0),
        ("Pos: Outside scan x=95 (scan 10-90)", "Internal crack", 95.0, 5.0, 4.0, 10.0, 90.0, 50, 10.0, 20.0),

        # Group C: Defect Depth Tests
        ("Depth: Shallow z=2.5", "Internal crack", 45.0, 2.5, 4.0, 10.0, 90.0, 50, 10.0, 20.0),
        ("Depth: Medium z=7.0", "Internal crack", 45.0, 7.0, 4.0, 10.0, 90.0, 50, 10.0, 20.0),
        ("Depth: Deep z=12.5", "Internal crack", 45.0, 12.5, 4.0, 10.0, 90.0, 50, 10.0, 20.0),

        # Group D: Crack Width / Void Size Tests
        ("Width: Narrow crack w=2.5", "Internal crack", 50.0, 5.0, 2.5, 10.0, 90.0, 50, 10.0, 20.0),
        ("Width: Wide crack w=10.0", "Internal crack", 50.0, 5.0, 10.0, 10.0, 90.0, 50, 10.0, 20.0),
        ("Void: Small void w=4.0", "Air void", 50.0, 5.0, 4.0, 10.0, 90.0, 50, 10.0, 20.0),
        ("Void: Large void w=14.0", "Air void", 50.0, 5.0, 14.0, 10.0, 90.0, 50, 10.0, 20.0),

        # Group E: Scanning Range & Step Resolution Tests
        ("Scan: Low steps (25 steps)", "Internal crack", 50.0, 5.0, 4.0, 10.0, 90.0, 25, 10.0, 20.0),
        ("Scan: High steps (75 steps)", "Internal crack", 50.0, 5.0, 4.0, 10.0, 90.0, 75, 10.0, 20.0),
        ("Scan: Shifted range 0-70 mm", "Internal crack", 35.0, 5.0, 4.0, 0.0, 70.0, 45, 10.0, 20.0),
        ("Scan: Shifted range 20-100 mm", "Internal crack", 60.0, 5.0, 4.0, 20.0, 100.0, 45, 10.0, 20.0),

        # Group F: Antenna Configuration Tests
        ("Antenna: Low freq 6.0 GHz", "Internal crack", 50.0, 5.0, 5.0, 10.0, 90.0, 50, 6.0, 20.0),
        ("Antenna: High freq 16.0 GHz", "Internal crack", 50.0, 5.0, 5.0, 10.0, 90.0, 50, 16.0, 20.0),
        ("Antenna: Close standoff 10 mm", "Internal crack", 50.0, 5.0, 5.0, 10.0, 90.0, 50, 10.0, 10.0),
        ("Antenna: Far standoff 35 mm", "Internal crack", 50.0, 5.0, 5.0, 10.0, 90.0, 50, 10.0, 35.0),
        ("Antenna: High noise (sigma=0.06)", "Internal crack", 50.0, 5.0, 5.0, 10.0, 90.0, 50, 10.0, 20.0, 0.060),
    ]

    print(f"Executing Automated Test Suite ({len(test_cases)} Test Cases)...")
    print("=" * 85)
    passed_count = 0

    for idx, tc in enumerate(test_cases, start=1):
        c_name = tc[0]
        params = tc[1:]
        res = run_single_test(c_name, *params, predictor=predictor)
        status = "PASS" if res["passed"] else "FAIL"
        if res["passed"]:
            passed_count += 1
        pos_str = f"x={res['est_x']:.1f}" if res['est_x'] is not None else "N/A"
        dep_str = f"z={res['est_z']:.1f}" if res['est_z'] is not None else "N/A"
        print(f"[{idx:2d}/{len(test_cases)}] {status:4s} | {c_name:35s} | GT: {res['effective_gt']:14s} -> Pred: {res['pred_class']:14s} ({res['confidence']*100:.1f}%) | {pos_str}, {dep_str}")

    print("=" * 85)
    print(f"SUMMARY: {passed_count} / {len(test_cases)} tests passed ({passed_count/len(test_cases)*100:.1f}%)")
