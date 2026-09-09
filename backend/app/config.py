"""
OcuPulse Central Configuration

Single source of truth for filesystem paths, server settings, computer-vision
pipeline parameters, clinical grading thresholds, and integration flags.

Every value can be overridden through an environment variable so the same code
runs unchanged in local development, in Docker, and behind an Nginx reverse
proxy.

Note on the ML layer
--------------------
OcuPulse ships a *deterministic classical computer-vision* implementation of the
grading, lesion-detection and explainability stages. No PyTorch / TensorFlow
runtime and no trained weights are required. The thresholds below are therefore
hand-calibrated decision boundaries rather than learned parameters, and the
``ModelPaths`` block exists so a trained network can be dropped in later without
touching call sites.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Filesystem layout & Environment Loading
# ---------------------------------------------------------------------------

APP_DIR: str = os.path.dirname(os.path.abspath(__file__))       # .../backend/app
BACKEND_DIR: str = os.path.dirname(APP_DIR)                     # .../backend
PROJECT_ROOT: str = os.path.dirname(BACKEND_DIR)                # .../ocupluse

# Automatically load environment variables from .env files
try:
    from dotenv import load_dotenv
    for _env_candidate in (
        os.path.join(PROJECT_ROOT, ".env"),
        os.path.join(BACKEND_DIR, ".env"),
        os.path.join(APP_DIR, ".env"),
    ):
        if os.path.isfile(_env_candidate):
            load_dotenv(_env_candidate, override=True)
except ImportError:
    pass


def _env_str(key: str, default: str) -> str:
    """Read a string setting, falling back to ``default`` when unset or blank."""
    value = os.environ.get(key)
    if value is None or value.strip() == "":
        return default
    return value


def _env_int(key: str, default: int) -> int:
    """Read an integer setting, tolerating malformed overrides."""
    value = os.environ.get(key)
    if value is None or value.strip() == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _env_float(key: str, default: float) -> float:
    """Read a float setting, tolerating malformed overrides."""
    value = os.environ.get(key)
    if value is None or value.strip() == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _env_bool(key: str, default: bool) -> bool:
    """Read a boolean setting from the usual truthy/falsy spellings."""
    value = os.environ.get(key)
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on", "y"}


def _env_path(key: str, default: str) -> str:
    """Read a filesystem path, expanding ``~`` and making it absolute."""
    return os.path.abspath(os.path.expanduser(_env_str(key, default)))


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ServerSettings:
    """FastAPI / Uvicorn runtime settings."""

    host: str = _env_str("OCUPULSE_HOST", "0.0.0.0")
    port: int = _env_int("OCUPULSE_PORT", 8000)
    reload: bool = _env_bool("OCUPULSE_RELOAD", False)
    log_level: str = _env_str("OCUPULSE_LOG_LEVEL", "info")

    app_name: str = "OcuPulse API"
    version: str = "1.0.0"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"

    #: Origins permitted by the CORS middleware. ``*`` keeps the local Vite dev
    #: server working on any port; narrow this in production.
    cors_origins: Tuple[str, ...] = tuple(
        o.strip()
        for o in _env_str("OCUPULSE_CORS_ORIGINS", "*").split(",")
        if o.strip()
    )


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class StorageSettings:
    """Database, sample images, scratch uploads and generated reports."""

    #: Explicit connection URL (e.g. Supabase PostgreSQL: postgresql://postgres:pass@db.xyz.supabase.co:5432/postgres)
    database_url: str = _env_str("DATABASE_URL", _env_str("SUPABASE_DB_URL", ""))

    #: Optional Supabase project URL and keys for cloud storage or auth
    supabase_url: str = _env_str("SUPABASE_URL", "")
    supabase_key: str = _env_str("SUPABASE_KEY", _env_str("SUPABASE_ANON_KEY", ""))

    #: Local SQLite fallback database path when DATABASE_URL is unset
    database_path: str = _env_path(
        "OCUPULSE_DB_PATH", os.path.join(BACKEND_DIR, "oculpulse.db")
    )
    sample_dir: str = _env_path(
        "OCUPULSE_SAMPLE_DIR", os.path.join(BACKEND_DIR, "sample_data")
    )
    upload_dir: str = _env_path(
        "OCUPULSE_UPLOAD_DIR", os.path.join(BACKEND_DIR, "storage", "uploads")
    )
    report_dir: str = _env_path(
        "OCUPULSE_REPORT_DIR", os.path.join(BACKEND_DIR, "storage", "reports")
    )
    data_dir: str = _env_path(
        "OCUPULSE_DATA_DIR", os.path.join(PROJECT_ROOT, "data")
    )
    model_dir: str = _env_path(
        "OCUPULSE_MODEL_DIR", os.path.join(PROJECT_ROOT, "models")
    )

    #: History pages are capped so the dashboard stays responsive.
    history_page_size: int = _env_int("OCUPULSE_HISTORY_PAGE_SIZE", 50)

    #: Uploaded originals are transient scratch data and are pruned on startup.
    retain_uploads: bool = _env_bool("OCUPULSE_RETAIN_UPLOADS", False)
    upload_ttl_hours: int = _env_int("OCUPULSE_UPLOAD_TTL_HOURS", 24)


# ---------------------------------------------------------------------------
# Ingestion limits
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class UploadSettings:
    """Validation limits applied to every inbound retinal photograph."""

    max_file_bytes: int = _env_int("OCUPULSE_MAX_UPLOAD_MB", 25) * 1024 * 1024
    allowed_extensions: Tuple[str, ...] = (
        ".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff",
    )
    allowed_content_types: Tuple[str, ...] = (
        "image/png", "image/jpeg", "image/bmp", "image/tiff",
    )

    min_dimension_px: int = _env_int("OCUPULSE_MIN_DIMENSION", 100)
    max_dimension_px: int = _env_int("OCUPULSE_MAX_DIMENSION", 6000)

    #: Below this standard deviation an image is treated as blank/solid colour.
    min_intensity_std: float = _env_float("OCUPULSE_MIN_INTENSITY_STD", 3.0)


# ---------------------------------------------------------------------------
# Computer-vision pipeline
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PipelineSettings:
    """Preprocessing, segmentation and geometry parameters."""

    #: Longest edge after the standardising resize. Keeps inference inside the
    #: 30 s budget while preserving enough resolution for micro-vessels.
    target_max_dim: int = _env_int("OCUPULSE_TARGET_MAX_DIM", 900)
    upscale_min_dim: int = _env_int("OCUPULSE_UPSCALE_MIN_DIM", 400)
    upscale_target_dim: int = _env_int("OCUPULSE_UPSCALE_TARGET_DIM", 600)

    # ROI (field-of-view) detection
    roi_luminance_threshold: int = _env_int("OCUPULSE_ROI_THRESHOLD", 15)
    roi_erosion_margin: int = _env_int("OCUPULSE_ROI_EROSION", 6)
    roi_min_area_fraction: float = _env_float("OCUPULSE_ROI_MIN_AREA_FRACTION", 0.15)

    # CLAHE
    clahe_clip_limit: float = _env_float("OCUPULSE_CLAHE_CLIP", 3.0)
    clahe_tile_grid: Tuple[int, int] = (8, 8)

    # Vessel segmentation
    tophat_kernel_radius: int = _env_int("OCUPULSE_TOPHAT_RADIUS", 9)
    adaptive_block_size: int = _env_int("OCUPULSE_ADAPTIVE_BLOCK", 31)
    adaptive_c: float = _env_float("OCUPULSE_ADAPTIVE_C", -3.0)
    otsu_relaxation: float = _env_float("OCUPULSE_OTSU_RELAXATION", 0.85)
    min_vessel_component_px: int = _env_int("OCUPULSE_MIN_VESSEL_PX", 20)

    # Overlay cosmetics (BGR)
    overlay_color: Tuple[int, int, int] = (0, 255, 230)
    overlay_alpha: float = _env_float("OCUPULSE_OVERLAY_ALPHA", 0.65)

    #: Whole-pipeline wall-clock budget, in seconds.
    inference_budget_sec: float = _env_float("OCUPULSE_INFERENCE_BUDGET_SEC", 30.0)


# ---------------------------------------------------------------------------
# Image quality / gradeability gate
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class QualitySettings:
    """Technical quality scoring and the ungradeable-image gate."""

    # Normalisation denominators for the composite score.
    sharpness_reference: float = _env_float("OCUPULSE_SHARPNESS_REF", 450.0)
    contrast_reference: float = _env_float("OCUPULSE_CONTRAST_REF", 0.45)
    coverage_reference: float = _env_float("OCUPULSE_COVERAGE_REF", 45.0)

    weights: Tuple[float, float, float, float] = (0.35, 0.25, 0.20, 0.20)

    good_threshold: float = _env_float("OCUPULSE_QUALITY_GOOD", 0.70)
    moderate_threshold: float = _env_float("OCUPULSE_QUALITY_MODERATE", 0.45)

    #: Below this composite score the image is rejected as ungradeable and the
    #: report asks for a recapture instead of emitting a grade.
    gradeable_threshold: float = _env_float("OCUPULSE_QUALITY_GRADEABLE", 0.30)

    #: Minimum retinal field coverage for a grade to be meaningful.
    min_roi_coverage_percent: float = _env_float("OCUPULSE_MIN_ROI_COVERAGE", 25.0)

    #: Minimum Laplacian variance before focus is considered too soft to grade.
    min_sharpness: float = _env_float("OCUPULSE_MIN_SHARPNESS", 40.0)


# ---------------------------------------------------------------------------
# Landmarks (optic disc + fovea)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LandmarkSettings:
    """Optic-disc and fovea localisation used for macula-relative lesion metrics."""

    #: Optic disc diameter as a fraction of the ROI bounding-box width.
    disc_diameter_fraction: float = _env_float("OCUPULSE_DISC_DIAMETER_FRACTION", 0.17)

    #: The fovea sits roughly 2.5 disc diameters temporal to the disc centre.
    fovea_offset_disc_diameters: float = _env_float("OCUPULSE_FOVEA_OFFSET_DD", 2.5)

    #: Percentile of the *brightness-excess* map used to select the disc core.
    #: The disc covers roughly 2-3% of a standard field, so the top 2% of the
    #: excess distribution lands inside it.
    disc_excess_percentile: float = _env_float("OCUPULSE_DISC_EXCESS_PERCENTILE", 98.0)

    #: Large-scale background blur sigma, expressed in expected disc radii. The
    #: illumination field (vignette + choroidal gradient) varies over hundreds of
    #: pixels while the disc varies over tens, so a wide blur isolates the
    #: former. Thresholding absolute brightness instead lets the bright central
    #: plateau merge with the disc and drags the centroid off-target.
    disc_background_radius_scale: float = _env_float("OCUPULSE_DISC_BACKGROUND_SCALE", 4.0)

    #: The disc boundary is taken where brightness excess falls to this fraction
    #: of its peak. The percentile-thresholded core is deliberately smaller than
    #: the true disc, so the radius is grown back out to this level.
    disc_edge_excess_fraction: float = _env_float("OCUPULSE_DISC_EDGE_FRACTION", 0.25)

    #: Lesions within this many disc diameters of the fovea are "macular".
    macula_radius_disc_diameters: float = _env_float("OCUPULSE_MACULA_RADIUS_DD", 1.0)


# ---------------------------------------------------------------------------
# Lesion detection
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LesionSettings:
    """Classical detectors for microaneurysms, haemorrhages and exudates."""

    #: Smallest accepted lesion blob, as a fraction of ROI area. Prevents single
    #: sensor-noise pixels from being reported as microaneurysms. At a 900 px
    #: field this admits blobs of roughly 20 px and up, which matches the true
    #: size of a microaneurysm (50-100 um) at fundus-camera resolution.
    min_lesion_area_fraction: float = _env_float("OCUPULSE_MIN_LESION_AREA_FRAC", 6.0e-5)
    max_lesion_area_fraction: float = _env_float("OCUPULSE_MAX_LESION_AREA_FRAC", 0.02)

    #: Gaussian sigma applied to the channel before morphological filtering, as
    #: a fraction of the image's smaller side. Suppresses pixel-level sensor
    #: noise, which otherwise produces hundreds of spurious blobs, while
    #: preserving lesion-scale structure.
    preblur_sigma_fraction: float = _env_float("OCUPULSE_LESION_PREBLUR", 0.0022)

    # Microaneurysms / haemorrhages: dark red blobs relative to local background.
    #: Cutoff is ``mean + sigma * std`` of the response inside the ROI, and never
    #: below ``mean + min_contrast``. High sigma values are required because
    #: fundus images carry substantial sensor noise.
    dark_lesion_sigma: float = _env_float("OCUPULSE_DARK_LESION_SIGMA", 4.5)
    dark_min_contrast: float = _env_float("OCUPULSE_DARK_MIN_CONTRAST", 10.0)

    # Exudates: bright yellow-white lipid deposits.
    bright_lesion_sigma: float = _env_float("OCUPULSE_BRIGHT_LESION_SIGMA", 4.5)
    bright_min_contrast: float = _env_float("OCUPULSE_BRIGHT_MIN_CONTRAST", 14.0)

    #: Microaneurysms are small and round; haemorrhages are larger and irregular.
    microaneurysm_max_area_fraction: float = _env_float(
        "OCUPULSE_MA_MAX_AREA_FRAC", 1.2e-4
    )
    microaneurysm_min_circularity: float = _env_float(
        "OCUPULSE_MA_MIN_CIRCULARITY", 0.35
    )

    #: Absolute-intensity gate, in standard deviations of ROI intensity.
    #: A local-contrast filter fires on any locally peaked structure, including
    #: the ordinary background between adjacent vessels. Requiring the blob to
    #: also be genuinely bright (exudate) or genuinely dark (haemorrhage) in
    #: absolute terms removes those, because real lesions stand well clear of
    #: the retinal mean.
    bright_absolute_margin: float = _env_float("OCUPULSE_BRIGHT_ABS_MARGIN", 0.85)
    dark_absolute_margin: float = _env_float("OCUPULSE_DARK_ABS_MARGIN", 0.85)

    #: Vessel-exclusion halo as a fraction of image size. Must be comparable to
    #: the blob-scale filter kernel, otherwise the bright background trapped
    #: between two dark vessels registers as an exudate.
    vessel_exclusion_fraction: float = _env_float("OCUPULSE_VESSEL_EXCLUSION", 0.030)

    #: Exclude the optic disc from lesion counts - its bright rim and dark cup
    #: otherwise masquerade as exudate and haemorrhage.
    disc_exclusion_diameters: float = _env_float("OCUPULSE_DISC_EXCLUSION_DD", 1.0)

    # Colour cues for the marker overlay (BGR).
    marker_colors: Dict[str, Tuple[int, int, int]] = field(default_factory=lambda: {
        "microaneurysm": (60, 60, 255),    # red
        "hemorrhage": (40, 40, 200),       # deep red
        "exudate": (0, 215, 255),          # gold
        "drusen": (180, 200, 255),         # pale gold
    })


# ---------------------------------------------------------------------------
# Diabetic retinopathy grading
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GradingSettings:
    """APTOS-style 5-level grading and the referable-DR (level 2+) decision."""

    #: Canonical APTOS 2019 label set.
    levels: Tuple[int, ...] = (0, 1, 2, 3, 4)
    level_names: Tuple[str, ...] = (
        "No DR",
        "Mild NPDR",
        "Moderate NPDR",
        "Severe NPDR",
        "Proliferative DR",
    )

    #: Level at or above which a patient is flagged for referral.
    referable_threshold: int = _env_int("OCUPULSE_REFERABLE_THRESHOLD", 2)

    # Decision boundaries on the lesion burden index (lesion area as a fraction
    # of ROI area, weighted by lesion class) combined with vascular change.
    mild_burden: float = _env_float("OCUPULSE_GRADE_MILD", 0.0015)
    moderate_burden: float = _env_float("OCUPULSE_GRADE_MODERATE", 0.0060)
    severe_burden: float = _env_float("OCUPULSE_GRADE_SEVERE", 0.0150)
    proliferative_burden: float = _env_float("OCUPULSE_GRADE_PROLIFERATIVE", 0.0300)

    #: Neovascularisation proxy: abnormal vessel density growth plus a high
    #: count of irregular blobs near the arcade. Above this, escalate to level 4.
    neovascularisation_index: float = _env_float("OCUPULSE_NEOVASC_INDEX", 0.55)

    #: A grade is suppressed to "ungradeable" when confidence falls below this.
    min_grade_confidence: float = _env_float("OCUPULSE_MIN_GRADE_CONFIDENCE", 0.20)

    # Clinical operating targets from the project specification, surfaced in the
    # validation report so measured performance can be compared against them.
    target_referable_sensitivity: float = 0.90
    target_referable_specificity: float = 0.85


# ---------------------------------------------------------------------------
# Confidence calibration
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ConfidenceSettings:
    """Temperature scaling and evidence aggregation for reported confidence."""

    #: Temperature applied to the softmax over grading logits. Values > 1 soften
    #: over-confident raw scores; this is the classical analogue of the
    #: temperature-scaling calibration step used for neural classifiers.
    temperature: float = _env_float("OCUPULSE_CONFIDENCE_TEMPERATURE", 1.35)

    #: Relative weight of each evidence channel in the aggregate score.
    weight_lesion_evidence: float = _env_float("OCUPULSE_CONF_W_LESION", 0.45)
    weight_vascular_evidence: float = _env_float("OCUPULSE_CONF_W_VASCULAR", 0.30)
    weight_image_quality: float = _env_float("OCUPULSE_CONF_W_QUALITY", 0.25)

    #: Confidence below this is reported as "low" and triggers a review prompt.
    low_confidence_threshold: float = _env_float("OCUPULSE_CONF_LOW", 0.40)
    high_confidence_threshold: float = _env_float("OCUPULSE_CONF_HIGH", 0.75)


# ---------------------------------------------------------------------------
# Explainability
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ExplainabilitySettings:
    """Saliency / Grad-CAM-style attribution map generation."""

    #: Multi-scale Gaussian set used to build the saliency response.
    saliency_sigmas: Tuple[float, ...] = (1.0, 2.0, 4.0, 8.0)

    #: Attribution maps are rendered at this size before being overlaid.
    heatmap_output_dim: int = _env_int("OCUPULSE_HEATMAP_DIM", 512)

    #: Colormap used for the rendered heatmap (cv2.COLORMAP_JET).
    colormap: int = 2

    #: Blend weight of the heatmap over the fundus photograph.
    overlay_alpha: float = _env_float("OCUPULSE_HEATMAP_ALPHA", 0.45)

    #: Fraction of the highest-saliency pixels treated as "attended region"
    #: when correlating attention with detected lesions.
    topk_fraction: float = _env_float("OCUPULSE_HEATMAP_TOPK", 0.02)


# ---------------------------------------------------------------------------
# MATLAB / Simulink integration
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MatlabSettings:
    """MATLAB Engine bridge configuration.

    MATLAB is optional. When the Engine API or a MATLAB installation is absent
    the bridge reports ``available == False`` and callers fall back to the
    equivalent Python implementation, so every endpoint keeps working.
    """

    enabled: bool = _env_bool("OCUPULSE_MATLAB_ENABLED", True)
    script_dir: str = _env_path(
        "OCUPULSE_MATLAB_SCRIPTS",
        os.path.join(APP_DIR, "matlab", "matlab_scripts"),
    )
    canonical_script_dir: str = _env_path(
        "OCUPULSE_MATLAB_CANONICAL",
        os.path.join(PROJECT_ROOT, "matlab_scripts"),
    )
    simulink_dir: str = _env_path(
        "OCUPULSE_SIMULINK_DIR", os.path.join(APP_DIR, "matlab", "simulink")
    )
    timeout_sec: float = _env_float("OCUPULSE_MATLAB_TIMEOUT", 120.0)

    #: Names of the scripts the bridge knows how to call.
    known_scripts: Tuple[str, ...] = (
        "analyse_retina",
        "vessel_geometry",
        "fractal_analytics",
        "lesion_quantification",
        "severity_grading",
    )


# ---------------------------------------------------------------------------
# Real-time progress (WebSocket)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class WebSocketSettings:
    """Streaming progress channel used by the analysis studio."""

    enabled: bool = _env_bool("OCUPULSE_WS_ENABLED", True)
    path: str = _env_str("OCUPULSE_WS_PATH", "/api/ws/analyze/{job_id}")
    heartbeat_sec: float = _env_float("OCUPULSE_WS_HEARTBEAT", 15.0)
    max_clients_per_job: int = _env_int("OCUPULSE_WS_MAX_CLIENTS", 8)

    #: Ordered pipeline stages broadcast to the UI. Labels are shown verbatim.
    stages: Tuple[Tuple[str, str], ...] = (
        ("validation", "Validating image"),
        ("preprocessing", "Isolating retinal field of view"),
        ("segmentation", "Segmenting retinal vessels"),
        ("skeletonization", "Extracting vessel centerlines"),
        ("geometry", "Computing topology and geometry"),
        ("lesions", "Detecting lesions"),
        ("grading", "Grading severity"),
        ("explainability", "Building attribution heatmap"),
        ("quality", "Assessing image quality"),
        ("report", "Assembling screening report"),
    )


# ---------------------------------------------------------------------------
# Batch analysis / throughput
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BatchSettings:
    """Batch endpoint and Simulink throughput-model defaults."""

    max_batch_size: int = _env_int("OCUPULSE_MAX_BATCH", 25)
    worker_concurrency: int = _env_int("OCUPULSE_WORKERS", 2)

    # District-level screening programme assumptions used by the resource
    # optimiser model (100k+ patient cohort).
    cohort_size: int = _env_int("OCUPULSE_COHORT_SIZE", 100_000)
    mean_image_mb: float = _env_float("OCUPULSE_MEAN_IMAGE_MB", 2.4)
    uplink_mbps: float = _env_float("OCUPULSE_UPLINK_MBPS", 20.0)
    seconds_per_image: float = _env_float("OCUPULSE_SEC_PER_IMAGE", 12.0)
    specialist_reviews_per_day: int = _env_int("OCUPULSE_REVIEWS_PER_DAY", 60)
    referable_prevalence: float = _env_float("OCUPULSE_REFERABLE_PREVALENCE", 0.18)


# ---------------------------------------------------------------------------
# Public benchmark datasets
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DatasetSpec:
    """Acquisition metadata for one benchmark dataset."""

    key: str
    name: str
    purpose: str
    url: str
    gated: bool
    license_note: str


DATASETS: Tuple[DatasetSpec, ...] = (
    DatasetSpec(
        key="aptos2019",
        name="APTOS 2019 Blindness Detection",
        purpose="5-level DR grading (train + calibration)",
        url="https://www.kaggle.com/c/aptos2019-blindness-detection",
        gated=True,
        license_note="Kaggle competition rules; requires account and rule acceptance.",
    ),
    DatasetSpec(
        key="idrid",
        name="IDRiD (Indian Diabetic Retinopathy Image Dataset)",
        purpose="Lesion-level annotations: microaneurysms, exudates, haemorrhages",
        url="https://idrid.grand-challenge.org/",
        gated=True,
        license_note="Registration and data-use agreement required.",
    ),
    DatasetSpec(
        key="drive",
        name="DRIVE (Digital Retinal Images for Vessel Extraction)",
        purpose="Vessel segmentation ground truth",
        url="https://drive.grand-challenge.org/",
        gated=True,
        license_note="Free registration; 40 images with manual annotations.",
    ),
    DatasetSpec(
        key="messidor2",
        name="Messidor-2",
        purpose="External validation of referable DR",
        url="https://www.adcis.net/en/Download-Third-Party/Messidor2.html",
        gated=True,
        license_note="Request-based academic access.",
    ),
    DatasetSpec(
        key="stare",
        name="STARE (Structured Analysis of the Retina)",
        purpose="Secondary vessel segmentation validation",
        url="https://cecas.clemson.edu/~ahoover/stare/",
        gated=False,
        license_note="Freely available for research.",
    ),
    DatasetSpec(
        key="chase_db1",
        name="CHASE_DB1",
        purpose="Paediatric vessel segmentation validation",
        url="https://blogs.kingston.ac.uk/retinal/chasedb1/",
        gated=False,
        license_note="Freely available for research.",
    ),
)


# ---------------------------------------------------------------------------
# Optional trained-model artefacts (not required by the shipped pipeline)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ModelPaths:
    """Where trained weights would live if a deep-learning stage is added.

    All entries are optional. ``exists()`` reports whether the artefact is
    present so callers can upgrade from the classical path transparently.
    """

    root: str = _env_path("OCUPULSE_MODEL_DIR", os.path.join(PROJECT_ROOT, "models"))
    vessel_unet: str = "vessel_unet.pt"
    dr_classifier: str = "dr_classifier_efficientnet_b3.pt"
    lesion_detector: str = "lesion_detector.pt"
    calibration: str = "temperature_calibration.json"

    def path_for(self, name: str) -> str:
        return os.path.join(self.root, getattr(self, name))

    def exists(self, name: str) -> bool:
        return os.path.isfile(self.path_for(name))

    def available(self) -> List[str]:
        """Names of the model artefacts currently present on disk."""
        return [
            n for n in ("vessel_unet", "dr_classifier", "lesion_detector", "calibration")
            if self.exists(n)
        ]


# ---------------------------------------------------------------------------
# Aggregate settings object
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Settings:
    """Root configuration container imported as ``from ..config import settings``."""

    server: ServerSettings = field(default_factory=ServerSettings)
    storage: StorageSettings = field(default_factory=StorageSettings)
    uploads: UploadSettings = field(default_factory=UploadSettings)
    pipeline: PipelineSettings = field(default_factory=PipelineSettings)
    quality: QualitySettings = field(default_factory=QualitySettings)
    landmarks: LandmarkSettings = field(default_factory=LandmarkSettings)
    lesions: LesionSettings = field(default_factory=LesionSettings)
    grading: GradingSettings = field(default_factory=GradingSettings)
    confidence: ConfidenceSettings = field(default_factory=ConfidenceSettings)
    explainability: ExplainabilitySettings = field(default_factory=ExplainabilitySettings)
    matlab: MatlabSettings = field(default_factory=MatlabSettings)
    websocket: WebSocketSettings = field(default_factory=WebSocketSettings)
    batch: BatchSettings = field(default_factory=BatchSettings)
    models: ModelPaths = field(default_factory=ModelPaths)

    #: Non-diagnostic disclaimer repeated verbatim across API and reports.
    disclaimer: str = (
        "OcuPulse is an AI-assisted retinal image analysis and screening tool. "
        "It is not intended to provide a definitive medical diagnosis. Results "
        "must be interpreted in conjunction with comprehensive clinical "
        "examination by a qualified ophthalmologist or eye-care professional."
    )

    # -- Flat aliases -------------------------------------------------------
    # The API, ORM and MATLAB layers address configuration with module-style
    # UPPERCASE names. These delegate to the nested dataclasses above so there
    # is exactly one source of truth for every value.

    @property
    def ALLOWED_EXTENSIONS(self) -> Tuple[str, ...]:
        """File extensions accepted by the upload endpoints."""
        return self.uploads.allowed_extensions

    @property
    def MAX_UPLOAD_SIZE(self) -> int:
        """Largest accepted upload, in bytes."""
        return self.uploads.max_file_bytes

    @property
    def UPLOAD_DIR(self) -> str:
        """Directory uploaded originals are written to."""
        return self.storage.upload_dir

    @property
    def REPORT_DIR(self) -> str:
        """Directory generated clinical reports are written to."""
        return self.storage.report_dir

    @property
    def MODEL_DIR(self) -> str:
        """Directory optional trained-model artefacts are loaded from."""
        return self.models.root

    @property
    def DATABASE_URL(self) -> str:
        """SQLAlchemy connection URL (Supabase PostgreSQL or local SQLite)."""
        raw_url = os.environ.get("DATABASE_URL") or os.environ.get("SUPABASE_DB_URL") or self.storage.database_url
        if raw_url and raw_url.strip():
            url = raw_url.strip()
            # Normalize PostgreSQL dialect for SQLAlchemy / psycopg2
            if url.startswith("postgres://"):
                url = "postgresql+psycopg2://" + url[len("postgres://"):]
            elif url.startswith("postgresql://") and not url.startswith("postgresql+"):
                url = "postgresql+psycopg2://" + url[len("postgresql://"):]
            return url
        return "sqlite:///{}".format(self.storage.database_path)

    @property
    def is_postgres(self) -> bool:
        """Return True if configured database is PostgreSQL/Supabase."""
        return self.DATABASE_URL.startswith("postgresql")

    @property
    def DR_CLASSIFIER_PATH(self) -> str:
        """Absolute path to the optional EfficientNet-B3 weight file."""
        return self.models.path_for("dr_classifier")

    @property
    def MATLAB_SCRIPTS_PATH(self) -> str:
        """Engine-facing MATLAB wrappers added to the MATLAB path."""
        return self.matlab.script_dir

    @property
    def SIMULINK_MODELS_PATH(self) -> str:
        """Directory holding the ``.slx`` telemedicine workflow models."""
        return self.matlab.simulink_dir

    def ensure_directories(self) -> None:
        """Create writable runtime directories if they are missing.

        Called at import time by ``app.main``: the report directory is mounted
        with ``StaticFiles`` before the lifespan hook runs, and SQLAlchemy needs
        the parent of the database file to exist before ``create_all``.
        """
        paths = [
            self.storage.upload_dir,
            self.storage.report_dir,
            self.storage.data_dir,
            self.models.root,
        ]
        if not self.is_postgres and self.storage.database_path:
            paths.append(os.path.dirname(self.storage.database_path))

        for path in paths:
            if path:
                os.makedirs(path, exist_ok=True)

    def describe(self) -> Dict[str, object]:
        """Serialise the effective configuration for ``/api/config`` and logs.

        No secrets are held in configuration, so the block is safe to expose.
        """
        db_type = "postgresql" if self.is_postgres else "sqlite"
        return {
            "version": self.server.version,
            "database_type": db_type,
            "is_supabase": self.is_postgres and ("supabase" in self.DATABASE_URL.lower()),
            "paths": {
                "project_root": PROJECT_ROOT,
                "database": "postgresql (cloud)" if self.is_postgres else self.storage.database_path,
                "samples": self.storage.sample_dir,
                "uploads": self.storage.upload_dir,
                "reports": self.storage.report_dir,
                "models": self.models.root,
            },
            "pipeline": {
                "target_max_dim": self.pipeline.target_max_dim,
                "inference_budget_sec": self.pipeline.inference_budget_sec,
            },
            "grading": {
                "levels": list(self.grading.levels),
                "level_names": list(self.grading.level_names),
                "referable_threshold": self.grading.referable_threshold,
            },
            "quality": {
                "gradeable_threshold": self.quality.gradeable_threshold,
                "good_threshold": self.quality.good_threshold,
            },
            "confidence": {
                "temperature": self.confidence.temperature,
                "low_threshold": self.confidence.low_confidence_threshold,
                "high_threshold": self.confidence.high_confidence_threshold,
            },
            "matlab": {
                "enabled": self.matlab.enabled,
                "script_dir": self.matlab.script_dir,
                "canonical_script_dir": self.matlab.canonical_script_dir,
            },
            "websocket": {
                "enabled": self.websocket.enabled,
                "stages": [key for key, _ in self.websocket.stages],
            },
            "trained_models_present": self.models.available(),
        }


#: Process-wide configuration instance.
settings = Settings()
