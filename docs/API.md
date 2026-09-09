# OcuPulse API Documentation

OcuPulse provides a comprehensive RESTful API built on **FastAPI** with OpenAPI (Swagger) specifications at `/docs`.

---

## 1. System Health & Readiness

### `GET /api/health`
Returns the operational health of the server, AI runtimes, and database dialect.

**Response**:
```json
{
  "status": "ok",
  "app": "OcuPulse",
  "database": {
    "status": "connected",
    "dialect": "postgresql",
    "is_supabase": true,
    "url_masked": "postgresql://postgres:***@db.ref.supabase.co:5432/postgres"
  }
}
```

---

## 2. Retinal Analysis Engine

### `POST /api/analyze`
Submits a fundus image (or demo sample ID) for full quantitative and qualitative analysis.

**Parameters (Multipart Form)**:
- `file` (optional): Image file (`.png`, `.jpg`, `.jpeg`, `.tif`).
- `demo_id` (optional): String identifier (`demo_normal`, `demo_dense`, `demo_sparse`).
- `patient_id` (optional): Patient reference ID (e.g. `PID-2026-0812`).

**Response (`AnalysisResponse`)**:
```json
{
  "success": true,
  "analysis_id": "OCU-20260908-153051-4CDF7A",
  "timestamp": "2026-09-08T15:30:51.123456Z",
  "filename": "fundus_scan.png",
  "metrics": {
    "vessel_density": 10.45,
    "vessel_area": 18420,
    "vessel_length_pixels": 8940,
    "branch_points": 142,
    "endpoints": 98,
    "average_vessel_width_px": 2.06,
    "fractal_dimension": 1.482
  },
  "quality": {
    "score": 0.88,
    "label": "Good",
    "description": "Image quality is good for clinical screening."
  },
  "summary": {
    "headline": "Normal Retinal Vasculature",
    "screening_status": "Automated Geometry Screening",
    "recommendation": "Vessel caliber and branching conform to screening thresholds. Continue annual screening."
  },
  "images": {
    "original": "data:image/png;base64,...",
    "enhanced": "data:image/png;base64,...",
    "vessel_mask": "data:image/png;base64,...",
    "vessel_overlay": "data:image/png;base64,...",
    "skeleton": "data:image/png;base64,..."
  }
}
```

---

## 3. Telemedicine Simulink Workflow Engine

### `POST /api/v1/simulink/optimize`
Runs the mathematical queuing model to optimize district-scale screening deployments.

**Request Body (`SimulinkParams`)**:
```json
{
  "patient_volume": 100000,
  "bandwidth_mbps": 100.0,
  "processing_throughput": 30.0,
  "review_capacity": 50,
  "operating_hours": 8
}
```

**Response (`SimulinkResult`)**:
```json
{
  "simulation_id": 1,
  "total_cost": 504000.0,
  "cost_per_patient": 5.04,
  "throughput_per_day": 34332,
  "backlog_after_year": 0,
  "optimized_params": {
    "bandwidth_mbps": 100.0,
    "processing_throughput": 30.0,
    "review_capacity": 50,
    "operating_hours": 8
  },
  "recommendations": [
    "Current network bandwidth and processing throughput are sufficient to absorb annual patient screening demand.",
    "Capacity surplus allows expanding screening coverage to adjacent community healthcare centers."
  ]
}
```

### `GET /api/v1/simulink/simulations`
Returns historical simulation runs saved to the database.

### `GET /api/v1/simulink/presets`
Returns standard district deployment templates:
- `rural_phc`: 25,000 screening population, 15 Mbps uplink, 10 reviewers.
- `district_hub`: 100,000 screening population, 100 Mbps uplink, 50 reviewers.
- `state_grid`: 500,000 screening population, 500 Mbps uplink, 180 reviewers.

---

## 4. Models & Diagnostics

### `GET /api/v1/model-info`
Returns clinical validation metrics for deployed models:
- **DR Classifier**: EfficientNet-B3 (Accuracy: 87%, Sensitivity: 92%, Specificity: 88%, AUC: 0.95).
- **Vessel Segmentation**: Multi-scale morphological top-hat & U-Net (Dice: 0.85, IoU: 0.78 on DRIVE).
- **Lesion Detection**: Sub-pixel microaneurysm, exudate, hemorrhage, and neovascularization models.
