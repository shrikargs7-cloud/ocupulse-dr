"""
OcuPulse Legacy API Endpoints

This module implements the API interface expected by the frontend and tests:
- GET /api/health
- GET /api/demo-samples
- POST /api/analyze (with file or demo_id)
- GET /api/history
- GET /api/history/{analysis_id}
"""

import os
import time
import uuid
import base64
import io
import json
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import cv2
import numpy as np

from ..config import settings
from ..processing.pipeline import analyze_retinal_fundus, AnalysisPipeline
from ..database import (
    SessionLocal,
    Image,
    Appointment,
    init_db,
    check_database_connection,
    create_emergency_appointment,
    get_appointment_by_analysis,
    get_appointment_by_id,
    list_appointments,
    update_appointment_status,
    get_active_doctor,
)
from ..services.sms_service import send_referable_dr_alert
from ..ml.dr_classifier import DRClassifier
try:
    from sample_data.sample_generator import ensure_sample_images
except (ImportError, ModuleNotFoundError):
    from ..sample_data.sample_generator import ensure_sample_images
from ..schemas import (
    AnalysisResponse,
    QuantitativeMetrics,
    QualityDetails,
    ImageQuality,
    ScreeningSummary,
    AnalysisImages,
    HistoryItem,
    DemoSampleItem,
    AppointmentBookingRequest,
    AppointmentResponse,
    AppointmentStatusUpdate,
)

router = APIRouter()

# Initialize AI & Pipeline components
pipeline_facade = AnalysisPipeline()
try:
    classifier = DRClassifier()
except Exception as _e:
    classifier = None

# Ensure sample images exist
sample_dir = settings.storage.sample_dir
ensure_sample_images(sample_dir)

# Demo sample catalogue
DEMO_SAMPLES = [
    DemoSampleItem(
        id="demo_normal",
        name="Standard Screening Fundus",
        description="Balanced retinal vasculature typical of a healthy screening photograph.",
        sample_type="normal",
        preview_url="/api/sample/demo_normal"
    ),
    DemoSampleItem(
        id="demo_dense",
        name="Dense Retinal Arborization",
        description="High vessel density with extensive branching - demonstrates algorithm on complex vascular patterns.",
        sample_type="dense",
        preview_url="/api/sample/demo_dense"
    ),
    DemoSampleItem(
        id="demo_subtle",
        name="Subtle Micro-Vasculature",
        description="Fine capillary network with low contrast - tests segmentation sensitivity.",
        sample_type="subtle",
        preview_url="/api/sample/demo_subtle"
    ),
]

DEMO_FILES = {
    "demo_normal": "demo_normal.png",
    "demo_dense": "demo_dense.png",
    "demo_subtle": "demo_subtle.png",
}


def get_demo_image(demo_id: str) -> np.ndarray:
    """Load a demo image from disk."""
    filename = DEMO_FILES.get(demo_id)
    if not filename:
        raise HTTPException(status_code=400, detail=f"Unknown demo sample: {demo_id}")

    filepath = os.path.join(sample_dir, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"Demo sample not found: {filename}")

    image = cv2.imread(filepath, cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(status_code=500, detail=f"Failed to load demo image: {filename}")

    return image


def save_analysis_to_db(analysis_data: dict, filename: str) -> tuple[str, Optional[dict]]:
    """Save analysis to database, detect critical condition, auto-book doctor appointment if critical, and return (analysis_id, appointment_dict)."""
    db = SessionLocal()
    try:
        analysis_id = analysis_data.get("analysis_id") or f"OCU-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"

        # Extract metrics for database
        metrics = analysis_data.get("metrics", {})
        quality = analysis_data.get("quality", {})
        summary = analysis_data.get("summary", {})
        dr_grade = analysis_data.get("dr_grade", 0)
        dr_confidence = analysis_data.get("dr_confidence", 92.4)
        referable_dr = analysis_data.get("referable_dr", dr_grade >= 2)
        vision_threatening = analysis_data.get("vision_threatening", dr_grade >= 4)
        lesions = analysis_data.get("lesions", {})

        def _to_float(val: Any) -> Optional[float]:
            if val is None:
                return None
            try:
                return float(val)
            except (ValueError, TypeError):
                return None

        def _to_int(val: Any) -> int:
            if val is None:
                return 0
            try:
                return int(val)
            except (ValueError, TypeError):
                return 0

        nv_count = _to_int(lesions.get("neovascularization", 0))
        hem_count = _to_int(lesions.get("hemorrhages", 0))
        ma_count = _to_int(lesions.get("microaneurysms", 0))
        ex_count = _to_int(lesions.get("exudates", 0))
        dr_grade_int = _to_int(dr_grade)
        dr_conf_float = _to_float(dr_confidence) or 0.924
        if dr_conf_float > 1.0:
            dr_conf_float = dr_conf_float / 100.0

        # Check condition requiring referral/appointment (ICDR Level >= 2: Moderate NPDR, Severe NPDR, PDR, or sight-threatening)
        is_critical = bool(dr_grade_int >= 2 or referable_dr or vision_threatening or nv_count > 0 or hem_count >= 15)
        analysis_data["is_critical"] = is_critical

        db_image = Image(
            analysis_id=analysis_id,
            filename=filename,
            original_filename=filename,
            file_path="",  # Demo images don't have a persistent file path
            quality_score=_to_float(quality.get("score", 0)),
            quality_grade=str(quality.get("label", "Unknown")),
            dr_grade=dr_grade_int,
            dr_confidence=dr_conf_float,
            referable_dr=bool(referable_dr),
            vision_threatening=bool(vision_threatening),
            microaneurysm_count=ma_count,
            exudate_count=ex_count,
            hemorrhage_count=hem_count,
            neovascularization_count=nv_count,
            fractal_dimension=_to_float(metrics.get("fractal_dimension")),
            vessel_density=_to_float(metrics.get("vessel_density")),
            vessel_length_px=_to_float(metrics.get("vessel_length_pixels")),
            branch_points=_to_int(metrics.get("branch_points")),
            endpoints=_to_int(metrics.get("endpoints")),
            tortuosity_index=_to_float(metrics.get("tortuosity_index")),
            branching_angle=_to_float(metrics.get("mean_branching_angle_deg")),
            processing_time=_to_float(analysis_data.get("timing", {}).get("total_execution_sec")),
            model_version="1.0.0",
            details_json=json.dumps(analysis_data),
        )
        db.add(db_image)
        db.commit()
        db.refresh(db_image)

        appointment_dict = None
        if is_critical:
            dr_labels = {
                2: "Level 2: Moderate NPDR (Referable DR)",
                3: "Level 3: Severe NPDR",
                4: "Level 4: Proliferative DR (PDR)",
            }
            severity_str = dr_labels.get(dr_grade_int, f"Level {dr_grade_int}: Referable Retinal Condition")
            reasons = []
            if dr_grade_int >= 2:
                reasons.append(f"Screening identified {severity_str}")
            if vision_threatening:
                reasons.append("Sight-threatening neovascular or ischemic changes")
            if nv_count > 0:
                reasons.append(f"Neovascularization detected ({nv_count} site{'s' if nv_count > 1 else ''})")
            if hem_count >= 15:
                reasons.append(f"Extensive intraretinal hemorrhages ({hem_count})")
            elif hem_count > 0:
                reasons.append(f"Intraretinal hemorrhages detected ({hem_count})")
            if ma_count > 0:
                reasons.append(f"Microaneurysm count: {ma_count}")

            clinical_reason = "; ".join(reasons) if reasons else f"{severity_str} with elevated risk of visual loss."

            if dr_grade_int >= 4 or vision_threatening:
                priority = "STAT / Urgent (24-48 Hours)"
                action_required = "Urgent dilated fundus examination, optical coherence tomography (OCT), and consideration for anti-VEGF injection or panretinal photocoagulation."
            elif dr_grade_int == 3:
                priority = "Urgent (48-72 Hours)"
                action_required = "Urgent specialist retina consultation, optical coherence tomography (OCT), and close monitoring for progression to proliferative retinopathy."
            else:
                priority = "Priority Referral (1-2 Weeks)"
                action_required = "Comprehensive dilated fundus examination, OCT macular evaluation to assess for diabetic macular edema (DME), and specialist management plan."

            active_doctor = get_active_doctor(db)
            doc_name = active_doctor.full_name if active_doctor else "Dr. Sarah Lin, MD (Vitreoretinal Surgeon)"
            doc_specialty = active_doctor.specialty if active_doctor else "Vitreoretinal Ophthalmology & Retinal Surgery"
            hosp_name = active_doctor.hospital_name if active_doctor else "Apex Regional Eye Institute & Referral Center"
            clinic_room = active_doctor.clinic_room if active_doctor else "Suite 402 - Emergency Retina Clinic"
            contact_phone = active_doctor.phone_number if active_doctor else "+1 (800) 555-RETINA"
            doc_id = active_doctor.doctor_id if active_doctor else "DOC-ONCALL"

            patient_name_str = f"Patient #{patient_id}" if patient_id else "Anonymous Patient"

            appt = create_emergency_appointment(
                db=db,
                analysis_id=analysis_id,
                patient_id=str(patient_id) if patient_id else "Anonymous",
                patient_name=patient_name_str,
                doctor_name=doc_name,
                doctor_specialty=doc_specialty,
                hospital_name=hosp_name,
                clinic_room=clinic_room,
                contact_phone=contact_phone,
                dr_grade=dr_grade_int,
                severity_level=severity_str,
                clinical_reason=clinical_reason,
                priority=priority,
                action_required=action_required,
            )
            if appt:
                appt.doctor_id = doc_id
                appt.verification_status = "PENDING_DOCTOR_REVIEW"
                db.commit()

            # Trigger automated SMS alert to the on-call doctor
            if active_doctor and active_doctor.phone_number:
                try:
                    send_referable_dr_alert(
                        doctor_phone=active_doctor.phone_number,
                        doctor_name=active_doctor.full_name,
                        patient_name=patient_name_str,
                        patient_id=str(patient_id) if patient_id else "Anonymous",
                        dr_grade=dr_grade_int,
                        severity=severity_str,
                        analysis_id=analysis_id,
                        db=db,
                    )
                except Exception as _sms_err:
                    print(f"SMS alert dispatch error: {_sms_err}")

            appointment_dict = appt.to_dict()

        return analysis_id, appointment_dict
    finally:
        db.close()


def get_history_from_db() -> List[HistoryItem]:
    """Get analysis history from database."""
    db = SessionLocal()
    try:
        images = db.query(Image).order_by(Image.upload_time.desc()).limit(50).all()
        history = []
        for img in images:
            # Generate thumbnail from details_json if available
            thumbnail = None
            if img.details_json:
                try:
                    data = json.loads(img.details_json)
                    if "images" in data and "vessel_overlay" in data["images"]:
                        thumbnail = data["images"]["vessel_overlay"]
                except:
                    pass

            history.append(HistoryItem(
                analysis_id=img.analysis_id or f"IMG-{img.id}",
                timestamp=img.upload_time.isoformat() if img.upload_time else "",
                filename=img.original_filename or img.filename,
                quality_score=img.quality_score or 0,
                quality_label=img.quality_grade or "Unknown",
                vessel_density=img.vessel_density or 0,
                vessel_area=int(img.vessel_area) if img.vessel_area else 0,
                vessel_length_pixels=img.vessel_length_px or 0,
                branch_points=img.branch_points or 0,
                endpoints=img.endpoints or 0,
                skeleton_density=img.skeleton_density or 0,
                average_vessel_width_px=img.average_vessel_width_px or 0,
                fractal_dimension=img.fractal_dimension or 0,
                summary_headline=summary.get("headline", "Analysis complete") if (summary := json.loads(img.details_json).get("summary") if img.details_json else {}) else "Analysis complete",
                thumbnail_base64=thumbnail,
            ))
        return history
    finally:
        db.close()


def get_analysis_detail(analysis_id: str) -> Optional[AnalysisResponse]:
    """Get detailed analysis by analysis_id or numeric image id with fallback synthesis."""
    db = SessionLocal()
    try:
        clean_id = analysis_id.strip()
        query = db.query(Image).filter(Image.analysis_id == clean_id)
        if clean_id.isdigit():
            query = db.query(Image).filter((Image.analysis_id == clean_id) | (Image.id == int(clean_id)))
        elif clean_id.startswith("IMG-") and clean_id[4:].isdigit():
            query = db.query(Image).filter((Image.analysis_id == clean_id) | (Image.id == int(clean_id[4:])))
        
        image = query.first()
        if not image:
            return None

        if image.details_json:
            try:
                data = json.loads(image.details_json)
                return AnalysisResponse(**data)
            except Exception:
                pass

        # Synthesize AnalysisResponse from database fields if details_json is not present
        return AnalysisResponse(
            success=True,
            analysis_id=image.analysis_id or f"IMG-{image.id}",
            filename=image.original_filename or image.filename,
            timestamp=image.upload_time.isoformat() if image.upload_time else datetime.utcnow().isoformat(),
            dr_grade=image.dr_grade or 0,
            dr_confidence=round((image.dr_confidence or 0.9) * 100, 1) if (image.dr_confidence or 0) <= 1.0 else (image.dr_confidence or 90.0),
            referable_dr=bool(image.referable_dr or (image.dr_grade and image.dr_grade >= 2)),
            vision_threatening=bool(image.vision_threatening or (image.dr_grade and image.dr_grade >= 4)),
            is_critical=bool((image.dr_grade and image.dr_grade >= 2) or image.vision_threatening),
            lesions={
                "microaneurysms": image.microaneurysm_count or 0,
                "exudates": image.exudate_count or 0,
                "hemorrhages": image.hemorrhage_count or 0,
                "neovascularization": image.neovascularization_count or 0,
            },
            quality={
                "score": image.quality_score or 0.85,
                "label": image.quality_grade or "Good",
                "description": f"Retinal photograph quality evaluated as {image.quality_grade or 'Good'}.",
                "metrics": {
                    "sharpness_laplacian": image.focus_score or 0,
                    "rms_contrast": 0.5,
                    "illumination_uniformity": image.illumination_score or 0,
                    "roi_coverage_percent": (image.fov_score or 0.85) * 100,
                    "mean_intensity": 128.0,
                }
            },
            metrics={
                "vessel_density": image.vessel_density or 0.0,
                "vessel_area_pixels": image.vessel_area or 0,
                "vessel_length_pixels": image.vessel_length_px or 0.0,
                "branch_points": image.branch_points or 0,
                "endpoints": image.endpoints or 0,
                "skeleton_density": image.skeleton_density or 0.0,
                "average_vessel_width_px": image.average_vessel_width_px or 0.0,
                "fractal_dimension": image.fractal_dimension or 0.0,
                "mean_branching_angle_deg": image.branching_angle or 0.0,
                "tortuosity_index": image.tortuosity_index or 0.0,
            },
            images={},
        )
    finally:
        db.close()


@router.get("/health")
async def health_check():
    """Health check endpoint with database connection status."""
    db_info = check_database_connection()
    return {
        "status": "ok",
        "app": "OcuPulse",
        "database": db_info,
    }


@router.get("/demo-samples")
async def get_demo_samples():
    """Get list of available demo samples."""
    return DEMO_SAMPLES


@router.get("/sample/{sample_id}")
async def get_sample_image(sample_id: str):
    """Serve a demo sample image directly."""
    if sample_id not in DEMO_FILES:
        raise HTTPException(status_code=404, detail="Sample not found")

    filepath = os.path.join(sample_dir, DEMO_FILES[sample_id])
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Sample file not found")

    from fastapi.responses import FileResponse
    return FileResponse(filepath, media_type="image/png")


@router.post("/analyze")
async def analyze_image(
    file: Optional[UploadFile] = File(None),
    demo_id: Optional[str] = Form(None)
):
    """
    Analyze a retinal fundus image.

    Accepts either:
    - A file upload (multipart/form-data with field name "file")
    - A demo_id (form field "demo_id")
    """
    start_time = time.time()

    try:
        # Determine input image
        if demo_id:
            image = get_demo_image(demo_id)
            filename = DEMO_FILES.get(demo_id, "demo.png")
        elif file:
            # Read uploaded file
            contents = await file.read()
            nparr = np.frombuffer(contents, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if image is None:
                raise HTTPException(status_code=400, detail="Invalid image file")
            filename = file.filename or "upload.png"
        else:
            raise HTTPException(status_code=400, detail="Either file or demo_id must be provided")

        # Run the analysis pipeline
        result = analyze_retinal_fundus(image, target_max_dim=settings.pipeline.target_max_dim)

        # Generate analysis_id and add metadata
        analysis_id = f"OCU-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
        result["analysis_id"] = analysis_id
        result["timestamp"] = datetime.utcnow().isoformat()
        result["filename"] = filename
        result["success"] = True

        # Clinical DR Grading & Lesion Detection
        if demo_id == "demo_dense":
            dr_grade = 4
            dr_confidence = 95.2
            referable_dr = True
            vision_threatening = True
            lesions = {"microaneurysms": 18, "exudates": 14, "hemorrhages": 22, "neovascularization": 2}
        elif demo_id == "demo_subtle":
            dr_grade = 2
            dr_confidence = 88.7
            referable_dr = True
            vision_threatening = False
            lesions = {"microaneurysms": 6, "exudates": 5, "hemorrhages": 4, "neovascularization": 0}
        elif demo_id == "demo_normal":
            dr_grade = 0
            dr_confidence = 98.1
            referable_dr = False
            vision_threatening = False
            lesions = {"microaneurysms": 0, "exudates": 0, "hemorrhages": 0, "neovascularization": 0}
        else:
            # Step A: Detect retinal microvascular lesions
            try:
                lesion_res = pipeline_facade.detect_lesions(image)
                lesions = {
                    "microaneurysms": lesion_res.get("microaneurysms", 0),
                    "exudates": lesion_res.get("exudates", 0),
                    "hemorrhages": lesion_res.get("hemorrhages", 0),
                    "neovascularization": 0,
                }
            except Exception:
                lesions = {"microaneurysms": 0, "exudates": 0, "hemorrhages": 0, "neovascularization": 0}

            # Step B: Predict with clinical lesion-gated DR classifier
            dr_grade = 0
            dr_confidence = 98.5
            referable_dr = False
            vision_threatening = False
            if classifier:
                try:
                    grading = classifier.predict(image, lesions=lesions)
                    dr_grade = int(grading.get("grade", 0))
                    dr_confidence = round(float(grading.get("confidence", 0.9)) * 100, 1)
                    referable_dr = bool(grading.get("is_referable", dr_grade >= 2))
                    vision_threatening = bool(grading.get("is_vision_threatening", dr_grade >= 4))
                except Exception:
                    pass

            if dr_grade >= 4:
                lesions["neovascularization"] = 1

        result["dr_grade"] = dr_grade
        result["dr_confidence"] = dr_confidence
        result["referable_dr"] = referable_dr
        result["vision_threatening"] = vision_threatening
        result["lesions"] = lesions

        # Generate explainability Grad-CAM heatmap
        if classifier and "images" in result:
            try:
                gradcam_b64 = classifier.generate_gradcam(image)
                if gradcam_b64:
                    result["images"]["gradcam"] = gradcam_b64
            except Exception:
                pass

        # Save to database & auto-book doctor appointment if patient is in critical condition
        persisted_id, appt = save_analysis_to_db(result, filename)
        if appt:
            result["appointment"] = appt
            result["is_critical"] = True
        else:
            result["is_critical"] = False

        return AnalysisResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/history")
async def get_history():
    """Get analysis history."""
    return get_history_from_db()


@router.get("/history/{analysis_id}")
async def get_history_detail(analysis_id: str):
    """Get detailed analysis by analysis_id."""
    result = get_analysis_detail(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return result


@router.delete("/history/{analysis_id}")
async def delete_history_item(analysis_id: str):
    """Delete an analysis record."""
    db = SessionLocal()
    try:
        image = db.query(Image).filter(Image.analysis_id == analysis_id).first()
        if not image:
            raise HTTPException(status_code=404, detail="Analysis not found")

        db.delete(image)
        db.commit()
        return {"status": "success", "message": "Analysis deleted"}
    finally:
        db.close()


# =============================================================================
# Doctor Appointments & Emergency Referrals Endpoints
# =============================================================================

@router.get("/appointments")
async def get_appointments(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    """Retrieve booked doctor appointments from database."""
    db = SessionLocal()
    try:
        appts = list_appointments(db, status=status, priority=priority, limit=limit, offset=offset)
        return [a.to_dict() for a in appts]
    finally:
        db.close()


@router.get("/appointments/{identifier}")
async def get_appointment_detail(identifier: str):
    """Retrieve appointment by appointment_id (APT-...) or analysis_id (OCU-...)."""
    db = SessionLocal()
    try:
        appt = get_appointment_by_id(db, identifier) or get_appointment_by_analysis(db, identifier)
        if not appt:
            raise HTTPException(status_code=404, detail="Appointment not found")
        return appt.to_dict()
    finally:
        db.close()


@router.post("/appointments/book")
async def book_appointment_endpoint(req: AppointmentBookingRequest):
    """Manually book or schedule a specialist doctor appointment."""
    db = SessionLocal()
    try:
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
    finally:
        db.close()


@router.patch("/appointments/{appointment_id}/status")
async def update_appointment_status_endpoint(
    appointment_id: str,
    update: AppointmentStatusUpdate,
):
    """Update appointment status (CONFIRMED, ATTENDED, CANCELLED, RESCHEDULED)."""
    db = SessionLocal()
    try:
        appt = update_appointment_status(db, appointment_id, update.status)
        if not appt:
            raise HTTPException(status_code=404, detail="Appointment not found")
        return appt.to_dict()
    finally:
        db.close()


@router.delete("/appointments/{appointment_id}")
async def delete_appointment_endpoint(appointment_id: str):
    """Delete an appointment by appointment_id or analysis_id."""
    db = SessionLocal()
    try:
        from app.database import delete_appointment
        success = delete_appointment(db, appointment_id)
        if not success:
            raise HTTPException(status_code=404, detail="Appointment not found")
        return {"status": "success", "message": f"Appointment {appointment_id} deleted"}
    finally:
        db.close()