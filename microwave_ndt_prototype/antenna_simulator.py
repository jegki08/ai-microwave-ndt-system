"""
antenna_simulator.py
====================
Python-based simplified microwave antenna simulation for Non-Destructive Testing (NDT).

This module models:
- Microwave Transmitting antenna (Tx) and Receiving antenna (Rx).
- Analytical antenna radiation patterns (directional cosine pattern: cos^n(theta)).
- Beamwidth, directivity weighting, and spatial geometry relative to the composite sample.
- Antenna standoff distance and probe scanning coordinate.

NOTE: This is an analytical/geometric ray-approximation model for educational and
prototyping purposes. It is NOT a 3D full-wave Maxwell electromagnetic solver (CST/HFSS).
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Tuple, Dict, Any


class MicrowaveAntennaSystem:
    """
    Simulates a directional microwave antenna arrangement (monostatic or bistatic pitch-catch)
    operating in the microwave band (e.g., 2 GHz to 24 GHz, X-band typical: 8-12 GHz).
    """

    def __init__(
        self,
        frequency_ghz: float = 10.0,
        standoff_distance_mm: float = 20.0,
        antenna_separation_mm: float = 13.0,
        directivity_n: float = 4.0,
        signal_amplitude: float = 1.0,
        noise_level: float = 0.035,
    ):
        """
        Parameters
        ----------
        frequency_ghz : float
            Operating microwave frequency in GHz (e.g., 10.0 GHz for X-band NDT).
        standoff_distance_mm : float
            Antenna-to-material surface distance in millimeters (probe standoff).
        antenna_separation_mm : float
            Distance between Tx and Rx phase centers in mm (pitch-catch bistatic mode).
            Set to 0 for monostatic (co-located) antenna.
        directivity_n : float
            Cosine pattern exponent n in E(theta) = cos^n(theta). Higher n = narrower beam.
            n=4 gives ~47 deg Half-Power Beamwidth (HPBW).
        signal_amplitude : float
            Peak transmitted signal voltage / normalized amplitude A_0.
        noise_level : float
            Standard deviation of thermal / receiver Gaussian white noise.
        """
        self.frequency_ghz = max(1.0, float(frequency_ghz))
        self.frequency_hz = self.frequency_ghz * 1e9
        self.wavelength_mm = (3.0e11) / self.frequency_hz  # c = 300 mm/ns
        self.standoff_distance_mm = max(2.0, float(standoff_distance_mm))
        self.antenna_separation_mm = max(0.0, float(antenna_separation_mm))
        self.directivity_n = max(1.0, float(directivity_n))
        self.signal_amplitude = max(0.1, float(signal_amplitude))
        self.noise_level = max(0.001, float(noise_level))

    @property
    def hpbw_deg(self) -> float:
        """Half-Power Beamwidth (HPBW) in degrees for cos^n(theta) power pattern."""
        # For electric field E(theta) = cos^n(theta), Power P(theta) = cos^(2n)(theta).
        # Half power point: cos^(2n)(theta_half) = 0.5 => theta_half = arccos(0.5^(1/(2n)))
        theta_half_rad = np.arccos(0.5 ** (1.0 / (2.0 * self.directivity_n)))
        return float(np.degrees(2.0 * theta_half_rad))

    def radiation_pattern(self, theta_rad: np.ndarray) -> np.ndarray:
        """
        Analytical directional cosine electric-field radiation pattern:
            E(theta) = cos^n(theta) for |theta| <= pi/2, 0 otherwise.

        Parameters
        ----------
        theta_rad : float or np.ndarray
            Angle in radians off antenna boresight (normal = 0 rad).
        """
        theta = np.asarray(theta_rad)
        pattern = np.zeros_like(theta, dtype=float)
        valid = np.abs(theta) <= (np.pi / 2.0)
        pattern[valid] = np.cos(theta[valid]) ** self.directivity_n
        return pattern

    def calculate_antenna_coupling(
        self,
        scan_x_mm: float,
        target_x_mm: float,
        target_z_mm: float
    ) -> Tuple[float, float, float]:
        """
        Calculates two-way antenna directivity weighting and path distances
        from Tx to target point (x, z) and back to Rx.

        Coordinates:
        - Surface of composite is at z = 0.
        - Air region is z < 0.
        - Antenna Tx is at (scan_x - sep/2, -standoff).
        - Antenna Rx is at (scan_x + sep/2, -standoff).
        - Target is at (target_x, target_z). Target z >= 0 is inside composite or at surface.

        Returns
        -------
        coupling_weight : float
            Two-way pattern weight E_Tx(theta_Tx) * E_Rx(theta_Rx).
        r_tx_mm : float
            Direct distance from Tx to target in mm.
        r_rx_mm : float
            Direct distance from target to Rx in mm.
        """
        tx_x = scan_x_mm - (self.antenna_separation_mm / 2.0)
        rx_x = scan_x_mm + (self.antenna_separation_mm / 2.0)
        ant_z = -self.standoff_distance_mm

        dx_tx = target_x_mm - tx_x
        dz_tx = target_z_mm - ant_z  # positive downwards
        r_tx = float(np.sqrt(dx_tx**2 + dz_tx**2))
        theta_tx = float(np.arctan2(dx_tx, dz_tx))

        dx_rx = rx_x - target_x_mm
        dz_rx = target_z_mm - ant_z
        r_rx = float(np.sqrt(dx_rx**2 + dz_rx**2))
        theta_rx = float(np.arctan2(dx_rx, dz_rx))

        e_tx = float(self.radiation_pattern(np.array([theta_tx]))[0])
        e_rx = float(self.radiation_pattern(np.array([theta_rx]))[0])

        two_way_weight = e_tx * e_rx
        return two_way_weight, r_tx, r_rx

    def plot_radiation_pattern(self) -> plt.Figure:
        """Plots polar and Cartesian radiation patterns."""
        theta = np.linspace(-np.pi / 2, np.pi / 2, 200)
        field = self.radiation_pattern(theta)
        power_db = 20.0 * np.log10(np.clip(field, 1e-4, 1.0))

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 3.8))

        # Cartesian plot
        ax1.plot(np.degrees(theta), field, "b-", lw=2, label=f"n = {self.directivity_n:.1f}")
        ax1.axhline(0.707, color="r", ls="--", alpha=0.7, label=f"-3 dB (HPBW={self.hpbw_deg:.1f}°)")
        ax1.set_xlabel("Angle θ (degrees)")
        ax1.set_ylabel("Normalized Field |E(θ)|")
        ax1.set_title("Antenna Directional Radiation Pattern")
        ax1.grid(True, alpha=0.3)
        ax1.legend(loc="upper right", fontsize=8)

        # dB plot
        ax2.plot(np.degrees(theta), power_db, "g-", lw=2)
        ax2.axhline(-3.0, color="r", ls="--", alpha=0.7, label="Half Power (-3 dB)")
        ax2.set_xlabel("Angle θ (degrees)")
        ax2.set_ylabel("Power Pattern (dB)")
        ax2.set_title(f"Frequency = {self.frequency_ghz:.1f} GHz, HPBW = {self.hpbw_deg:.1f}°")
        ax2.set_ylim(-25, 1)
        ax2.grid(True, alpha=0.3)
        ax2.legend(loc="upper right", fontsize=8)

        plt.tight_layout()
        return fig

    def plot_inspection_setup(
        self,
        sample_length_mm: float = 100.0,
        sample_thickness_mm: float = 15.0,
        current_scan_x_mm: float = 50.0,
        defect_type: str = "No defect",
        defect_x_mm: float = 50.0,
        defect_z_mm: float = 6.0,
        defect_width_mm: float = 8.0,
    ) -> plt.Figure:
        """
        Draws a physical schematic of the microwave inspection setup:
        - Tx and Rx antennas with beam directivity cones.
        - Air standoff gap.
        - Composite material sample.
        - Defect (internal crack or air void) if present.
        - Current scanning position.
        """
        fig, ax = plt.subplots(figsize=(10, 4.2))

        # Coordinates:
        # z=0 is front surface of composite
        # z=sample_thickness_mm is back wall of composite
        # z=-standoff is antenna plane

        # 1. Composite Material Slab
        ax.fill_between(
            [0, sample_length_mm],
            0,
            sample_thickness_mm,
            color="#D0E1F9",
            alpha=0.85,
            label="Composite Sample (GFRP)",
            edgecolor="#2E4057",
            lw=1.5,
        )

        # 2. Defect representation
        if defect_type == "Internal crack":
            crack_x0 = defect_x_mm - defect_width_mm / 2.0
            crack_x1 = defect_x_mm + defect_width_mm / 2.0
            ax.plot(
                [crack_x0, crack_x1],
                [defect_z_mm, defect_z_mm],
                color="#C0392B",
                lw=3.5,
                solid_capstyle="round",
                label=f"Internal Crack (x={defect_x_mm:.1f} mm)",
            )
            ax.plot(defect_x_mm, defect_z_mm, "r*", markersize=10)
        elif defect_type == "Air void":
            void_radius = defect_width_mm / 2.0
            void_patch = plt.Circle(
                (defect_x_mm, defect_z_mm),
                void_radius,
                color="#E67E22",
                ec="#935116",
                lw=1.5,
                alpha=0.9,
                label=f"Air Void (x={defect_x_mm:.1f} mm, ⌀={defect_width_mm:.1f} mm)",
            )
            ax.add_patch(void_patch)

        # 3. Tx and Rx Antennas
        tx_x = current_scan_x_mm - (self.antenna_separation_mm / 2.0)
        rx_x = current_scan_x_mm + (self.antenna_separation_mm / 2.0)
        ant_z = -self.standoff_distance_mm

        # Draw Horn Antennas
        horn_w = 6.0
        horn_h = 8.0
        # Tx Horn
        ax.fill(
            [tx_x - horn_w, tx_x + horn_w, tx_x + horn_w / 2, tx_x - horn_w / 2],
            [ant_z, ant_z, ant_z - horn_h, ant_z - horn_h],
            color="#27AE60",
            ec="#1E8449",
            lw=1.5,
            label="Tx Microwave Antenna",
        )
        ax.text(tx_x, ant_z - horn_h - 2.0, "Tx", ha="center", va="bottom", fontweight="bold", color="#1E8449")

        # Rx Horn
        ax.fill(
            [rx_x - horn_w, rx_x + horn_w, rx_x + horn_w / 2, rx_x - horn_w / 2],
            [ant_z, ant_z, ant_z - horn_h, ant_z - horn_h],
            color="#8E44AD",
            ec="#5B2C6F",
            lw=1.5,
            label="Rx Microwave Antenna",
        )
        ax.text(rx_x, ant_z - horn_h - 2.0, "Rx", ha="center", va="bottom", fontweight="bold", color="#5B2C6F")

        # 4. Draw Radiation Cones (HPBW beam spread)
        theta_hpbw = np.radians(self.hpbw_deg / 2.0)
        beam_depth = self.standoff_distance_mm + sample_thickness_mm
        dx_beam = beam_depth * np.tan(theta_hpbw)

        # Tx Beam cone (Outgoing transmit signal)
        ax.fill(
            [tx_x, tx_x - dx_beam, tx_x + dx_beam],
            [ant_z, sample_thickness_mm, sample_thickness_mm],
            color="#2ECC71",
            alpha=0.15,
            edgecolor="#27AE60",
            linestyle="--",
            label=f"Tx Transmit Beam (HPBW={self.hpbw_deg:.0f}°)",
        )

        # Rx Beam cone (Incoming receive field of view)
        ax.fill(
            [rx_x, rx_x - dx_beam, rx_x + dx_beam],
            [ant_z, sample_thickness_mm, sample_thickness_mm],
            color="#8E44AD",
            alpha=0.12,
            edgecolor="#8E44AD",
            linestyle=":",
            label=f"Rx Receive Field of View",
        )

        # 5. Draw Active Wave Ray Paths (Tx -> Target -> Rx)
        # Check if defect is inside or near the current beam
        dist_to_defect = abs(current_scan_x_mm - defect_x_mm)
        if defect_type != "No defect" and dist_to_defect <= (dx_beam * 0.8):
            # Target is the defect
            tgt_x = defect_x_mm
            tgt_z = defect_z_mm
            # Incident wave ray (Tx -> Defect)
            ax.annotate(
                "",
                xy=(tgt_x, tgt_z),
                xytext=(tx_x, ant_z),
                arrowprops=dict(arrowstyle="->", color="#1E8449", lw=2.2, linestyle="-"),
            )
            # Reflected echo ray (Defect -> Rx)
            ax.annotate(
                "",
                xy=(rx_x, ant_z),
                xytext=(tgt_x, tgt_z),
                arrowprops=dict(arrowstyle="->", color="#C0392B", lw=2.2, linestyle="-"),
            )
            ax.text((tx_x + tgt_x) / 2.0 - 2, (ant_z + tgt_z) / 2.0, "Incident Wave", color="#1E8449", fontsize=7.5, fontweight="bold")
            ax.text((rx_x + tgt_x) / 2.0 + 2, (ant_z + tgt_z) / 2.0, "Reflected Echo", color="#C0392B", fontsize=7.5, fontweight="bold")
        else:
            # Ray reflecting off surface beneath probe
            mid_x = (tx_x + rx_x) / 2.0
            ax.annotate(
                "",
                xy=(mid_x, 0.0),
                xytext=(tx_x, ant_z),
                arrowprops=dict(arrowstyle="->", color="#27AE60", lw=1.5, linestyle="--"),
            )
            ax.annotate(
                "",
                xy=(rx_x, ant_z),
                xytext=(mid_x, 0.0),
                arrowprops=dict(arrowstyle="->", color="#8E44AD", lw=1.5, linestyle="--"),
            )
            ax.text((tx_x + mid_x) / 2.0 - 2, ant_z / 2.0, "Tx Ray", color="#27AE60", fontsize=7)
            ax.text((rx_x + mid_x) / 2.0 + 2, ant_z / 2.0, "Rx Echo", color="#8E44AD", fontsize=7)

        # Scanning indicator arrow
        ax.annotate(
            "",
            xy=(current_scan_x_mm + 12, ant_z - horn_h / 2),
            xytext=(current_scan_x_mm - 12, ant_z - horn_h / 2),
            arrowprops=dict(arrowstyle="->", color="#34495E", lw=2.0),
        )
        ax.text(current_scan_x_mm, ant_z - horn_h / 2 - 2, "Scan Axis (x)", ha="center", fontsize=8, color="#34495E")

        # Standoff dimension annotation
        ax.annotate(
            f"Standoff = {self.standoff_distance_mm:.1f} mm",
            xy=(2.0, -self.standoff_distance_mm / 2.0),
            fontsize=8,
            color="#2C3E50",
            fontstyle="italic",
        )

        # Formatting
        ax.set_xlim(-8, sample_length_mm + 8)
        ax.set_ylim(sample_thickness_mm + 4, ant_z - horn_h - 6)  # Inverted y: top is antenna, bottom is backwall
        ax.set_xlabel("Scan Coordinate x (mm)", fontweight="bold")
        ax.set_ylabel("Depth z (mm)\n[z=0 Front Surface]", fontweight="bold")
        ax.set_title(
            f"Antenna-Material Inspection Arrangement | f = {self.frequency_ghz:.1f} GHz | Scan Pos x = {current_scan_x_mm:.1f} mm",
            fontsize=11,
            fontweight="bold",
        )
        ax.grid(True, alpha=0.3, linestyle=":")
        ax.legend(loc="upper right", fontsize=8, framealpha=0.9)

        plt.tight_layout()
        return fig
