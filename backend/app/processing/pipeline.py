"""
OcuPulse Retinal Image Analysis Pipeline Orchestrator

Integrates:
1. Input validation and resizing
2. Retinal Field of View (ROI) detection
3. Green channel extraction
4. CLAHE contrast enhancement
5. Edge-preserving noise reduction
6. Multi-scale vessel segmentation
7. Vessel detection overlay generation
8. Centerline skeletonization
9. Geometric & topological feature extraction
10. Image quality assessment
11. Screening summary synthesis
"""

import time
import base64
import cv2
import numpy as np
from typing import Dict, Any, List, Optional

from .preprocessing import preprocess_fundus_image
from .segmentation import segment_vessels, create_vessel_overlay
from .skeletonization import extract_vessel_skeleton, generate_skeleton_visualizer
from .geometry import analyze_vessel_geometry, calculate_fractal_dimension
from .quality import QualityAssessor, assess_image_quality, generate_screening_summary
from .enhancement import ImageEnhancer
from ..ml.lesion_detector import LESION_TYPES, detect_lesions as detect_lesions_cv


def mat_to_base64_png(img: np.ndarray) -> str:
    """Convert an OpenCV image matrix to a base64 encoded PNG data URI."""
    success, buffer = cv2.imencode('.png', img)
    if not success:
        raise ValueError("Failed to encode image to PNG format")
    b64_str = base64.b64encode(buffer).decode('utf-8')
    return f"data:image/png;base64,{b64_str}"


def analyze_retinal_fundus(
    image: np.ndarray,
    target_max_dim: int = 900
) -> Dict[str, Any]:
    """
    Run complete end-to-end OcuPulse computer vision analysis pipeline on a retinal image.
    
    Args:
        image: Input fundus photograph (BGR uint8)
        target_max_dim: Max processing dimension
        
    Returns:
        Structured dictionary containing metrics, quality, images (base64 PNGs),
        and screening summary.
    """
    start_time = time.time()
    stage_timings = {}
    
    # --- STAGE 1: Preprocessing & Retinal ROI Detection ---
    t0 = time.time()
    preprocessed = preprocess_fundus_image(image, target_max_dim=target_max_dim)
    proc_img = preprocessed["processed_image"]
    roi_mask = preprocessed["roi_mask"]
    green_ch = preprocessed["green_channel"]
    enhanced_img = preprocessed["enhanced_image"]
    denoised_img = preprocessed["denoised_image"]
    stage_timings["preprocessing_sec"] = round(time.time() - t0, 3)
    
    # --- STAGE 2: Vessel Segmentation ---
    t0 = time.time()
    vessel_mask = segment_vessels(denoised_img, roi_mask)
    stage_timings["segmentation_sec"] = round(time.time() - t0, 3)
    
    # --- STAGE 3: Vessel Overlay Generation ---
    t0 = time.time()
    vessel_overlay = create_vessel_overlay(proc_img, vessel_mask, overlay_color=(0, 255, 230), alpha=0.65)
    stage_timings["overlay_sec"] = round(time.time() - t0, 3)
    
    # --- STAGE 4: Skeletonization ---
    t0 = time.time()
    skeleton_mask = extract_vessel_skeleton(vessel_mask)
    stage_timings["skeletonization_sec"] = round(time.time() - t0, 3)
    
    # --- STAGE 5: Geometric & Topological Analysis ---
    t0 = time.time()
    geometry = analyze_vessel_geometry(vessel_mask, skeleton_mask, roi_mask)
    stage_timings["geometry_sec"] = round(time.time() - t0, 3)
    
    # --- STAGE 6: Skeleton Visualizer with Branch & End Markers ---
    skeleton_visualizer = generate_skeleton_visualizer(
        skeleton=skeleton_mask,
        branch_coords=np.array(geometry["branch_coordinates"]),
        endpoint_coords=np.array(geometry["endpoint_coordinates"]),
        base_image=proc_img
    )
    
    # --- STAGE 7: Image Quality Assessment & Summary ---
    t0 = time.time()
    quality = assess_image_quality(proc_img, green_ch, roi_mask, vessel_mask)
    summary = generate_screening_summary(geometry, quality)
    stage_timings["quality_sec"] = round(time.time() - t0, 3)
    
    total_time = round(time.time() - start_time, 3)
    stage_timings["total_execution_sec"] = total_time
    
    # Encode output visualizers as base64 PNG data URLs
    images_dict = {
        "original": mat_to_base64_png(proc_img),
        "enhanced": mat_to_base64_png(enhanced_img),
        "roi_mask": mat_to_base64_png(roi_mask),
        "vessel_mask": mat_to_base64_png(vessel_mask),
        "vessel_overlay": mat_to_base64_png(vessel_overlay),
        "skeleton": mat_to_base64_png(skeleton_visualizer),
        "skeleton_mask": mat_to_base64_png(skeleton_mask)
    }
    
    return {
        "metrics": {
            "vessel_density": geometry["vessel_density"],
            "vessel_area": geometry["vessel_area"],
            "vessel_length_pixels": geometry["vessel_length_pixels"],
            "branch_points": geometry["branch_points"],
            "endpoints": geometry["endpoints"],
            "skeleton_density": geometry["skeleton_density"],
            "vessel_to_roi_ratio": geometry["vessel_to_roi_ratio"],
            "average_vessel_width_px": geometry["average_vessel_width_px"],
            "branching_index": geometry["branching_index"],
            "fractal_dimension": geometry["fractal_dimension"],
            "tortuosity_index": geometry["tortuosity_index"],
            "mean_branching_angle_deg": geometry["mean_branching_angle_deg"],
            "roi_pixels": geometry["roi_pixels"]
        },
        "quality": quality,
        "summary": summary,
        "images": images_dict,
        "dimensions": preprocessed["dimensions"],
        "timing": stage_timings
    }


#: Geometry keys holding per-pixel coordinate lists. They drive overlay drawing
#: but are far too bulky for the API's biomarker payload, so they are dropped
#: from the ``geometry`` dictionary ``AnalysisPipeline.segment_vessels`` returns.
_GEOMETRY_COORDINATE_KEYS = ("branch_coordinates", "endpoint_coordinates")


class AnalysisPipeline:
    """
    Stage-by-stage analysis facade backing the ``/api/v1`` persistence workflow.

    :func:`analyze_retinal_fundus` runs the entire screening pass over an
    in-memory image and returns base64 visualisers for the dashboard. The API
    layer instead needs the stages separately against a stored file, so that it
    can persist intermediate results, bail out early on an ungradeable image,
    and hand individual outputs to the DR classifier, the MATLAB bridge and the
    report generator.

    Every array crossing this boundary is BGR uint8, matching the rest of the CV
    pipeline. :class:`~app.processing.enhancement.ImageEnhancer` works in RGB
    internally, so :meth:`enhance_image` converts back before returning.
    """

    def __init__(self, target_max_dim: int = 900):
        self.target_max_dim = target_max_dim
        self.quality_assessor = QualityAssessor()
        self.enhancer = ImageEnhancer()

    def assess_quality(self, image_path: str) -> Dict[str, Any]:
        """
        Grade the acquisition quality of a stored fundus photograph.

        Args:
            image_path: Path to the uploaded image on disk.

        Returns:
            Dictionary with ``score``, ``grade``, ``focus``, ``illumination``,
            ``fov`` and a ``recommendations`` sentence. ``grade`` is a
            :class:`~app.schemas.QualityGrade`, which subclasses ``str`` so the
            caller's ``grade == "Reject"`` test holds without unpacking it.
        """
        return self.quality_assessor.quick_assess(image_path)

    def enhance_image(self, image_path: str) -> np.ndarray:
        """
        Read a stored photograph and enhance it for downstream analysis.

        Args:
            image_path: Path to the uploaded image on disk.

        Returns:
            Enhanced fundus image as BGR uint8.

        Raises:
            ValueError: If the file cannot be decoded.
        """
        return cv2.cvtColor(self.enhancer.enhance(image_path), cv2.COLOR_RGB2BGR)

    def segment_vessels(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Segment the vasculature and measure its geometry.

        Args:
            image: BGR uint8 fundus photograph.

        Returns:
            Dictionary holding the ``processed_image``, ``roi_mask``,
            ``vessel_mask`` and ``skeleton`` arrays; the headline ``density``,
            ``tortuosity``, ``branching_angle`` and ``fractal_dimension``
            numbers; and ``geometry``, the full JSON-safe measure set.
        """
        preprocessed = preprocess_fundus_image(image, target_max_dim=self.target_max_dim)
        roi_mask = preprocessed["roi_mask"]

        vessel_mask = segment_vessels(preprocessed["denoised_image"], roi_mask)
        skeleton = extract_vessel_skeleton(vessel_mask)
        geometry = analyze_vessel_geometry(vessel_mask, skeleton, roi_mask)

        return {
            "processed_image": preprocessed["processed_image"],
            "roi_mask": roi_mask,
            "vessel_mask": vessel_mask,
            "skeleton": skeleton,
            "density": geometry["vessel_density"],
            "tortuosity": geometry["tortuosity_index"],
            "branching_angle": geometry["mean_branching_angle_deg"],
            "fractal_dimension": geometry["fractal_dimension"],
            "geometry": {
                key: value
                for key, value in geometry.items()
                if key not in _GEOMETRY_COORDINATE_KEYS
            },
        }

    def compute_fractal_dimension(self, mask: np.ndarray) -> float:
        """
        Box-counting fractal dimension of a binary vascular mask.

        The dimension describes whatever mask is supplied, so the value depends
        on the choice: passing the centrelines skeleton yields the classic
        skeletal fractal dimension used in retinal literature, while passing the
        filled vessel mask yields a higher area-based figure. The API passes the
        skeleton; :meth:`segment_vessels` reports the mask-based value in its
        ``geometry`` block.

        Args:
            mask: Binary vessel or skeleton mask.

        Returns:
            Fractal dimension, clamped to the physically meaningful 1.0-1.95.
        """
        return calculate_fractal_dimension(mask)

    def detect_lesions(
        self,
        image: np.ndarray,
        roi_mask: Optional[np.ndarray] = None,
        vessel_mask: Optional[np.ndarray] = None,
        quality: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Detect and quantify retinal lesions.

        Args:
            image: BGR uint8 fundus photograph.
            roi_mask: Precomputed retinal field-of-view mask. Derived from
                ``image`` when omitted.
            vessel_mask: Precomputed vessel mask used to suppress vessels.
                Derived from ``image`` when omitted.
            quality: Optional quality assessment; scales detection reliability.

        Returns:
            Dictionary with a plural count key per detected lesion class
            (``microaneurysms``, ``hemorrhages``, ``exudates``, ``drusen``), a
            ``detected_lesions`` list of per-class aggregates shaped for
            :class:`~app.schemas.LesionData`, and the detector's burden,
            quadrant, landmark and reliability results passed through.

        Neovascularisation is deliberately absent from the result rather than
        reported as a genuine zero: this classical detector delineates
        microaneurysms, haemorrhages, exudates and drusen but makes no attempt
        to segment new vessels. Callers reading
        ``result.get("neovascularization", 0)`` get 0, meaning "not measured by
        this stage", and should not treat it as evidence of absence.
        """
        preprocessed = preprocess_fundus_image(image, target_max_dim=self.target_max_dim)
        processed_image = preprocessed["processed_image"]

        if roi_mask is None:
            roi_mask = preprocessed["roi_mask"]
        if vessel_mask is None:
            vessel_mask = segment_vessels(preprocessed["denoised_image"], roi_mask)

        result = detect_lesions_cv(processed_image, roi_mask, vessel_mask, quality)

        roi_area = max(1, int(np.count_nonzero(roi_mask)))
        counts = result["counts"]

        detected_lesions: List[Dict[str, Any]] = []
        for lesion_type in LESION_TYPES:
            records = [
                record for record in result["lesions"]
                if record.get("type") == lesion_type
            ]
            area_px = float(sum(float(record.get("area_px", 0.0)) for record in records))
            detected_lesions.append({
                "type": lesion_type,
                "count": len(records),
                "area": round(area_px, 2),
                "density": round(area_px / roi_area, 8),
                "locations": [
                    {
                        "x": record["x"],
                        "y": record["y"],
                        "area_px": record["area_px"],
                        "confidence": record["confidence"],
                        "distance_to_fovea_dd": record["distance_to_fovea_dd"],
                        "is_macular": record["is_macular"],
                        "quadrant": record["quadrant"],
                    }
                    for record in records
                ],
            })

        return {
            "microaneurysms": int(counts.get("microaneurysm", 0)),
            "hemorrhages": int(counts.get("hemorrhage", 0)),
            "exudates": int(counts.get("exudate", 0)),
            "drusen": int(counts.get("drusen", 0)),
            "total_lesions": int(counts.get("total", len(result["lesions"]))),
            "detected_lesions": detected_lesions,
            "lesion_area_fraction": result["lesion_area_fraction"],
            "burden_index": result["burden_index"],
            "macular_lesion_count": result["macular_lesion_count"],
            "quadrants": result["quadrants"],
            "landmarks": result["landmarks"],
            "detection_reliability": result["detection_reliability"],
            "roi_pixels": roi_area,
        }
