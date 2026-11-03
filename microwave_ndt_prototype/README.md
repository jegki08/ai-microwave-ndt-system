# AI-Based Microwave Non-Destructive Testing (NDT) System for Composite Materials Using Python Antenna Simulation

## Overview
This system provides an end-to-end Python simulation and machine-learning inspection pipeline for microwave Non-Destructive Testing (NDT) of dielectric composite materials (such as Glass-Fiber Reinforced Polymer slabs, GFRP).

The system integrates:
1. **Directional Antenna Simulation**: Transmitting (Tx) and Receiving (Rx) microwave antennas with analytical cosine radiation patterns $E(\theta) = \cos^n(\theta)$, configurable beamwidth, frequency, and standoff distance.
2. **Electromagnetic Signal & Wave Propagation**: Modulated microwave Gaussian pulse transmission, Fresnel reflection/transmission interfaces, phase velocity $v = c / \sqrt{\epsilon_r}$, dielectric attenuation $\alpha$, time-of-flight (ToF) delay, and defect shadowing effects.
3. **Defect Simulation**: Three conditions:
   - **No defect** (pristine composite slab).
   - **Internal crack** (thin planar boundary/delamination, sharp reflection echo, narrow spatial response).
   - **Air void** (volumetric pore cavity, dual boundary echo with phase inversion, wider spatial scattering).
4. **B-Scan Microwave Imaging**: Antenna scanning across the sample yielding 2D B-scan heatmaps and 1D reflection profiles.
5. **AI Classification & Defect Localization**: Random Forest and Gradient Boosting pipelines predicting condition ("No defect", "Internal crack", "Air void"), confidence scores, lateral position $x$ (mm), and depth $z$ (mm).
6. **Streamlit Interactive Dashboard**: Complete UI separating simulator ground truth from blind AI inference, featuring interactive waveforms, B-scan heatmaps, antenna setup schematics, and evaluation metrics.

---

## Project Structure

```text
microwave_ndt_prototype/
│
├── antenna_simulator.py    # Analytical antenna radiation pattern, directivity, Tx/Rx geometry
├── signal_simulator.py     # Wave propagation physics, Fresnel equations, A-scan & B-scan generation
├── dataset_generator.py    # Synthetic dataset generator with strict parameter variation
├── train_model.py          # ML training pipeline (70/15/15 train/val/test split, metrics, model export)
├── prediction.py           # Blind AI inference engine for classification and localization
├── app.py                  # Streamlit web dashboard
├── test_system.py          # Automated verification script testing all modules
├── requirements.txt        # Python package dependencies
├── RUN_PROJECT.bat         # One-click Windows launch script
│
└── models/                 # Serialized model artifacts
    ├── defect_classifier.joblib
    ├── position_regressor.joblib
    ├── depth_regressor.joblib
    ├── model_metrics.joblib
    ├── class_names.joblib
    └── feature_names.joblib
```

---

## Mathematical & Physical Foundations

### 1. Analytical Antenna Radiation Pattern
Microwave horn/probe directivity is modeled via an analytical directional cosine pattern:
$$E(\theta) = \begin{cases} \cos^n(\theta), & |\theta| \le \frac{\pi}{2} \\ 0, & |\theta| > \frac{\pi}{2} \end{cases}$$
For directivity factor $n = 4$, the Half-Power Beamwidth (HPBW) is:
$$\text{HPBW} = 2 \arccos\left(0.5^{\frac{1}{2n}}\right) \approx 47.0^\circ$$
The two-way antenna coupling to a target point $(x, z)$ from Tx and Rx is:
$$W(x, z) = E(\theta_{Tx}) \cdot E(\theta_{Rx})$$

### 2. Dielectric Wave Propagation & Attenuation
In a low-loss dielectric composite with real relative permittivity $\epsilon_r$ and loss tangent $\tan\delta$:
- **Propagation Speed**:
  $$v_m = \frac{c}{\sqrt{\epsilon_r}} \approx 146.4 \text{ mm/ns} \quad (\text{for } \epsilon_r = 4.2)$$
- **Dielectric Attenuation Constant**:
  $$\alpha \approx \frac{\omega}{2c} \sqrt{\epsilon_r} \tan\delta \quad [\text{Np/mm}]$$

### 3. Reflection Coefficients (Fresnel)
- Air-to-Composite Surface Reflection:
  $$\Gamma_{01} = \frac{1 - \sqrt{\epsilon_r}}{1 + \sqrt{\epsilon_r}}$$
- Back-Wall Reflection (Composite-to-Air):
  $$\Gamma_{10} = \frac{\sqrt{\epsilon_r} - 1}{\sqrt{\epsilon_r} + 1}$$

### 4. Time-of-Flight (ToF) Relations
$$\tau_{front} = \frac{2 d_{standoff}}{c}$$
$$\tau_{defect} = \tau_{front} + \frac{2 z_{defect}}{v_m}$$
$$\tau_{back} = \tau_{front} + \frac{2 L_{material}}{v_m}$$

---

## Actual Model Evaluation Metrics (Held-Out Test Set)

Models were evaluated on an unseen held-out test partition (158 samples, 15% stratified test split from 1,050 total simulations with varying frequencies, standoffs, materials, and noise levels $\sigma \in [0.015, 0.055]$).

- **Overall Test Classification Accuracy**: **92.41%**
- **Validation Accuracy**: **91.77%**
- **Defect Lateral Position ($x$) MAE**: **0.76 mm** (RMSE: 0.94 mm)
- **Defect Depth ($z$) MAE**: **0.69 mm** (RMSE: 0.96 mm)

### Classification Report:
```text
                precision    recall  f1-score   support

     No defect       1.00      1.00      1.00        52
Internal crack       0.89      0.89      0.89        53
      Air void       0.89      0.89      0.89        53

      accuracy                           0.92       158
     macro avg       0.92      0.92      0.92       158
  weighted avg       0.92      0.92      0.92       158
```

### Confusion Matrix:
```text
Predicted ->    No defect   Internal crack   Air void
True
No defect           52            0             0
Internal crack       0           47             6
Air void             0            6            47
```

### Top Most Informative Microwave Signal Features:
1. `waveform_kurtosis`: **14.49%** (sharp peaked crack echo vs flattened void doublet)
2. `spectral_centroid_norm`: **13.48%** (physical frequency spectrum centroid)
3. `defect_to_front_ratio`: **9.71%** (reflection contrast)
4. `spatial_fwhm_mm`: **9.06%** (clean contiguous anomaly lateral spread)
5. `backwall_drop_ratio`: **7.19%** (defect shadowing drop)

---

## Execution Instructions

### Option 1: Quick Launch (Windows)
Double-click `RUN_PROJECT.bat` in either the workspace root or the `microwave_ndt_prototype/` folder.

### Option 2: Command Line (PowerShell / Command Prompt)

```powershell
cd c:\Users\LENOVO\Downloads\microwave_ndt_2day_prototype\microwave_ndt_prototype

# 1. Activate Python virtual environment
.\.venv\Scripts\Activate.ps1

# 2. Run system verification tests
python test_system.py

# 3. Train models (if not already trained)
python train_model.py

# 4. Launch Streamlit Web Dashboard
streamlit run app.py
```

---

## Scientific Assumptions & Limitations

1. **Ray-Tracing & Analytical Pattern Approximation**:
   - The simulation employs geometric ray-path time-of-flight, Fresnel reflection formulas, and an analytical $\cos^n(\theta)$ directional antenna pattern.
   - It is an **educational and prototyping tool**, NOT a 3D full-wave electromagnetic solver (such as CST Studio Suite, Ansys HFSS, or openEMS FDTD).
2. **Synthetic Data Disclaimer**:
   - The reported accuracy reflects performance on synthetically generated microwave responses.
   - Real-world composite inspection entails fiber weave scattering, delamination surface roughness, probe cross-polarization, and hardware instrument drift.
3. **Hardware Validation Requirement**:
   - Deployment on physical structures requires Vector Network Analyzer (VNA) $S_{11}/S_{21}$ calibration, calibrated reference composite standards, and experimental NDT validation.
