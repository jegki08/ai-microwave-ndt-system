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

def generate_robust_sample(
    defect_type: str,
    rng: np.random.Generator,
) -> Tuple[np.ndarray, Dict[str, float]]:
    freq = float(rng.uniform(6.0, 18.0))
    standoff = float(rng.uniform(10.0, 35.0))
    sep = 13.0 # fixed optimal probe separation
    thickness = float(rng.uniform(10.0, 22.0))
    eps_r = float(rng.uniform(3.5, 5.0))
    loss_tan = float(rng.uniform(0.012, 0.030))
    amp = float(rng.uniform(0.85, 1.15))
    noise = float(rng.uniform(0.015, 0.055))

    # Varied scan range
    scan_start = float(rng.choice([0.0, 5.0, 10.0, 15.0]))
    scan_end = float(rng.choice([65.0, 70.0, 80.0, 90.0, 100.0]))
    n_pts = int(rng.choice([25, 30, 40, 50, 60]))

    if defect_type == "No defect":
        def_x = -1.0
        def_z = -1.0
        def_w = 0.0
    elif defect_type == "Internal crack":
        # Defect anywhere within the active scan range
        def_x = float(rng.uniform(scan_start + 4.0, scan_end - 4.0))
        def_z = float(rng.uniform(2.0, thickness - 1.5))
        def_w = float(rng.uniform(2.0, 10.0))
    elif defect_type == "Air void":
        def_x = float(rng.uniform(scan_start + 4.0, scan_end - 4.0))
        def_z = float(rng.uniform(2.5, thickness - 1.5))
        def_w = float(rng.uniform(3.5, 15.0))

    antenna = MicrowaveAntennaSystem(
        frequency_ghz=freq,
        standoff_distance_mm=standoff,
        antenna_separation_mm=sep,
        directivity_n=4.0,
        signal_amplitude=amp,
        noise_level=noise,
    )

    material = CompositeMaterial(
        name="Composite Specimen",
        thickness_mm=thickness,
        relative_permittivity=eps_r,
        loss_tangent=loss_tan,
    )

    scan_pos, time_ax, b_scan, meta = simulate_b_scan(
        antenna=antenna,
        material=material,
        defect_type=defect_type,
        defect_x_mm=def_x,
        defect_z_mm=def_z,
        defect_width_mm=def_w,
        scan_start_x_mm=scan_start,
        scan_end_x_mm=scan_end,
        n_scan_positions=n_pts,
        n_time_points=400,
        rng=rng,
    )

    features = extract_features_from_bscan(
        scan_positions=scan_pos,
        time_axis=time_ax,
        b_scan=b_scan,
        material_thickness_mm=thickness,
        material_eps_r=eps_r,
        tau_front_approx=meta.get("tau_front_ns"),
        tau_back_approx=meta.get("tau_back_ns"),
    )

    ground_truth = {
        "defect_type": defect_type,
        "defect_x_mm": def_x,
        "defect_z_mm": def_z,
        "defect_width_mm": def_w,
        "scan_start": scan_start,
        "scan_end": scan_end,
    }

    return features, ground_truth
