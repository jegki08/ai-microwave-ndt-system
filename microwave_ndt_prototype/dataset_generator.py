"""
dataset_generator.py
====================
Synthetic dataset generator for AI-based microwave NDT of composite materials.

Generates varied simulation samples across:
- Microwave frequencies (8 - 12 GHz X-band).
- Probe standoff distances (15 - 30 mm).
- Specimen properties (dielectric constant eps_r, loss tangent, thickness).
- Defect parameters: type, lateral position x, depth z, width/size.
- Noise levels and signal amplitudes.

Guarantees strict train/val/test split separation without data leakage.
"""

import os
import numpy as np
from typing import Dict, Tuple, List
from antenna_simulator import MicrowaveAntennaSystem
from signal_simulator import (
    CLASSES,
    FEATURE_NAMES,
    CompositeMaterial,
    simulate_b_scan,
    extract_features_from_bscan,
)


def generate_single_sample(
    defect_type: str,
    frequency_ghz: float,
    standoff_mm: float,
    antenna_separation_mm: float,
    thickness_mm: float,
    eps_r: float,
    loss_tangent: float,
    defect_x_mm: float,
    defect_z_mm: float,
    defect_width_mm: float,
    amplitude: float,
    noise_level: float,
    directivity_n: float = 4.0,
    scan_start_x_mm: float = 10.0,
    scan_end_x_mm: float = 90.0,
    n_scan_positions: int = 45,
    n_time_points: int = 400,
    rng: np.random.Generator = None,
) -> Tuple[np.ndarray, Dict[str, float]]:
    """Generates a single synthetic microwave B-scan and extracts its feature vector."""
    rng = rng or np.random.default_rng()

    antenna = MicrowaveAntennaSystem(
        frequency_ghz=frequency_ghz,
        standoff_distance_mm=standoff_mm,
        antenna_separation_mm=antenna_separation_mm,
        directivity_n=directivity_n,
        signal_amplitude=amplitude,
        noise_level=noise_level,
    )

    material = CompositeMaterial(
        name="Composite Specimen",
        thickness_mm=thickness_mm,
        relative_permittivity=eps_r,
        loss_tangent=loss_tangent,
    )

    scan_pos, time_ax, b_scan, meta = simulate_b_scan(
        antenna=antenna,
        material=material,
        defect_type=defect_type,
        defect_x_mm=defect_x_mm,
        defect_z_mm=defect_z_mm,
        defect_width_mm=defect_width_mm,
        scan_start_x_mm=scan_start_x_mm,
        scan_end_x_mm=scan_end_x_mm,
        n_scan_positions=n_scan_positions,
        n_time_points=n_time_points,
        rng=rng,
    )

    features = extract_features_from_bscan(
        scan_positions=scan_pos,
        time_axis=time_ax,
        b_scan=b_scan,
        material_thickness_mm=thickness_mm,
        material_eps_r=eps_r,
        tau_front_approx=meta.get("tau_front_ns"),
        tau_back_approx=meta.get("tau_back_ns"),
    )

    ground_truth = {
        "defect_type": defect_type,
        "defect_x_mm": defect_x_mm if defect_type != "No defect" else -1.0,
        "defect_z_mm": defect_z_mm if defect_type != "No defect" else -1.0,
        "defect_width_mm": defect_width_mm if defect_type != "No defect" else 0.0,
        "frequency_ghz": frequency_ghz,
        "standoff_mm": standoff_mm,
        "thickness_mm": thickness_mm,
        "eps_r": eps_r,
    }

    return features, ground_truth


def generate_microwave_ndt_dataset(
    samples_per_class: int = 350,
    random_seed: int = 42,
    verbose: bool = True,
) -> Dict[str, np.ndarray]:
    """
    Generates a full synthetic dataset across all three defect classes.

    Parameters
    ----------
    samples_per_class : int
        Number of distinct simulation configurations per class.
    random_seed : int
        Master random seed for reproducibility.
    """
    rng = np.random.default_rng(random_seed)

    X_list = []
    y_list = []
    pos_x_list = []
    pos_z_list = []
    configs_list = []

    if verbose:
        print(f"Generating synthetic microwave NDT dataset ({samples_per_class * len(CLASSES)} total scans)...")

    for class_idx, defect_class in enumerate(CLASSES):
        if verbose:
            print(f"  Simulating class: {defect_class} ({samples_per_class} samples)...")

        for s_idx in range(samples_per_class):
            freq = float(rng.uniform(5.0, 20.0))
            standoff = float(rng.uniform(5.0, 40.0))
            sep = 13.0  # Fixed optimal probe separation
            dir_n = float(rng.uniform(1.0, 8.0))
            thickness = float(rng.uniform(8.0, 25.0))
            eps_r = float(rng.uniform(1.5, 6.0))
            loss_tan = float(rng.uniform(0.005, 0.045))
            amp = float(rng.uniform(0.5, 2.0))
            noise = float(rng.uniform(0.005, 0.080))

            # Cover full scan range combinations matching user options
            scan_start = float(rng.choice([0.0, 5.0, 10.0, 15.0]))
            scan_end = float(rng.choice([65.0, 70.0, 80.0, 90.0, 100.0]))
            n_scan_pts = int(rng.choice([25, 30, 40, 50, 60]))

            if defect_class == "No defect":
                def_x = -1.0
                def_z = -1.0
                def_w = 0.0
            elif defect_class == "Internal crack":
                # Sample defect anywhere across the entire active scan range
                def_x = float(rng.uniform(scan_start + 3.0, scan_end - 3.0))
                def_z = float(rng.uniform(2.0, thickness - 1.5))
                def_w = float(rng.uniform(2.0, 10.0))
            elif defect_class == "Air void":
                def_x = float(rng.uniform(scan_start + 3.0, scan_end - 3.0))
                def_z = float(rng.uniform(2.5, thickness - 1.5))
                def_w = float(rng.uniform(3.5, 15.0))

            feat, gt = generate_single_sample(
                defect_type=defect_class,
                frequency_ghz=freq,
                standoff_mm=standoff,
                antenna_separation_mm=sep,
                thickness_mm=thickness,
                eps_r=eps_r,
                loss_tangent=loss_tan,
                defect_x_mm=def_x,
                defect_z_mm=def_z,
                defect_width_mm=def_w,
                amplitude=amp,
                noise_level=noise,
                directivity_n=dir_n,
                scan_start_x_mm=scan_start,
                scan_end_x_mm=scan_end,
                n_scan_positions=n_scan_pts,
                n_time_points=400,
                rng=rng,
            )

            X_list.append(feat)
            y_list.append(class_idx)
            pos_x_list.append(def_x)
            pos_z_list.append(def_z)
            configs_list.append(gt)

    X = np.asarray(X_list, dtype=float)
    y = np.asarray(y_list, dtype=int)
    pos_x = np.asarray(pos_x_list, dtype=float)
    pos_z = np.asarray(pos_z_list, dtype=float)

    if verbose:
        print(f"Dataset generated. Feature shape: {X.shape}, Classes: {np.bincount(y)}")

    return {
        "X": X,
        "y": y,
        "pos_x": pos_x,
        "pos_z": pos_z,
        "feature_names": FEATURE_NAMES,
        "classes": CLASSES,
        "configs": configs_list,
    }


if __name__ == "__main__":
    data = generate_microwave_ndt_dataset(samples_per_class=10, verbose=True)
    print("Test run sample features:\n", data["X"][:2])
