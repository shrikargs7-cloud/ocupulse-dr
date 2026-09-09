# OcuPulse — AI-Powered Retinal Vessel Analysis

[![Python](https://img.shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.9+-5C3EE8?logo=opencv)](https://opencv.org/)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?logo=react)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.4-3178C6?logo=typescript)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/TailwindCSS-3.4-38B2AC?logo=tailwind-css)](https://tailwindcss.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **"See the Vessels. Understand the Risk."**
>
> *AI-Assisted Quantitative Retinal Vessel Segmentation, Centerline Skeletonization, Topological Geometry Extraction, and Clinical Screening Reporting.*

---

## 1. Important Medical Disclaimer

> [!IMPORTANT]
> **OcuPulse is an AI-assisted retinal image analysis and screening tool. It is not intended to provide a definitive medical diagnosis. Results must be reviewed by a qualified ophthalmologist or healthcare professional.**
>
> Quantitative metrics (vessel density, skeleton length, bifurcation counts, caliber indices) represent objective computer-vision measurements. The system is designed for **assistive screening, population health triaging, and clinical research**.

---

## 2. Problem Statement & Overview

Retinal fundus photographs contain visible micro-vasculature that offers a direct, non-invasive anatomical window into human vascular health. However, manual examination and tracing of retinal vessel arborization is:
- **Time-consuming**: Requires manual tracing of thousands of vascular branches.
- **Subjective**: High inter-observer variability between clinicians.
- **Scarcity of Specialists**: Limited access to ophthalmologists in remote/primary care settings.

**OcuPulse** provides an automated, reproducible computer-vision pipeline that:
1. Detects and isolates the circular retinal field of view (ROI).
2. Enhances the green spectral channel via CLAHE and edge-preserving filtering.
3. Segments retinal blood vessels into clean binary masks.
4. Thin vessels into one-pixel-wide centerline skeletons (Zhang-Suen algorithm).
5. Extracts topological geometry: vessel density (%), centerline length (px), branch points (bifurcations), terminal endpoints, caliber indices, and fractal complexity.
6. Assesses technical image quality (sharpness, contrast, illumination uniformity).
7. Generates downloadable & printable structured clinical screening reports.

---

## 3. High-Level System Architecture

```text
                               OCUPULSE SYSTEM ARCHITECTURE
                               
  +-----------------------------------------------------------------------------------+
  |                                  FRONTEND (React + Vite + TS)                      |
  |  - Landing Page (Hero, Tagline, Problem Overview, Scientific Rationale)           |
  |  - Analysis Studio (Drag & Drop, Demo Selectors, Live Pipeline Progress)          |
  |  - Interactive Dashboard (Metrics Cards, 6-Panel Visualizer, Split Slider, Zoom)   |
  |  - Analytics & Geometry Charts (Recharts Area & Structural Distributions)         |
  |  - History & Past Sessions Explorer (SQLite-backed session manager)               |
  |  - Comprehensive Downloadable Clinical Screening Report Generator                 |
  +-----------------------------------------------------------------------------------+
                                           ▲ │
                          REST API Requests │ │ JSON Responses & Base64/Static Media
                                           │ ▼
  +-----------------------------------------------------------------------------------+
  |                                 BACKEND (FastAPI + Python)                        |
  |  - REST Endpoints (/api/health, /api/analyze, /api/demo-samples, /api/history)    |
  |  - Storage & Database (SQLite Analysis History + Temp Image Storage)              |
  |  - Screening Interpretation Engine (Objective metrics to structured summaries)    |
  +-----------------------------------------------------------------------------------+
                                           ▲ │
                                           │ ▼
  +-----------------------------------------------------------------------------------+
  |                       COMPUTER VISION & GEOMETRY PIPELINE                         |
  |                                                                                   |
  |  [Input Fundus] ──► [ROI Circular FOV Mask] ──► [Green Channel Extraction]        |
  |                                                                                   |
  |  ──► [CLAHE Local Contrast Enhancement] ──► [Edge-Preserving Denoising]           |
  |                                                                                   |
  |  ──► [Multi-Scale Vessel Segmentation] ──► [Clean Binary Vessel Mask]            |
  |                                                                                   |
  |  ──► [Zhang-Suen Skeletonization] ──► [Topology & Geometric Feature Extraction]  |
  |                                                                                   |
  |  ──► [Vessel Density / Length / Branch Points / Endpoints / Image Quality Score]  |
  +-----------------------------------------------------------------------------------+
```

---

## 4. Computer Vision Pipeline Stages

| Stage | Module | Description | Output |
|---|---|---|---|
| **01. Ingestion & Validation** | `preprocessing.py` | Validates channels, min/max dimensions (≥100px), and non-zero variance. | Normalized RGB/BGR Matrix |
| **02. Retinal ROI Detection** | `preprocessing.py` | Luminance thresholding + morphological closing + convex hull to extract circular retinal field. | `roi_mask.png` (Binary 0/255) |
| **03. Green Channel & CLAHE** | `preprocessing.py` | Extracts green channel (peak 540-570nm vessel absorption) and applies CLAHE. | `enhanced.png` (Grayscale) |
| **04. Vessel Segmentation** | `segmentation.py` | Multi-scale Top-Hat ridge filters + local adaptive Gaussian thresholding within ROI. | `vessel_mask.png` (Binary) |
| **05. Vessel Detection Overlay** | `segmentation.py` | Alpha-blended cyan/teal vessel mask overlaid on anatomical fundus photograph. | `vessel_overlay.png` (Color) |
| **06. Centerline Skeletonization** | `skeletonization.py`| Zhang-Suen morphological thinning to extract 1-pixel-wide centerline centerlines. | `skeleton.png` (Centerline) |
| **07. Geometry & Topology** | `geometry.py` | 8-connectivity neighborhood convolution for branch points, endpoints, and vessel length. | Numerical Metric Vectors |
| **08. Quality & Screening Report** | `quality.py` | Laplacian variance focus, RMS contrast, and structured non-diagnostic report synthesis. | Screening Report JSON/PDF |

---

## 5. Quantitative Biomarkers Extracted

- **Vessel Density (%)**: $\frac{\text{Vessel Pixels}}{\text{Retinal ROI Pixels}} \times 100\%$ (strictly calculated, e.g. 11.98%).
- **Total Vessel Length (px)**: Zhang-Suen skeleton centerline length accounting for orthogonal and diagonal steps.
- **Branch Points (Bifurcations)**: Connected-component clustered junction pixels ($\sum N_8 \ge 3$).
- **Terminal Endpoints**: Centerline endpoints with exactly 1 neighbor ($\sum N_8 = 1$).
- **Vessel Area (px)**: Absolute vascular pixel area within retinal field.
- **Skeleton Density (%)**: Centerline linear density relative to ROI area.
- **Mean Caliber Index (px)**: $\frac{\text{Vessel Area}}{\text{Total Centerline Length}}$.
- **Vascular Fractal Dimension**: Box-counting structural complexity index ($1.0$ to $2.0$).
- **Image Quality Score**: Composite score ($0.0 - 1.0$) based on focus, contrast, and quadrant illumination uniformity.

---

## 6. Smart India Hackathon (SIH) 2-Minute Demo Flow

1. **Open OcuPulse**: Landing page introduces the problem and scientific rationale.
2. **Click "Try Demo"**: Preloads benchmark fundus images (Standard, Dense Arborization, Subtle Micro-vessels).
3. **Click "Analyze Retina"**: Real-time progress tracker visualizes all 7 computer vision pipeline phases.
4. **Results Dashboard**:
   - Inspect **Key Metrics Cards** (Density %, Length, Branch Points, Endpoints).
   - Test the **Interactive Before/After Split Comparison Slider**.
   - Explore the **6-Stage Visualizer Grid** and open the **Fullscreen Zoom & Pan Modal**.
   - Review **Recharts Distribution & Topology Analytics**.
5. **Download Report**: Open the **Clinical Screening Report Modal** and click **Print / Save PDF**.
6. **History Explorer**: Navigate to `/history` to review saved SQLite records.

---

## 7. Local Installation & Development

### Prerequisites
- Python 3.9+ (Python 3.10 / 3.11 / 3.12 recommended)
- Node.js 18+ and npm

### Backend Setup (macOS / Linux)

```bash
# 1. Navigate to workspace
cd outputs/film-production-club

# 2. Activate virtual environment
source venv/bin/activate

# 3. Run FastAPI backend server
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Backend Setup (Windows PowerShell)

```powershell
cd outputs\film-production-club
.\venv\Scripts\Activate.ps1
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup

```bash
# In a new terminal window
cd outputs/film-production-club/frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```

Open your browser at `http://localhost:5173`.

---

## 8. Backend REST API Reference

The interactive Swagger UI is available at `http://localhost:8000/docs`.

### Core Endpoints:
- `GET /api/health`: System health status and operational check.
- `GET /api/demo-samples`: Returns metadata and preview links for preloaded benchmark fundus images.
- `GET /api/sample/{sample_id}`: Serves sample retinal fundus images directly.
- `POST /api/analyze`: Multipart/form-data endpoint accepting an uploaded fundus image (`file`) or `demo_id`. Returns metrics, quality score, base64 visualizer images, and structured screening summary.
- `GET /api/history`: Lists previous analysis sessions stored in SQLite.
- `GET /api/history/{analysis_id}`: Retrieves complete details and visualizers for a past session.
- `DELETE /api/history/{analysis_id}`: Deletes an analysis record.

---

## 9. Running Automated Tests

Run backend unit and integration tests with pytest:

```bash
PYTHONPATH=. ./venv/bin/pytest backend/tests -v
```

Test coverage includes:
- Image validation & boundary protection
- Preprocessing and circular ROI field isolation
- Multi-scale vessel segmentation and alpha overlay
- Centerline skeletonization and topology detection (endpoints, branch points)
- Geometric feature calculations (density, length, caliber, fractal dimension)
- API endpoints (`/api/health`, `/api/demo-samples`, `/api/analyze`, `/api/history`)
- Invalid file and error handling

---

## 10. Future Deep Learning & Dataset Roadmap

OcuPulse is architected with a decoupled segmentation interface (`segment_vessels`), enabling future upgrades:
- **Deep Learning Vessel Segmentation**: U-Net / Attention U-Net / LadderNet.
- **Dataset Benchmarking**: Validation against standard public datasets:
  - **DRIVE** (Digital Retinal Images for Vessel Extraction)
  - **STARE** (Structured Analysis of the Retina)
  - **HRF** (High-Resolution Fundus)
  - **CHASE_DB1**
- **Evaluation Metrics**: Dice Coefficient, IoU, Sensitivity, Specificity, Accuracy, and Precision.
- **Clinical Landmark Detection**: Automated Optic Disc and Macula foveal avascular zone (FAZ) segmentation.

---

## 11. License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
