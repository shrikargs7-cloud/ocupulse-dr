#!/usr/bin/env python3
"""
OcuPulse Database Connection Tester
-----------------------------------
Verifies the database connection for OcuPulse (Supabase PostgreSQL or local SQLite).

Usage:
    python scripts/test_supabase_connection.py
    python scripts/test_supabase_connection.py "postgresql://postgres:pass@db.xyz.supabase.co:5432/postgres"
"""

import os
import sys

# Ensure backend is on sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Load environment
try:
    from dotenv import load_dotenv
    for env_file in [
        os.path.join(PROJECT_ROOT, ".env"),
        os.path.join(BACKEND_DIR, ".env"),
    ]:
        if os.path.isfile(env_file):
            load_dotenv(env_file, override=False)
except ImportError:
    pass


def main():
    print("=" * 65)
    print("       OcuPulse Retinal Analysis - Database Connection Test     ")
    print("=" * 65)

    # 1. Determine connection URL
    url = None
    if len(sys.argv) > 1 and sys.argv[1].strip():
        url = sys.argv[1].strip()
        print(f"[INFO] Using database URL passed via command-line argument.")
    else:
        url = os.environ.get("DATABASE_URL") or os.environ.get("SUPABASE_DB_URL")

    if not url or not url.strip():
        print("[!] No remote DATABASE_URL found in environment or arguments.")
        print("[*] Falling back to default local SQLite database.")
        from app.config import settings
        url = settings.DATABASE_URL
    else:
        url = url.strip()

    # 2. Normalize PostgreSQL URL if necessary
    if url.startswith("postgres://"):
        url = "postgresql+psycopg2://" + url[len("postgres://"):]
    elif url.startswith("postgresql://") and not url.startswith("postgresql+"):
        url = "postgresql+psycopg2://" + url[len("postgresql://"):]

    # Mask credentials for printing
    masked_url = url
    if "@" in url:
        prefix = url.split("://")[0]
        host_part = url.split("@")[-1]
        masked_url = f"{prefix}://*****:*****@{host_part}"

    print(f"\n[TARGET] Connecting to: {masked_url}")

    # 3. Test SQLAlchemy connection
    try:
        from sqlalchemy import create_engine, text, inspect
        from app.database import Base, Patient, Image, Report, AnalysisLog, SimulinkSimulation
    except ImportError as e:
        print(f"\n[ERROR] Missing required Python package: {e}")
        print("Please install dependencies: pip install -r backend/requirements.txt")
        sys.exit(1)

    is_sqlite = url.startswith("sqlite")
    connect_args = {"check_same_thread": False, "timeout": 30} if is_sqlite else {}

    try:
        engine = create_engine(
            url,
            connect_args=connect_args,
            pool_pre_ping=True,
        )
        print("[1/4] Establishing TCP / database handshake...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            assert result == 1
        print("      ✓ Handshake successful! Database is online and responsive.")
    except Exception as exc:
        print(f"\n[FAIL] Could not connect to database:")
        print(f"       {type(exc).__name__}: {exc}")
        print("\nTroubleshooting Tips:")
        print(" 1. Check your password in the Supabase connection string.")
        print(" 2. Make sure you use the 'Direct' or 'Transaction Pooler' URI from:")
        print("    Supabase Dashboard -> Project Settings -> Database -> Connection string -> URI")
        print(" 3. If your network blocks port 5432, use the Session/Transaction Pooler port (6543 or 5432 with pooler host).")
        sys.exit(1)

    # 4. Check existing tables
    print("\n[2/4] Inspecting schema and existing tables...")
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    expected_tables = {"patients", "images", "reports", "analysis_logs", "simulink_simulations"}
    missing_tables = expected_tables - existing_tables

    print(f"      Existing tables found: {list(existing_tables) or 'None'}")
    if missing_tables:
        print(f"      Missing tables: {list(missing_tables)}")
        print("\n[3/4] Auto-creating missing tables with SQLAlchemy metadata...")
        Base.metadata.create_all(bind=engine)
        new_tables = set(inspect(engine).get_table_names())
        print(f"      ✓ Created! Current tables in database: {list(new_tables)}")
    else:
        print("\n[3/4] All required OcuPulse tables are already present in the database.")

    # 5. Verify Read / Write capability
    print("\n[4/4] Verifying read / write permissions with a temporary test probe...")
    try:
        from sqlalchemy.orm import Session
        with Session(engine) as session:
            test_patient_id = "TEST-PROBE-SUPABASE-CHECK"
            # Cleanup any leftover probe
            old_probe = session.query(Patient).filter(Patient.patient_id == test_patient_id).first()
            if old_probe:
                session.delete(old_probe)
                session.commit()

            # Insert probe
            probe = Patient(patient_id=test_patient_id)
            session.add(probe)
            session.commit()

            # Query probe
            verified = session.query(Patient).filter(Patient.patient_id == test_patient_id).first()
            assert verified is not None

            # Clean up
            session.delete(verified)
            session.commit()
        print("      ✓ Read and write operations verified successfully!")
    except Exception as exc:
        print(f"      [!] Read/Write test failed: {exc}")
        sys.exit(1)

    print("\n" + "=" * 65)
    if not is_sqlite:
        print("🎉 SUCCESS! OcuPulse is successfully connected to Supabase PostgreSQL!")
    else:
        print("✓ SUCCESS! Local SQLite database verified.")
        print("  To switch to Supabase, add DATABASE_URL=... in your .env file.")
    print("=" * 65)


if __name__ == "__main__":
    main()
