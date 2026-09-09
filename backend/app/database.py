"""
OcuPulse persistence layer.

SQLAlchemy 2.0 declarative models over a single SQLite file. The schema is
deliberately thin: an uploaded fundus photograph (``Image``) is the unit of
work, and every downstream artefact - quality scores, DR grade, quantitative
vascular metrics, lesion counts, generated reports, per-step processing logs -
hangs off it.

``Image.analysis_id`` carries the human-facing ``OCU-YYYYMMDD-HHMMSS-XXXXXX``
slug the screening dashboard displays and links on, while ``Image.id`` is the
integer primary key the ``/api/v1`` endpoints address. Both are unique, so a
caller can resolve a record either way.

No directly identifying patient data is stored: ``Patient.patient_id`` is an
opaque site-supplied identifier.
"""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    event,
)
from sqlalchemy.orm import DeclarativeBase, Session, relationship, sessionmaker

from .config import settings

# The SQLite file's parent directory and the report directory (mounted with
# StaticFiles at import time by app.main) must exist before create_all runs.
settings.ensure_directories()


class Base(DeclarativeBase):
    """Declarative base for every OcuPulse model."""


# Register psycopg2 adapters for NumPy numeric and boolean types so PostgreSQL / Supabase
# handles np.float64, np.int64, np.bool_ without "schema np does not exist" errors
try:
    import numpy as np
    import psycopg2
    from psycopg2.extensions import register_adapter, AsIs

    register_adapter(np.floating, lambda val: AsIs(float(val)))
    register_adapter(np.integer, lambda val: AsIs(int(val)))
    register_adapter(np.bool_, lambda val: AsIs(bool(val)))
except Exception as _adapter_err:
    pass


# Configure SQLAlchemy engine dynamically for PostgreSQL (Supabase) or local SQLite
if settings.is_postgres:
    engine = create_engine(
        settings.DATABASE_URL,
        echo=False,
        future=True,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args={
            "connect_timeout": 10,
            "application_name": "ocupluse_api",
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
        },
    )
else:
    engine = create_engine(
        settings.DATABASE_URL,
        echo=False,
        future=True,
        # FastAPI serves requests from a threadpool, so the connection is shared
        # across threads; SQLite writes are still serialised by the engine pool.
        connect_args={"check_same_thread": False, "timeout": 30},
    )

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _connection_record) -> None:
        """Enable foreign keys and WAL journaling on SQLite."""
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Patient(Base):
    """An opaque, site-supplied patient identifier and its image history."""

    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(64), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    images = relationship(
        "Image",
        back_populates="patient",
        cascade="all, delete-orphan",
        order_by="Image.upload_time.desc()",
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return "<Patient {}>".format(self.patient_id)


class Image(Base):
    """One uploaded retinal fundus photograph and everything derived from it."""

    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)

    #: ``OCU-YYYYMMDD-HHMMSS-XXXXXX`` slug surfaced in the dashboard.
    analysis_id = Column(String(32), unique=True, index=True, nullable=True)

    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True, index=True)

    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=True)
    file_path = Column(String(512), nullable=False)
    upload_time = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)

    # --- Quality assessment -------------------------------------------------
    quality_score = Column(Float, nullable=True)
    quality_grade = Column(String(64), nullable=True)
    illumination_score = Column(Float, nullable=True)
    focus_score = Column(Float, nullable=True)
    fov_score = Column(Float, nullable=True)

    # --- Grading outcome ----------------------------------------------------
    dr_grade = Column(Integer, nullable=True, index=True)
    dr_confidence = Column(Float, nullable=True)
    referable_dr = Column(Boolean, default=False, index=True)
    vision_threatening = Column(Boolean, default=False)

    # --- Quantitative vascular metrics --------------------------------------
    fractal_dimension = Column(Float, nullable=True)
    vessel_density = Column(Float, nullable=True)
    vessel_area = Column(Integer, nullable=True)
    skeleton_density = Column(Float, nullable=True)
    average_vessel_width_px = Column(Float, nullable=True)
    tortuosity_index = Column(Float, nullable=True)
    branching_angle = Column(Float, nullable=True)
    vessel_length_px = Column(Float, nullable=True)
    branch_points = Column(Integer, nullable=True)
    endpoints = Column(Integer, nullable=True)

    # --- Lesion counts ------------------------------------------------------
    microaneurysm_count = Column(Integer, default=0)
    exudate_count = Column(Integer, default=0)
    hemorrhage_count = Column(Integer, default=0)
    neovascularization_count = Column(Integer, default=0)
    drusen_count = Column(Integer, default=0)

    # --- Provenance ---------------------------------------------------------
    #: Raw MATLAB Engine struct, when MATLAB was available for this image.
    matlab_analysis = Column(Text, nullable=True)
    processing_time = Column(Float, nullable=True)
    model_version = Column(String(32), nullable=True)

    #: Complete analysis payload as JSON, so the dashboard can restore a past
    #: result - including its overlay images - without recomputing anything.
    details_json = Column(Text, nullable=True)

    patient = relationship("Patient", back_populates="images")
    report = relationship(
        "Report",
        back_populates="image",
        uselist=False,
        cascade="all, delete-orphan",
    )
    logs = relationship(
        "AnalysisLog",
        back_populates="image",
        cascade="all, delete-orphan",
        order_by="AnalysisLog.start_time",
    )

    def to_history_record(self) -> Dict[str, Any]:
        """Flatten to the shape the history dashboard renders."""
        return {
            "id": self.id,
            "analysis_id": self.analysis_id,
            "patient_id": self.patient.patient_id if self.patient else None,
            "filename": self.filename,
            "upload_time": self.upload_time,
            "dr_grade": self.dr_grade,
            "dr_confidence": self.dr_confidence,
            "referable_dr": self.referable_dr,
            "vision_threatening": self.vision_threatening,
            "processing_time": self.processing_time,
            "quality_grade": self.quality_grade,
            "quality_score": self.quality_score,
            "fractal_dimension": self.fractal_dimension,
            "vessel_density": self.vessel_density,
        }


class Report(Base):
    """A generated clinical report file and its optional share token."""

    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(
        Integer, ForeignKey("images.id"), unique=True, nullable=False, index=True
    )
    report_path = Column(String(512), nullable=False)
    report_format = Column(String(8), default="HTML", nullable=False)
    is_shared = Column(Boolean, default=False, nullable=False)
    share_token = Column(String(64), unique=True, nullable=True, index=True)
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    image = relationship("Image", back_populates="report")


class AnalysisLog(Base):
    """Per-step processing audit trail for one image."""

    __tablename__ = "analysis_logs"

    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(Integer, ForeignKey("images.id"), nullable=False, index=True)
    step_name = Column(String(64), nullable=False)
    start_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_time = Column(DateTime, nullable=True)
    status = Column(String(16), default="Processing", nullable=False)
    metrics = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

    image = relationship("Image", back_populates="logs")

    @property
    def duration_seconds(self) -> Optional[float]:
        """Wall-clock duration of the step, or ``None`` if still running."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


class SimulinkSimulation(Base):
    """One recorded run of the district-scale telemedicine optimiser."""

    __tablename__ = "simulink_simulations"

    id = Column(Integer, primary_key=True, index=True)
    simulation_name = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)

    # Inputs
    patient_volume = Column(Integer, nullable=False)
    bandwidth_mbps = Column(Float, nullable=False)
    processing_throughput = Column(Float, nullable=False)
    review_capacity = Column(Integer, nullable=False)
    operating_hours = Column(Integer, nullable=True)

    # Outputs
    total_cost = Column(Float, nullable=True)
    cost_per_patient = Column(Float, nullable=True)
    throughput_per_day = Column(Integer, nullable=True)
    backlog_after_year = Column(Integer, nullable=True)
    optimized_params = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)
    source = Column(String(16), default="python-fallback", nullable=False)


class Appointment(Base):
    """Urgent clinical doctor appointment booked for patients in critical condition."""

    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(String(64), unique=True, index=True, nullable=False)
    analysis_id = Column(String(64), index=True, nullable=True)
    patient_id = Column(String(64), index=True, nullable=True)
    patient_name = Column(String(128), default="Anonymous Patient", nullable=False)
    doctor_name = Column(String(128), default="Dr. Sarah Lin, MD (Vitreoretinal Surgeon)", nullable=False)
    doctor_specialty = Column(String(128), default="Vitreoretinal Ophthalmology & Retinal Surgery", nullable=False)
    hospital_name = Column(String(256), default="Apex Regional Eye Institute & Referral Center", nullable=False)
    clinic_room = Column(String(64), default="Suite 402 - Emergency Retina Clinic", nullable=False)
    contact_phone = Column(String(32), default="+1 (800) 555-RETINA", nullable=False)
    scheduled_time = Column(DateTime, nullable=False)
    priority = Column(String(32), default="STAT / Urgent", nullable=False)
    status = Column(String(32), default="CONFIRMED", nullable=False)
    dr_grade = Column(Integer, nullable=True)
    severity_level = Column(String(64), nullable=True)
    clinical_reason = Column(Text, nullable=True)
    action_required = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "appointment_id": self.appointment_id,
            "analysis_id": self.analysis_id,
            "patient_id": self.patient_id,
            "patient_name": self.patient_name,
            "doctor_name": self.doctor_name,
            "doctor_specialty": self.doctor_specialty,
            "hospital_name": self.hospital_name,
            "clinic_room": self.clinic_room,
            "contact_phone": self.contact_phone,
            "scheduled_time": self.scheduled_time.isoformat() if self.scheduled_time else "",
            "priority": self.priority,
            "status": self.status,
            "dr_grade": self.dr_grade,
            "severity_level": self.severity_level,
            "clinical_reason": self.clinical_reason,
            "action_required": self.action_required,
            "created_at": self.created_at.isoformat() if self.created_at else "",
        }


def _migrate_missing_columns() -> None:
    """Safely adds newly defined columns to existing tables if missing."""
    from sqlalchemy import inspect, text
    try:
        inspector = inspect(engine)
        if "images" in inspector.get_table_names():
            columns = {col["name"] for col in inspector.get_columns("images")}
            missing = {
                "vessel_area": "INTEGER",
                "skeleton_density": "FLOAT",
                "average_vessel_width_px": "FLOAT",
            }
            with engine.connect() as conn:
                for col_name, col_type in missing.items():
                    if col_name not in columns:
                        conn.execute(text(f"ALTER TABLE images ADD COLUMN {col_name} {col_type}"))
                conn.commit()
    except Exception as e:
        print(f"Column migration notice: {e}")


_db_initialized = False

def init_db(force: bool = False) -> None:
    """Create every table that does not yet exist and migrate columns efficiently."""
    global _db_initialized
    if _db_initialized and not force:
        return

    try:
        from sqlalchemy import inspect
        inspector = inspect(engine)
        existing = set(inspector.get_table_names())
        expected = {"patients", "images", "reports", "analysis_logs", "simulink_simulations", "appointments"}
        if not expected.issubset(existing):
            Base.metadata.create_all(bind=engine)
        _migrate_missing_columns()
        _db_initialized = True
    except Exception as e:
        print(f"init_db fallback: {e}")
        Base.metadata.create_all(bind=engine)
        _db_initialized = True


def get_db():
    """FastAPI dependency yielding a session that always closes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_image_or_none(db: Session, image_id: int) -> Optional[Image]:
    """Fetch one image by primary key."""
    return db.get(Image, image_id)


def get_image_by_analysis_id(db: Session, analysis_id: str) -> Optional[Image]:
    """Fetch one image by its ``OCU-...`` dashboard slug."""
    return (
        db.query(Image).filter(Image.analysis_id == analysis_id).one_or_none()
    )


def get_or_create_patient(db: Session, patient_id: str) -> Optional[Patient]:
    """Resolve an opaque patient identifier, creating the row on first sight.

    Returns ``None`` for an empty identifier so callers can store an
    unattributed image rather than inventing a patient.
    """
    if not patient_id:
        return None
    patient = (
        db.query(Patient).filter(Patient.patient_id == patient_id).one_or_none()
    )
    if patient is None:
        patient = Patient(patient_id=patient_id)
        db.add(patient)
        db.flush()
    return patient


def list_images(
    db: Session,
    limit: int = 50,
    offset: int = 0,
) -> List[Image]:
    """Most recent images first, for the history dashboard."""
    return (
        db.query(Image)
        .order_by(Image.upload_time.desc(), Image.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


_last_health_check = {"time": 0.0, "data": None}

def check_database_connection(use_cache: bool = True) -> Dict[str, Any]:
    """Test connection to the database and return status metadata with short TTL caching."""
    import time
    now = time.time()
    if use_cache and _last_health_check["data"] is not None and (now - _last_health_check["time"] < 10.0):
        return _last_health_check["data"]

    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        result = {
            "status": "connected",
            "dialect": engine.dialect.name,
            "is_supabase": settings.is_postgres and ("supabase" in settings.DATABASE_URL.lower()),
            "url_masked": (
                settings.DATABASE_URL.split("@")[-1]
                if "@" in settings.DATABASE_URL
                else settings.DATABASE_URL
            ),
        }
        _last_health_check["time"] = now
        _last_health_check["data"] = result
        return result
    except Exception as exc:
        err_res = {
            "status": "disconnected",
            "error": str(exc),
            "dialect": engine.dialect.name,
            "is_supabase": settings.is_postgres and ("supabase" in settings.DATABASE_URL.lower()),
        }
        _last_health_check["time"] = now
        _last_health_check["data"] = err_res
        return err_res


def create_emergency_appointment(
    db: Session,
    analysis_id: Optional[str] = None,
    patient_id: Optional[str] = None,
    patient_name: str = "Anonymous Patient",
    dr_grade: Optional[int] = None,
    severity_level: Optional[str] = None,
    clinical_reason: Optional[str] = None,
    action_required: Optional[str] = None,
    priority: str = "STAT / Urgent",
    doctor_name: str = "Dr. Sarah Lin, MD (Vitreoretinal Surgeon)",
    doctor_specialty: str = "Vitreoretinal Ophthalmology & Retinal Surgery",
    hospital_name: str = "Apex Regional Eye Institute & Referral Center",
    clinic_room: str = "Suite 402 - Emergency Retina Clinic",
    contact_phone: str = "+1 (800) 555-RETINA",
    scheduled_time: Optional[datetime] = None,
) -> Appointment:
    """Book an emergency appointment for critical retinal findings."""
    import uuid
    from datetime import timedelta

    # Default to next-day morning urgent slot (approx 24 hours out, 9:00 AM)
    if scheduled_time is None:
        tomorrow = datetime.utcnow() + timedelta(days=1)
        scheduled_time = tomorrow.replace(hour=9, minute=30, second=0, microsecond=0)

    appointment_id = f"APT-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    appointment = Appointment(
        appointment_id=appointment_id,
        analysis_id=analysis_id,
        patient_id=patient_id,
        patient_name=patient_name,
        doctor_name=doctor_name,
        doctor_specialty=doctor_specialty,
        hospital_name=hospital_name,
        clinic_room=clinic_room,
        contact_phone=contact_phone,
        scheduled_time=scheduled_time,
        priority=priority,
        status="CONFIRMED",
        dr_grade=dr_grade,
        severity_level=severity_level,
        clinical_reason=clinical_reason,
        action_required=action_required,
        created_at=datetime.utcnow(),
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


def get_appointment_by_analysis(db: Session, analysis_id: str) -> Optional[Appointment]:
    """Retrieve appointment associated with an analysis ID."""
    return (
        db.query(Appointment)
        .filter(Appointment.analysis_id == analysis_id)
        .order_by(Appointment.created_at.desc())
        .first()
    )


def get_appointment_by_id(db: Session, appointment_id: str) -> Optional[Appointment]:
    """Retrieve appointment by its APT-XXX identifier."""
    return (
        db.query(Appointment)
        .filter(Appointment.appointment_id == appointment_id)
        .first()
    )


def list_appointments(
    db: Session,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Appointment]:
    """Query booked doctor appointments sorted by urgency and scheduled time."""
    query = db.query(Appointment)
    if status and status.upper() != "ALL":
        query = query.filter(Appointment.status == status.upper())
    if priority and priority.upper() != "ALL":
        query = query.filter(Appointment.priority.ilike(f"%{priority}%"))
    return (
        query.order_by(Appointment.scheduled_time.asc(), Appointment.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def update_appointment_status(
    db: Session,
    appointment_id: str,
    new_status: str,
) -> Optional[Appointment]:
    """Update status of an appointment (e.g., CONFIRMED, ATTENDED, CANCELLED)."""
    appointment = get_appointment_by_id(db, appointment_id)
    if not appointment:
        return None
    appointment.status = new_status.upper()
    db.commit()
    db.refresh(appointment)
    return appointment


def delete_appointment(
    db: Session,
    appointment_id: str,
) -> bool:
    """Delete an appointment by appointment_id or analysis_id."""
    appointment = get_appointment_by_id(db, appointment_id)
    if not appointment:
        return False
    db.delete(appointment)
    db.commit()
    return True


