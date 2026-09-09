"""
OcuPulse Input Validation Utilities

Guards every boundary where untrusted data enters the system: uploaded files,
URL path parameters, demo identifiers and decoded image arrays.

Two concerns are handled here that the computer-vision layer deliberately does
not know about:

1. **Filesystem safety** - uploaded filenames are attacker-controlled and are
   never trusted as paths. :func:`sanitize_filename` strips directory
   components and rejects traversal sequences before anything touches disk.
2. **Clinical gradeability** - a technically unusable photograph must not be
   given a severity grade. :func:`assess_gradeability` turns the quality
   assessment into an explicit accept/reject decision plus recapture advice,
   so downstream code can short-circuit instead of reporting a misleading
   grade for a blurred image.
"""

from __future__ import annotations

import os
import re
import unicodedata
from typing import Any, Dict, Iterable, List, Optional, Tuple

import cv2
import numpy as np

from ..config import settings

#: ``OCU-YYYYMMDD-HHMMSS-XXXXXX`` as produced by the analysis endpoint.
ANALYSIS_ID_PATTERN = re.compile(r"^OCU-\d{8}-\d{6}-[0-9A-Fa-f]{6}$")

#: Conservative filename allow-list: alphanumerics plus a few safe separators.
_SAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9._-]+")

#: Upper bound on a sanitised filename length, keeping extension intact.
MAX_FILENAME_LENGTH = 120


# ---------------------------------------------------------------------------
# Filename / path safety
# ---------------------------------------------------------------------------

def sanitize_filename(filename: Optional[str], fallback: str = "fundus_image.png") -> str:
    """
    Reduce an untrusted filename to a safe basename.

    Strips any directory component (in either POSIX or Windows form), removes
    traversal sequences, normalises unicode and replaces disallowed characters
    with underscores. The result is always a plain basename, so it can be
    joined onto a storage directory without escaping it.

    Args:
        filename: Raw client-supplied filename, possibly ``None``.
        fallback: Value returned when nothing usable remains.

    Returns:
        A safe basename string.
    """
    if not filename:
        return fallback

    # Neutralise control characters and normalise unicode before splitting.
    name = unicodedata.normalize("NFKC", str(filename))
    name = "".join(ch for ch in name if ch.isprintable())

    # Clients may send either separator; take the basename of both forms.
    name = os.path.basename(name.replace("\\", "/"))

    # Drop traversal sequences that survived basename extraction.
    name = name.replace("..", "_")
    name = _SAFE_FILENAME_CHARS.sub("_", name).strip("._")

    if not name:
        return fallback

    root, ext = os.path.splitext(name)
    ext = ext.lower()
    if ext not in settings.uploads.allowed_extensions:
        ext = ""

    if not root:
        return fallback

    # Keep the total length bounded without losing the extension.
    max_root = max(8, MAX_FILENAME_LENGTH - len(ext))
    if len(root) > max_root:
        root = root[:max_root]

    return f"{root}{ext}" if ext else root


def validate_filename(filename: Optional[str]) -> Tuple[bool, Optional[str]]:
    """
    Check that a client-supplied filename carries an allowed image extension.

    Args:
        filename: Raw filename from the upload.

    Returns:
        Tuple of ``(is_valid, error_message)``.
    """
    if not filename or not str(filename).strip():
        return False, "No filename was supplied with the upload."

    safe = sanitize_filename(filename)
    ext = os.path.splitext(safe)[1].lower()

    if ext not in settings.uploads.allowed_extensions:
        allowed = ", ".join(e.lstrip(".").upper() for e in settings.uploads.allowed_extensions)
        return False, (
            f"Unsupported file format '{ext or 'unknown'}'. "
            f"Please upload one of: {allowed}."
        )

    return True, None


def validate_content_type(content_type: Optional[str]) -> Tuple[bool, Optional[str]]:
    """
    Check a declared MIME type against the image allow-list.

    A missing content type is tolerated because several HTTP clients omit it
    for multipart bodies; the decoder is the real gate in that case.

    Args:
        content_type: Value of the multipart part's ``Content-Type``.

    Returns:
        Tuple of ``(is_valid, error_message)``.
    """
    if not content_type:
        return True, None

    declared = content_type.split(";")[0].strip().lower()
    if declared in settings.uploads.allowed_content_types:
        return True, None

    # Browsers occasionally send a generic binary type for images.
    if declared in ("application/octet-stream", "binary/octet-stream"):
        return True, None

    return False, (
        f"Unsupported content type '{declared}'. Expected an image payload "
        f"({', '.join(settings.uploads.allowed_content_types)})."
    )


def validate_file_size(size_bytes: int) -> Tuple[bool, Optional[str]]:
    """
    Check an upload's byte length against the configured ceiling.

    Args:
        size_bytes: Number of bytes in the payload.

    Returns:
        Tuple of ``(is_valid, error_message)``.
    """
    if size_bytes <= 0:
        return False, "Uploaded file is empty (0 bytes)."

    limit = settings.uploads.max_file_bytes
    if size_bytes > limit:
        return False, (
            f"File exceeds the maximum allowable size "
            f"({size_bytes / (1024 * 1024):.1f} MB > {limit // (1024 * 1024)} MB)."
        )

    return True, None


def validate_upload(
    filename: Optional[str],
    size_bytes: int,
    content_type: Optional[str] = None,
) -> Tuple[bool, Optional[str]]:
    """
    Run the complete inbound-file gate: name, MIME type and size.

    Args:
        filename: Raw client filename.
        size_bytes: Payload length in bytes.
        content_type: Optional declared MIME type.

    Returns:
        Tuple of ``(is_valid, first_error_message)``.
    """
    for is_valid, error in (
        validate_filename(filename),
        validate_content_type(content_type),
        validate_file_size(size_bytes),
    ):
        if not is_valid:
            return False, error

    return True, None


# ---------------------------------------------------------------------------
# Identifier safety
# ---------------------------------------------------------------------------

def validate_analysis_id(analysis_id: Optional[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate a history identifier before it is used in a database lookup.

    The strict format check keeps malformed or hostile values away from the
    SQL layer even though queries are parameterised.

    Args:
        analysis_id: Identifier from a URL path parameter.

    Returns:
        Tuple of ``(is_valid, error_message)``.
    """
    if not analysis_id or not str(analysis_id).strip():
        return False, "Analysis ID is required."

    if not ANALYSIS_ID_PATTERN.match(str(analysis_id).strip()):
        return False, (
            f"Malformed analysis ID '{analysis_id}'. "
            "Expected the format OCU-YYYYMMDD-HHMMSS-XXXXXX."
        )

    return True, None


def validate_demo_id(
    demo_id: Optional[str],
    allowed_ids: Iterable[str],
) -> Tuple[bool, Optional[str]]:
    """
    Check a requested demo sample against the known catalogue.

    Args:
        demo_id: Client-requested sample identifier.
        allowed_ids: Identifiers that actually exist on disk.

    Returns:
        Tuple of ``(is_valid, error_message)``.
    """
    allowed = list(allowed_ids)

    if not demo_id or not str(demo_id).strip():
        return False, "Demo sample ID is required."

    if demo_id not in allowed:
        return False, (
            f"Invalid demo sample ID '{demo_id}'. "
            f"Available samples: {', '.join(allowed) if allowed else 'none'}."
        )

    return True, None


# ---------------------------------------------------------------------------
# Image payload validation
# ---------------------------------------------------------------------------

def decode_image_bytes(payload: Optional[bytes]) -> Tuple[Optional[np.ndarray], Optional[str]]:
    """
    Decode raw bytes into a BGR image array, reporting failures as messages.

    ``cv2.imdecode`` returns ``None`` for anything it cannot parse, including
    truncated uploads and non-image files renamed with an image extension, so
    the outcome is converted into an explicit error string here rather than
    propagating a ``None`` array into the pipeline.

    Args:
        payload: Raw file bytes.

    Returns:
        Tuple of ``(image_or_None, error_message_or_None)``.
    """
    if not payload:
        return None, "No image bytes were received."

    is_valid, error = validate_file_size(len(payload))
    if not is_valid:
        return None, error

    try:
        buffer = np.frombuffer(payload, np.uint8)
        image = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
    except Exception as exc:  # pragma: no cover - defensive decode guard
        return None, f"Failed to decode image data: {exc}"

    if image is None:
        return None, (
            "Failed to decode the image file. Ensure it is a valid, uncorrupted "
            "retinal photograph in PNG, JPEG, BMP or TIFF format."
        )

    return image, None


def validate_image_array(image: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate a decoded image array's type, shape, resolution and contrast.

    This is the configuration-driven counterpart to
    :func:`backend.app.processing.preprocessing.validate_image`; thresholds come
    from :data:`~backend.app.config.settings` so deployments can retune them
    without editing pipeline code.

    Args:
        image: Candidate image, expected to be a numpy array.

    Returns:
        Tuple of ``(is_valid, error_message)``.
    """
    if image is None or not isinstance(image, np.ndarray):
        return False, "Invalid image payload: unable to decode image data."

    if image.size == 0:
        return False, "Uploaded image is empty (0 bytes)."

    if image.ndim not in (2, 3):
        return False, f"Unsupported image dimensions: {image.shape}"

    if image.ndim == 3 and image.shape[2] not in (1, 3, 4):
        return False, f"Unsupported channel count: {image.shape[2]}"

    height, width = image.shape[:2]
    limits = settings.uploads

    if height < limits.min_dimension_px or width < limits.min_dimension_px:
        return False, (
            f"Image resolution too small ({width}x{height} px). "
            f"Minimum required is {limits.min_dimension_px}x{limits.min_dimension_px} px."
        )

    if height > limits.max_dimension_px or width > limits.max_dimension_px:
        return False, (
            f"Image resolution too large ({width}x{height} px). "
            f"Maximum supported is {limits.max_dimension_px}x{limits.max_dimension_px} px."
        )

    if float(np.std(image)) < limits.min_intensity_std:
        return False, (
            "Image contains almost zero contrast (appears blank or solid colour). "
            "Please capture a properly illuminated retinal photograph."
        )

    return True, None


def validate_mask(mask: Any, reference_shape: Optional[Tuple[int, ...]] = None) -> Tuple[bool, Optional[str]]:
    """
    Validate a binary mask produced by an earlier pipeline stage.

    Args:
        mask: Candidate mask array.
        reference_shape: Expected ``(height, width)`` when masks must align.

    Returns:
        Tuple of ``(is_valid, error_message)``.
    """
    if mask is None or not isinstance(mask, np.ndarray):
        return False, "Mask is missing or is not a numpy array."

    if mask.ndim != 2:
        return False, f"Mask must be 2-dimensional, got shape {mask.shape}."

    if reference_shape is not None and mask.shape[:2] != tuple(reference_shape[:2]):
        return False, (
            f"Mask shape {mask.shape[:2]} does not match the reference "
            f"image shape {tuple(reference_shape[:2])}."
        )

    return True, None


# ---------------------------------------------------------------------------
# Numeric helpers
# ---------------------------------------------------------------------------

def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    """Clamp ``value`` into ``[low, high]``, mapping NaN to ``low``."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return low
    return float(max(low, min(high, value)))


def safe_round(value: Any, digits: int = 2, default: float = 0.0) -> float:
    """Round ``value`` defensively, returning ``default`` for non-finite input."""
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    if not np.isfinite(result):
        return default
    return round(result, digits)


# ---------------------------------------------------------------------------
# Clinical gradeability gate
# ---------------------------------------------------------------------------

def assess_gradeability(quality: Dict[str, Any]) -> Dict[str, Any]:
    """
    Decide whether an image is technically good enough to be graded.

    A severity grade computed from a blurred, under-exposed or badly cropped
    photograph is worse than no grade at all, because it can be mistaken for a
    clinical finding. This function applies explicit rejection rules and, when
    the image is rejected, returns concrete recapture advice instead.

    Args:
        quality: Dictionary produced by
            :func:`backend.app.processing.quality.assess_image_quality`,
            containing ``score``, ``label`` and a ``metrics`` block.

    Returns:
        Dictionary with keys:
            - ``gradeable`` (bool): whether grading should proceed.
            - ``reasons`` (list[str]): each failed check, human readable.
            - ``recapture_advice`` (list[str]): actionable remediation steps.
            - ``message`` (str): single-sentence summary for the report.
    """
    thresholds = settings.quality
    metrics = quality.get("metrics", {}) if isinstance(quality, dict) else {}

    score = safe_round(quality.get("score", 0.0) if isinstance(quality, dict) else 0.0, 3)
    sharpness = safe_round(metrics.get("sharpness_laplacian", 0.0), 2)
    coverage = safe_round(metrics.get("roi_coverage_percent", 0.0), 2)
    contrast = safe_round(metrics.get("rms_contrast", 0.0), 4)
    uniformity = safe_round(metrics.get("illumination_uniformity", 0.0), 3)

    reasons: List[str] = []
    advice: List[str] = []

    if score < thresholds.gradeable_threshold:
        reasons.append(
            f"Overall technical quality score {score:.2f} is below the gradeable "
            f"threshold {thresholds.gradeable_threshold:.2f}."
        )
        advice.append("Recapture the fundus photograph under standard imaging conditions.")

    if sharpness < thresholds.min_sharpness:
        reasons.append(
            f"Focus measure (Laplacian variance) {sharpness:.1f} is below the "
            f"minimum {thresholds.min_sharpness:.1f}, indicating motion blur or misfocus."
        )
        advice.append("Stabilise the camera and re-focus on the macula before recapture.")

    if coverage < thresholds.min_roi_coverage_percent:
        reasons.append(
            f"Retinal field of view covers only {coverage:.1f}% of the frame, below the "
            f"required {thresholds.min_roi_coverage_percent:.1f}%."
        )
        advice.append("Centre the optic disc and macula in the frame and use a wider field setting.")

    if contrast < 0.10:
        reasons.append(
            f"RMS contrast {contrast:.3f} is very low, suggesting under-exposure or haze."
        )
        advice.append("Increase illumination or apply the camera's exposure compensation.")

    if uniformity < 0.45:
        reasons.append(
            f"Illumination uniformity {uniformity:.2f} indicates strong vignetting or "
            "partial eyelid/lash shadowing."
        )
        advice.append("Ask the patient to open wider and re-position the light source.")

    gradeable = len(reasons) == 0

    if gradeable:
        message = (
            f"Image quality is sufficient for automated grading "
            f"(score {score:.2f}, label '{quality.get('label', 'Unknown')}')."
        )
    else:
        message = (
            "Image is UNGRADEABLE for technical reasons. No severity grade is issued; "
            "a recapture is recommended before screening can proceed."
        )

    return {
        "gradeable": gradeable,
        "reasons": reasons,
        "recapture_advice": advice,
        "message": message,
        "quality_score": score,
        "thresholds": {
            "gradeable": thresholds.gradeable_threshold,
            "min_sharpness": thresholds.min_sharpness,
            "min_roi_coverage_percent": thresholds.min_roi_coverage_percent,
        },
    }
