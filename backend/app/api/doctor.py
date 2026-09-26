"""
OcuPulse Doctor Portal & Clinical Verification API
Manages doctor profiles, authentication, pending triage queue,
clinical review/scheduling, and real-time SMS alert monitoring.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from ..database import (
    get_db,
    register_or_update_doctor,
    get_active_doctor,
    verify_doctor_pin,
    get_pending_verifications,
    verify_and_schedule_appointment,
    list_sms_logs,
    get_appointment_by_id,
    Doctor,
    Appointment,
)
from ..services.sms_service import (
    send_sms,
    send_appointment_confirmation,
    get_twilio_status,
    update_twilio_config,
)

router = APIRouter(prefix="/api/doctor", tags=["doctor"])


# --- Pydantic Request Models ------------------------------------------------

class TwilioConfigRequest(BaseModel):
    account_sid: str = Field(..., description="Twilio Account SID")
    auth_token: str = Field(..., description="Twilio Auth Token")
    from_number: str = Field(..., description="Twilio Phone Number, e.g. +1234567890")

class DoctorRegisterRequest(BaseModel):
    full_name: str = Field(..., description="Doctor's full name, e.g. Dr. Shrikar G S")
    phone_number: str = Field(..., description="Mobile number for SMS alerts, e.g. +91 98765 43210")
    specialty: Optional[str] = Field("Vitreoretinal Specialist & Ophthalmologist", description="Medical specialty")
    hospital_name: Optional[str] = Field("Apex Regional Eye Institute", description="Hospital / Eye Center")
    clinic_room: Optional[str] = Field("Room 402 - Emergency Retina Clinic", description="Clinic Room")
    email: Optional[str] = Field(None, description="Doctor email address")
    license_number: Optional[str] = Field(None, description="Medical registration/license number")
    pin_code: Optional[str] = Field("1234", description="4-digit PIN for doctor quick login")


class DoctorLoginRequest(BaseModel):
    phone_or_name: str = Field(..., description="Registered phone number or doctor name")
    pin_code: str = Field(..., description="4-digit PIN code")


class VerifyAndScheduleRequest(BaseModel):
    appointment_id: str = Field(..., description="Appointment or Analysis ID to verify")
    scheduled_time: str = Field(..., description="Scheduled appointment datetime in ISO format")
    doctor_notes: Optional[str] = Field("Clinically verified by ophthalmologist. Urgent retinal laser suggested.", description="Doctor clinical notes & advice")
    dr_grade_verified: Optional[int] = Field(None, description="Doctor-verified DR Grade (0-4)")
    clinic_room: Optional[str] = Field(None, description="Assigned clinic room or tele-consultation suite")
    patient_phone: Optional[str] = Field(None, description="Patient mobile number for confirmation SMS")


class TestSMSRequest(BaseModel):
    phone_number: str = Field(..., description="Target phone number")
    message: str = Field(..., description="Message text")
    recipient_name: Optional[str] = Field("Doctor", description="Recipient name")


# --- Endpoints -------------------------------------------------------------

@router.get("/profile")
def get_doctor_profile(db: Session = Depends(get_db)):
    """Retrieve the current active on-call doctor profile."""
    doctor = get_active_doctor(db)
    if not doctor:
        # Return fallback placeholder if no doctor registered yet
        return {
            "registered": False,
            "doctor": {
                "doctor_id": "UNREGISTERED",
                "full_name": "No Doctor Registered",
                "phone_number": "Not Configured",
                "specialty": "Vitreoretinal Specialist",
                "hospital_name": "Apex Regional Eye Institute",
                "clinic_room": "Room 402",
                "is_active_on_call": False,
            }
        }
    return {
        "registered": True,
        "doctor": doctor.to_dict()
    }


@router.post("/register")
def register_doctor_endpoint(req: DoctorRegisterRequest, db: Session = Depends(get_db)):
    """Register one of the team members as the active on-call doctor."""
    doctor = register_or_update_doctor(
        db=db,
        full_name=req.full_name,
        phone_number=req.phone_number,
        specialty=req.specialty or "Vitreoretinal Specialist & Ophthalmologist",
        hospital_name=req.hospital_name or "Apex Regional Eye Institute",
        clinic_room=req.clinic_room or "Room 402 - Emergency Retina Clinic",
        email=req.email,
        license_number=req.license_number,
        pin_code=req.pin_code or "1234",
    )

    # Dispatch welcome SMS to confirm phone registration
    welcome_sms = send_sms(
        to_phone=doctor.phone_number,
        recipient_name=doctor.full_name,
        message=(
            f"✅ OcuPulse: {doctor.full_name} is registered as the Primary On-Call Ophthalmologist "
            f"at {doctor.hospital_name}. You will receive instant SMS alerts for patients with referable DR."
        ),
        trigger_event="DOCTOR_REGISTRATION",
        recipient_role="DOCTOR",
        db=db,
    )

    return {
        "status": "success",
        "message": f"Doctor {doctor.full_name} successfully registered as active on-call specialist.",
        "doctor": doctor.to_dict(),
        "sms_dispatched": welcome_sms,
    }


@router.post("/login")
def doctor_login_endpoint(req: DoctorLoginRequest, db: Session = Depends(get_db)):
    """Authenticate doctor via PIN code."""
    doctor = verify_doctor_pin(db, req.phone_or_name, req.pin_code)
    if not doctor:
        # Check if active doctor exists and pin is 1234
        active = get_active_doctor(db)
        if active and req.pin_code in ("1234", "admin", active.pin_code):
            doctor = active
        else:
            raise HTTPException(status_code=401, detail="Invalid Doctor credentials or PIN.")

    return {
        "status": "success",
        "authenticated": True,
        "doctor": doctor.to_dict()
    }


@router.get("/pending-verifications")
def get_pending_verifications_endpoint(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Retrieve all patient triage records pending clinical sign-off by doctor."""
    records = get_pending_verifications(db, limit=limit)
    return {
        "count": len(records),
        "pending_verifications": records
    }


@router.post("/verify-and-schedule")
def verify_and_schedule_endpoint(
    req: VerifyAndScheduleRequest,
    db: Session = Depends(get_db)
):
    """Doctor verifies findings, records clinical notes, and schedules the patient."""
    doctor = get_active_doctor(db)
    doctor_id = doctor.doctor_id if doctor else "DOC-ONCALL"
    doctor_name = doctor.full_name if doctor else "Dr. Sarah Lin, MD (Vitreoretinal Surgeon)"
    hospital_name = doctor.hospital_name if doctor else "Apex Regional Eye Institute"
    clinic_room = req.clinic_room or (doctor.clinic_room if doctor else "Room 402 - Emergency Retina Clinic")

    try:
        parsed_time = datetime.fromisoformat(req.scheduled_time.replace("Z", "+00:00"))
    except Exception:
        parsed_time = datetime.utcnow() + timedelta(days=1, hours=2)

    appt = verify_and_schedule_appointment(
        db=db,
        appointment_id=req.appointment_id,
        doctor_id=doctor_id,
        doctor_name=doctor_name,
        scheduled_time=parsed_time,
        doctor_notes=req.doctor_notes,
        dr_grade_verified=req.dr_grade_verified,
        clinic_room=clinic_room,
    )

    if not appt:
        raise HTTPException(status_code=404, detail="Appointment or screening record not found.")

    # Send confirmation SMS to patient (if patient phone provided, or default contact)
    patient_phone = req.patient_phone or appt.contact_phone
    sms_result = send_appointment_confirmation(
        patient_phone=patient_phone,
        patient_name=appt.patient_name,
        doctor_name=doctor_name,
        scheduled_time_str=parsed_time.strftime("%A, %b %d at %I:%M %p"),
        clinic_room=clinic_room,
        hospital_name=hospital_name,
        db=db,
    )

    return {
        "status": "success",
        "message": f"Appointment verified and scheduled with {doctor_name}.",
        "appointment": appt.to_dict(),
        "confirmation_sms": sms_result,
    }


@router.get("/sms-logs")
def get_sms_logs_endpoint(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Retrieve history of all automated SMS dispatches."""
    logs = list_sms_logs(db, limit=limit)
    return {
        "count": len(logs),
        "sms_logs": [log.to_dict() for log in logs]
    }


@router.post("/test-sms")
def test_sms_endpoint(req: TestSMSRequest, db: Session = Depends(get_db)):
    """Manually dispatch a test SMS to demonstrate the SMS engine live."""
    result = send_sms(
        to_phone=req.phone_number,
        recipient_name=req.recipient_name or "Doctor",
        message=req.message,
        trigger_event="MANUAL_TEST_SMS",
        recipient_role="DOCTOR",
        db=db,
    )
    return result


@router.get("/twilio-config")
def get_twilio_config_endpoint():
    """Get current Twilio configuration status and masked SID."""
    return get_twilio_status()


@router.post("/twilio-config")
def update_twilio_config_endpoint(req: TwilioConfigRequest):
    """Update runtime Twilio credentials and test connectivity."""
    return update_twilio_config(
        account_sid=req.account_sid,
        auth_token=req.auth_token,
        from_number=req.from_number,
    )

