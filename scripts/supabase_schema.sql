-- =============================================================================
-- OcuPulse Retinal Analysis Database Schema for Supabase (PostgreSQL)
--
-- How to run this:
-- 1. Open your Supabase Dashboard: https://supabase.com/dashboard
-- 2. Select your project -> Go to the "SQL Editor" tab on the left.
-- 3. Click "New Query", paste this entire script, and click "Run".
-- =============================================================================

-- Enable UUID extension (standard on Supabase)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- -----------------------------------------------------------------------------
-- 1. Patients Table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS patients (
    id SERIAL PRIMARY KEY,
    patient_id VARCHAR(64) UNIQUE NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc') NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_patients_patient_id ON patients(patient_id);

-- -----------------------------------------------------------------------------
-- 2. Images & Analysis Table (Core Unit of Work)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS images (
    id SERIAL PRIMARY KEY,
    analysis_id VARCHAR(32) UNIQUE,
    patient_id INTEGER REFERENCES patients(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255),
    file_path VARCHAR(512) NOT NULL,
    upload_time TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc') NOT NULL,

    -- Quality Assessment
    quality_score DOUBLE PRECISION,
    quality_grade VARCHAR(16),
    illumination_score DOUBLE PRECISION,
    focus_score DOUBLE PRECISION,
    fov_score DOUBLE PRECISION,

    -- DR Grading Outcomes
    dr_grade INTEGER,
    dr_confidence DOUBLE PRECISION,
    referable_dr BOOLEAN DEFAULT FALSE,
    vision_threatening BOOLEAN DEFAULT FALSE,

    -- Quantitative Vascular Geometry & Metrics
    fractal_dimension DOUBLE PRECISION,
    vessel_density DOUBLE PRECISION,
    vessel_area INTEGER,
    skeleton_density DOUBLE PRECISION,
    average_vessel_width_px DOUBLE PRECISION,
    tortuosity_index DOUBLE PRECISION,
    branching_angle DOUBLE PRECISION,
    vessel_length_px DOUBLE PRECISION,
    branch_points INTEGER,
    endpoints INTEGER,

    -- Lesion Counts
    microaneurysm_count INTEGER DEFAULT 0,
    exudate_count INTEGER DEFAULT 0,
    hemorrhage_count INTEGER DEFAULT 0,
    neovascularization_count INTEGER DEFAULT 0,
    drusen_count INTEGER DEFAULT 0,

    -- Provenance & Metadata
    matlab_analysis TEXT,
    processing_time DOUBLE PRECISION,
    model_version VARCHAR(32),
    details_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_images_analysis_id ON images(analysis_id);
CREATE INDEX IF NOT EXISTS idx_images_upload_time ON images(upload_time DESC);
CREATE INDEX IF NOT EXISTS idx_images_patient_id ON images(patient_id);
CREATE INDEX IF NOT EXISTS idx_images_dr_grade ON images(dr_grade);
CREATE INDEX IF NOT EXISTS idx_images_referable ON images(referable_dr);

-- -----------------------------------------------------------------------------
-- 3. Reports Table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reports (
    id SERIAL PRIMARY KEY,
    image_id INTEGER UNIQUE NOT NULL REFERENCES images(id) ON DELETE CASCADE,
    report_path VARCHAR(512) NOT NULL,
    report_format VARCHAR(8) DEFAULT 'HTML' NOT NULL,
    is_shared BOOLEAN DEFAULT FALSE NOT NULL,
    share_token VARCHAR(64) UNIQUE,
    generated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc') NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_reports_image_id ON reports(image_id);
CREATE INDEX IF NOT EXISTS idx_reports_share_token ON reports(share_token);

-- -----------------------------------------------------------------------------
-- 4. Analysis Logs Table (Audit Trail)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS analysis_logs (
    id SERIAL PRIMARY KEY,
    image_id INTEGER NOT NULL REFERENCES images(id) ON DELETE CASCADE,
    step_name VARCHAR(64) NOT NULL,
    start_time TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc') NOT NULL,
    end_time TIMESTAMP WITHOUT TIME ZONE,
    status VARCHAR(16) DEFAULT 'Processing' NOT NULL,
    metrics TEXT,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_analysis_logs_image_id ON analysis_logs(image_id);

-- -----------------------------------------------------------------------------
-- 5. Simulink Telemedicine Simulations Table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS simulink_simulations (
    id SERIAL PRIMARY KEY,
    simulation_name VARCHAR(64) NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc') NOT NULL,

    -- Inputs
    patient_volume INTEGER NOT NULL,
    bandwidth_mbps DOUBLE PRECISION NOT NULL,
    processing_throughput DOUBLE PRECISION NOT NULL,
    review_capacity INTEGER NOT NULL,
    operating_hours INTEGER,

    -- Outputs
    total_cost DOUBLE PRECISION,
    cost_per_patient DOUBLE PRECISION,
    throughput_per_day INTEGER,
    backlog_after_year INTEGER,
    optimized_params TEXT,
    recommendations TEXT,
    source VARCHAR(16) DEFAULT 'python-fallback' NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_simulink_simulations_created_at ON simulink_simulations(created_at DESC);
