"""
OcuPulse Real-Time Twilio SMS Dispatch Engine
Dispatches real-time SMS alerts to registered Doctors upon detection of referable DR
and sends confirmation SMS to patients when appointments are verified and scheduled.

Powered by the official Twilio REST API with seamless live fallback simulation.
"""

import os
import json
import logging
import re
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from sqlalchemy.orm import Session
from ..database import log_sms, SessionLocal

logger = logging.getLogger("ocupulse.sms")

# Global in-memory / environment credential cache
_TWILIO_CONFIG = {
    "account_sid": os.getenv("TWILIO_ACCOUNT_SID", "").strip(),
    "auth_token": os.getenv("TWILIO_AUTH_TOKEN", "").strip(),
    "from_number": os.getenv("TWILIO_FROM_NUMBER", "").strip(),
}


def get_twilio_status() -> Dict[str, Any]:
    """Retrieve current Twilio API configuration status (credentials masked)."""
    sid = _TWILIO_CONFIG["account_sid"] or os.getenv("TWILIO_ACCOUNT_SID", "").strip()
    from_num = _TWILIO_CONFIG["from_number"] or os.getenv("TWILIO_FROM_NUMBER", "").strip()
    is_configured = bool(sid and (_TWILIO_CONFIG["auth_token"] or os.getenv("TWILIO_AUTH_TOKEN", "").strip()) and from_num)

    masked_sid = f"{sid[:6]}...{sid[-4:]}" if len(sid) > 10 else ("Configured" if sid else "Not set")

    return {
        "configured": is_configured,
        "mode": "Twilio Real-Time Live Gateway" if is_configured else "OcuPulse Live SMS Simulator",
        "account_sid_masked": masked_sid if is_configured else None,
        "from_number": from_num if is_configured else None,
    }


def update_twilio_config(account_sid: str, auth_token: str, from_number: str) -> Dict[str, Any]:
    """Update Twilio credentials dynamically at runtime and persist to .env."""
    clean_sid = account_sid.strip()
    clean_token = auth_token.strip()
    clean_from = from_number.strip().replace(" ", "")

    _TWILIO_CONFIG["account_sid"] = clean_sid
    _TWILIO_CONFIG["auth_token"] = clean_token
    _TWILIO_CONFIG["from_number"] = clean_from

    # Also persist to process environment
    os.environ["TWILIO_ACCOUNT_SID"] = clean_sid
    os.environ["TWILIO_AUTH_TOKEN"] = clean_token
    os.environ["TWILIO_FROM_NUMBER"] = clean_from

    # Append or update root .env file if it exists
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.env"))
    try:
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Replace or append
            for key, val in [("TWILIO_ACCOUNT_SID", clean_sid), ("TWILIO_AUTH_TOKEN", clean_token), ("TWILIO_FROM_NUMBER", clean_from)]:
                if f"{key}=" in content:
                    content = re.sub(rf"^{key}=.*$", f"{key}={val}", content, flags=re.MULTILINE)
                else:
                    content += f"\n{key}={val}"

            with open(env_path, "w", encoding="utf-8") as f:
                f.write(content)
    except Exception as e:
        logger.warning(f"Could not persist Twilio credentials to .env: {e}")

    # Test credentials with twilio Client validation if provided
    client_valid = False
    validation_note = "Credentials saved."
    if clean_sid and clean_token:
        try:
            from twilio.rest import Client
            client = Client(clean_sid, clean_token)
            account = client.api.accounts(clean_sid).fetch()
            client_valid = True
            validation_note = f"Connected to Twilio Account: {account.friendly_name} ({account.status})"
        except Exception as te:
            validation_note = f"Credentials saved (Twilio validation check: {str(te)})"

    return {
        "success": True,
        "valid": client_valid,
        "message": validation_note,
        "status": get_twilio_status(),
    }


def send_sms(
    to_phone: str,
    recipient_name: str,
    message: str,
    trigger_event: str = "CLINICAL_ALERT",
    recipient_role: str = "DOCTOR",
    db: Optional[Session] = None,
) -> Dict[str, Any]:
    """
    Sends a real-time SMS using Twilio REST API if configured,
    or delivers through the high-fidelity OcuPulse Live SMS Simulator.
    Records every transmission in the database for presentation and auditing.
    """
    close_db_at_end = False
    if db is None:
        db = SessionLocal()
        close_db_at_end = True

    clean_phone = to_phone.strip().replace(" ", "").replace("-", "")
    # Ensure E.164 formatting if possible (default to +91 if 10-digit Indian mobile)
    if not clean_phone.startswith("+"):
        if len(clean_phone) == 10:
            clean_phone = f"+91{clean_phone}"
        else:
            clean_phone = f"+{clean_phone}"

    sid = _TWILIO_CONFIG["account_sid"] or os.getenv("TWILIO_ACCOUNT_SID", "").strip()
    token = _TWILIO_CONFIG["auth_token"] or os.getenv("TWILIO_AUTH_TOKEN", "").strip()
    from_num = _TWILIO_CONFIG["from_number"] or os.getenv("TWILIO_FROM_NUMBER", "").strip()

    gateway = "OcuPulse Live SMS Simulator"
    status = "DELIVERED (SIMULATED)"
    twilio_sid = None
    delivery_note = None

    if sid and token and from_num:
        try:
            from twilio.rest import Client
            client = Client(sid, token)
            message_instance = client.messages.create(
                to=clean_phone,
                from_=from_num,
                body=message,
            )
            twilio_sid = message_instance.sid
            gateway = "Twilio Live SMS Gateway"
            status = f"DELIVERED (Twilio: {message_instance.status.upper()} - {twilio_sid})"
            delivery_note = f"Twilio Message SID: {twilio_sid} | Status: {message_instance.status}"
            print(f"\n🚀 [TWILIO REAL-TIME SMS DELIVERED] SID: {twilio_sid} To: {clean_phone}")
        except Exception as e:
            err_msg = str(e)
            logger.error(f"Twilio transmission error: {err_msg}")
            gateway = "Twilio (Failed -> Local Simulator)"
            status = f"FAILED: {err_msg[:60]}"
            delivery_note = f"Twilio API Error: {err_msg}"
            print(f"\n⚠️ [TWILIO ERROR] {err_msg}")
            print(f"   Fallback to Simulator for recipient {clean_phone}")

    # Terminal Broadcast for Hackathon / Presentation Display
    print(f"\n=================================================================")
    print(f"📱 [OCUPULSE CLINICAL SMS DISPATCH - REAL-TIME]")
    print(f"   Recipient: {clean_phone} ({recipient_name or 'Recipient'}) [{recipient_role}]")
    print(f"   Event:     {trigger_event}")
    print(f"   Gateway:   {gateway}")
    print(f"   Status:    {status}")
    if delivery_note:
        print(f"   Note:      {delivery_note}")
    print(f"   Message:\n   \"{message}\"")
    print(f"=================================================================\n")

    # Save to database log
    log_entry = log_sms(
        db=db,
        recipient_phone=clean_phone,
        recipient_name=recipient_name,
        recipient_role=recipient_role,
        message_text=message,
        trigger_event=trigger_event,
        status=status,
        gateway=gateway,
    )

    result = {
        "success": True,
        "sms_id": log_entry.id,
        "twilio_sid": twilio_sid,
        "recipient_phone": clean_phone,
        "recipient_name": recipient_name,
        "status": status,
        "gateway": gateway,
        "message": message,
        "sent_at": log_entry.sent_at.isoformat() if log_entry.sent_at else datetime.utcnow().isoformat(),
    }

    if close_db_at_end:
        db.close()

    return result


def send_referable_dr_alert(
    doctor_phone: str,
    doctor_name: str,
    patient_name: str,
    patient_id: str,
    dr_grade: int,
    severity: str,
    analysis_id: str,
    db: Optional[Session] = None,
) -> Dict[str, Any]:
    """
    Sends an urgent clinical triage SMS alert to the registered Doctor
    when a patient is screened with referable diabetic retinopathy (Grade 2+).
    """
    message = (
        f"🚨 OcuPulse CLINICAL ALERT: Patient {patient_name} (ID: {patient_id}) has been screened with "
        f"REFERABLE DIABETIC RETINOPATHY: Grade {dr_grade} ({severity}). "
        f"Urgent review required: http://localhost:5173/doctor [Scan: {analysis_id[:14]}]"
    )

    return send_sms(
        to_phone=doctor_phone,
        recipient_name=doctor_name,
        message=message,
        trigger_event="REFERABLE_DR_ALERT",
        recipient_role="DOCTOR",
        db=db,
    )


def send_appointment_confirmation(
    patient_phone: str,
    patient_name: str,
    doctor_name: str,
    scheduled_time_str: str,
    clinic_room: str,
    hospital_name: str,
    db: Optional[Session] = None,
) -> Dict[str, Any]:
    """
    Sends an SMS appointment confirmation to the patient once the Doctor has signed off and scheduled the slot.
    """
    message = (
        f"✅ OcuPulse Healthcare: Your retinal specialist consultation with {doctor_name} is confirmed for "
        f"{scheduled_time_str} at {hospital_name} ({clinic_room}). "
        f"Please arrive 15 minutes prior. Need help? Call: +1 (800) 555-RETINA."
    )

    return send_sms(
        to_phone=patient_phone,
        recipient_name=patient_name,
        message=message,
        trigger_event="APPOINTMENT_CONFIRMED",
        recipient_role="PATIENT",
        db=db,
    )
