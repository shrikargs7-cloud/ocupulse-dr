from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from contextlib import asynccontextmanager

from .api import endpoints, image_upload, analysis, reports, legacy, admin, doctor
from .database import engine, Base, check_database_connection, init_db
from .config import settings

import asyncio

def _safe_init_db():
    try:
        init_db()
        print("✅ Database tables verified and initialized in background.")
    except Exception as e:
        print(f"⚠️ Database table initialization notice: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    db_desc = "PostgreSQL (Supabase)" if settings.is_postgres else "SQLite"
    print(f"🚀 Starting OcuPlus AIDRSS with {db_desc} database...")
    os.makedirs(settings.storage.upload_dir, exist_ok=True)
    os.makedirs(settings.storage.report_dir, exist_ok=True)
    
    # Initialize DB in worker thread so Uvicorn binds and accepts requests instantly
    asyncio.create_task(asyncio.to_thread(_safe_init_db))
    yield
    # Shutdown
    print("👋 Shutting down OcuPlus AIDRSS...")

app = FastAPI(
    title="OcuPlus AIDRSS - AI-Driven Diabetic Retinopathy Screening System",
    description="""
    ## Deterministic Computer Vision + Explainable AI for DR Screening
    
    ### Features:
    - **Zero Hallucination**: Pure geometry and fractal mathematics
    - **Explainable AI**: Grad-CAM + Lesion-level evidence
    - **Clinical Validation**: 90%+ sensitivity for referable DR
    - **MATLAB Integration**: Advanced analysis pipeline
    - **Simulink Workflow**: Telemedicine optimization
    """,
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for reports
os.makedirs(settings.storage.report_dir, exist_ok=True)
app.mount("/reports", StaticFiles(directory=settings.storage.report_dir), name="reports")

# Include routers
app.include_router(endpoints.router, prefix="/api/v1", tags=["Main"])
app.include_router(image_upload.router, prefix="/api/v1", tags=["Upload"])
app.include_router(analysis.router, prefix="/api/v1", tags=["Analysis"])
app.include_router(reports.router, prefix="/api/v1", tags=["Reports"])
app.include_router(legacy.router, prefix="/api", tags=["Legacy"])
app.include_router(admin.router, prefix="/api", tags=["Admin"])
app.include_router(doctor.router, tags=["Doctor"])

@app.get("/")
async def root():
    return {
        "message": "OcuPlus AIDRSS - Diabetic Retinopathy Screening",
        "version": "1.0.0",
        "endpoints": {
            "upload": "/api/v1/upload",
            "analyze": "/api/v1/analyze/{image_id}",
            "batch": "/api/v1/batch-analyze",
            "history": "/api/v1/history",
            "report": "/api/v1/report/{image_id}",
            "simulink": "/api/v1/simulink"
        }
    }

@app.get("/health")
async def health_check():
    db_info = check_database_connection()
    return {
        "status": "healthy" if db_info["status"] == "connected" else "degraded",
        "service": "OcuPlus AIDRSS",
        "database": db_info,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)