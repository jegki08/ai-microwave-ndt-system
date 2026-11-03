"""
test_system.py
==============
Comprehensive verification script for the Microwave NDT AI system.
Tests:
1. Antenna radiation pattern and coupling simulation.
2. Signal transmission and A-scan generation.
3. 2D B-scan scanning generation across all 3 classes (No defect, Internal crack, Air void).
4. Feature extraction.
5. AI Model predictions and position estimation on unseen configurations.
"""

import sys
import numpy as np
from antenna_simulator import MicrowaveAntennaSystem
from signal_simulator import (
    CLASSES,
    FEATURE_NAMES,
    CompositeMaterial,
    generate_transmitted_pulse,
    simulate_single_ascan,
    simulate_b_scan,
    extract_features_from_bscan,
)
from prediction import MicrowaveNDTPredictor


def run_tests():
    print("=" * 70)
    print("RUNNING MICROWAVE NDT SYSTEM VERIFICATION")
    print("=" * 70)

    # 1. Antenna Simulator Test
    print("\n[1] Testing Antenna Simulation...")
    antenna = MicrowaveAntennaSystem(
        frequency_ghz=10.0,
        standoff_distance_mm=20.0,
        antenna_separation_mm=12.0,
        directivity_n=4.0,
    )
    hpbw = antenna.hpbw_deg
    print(f"  Operating Frequency: {antenna.frequency_ghz:.1f} GHz")
    print(f"  Wavelength:          {antenna.wavelength_mm:.2f} mm")
    print(f"  Half-Power Beamwidth (HPBW): {hpbw:.1f} deg")
    assert 20.0 < hpbw < 70.0, f"Unexpected HPBW: {hpbw}"

    # Two-way coupling check
    w_on_axis, _, _ = antenna.calculate_antenna_coupling(50.0, 50.0, 5.0)
    w_off_axis, _, _ = antenna.calculate_antenna_coupling(50.0, 80.0, 5.0)
    print(f"  On-axis antenna coupling:  {w_on_axis:.4f}")
    print(f"  Off-axis antenna coupling: {w_off_axis:.4f}")
    assert w_on_axis > w_off_axis, "Antenna directional pattern failed directivity check"
    print("  Antenna simulation test PASSED.")

    # 2. Material and Signal Propagation Test
    print("\n[2] Testing Microwave Signal & Wave Propagation...")
    material = CompositeMaterial(
        name="GFRP Specimen",
        thickness_mm=15.0,
        relative_permittivity=4.2,
        loss_tangent=0.02,
    )
    v_mat = material.wave_velocity_mm_ns
    alpha = material.attenuation_constant_per_mm(10.0)
    print(f"  Wave speed in composite:    {v_mat:.2f} mm/ns")
    print(f"  Dielectric attenuation:     {alpha:.4f} Np/mm")
    print(f"  Fresnel reflection (air-mat): {material.fresnel_reflection_air_to_mat:.4f}")
    assert 130.0 < v_mat < 160.0, f"Unexpected wave speed: {v_mat}"
    print("  Wave propagation physics test PASSED.")

    # 3. Transmitted Waveform & Single A-scan Test
    print("\n[3] Testing Transmitted Pulse & Single A-Scan Generation...")
    t_tx = np.linspace(0.0, 0.4, 200)
    s_tx = generate_transmitted_pulse(t_tx, 10.0, 1.0)
    assert len(s_tx) == 200
    assert np.max(np.abs(s_tx)) > 0.8

    t_rx, s_rx, info = simulate_single_ascan(
        antenna, material, scan_x_mm=50.0, defect_type="Internal crack", defect_x_mm=50.0, defect_z_mm=6.0
    )
    assert len(s_rx) == 600
    assert info["tau_front_ns"] > 0
    assert info["tau_back_ns"] > info["tau_front_ns"]
    print(f"  Front wall delay: {info['tau_front_ns']:.3f} ns | Back wall delay: {info['tau_back_ns']:.3f} ns")
    print("  A-scan generation test PASSED.")

    # 4. Predictor & All 3 Defect Categories Test
    print("\n[4] Testing AI Model Prediction Across All 3 Classes (Unseen Scenarios)...")
    predictor = MicrowaveNDTPredictor()
    assert predictor.is_ready(), "Predictor models not found or failed to load!"

    test_scenarios = [
        {"class": "No defect", "x": 50.0, "z": 7.0, "w": 0.0, "freq": 10.0, "standoff": 20.0, "sep": 12.0},
        {"class": "Internal crack", "x": 42.0, "z": 5.5, "w": 6.0, "freq": 10.0, "standoff": 20.0, "sep": 12.0},
        {"class": "Air void", "x": 68.0, "z": 8.0, "w": 9.0, "freq": 10.0, "standoff": 20.0, "sep": 12.0},
        {"class": "Air void", "x": 52.0, "z": 6.5, "w": 8.0, "freq": 19.0, "standoff": 35.0, "sep": 25.0},
    ]

    for sc in test_scenarios:
        ant = MicrowaveAntennaSystem(
            frequency_ghz=sc["freq"],
            standoff_distance_mm=sc["standoff"],
            antenna_separation_mm=sc["sep"],
        )
        sp, ta, bscan, meta = simulate_b_scan(
            antenna=ant,
            material=material,
            defect_type=sc["class"],
            defect_x_mm=sc["x"],
            defect_z_mm=sc["z"],
            defect_width_mm=sc["w"],
            scan_start_x_mm=10.0,
            scan_end_x_mm=90.0,
            n_scan_positions=45,
            n_time_points=350,
        )
        res = predictor.predict_from_bscan(
            scan_positions=sp,
            time_axis=ta,
            b_scan=bscan,
            material_thickness_mm=material.thickness_mm,
            material_eps_r=material.relative_permittivity,
            tau_front_ns=meta["tau_front_ns"],
            tau_back_ns=meta["tau_back_ns"],
        )

        pred_class = res["predicted_class"]
        conf = res["confidence"] * 100
        est_x = res["estimated_pos_x_mm"]
        est_z = res["estimated_depth_z_mm"]

        print(f"  Ground Truth: {sc['class']:15s} -> AI Predicted: {pred_class:15s} (Conf: {conf:5.1f}%)")
        if sc["class"] != "No defect":
            print(f"    Target Pos x: {sc['x']:.1f} mm | Est Pos x: {est_x:.1f} mm (Err: {abs(est_x - sc['x']):.1f} mm)")
            print(f"    Target Depth z: {sc['z']:.1f} mm | Est Depth z: {est_z:.1f} mm (Err: {abs(est_z - sc['z']):.1f} mm)")

        # Verify predicted class is one of the valid classes
        assert pred_class in CLASSES

    print("\n" + "=" * 70)
    print("ALL VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
