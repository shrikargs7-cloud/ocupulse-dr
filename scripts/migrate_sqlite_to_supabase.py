#!/usr/bin/env python3
"""
OcuPulse SQLite to Supabase Migration Utility
---------------------------------------------
Transfers existing records from the local SQLite file (backend/oculpulse.db)
to the remote Supabase PostgreSQL database.

Usage:
    python scripts/migrate_sqlite_to_supabase.py
    python scripts/migrate_sqlite_to_supabase.py --target "postgresql://postgres:pass@db.xyz.supabase.co:5432/postgres"
"""

import os
import sys
import argparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

try:
    from dotenv import load_dotenv
    for env_file in [
        os.path.join(PROJECT_ROOT, ".env"),
        os.path.join(BACKEND_DIR, ".env"),
    ]:
        if os.path.isfile(env_file):
            load_dotenv(env_file, override=True)
except ImportError:
    pass

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, Patient, Image, Report, AnalysisLog, SimulinkSimulation


def migrate(sqlite_path: str, target_url: str):
    # Normalize target URL
    if target_url.startswith("postgres://"):
        target_url = "postgresql+psycopg2://" + target_url[len("postgres://"):]
    elif target_url.startswith("postgresql://") and not target_url.startswith("postgresql+"):
        target_url = "postgresql+psycopg2://" + target_url[len("postgresql://"):]

    if not os.path.exists(sqlite_path):
        print(f"[!] SQLite file not found at: {sqlite_path}")
        return

    print(f"[*] Source (SQLite): {sqlite_path}")
    masked_target = target_url.split("@")[-1] if "@" in target_url else target_url
    print(f"[*] Target (PostgreSQL/Supabase): ...@{masked_target}")

    # Source SQLite Engine
    source_engine = create_engine(f"sqlite:///{sqlite_path}", connect_args={"check_same_thread": False})
    SourceSession = sessionmaker(bind=source_engine)

    # Target Supabase Engine
    target_engine = create_engine(target_url, pool_pre_ping=True)
    TargetSession = sessionmaker(bind=target_engine)

    # Ensure tables exist on target
    print("\n[1/5] Ensuring target tables exist...")
    Base.metadata.create_all(bind=target_engine)

    with SourceSession() as src_db, TargetSession() as tgt_db:
        # 1. Patients
        patients = src_db.query(Patient).all()
        print(f"[2/5] Migrating {len(patients)} patients...")
        for p in patients:
            exists = tgt_db.query(Patient).filter(Patient.patient_id == p.patient_id).first()
            if not exists:
                tgt_db.add(Patient(
                    patient_id=p.patient_id,
                    created_at=p.created_at,
                ))
        tgt_db.commit()

        # Build patient map (patient_id string -> target patient integer id)
        patient_map = {p.patient_id: p.id for p in tgt_db.query(Patient).all()}

        # 2. Images
        images = src_db.query(Image).all()
        print(f"[3/5] Migrating {len(images)} images and analysis records...")
        image_id_map = {}  # source image id -> target image id
        for img in images:
            exists = tgt_db.query(Image).filter(Image.analysis_id == img.analysis_id).first() if img.analysis_id else None
            if exists:
                image_id_map[img.id] = exists.id
                continue

            target_patient_id = None
            if img.patient:
                target_patient_id = patient_map.get(img.patient.patient_id)

            new_img = Image(
                analysis_id=img.analysis_id,
                patient_id=target_patient_id,
                filename=img.filename,
                original_filename=img.original_filename,
                file_path=img.file_path,
                upload_time=img.upload_time,
                quality_score=img.quality_score,
                quality_grade=img.quality_grade,
                illumination_score=img.illumination_score,
                focus_score=img.focus_score,
                fov_score=img.fov_score,
                dr_grade=img.dr_grade,
                dr_confidence=img.dr_confidence,
                referable_dr=img.referable_dr,
                vision_threatening=img.vision_threatening,
                fractal_dimension=img.fractal_dimension,
                vessel_density=img.vessel_density,
                vessel_area=getattr(img, "vessel_area", None),
                skeleton_density=getattr(img, "skeleton_density", None),
                average_vessel_width_px=getattr(img, "average_vessel_width_px", None),
                tortuosity_index=img.tortuosity_index,
                branching_angle=img.branching_angle,
                vessel_length_px=img.vessel_length_px,
                branch_points=img.branch_points,
                endpoints=img.endpoints,
                microaneurysm_count=img.microaneurysm_count,
                exudate_count=img.exudate_count,
                hemorrhage_count=img.hemorrhage_count,
                neovascularization_count=img.neovascularization_count,
                drusen_count=img.drusen_count,
                matlab_analysis=img.matlab_analysis,
                processing_time=img.processing_time,
                model_version=img.model_version,
                details_json=img.details_json,
            )
            tgt_db.add(new_img)
            tgt_db.flush()
            image_id_map[img.id] = new_img.id
        tgt_db.commit()

        # 3. Reports
        reports = src_db.query(Report).all()
        print(f"[4/5] Migrating {len(reports)} reports...")
        for r in reports:
            target_image_id = image_id_map.get(r.image_id)
            if not target_image_id:
                continue
            exists = tgt_db.query(Report).filter(Report.image_id == target_image_id).first()
            if not exists:
                tgt_db.add(Report(
                    image_id=target_image_id,
                    report_path=r.report_path,
                    report_format=r.report_format,
                    is_shared=r.is_shared,
                    share_token=r.share_token,
                    generated_at=r.generated_at,
                ))
        tgt_db.commit()

        # 4. Analysis Logs
        logs = src_db.query(AnalysisLog).all()
        print(f"[5/5] Migrating {len(logs)} audit logs...")
        for log in logs:
            target_image_id = image_id_map.get(log.image_id)
            if not target_image_id:
                continue
            tgt_db.add(AnalysisLog(
                image_id=target_image_id,
                step_name=log.step_name,
                start_time=log.start_time,
                end_time=log.end_time,
                status=log.status,
                metrics=log.metrics,
                error_message=log.error_message,
            ))
        tgt_db.commit()

    print("\n✅ Migration complete! All records successfully transferred to Supabase.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate OcuPulse SQLite records to Supabase")
    parser.add_argument("--source", default=os.path.join(BACKEND_DIR, "oculpulse.db"), help="Source SQLite file path")
    parser.add_argument("--target", default=None, help="Target PostgreSQL connection string (defaults to DATABASE_URL in .env)")
    args = parser.parse_args()

    target_url = args.target or os.environ.get("DATABASE_URL") or os.environ.get("SUPABASE_DB_URL")
    if not target_url:
        print("[!] No target database URL provided. Set DATABASE_URL in .env or pass --target <url>")
        sys.exit(1)

    migrate(args.source, target_url)
