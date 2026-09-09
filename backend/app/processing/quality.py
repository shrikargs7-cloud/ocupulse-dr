import cv2
import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from skimage import exposure, filters
from scipy import ndimage

from app.config import settings
from app.schemas import QualityGrade

class QualityAssessor:
    """Assess fundus image quality for DR screening"""
    
    def __init__(self):
        self.min_focus_threshold = 0.15
        self.min_illumination_threshold = 0.3
        self.min_fov_threshold = 0.7
        
    def quick_assess(self, image_path: str) -> Dict[str, Any]:
        """Quick quality assessment for upload"""
        img = cv2.imread(image_path)
        if img is None:
            return {"score": 0, "grade": QualityGrade.REJECT, "error": "Cannot read image"}
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Focus score (variance of Laplacian)
        focus = cv2.Laplacian(gray, cv2.CV_64F).var()
        focus_score = min(focus / 1000, 1.0)
        
        # Illumination score
        illumination = gray.mean() / 255.0
        illumination_score = 1 - abs(illumination - 0.5) * 2
        
        # Field of view (FOV) detection
        fov_mask = self._detect_fov(gray)
        fov_score = np.sum(fov_mask) / fov_mask.size
        
        # Overall score
        score = (focus_score + illumination_score + fov_score) / 3
        
        # Determine grade
        if score < 0.4:
            grade = QualityGrade.REJECT
            recommendations = "Image quality insufficient. Please recapture with better focus and lighting."
        elif score < 0.6:
            grade = QualityGrade.BORDERLINE
            recommendations = "Image quality is borderline. Consider enhancement."
        else:
            grade = QualityGrade.GOOD
            recommendations = "Image quality is good for analysis."
        
        return {
            "score": score,
            "grade": grade,
            "focus": focus_score,
            "illumination": illumination_score,
            "fov": fov_score,
            "recommendations": recommendations
        }
    
    def full_assess(self, image_path: str) -> Dict[str, Any]:
        """Full quality assessment with detailed metrics"""
        img = cv2.imread(image_path)
        if img is None:
            return {"error": "Cannot read image"}
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 1. Focus assessment
        focus_score, focus_metrics = self._assess_focus(gray)
        
        # 2. Illumination assessment
        illumination_score, illum_metrics = self._assess_illumination(gray)
        
        # 3. Field of view assessment
        fov_score, fov_mask = self._assess_fov(gray)
        
        # 4. Color balance assessment
        color_score, color_metrics = self._assess_color(img)
        
        # 5. Artifact detection
        artifact_score, artifacts = self._detect_artifacts(img)
        
        # Combined score
        overall_score = (focus_score * 0.25 + illumination_score * 0.25 + 
                        fov_score * 0.20 + color_score * 0.15 + artifact_score * 0.15)
        
        # Determine grade
        if overall_score < 0.4:
            grade = QualityGrade.REJECT
            recommendations = "Image quality unacceptable. Please recapture."
        elif overall_score < 0.6:
            grade = QualityGrade.BORDERLINE
            recommendations = "Image quality borderline. Enhancement recommended."
        else:
            grade = QualityGrade.GOOD
            recommendations = "Image quality suitable for analysis."
        
        return {
            "score": overall_score,
            "grade": grade,
            "focus": {"score": focus_score, "metrics": focus_metrics},
            "illumination": {"score": illumination_score, "metrics": illum_metrics},
            "fov": {"score": fov_score},
            "color": {"score": color_score, "metrics": color_metrics},
            "artifacts": {"score": artifact_score, "detected": artifacts},
            "recommendations": recommendations,
            "fov_mask": fov_mask.tolist() if fov_mask is not None else None
        }
    
    def _assess_focus(self, gray: np.ndarray) -> Tuple[float, Dict]:
        """Assess image focus using multiple metrics"""
        # Laplacian variance
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        lap_var = laplacian.var()
        
        # Tenengrad focus measure
        gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        tenengrad = np.mean(gx*gx + gy*gy)
        
        # Normalize
        lap_score = min(lap_var / 2000, 1.0)
        ten_score = min(tenengrad / 500, 1.0)
        
        # Combined focus score
        focus_score = 0.6 * lap_score + 0.4 * ten_score
        
        metrics = {
            "laplacian_variance": float(lap_var),
            "tenengrad": float(tenengrad),
            "normalized_laplacian": float(lap_score),
            "normalized_tenengrad": float(ten_score)
        }
        
        return focus_score, metrics
    
    def _assess_illumination(self, gray: np.ndarray) -> Tuple[float, Dict]:
        """Assess illumination uniformity"""
        # Overall brightness
        mean_intensity = gray.mean() / 255.0
        std_intensity = gray.std() / 255.0
        
        # Illumination uniformity (using polynomial surface fitting)
        h, w = gray.shape
        x = np.linspace(-1, 1, w)
        y = np.linspace(-1, 1, h)
        X, Y = np.meshgrid(x, y)
        
        # Fit quadratic surface
        A = np.vstack([X.flatten(), Y.flatten(), X.flatten()*Y.flatten(), 
                       X.flatten()**2, Y.flatten()**2, np.ones(len(X.flatten()))]).T
        coeffs, _, _, _ = np.linalg.lstsq(A, gray.flatten(), rcond=None)
        
        # Reconstruction error as uniformity measure
        fitted = (coeffs[0]*X + coeffs[1]*Y + coeffs[2]*X*Y + 
                 coeffs[3]*X**2 + coeffs[4]*Y**2 + coeffs[5])
        error = np.abs(gray - fitted).mean() / 255.0
        
        # Score
        brightness_score = 1 - abs(mean_intensity - 0.5) * 2
        uniformity_score = 1 - min(error / 0.3, 1.0)
        illumination_score = 0.5 * brightness_score + 0.5 * uniformity_score
        
        metrics = {
            "mean_intensity": float(mean_intensity),
            "std_intensity": float(std_intensity),
            "uniformity_error": float(error),
            "brightness_quality": float(brightness_score),
            "uniformity_quality": float(uniformity_score)
        }
        
        return illumination_score, metrics
    
    def _assess_fov(self, gray: np.ndarray) -> Tuple[float, np.ndarray]:
        """Detect and assess field of view"""
        # Threshold to find FOV
        _, thresh = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)
        
        # Morphological operations
        kernel = np.ones((20, 20), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        
        # Find largest contour (FOV)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return 0.0, None
        
        largest = max(contours, key=cv2.contourArea)
        fov_mask = np.zeros_like(gray)
        cv2.drawContours(fov_mask, [largest], -1, 255, -1)
        
        # Calculate FOV metrics
        fov_area = cv2.contourArea(largest)
        image_area = gray.shape[0] * gray.shape[1]
        fov_ratio = fov_area / image_area
        
        # Check for circularity (fundus should be roughly circular)
        perimeter = cv2.arcLength(largest, True)
        circularity = 4 * np.pi * fov_area / (perimeter * perimeter) if perimeter > 0 else 0
        
        # Score
        fov_score = fov_ratio * (0.7 + 0.3 * min(circularity / 0.8, 1.0))
        fov_score = min(fov_score, 1.0)
        
        return fov_score, fov_mask
    
    def _assess_color(self, img: np.ndarray) -> Tuple[float, Dict]:
        """Assess color balance and quality"""
        # Convert to LAB for better color assessment
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Color balance (should be around neutral)
        a_mean = a.mean() - 128
        b_mean = b.mean() - 128
        color_balance = 1 - (abs(a_mean) + abs(b_mean)) / 128
        
        # Color saturation
        saturation = np.std(lab, axis=2).mean()
        saturation_score = min(saturation / 50, 1.0)
        
        # Color consistency (low variance in color channels)
        l_var = l.var()
        a_var = a.var()
        b_var = b.var()
        consistency = 1 - min((a_var + b_var) / (l_var + 1), 1.0)
        
        color_score = 0.4 * color_balance + 0.3 * saturation_score + 0.3 * consistency
        
        metrics = {
            "color_balance": float(color_balance),
            "saturation": float(saturation),
            "saturation_score": float(saturation_score),
            "consistency": float(consistency),
            "a_channel_mean": float(a_mean),
            "b_channel_mean": float(b_mean)
        }
        
        return color_score, metrics
    
    def _detect_artifacts(self, img: np.ndarray) -> Tuple[float, list]:
        """Detect image artifacts (dust, glare, etc.)"""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        artifacts = []
        
        # 1. Glare detection (bright spots)
        glare_thresh = 240
        glare_mask = gray > glare_thresh
        glare_count = np.sum(glare_mask)
        glare_ratio = glare_count / gray.size
        
        if glare_ratio > 0.01:
            artifacts.append("glare")
        
        # 2. Dust detection (dark spots)
        dust_thresh = 20
        dust_mask = gray < dust_thresh
        dust_count = np.sum(dust_mask)
        dust_ratio = dust_count / gray.size
        
        if dust_ratio > 0.005:
            artifacts.append("dust")
        
        # 3. Hair detection (thin dark lines)
        edges = cv2.Canny(gray, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=100, maxLineGap=10)
        if lines is not None and len(lines) > 5:
            artifacts.append("hair")
        
        # 4. Blur detection (already covered in focus assessment)
        
        # Score
        artifact_score = 1 - (len(artifacts) * 0.2)
        artifact_score = max(artifact_score, 0)
        
        return artifact_score, artifacts
    
    def _detect_fov(self, gray: np.ndarray) -> np.ndarray:
        """Simple FOV detection for quick assessment"""
        _, thresh = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)
        kernel = np.ones((20, 20), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        return thresh > 0


# ---------------------------------------------------------------------------
# Array-based assessment used by the in-memory CV pipeline
# ---------------------------------------------------------------------------
#
# ``QualityAssessor`` above works on file paths and serves the upload endpoint.
# The two functions below work on the arrays the analysis pipeline already holds
# in memory, and produce the shape declared by ``ImageQuality`` /
# ``ScreeningSummary`` in ``app.schemas``.

def _roi_boolean(roi_mask: np.ndarray, shape: Tuple[int, ...]) -> np.ndarray:
    """Coerce a ROI mask to a boolean array matching ``shape``."""
    mask = np.asarray(roi_mask)
    if mask.ndim == 3:
        mask = mask[:, :, 0]
    if mask.shape != shape[:2]:
        mask = cv2.resize(
            mask.astype(np.uint8), (shape[1], shape[0]), interpolation=cv2.INTER_NEAREST
        )
    return mask > 0


def assess_image_quality(
    processed_image: np.ndarray,
    green_channel: np.ndarray,
    roi_mask: np.ndarray,
    vessel_mask: Optional[np.ndarray] = None,
) -> Dict[str, Any]:
    """
    Score the technical quality of a preprocessed fundus photograph.

    Four normalised terms are blended with the configured weights: focus
    (variance of the Laplacian on the green channel, the standard no-reference
    sharpness measure), RMS contrast, retinal field coverage, and illumination
    uniformity (the 10th-to-90th percentile ratio of a heavily blurred
    luminance field, which is insensitive to vessels and lesions).

    Args:
        processed_image: Standardised BGR image from the preprocessing stage.
        green_channel: Extracted green channel, where vessel/lesion contrast peaks.
        roi_mask: Binary retinal field-of-view mask.
        vessel_mask: Optional vessel mask, currently unused for scoring but
            accepted so the pipeline can pass its full state.

    Returns:
        Dictionary matching the ``ImageQuality`` schema: ``score``, ``label``,
        ``description`` and a ``metrics`` block of the five raw measurements.
    """
    config = settings.quality

    green = np.asarray(green_channel)
    if green.ndim == 3:
        green = green[:, :, 0]
    green = green.astype(np.float32)
    shape = green.shape

    inside = _roi_boolean(roi_mask, shape)
    roi_pixels = int(np.count_nonzero(inside))

    if roi_pixels == 0:
        # No retinal field at all: every term is zero and the image cannot be
        # graded. Report it rather than dividing by an empty selection.
        return {
            "score": 0.0,
            "label": "Poor",
            "description": (
                "No retinal field of view was detected in this image. The "
                "photograph may be mis-framed, severely under-exposed, or not a "
                "fundus image at all."
            ),
            "metrics": {
                "sharpness_laplacian": 0.0,
                "rms_contrast": 0.0,
                "illumination_uniformity": 0.0,
                "roi_coverage_percent": 0.0,
                "mean_intensity": 0.0,
            },
        }

    # --- Focus: variance of the Laplacian, measured inside the retinal field ---
    laplacian = cv2.Laplacian(green, cv2.CV_32F)
    sharpness = float(np.var(laplacian[inside]))

    # --- Contrast: RMS deviation of the green channel inside the field ---
    region = green[inside]
    rms_contrast = float(np.std(region) / 255.0)
    mean_intensity = float(np.mean(region))

    # --- Coverage: how much of the frame is usable retina ---
    roi_coverage_percent = float(roi_pixels / float(shape[0] * shape[1]) * 100.0)

    # --- Illumination uniformity: p10/p90 of a blurred luminance field ---
    # Blurring at a wide sigma averages out vessels, lesions and noise so only
    # the illumination gradient survives.
    blur_sigma = max(4.0, float(min(shape)) / 24.0)
    illumination = cv2.GaussianBlur(green, (0, 0), sigmaX=blur_sigma)
    illum_region = illumination[inside]
    p90 = float(np.percentile(illum_region, 90))
    p10 = float(np.percentile(illum_region, 10))
    illumination_uniformity = float(np.clip(p10 / p90, 0.0, 1.0)) if p90 > 1e-6 else 0.0

    w_sharp, w_contrast, w_coverage, w_uniform = config.weights
    score = (
        w_sharp * float(np.clip(sharpness / max(config.sharpness_reference, 1e-6), 0.0, 1.0))
        + w_contrast * float(np.clip(rms_contrast / max(config.contrast_reference, 1e-6), 0.0, 1.0))
        + w_coverage * float(np.clip(roi_coverage_percent / max(config.coverage_reference, 1e-6), 0.0, 1.0))
        + w_uniform * illumination_uniformity
    )
    score = round(float(np.clip(score, 0.0, 1.0)), 4)

    if score >= config.good_threshold:
        label = "Good"
    elif score >= config.moderate_threshold:
        label = "Moderate"
    else:
        label = "Poor"

    weakest = min(
        [
            (sharpness / max(config.sharpness_reference, 1e-6), "focus"),
            (rms_contrast / max(config.contrast_reference, 1e-6), "contrast"),
            (roi_coverage_percent / max(config.coverage_reference, 1e-6), "field coverage"),
            (illumination_uniformity, "illumination uniformity"),
        ],
        key=lambda item: item[0],
    )[1]

    description = (
        "Technical quality is {label}. Retinal field coverage is {coverage:.1f}% "
        "with a sharpness of {sharp:.0f} and illumination uniformity of "
        "{uniform:.2f}. The limiting factor is {weakest}."
    ).format(label=label.lower(), coverage=roi_coverage_percent,
              sharp=sharpness, uniform=illumination_uniformity, weakest=weakest)

    if score < config.gradeable_threshold:
        description += (
            " This image falls below the gradeable threshold; a recapture is "
            "recommended before any screening conclusion is drawn."
        )

    return {
        "score": score,
        "label": label,
        "description": description,
        "metrics": {
            "sharpness_laplacian": round(sharpness, 3),
            "rms_contrast": round(rms_contrast, 4),
            "illumination_uniformity": round(illumination_uniformity, 4),
            "roi_coverage_percent": round(roi_coverage_percent, 2),
            "mean_intensity": round(mean_intensity, 2),
        },
    }


def generate_screening_summary(
    geometry: Dict[str, Any],
    quality: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Synthesise a plain-language screening summary from measured features.

    The wording is deliberately non-diagnostic: it reports what was measured and
    whether the image was gradeable, and always routes the clinical decision to a
    qualified eye-care professional.

    Args:
        geometry: Output of :func:`analyze_vessel_geometry`.
        quality: Output of :func:`assess_image_quality`.

    Returns:
        Dictionary matching the ``ScreeningSummary`` schema.
    """
    score = float(quality.get("score", 0.0))
    label = str(quality.get("label", "Poor"))
    gradeable = score >= settings.quality.gradeable_threshold

    vessel_density = float(geometry.get("vessel_density", 0.0))
    fractal_dimension = float(geometry.get("fractal_dimension", 0.0))
    branching_index = float(geometry.get("branching_index", 0.0))
    branch_points = int(geometry.get("branch_points", 0))
    endpoints = int(geometry.get("endpoints", 0))
    vessel_length = float(geometry.get("vessel_length_pixels", 0.0))

    observations: List[str] = []

    if gradeable:
        observations.append(
            "Image quality is sufficient for automated screening "
            "(composite score {:.2f}, rated {}).".format(score, label)
        )
    else:
        observations.append(
            "Image quality is below the gradeable threshold (composite score "
            "{:.2f}, rated {}); vascular measurements may be unreliable.".format(score, label)
        )

    observations.append(
        "Vascular network occupies {:.2f}% of the retinal field across "
        "{:,.0f} pixels of centrelines.".format(vessel_density, vessel_length)
    )
    observations.append(
        "Fractal dimension {:.3f} - {}.".format(
            fractal_dimension,
            "within the healthy arborisation range of roughly 1.20 to 1.90"
            if 1.20 <= fractal_dimension <= 1.90
            else "outside the typical healthy range, which can indicate "
                 "vascular remodelling or a segmentation limited by image quality",
        )
    )
    observations.append(
        "Topology: {} branch points and {} endpoints, a branching index of "
        "{:.2f} per 1000 pixels of vessel.".format(branch_points, endpoints, branching_index)
    )

    if gradeable:
        headline = "Retinal vasculature quantified from a gradeable image"
        screening_status = "REVIEW_RECOMMENDED"
        recommendation = (
            "These quantitative vascular measurements are ready for clinical "
            "review. Any referral decision should be made by a qualified "
            "ophthalmologist or eye-care professional together with a "
            "comprehensive examination."
        )
    else:
        headline = "Image quality insufficient for reliable screening"
        screening_status = "UNGRADEABLE_RECAPTURE"
        recommendation = (
            "Recapture the photograph before screening. Improve focus, ensure "
            "the retinal field fills the frame, and reduce uneven illumination "
            "or eyelash and reflection artefacts."
        )

    full_text = "{}. {}".format(headline, " ".join(observations))

    return {
        "headline": headline,
        "observations": observations,
        "full_text": full_text,
        "screening_status": screening_status,
        "recommendation": recommendation,
        "disclaimer": settings.disclaimer,
    }