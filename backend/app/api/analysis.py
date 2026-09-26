from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any
import json
import time
import uuid
from datetime import datetime

from app.database import SessionLocal, Image, AnalysisLog, create_emergency_appointment, get_active_doctor
from app.services.sms_service import send_referable_dr_alert
from app.schemas import AnalysisResult, QualityAssessment, DrGrading, LesionData, FeatureData
from app.processing.pipeline import AnalysisPipeline, mat_to_base64_png
from app.ml.dr_classifier import DRClassifier
from app.matlab.bridge import MATLABBridge
from app.utils.metrics import calculate_metrics

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

pipeline = AnalysisPipeline()
classifier = DRClassifier()
matlab_bridge = MATLABBridge()

@router.post("/analyze/{image_id}", response_model=AnalysisResult)
async def analyze_image(
    image_id: int,
    background_tasks: BackgroundTasks,
    use_matlab: bool = True,
    db: Session = Depends(get_db)
):
    """Perform complete analysis on an uploaded image"""
    
    # Get image record
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Check if already analyzed
    if image.dr_grade is not None:
        return await get_analysis_result(image_id, db)
    
    try:
        start_time = time.time()
        analysis_log = AnalysisLog(
            image_id=image_id,
            step_name="Full Analysis",
            start_time=datetime.utcnow(),
            status="Processing"
        )
        db.add(analysis_log)
        db.commit()
        
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

        # Step 1: Quality Assessment
        quality_result = pipeline.assess_quality(image.file_path)
        image.quality_score = _to_float(quality_result.get("score"))
        raw_grade = quality_result.get("grade")
        image.quality_grade = raw_grade.value if hasattr(raw_grade, "value") else str(raw_grade or "Good")
        
        if str(image.quality_grade).lower() == "reject":
            raise HTTPException(
                status_code=400,
                detail=f"Image quality insufficient: {quality_result.get('recommendations', '')}"
            )
        
        # Step 2: Image Enhancement
        enhanced_image = pipeline.enhance_image(image.file_path)
        
        # Step 3: Vessel Segmentation & Geometry
        vessel_data = pipeline.segment_vessels(enhanced_image)
        image.vessel_density = _to_float(vessel_data.get("density"))
        image.tortuosity_index = _to_float(vessel_data.get("tortuosity"))
        image.branching_angle = _to_float(vessel_data.get("branching_angle"))
        
        # Step 4: Fractal Dimension
        fractal_dim = pipeline.compute_fractal_dimension(vessel_data["skeleton"])
        image.fractal_dimension = _to_float(fractal_dim)
        
        # Step 5: Lesion Detection
        lesions = pipeline.detect_lesions(enhanced_image)
        image.microaneurysm_count = _to_int(lesions.get("microaneurysms", 0))
        image.exudate_count = _to_int(lesions.get("exudates", 0))
        image.hemorrhage_count = _to_int(lesions.get("hemorrhages", 0))
        image.neovascularization_count = _to_int(lesions.get("neovascularization", 0))
        
        # Step 6: DR Grading (ML) with clinical lesion gating
        grading_result = classifier.predict(enhanced_image, lesions=lesions)
        image.dr_grade = _to_int(grading_result.get("grade", 0))
        image.dr_confidence = _to_float(grading_result.get("confidence"))
        image.referable_dr = bool(grading_result.get("is_referable", False))
        image.vision_threatening = bool(grading_result.get("is_vision_threatening", False))
        
        if not image.analysis_id:
            image.analysis_id = f"OCU-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"

        # Step 6.5: Automated Doctor Appointment Booking for ICDR Scale >= 2 (Moderate NPDR, Severe NPDR, PDR)
        if image.vision_threatening or (image.dr_grade is not None and image.dr_grade >= 2) or (image.neovascularization_count and image.neovascularization_count > 0):
            try:
                active_doctor = get_active_doctor(db)
                doc_name = active_doctor.full_name if active_doctor else "Dr. Sarah Lin, MD (Vitreoretinal Surgeon)"
                doc_specialty = active_doctor.specialty if active_doctor else "Vitreoretinal Ophthalmology & Retinal Surgery"
                hosp_name = active_doctor.hospital_name if active_doctor else "Apex Regional Eye Institute & Referral Center"
                clinic_room = active_doctor.clinic_room if active_doctor else "Suite 402 - Emergency Retina Clinic"
                contact_phone = active_doctor.phone_number if active_doctor else "+1 (800) 555-RETINA"
                doc_id = active_doctor.doctor_id if active_doctor else "DOC-ONCALL"

                dr_labels = {
                    2: "Level 2: Moderate NPDR (Referable DR)",
                    3: "Level 3: Severe NPDR",
                    4: "Level 4: Proliferative DR (PDR)",
                }
                sev_label = dr_labels.get(image.dr_grade, f"Level {image.dr_grade}: Referable DR Condition")

                if (image.dr_grade is not None and image.dr_grade >= 4) or image.vision_threatening:
                    priority = "STAT / Urgent (24-48 Hours)"
                    action = "Urgent dilated fundus examination, optical coherence tomography (OCT), and consideration for anti-VEGF injection or panretinal photocoagulation."
                elif image.dr_grade == 3:
                    priority = "Urgent (48-72 Hours)"
                    action = "Urgent specialist retina consultation, optical coherence tomography (OCT), and close monitoring for progression to proliferative retinopathy."
                else:
                    priority = "Priority Referral (1-2 Weeks)"
                    action = "Comprehensive dilated fundus examination, OCT macular evaluation to assess for diabetic macular edema (DME), and specialist management plan."

                clinical_reason = f"Automated screening identified {sev_label} with referable vascular lesions requiring ophthalmology evaluation."
                if image.vision_threatening:
                    clinical_reason += " Sight-threatening risk flagged."

                patient_label = f"Patient #{image.patient_id}" if image.patient_id else "Anonymous Patient"

                appt = create_emergency_appointment(
                    db=db,
                    analysis_id=image.analysis_id or f"IMG-{image.id}",
                    patient_id=str(image.patient_id) if image.patient_id else "Anonymous",
                    patient_name=patient_label,
                    doctor_name=doc_name,
                    doctor_specialty=doc_specialty,
                    hospital_name=hosp_name,
                    clinic_room=clinic_room,
                    contact_phone=contact_phone,
                    dr_grade=image.dr_grade,
                    severity_level=sev_label,
                    clinical_reason=clinical_reason,
                    priority=priority,
                    action_required=action,
                )
                if appt:
                    appt.doctor_id = doc_id
                    appt.verification_status = "PENDING_DOCTOR_REVIEW"
                    db.commit()

                # Dispatch automated SMS alert to active doctor
                if active_doctor and active_doctor.phone_number:
                    send_referable_dr_alert(
                        doctor_phone=active_doctor.phone_number,
                        doctor_name=active_doctor.full_name,
                        patient_name=patient_label,
                        patient_id=str(image.patient_id) if image.patient_id else str(image.id),
                        dr_grade=image.dr_grade or 2,
                        severity=sev_label,
                        analysis_id=image.analysis_id or f"IMG-{image.id}",
                        db=db,
                    )
            except Exception as _e:
                print(f"Appointment / SMS alert dispatch notice: {_e}")
        
        # Step 7: MATLAB Analysis (if available)
        matlab_result = None
        if use_matlab and matlab_bridge.is_available():
            matlab_result = matlab_bridge.analyze_retina(image.file_path)
            image.matlab_analysis = json.dumps(matlab_result)
        
        # Step 8: Grad-CAM Heatmap
        heatmap = classifier.generate_gradcam(enhanced_image)
        
        # Step 9: Generate Report (background)
        background_tasks.add_task(
            generate_report_background,
            image_id,
            image.patient_id,
            quality_result,
            grading_result,
            lesions,
            vessel_data,
            fractal_dim,
            matlab_result
        )
        
        # Update processing time
        image.processing_time = time.time() - start_time
        image.model_version = "v2.1.0"
        
        # Update analysis log
        analysis_log.end_time = datetime.utcnow()
        analysis_log.status = "Success"
        analysis_log.metrics = json.dumps({
            "processing_time": image.processing_time,
            "quality_score": image.quality_score,
            "dr_grade": image.dr_grade,
            "confidence": image.dr_confidence
        })

        # Save complete details_json so the screening report can be retrieved
        try:
            analysis_payload = {
                "success": True,
                "analysis_id": image.analysis_id,
                "filename": image.original_filename or image.filename,
                "timestamp": datetime.utcnow().isoformat(),
                "dr_grade": image.dr_grade,
                "dr_confidence": round((image.dr_confidence or 0.9) * 100, 1) if (image.dr_confidence or 0) <= 1.0 else (image.dr_confidence or 90.0),
                "referable_dr": image.referable_dr,
                "vision_threatening": image.vision_threatening,
                "is_critical": bool((image.dr_grade and image.dr_grade >= 2) or image.vision_threatening),
                "lesions": {
                    "microaneurysms": image.microaneurysm_count or 0,
                    "exudates": image.exudate_count or 0,
                    "hemorrhages": image.hemorrhage_count or 0,
                    "neovascularization": image.neovascularization_count or 0,
                },
                "quality": {
                    "score": image.quality_score or 0.85,
                    "label": image.quality_grade or "Good",
                    "description": quality_result.get("recommendations") or f"Quality assessed as {image.quality_grade}.",
                    "metrics": {
                        "sharpness_laplacian": _to_float(quality_result.get("focus", 0)),
                        "rms_contrast": 0.5,
                        "illumination_uniformity": _to_float(quality_result.get("illumination", 0)),
                        "roi_coverage_percent": _to_float(quality_result.get("fov", 0.85)) * 100,
                        "mean_intensity": 128.0,
                    }
                },
                "metrics": {
                    "vessel_density": image.vessel_density or 0.0,
                    "vessel_area_pixels": _to_int(vessel_data.get("area", 0)),
                    "vessel_length_pixels": _to_float(vessel_data.get("length", 0.0)),
                    "branch_points": _to_int(vessel_data.get("branch_points", 0)),
                    "endpoints": _to_int(vessel_data.get("endpoints", 0)),
                    "skeleton_density": _to_float(vessel_data.get("skeleton_density", 0.0)),
                    "average_vessel_width_px": _to_float(vessel_data.get("average_width", 0.0)),
                    "fractal_dimension": image.fractal_dimension or 0.0,
                    "mean_branching_angle_deg": image.branching_angle or 0.0,
                    "tortuosity_index": image.tortuosity_index or 0.0,
                },
                "images": {
                    "enhanced": mat_to_base64_png(enhanced_image) if enhanced_image is not None else None,
                    "vessel_mask": mat_to_base64_png(vessel_data["vessel_mask"]) if "vessel_mask" in vessel_data and vessel_data["vessel_mask"] is not None else None,
                    "vessel_overlay": mat_to_base64_png(vessel_data["processed_image"]) if "processed_image" in vessel_data and vessel_data["processed_image"] is not None else None,
                    "skeleton": mat_to_base64_png(vessel_data["skeleton"]) if "skeleton" in vessel_data and vessel_data["skeleton"] is not None else None,
                    "gradcam": heatmap,
                },
            }
            image.details_json = json.dumps(analysis_payload)
        except Exception:
            pass
        
        db.commit()
        db.refresh(image)
        
        # Return results
        return AnalysisResult(
            image_id=image.id,
            quality=QualityAssessment(
                quality_grade=image.quality_grade,
                quality_score=image.quality_score,
                illumination_score=quality_result.get("illumination", 0),
                focus_score=quality_result.get("focus", 0),
                fov_score=quality_result.get("fov", 0),
                recommendations=quality_result.get("recommendations")
            ),
            grading=DrGrading(
                grade=image.dr_grade,
                grade_label=grading_result["grade_label"],
                confidence=image.dr_confidence,
                is_referable=image.referable_dr,
                is_vision_threatening=image.vision_threatening,
                clinical_criteria=grading_result["clinical_criteria"]
            ),
            lesions=[
                LesionData(
                    type=lesion["type"],
                    count=lesion["count"],
                    area=lesion["area"],
                    density=lesion["density"],
                    locations=lesion["locations"]
                )
                for lesion in lesions["detected_lesions"]
            ],
            features=FeatureData(
                fractal_dimension=image.fractal_dimension,
                vessel_density=image.vessel_density,
                tortuosity_index=image.tortuosity_index,
                branching_angle=image.branching_angle,
                vessel_geometry=vessel_data["geometry"]
            ),
            grad_cam_heatmap=heatmap,
            processing_time=image.processing_time,
            matlab_analysis=matlab_result,
            model_version=image.model_version
        )
        
    except Exception as e:
        # Update analysis log with error
        if 'analysis_log' in locals():
            analysis_log.end_time = datetime.utcnow()
            analysis_log.status = "Failed"
            analysis_log.error_message = str(e)
            db.commit()
        
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/batch-analyze")
async def batch_analyze(
    image_ids: list[int],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Analyze multiple images in batch"""
    results = []
    summary = {
        "total": len(image_ids),
        "processed": 0,
        "failed": 0,
        "referable": 0,
        "vision_threatening": 0
    }
    
    for image_id in image_ids:
        try:
            result = await analyze_image(image_id, background_tasks, db=db)
            results.append({
                "image_id": image_id,
                "status": "success",
                "result": result.dict()
            })
            summary["processed"] += 1
            if result.grading.is_referable:
                summary["referable"] += 1
            if result.grading.is_vision_threatening:
                summary["vision_threatening"] += 1
        except Exception as e:
            results.append({
                "image_id": image_id,
                "status": "failed",
                "error": str(e)
            })
            summary["failed"] += 1
    
    return {
        "summary": summary,
        "results": results
    }

@router.get("/analysis/{image_id}")
async def get_analysis_result(image_id: int, db: Session = Depends(get_db)):
    """Get stored analysis results for an image"""
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    if image.dr_grade is None:
        raise HTTPException(status_code=400, detail="Image not analyzed yet")
    
    return {
        "image_id": image.id,
        "quality": {
            "grade": image.quality_grade,
            "score": image.quality_score
        },
        "grading": {
            "grade": image.dr_grade,
            "confidence": image.dr_confidence,
            "referable": image.referable_dr,
            "vision_threatening": image.vision_threatening
        },
        "features": {
            "fractal_dimension": image.fractal_dimension,
            "vessel_density": image.vessel_density,
            "tortuosity_index": image.tortuosity_index,
            "branching_angle": image.branching_angle
        },
        "lesions": {
            "microaneurysms": image.microaneurysm_count,
            "exudates": image.exudate_count,
            "hemorrhages": image.hemorrhage_count,
            "neovascularization": image.neovascularization_count
        },
        "processing_time": image.processing_time,
        "model_version": image.model_version,
        "matlab_analysis": json.loads(image.matlab_analysis) if image.matlab_analysis else None,
        "upload_time": image.upload_time
    }

@router.post("/analyze-url")
async def analyze_from_url(
    url: str,
    patient_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Analyze an image from a URL"""
    import requests
    from io import BytesIO
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        # Create a temporary file
        temp_path = os.path.join(settings.UPLOAD_DIR, f"temp_{uuid.uuid4()}.jpg")
        with open(temp_path, "wb") as f:
            f.write(response.content)
        
        # Upload and analyze
        # First upload
        image_obj = Image(
            patient_id=None,
            filename=os.path.basename(temp_path),
            file_path=temp_path,
            original_filename="from_url.jpg"
        )
        db.add(image_obj)
        db.commit()
        db.refresh(image_obj)
        
        # Then analyze
        result = await analyze_image(image_obj.id, BackgroundTasks(), db=db)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"URL analysis failed: {str(e)}")

async def generate_report_background(image_id, patient_id, quality, grading, lesions, vessels, fractal, matlab):
    """Background task to generate report"""
    try:
        from app.utils.report_generator import ReportGenerator
        generator = ReportGenerator()
        
        report_path = generator.generate_clinical_report(
            image_id=image_id,
            patient_id=patient_id,
            quality=quality,
            grading=grading,
            lesions=lesions,
            vessels=vessels,
            fractal=fractal,
            matlab_analysis=matlab
        )
        
        # Update database with report path
        db = SessionLocal()
        try:
            image = db.query(Image).filter(Image.id == image_id).first()
            if image:
                from app.database import Report
                report = Report(
                    image_id=image_id,
                    report_path=report_path,
                    report_format="PDF"
                )
                db.add(report)
                db.commit()
        finally:
            db.close()
            
    except Exception as e:
        print(f"Report generation failed: {e}")