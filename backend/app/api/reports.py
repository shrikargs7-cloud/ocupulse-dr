from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from typing import Optional
import os

from ..database import SessionLocal, Image, Report
from ..schemas import ReportRequest, ReportResponse
from ..utils.report_generator import ReportGenerator

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/report/generate", response_model=ReportResponse)
async def generate_report(
    request: ReportRequest,
    db: Session = Depends(get_db)
):
    """Generate a clinical report for an image"""
    image = db.query(Image).filter(Image.id == request.image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Check if report already exists
    existing_report = db.query(Report).filter(Report.image_id == request.image_id).first()
    if existing_report and os.path.exists(existing_report.report_path):
        return ReportResponse(
            report_id=existing_report.id,
            image_id=existing_report.image_id,
            report_path=existing_report.report_path,
            report_format=existing_report.report_format,
            generated_at=existing_report.generated_at,
            download_url=f"/reports/{os.path.basename(existing_report.report_path)}"
        )
    
    # Generate new report
    generator = ReportGenerator()
    report_path = generator.generate_clinical_report(
        image_id=image.id,
        patient_id=image.patient_id,
        include_metadata=request.include_metadata,
        include_visualizations=request.include_visualizations,
        format=request.format
    )
    
    # Save to database
    report = Report(
        image_id=image.id,
        report_path=report_path,
        report_format=request.format,
        is_shared=False
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    
    return ReportResponse(
        report_id=report.id,
        image_id=report.image_id,
        report_path=report.report_path,
        report_format=report.report_format,
        generated_at=report.generated_at,
        download_url=f"/reports/{os.path.basename(report.report_path)}"
    )

@router.get("/report/{report_id}/download")
async def download_report(report_id: int, db: Session = Depends(get_db)):
    """Download a generated report"""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if not os.path.exists(report.report_path):
        raise HTTPException(status_code=404, detail="Report file not found")
    
    return Response(
        content=open(report.report_path, "rb").read(),
        media_type="application/pdf" if report.report_format == "PDF" else "text/html",
        headers={"Content-Disposition": f"attachment; filename=report_{report.image_id}.{report.report_format.lower()}"}
    )

@router.get("/report/{image_id}/share")
async def share_report(image_id: int, db: Session = Depends(get_db)):
    """Generate a shareable link for a report"""
    import secrets
    
    report = db.query(Report).filter(Report.image_id == image_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="No report found for this image")
    
    # Generate share token
    token = secrets.token_urlsafe(32)
    report.is_shared = True
    report.share_token = token
    db.commit()
    
    return {
        "share_url": f"/api/v1/report/shared/{token}",
        "token": token,
        "expires_in": "30 days"
    }

@router.get("/report/shared/{token}")
async def get_shared_report(token: str, db: Session = Depends(get_db)):
    """Access a shared report via token"""
    report = db.query(Report).filter(Report.share_token == token, Report.is_shared == True).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found or not shared")
    
    if not os.path.exists(report.report_path):
        raise HTTPException(status_code=404, detail="Report file not found")
    
    return Response(
        content=open(report.report_path, "rb").read(),
        media_type="application/pdf" if report.report_format == "PDF" else "text/html"
    )

@router.get("/report/history/{patient_id}")
async def get_patient_reports(patient_id: str, db: Session = Depends(get_db)):
    """Get all reports for a patient"""
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    reports = db.query(Report).join(Image).filter(Image.patient_id == patient.id).all()
    
    return [
        {
            "report_id": r.id,
            "image_id": r.image_id,
            "generated_at": r.generated_at,
            "format": r.report_format,
            "is_shared": r.is_shared,
            "download_url": f"/api/v1/report/{r.id}/download"
        }
        for r in reports
    ]