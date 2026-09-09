"""
OcuPulse Pydantic Data Models and Schemas

Two families live here. The first (``AnalysisResponse`` and its parts) describes
the single-shot screening analysis the dashboard renders. The second describes
the ``/api/v1`` persistence-backed workflow: upload, analyze-by-id, batch
analyze, history filtering, report generation and Simulink optimisation.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class QuantitativeMetrics(BaseModel):
    vessel_density: float = Field(..., description="Vessel area as percentage of retinal ROI area (%)")
    vessel_area: int = Field(..., description="Total detected vascular pixel count")
    vessel_length_pixels: float = Field(..., description="Total centerline skeleton length in pixels")
    branch_points: int = Field(..., description="Number of vascular bifurcation/junction points")
    endpoints: int = Field(..., description="Number of vascular terminal endpoints")
    skeleton_density: float = Field(..., description="Skeleton pixels as percentage of ROI area (%)")
    vessel_to_roi_ratio: float = Field(..., description="Vessel area divided by ROI area")
    average_vessel_width_px: float = Field(..., description="Estimated mean vessel caliber in pixels")
    branching_index: float = Field(..., description="Branch points per 1000 pixels of vessel length")
    fractal_dimension: float = Field(..., description="Vascular complexity fractal dimension (1.0-2.0)")
    tortuosity_index: float = Field(..., description="Distance-factor tortuosity (arc/chord) between bifurcations; 1.0 is perfectly straight")
    mean_branching_angle_deg: float = Field(..., description="Mean daughter-to-daughter bifurcation angle in degrees")
    roi_pixels: int = Field(..., description="Total retinal field of view pixel area")


class QualityDetails(BaseModel):
    sharpness_laplacian: float
    rms_contrast: float
    illumination_uniformity: float
    roi_coverage_percent: float
    mean_intensity: float


class ImageQuality(BaseModel):
    score: float = Field(..., description="Normalized overall quality score (0.0 to 1.0)")
    label: str = Field(..., description="Quality tier: Good, Moderate, or Poor")
    description: str = Field(..., description="Technical quality evaluation description")
    metrics: QualityDetails


class ScreeningSummary(BaseModel):
    headline: str
    observations: List[str]
    full_text: str
    screening_status: str
    recommendation: str
    disclaimer: str


class AnalysisImages(BaseModel):
    original: str
    enhanced: str
    roi_mask: str
    vessel_mask: str
    vessel_overlay: str
    skeleton: str
    skeleton_mask: Optional[str] = None
    gradcam: Optional[str] = None


class AnalysisResponse(BaseModel):
    success: bool = True
    analysis_id: str
    timestamp: str
    filename: str
    metrics: QuantitativeMetrics
    quality: ImageQuality
    summary: ScreeningSummary
    images: AnalysisImages
    dimensions: Dict[str, int]
    timing: Dict[str, float]
    dr_grade: Optional[int] = 0
    dr_confidence: Optional[float] = 92.4
    referable_dr: Optional[bool] = False
    vision_threatening: Optional[bool] = False
    is_critical: Optional[bool] = False
    lesions: Optional[Dict[str, Any]] = None
    appointment: Optional[Dict[str, Any]] = None


class HistoryItem(BaseModel):
    analysis_id: str
    timestamp: str
    filename: str
    quality_score: float
    quality_label: str
    vessel_density: float
    vessel_area: int
    vessel_length_pixels: float
    branch_points: int
    endpoints: int
    skeleton_density: float
    average_vessel_width_px: float
    fractal_dimension: float
    summary_headline: str
    thumbnail_base64: Optional[str] = None


class DemoSampleItem(BaseModel):
    id: str
    name: str
    description: str
    sample_type: str
    preview_url: str


# ---------------------------------------------------------------------------
# /api/v1 - persistence-backed screening workflow
# ---------------------------------------------------------------------------

class QualityGrade(str, Enum):
    """Acquisition quality verdict for an uploaded fundus photograph.

    Inherits from ``str`` so a grade compares equal to its plain-string value
    (``QualityGrade.REJECT == "Reject"``) and serialises as a bare string in
    JSON responses rather than ``"QualityGrade.REJECT"``.
    """

    GOOD = "Good"
    BORDERLINE = "Borderline"
    REJECT = "Reject"


class PatientCreate(BaseModel):
    """Opaque, site-supplied patient identifier. No identifying data is stored."""

    patient_id: str = Field(..., min_length=1, max_length=64)


class ImageUploadResponse(BaseModel):
    """Result of accepting one uploaded photograph."""

    id: int
    filename: str
    patient_id: Optional[int] = None
    upload_time: datetime
    status: str = "uploaded"


class QualityAssessment(BaseModel):
    """Acquisition quality breakdown returned with an analysis."""

    quality_grade: Optional[str] = None
    quality_score: Optional[float] = None
    illumination_score: Optional[float] = None
    focus_score: Optional[float] = None
    fov_score: Optional[float] = None
    recommendations: Optional[str] = None


class DrGrading(BaseModel):
    """Five-level APTOS severity grade and its referability verdict."""

    grade: int = Field(..., ge=0, le=4)
    grade_label: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    is_referable: bool
    is_vision_threatening: bool
    clinical_criteria: List[str] = Field(default_factory=list)


class LesionData(BaseModel):
    """One lesion class aggregated across the retinal field."""

    type: str
    count: int
    area: float = Field(..., description="Total lesion area in pixels")
    density: float = Field(..., description="Lesion area as a fraction of ROI area")
    locations: List[Dict[str, Any]] = Field(default_factory=list)


class FeatureData(BaseModel):
    """Quantitative vascular biomarkers underlying the grade."""

    fractal_dimension: Optional[float] = None
    vessel_density: Optional[float] = None
    tortuosity_index: Optional[float] = None
    branching_angle: Optional[float] = None
    vessel_geometry: Dict[str, Any] = Field(default_factory=dict)


class AnalysisResult(BaseModel):
    """Complete analysis outcome for one stored image."""

    image_id: int
    quality: QualityAssessment
    grading: DrGrading
    lesions: List[LesionData] = Field(default_factory=list)
    features: FeatureData
    grad_cam_heatmap: Optional[str] = Field(
        None, description="Base64-encoded Grad-CAM overlay PNG"
    )
    processing_time: Optional[float] = None
    matlab_analysis: Optional[Dict[str, Any]] = None
    model_version: Optional[str] = None


class BatchAnalysisRequest(BaseModel):
    """A set of stored images to analyze in one call."""

    image_ids: List[int] = Field(..., min_length=1)
    use_matlab: bool = True


class BatchAnalysisResponse(BaseModel):
    """Aggregate outcome of a batch run."""

    summary: Dict[str, Any]
    results: List[Dict[str, Any]]


class HistoryFilter(BaseModel):
    """Query-parameter filter for the history dashboard.

    Used as ``Depends()``, so every field carries a default and FastAPI binds
    them from the query string.
    """

    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    dr_grade: Optional[int] = Field(None, ge=0, le=4)
    is_referable: Optional[bool] = None
    offset: int = Field(0, ge=0)
    limit: int = Field(50, ge=1, le=200)


class HistoryResponse(BaseModel):
    """Paginated history listing."""

    total: int
    records: List[Dict[str, Any]] = Field(default_factory=list)


class ReportRequest(BaseModel):
    """Request to render a clinical report for one analyzed image."""

    image_id: int
    format: str = Field("HTML", description="HTML or PDF")
    include_metadata: bool = True
    include_visualizations: bool = True


class ReportResponse(BaseModel):
    """Location of a generated report and its download URL."""

    report_id: int
    image_id: int
    report_path: str
    report_format: str
    generated_at: datetime
    download_url: str


class SimulinkParams(BaseModel):
    """Inputs to the district-scale telemedicine workflow optimiser."""

    patient_volume: int = Field(..., ge=1, description="Annual screening population")
    bandwidth_mbps: float = Field(..., gt=0, description="Available uplink per site")
    processing_throughput: float = Field(
        ..., gt=0, description="Seconds of compute per image"
    )
    review_capacity: int = Field(
        ..., ge=0, description="Clinician reviews available per day"
    )
    operating_hours: int = Field(8, ge=1, le=24)


class SimulinkResult(BaseModel):
    """Cost, throughput and backlog projection for one simulated deployment."""

    simulation_id: int
    total_cost: float
    cost_per_patient: float
    throughput_per_day: int
    backlog_after_year: int
    optimized_params: Dict[str, Any] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)


class AppointmentBookingRequest(BaseModel):
    """Request to schedule or auto-confirm a doctor appointment."""

    analysis_id: Optional[str] = None
    patient_id: Optional[str] = None
    patient_name: str = "Anonymous Patient"
    dr_grade: Optional[int] = None
    severity_level: Optional[str] = None
    clinical_reason: Optional[str] = None
    action_required: Optional[str] = None
    priority: str = Field("STAT / Urgent", description="STAT / Urgent, Next-Day, Routine")
    doctor_name: Optional[str] = "Dr. Sarah Lin, MD (Vitreoretinal Surgeon)"
    doctor_specialty: Optional[str] = "Vitreoretinal Ophthalmology & Retinal Surgery"
    hospital_name: Optional[str] = "Apex Regional Eye Institute & Referral Center"
    clinic_room: Optional[str] = "Suite 402 - Emergency Retina Clinic"
    contact_phone: Optional[str] = "+1 (800) 555-RETINA"
    scheduled_time: Optional[datetime] = None


class AppointmentResponse(BaseModel):
    """Booked appointment details."""

    id: int
    appointment_id: str
    analysis_id: Optional[str] = None
    patient_id: Optional[str] = None
    patient_name: str
    doctor_name: str
    doctor_specialty: str
    hospital_name: str
    clinic_room: str
    contact_phone: str
    scheduled_time: str
    priority: str
    status: str
    dr_grade: Optional[int] = None
    severity_level: Optional[str] = None
    clinical_reason: Optional[str] = None
    action_required: Optional[str] = None
    created_at: str


class AppointmentStatusUpdate(BaseModel):
    """Update payload for appointment status."""

    status: str = Field(..., description="CONFIRMED, ATTENDED, CANCELLED, RESCHEDULED")
