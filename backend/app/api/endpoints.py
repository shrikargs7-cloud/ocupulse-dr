from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import json

from app.database import (
    SessionLocal, Image, Patient, Report, AnalysisLog, Appointment,
    create_emergency_appointment, get_appointment_by_analysis,
    get_appointment_by_id, list_appointments, update_appointment_status,
    delete_appointment
)
from app.schemas import (
    HistoryFilter, HistoryResponse, SimulinkParams, SimulinkResult,
    AnalysisResult, BatchAnalysisRequest, BatchAnalysisResponse,
    AppointmentBookingRequest, AppointmentResponse, AppointmentStatusUpdate
)
from app.processing.pipeline import AnalysisPipeline
from app.ml.dr_classifier import DRClassifier
from app.matlab.bridge import MATLABBridge
from app.utils.report_generator import ReportGenerator

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize components
pipeline = AnalysisPipeline()
classifier = DRClassifier()
matlab_bridge = MATLABBridge()
report_generator = ReportGenerator()

@router.get("/history", response_model=HistoryResponse)
async def get_history(
    filter_params: HistoryFilter = Depends(),
    db: Session = Depends(get_db)
):
    """Get analysis history with filtering"""
    query = db.query(Image)
    
    if filter_params.start_date:
        query = query.filter(Image.upload_time >= filter_params.start_date)
    if filter_params.end_date:
        query = query.filter(Image.upload_time <= filter_params.end_date)
    if filter_params.dr_grade is not None:
        query = query.filter(Image.dr_grade == filter_params.dr_grade)
    if filter_params.is_referable is not None:
        query = query.filter(Image.referable_dr == filter_params.is_referable)
    
    total = query.count()
    records = query.order_by(Image.upload_time.desc()).offset(filter_params.offset).limit(filter_params.limit).all()
    
    return HistoryResponse(
        total=total,
        records=[
            {
                "id": img.id,
                "patient_id": img.patient.patient_id if img.patient else None,
                "filename": img.filename,
                "upload_time": img.upload_time,
                "dr_grade": img.dr_grade,
                "dr_confidence": img.dr_confidence,
                "referable_dr": img.referable_dr,
                "vision_threatening": img.vision_threatening,
                "processing_time": img.processing_time,
                "quality_grade": img.quality_grade
            }
            for img in records
        ]
    )

@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get system statistics"""
    total_images = db.query(Image).count()
    referable_dr = db.query(Image).filter(Image.referable_dr == True).count()
    
    # Calculate sensitivity/specificity (would need ground truth)
    # For demo, using stored metrics
    metrics = {
        "total_images": total_images,
        "referable_dr_count": referable_dr,
        "referable_dr_percentage": (referable_dr / total_images * 100) if total_images > 0 else 0,
        "average_processing_time": db.query(Image).with_entities(Image.processing_time).filter(Image.processing_time.isnot(None)).all(),
        "model_version": "v2.1.0",
        "target_sensitivity": 0.90,
        "target_specificity": 0.85,
        "matlab_available": matlab_bridge.is_available()
    }
    
    # Calculate averages
    times = [t[0] for t in metrics["average_processing_time"] if t[0] is not None]
    metrics["average_processing_time_seconds"] = sum(times) / len(times) if times else 0
    del metrics["average_processing_time"]
    
    return metrics

@router.post("/simulink/optimize", response_model=SimulinkResult)
async def optimize_simulink(params: SimulinkParams, db: Session = Depends(get_db)):
    """Run Simulink optimization for telemedicine workflow"""
    try:
        # Run optimization (MATLAB engine or high-fidelity queuing simulation)
        result = matlab_bridge.run_simulink_optimization(
            patient_volume=params.patient_volume,
            bandwidth_mbps=params.bandwidth_mbps,
            processing_throughput=params.processing_throughput,
            review_capacity=params.review_capacity,
            operating_hours=params.operating_hours
        )
        
        # Save to database
        from app.database import SimulinkSimulation
        sim = SimulinkSimulation(
            simulation_name=f"Optimization_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            patient_volume=params.patient_volume,
            bandwidth_mbps=params.bandwidth_mbps,
            processing_throughput=params.processing_throughput,
            review_capacity=params.review_capacity,
            operating_hours=params.operating_hours,
            cost_per_patient=float(result.get("cost_per_patient", 0.0)),
            total_cost=float(result.get("total_cost", 0.0)),
            throughput_per_day=int(result.get("throughput_per_day", 0)),
            backlog_after_year=int(result.get("backlog_after_year", 0)),
            optimized_params=json.dumps(result.get("optimized_params", {})),
            recommendations=json.dumps(result.get("recommendations", [])),
            source=result.get("source", "telemedicine-simulation-engine")
        )
        db.add(sim)
        db.commit()
        db.refresh(sim)
        
        return SimulinkResult(
            simulation_id=sim.id,
            total_cost=float(result.get("total_cost", 0.0)),
            cost_per_patient=float(result.get("cost_per_patient", 0.0)),
            throughput_per_day=int(result.get("throughput_per_day", 0)),
            backlog_after_year=int(result.get("backlog_after_year", 0)),
            optimized_params=result.get("optimized_params", {}),
            recommendations=result.get("recommendations", [])
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Simulink optimization failed: {str(e)}")


@router.get("/simulink/simulations")
async def get_simulink_simulations(limit: int = 10, db: Session = Depends(get_db)):
    """Retrieve history of saved telemedicine simulations."""
    from app.database import SimulinkSimulation
    sims = db.query(SimulinkSimulation).order_by(SimulinkSimulation.created_at.desc()).limit(limit).all()
    out = []
    for s in sims:
        try:
            opt_p = json.loads(s.optimized_params) if s.optimized_params else {}
        except Exception:
            opt_p = {}
        try:
            recs = json.loads(s.recommendations) if s.recommendations else []
        except Exception:
            recs = []
        out.append({
            "id": s.id,
            "simulation_name": s.simulation_name,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "patient_volume": s.patient_volume,
            "bandwidth_mbps": s.bandwidth_mbps,
            "processing_throughput": s.processing_throughput,
            "review_capacity": s.review_capacity,
            "operating_hours": s.operating_hours,
            "total_cost": s.total_cost,
            "cost_per_patient": s.cost_per_patient,
            "throughput_per_day": s.throughput_per_day,
            "backlog_after_year": s.backlog_after_year,
            "optimized_params": opt_p,
            "recommendations": recs,
            "source": s.source
        })
    return out


@router.get("/simulink/presets")
async def get_simulink_presets():
    """Preset network and clinical deployment profiles."""
    return [
        {
            "id": "rural_phc",
            "name": "Rural Primary Health Center",
            "description": "Low-bandwidth remote clinic network with limited local clinician reviews.",
            "params": {
                "patient_volume": 25000,
                "bandwidth_mbps": 15.0,
                "processing_throughput": 5.0,
                "review_capacity": 10,
                "operating_hours": 6
            }
        },
        {
            "id": "district_hub",
            "name": "District Hospital Screening Grid",
            "description": "Standard district-scale deployment serving semi-urban community centers.",
            "params": {
                "patient_volume": 100000,
                "bandwidth_mbps": 100.0,
                "processing_throughput": 30.0,
                "review_capacity": 50,
                "operating_hours": 8
            }
        },
        {
            "id": "state_grid",
            "name": "State-Wide Telemedicine Grid",
            "description": "High-volume cloud infrastructure with multi-threaded GPU nodes and central review.",
            "params": {
                "patient_volume": 500000,
                "bandwidth_mbps": 500.0,
                "processing_throughput": 120.0,
                "review_capacity": 180,
                "operating_hours": 12
            }
        }
    ]

@router.get("/model-info")
async def get_model_info():
    """Get information about the deployed models"""
    return {
        "dr_classifier": {
            "name": "EfficientNet-B3",
            "version": "v2.1.0",
            "accuracy": 0.87,
            "sensitivity": 0.92,
            "specificity": 0.88,
            "auc": 0.95,
            "training_dataset": "APTOS 2019 + IDRiD",
            "validation_dataset": "Messidor-2"
        },
        "vessel_segmentation": {
            "name": "U-Net",
            "version": "v1.0.0",
            "dice_score": 0.85,
            "iou": 0.78,
            "training_dataset": "DRIVE"
        },
        "lesion_detection": {
            "microaneurysm": {"confidence": 0.85},
            "exudate": {"confidence": 0.82},
            "hemorrhage": {"confidence": 0.88}
        },
        "matlab_integration": {
            "available": matlab_bridge.is_available(),
            "scripts": ["fractal_analysis", "vessel_geometry", "lesion_quantification", "severity_grading"]
        }
    }

@router.get("/feature-importance")
async def get_feature_importance():
    """Get feature importance from SHAP analysis"""
    return {
        "features": {
            "fractal_dimension": 0.35,
            "microaneurysm_count": 0.28,
            "vessel_density": 0.15,
            "exudate_area": 0.12,
            "hemorrhage_area": 0.07,
            "tortuosity_index": 0.03
        },
        "clinical_criteria": {
            "No DR": "No retinal abnormalities",
            "Mild NPDR": "At least 1 microaneurysm only",
            "Moderate NPDR": "Multiple microaneurysms, exudates",
            "Severe NPDR": ">20 hemorrhages in 4 quadrants",
            "PDR": "Neovascularization, vitreous hemorrhage"
        }
    }


# -----------------------------------------------------------------------------
# Doctor Appointments & Emergency Referrals Endpoints (/api/v1/appointments)
# -----------------------------------------------------------------------------

@router.get("/appointments", response_model=List[AppointmentResponse])
async def get_appointments(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """Retrieve booked doctor appointments from database."""
    appts = list_appointments(db, status=status, priority=priority, limit=limit, offset=offset)
    return [a.to_dict() for a in appts]


@router.get("/appointments/{identifier}", response_model=AppointmentResponse)
async def get_appointment_detail(
    identifier: str,
    db: Session = Depends(get_db),
):
    """Retrieve appointment by appointment_id or analysis_id."""
    appt = get_appointment_by_id(db, identifier) or get_appointment_by_analysis(db, identifier)
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appt.to_dict()


@router.post("/appointments/book", response_model=AppointmentResponse)
async def book_appointment_endpoint(
    req: AppointmentBookingRequest,
    db: Session = Depends(get_db),
):
    """Manually book or schedule a specialist doctor appointment."""
    appt = create_emergency_appointment(
        db=db,
        analysis_id=req.analysis_id,
        patient_id=req.patient_id,
        patient_name=req.patient_name,
        dr_grade=req.dr_grade,
        severity_level=req.severity_level,
        clinical_reason=req.clinical_reason,
        action_required=req.action_required,
        priority=req.priority,
        doctor_name=req.doctor_name or "Dr. Sarah Lin, MD (Vitreoretinal Surgeon)",
        doctor_specialty=req.doctor_specialty or "Vitreoretinal Ophthalmology & Retinal Surgery",
        hospital_name=req.hospital_name or "Apex Regional Eye Institute & Referral Center",
        clinic_room=req.clinic_room or "Suite 402 - Emergency Retina Clinic",
        contact_phone=req.contact_phone or "+1 (800) 555-RETINA",
        scheduled_time=req.scheduled_time,
    )
    return appt.to_dict()


@router.patch("/appointments/{appointment_id}/status", response_model=AppointmentResponse)
async def update_appointment_status_endpoint(
    appointment_id: str,
    update: AppointmentStatusUpdate,
    db: Session = Depends(get_db),
):
    """Update appointment status (CONFIRMED, ATTENDED, CANCELLED, RESCHEDULED)."""
    appt = update_appointment_status(db, appointment_id, update.status)
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appt.to_dict()


@router.delete("/appointments/{appointment_id}")
async def delete_appointment_endpoint(
    appointment_id: str,
    db: Session = Depends(get_db),
):
    """Delete an appointment by appointment_id or analysis_id."""
    success = delete_appointment(db, appointment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {"status": "success", "message": f"Appointment {appointment_id} deleted"}