"""
create_presentation.py
======================
Generates a professional 12-slide widescreen PowerPoint presentation (.pptx)
for the AI-Based Microwave NDT System for Composite Materials.

Includes:
- Professional 16:9 widescreen layout with modern navy/cyan/slate theme.
- High-resolution reference images generated directly from the simulation models:
  1. Antenna Inspection Setup Schematic (Tx/Rx horns, beam directivity, rays, composite plate).
  2. Transmitted Pulse vs Received A-Scan Waveforms.
  3. 2D Microwave B-Scan Heatmap & 1D Scan Reflection Profile.
  4. AI Model Confusion Matrix & Feature Importances.
- Structured, easy-to-understand content covering background, physics, AI models,
  evaluation metrics, dashboard, and limitations.
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import joblib

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

from antenna_simulator import MicrowaveAntennaSystem
from signal_simulator import CompositeMaterial, generate_transmitted_pulse, simulate_b_scan, CLASSES

# Output directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, "presentation_images")
os.makedirs(IMG_DIR, exist_ok=True)

PPTX_PATH = os.path.join(BASE_DIR, "Microwave_NDT_AI_Presentation.pptx")
ROOT_PPTX_PATH = os.path.join(os.path.dirname(BASE_DIR), "Microwave_NDT_AI_Presentation.pptx")

# -------------------------------------------------------------
# STEP 1: Generate High-Resolution Reference Images
# -------------------------------------------------------------
print("Generating presentation reference images...")

antenna = MicrowaveAntennaSystem(frequency_ghz=10.0, standoff_distance_mm=20.0, antenna_separation_mm=12.0)
material = CompositeMaterial(name="GFRP Specimen", thickness_mm=15.0, relative_permittivity=4.2, loss_tangent=0.02)

# Image 1: Antenna Inspection Setup Schematic
fig_setup = antenna.plot_inspection_setup(
    sample_length_mm=100.0,
    sample_thickness_mm=15.0,
    current_scan_x_mm=52.0,
    defect_type="Internal crack",
    defect_x_mm=52.0,
    defect_z_mm=6.5,
    defect_width_mm=6.0,
)
img1_path = os.path.join(IMG_DIR, "ref_img1_setup.png")
fig_setup.savefig(img1_path, dpi=220, bbox_inches="tight")
plt.close(fig_setup)

# Image 2: Transmitted Pulse vs Received A-Scan Waveforms
t_tx = np.linspace(0.0, 0.4, 300)
s_tx = generate_transmitted_pulse(t_tx, frequency_ghz=10.0, amplitude=1.0)

sp, ta, bscan, meta = simulate_b_scan(
    antenna=antenna,
    material=material,
    defect_type="Internal crack",
    defect_x_mm=52.0,
    defect_z_mm=6.5,
    defect_width_mm=6.0,
    n_scan_positions=50,
    n_time_points=400,
)

fig_wave, (ax_tx, ax_rx) = plt.subplots(1, 2, figsize=(10, 4.0))

ax_tx.plot(t_tx, s_tx, color="#16A085", lw=2)
ax_tx.set_xlabel("Time (ns)", fontweight="bold")
ax_tx.set_ylabel("Amplitude (V)", fontweight="bold")
ax_tx.set_title("Transmitted Microwave Pulse s_tx(t)", fontsize=11, fontweight="bold")
ax_tx.grid(True, alpha=0.3)

closest_idx = int(np.argmin(np.abs(sp - 52.0)))
ascan_at_pos = bscan[closest_idx, :]
ax_rx.plot(ta, ascan_at_pos, color="#2980B9", lw=1.8, label="Rx Signal @ x=52 mm")
ax_rx.axvline(meta["tau_front_ns"], color="#E67E22", ls="--", lw=1.8, label="Front Surface (0.14 ns)")
ax_rx.axvline(meta["tau_front_ns"] + (2.0 * 6.5 / material.wave_velocity_mm_ns), color="#C0392B", ls=":", lw=2.2, label="Defect Echo (0.23 ns)")
ax_rx.axvline(meta["tau_back_ns"], color="#8E44AD", ls="--", lw=1.8, label="Back Wall (0.34 ns)")
ax_rx.set_xlabel("Time of Flight (ns)", fontweight="bold")
ax_rx.set_ylabel("Received Voltage (V)", fontweight="bold")
ax_rx.set_title("Received A-Scan s_rx(t) with 3 Echoes", fontsize=11, fontweight="bold")
ax_rx.grid(True, alpha=0.3)
ax_rx.legend(loc="upper right", fontsize=8)

plt.tight_layout()
img2_path = os.path.join(IMG_DIR, "ref_img2_waveforms.png")
fig_wave.savefig(img2_path, dpi=220, bbox_inches="tight")
plt.close(fig_wave)

# Image 3: 2D Microwave B-Scan Heatmap & 1D Scan Profile
fig_b, (ax_b, ax_p) = plt.subplots(1, 2, figsize=(10, 4.0), gridspec_kw={"width_ratios": [1.4, 1.0]})

im = ax_b.imshow(
    bscan.T,
    aspect="auto",
    extent=[sp[0], sp[-1], ta[-1], ta[0]],
    cmap="seismic",
    vmin=-0.8 * np.max(np.abs(bscan)),
    vmax=0.8 * np.max(np.abs(bscan)),
)
plt.colorbar(im, ax=ax_b, pad=0.03).set_label("Echo (V)", rotation=270, labelpad=12)
ax_b.axhline(meta["tau_front_ns"], color="orange", ls="--", lw=1.5)
ax_b.text(sp[0] + 1, meta["tau_front_ns"] - 0.03, "Front Surface", color="yellow", fontsize=8, fontweight="bold")
ax_b.axhline(meta["tau_back_ns"], color="magenta", ls="--", lw=1.5)
ax_b.text(sp[0] + 1, meta["tau_back_ns"] + 0.05, "Back Wall", color="cyan", fontsize=8, fontweight="bold")
ax_b.set_xlabel("Scan Position x (mm)", fontweight="bold")
ax_b.set_ylabel("Time of Flight (ns)", fontweight="bold")
ax_b.set_title("2D B-Scan Heatmap", fontsize=11, fontweight="bold")

# 1D profile
diff_scan = bscan - np.median(bscan, axis=0)
dt = ta[1] - ta[0]
f_idx = int(np.argmin(np.abs(ta - meta["tau_front_ns"])))
b_idx = int(np.argmin(np.abs(ta - meta["tau_back_ns"])))
internal_diff = np.abs(diff_scan[:, f_idx + int(0.025 / dt) : b_idx - int(0.015 / dt)])
prof = np.max(internal_diff, axis=1)

ax_p.plot(sp, prof, "r-o", lw=2, markersize=3.5)
ax_p.axvline(52.0, color="gray", ls=":", label="Defect Center (52 mm)")
ax_p.set_xlabel("Scan Position x (mm)", fontweight="bold")
ax_p.set_ylabel("Internal Gate Echo (V)", fontweight="bold")
ax_p.set_title("1D Defect Reflection Profile", fontsize=11, fontweight="bold")
ax_p.grid(True, alpha=0.3)
ax_p.legend(loc="upper right", fontsize=8)

plt.tight_layout()
img3_path = os.path.join(IMG_DIR, "ref_img3_bscan.png")
fig_b.savefig(img3_path, dpi=220, bbox_inches="tight")
plt.close(fig_b)

# Image 4: AI Model Confusion Matrix & Feature Importances
metrics_path = os.path.join(BASE_DIR, "models", "model_metrics.joblib")
if os.path.exists(metrics_path):
    m = joblib.load(metrics_path)
    cm = np.array(m["confusion_matrix"])
    feat_names = m["feature_names"]
    importances = m["feature_importances"]
    sorted_idx = np.argsort(importances)[::-1][:6]

    fig_m, (ax_cm, ax_fi) = plt.subplots(1, 2, figsize=(10, 4.0), gridspec_kw={"width_ratios": [1.0, 1.3]})

    cax = ax_cm.matshow(cm, cmap="Blues", alpha=0.85)
    plt.colorbar(cax, ax=ax_cm, fraction=0.046, pad=0.04)
    for i in range(len(m["classes"])):
        for j in range(len(m["classes"])):
            ax_cm.text(j, i, str(cm[i, j]), ha="center", va="center", color="black", fontsize=12, fontweight="bold")
    ax_cm.set_xticks(range(len(m["classes"])))
    ax_cm.set_yticks(range(len(m["classes"])))
    ax_cm.set_xticklabels(m["classes"], rotation=20, ha="left", fontsize=8.5)
    ax_cm.set_yticklabels(m["classes"], fontsize=8.5)
    ax_cm.set_xlabel("Predicted Condition", fontweight="bold")
    ax_cm.set_ylabel("True Condition", fontweight="bold")
    ax_cm.set_title("Held-Out Test Confusion Matrix", fontsize=11, fontweight="bold", pad=25)

    # Feature Importances
    top_n = [feat_names[i].replace("_", " ").title() for i in sorted_idx]
    top_v = [importances[i] * 100 for i in sorted_idx]
    ax_fi.barh(range(len(top_n)), top_v[::-1], color="#2980B9")
    ax_fi.set_yticks(range(len(top_n)))
    ax_fi.set_yticklabels(top_n[::-1], fontsize=8.5)
    ax_fi.set_xlabel("Relative Importance (%)", fontweight="bold")
    ax_fi.set_title("Top Informative Microwave Features", fontsize=11, fontweight="bold")
    ax_fi.grid(True, axis="x", alpha=0.3)

    plt.tight_layout()
    img4_path = os.path.join(IMG_DIR, "ref_img4_metrics.png")
    fig_m.savefig(img4_path, dpi=220, bbox_inches="tight")
    plt.close(fig_m)
else:
    img4_path = None

print("Reference images successfully generated.")

# -------------------------------------------------------------
# STEP 2: Build Professional PowerPoint Presentation
# -------------------------------------------------------------
print("Building PowerPoint Presentation (.pptx)...")

prs = Presentation()
# Set widescreen 16:9 (13.333 x 7.5 inches)
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

blank_layout = prs.slide_layouts[6]

# Theme Colors
NAVY = RGBColor(15, 32, 67)       # #0F2043 (Deep professional primary)
CYAN = RGBColor(14, 165, 233)     # #0EA5E9 (Modern tech accent)
DARK_GRAY = RGBColor(30, 41, 59)  # #1E293B (Body text)
LIGHT_BG = RGBColor(248, 250, 252)# #F8FAFC (Slide background)
CARD_BG = RGBColor(255, 255, 255) # White
ACCENT_GREEN = RGBColor(16, 185, 129)
ACCENT_RED = RGBColor(239, 68, 68)


def create_header(slide, title_text, category_text="AI-BASED MICROWAVE NDT SYSTEM"):
    """Creates a consistent, modern slide banner header."""
    # Top banner bar
    banner = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(1.15))
    banner.fill.solid()
    banner.fill.fore_color.rgb = NAVY
    banner.line.color.rgb = NAVY

    # Category Pill
    cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.12), Inches(10), Inches(0.3))
    tf_c = cat_box.text_frame
    tf_c.word_wrap = True
    p_c = tf_c.paragraphs[0]
    p_c.text = category_text.upper()
    p_c.font.size = Pt(9.5)
    p_c.font.bold = True
    p_c.font.color.rgb = CYAN

    # Main Title
    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.35), Inches(11.5), Inches(0.7))
    tf = title_box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title_text
    p.font.size = Pt(22)
    p.font.bold = True
    p.font.color.rgb = RGBColor(255, 255, 255)


def add_card(slide, left, top, width, height, bg_color=CARD_BG, border_color=RGBColor(226, 232, 240)):
    """Creates a styled card box."""
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color
    card.line.color.rgb = border_color
    card.line.width = Pt(1.5)
    return card


# =============================================================
# SLIDE 1: Title Slide (Dark Elegant Theme)
# =============================================================
slide1 = prs.slides.add_slide(blank_layout)
bg1 = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
bg1.fill.solid()
bg1.fill.fore_color.rgb = NAVY
bg1.line.color.rgb = NAVY

# Accent Cyan line
line1 = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.2), Inches(1.6), Inches(2.5), Inches(0.08))
line1.fill.solid()
line1.fill.fore_color.rgb = CYAN
line1.line.color.rgb = CYAN

title_box = slide1.shapes.add_textbox(Inches(1.2), Inches(1.8), Inches(11), Inches(2.2))
tf = title_box.text_frame
tf.word_wrap = True
p1 = tf.paragraphs[0]
p1.text = "AI-Based Microwave Non-Destructive Testing\nSystem for Composite Materials"
p1.font.size = Pt(36)
p1.font.bold = True
p1.font.color.rgb = RGBColor(255, 255, 255)

sub_box = slide1.shapes.add_textbox(Inches(1.2), Inches(4.2), Inches(10.5), Inches(1.2))
tf_sub = sub_box.text_frame
tf_sub.word_wrap = True
p2 = tf_sub.paragraphs[0]
p2.text = "Python Antenna Simulation, Dielectric Wave Propagation, B-Scan Imaging & Machine Learning Defect Detection"
p2.font.size = Pt(16)
p2.font.color.rgb = CYAN

tag_box = slide1.shapes.add_textbox(Inches(1.2), Inches(5.8), Inches(10), Inches(0.8))
tf_tag = tag_box.text_frame
p3 = tf_tag.paragraphs[0]
p3.text = "Project Architecture • Physical Principles • Evaluation Metrics • Interactive Dashboard"
p3.font.size = Pt(12)
p3.font.color.rgb = RGBColor(148, 163, 184)


# =============================================================
# SLIDE 2: Problem Statement & Motivation
# =============================================================
slide2 = prs.slides.add_slide(blank_layout)
create_header(slide2, "1. Motivation: Why Microwave NDT for Composites?")

# Card 1: The Material Shift
add_card(slide2, Inches(0.8), Inches(1.5), Inches(3.6), Inches(5.3))
c1 = slide2.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(3.2), Inches(4.9))
tf1 = c1.text_frame
tf1.word_wrap = True
tf1.paragraphs[0].text = "✈️ The Composite Revolution"
tf1.paragraphs[0].font.size = Pt(16)
tf1.paragraphs[0].font.bold = True
tf1.paragraphs[0].font.color.rgb = NAVY

bullets1 = [
    "Composite materials (e.g. GFRP, Glass-Fiber Reinforced Polymer) are replacing metals in aerospace, wind turbine blades, and automotive.",
    "Superior strength-to-weight ratio and corrosion resistance.",
    "Critical challenge: Internal flaws (cracks, delaminations, air voids) occur beneath the surface, invisible to visual inspection."
]
for b in bullets1:
    p = tf1.add_paragraph()
    p.text = "• " + b
    p.font.size = Pt(12)
    p.font.color.rgb = DARK_GRAY

# Card 2: Limitations of Conventional NDT
add_card(slide2, Inches(4.8), Inches(1.5), Inches(3.6), Inches(5.3))
c2 = slide2.shapes.add_textbox(Inches(5.0), Inches(1.7), Inches(3.2), Inches(4.9))
tf2 = c2.text_frame
tf2.word_wrap = True
tf2.paragraphs[0].text = "⚠️ Conventional NDT Limits"
tf2.paragraphs[0].font.size = Pt(16)
tf2.paragraphs[0].font.bold = True
tf2.paragraphs[0].font.color.rgb = NAVY

bullets2 = [
    "Ultrasonic Testing: Requires liquid couplants (water/gel) that can damage, contaminate, or swell composite laminates.",
    "Radiography (X-ray): Involves hazardous ionizing radiation, bulky lead shielding, and high operational costs.",
    "Eddy-Current Testing: Works only on electrical conductors; fails on non-conducting glass/resin composites."
]
for b in bullets2:
    p = tf2.add_paragraph()
    p.text = "• " + b
    p.font.size = Pt(12)
    p.font.color.rgb = DARK_GRAY

# Card 3: The Microwave Advantage
add_card(slide2, Inches(8.8), Inches(1.5), Inches(3.7), Inches(5.3), bg_color=RGBColor(240, 249, 255), border_color=CYAN)
c3 = slide2.shapes.add_textbox(Inches(9.0), Inches(1.7), Inches(3.3), Inches(4.9))
tf3 = c3.text_frame
tf3.word_wrap = True
tf3.paragraphs[0].text = "💡 The Microwave Solution"
tf3.paragraphs[0].font.size = Pt(16)
tf3.paragraphs[0].font.bold = True
tf3.paragraphs[0].font.color.rgb = CYAN

bullets3 = [
    "Non-contact & Couplant-free: Operates across an air standoff gap without touching the sample.",
    "Non-ionizing & Safe: Low-power gigahertz microwaves present zero health hazards.",
    "Deep Penetration: Readily passes through dielectric resin/glass matrices and reflects strongly off internal air boundaries.",
    "Real-time Inspection: Enables fast scanning and automated AI defect identification."
]
for b in bullets3:
    p = tf3.add_paragraph()
    p.text = "• " + b
    p.font.size = Pt(12)
    p.font.color.rgb = DARK_GRAY


# =============================================================
# SLIDE 3: System Workflow & Pipeline Architecture
# =============================================================
slide3 = prs.slides.add_slide(blank_layout)
create_header(slide3, "2. End-to-End System Workflow Architecture")

steps = [
    ("Step 1: Antenna Simulation", "Directivity pattern E(theta) = cos^n(theta), carrier freq 10 GHz, standoff air gap, Tx/Rx pitch-catch geometry."),
    ("Step 2: Wave Propagation", "Modulated pulse transmission, speed v = c/sqrt(eps_r), dielectric attenuation alpha, Fresnel boundary reflections."),
    ("Step 3: Raster B-Scan Imaging", "Antenna array sweeps across the sample from x=10 to 90 mm, recording single A-scans to assemble 2D B-scan."),
    ("Step 4: Physical Feature Extraction", "Background median subtraction, Time-of-Flight depth, contiguous spatial FWHM, kurtosis, spectral centroid."),
    ("Step 5: Machine Learning AI Inference", "StandardScaler + RandomForest pipeline classifies defect condition and predicts exact position x and depth z."),
]

for idx, (title, desc) in enumerate(steps):
    top_pos = Inches(1.5 + idx * 1.1)
    card = add_card(slide3, Inches(0.8), top_pos, Inches(11.7), Inches(0.95))
    
    # Number badge
    badge = slide3.shapes.add_shape(MSO_SHAPE.OVAL, Inches(1.1), top_pos + Inches(0.18), Inches(0.6), Inches(0.6))
    badge.fill.solid()
    badge.fill.fore_color.rgb = CYAN
    badge.line.color.rgb = CYAN
    p_b = badge.text_frame.paragraphs[0]
    p_b.text = str(idx + 1)
    p_b.font.size = Pt(14)
    p_b.font.bold = True
    p_b.alignment = PP_ALIGN.CENTER

    # Content
    tb = slide3.shapes.add_textbox(Inches(1.9), top_pos + Inches(0.12), Inches(10.3), Inches(0.7))
    tf = tb.text_frame
    tf.word_wrap = True
    p_t = tf.paragraphs[0]
    p_t.text = title
    p_t.font.size = Pt(13.5)
    p_t.font.bold = True
    p_t.font.color.rgb = NAVY
    
    p_d = tf.add_paragraph()
    p_d.text = desc
    p_d.font.size = Pt(11)
    p_d.font.color.rgb = DARK_GRAY


# =============================================================
# SLIDE 4: Antenna Simulation & Physical Setup (With Image 1)
# =============================================================
slide4 = prs.slides.add_slide(blank_layout)
create_header(slide4, "3. Antenna Simulation & Physical Inspection Setup")

# Left Column: Technical Explanations
add_card(slide4, Inches(0.8), Inches(1.5), Inches(5.4), Inches(5.4))
c_ant = slide4.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(5.0), Inches(5.0))
tf_ant = c_ant.text_frame
tf_ant.word_wrap = True
tf_ant.paragraphs[0].text = "Directional Horn Antenna Modeling"
tf_ant.paragraphs[0].font.size = Pt(15)
tf_ant.paragraphs[0].font.bold = True
tf_ant.paragraphs[0].font.color.rgb = NAVY

ant_bullets = [
    "Transmitting (Tx) & Receiving (Rx) Horns: Bistatic pitch-catch arrangement with separation (sep = 12 mm) and standoff gap (20 mm).",
    "Analytical Radiation Pattern: Directional cosine model E(theta) = cos^n(theta) for |theta| <= 90 deg.",
    "Half-Power Beamwidth (HPBW): For directivity factor n=4.0, HPBW = 47.0 deg, directing radiation downward into the specimen.",
    "Two-Way Coupling: Total pattern weight W = E(theta_Tx) * E(theta_Rx) naturally models beam spreading and spatial illumination.",
    "Active Wave Rays: Incident wave from Tx strikes target, and reflected wave bounces back up into Rx aperture."
]
for b in ant_bullets:
    p = tf_ant.add_paragraph()
    p.text = "• " + b
    p.font.size = Pt(11.5)
    p.font.color.rgb = DARK_GRAY

# Right Column: Embedded Reference Image 1
add_card(slide4, Inches(6.5), Inches(1.5), Inches(6.0), Inches(5.4))
slide4.shapes.add_picture(img1_path, Inches(6.6), Inches(1.9), width=Inches(5.8))
lbl1 = slide4.shapes.add_textbox(Inches(6.6), Inches(6.4), Inches(5.8), Inches(0.4))
lbl1.text_frame.paragraphs[0].text = "Fig 1: Antenna Inspection Setup Schematic with Beam Cones & Ray Tracing"
lbl1.text_frame.paragraphs[0].font.size = Pt(10)
lbl1.text_frame.paragraphs[0].font.italic = True
lbl1.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER


# =============================================================
# SLIDE 5: Waveform Physics — How Echoes Form (With Image 2)
# =============================================================
slide5 = prs.slides.add_slide(blank_layout)
create_header(slide5, "4. Waveform Physics: Transmitted Pulse vs. Received A-Scan")

# Left Column: Explanation
add_card(slide5, Inches(0.8), Inches(1.5), Inches(5.4), Inches(5.4))
c_w = slide5.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(5.0), Inches(5.0))
tf_w = c_w.text_frame
tf_w.word_wrap = True
tf_w.paragraphs[0].text = "Echo Formation & Time of Flight (ToF)"
tf_w.paragraphs[0].font.size = Pt(15)
tf_w.paragraphs[0].font.bold = True
tf_w.paragraphs[0].font.color.rgb = NAVY

w_bullets = [
    "Transmitted Pulse: Modulated Gaussian carrier pulse s_tx(t) = A_0 exp(-t^2/2sigma^2) cos(2pi f t) lasting only 0.1 nanoseconds.",
    "Speed in Composite: Dielectric matrix slows wave: v_m = c / sqrt(eps_r) = 146.4 mm/ns for GFRP (eps_r = 4.2).",
    "Spike 1 — Front Surface (0.14 ns): Initial bounce off the top face of the plate (Fresnel reflection Gamma_01 = -0.344).",
    "Spike 2 — Defect Echo (0.23 ns): Internal reflection from the crack/void buried at depth z = 6.5 mm.",
    "Spike 3 — Back Wall Echo (0.35 ns): Reflection off the bottom surface of the plate (15 mm thickness).",
    "Depth Formula: z = 0.5 * (tau_defect - tau_front) * v_m."
]
for b in w_bullets:
    p = tf_w.add_paragraph()
    p.text = "• " + b
    p.font.size = Pt(11)
    p.font.color.rgb = DARK_GRAY

# Right Column: Embedded Reference Image 2
add_card(slide5, Inches(6.5), Inches(1.5), Inches(6.0), Inches(5.4))
slide5.shapes.add_picture(img2_path, Inches(6.6), Inches(2.0), width=Inches(5.8))
lbl2 = slide5.shapes.add_textbox(Inches(6.6), Inches(6.4), Inches(5.8), Inches(0.4))
lbl2.text_frame.paragraphs[0].text = "Fig 2: Transmitted Microwave Pulse s_tx(t) & Received A-Scan with 3 Echoes"
lbl2.text_frame.paragraphs[0].font.size = Pt(10)
lbl2.text_frame.paragraphs[0].font.italic = True
lbl2.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER


# =============================================================
# SLIDE 6: 2D B-Scan Imaging & Scan Profile (With Image 3)
# =============================================================
slide6 = prs.slides.add_slide(blank_layout)
create_header(slide6, "5. 2D B-Scan Imaging & Anomaly Profiling")

# Left Column: Explanation
add_card(slide6, Inches(0.8), Inches(1.5), Inches(5.4), Inches(5.4))
c_b = slide6.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(5.0), Inches(5.0))
tf_b = c_b.text_frame
tf_b.word_wrap = True
tf_b.paragraphs[0].text = "Cross-Sectional Imaging & Localization"
tf_b.paragraphs[0].font.size = Pt(15)
tf_b.paragraphs[0].font.bold = True
tf_b.paragraphs[0].font.color.rgb = NAVY

b_bullets = [
    "A-Scan vs. B-Scan: An A-scan is a 1D trace at a single spot. Stacking A-scans across all probe positions produces the 2D B-scan.",
    "2D B-Scan Heatmap: Horizontal axis = Scan coordinate x (10 to 90 mm); Vertical axis = Time-of-Flight / Depth.",
    "Top/Bottom Stripes: Top orange line represents the front surface; bottom magenta line represents the back wall.",
    "Internal Defect Anomaly: Clearly visible as a localized disturbance between the surface and back-wall stripes around x = 52 mm.",
    "1D Reflection Profile: Peaks sharply directly over the defect center, providing instant lateral position localization."
]
for b in b_bullets:
    p = tf_b.add_paragraph()
    p.text = "• " + b
    p.font.size = Pt(11)
    p.font.color.rgb = DARK_GRAY

# Right Column: Embedded Reference Image 3
add_card(slide6, Inches(6.5), Inches(1.5), Inches(6.0), Inches(5.4))
slide6.shapes.add_picture(img3_path, Inches(6.6), Inches(2.0), width=Inches(5.8))
lbl3 = slide6.shapes.add_textbox(Inches(6.6), Inches(6.4), Inches(5.8), Inches(0.4))
lbl3.text_frame.paragraphs[0].text = "Fig 3: 2D Microwave B-Scan Heatmap & 1D Reflection Peak Profile"
lbl3.text_frame.paragraphs[0].font.size = Pt(10)
lbl3.text_frame.paragraphs[0].font.italic = True
lbl3.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER


# =============================================================
# SLIDE 7: Defect Types & Physical Signatures
# =============================================================
slide7 = prs.slides.add_slide(blank_layout)
create_header(slide7, "6. Simulated Defect Conditions & Signatures")

def_cards = [
    ("1. No Defect (Pristine)", "Pristine composite matrix", [
        "Homogeneous composite plate without internal flaws.",
        "Generates clean front-wall reflection and strong, unattenuated back-wall echo.",
        "Zero intermediate reflection in the defect gate window.",
        "Baseline reference for normal structural integrity."
    ], RGBColor(240, 253, 244), ACCENT_GREEN),
    ("2. Internal Crack (Delamination)", "Thin planar air gap (< 0.5 mm)", [
        "Planar separation between composite lamina layers.",
        "Sharp dielectric impedance boundary creates a crisp single-pulse reflection.",
        "High-frequency phase shift and localized spatial width (FWHM ~ 10 mm).",
        "Moderate back-wall echo shadowing beneath the crack."
    ], RGBColor(254, 242, 242), ACCENT_RED),
    ("3. Air Void (Porosity Cluster)", "Volumetric 3D cavity (3 to 14 mm)", [
        "Trapped air pocket or porosity cluster formed during curing.",
        "Dual boundary echoes: top interface (composite->air) + bottom interface (air->composite with phase reversal).",
        "Broadened pulse duration and wider spatial beam scattering (FWHM ~ 21 mm).",
        "Strong back-wall echo drop (severe shadowing)."
    ], RGBColor(255, 247, 237), RGBColor(249, 115, 22)),
]

for idx, (title, sub, bullets, bg, border) in enumerate(def_cards):
    left_p = Inches(0.8 + idx * 4.0)
    add_card(slide7, left_p, Inches(1.5), Inches(3.7), Inches(5.3), bg_color=bg, border_color=border)
    tb = slide7.shapes.add_textbox(left_p + Inches(0.2), Inches(1.7), Inches(3.3), Inches(4.9))
    tf = tb.text_frame
    tf.word_wrap = True
    
    p_t = tf.paragraphs[0]
    p_t.text = title
    p_t.font.size = Pt(14)
    p_t.font.bold = True
    p_t.font.color.rgb = NAVY
    
    p_s = tf.add_paragraph()
    p_s.text = sub
    p_s.font.size = Pt(11)
    p_s.font.italic = True
    p_s.font.color.rgb = DARK_GRAY
    
    for b in bullets:
        p = tf.add_paragraph()
        p.text = "• " + b
        p.font.size = Pt(10.5)
        p.font.color.rgb = DARK_GRAY


# =============================================================
# SLIDE 8: AI Model Training & Feature Extraction
# =============================================================
slide8 = prs.slides.add_slide(blank_layout)
create_header(slide8, "7. AI Machine Learning Pipeline & Training")

# Left Column: Dataset Details
add_card(slide8, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.4))
c_ds = slide8.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(5.2), Inches(5.0))
tf_ds = c_ds.text_frame
tf_ds.word_wrap = True
tf_ds.paragraphs[0].text = "Dataset Generation & Leakage Prevention"
tf_ds.paragraphs[0].font.size = Pt(15)
tf_ds.paragraphs[0].font.bold = True
tf_ds.paragraphs[0].font.color.rgb = NAVY

ds_bullets = [
    "1,050 Total Scans: Perfectly balanced dataset of 350 pristine plates, 350 cracked plates, and 350 void plates.",
    "Comprehensive Physical Variation: Frequencies (6 to 20 GHz), Standoffs (10 to 38 mm), Separations (0 to 25 mm), Thicknesses (10 to 22 mm), Permittivities (3.5 to 5.2), and Noise (0.015 to 0.055).",
    "Zero Data Leakage Split: Partitioned strictly into 70% Train (734 scans), 15% Validation (158 scans), and 15% Held-Out Test (158 scans).",
    "Stratified Splitting: Ensures equal representation across all 3 classes without overlapping random seeds."
]
for b in ds_bullets:
    p = tf_ds.add_paragraph()
    p.text = "• " + b
    p.font.size = Pt(11)
    p.font.color.rgb = DARK_GRAY

# Right Column: ML Algorithms & 18 Features
add_card(slide8, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.4))
c_ml = slide8.shapes.add_textbox(Inches(7.0), Inches(1.7), Inches(5.3), Inches(5.0))
tf_ml = c_ml.text_frame
tf_ml.word_wrap = True
tf_ml.paragraphs[0].text = "Algorithms & 18 Physical Features"
tf_ml.paragraphs[0].font.size = Pt(15)
tf_ml.paragraphs[0].font.bold = True
tf_ml.paragraphs[0].font.color.rgb = NAVY

ml_bullets = [
    "Classification Pipeline: StandardScaler + RandomForestClassifier (200 trees, balanced weights, max depth 12).",
    "Position & Depth Regressors: StandardScaler + RandomForestRegressor (150 trees) predicting continuous coordinates x and z.",
    "Domain-Specific Features (18 Dimensions):",
    "  - Defect gate peak amplitude & energy ratio",
    "  - Back-wall drop ratio & contiguous shadow width",
    "  - Time-of-Flight inferred depth & spatial peak x",
    "  - Contiguous spatial FWHM anomaly width",
    "  - Waveform kurtosis, skewness & physical spectral centroid",
    "  - Pulse spread duration & trailing echo ratio"
]
for b in ml_bullets:
    p = tf_ml.add_paragraph()
    p.text = b if b.startswith("  -") else "• " + b
    p.font.size = Pt(10.5)
    p.font.color.rgb = DARK_GRAY


# =============================================================
# SLIDE 9: Actual Evaluation Metrics & Results (With Image 4)
# =============================================================
slide9 = prs.slides.add_slide(blank_layout)
create_header(slide9, "8. Actual Evaluation Metrics on Held-Out Test Set")

# Left Column: Metric Cards
add_card(slide9, Inches(0.8), Inches(1.5), Inches(5.4), Inches(5.4))

# Mini Metric Cards inside
metrics_data = [
    ("Overall Test Accuracy", "92.41%", "Evaluated on 158 unseen scans"),
    ("Position x MAE", "0.76 mm", "Sub-millimeter lateral precision"),
    ("Depth z MAE", "0.69 mm", "Sub-millimeter vertical precision"),
    ("No-Defect Precision", "100.0%", "Zero false alarms on pristine plates"),
]
for m_idx, (m_title, m_val, m_sub) in enumerate(metrics_data):
    m_top = Inches(1.7 + m_idx * 1.25)
    add_card(slide9, Inches(1.0), m_top, Inches(5.0), Inches(1.05), bg_color=RGBColor(241, 245, 249))
    tb_m = slide9.shapes.add_textbox(Inches(1.2), m_top + Inches(0.08), Inches(4.6), Inches(0.9))
    tf_m = tb_m.text_frame
    tf_m.word_wrap = True
    p1 = tf_m.paragraphs[0]
    p1.text = m_title
    p1.font.size = Pt(11)
    p1.font.color.rgb = DARK_GRAY
    p2 = tf_m.add_paragraph()
    p2.text = m_val
    p2.font.size = Pt(18)
    p2.font.bold = True
    p2.font.color.rgb = CYAN if "Accuracy" in m_title or "100" in m_val else NAVY
    p3 = tf_m.add_paragraph()
    p3.text = m_sub
    p3.font.size = Pt(9.5)
    p3.font.color.rgb = RGBColor(100, 116, 139)

# Right Column: Embedded Image 4
if img4_path:
    add_card(slide9, Inches(6.5), Inches(1.5), Inches(6.0), Inches(5.4))
    slide9.shapes.add_picture(img4_path, Inches(6.6), Inches(2.0), width=Inches(5.8))
    lbl4 = slide9.shapes.add_textbox(Inches(6.6), Inches(6.4), Inches(5.8), Inches(0.4))
    lbl4.text_frame.paragraphs[0].text = "Fig 4: Held-Out Confusion Matrix & Most Informative Microwave Features"
    lbl4.text_frame.paragraphs[0].font.size = Pt(10)
    lbl4.text_frame.paragraphs[0].font.italic = True
    lbl4.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER


# =============================================================
# SLIDE 10: Interactive Streamlit Dashboard
# =============================================================
slide10 = prs.slides.add_slide(blank_layout)
create_header(slide10, "9. Interactive Streamlit Web Dashboard")

dash_items = [
    ("A. Antenna Controls", "Interactive sliders for Operating Frequency (5-20 GHz), Standoff Distance (5-40 mm), Probe Pitch-Catch Separation (0-25 mm), and Noise Level."),
    ("B. Material & Defect Ground Truth", "Select material presets (GFRP, Quartz), thickness (mm), and hidden ground truth flaw (used strictly by simulator; AI remains blind)."),
    ("C. Repeatability Lock Feature", "Lock Noise Seed checkbox (checked by default) guarantees 100% stable, identical AI prediction between repeated clicks."),
    ("D. Live Inspection Waveforms", "Plots Tx outgoing pulse s_tx(t) and Rx received A-scan s_rx(t) with annotated front-surface, defect, and back-wall time markers."),
    ("E. 2D B-Scan & 1D Scan Profiler", "Real-time 2D color heatmap of the entire plate thickness alongside the 1D reflection peak profile."),
    ("F. Blind AI Defect Diagnostics", "Automatic classification card, confidence meter, predicted position x, predicted depth z, class probabilities, and diagnostic metrics table.")
]

for idx, (title, desc) in enumerate(dash_items):
    col = idx % 2
    row = idx // 2
    l_pos = Inches(0.8 + col * 5.9)
    t_pos = Inches(1.5 + row * 1.8)
    
    add_card(slide10, l_pos, t_pos, Inches(5.7), Inches(1.6))
    tb = slide10.shapes.add_textbox(l_pos + Inches(0.2), t_pos + Inches(0.15), Inches(5.3), Inches(1.3))
    tf = tb.text_frame
    tf.word_wrap = True
    
    p_t = tf.paragraphs[0]
    p_t.text = title
    p_t.font.size = Pt(13)
    p_t.font.bold = True
    p_t.font.color.rgb = NAVY
    
    p_d = tf.add_paragraph()
    p_d.text = desc
    p_d.font.size = Pt(10.5)
    p_d.font.color.rgb = DARK_GRAY


# =============================================================
# SLIDE 11: Scientific Assumptions & Limitations
# =============================================================
slide11 = prs.slides.add_slide(blank_layout)
create_header(slide11, "10. Scientific Assumptions & Limitations")

# Card 1: Analytical Simulation vs FEM Solvers
add_card(slide11, Inches(0.8), Inches(1.5), Inches(3.6), Inches(5.3))
c_l1 = slide11.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(3.2), Inches(4.9))
tf_l1 = c_l1.text_frame
tf_l1.word_wrap = True
tf_l1.paragraphs[0].text = "🔬 Ray-Tracing vs. 3D FEM"
tf_l1.paragraphs[0].font.size = Pt(15)
tf_l1.paragraphs[0].font.bold = True
tf_l1.paragraphs[0].font.color.rgb = NAVY

bullets_l1 = [
    "Analytical Model: Employs directional cosine beam weighting, geometric ray tracing, and Fresnel boundary equations.",
    "Fast Real-Time Execution: Allows sub-second B-scan synthesis and interactive UI response.",
    "Clear Boundary: This is NOT a 3D full-wave finite-element Maxwell solver (like CST Studio or Ansys HFSS) and does not claim full-wave field accuracy."
]
for b in bullets_l1:
    p = tf_l1.add_paragraph()
    p.text = "• " + b
    p.font.size = Pt(11)
    p.font.color.rgb = DARK_GRAY

# Card 2: Synthetic Data Disclaimer
add_card(slide11, Inches(4.8), Inches(1.5), Inches(3.6), Inches(5.3))
c_l2 = slide11.shapes.add_textbox(Inches(5.0), Inches(1.7), Inches(3.2), Inches(4.9))
tf_l2 = c_l2.text_frame
tf_l2.word_wrap = True
tf_l2.paragraphs[0].text = "📊 Synthetic Data Scope"
tf_l2.paragraphs[0].font.size = Pt(15)
tf_l2.paragraphs[0].font.bold = True
tf_l2.paragraphs[0].font.color.rgb = NAVY

bullets_l2 = [
    "Mathematical Dataset: AI models were trained and tested exclusively on synthetically simulated microwave responses.",
    "Physical Disparity: Real-world composite structures involve fiber weave scatter, laminate roughness, probe misalignment, and thermal drift.",
    "Academic Honesty: High synthetic test accuracy (92.4%) establishes proof-of-concept pipeline validity, NOT field qualification."
]
for b in bullets_l2:
    p = tf_l2.add_paragraph()
    p.text = "• " + b
    p.font.size = Pt(11)
    p.font.color.rgb = DARK_GRAY

# Card 3: Path to Physical Deployment
add_card(slide11, Inches(8.8), Inches(1.5), Inches(3.7), Inches(5.3), bg_color=RGBColor(240, 249, 255), border_color=CYAN)
c_l3 = slide11.shapes.add_textbox(Inches(9.0), Inches(1.7), Inches(3.3), Inches(4.9))
tf_l3 = c_l3.text_frame
tf_l3.word_wrap = True
tf_l3.paragraphs[0].text = "🚀 Future Physical Validation"
tf_l3.paragraphs[0].font.size = Pt(15)
tf_l3.paragraphs[0].font.bold = True
tf_l3.paragraphs[0].font.color.rgb = CYAN

bullets_l3 = [
    "Vector Network Analyzer (VNA): Measuring actual S-parameters (S_11 reflection and S_21 transmission).",
    "Calibrated Reference Standards: Manufactured GFRP specimens with known artificial Teflon delaminations and drilled air voids.",
    "Transfer Learning: Fine-tuning the synthetic-trained Random Forest pipeline with physical laboratory scan measurements."
]
for b in bullets_l3:
    p = tf_l3.add_paragraph()
    p.text = "• " + b
    p.font.size = Pt(11)
    p.font.color.rgb = DARK_GRAY


# =============================================================
# SLIDE 12: Conclusion & Summary
# =============================================================
slide12 = prs.slides.add_slide(blank_layout)
bg12 = slide12.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
bg12.fill.solid()
bg12.fill.fore_color.rgb = NAVY
bg12.line.color.rgb = NAVY

line12 = slide12.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.2), Inches(1.2), Inches(2.5), Inches(0.08))
line12.fill.solid()
line12.fill.fore_color.rgb = CYAN
line12.line.color.rgb = CYAN

t_c = slide12.shapes.add_textbox(Inches(1.2), Inches(1.5), Inches(11), Inches(1.0))
p_c1 = t_c.text_frame.paragraphs[0]
p_c1.text = "Summary of Accomplishments"
p_c1.font.size = Pt(30)
p_c1.font.bold = True
p_c1.font.color.rgb = RGBColor(255, 255, 255)

card_sum = slide12.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.2), Inches(2.6), Inches(10.9), Inches(4.0))
card_sum.fill.solid()
card_sum.fill.fore_color.rgb = RGBColor(25, 45, 85)
card_sum.line.color.rgb = CYAN

tb_sum = slide12.shapes.add_textbox(Inches(1.5), Inches(2.8), Inches(10.3), Inches(3.6))
tf_s = tb_sum.text_frame
tf_s.word_wrap = True

achievements = [
    "Complete End-to-End NDT Pipeline: Successfully integrated directional microwave antenna modeling, wave propagation physics, 2D B-scan imaging, and AI defect detection.",
    "Accurate Defect Classification (92.4%): Distinguishes pristine composites, thin delamination cracks, and volumetric air voids with high statistical confidence.",
    "Sub-Millimeter Defect Localization: Predicts lateral flaw position x within 0.76 mm and buried flaw depth z within 0.69 mm.",
    "Interactive Real-Time Dashboard: Professional Streamlit UI with live waveform visualizers, B-scan heatmaps, and ground-truth comparison cards.",
    "Academic & Scientific Integrity: Transparently documents physical ray-tracing assumptions, parameter sensitivities, and hardware validation requirements."
]
for a in achievements:
    p = tf_s.add_paragraph()
    p.text = "✓  " + a
    p.font.size = Pt(13)
    p.font.color.rgb = RGBColor(241, 245, 249)

# Save presentation
prs.save(PPTX_PATH)
prs.save(ROOT_PPTX_PATH)

print(f"Presentation successfully created and saved to:")
print(f"  1. {PPTX_PATH}")
print(f"  2. {ROOT_PPTX_PATH}")
