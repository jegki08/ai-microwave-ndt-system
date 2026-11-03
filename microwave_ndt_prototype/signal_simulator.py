"""
signal_simulator.py
===================
Microwave signal transmission, reflection, and B-scan generation for composite NDT.

Physical concepts modeled:
- Transmitted microwave modulated Gaussian pulse.
- Speed of light in composite medium: v = c / sqrt(epsilon_r).
- High-frequency dielectric attenuation: alpha(f, epsilon_r, tan_delta).
- Fresnel reflection and transmission at air-dielectric and dielectric-defect interfaces.
- Time-of-flight (ToF) calculations for front-wall, internal defects, and back-wall.
- Antenna beam pattern coupling as a function of scanning position.
- Defect shadowing effect (back-wall echo amplitude drop).
- Multi-feature extraction for machine learning classification and localization.

CLASSES:
1. "No defect"
2. "Internal crack"
3. "Air void"
"""

import numpy as np
from scipy.signal import hilbert
from typing import Dict, Tuple, Any, Optional
from antenna_simulator import MicrowaveAntennaSystem

CLASSES = ["No defect", "Internal crack", "Air void"]

# Speed of light in vacuum in mm / ns (c = 3e8 m/s = 300 mm/ns)
C_SPEED_MM_NS = 300.0


class CompositeMaterial:
    """Represents the composite material specimen under microwave inspection."""

    def __init__(
        self,
        name: str = "Glass Fiber Reinforced Polymer (GFRP)",
        thickness_mm: float = 15.0,
        relative_permittivity: float = 4.2,
        loss_tangent: float = 0.020,
    ):
        """
        Parameters
        ----------
        name : str
            Descriptive material name.
        thickness_mm : float
            Specimen thickness in millimeters (e.g., 10 to 25 mm).
        relative_permittivity : float
            Real relative permittivity (dielectric constant eps_r, typical 3.5 - 5.5 for GFRP).
        loss_tangent : float
            Dielectric dissipation factor tan(delta) = eps'' / eps'.
        """
        self.name = name
        self.thickness_mm = max(2.0, float(thickness_mm))
        self.relative_permittivity = max(1.05, float(relative_permittivity))
        self.loss_tangent = max(0.0001, float(loss_tangent))

    @property
    def wave_velocity_mm_ns(self) -> float:
        """Propagation speed of microwave in the dielectric material (mm/ns)."""
        return C_SPEED_MM_NS / np.sqrt(self.relative_permittivity)

    def attenuation_constant_per_mm(self, frequency_ghz: float) -> float:
        """
        Microwave attenuation constant alpha in Np/mm:
            alpha ~= (omega / (2 * c)) * sqrt(eps_r) * tan(delta)
        where omega = 2 * pi * f.
        """
        omega = 2.0 * np.pi * frequency_ghz  # rad / ns
        alpha = (omega / (2.0 * C_SPEED_MM_NS)) * np.sqrt(self.relative_permittivity) * self.loss_tangent
        return float(alpha)

    @property
    def fresnel_reflection_air_to_mat(self) -> float:
        """Fresnel reflection coefficient at normal incidence from Air to Composite: (1 - sqrt(eps_r))/(1 + sqrt(eps_r))."""
        sqrt_eps = np.sqrt(self.relative_permittivity)
        return float((1.0 - sqrt_eps) / (1.0 + sqrt_eps))

    @property
    def fresnel_transmission_air_to_mat(self) -> float:
        """Fresnel amplitude transmission coefficient Air -> Composite: 2 / (1 + sqrt(eps_r))."""
        sqrt_eps = np.sqrt(self.relative_permittivity)
        return float(2.0 / (1.0 + sqrt_eps))

    @property
    def fresnel_transmission_mat_to_air(self) -> float:
        """Fresnel amplitude transmission coefficient Composite -> Air: 2 * sqrt(eps_r) / (1 + sqrt(eps_r))."""
        sqrt_eps = np.sqrt(self.relative_permittivity)
        return float(2.0 * sqrt_eps / (1.0 + sqrt_eps))


def generate_transmitted_pulse(
    time_ns: np.ndarray,
    frequency_ghz: float = 10.0,
    amplitude: float = 1.0,
    pulse_width_ns: float = 0.055,
    pulse_center_ns: float = 0.12,
) -> np.ndarray:
    """
    Generates a modulated microwave Gaussian pulse:
        s_tx(t) = A_0 * exp(-(t - t_0)^2 / (2 * sigma^2)) * cos(2*pi*f*(t - t_0))
    """
    envelope = amplitude * np.exp(-((time_ns - pulse_center_ns) ** 2) / (2.0 * (pulse_width_ns ** 2)))
    carrier = np.cos(2.0 * np.pi * frequency_ghz * (time_ns - pulse_center_ns))
    return envelope * carrier


def simulate_single_ascan(
    antenna: MicrowaveAntennaSystem,
    material: CompositeMaterial,
    scan_x_mm: float,
    defect_type: str = "No defect",
    defect_x_mm: float = 50.0,
    defect_z_mm: float = 6.0,
    defect_width_mm: float = 8.0,
    n_points: int = 600,
    time_window_ns: float = 1.6,
    rng: Optional[np.random.Generator] = None,
) -> Tuple[np.ndarray, np.ndarray, Dict[str, float]]:
    """
    Simulates a received microwave A-scan (reflected voltage waveform vs time) at a single scan position.

    Physics modeled:
    - Front surface reflection (air-composite interface).
    - Defect scattering (amplitude scaled by antenna beam coupling and defect geometry).
    - Back wall reflection (composite-air interface).
    - Defect shadowing (reduction of back-wall reflection below defect).
    - Material absorption / exponential attenuation.
    - Receiver noise.
    """
    rng = rng or np.random.default_rng()
    time_ns = np.linspace(0.0, time_window_ns, n_points)
    dt = time_ns[1] - time_ns[0]
    pulse_sigma_ns = 0.045
    f_ghz = antenna.frequency_ghz
    alpha = material.attenuation_constant_per_mm(f_ghz)
    v_mat = material.wave_velocity_mm_ns

    # Standoff travel time in air (two-way)
    # Average travel distance: sqrt(standoff^2 + (sep/2)^2)
    path_air_one_way = np.sqrt(antenna.standoff_distance_mm**2 + (antenna.antenna_separation_mm / 2.0)**2)
    tau_front = 2.0 * path_air_one_way / C_SPEED_MM_NS

    # Back-wall travel time: tau_front + 2 * thickness / v_mat
    tau_back = tau_front + 2.0 * material.thickness_mm / v_mat

    # Signal initialized to 0
    received_signal = np.zeros_like(time_ns)

    # 1. Front-wall surface reflection
    gamma_front = material.fresnel_reflection_air_to_mat
    w_surface, _, _ = antenna.calculate_antenna_coupling(scan_x_mm, scan_x_mm, 0.0)
    amp_front = antenna.signal_amplitude * gamma_front * w_surface
    received_signal += amp_front * np.exp(-((time_ns - tau_front) ** 2) / (2.0 * pulse_sigma_ns**2)) * np.cos(
        2.0 * np.pi * f_ghz * (time_ns - tau_front)
    )

    # 2. Defect reflection (if applicable)
    tau_defect = 0.0
    amp_defect = 0.0
    shadow_factor = 0.0

    if defect_type != "No defect":
        # Check antenna beam coupling to defect location
        w_defect, _, _ = antenna.calculate_antenna_coupling(scan_x_mm, defect_x_mm, defect_z_mm)
        # Spatial lateral extent factor (how close probe is to defect)
        dist_x = abs(scan_x_mm - defect_x_mm)
        spatial_coupling = np.exp(-(dist_x**2) / (2.0 * ((defect_width_mm / 1.8) ** 2)))

        two_way_weight = w_defect * spatial_coupling

        if two_way_weight > 0.01:
            tau_defect = tau_front + 2.0 * defect_z_mm / v_mat
            two_way_atten = np.exp(-2.0 * alpha * defect_z_mm)
            two_way_trans = material.fresnel_transmission_air_to_mat * material.fresnel_transmission_mat_to_air

            if defect_type == "Internal crack":
                # Delamination / crack: thin planar dielectric boundary
                # Sharp localized reflection, narrow spatial extent, mild backwall shadow
                gamma_crack = 0.72 * ((np.sqrt(material.relative_permittivity) - 1.0) / (np.sqrt(material.relative_permittivity) + 1.0))
                amp_defect = antenna.signal_amplitude * gamma_crack * two_way_trans * two_way_atten * two_way_weight
                # Single crisp pulse
                echo = amp_defect * np.exp(-((time_ns - tau_defect) ** 2) / (2.0 * (pulse_sigma_ns * 0.90) ** 2)) * np.cos(
                    2.0 * np.pi * f_ghz * (time_ns - tau_defect) + 0.3
                )
                received_signal += echo
                shadow_factor = 0.35 * two_way_weight

            elif defect_type == "Air void":
                # Air void: volumetric 3D cavity
                # Dual boundary echo (front and back of void) with phase inversion, wider spatial scattering & stronger shadow
                gamma_void = 0.58 * ((np.sqrt(material.relative_permittivity) - 1.0) / (np.sqrt(material.relative_permittivity) + 1.0))
                amp_defect = antenna.signal_amplitude * gamma_void * two_way_trans * two_way_atten * two_way_weight
                # First echo (front boundary: composite -> air)
                echo1 = amp_defect * np.exp(-((time_ns - tau_defect) ** 2) / (2.0 * (pulse_sigma_ns * 1.05) ** 2)) * np.cos(
                    2.0 * np.pi * f_ghz * (time_ns - tau_defect)
                )
                # Second trailing echo (back boundary: air -> composite) with phase reversal and delay
                dt_void = min(0.065, max(0.035, (defect_width_mm * 0.40) / C_SPEED_MM_NS))
                echo2 = -0.70 * amp_defect * np.exp(-((time_ns - (tau_defect + dt_void)) ** 2) / (2.0 * (pulse_sigma_ns * 1.10) ** 2)) * np.cos(
                    2.0 * np.pi * f_ghz * (time_ns - (tau_defect + dt_void))
                )
                received_signal += (echo1 + echo2)
                shadow_factor = 0.70 * two_way_weight

    # 3. Back-wall reflection
    w_back, _, _ = antenna.calculate_antenna_coupling(scan_x_mm, scan_x_mm, material.thickness_mm)
    gamma_back = (np.sqrt(material.relative_permittivity) - 1.0) / (np.sqrt(material.relative_permittivity) + 1.0)
    two_way_atten_back = np.exp(-2.0 * alpha * material.thickness_mm)
    two_way_trans_back = material.fresnel_transmission_air_to_mat * material.fresnel_transmission_mat_to_air

    # Apply defect shadowing drop
    back_attenuation = max(0.15, 1.0 - shadow_factor)
    amp_back = antenna.signal_amplitude * gamma_back * two_way_trans_back * two_way_atten_back * w_back * back_attenuation

    received_signal += amp_back * np.exp(-((time_ns - tau_back) ** 2) / (2.0 * pulse_sigma_ns**2)) * np.cos(
        2.0 * np.pi * f_ghz * (time_ns - tau_back)
    )

    # 4. Additive Gaussian white noise
    noise = rng.normal(0.0, antenna.noise_level, size=n_points)
    received_signal += noise

    info = {
        "tau_front_ns": float(tau_front),
        "tau_back_ns": float(tau_back),
        "tau_defect_ns": float(tau_defect) if defect_type != "No defect" else 0.0,
        "amp_front": float(amp_front),
        "amp_back": float(amp_back),
        "amp_defect": float(amp_defect),
        "shadow_factor": float(shadow_factor),
    }

    return time_ns, received_signal, info


def simulate_b_scan(
    antenna: MicrowaveAntennaSystem,
    material: CompositeMaterial,
    defect_type: str = "No defect",
    defect_x_mm: float = 50.0,
    defect_z_mm: float = 6.0,
    defect_width_mm: float = 8.0,
    scan_start_x_mm: float = 10.0,
    scan_end_x_mm: float = 90.0,
    n_scan_positions: int = 50,
    n_time_points: int = 400,
    time_window_ns: float = 1.6,
    rng: Optional[np.random.Generator] = None,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, Dict[str, Any]]:
    """
    Simulates an antenna raster/linear scan across the composite specimen (B-scan).

    Returns
    -------
    scan_positions_mm : np.ndarray
        Array of scan positions along x (1D).
    time_axis_ns : np.ndarray
        Time-of-flight axis in ns.
    b_scan_matrix : np.ndarray
        2D matrix of shape (n_scan_positions, n_time_points).
    scan_info : Dict
        Metadata including front/back times and geometry.
    """
    rng = rng or np.random.default_rng()
    scan_positions = np.linspace(scan_start_x_mm, scan_end_x_mm, n_scan_positions)
    time_axis = np.linspace(0.0, time_window_ns, n_time_points)

    b_scan = np.zeros((n_scan_positions, n_time_points), dtype=float)

    representative_info = {}
    for i, x in enumerate(scan_positions):
        _, sig, info = simulate_single_ascan(
            antenna=antenna,
            material=material,
            scan_x_mm=x,
            defect_type=defect_type,
            defect_x_mm=defect_x_mm,
            defect_z_mm=defect_z_mm,
            defect_width_mm=defect_width_mm,
            n_points=n_time_points,
            time_window_ns=time_window_ns,
            rng=rng,
        )
        b_scan[i, :] = sig
        if i == len(scan_positions) // 2:
            representative_info = info

    metadata = {
        "antenna": antenna,
        "material": material,
        "defect_type": defect_type,
        "defect_x_mm": defect_x_mm,
        "defect_z_mm": defect_z_mm,
        "defect_width_mm": defect_width_mm,
        "tau_front_ns": representative_info.get("tau_front_ns", 0.15),
        "tau_back_ns": representative_info.get("tau_back_ns", 0.65),
    }

    return scan_positions, time_axis, b_scan, metadata


def extract_features_from_bscan(
    scan_positions: np.ndarray,
    time_axis: np.ndarray,
    b_scan: np.ndarray,
    material_thickness_mm: float = 15.0,
    material_eps_r: float = 4.2,
    tau_front_approx: Optional[float] = None,
    tau_back_approx: Optional[float] = None,
) -> np.ndarray:
    """
    Extracts physically motivated statistical, temporal, and spatial features from a microwave B-scan.

    Features extracted (14 dimensions):
    0. defect_window_max_amp: Peak absolute signal in internal material window.
    1. defect_window_energy: Energy (sum of squares) in internal material window.
    2. defect_to_front_ratio: Ratio of internal peak to front surface peak.
    3. backwall_drop_ratio: Ratio of min backwall peak to baseline backwall peak.
    4. peak_lateral_x: Estimated lateral position x of max internal reflection.
    5. peak_time_ns: Time-of-flight of max internal echo.
    6. inferred_depth_mm: Estimated depth = 0.5 * (tau_echo - tau_front) * v_mat.
    7. spatial_fwhm_mm: Spatial half-width of the anomaly along scan axis x.
    8. waveform_std: Overall standard deviation of B-scan.
    9. waveform_skew: Skewness of internal window signals.
    10. waveform_kurtosis: Kurtosis (peakedness) of internal window signals.
    11. spectral_centroid_norm: Spectral centroid of the peak A-scan.
    12. max_spatial_gradient: Max rate of change along scanning positions.
    13. envelope_area_ratio: Area of Hilbert-like envelope in defect zone vs total.
    """
    n_scans, n_times = b_scan.shape
    v_mat = C_SPEED_MM_NS / np.sqrt(material_eps_r)

    # 1. Determine front and back wall time indices from average or envelope
    mean_ascan = np.mean(np.abs(b_scan), axis=0)

    if tau_front_approx is None:
        # Front wall is prominent peak in the first 35% of time window
        front_search_end = int(0.35 * n_times)
        front_idx = int(np.argmax(mean_ascan[:front_search_end]))
    else:
        front_idx = int(np.argmin(np.abs(time_axis - tau_front_approx)))

    if tau_back_approx is None:
        # Back wall is prominent peak after front wall + delay
        back_search_start = min(n_times - 1, front_idx + int(0.10 * n_times))
        back_search_end = min(n_times, back_search_start + int(0.50 * n_times))
        if back_search_end > back_search_start:
            back_idx = back_search_start + int(np.argmax(mean_ascan[back_search_start:back_search_end]))
        else:
            back_idx = min(n_times - 1, front_idx + 60)
    else:
        back_idx = int(np.argmin(np.abs(time_axis - tau_back_approx)))

    dt = time_axis[1] - time_axis[0]
    n_scans, n_times = b_scan.shape
    v_mat = C_SPEED_MM_NS / np.sqrt(material_eps_r)

    # 1. Background median subtraction (isolates anomaly from uniform front/back interfaces)
    bg_ascan = np.median(b_scan, axis=0)
    diff_scan = b_scan - bg_ascan

    if tau_front_approx is None:
        front_search_end = int(0.35 * n_times)
        front_idx = int(np.argmax(np.abs(bg_ascan[:front_search_end])))
    else:
        front_idx = int(np.argmin(np.abs(time_axis - tau_front_approx)))

    if tau_back_approx is None:
        back_search_start = min(n_times - 1, front_idx + int(0.10 * n_times))
        back_search_end = min(n_times, back_search_start + int(0.50 * n_times))
        if back_search_end > back_search_start:
            back_idx = back_search_start + int(np.argmax(np.abs(bg_ascan[back_search_start:back_search_end])))
        else:
            back_idx = min(n_times - 1, front_idx + 60)
    else:
        back_idx = int(np.argmin(np.abs(time_axis - tau_back_approx)))

    front_idx = max(5, front_idx)
    back_idx = max(front_idx + 15, min(n_times - 5, back_idx))

    # Defect window: strictly inside the material between front and back wall
    guard_front_pts = max(3, int(0.032 / dt))
    guard_back_pts = max(3, int(0.015 / dt))
    w_start = min(n_times - 3, front_idx + guard_front_pts)
    w_end = max(w_start + 2, back_idx - guard_back_pts)

    defect_diff_window = diff_scan[:, w_start:w_end]

    # Analytic Hilbert envelope across time to eliminate high-frequency carrier ripple artifacts
    env_diff_full = np.abs(hilbert(diff_scan, axis=1))
    defect_env_window = env_diff_full[:, w_start:w_end]

    # Reference front-wall reflection amplitude
    front_amp = float(np.max(np.abs(b_scan[:, max(0, front_idx - 10) : front_idx + 10])))
    norm_factor = max(1e-4, front_amp)

    # Feature 0 & 1: Envelope Peak Amplitude and Normalized Defect Energy
    max_amp = float(np.max(defect_env_window))
    energy = float(np.sum(defect_diff_window**2) / (defect_diff_window.size + 1e-6))

    # Feature 2: Defect to frontwall ratio (contrast relative to front reflection)
    defect_to_front_ratio = float(max_amp / norm_factor)

    # Feature 3: Backwall drop ratio (spatially smoothed with edge padding to eliminate boundary artifacts)
    backwall_profile = np.max(np.abs(b_scan[:, max(0, back_idx - 10) : min(n_times, back_idx + 10)]), axis=1)
    if len(backwall_profile) >= 3:
        pad_b = np.pad(backwall_profile, 1, mode="edge")
        bw_smooth = np.convolve(pad_b, np.array([0.2, 0.6, 0.2]), mode="valid")
    else:
        bw_smooth = backwall_profile

    baseline_backwall = float(np.percentile(bw_smooth, 85))
    min_backwall = float(np.min(bw_smooth))
    backwall_drop = float(1.0 - (min_backwall / (baseline_backwall + 1e-6)))
    backwall_drop = float(np.clip(backwall_drop, 0.0, 1.0))

    # Position along scan where backwall shadow is maximum
    bw_deficit = np.maximum(0.0, baseline_backwall - bw_smooth)
    shadow_idx = int(np.argmax(bw_deficit))
    shadow_peak_lateral_x = float(scan_positions[shadow_idx])

    # Feature 4: Peak anomaly lateral position from edge-padded smoothed envelope profile
    spatial_prof_raw = np.max(defect_env_window, axis=1)
    if len(spatial_prof_raw) >= 3:
        pad_s = np.pad(spatial_prof_raw, 1, mode="edge")
        spatial_prof_smooth = np.convolve(pad_s, np.array([0.2, 0.6, 0.2]), mode="valid")
    else:
        spatial_prof_smooth = spatial_prof_raw

    scan_idx_peak = int(np.argmax(spatial_prof_smooth))
    peak_lateral_x = float(scan_positions[scan_idx_peak])

    # Feature 5 & 6: Temporal peak in Hilbert envelope and inferred depth (immune to carrier cycle hopping)
    ascan_env = defect_env_window[scan_idx_peak, :]
    time_idx_peak = int(np.argmax(ascan_env))
    peak_time_ns = float(time_axis[w_start + time_idx_peak])

    tau_front_time = float(time_axis[front_idx])
    delta_t = max(0.0, peak_time_ns - tau_front_time)
    inferred_depth_mm = float(np.clip(0.5 * delta_t * v_mat, 0.0, material_thickness_mm))

    # Feature 7: Boundary-aware spatial FWHM around anomaly peak (reconstructs truncated wings at scan edges)
    pk_val = spatial_prof_smooth[scan_idx_peak]
    noise_floor = float(np.percentile(spatial_prof_smooth, 30))
    half_val = noise_floor + 0.5 * max(1e-4, pk_val - noise_floor)
    l_idx = scan_idx_peak
    while l_idx > 0 and spatial_prof_smooth[l_idx] >= half_val:
        l_idx -= 1
    r_idx = scan_idx_peak
    while r_idx < len(spatial_prof_smooth) - 1 and spatial_prof_smooth[r_idx] >= half_val:
        r_idx += 1

    left_truncated = (l_idx == 0 and spatial_prof_smooth[0] >= half_val)
    right_truncated = (r_idx == len(spatial_prof_smooth) - 1 and spatial_prof_smooth[-1] >= half_val)

    if left_truncated and not right_truncated:
        spatial_fwhm_mm = 2.0 * float(scan_positions[r_idx] - scan_positions[scan_idx_peak])
    elif right_truncated and not left_truncated:
        spatial_fwhm_mm = 2.0 * float(scan_positions[scan_idx_peak] - scan_positions[l_idx])
    else:
        spatial_fwhm_mm = float(scan_positions[r_idx] - scan_positions[l_idx])
    spatial_fwhm_mm = float(np.clip(spatial_fwhm_mm, 2.0, 35.0))

    # Feature 8: Standard deviation
    waveform_std = float(np.std(defect_diff_window))

    # Feature 9 & 10: Skewness and Kurtosis of defect window
    diffs = defect_diff_window.flatten() - np.mean(defect_diff_window)
    m2 = np.mean(diffs**2) + 1e-9
    m3 = np.mean(diffs**3)
    m4 = np.mean(diffs**4)
    skew = float(m3 / (m2**1.5))
    kurt = float(m4 / (m2**2.0) - 3.0)

    # Feature 11: Spectral Centroid of peak difference A-scan in physical GHz
    peak_ascan = diff_scan[scan_idx_peak, :]
    fft_mag = np.abs(np.fft.rfft(peak_ascan))
    freqs = np.fft.rfftfreq(len(peak_ascan), d=dt)
    spectral_centroid = float(np.sum(freqs * fft_mag) / (np.sum(fft_mag) + 1e-6))

    # Feature 12: Max spatial gradient across scan axis
    spatial_grad = np.max(np.abs(np.diff(spatial_prof_smooth)))
    max_spatial_grad = float(spatial_grad)

    # Feature 13: Area ratio
    total_energy = float(np.sum(diff_scan**2) + 1e-6)
    area_ratio = float(np.sum(defect_diff_window**2) / total_energy)

    # Feature 14: Echo pulse spread (temporal FWHM of Hilbert envelope)
    gate_max = ascan_env[time_idx_peak] + 1e-6
    gate_half = 0.5 * gate_max
    tl_idx = time_idx_peak
    while tl_idx > 0 and ascan_env[tl_idx] >= gate_half:
        tl_idx -= 1
    tr_idx = time_idx_peak
    while tr_idx < len(ascan_env) - 1 and ascan_env[tr_idx] >= gate_half:
        tr_idx += 1
    pulse_spread_ns = float((tr_idx - tl_idx) * dt)

    # Feature 15: Trailing secondary echo ratio (volumetric void back-boundary reflection)
    trailing_offset = max(2, int(0.035 / dt))
    trailing_slice = ascan_env[time_idx_peak + trailing_offset :]
    if len(trailing_slice) > 3:
        sec_peak = float(np.max(trailing_slice))
        trailing_ratio = float(sec_peak / gate_max)
    else:
        trailing_ratio = 0.0

    # Feature 16: Contiguous shadow extent along scan axis
    sh_half = bw_deficit[shadow_idx] / 2.0
    sl_idx = shadow_idx
    while sl_idx > 0 and bw_deficit[sl_idx] >= sh_half:
        sl_idx -= 1
    sr_idx = shadow_idx
    while sr_idx < len(bw_deficit) - 1 and bw_deficit[sr_idx] >= sh_half:
        sr_idx += 1
    shadow_extent_mm = float(scan_positions[sr_idx] - scan_positions[sl_idx])

    features = np.array([
        max_amp,
        energy,
        defect_to_front_ratio,
        backwall_drop,
        peak_lateral_x,
        peak_time_ns,
        inferred_depth_mm,
        spatial_fwhm_mm,
        waveform_std,
        skew,
        kurt,
        spectral_centroid,
        max_spatial_grad,
        area_ratio,
        pulse_spread_ns,
        trailing_ratio,
        shadow_extent_mm,
        shadow_peak_lateral_x,
    ], dtype=float)

    return features


FEATURE_NAMES = [
    "defect_window_max_amp",
    "defect_window_energy",
    "defect_to_front_ratio",
    "backwall_drop_ratio",
    "peak_lateral_x",
    "peak_time_ns",
    "inferred_depth_mm",
    "spatial_fwhm_mm",
    "waveform_std",
    "waveform_skew",
    "waveform_kurtosis",
    "spectral_centroid_norm",
    "max_spatial_gradient",
    "envelope_area_ratio",
    "pulse_spread_ns",
    "trailing_echo_ratio",
    "shadow_extent_mm",
    "shadow_peak_lateral_x",
]
