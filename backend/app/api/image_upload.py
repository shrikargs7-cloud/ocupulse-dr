from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
import uuid
from datetime import datetime
from PIL import Image as PILImage
import cv2
import numpy as np

from ..database import SessionLocal, Image, Patient
from ..schemas import ImageUploadResponse, PatientCreate, QualityGrade
from ..processing.quality import QualityAssessor
from ..config import settings

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

quality_assessor = QualityAssessor()

@router.post("/upload", response_model=ImageUploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    patient_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Upload a fundus image for analysis"""
    
    # Validate file extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File extension {ext} not allowed. Allowed: {settings.ALLOWED_EXTENSIONS}"
        )
    
    # Check file size
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    if size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="File too large")
    
    try:
        # Read and validate image
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image file")
        
        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}{ext}"
        file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
        
        # Save file
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Get or create patient
        patient_obj = None
        if patient_id:
            patient_obj = db.query(Patient).filter(Patient.patient_id == patient_id).first()
            if not patient_obj:
                patient_obj = Patient(patient_id=patient_id)
                db.add(patient_obj)
                db.flush()
        
        # Quick quality check
        quality_result = quality_assessor.quick_assess(file_path)
        
        def _to_float(val: Any) -> Optional[float]:
            if val is None:
                return None
            try:
                return float(val)
            except (ValueError, TypeError):
                return None

        grade_val = quality_result.get("grade")
        grade_str = grade_val.value if hasattr(grade_val, "value") else str(grade_val) if grade_val else None

        # Create database entry with strictly native Python primitives
        analysis_id = f"OCU-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
        db_image = Image(
            analysis_id=analysis_id,
            patient_id=patient_obj.id if patient_obj else None,
            filename=unique_filename,
            file_path=file_path,
            original_filename=file.filename,
            quality_score=_to_float(quality_result.get("score")),
            quality_grade=grade_str,
            illumination_score=_to_float(quality_result.get("illumination")),
            focus_score=_to_float(quality_result.get("focus")),
            fov_score=_to_float(quality_result.get("fov"))
        )
        db.add(db_image)
        db.commit()
        db.refresh(db_image)
        
        return ImageUploadResponse(
            id=db_image.id,
            filename=db_image.filename,
            patient_id=db_image.patient_id,
            upload_time=db_image.upload_time,
            status="uploaded"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/upload-batch")
async def upload_batch(
    files: List[UploadFile] = File(...),
    patient_ids: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Upload multiple fundus images"""
    results = []
    patient_id_list = patient_ids.split(",") if patient_ids else []
    
    for i, file in enumerate(files):
        try:
            patient_id = patient_id_list[i] if i < len(patient_id_list) else None
            
            # Re-upload single image
            result = await upload_image(file, patient_id, db)
            results.append({
                "file": file.filename,
                "status": "success",
                "image_id": result.id
            })
        except Exception as e:
            results.append({
                "file": file.filename,
                "status": "failed",
                "error": str(e)
            })
    
    return {
        "total": len(files),
        "success": len([r for r in results if r["status"] == "success"]),
        "failed": len([r for r in results if r["status"] == "failed"]),
        "results": results
    }

@router.get("/image/{image_id}")
async def get_image_info(image_id: int, db: Session = Depends(get_db)):
    """Get information about a specific image"""
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    return {
        "id": image.id,
        "filename": image.filename,
        "original_filename": image.original_filename,
        "upload_time": image.upload_time,
        "quality_grade": image.quality_grade,
        "quality_score": image.quality_score,
        "dr_grade": image.dr_grade,
        "dr_confidence": image.dr_confidence,
        "referable_dr": image.referable_dr,
        "vision_threatening": image.vision_threatening,
        "fractal_dimension": image.fractal_dimension,
        "vessel_density": image.vessel_density,
        "microaneurysm_count": image.microaneurysm_count,
        "exudate_count": image.exudate_count,
        "hemorrhage_count": image.hemorrhage_count,
        "processing_time": image.processing_time
    }

@router.delete("/image/{image_id}")
async def delete_image(image_id: int, db: Session = Depends(get_db)):
    """Delete an image and its associated data"""
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Delete file
    if os.path.exists(image.file_path):
        os.remove(image.file_path)
    
    # Delete from database
    db.delete(image)
    db.commit()
    
    return {"status": "success", "message": "Image deleted"}