import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os

dest_dir = r"c:\Users\LENOVO\Downloads\microwave_ndt_2day_prototype\microwave_ndt_prototype\presentation_images"
os.makedirs(dest_dir, exist_ok=True)

# 1. Dataflow Diagram
fig, ax = plt.subplots(figsize=(12, 6.5), dpi=300)
ax.set_facecolor('#0d1117')
fig.patch.set_facecolor('#0d1117')

boxes = [
    ("Operator Scan Configuration\n• Frequency (2.4 - 10 GHz)\n• Material & Thickness\n• Defect Type & Coords", 0.08, 0.72, '#1f6feb', '#58a6ff'),
    ("Antenna & Signal Engine\n• Pulse Generator (Gaussian RF)\n• Beam Pattern & Attenuation\n• Multi-layer Dielectric Ray Tracing", 0.38, 0.72, '#238636', '#3fb950'),
    ("Composite Specimen Interaction\n• Air / Surface Reflection ($R_1$)\n• Flaw Impedance Mismatch ($R_2$)\n• Bottom Wall Boundary ($R_3$)", 0.68, 0.72, '#8957e5', '#bc8cff'),
    ("A-Scan & B-Scan Assembly\n• Time-Domain A-Scan per position\n• Raster Scanning (0 - 100 mm)\n• 2D Matrix Concatenation", 0.68, 0.22, '#d29922', '#f0883e'),
    ("Physics Feature Extractor\n• Median Background Subtraction\n• Peak Reflection Amplitude\n• Time-of-Flight (ToF) & Delay\n• Spatial FWHM Flaw Width", 0.38, 0.22, '#da3633', '#f85149'),
    ("Machine Learning & UI Output\n• Random Forest Classifier (92.4%)\n• Flaw Depth & Position Regressors\n• Interactive Streamlit Visualizer", 0.08, 0.22, '#1f6feb', '#58a6ff'),
]

for text, x, y, fc, ec in boxes:
    rect = patches.FancyBboxPatch((x, y), 0.24, 0.22, boxstyle="round,pad=0.02,rounding_size=0.03",
                                  facecolor=fc, edgecolor=ec, linewidth=2, alpha=0.9)
    ax.add_patch(rect)
    ax.text(x + 0.12, y + 0.11, text, color='#ffffff', fontsize=9.5, fontweight='bold',
            ha='center', va='center', family='sans-serif', linespacing=1.3)

arrows = [
    ((0.32, 0.83), (0.38, 0.83), "Config"),
    ((0.62, 0.83), (0.68, 0.83), "RF Wave"),
    ((0.80, 0.72), (0.80, 0.44), "Reflected Echoes"),
    ((0.68, 0.33), (0.62, 0.33), "2D B-Scan Data"),
    ((0.38, 0.33), (0.32, 0.33), "Feature Vector"),
]

for start, end, label in arrows:
    ax.annotate('', xy=end, xytext=start,
                arrowprops=dict(arrowstyle="->", color='#58a6ff', lw=2.5, mutation_scale=18))
    mx = (start[0] + end[0]) / 2
    my = (start[1] + end[1]) / 2 + 0.03
    ax.text(mx, my, label, color='#8b949e', fontsize=8.5, ha='center', va='center', fontweight='bold')

# Feedback loop
ax.annotate('', xy=(0.20, 0.44), xytext=(0.20, 0.72),
            arrowprops=dict(arrowstyle="<-", color='#3fb950', lw=2, linestyle='--', mutation_scale=15))
ax.text(0.12, 0.58, "Real-time\nValidation", color='#3fb950', fontsize=8, ha='center', va='center', fontweight='bold')

ax.set_xlim(0.04, 0.96)
ax.set_ylim(0.12, 0.98)
ax.axis('off')
plt.title("MICROWAVE NDT SYSTEM - END-TO-END DATAFLOW PIPELINE", color='#ffffff', fontsize=15, fontweight='bold', pad=15)
plt.tight_layout()
df_path = os.path.join(dest_dir, "dataflow_diagram.png")
plt.savefig(df_path, facecolor=fig.get_facecolor(), edgecolor='none', dpi=300)
plt.close()
print("Saved dataflow diagram:", df_path)


# 2. Architecture Diagram
fig, ax = plt.subplots(figsize=(12, 6.5), dpi=300)
ax.set_facecolor('#0d1117')
fig.patch.set_facecolor('#0d1117')

layers = [
    ("PRESENTATION LAYER (STREAMLIT DASHBOARD)", [
        "Interactive Control Sidebar\n(Frequency, Thickness, Position)",
        "RF A-Scan & B-Scan Heatmap\n(Plotly & Matplotlib Visualizers)",
        "AI Diagnostic Report\n(Classification & Sub-mm Depth)"
    ], 0.76, '#1f6feb'),
    ("AI / ML DIAGNOSTIC & REGRESSION LAYER", [
        "Random Forest Classifier\n(150 Trees, Gini Impurity, 92.4% Acc)",
        "Flaw Depth Regressor\n(ToF Physical Calibration, 0.69mm MAE)",
        "Lateral Position Regressor\n(Contiguous FWHM Peak, 0.76mm MAE)"
    ], 0.52, '#8957e5'),
    ("SIGNAL PROCESSING & FEATURE EXTRACTION LAYER", [
        "Median Background Subtraction\n(Baseline Contrast Filter)",
        "Peak Reflection Envelope\n(Hilbert Transform / ToF Extraction)",
        "Spatial Peak Walk-Off FWHM\n(Lateral Boundary Sizing)"
    ], 0.28, '#238636'),
    ("ELECTROMAGNETIC & MATERIAL SIMULATION LAYER", [
        "Horn Antenna Simulator\n(Gain, Beamwidth, Operating GHz)",
        "Dielectric Wave Ray Tracing\n(Fresnel Reflection & Attenuation)",
        "Composite Specimen Model\n(GFRP, Permittivity, Defects)"
    ], 0.04, '#d29922'),
]

for title, boxes, y_base, border_color in layers:
    # Outer layer box
    rect_outer = patches.FancyBboxPatch((0.05, y_base), 0.90, 0.19, boxstyle="round,pad=0.015,rounding_size=0.02",
                                        facecolor='#161b22', edgecolor=border_color, linewidth=2, alpha=0.95)
    ax.add_patch(rect_outer)
    ax.text(0.07, y_base + 0.155, title, color=border_color, fontsize=10.5, fontweight='bold', family='sans-serif')
    
    # Inner 3 component boxes
    box_w = 0.27
    for b_idx, b_text in enumerate(boxes):
        bx = 0.07 + b_idx * 0.305
        by = y_base + 0.02
        rect_inner = patches.FancyBboxPatch((bx, by), box_w, 0.12, boxstyle="round,pad=0.01,rounding_size=0.015",
                                            facecolor='#21262d', edgecolor='#30363d', linewidth=1.2)
        ax.add_patch(rect_inner)
        ax.text(bx + box_w/2, by + 0.06, b_text, color='#e6edf3', fontsize=8.5,
                ha='center', va='center', family='sans-serif', linespacing=1.2)

# Inter-layer connecting arrows
for y_arr in [0.24, 0.48, 0.72]:
    ax.annotate('', xy=(0.50, y_arr + 0.035), xytext=(0.50, y_arr - 0.01),
                arrowprops=dict(arrowstyle="->", color='#58a6ff', lw=3, mutation_scale=18))

ax.set_xlim(0.02, 0.98)
ax.set_ylim(0.01, 0.99)
ax.axis('off')
plt.title("MICROWAVE NDT SYSTEM - 4-TIER MODULAR SYSTEM ARCHITECTURE", color='#ffffff', fontsize=15, fontweight='bold', pad=15)
plt.tight_layout()
arch_path = os.path.join(dest_dir, "architecture_diagram.png")
plt.savefig(arch_path, facecolor=fig.get_facecolor(), edgecolor='none', dpi=300)
plt.close()
print("Saved architecture diagram:", arch_path)
