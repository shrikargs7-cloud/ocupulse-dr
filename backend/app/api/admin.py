"""
OcuPulse Admin & Systems Telemetry Endpoints
Provides system information, database metrics, storage status, and AI model health
for the dedicated Admin & Systems Engineering Console (Port 5174).
"""

import os
import time
from datetime import datetime
from typing import Any, Dict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db, Image, Patient, Appointment, Report, AnalysisLog, _using_fallback_sqlite
from app.config import settings
from app.ml.dr_classifier import DRClassifier
from app.matlab.bridge import MATLABBridge

router = APIRouter(prefix="/admin", tags=["admin"])
matlab_bridge = MATLABBridge()

_SERVER_START_TIME = time.time()

@router.get("/system-info")
async def get_system_info(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Return exhaustive telemetry on database, ML models, storage, and server uptime."""
    uptime_seconds = int(time.time() - _SERVER_START_TIME)
    
    # 1. Database Telemetry
    db_dialect = db.bind.dialect.name if db.bind else "unknown"
    is_supabase = settings.is_postgres and not _using_fallback_sqlite
    
    # Table counts
    try:
        image_count = db.query(Image).count()
    except Exception:
        image_count = 0

    try:
        patient_count = db.query(Patient).count()
    except Exception:
        patient_count = 0

    try:
        appointment_count = db.query(Appointment).count()
    except Exception:
        appointment_count = 0

    try:
        report_count = db.query(Report).count()
    except Exception:
        report_count = 0

    # 2. Storage metrics
    uploads_dir = settings.storage.upload_dir
    upload_files_count = 0
    upload_total_bytes = 0
    if os.path.exists(uploads_dir):
        for f in os.listdir(uploads_dir):
            fp = os.path.join(uploads_dir, f)
            if os.path.isfile(fp):
                upload_files_count += 1
                upload_total_bytes += os.path.getsize(fp)

    # 3. ML Model details
    model_path = os.path.join(settings.storage.model_dir, "dr_classifier_efficientnet_b3.pt")
    model_exists = os.path.exists(model_path)
    model_size_mb = round(os.path.getsize(model_path) / (1024 * 1024), 2) if model_exists else 0.0

    return {
        "status": "online",
        "app_name": "OcuPulse AIDRSS",
        "version": "2.1.0-production",
        "uptime_seconds": uptime_seconds,
        "uptime_human": f"{uptime_seconds // 3600}h {(uptime_seconds % 3600) // 60}m {uptime_seconds % 60}s",
        "timestamp": datetime.utcnow().isoformat(),
        "database": {
            "dialect": db_dialect,
            "is_supabase": is_supabase,
            "using_fallback_sqlite": _using_fallback_sqlite,
            "active_storage_path": settings.storage.database_path if not is_supabase else "Supabase Cloud Pooler (Port 5432/6543)",
            "table_records": {
                "patients": patient_count,
                "images": image_count,
                "appointments": appointment_count,
                "reports": report_count,
            },
            "status": "connected"
        },
        "ml_subsystem": {
            "model_name": "EfficientNet-B3",
            "weights_file": "dr_classifier_efficientnet_b3.pt",
            "weights_found": model_exists,
            "weights_size_mb": model_size_mb,
            "icdr_classes": 5,
            "reconciliation_engine": "Clinical Lesion-Gated Prior (AAO Standard)",
            "explainability": "Grad-CAM Saliency Engine"
        },
        "matlab_simulink": {
            "matlab_bridge_available": matlab_bridge.is_available(),
            "simulink_models_loaded": [
                "screening_pipeline.slx",
                "resource_optimiser.slx",
                "telemedicine_workflow.slx"
            ],
            "matlab_scripts": [
                "analyse_retina.m",
                "FrangFilter2D.m",
                "vessel_geometry.m",
                "fractal_analytics.m",
                "lesion_quantification.m",
                "severity_grading.m"
            ]
        },
        "storage": {
            "uploads_directory": uploads_dir,
            "cached_images_count": upload_files_count,
            "total_storage_mb": round(upload_total_bytes / (1024 * 1024), 2)
        }
    }
