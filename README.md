# OcuPulse — AI-Powered Retinal Diagnostic & Diabetic Retinopathy Platform

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-EE4C2C?logo=pytorch&logoColor=white)](https://pytorch.org/)
[![React 18](https://img.shields.io/badge/React-18.3-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.4-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/TailwindCSS-3.4-38B2AC?logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?logo=supabase&logoColor=white)](https://supabase.com/)
[![MATLAB Simulink](https://img.shields.io/badge/MATLAB-Simulink-E16727?logo=mathworks&logoColor=white)](https://www.mathworks.com/products/simulink.html)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **"Bridging Computer Vision, Biophysical Modeling, and Clinical Ophthalmology to Eradicate Preventable Diabetic Blindness."**

---

## 🎥 Project Demonstration & Video Walkthrough

[![Watch OcuPulse Video Walkthrough](https://img.shields.io/badge/▶%20Watch%20Demo-Google%20Drive%20Video-E1306C?style=for-the-badge&logo=google-drive&logoColor=white)](https://drive.google.com/file/d/1iIu_hFnGv9Qd7C7yrte3tSrKxbx1NjUM/view?usp=sharing)

> **Full Video Walkthrough & Presentation**:  
> 🔗 **[https://drive.google.com/file/d/1iIu_hFnGv9Qd7C7yrte3tSrKxbx1NjUM/view?usp=sharing](https://drive.google.com/file/d/1iIu_hFnGv9Qd7C7yrte3tSrKxbx1NjUM/view?usp=sharing)**  
> *Includes live platform demonstration, deep learning inference, Grad-CAM attention heatmaps, automated triage scheduling, and Simulink clinical capacity modeling.*

---

## 📑 Table of Contents

1. [Important Medical Disclaimer](#1-important-medical-disclaimer)
2. [Executive Summary & Problem Statement](#2-executive-summary--problem-statement)
3. [Key Innovations](#3-key-innovations)
4. [System Architecture](#4-system-architecture)
5. [AI & Computer Vision Diagnostic Pipeline](#5-ai--computer-vision-diagnostic-pipeline)
   - [PyTorch Deep Learning Classifier (EfficientNet-B3)](#51-pytorch-deep-learning-classifier-efficientnet-b3)
   - [Clinical Lesion-Gated Reconciliation Engine](#52-clinical-lesion-gated-reconciliation-engine)
   - [Explainable AI (Grad-CAM Saliency)](#53-explainable-ai-grad-cam-saliency)
   - [Multi-Scale Vessel Segmentation & Geometry](#54-multi-scale-vessel-segmentation--geometry)
   - [Quantitative Retinal Biomarkers](#55-quantitative-retinal-biomarkers)
6. [Automated Clinical Triage & Specialist Referral](#6-automated-clinical-triage--specialist-referral)
7. [MATLAB & Simulink Healthcare Modeling](#7-matlab--simulink-healthcare-modeling)
8. [Validated Clinical Datasets](#8-validated-clinical-datasets)
9. [Database & Cloud Infrastructure (Supabase + SQLite)](#9-database--cloud-infrastructure-supabase--sqlite)
10. [Technology Stack](#10-technology-stack)
11. [Installation & Getting Started](#11-installation--getting-started)
12. [REST API Documentation](#12-rest-api-documentation)
13. [Verification & Quality Assurance](#13-verification--quality-assurance)
14. [License](#14-license)

---

## 1. Important Medical Disclaimer

> [!IMPORTANT]
> **OcuPulse is an assistive medical AI platform designed for clinical research, automated triage, and telemedicine screening.** It is engineered to assist healthcare providers and optometrists in rapidly detecting diabetic retinopathy and microvascular abnormalities. It is not intended to replace direct professional clinical evaluation. Final diagnostic and treatment determinations must always be confirmed by a licensed ophthalmologist or retina specialist.

---

## 2. Executive Summary & Problem Statement

Diabetic Retinopathy (DR) is the **leading cause of preventable blindness** among working-age adults globally, impacting over **100 million individuals**. Early detection and timely intervention can prevent up to **95% of vision loss**.

### The Clinical Screening Bottlenecks:
1. **Severe Specialist Deficit**: In low- and middle-income regions, the ratio of ophthalmologists to patients often exceeds 1:100,000, creating months-long waiting lists for routine screening.
2. **Subjectivity & Human Fatigue**: Manual grading of fundus photographs across high-volume screening camps exhibits high inter-observer variability ($\kappa \approx 0.65-0.75$).
3. **Black-Box AI Trust Deficit**: Standard end-to-end deep neural networks often fail to explain *why* an image was classified as diseased and suffer from false-positive hallucinations on artifact-laden normal retinas.
4. **Disjointed Referral Loops**: Traditional screening programs lack automated closing loops—patients identified with vision-threatening disease frequently drop out before obtaining an emergency appointment.

**OcuPulse** resolves these challenges by introducing a **neuro-symbolic, biophysically-grounded screening pipeline** that unifies:
- Deep convolutional neural networks calibrated to the **International Clinical Diabetic Retinopathy (ICDR)** standard.
- Deterministic **biophysical lesion gating** that cross-examines microvascular anomalies (microaneurysms, hemorrhages, hard/soft exudates, neovascularization).
- **Explainable AI (Grad-CAM)** highlighting precise anatomical regions of concern.
- **Automated clinical triage dispatch** that auto-schedules doctor appointments for critical patients (ICDR $\ge 2$).
- **Simulink queue-theoretic capacity modeling** to optimize hospital throughput and prevent resource saturation.

---

## 3. Key Innovations

- 🧠 **Dual-Engine Diagnostic Architecture**: Combines an EfficientNet-B3 deep convolutional network with deterministic lesion-detection rules, ensuring high sensitivity while eliminating false-positive referrals on clean scans.
- 🔬 **Clinical Lesion-Gated Prior**: Enforces AAO/ICDR guidelines—retinas exhibiting zero microvascular lesions are strictly reconciled as **Grade 0 (No DR)** with high confidence ($98.5\%$), protecting healthy individuals from unnecessary emergency referrals.
- 👁️ **Visual Explainability (Grad-CAM)**: Generates high-resolution saliency maps overlaid on fundus structures so clinicians can verify whether neural attention aligns with true pathological lesions.
- 📐 **Sub-Pixel Microvascular Morphometry**: Computes objective structural biomarkers including vessel density, fractal dimension (box-counting complexity), vessel caliber, skeleton tortuosity, and bifurcation topology.
- 🏥 **Closed-Loop Emergency Scheduling**: When referable disease (ICDR Grade 2, 3, or 4) is identified, the platform automatically schedules an emergency consultation with available ophthalmologists, tracking urgency, priority level, and clinical justification.
- 📈 **Simulink Telemedicine Queue Modeling**: Integrates MATLAB/Simulink stateflow models (`.slx`) to simulate patient flow, network latency, edge-vs-cloud compute tradeoffs, and hospital specialist load balancing.
- ☁️ **Resilient Cloud Persistence**: High-availability database layer utilizing **Supabase PostgreSQL** (with pooled connections) with automatic seamless fallback to local SQLite for offline/remote clinic operations.

---

## 4. System Architecture

```text
                                       OCUPULSE SYSTEM TOPOLOGY
                                       
  ┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐
  │                                    CLIENT LAYER (React 18 + Vite + TS)                                   │
  │  • Modern Glassmorphic Dark UI               • Multi-Stage Live Processing Stepper                       │
  │  • Interactive Before/After Split Slider     • 6-Stage Visualizer Grid (Masks, Heatmaps, Skeletons)       │
  │  • Real-Time Recharts Telemetry Charts       • Automated Triage & Appointment Scheduling Dashboard       │
  │  • MATLAB/Simulink Interactive Simulator     • Comprehensive PDF Clinical Report Generation              │
  └────────────────────────────────────────────────────┬─────────────────────────────────────────────────────┘
                                                       │ HTTPS / REST & WebSockets
                                                       ▼
  ┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐
  │                                    BACKEND ENGINE (FastAPI / Uvicorn)                                    │
  │  • REST API Controllers (/api/analyze, /api/appointments, /api/reports, /api/history)                    │
  │  • Image Validation & Quality Assurance Gate (FOV verification, illumination, sharpness)                 │
  │  • Dual-Database ORM Router (Supabase PostgreSQL / Offline SQLite Fallback)                              │
  └────────────────────────┬──────────────────────────────────────────────────┬──────────────────────────────┘
                           │                                                  │
                           ▼                                                  ▼
  ┌──────────────────────────────────────────────────┐     ┌─────────────────────────────────────────────────┐
  │         AI & COMPUTER VISION SUBSYSTEM           │     │            MATLAB & SIMULINK SUBSYSTEM          │
  │                                                  │     │                                                 │
  │  [Raw Fundus] ──► [Green Channel + CLAHE]        │     │  • screening_pipeline.slx (Edge vs Cloud Model) │
  │        │                                         │     │  • resource_optimiser.slx (Queue Optimization)  │
  │        ├─► [EfficientNet-B3 Deep Classifier]     │     │  • telemedicine_workflow.slx (Clinic Triage)    │
  │        │         │                               │     │  • analyse_retina.m (Biophysical Biomarkers)    │
  │        │         ▼                               │     │  • fractal_analytics.m (Box-Counting Dimension) │
  │        ├─► [Grad-CAM Attention Heatmap]          │     │  • lesion_quantification.m (MA/HE/EX Detect)    │
  │        │                                         │     └─────────────────────────────────────────────────┘
  │        ├─► [Biophysical Lesion Detection]        │
  │        │   (Microaneurysms, Exudates, Hemorrhages│
  │        │                                         │
  │        ▼                                         │
  │  [Clinical Lesion-Gated Reconciliation Engine]   │
  │        │                                         │
  │        ├─► [Zhang-Suen Centerline Skeletonizer]  │
  │        │                                         │
  │        ▼                                         │
  │  [Topological & Geometric Biomarker Extractor]   │
  │  (Vessel Density, Tortuosity, Caliber, Fractal)  │
  └────────────────────────┬─────────────────────────┘
                           │
                           ▼
  ┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐
  │                                 CLINICAL ACTION & PERSISTENCE LAYER                                      │
  │  • ICDR Scale Determination (Grade 0: Normal ──► Grade 4: Proliferative DR)                              │
  │  • Referral Gate: If Grade >= 2 & Referable ──► Auto-Book Emergency Specialist Appointment               │
  │  • Supabase Enterprise Cloud DB: Encrypted storage of patient metadata, metrics, and appointment records │
  └──────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. AI & Computer Vision Diagnostic Pipeline

### 5.1. PyTorch Deep Learning Classifier (EfficientNet-B3)

The deep learning classifier uses an **EfficientNet-B3** backbone pre-trained on ImageNet and fine-tuned on multi-center retinal fundus corpora. EfficientNet-B3 compounds depth, width, and resolution scaling, providing optimal feature extraction for fine vascular lesions with modest parameter count ($\approx 12\text{M}$ parameters).

#### The 5-Point International Clinical Diabetic Retinopathy (ICDR) Grading Scale:

$$\mathcal{C} = \{\text{Grade 0: No DR}, \text{Grade 1: Mild NPDR}, \text{Grade 2: Moderate NPDR}, \text{Grade 3: Severe NPDR}, \text{Grade 4: Proliferative DR}\}$$

```
   Grade 0 (No DR)             Grade 1 (Mild)            Grade 2 (Moderate)          Grade 3 (Severe)             Grade 4 (PDR)
 ┌─────────────────┐        ┌──────────────────┐       ┌───────────────────┐      ┌────────────────────┐       ┌──────────────────┐
 │ • Zero lesions  │        │ • Microaneurysms │       │ • More than MAs   │      │ • 4-2-1 Rule:      │       │ • Neovascular-   │
 │ • Healthy retina│   ──►  │   only (<= 3)    │  ──►  │ • Hard exudates   │ ──►  │   >20 intraretinal │  ──►  │   ization        │
 │ • Non-referable │        │ • Non-referable  │       │ • Blot hemorrhage │      │   hemorrhages/quad │       │ • Vitreous bleed │
 │ • Routine check │        │ • 12-mo review   │       │ • Refer to Doctor │      │ • Urgent Referral  │       │ • Emergency Care │
 └─────────────────┘        └──────────────────┘       └───────────────────┘      └────────────────────┘       └──────────────────┘
```

---

### 5.2. Clinical Lesion-Gated Reconciliation Engine

Deep learning classifiers alone can occasionally produce false positives due to illumination gradients or camera artifacts. In clinical ophthalmology, **Diabetic Retinopathy cannot exist without verifiable microvascular lesions**.

OcuPulse implements a **Biophysical Prior Reconciler**:
- **Zero Lesions Check**: If the biophysical lesion detector counts $0$ microaneurysms, $0$ exudates, $0$ hemorrhages, and $0$ neovascular regions:
  $$\text{Reconciled Grade} = \text{Grade 0 (No DR)}, \quad \text{Confidence} = 98.5\%, \quad \text{Referable} = \text{False}$$
- **Mild Microvascular Stage**: If isolated microaneurysms are detected ($\le 3$) without hemorrhages/exudates:
  $$\text{Reconciled Grade} = \text{Grade 1 (Mild NPDR)}, \quad \text{Referable} = \text{False}$$
- **Moderate / Severe Stage**: If $\ge 5$ microaneurysms, exudates, or hemorrhages are confirmed:
  $$\text{Reconciled Grade} \ge \text{Grade 2 (Moderate+ NPDR)}, \quad \text{Referable} = \text{True}, \quad \text{Trigger Appointment} = \text{True}$$

This hybrid neuro-symbolic mechanism guarantees **zero false-positive emergency appointments** on clean retinas.

---

### 5.3. Explainable AI (Grad-CAM Saliency)

To provide transparency, OcuPulse generates **Gradient-Weighted Class Activation Mapping (Grad-CAM)** from the final convolutional layer of EfficientNet-B3:

$$L_{\text{Grad-CAM}}^c = \text{ReLU}\left(\sum_k \alpha_k^c A^k\right), \quad \text{where} \quad \alpha_k^c = \frac{1}{Z}\sum_{i}\sum_{j} \frac{\partial y^c}{\partial A_{i,j}^k}$$

The resulting continuous heatmap highlights the specific microvascular patches driving the model's classification, rendering AI reasoning fully inspectable by the ophthalmologist.

---

### 5.4. Multi-Scale Vessel Segmentation & Geometry

```
[Raw Fundus] ──► [Circular FOV Masking] ──► [Green Channel Selection (λ ~ 540-570nm)]
       │
       ▼
[CLAHE Dynamic Contrast Amplification] ──► [Multi-Scale Frangi Hessian Ridge Filters]
       │
       ▼
[Adaptive Gaussian Thresholding] ──► [Binary Vessel Tree Mask]
       │
       ▼
[Zhang-Suen Morphological Thinning] ──► [Single-Pixel Centerline Skeleton]
       │
       ▼
[8-Connected Graph Topology Traversal] ──► [Bifurcations, Endpoints, Tortuosity Index]
```

1. **Spectral Channel Isolation**: Extracts the green channel where ocular hemoglobin exhibits peak light absorption, maximizing contrast between blood vessels and the choroidal background.
2. **Circular FOV Mask**: Automatically detects the round retinal boundary, eliminating flash perimeter artifacts.
3. **CLAHE Enhancement**: Contrast Limited Adaptive Histogram Equalization prevents over-amplification in bright macular regions while exposing faint peripheral capillaries.
4. **Frangi Hessian Filter**: Computes eigenvalues of the local Hessian matrix $(\lambda_1, \lambda_2)$ across multiple scales ($\sigma \in [1.0, 3.0]$) to selectively amplify tubular vascular structures while suppressing planar and spherical noise.
5. **Zhang-Suen Skeletonization**: Iteratively thins the segmented vessels to a 1-pixel-wide topological centerline without altering connectivity.

---

### 5.5. Quantitative Retinal Biomarkers

| Biomarker Metric | Clinical Formula / Method | Diagnostic Relevance |
|---|---|---|
| **Vessel Density (%)** | $\frac{\text{Vessel Pixels}}{\text{Retinal ROI Pixels}} \times 100$ | Ischemic dropout, vascular rarefaction in advanced diabetes |
| **Centerline Length (px)** | $\sum \text{Skeleton Pixels} \times \text{Step Correction}$ | Total perfused vascular arborization |
| **Branch Points (Bifurcations)** | 8-neighbor connectivity $\sum N_8(p) \ge 3$ | Microvascular pruning or aberrant neovascular budding |
| **Terminal Endpoints** | 8-neighbor connectivity $\sum N_8(p) = 1$ | Capillary bed non-perfusion and terminal pruning |
| **Mean Caliber Index (px)** | $\frac{\text{Vessel Area}}{\text{Skeleton Length}}$ | Arteriolar narrowing / venular dilation (AV ratio marker) |
| **Tortuosity Index** | $\frac{\text{Actual Arc Length}}{\text{Chord Distance}} - 1$ | Elevated vascular shear stress, hypertension, and DR progression |
| **Fractal Dimension ($D_0$)** | Box-counting method: $\lim_{\epsilon \to 0} \frac{\log N(\epsilon)}{\log(1/\epsilon)}$ | Global vascular complexity loss ($D_0 < 1.40$ indicates risk) |
| **Image Quality Grade** | Laplacian variance + Michelson contrast | Pre-screening quality assurance preventing misdiagnosis |

---

## 6. Automated Clinical Triage & Specialist Referral

When an analysis reveals **referable disease** ($\text{ICDR Grade} \ge 2$), OcuPulse's triage dispatch orchestrates an emergency clinical referral:

```
                  DIAGNOSTIC TRIAGE DECISION TREE
                  
                        [Analysis Complete]
                                 │
                     Is ICDR Grade >= 2 AND
                       Referable == True?
                                 │
                ┌────────────────┴────────────────┐
               YES                                NO
                │                                 │
                ▼                                 ▼
   [Critical Triage Active]           [Routine Care Pathway]
   • Assign Priority Level            • Annual/Biennial Screening
   • Match Available Doctor           • Self-Care Recommendations
   • Allocate Hospital Slot           • No Referral Required
   • Persist to DB Appointments       • Return Clean Status
   • Render in Appointments UI
```

### Auto-Generated Referral Record:
- **Patient Identifier**: Auto-assigned or linked to existing health ID.
- **Assigned Specialist**: Matches verified ophthalmologists (e.g., *Dr. Rajesh Sharma, MD (Retina)*).
- **Scheduled Time**: Automatically provisioned within a 48-hour critical window.
- **Priority Tier**: `URGENT` for Grade 2 (Moderate), `EMERGENCY` for Grade 3-4 (Severe/PDR).
- **Clinical Justification**: Clear documentation of detected microaneurysms, hemorrhages, and vascular density reductions for immediate review.

---

## 7. MATLAB & Simulink Healthcare Modeling

OcuPulse bridges clinical AI with industrial systems engineering by integrating MATLAB algorithms and Simulink models:

### 1. Simulink Models (`/simulink_models`)
- `screening_pipeline.slx`: Models multi-tier edge-vs-cloud screening throughput, network latency under variable bandwidth, and packet loss handling in rural telemedicine camps.
- `resource_optimiser.slx`: Queue-theoretic discrete-event simulation optimizing ophthalmologist review loads, triage queue wait times, and emergency bed allocation.
- `telemedicine_workflow.slx`: End-to-end operational stateflow model illustrating patient ingestion, automated grading, tele-consultation dispatch, and follow-up closure.

### 2. Standalone MATLAB Scripts (`/matlab_scripts`)
- `analyse_retina.m`: Complete biophysical feature extraction pipeline in pure MATLAB.
- `FrangFilter2D.m`: High-performance 2D multiscale vesselness filter implementation.
- `fractal_dimension.m`: Multi-box counting grid evaluation of vascular complexity.
- `lesion_detection.m`: Mathematical morphology for microaneurysm and exudate segmentation.
- `dr_grading.m` & `severity_grading.m`: MATLAB decision tree severity classifier.

---

## 8. Validated Clinical Datasets

The models and algorithms within OcuPulse are designed and validated against international gold-standard ophthalmic databases:

| Dataset | Sample Volume | Resolution | Ground Truth Annotations | Primary Usage |
|---|---|---|---|---|
| **APTOS 2019** | 3,662 fundus scans | Multi-resolution | 5-class ICDR severity grades | Deep learning classifier fine-tuning |
| **Kaggle DR 2750** | 2,750 fundus scans | Multi-resolution | 5-class (Healthy: 1,000, Mild: 370, Moderate: 900, Severe: 190, PDR: 290) | Class-imbalance evaluation & ordinal grading |
| **DRIVE** | 40 fundus images | $565 \times 584$ | Dual expert manual vessel segmentations | Vessel segmentation & skeleton accuracy |
| **IDRiD** | 516 images | $4288 \times 2848$ | Pixel-level lesion masks (MA, HE, EX, SE) | Biophysical lesion detection calibration |
| **Messidor-2** | 1,200 images | $1440 \times 960$ | DR grade and Diabetic Macular Edema (DME) | Cross-dataset generalizability testing |

---

## 9. Database & Cloud Infrastructure (Supabase + SQLite)

OcuPulse features an enterprise **hybrid persistence architecture**:

```
                         PERSISTENCE ROUTER
                                  │
                 Is DATABASE_URL (Supabase) Available?
                                  │
                ┌─────────────────┴─────────────────┐
               YES                                 NO
                │                                  │
                ▼                                  ▼
   [Supabase PostgreSQL]                   [Local SQLite Engine]
   • Cloud-Hosted Relational DB            • Zero-Config Local File
   • Session Pooler (Port 5432/6543)       • Offline Remote Clinic Capable
   • Auto-Migrated Schema                  • Seamless Dev Fallback
```

### Database Schema Highlights:
- **`analyses` / `images`**: Stores scan telemetry, quality scores, ICDR grade, confidence, fractal dimension, vessel density, and full biomarker JSON payloads.
- **`appointments`**: Manages patient triage bookings, physician assignments, urgency status (`SCHEDULED`, `COMPLETED`), and scheduled appointment timestamps.

---

## 10. Technology Stack

### Frontend Application
- **Core**: React 18.3, TypeScript 5.4, Vite
- **Styling**: Tailwind CSS 3.4, Lucide React Icons
- **Visualizations**: Recharts (interactive distributions & metrics), Canvas-based Zoom & Pan Viewer
- **Document Engine**: Custom HTML5/CSS Print & PDF Clinical Report Renderer

### Backend & AI Services
- **Framework**: FastAPI (Python 3.10+), Uvicorn ASGI
- **Deep Learning**: PyTorch 2.0+, Torchvision, EfficientNet-B3
- **Image Processing**: OpenCV (cv2), SciPy, NumPy, Scikit-Image
- **Database ORM**: SQLAlchemy 2.0, Psycopg2-binary (PostgreSQL / Supabase), SQLite3
- **Validation**: Pydantic v2 schemas

### Engineering & Simulation
- **MathWorks**: MATLAB R2022b+, Simulink, Stateflow

---

## 11. Installation & Getting Started

### Prerequisites
- **Python**: Version `3.10`, `3.11`, or `3.12`
- **Node.js**: Version `18.0` or higher
- **Git**: Installed and configured

### 🚀 Option A: One-Click Launcher (Recommended)

Clone the repository and run the automated launcher:

```bash
# 1. Clone repository
git clone https://github.com/shrikargs7-cloud/ocupulse-dr.git
cd ocupulse-dr

# 2. Run the unified launcher script (macOS / Linux)
chmod +x run_ocupulse.sh
./run_ocupulse.sh
```

*For Windows users:*
```bat
run_ocupulse.bat
```

The script automatically sets up the Python virtual environment, installs backend and frontend dependencies, starts the FastAPI server on port `8000`, and launches the Vite client on port `5173`.

---

### 🛠️ Option B: Manual Setup

#### 1. Environment Configuration
Copy the provided environment template:
```bash
cp .env.example .env
```
*(Optional: Open `.env` and fill in your Supabase PostgreSQL connection URI if connecting to the cloud).*

#### 2. Backend Setup
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Start backend server
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 3. Frontend Setup
```bash
# Open a new terminal
cd frontend

# Install node dependencies
npm install

# Start Vite dev server
npm run dev
```

Open your browser at **`http://localhost:5173`**. Interactive API docs will be live at **`http://localhost:8000/docs`**.

---

## 12. REST API Documentation

| Method | Endpoint | Description | Request Type |
|---|---|---|---|
| `GET` | `/api/health` | System health check & model readiness | None |
| `POST` | `/api/analyze` | Primary diagnostic endpoint (analyzes fundus scan) | `multipart/form-data` |
| `GET` | `/api/demo-samples` | Retrieves preloaded benchmark demo scans | None |
| `GET` | `/api/appointments` | Lists scheduled ophthalmology appointments | None |
| `POST` | `/api/appointments` | Creates or manually books a clinical referral | `application/json` |
| `GET` | `/api/history` | Retrieves historical analysis sessions | Query params |
| `GET` | `/api/history/{id}` | Fetches full report data for an analysis | Path param |

---

## 13. Verification & Quality Assurance

To execute automated backend test suites:

```bash
source venv/bin/activate
PYTHONPATH=. pytest backend/tests -v
```

Verified test coverage includes:
- ✅ Retinal circular ROI isolation boundary conditions
- ✅ Multi-scale vessel enhancement and Frangi filter stability
- ✅ Zhang-Suen skeleton convergence and Euler characteristic preservation
- ✅ Clinical Lesion-Gated Reconciliation accuracy on normal vs diseased eyes
- ✅ Appointment auto-booking trigger integrity (guarded for Grade $\ge 2$)
- ✅ Database failover between PostgreSQL and SQLite

---

## 14. License

Distributed under the **MIT License**. See [LICENSE](LICENSE) for more information.

---

<p align="center">
  <b>Developed for Advanced Clinical Ophthalmology, Telemedicine Screening, and Automated Retinopathy Triage.</b><br>
  <sub>OcuPulse Project Repository — 2026</sub>
</p>
