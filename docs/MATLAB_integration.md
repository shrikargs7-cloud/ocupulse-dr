# OcuPulse MATLAB & Simulink Integration Guide

OcuPulse features a hybrid architecture combining a high-performance Python/FastAPI web service with MATLAB and Simulink algorithms.

---

## 1. Supported Toolboxes

The pipeline leverages functions from:
1. **Image Processing Toolbox**: Contrast Limited Adaptive Histogram Equalization (`adapthisteq`), multi-scale Top-Hat morphology, connected component labeling (`bwconncomp`), and morphological thinning.
2. **Computer Vision Toolbox**: Feature extraction, circular Hough transforms for optic disc localization.
3. **Deep Learning Toolbox**: Pretrained feature extraction, Grad-CAM attention map generation.
4. **Medical Imaging Toolbox**: Retinal coordinate calibration and DICOM parsing.
5. **Simulink**: Multi-server queuing and discrete-event flow simulation (`screening_pipeline.slx`).
6. **Statistics and Machine Learning Toolbox**: Temperature scaling calibration, confidence interval estimation.

---

## 2. Python-MATLAB Bridge (`backend/app/matlab/bridge.py`)

The bridge connects Python to MATLAB using the official MATLAB Engine for Python:
```python
import matlab.engine
eng = matlab.engine.start_matlab()
```

### Automatic Standalone Fallback
To ensure OcuPulse runs reliably on machines without a commercial MATLAB license (e.g. hackathon demo environments or lightweight clinic servers), `bridge.py` includes a **zero-dependency Python mathematical fallback**:
- If MATLAB Engine is present: executes `.m` and `.slx` models via `eng`.
- If MATLAB Engine is absent: runs the mathematical queuing and computer-vision algorithms in Python.

---

## 3. MATLAB Script Reference

All MATLAB algorithms are located in `matlab_scripts/`:
- `quality_assessment.m`: Focus (Laplacian), Illumination, FOV evaluation and adaptive CLAHE enhancement.
- `vessel_extraction.m`: Multi-scale morphological vessel segmentation, centerline thinning, and caliber estimation.
- `lesion_detection.m`: Sub-pixel microaneurysm detection, exudates, hemorrhages, and neovascularization.
- `dr_grading.m`: 5-level International Clinical Diabetic Retinopathy (ICDR) severity scoring.
- `fractal_dimension.m`: Box-counting vascular complexity estimation.
- `explainability.m`: Feature importance plots and lesion distribution charts.
- `simulate_pipeline.m`: Simulink telemedicine district-scale queuing simulation.
- `report_generation.m`: Clinical diagnostic report synthesis.

---

## 4. Running Scripts Directly in MATLAB

Open MATLAB, navigate to `matlab_scripts/`, and test any function:
```matlab
img = imread('../backend/data/samples/demo_normal.png');
[quality, enhanced] = quality_assessment(img);
[vessels, skeleton, metrics] = vessel_extraction(enhanced);
lesions = lesion_detection(enhanced, vessels);
result = simulate_pipeline(100000, 100, 30, 50, 8);
```
