"""
Unit tests for OcuPulse Computer Vision Pipeline
"""

import os
import cv2
import numpy as np
import pytest

from backend.app.processing.preprocessing import (
    validate_image,
    detect_retinal_roi,
    extract_green_channel,
    enhance_contrast,
    reduce_noise,
    preprocess_fundus_image
)
from backend.app.processing.segmentation import (
    enhance_vessel_ridges,
    segment_vessels,
    create_vessel_overlay
)
from backend.app.processing.skeletonization import (
    extract_vessel_skeleton,
    generate_skeleton_visualizer
)
from backend.app.processing.geometry import (
    detect_endpoints_and_branch_points,
    compute_vessel_length,
    analyze_vessel_geometry,
    calculate_fractal_dimension
)
from backend.app.processing.quality import assess_image_quality, generate_screening_summary
from backend.app.processing.pipeline import analyze_retinal_fundus
from backend.sample_data.sample_generator import generate_synthetic_fundus


@pytest.fixture
def sample_fundus():
    return generate_synthetic_fundus(width=400, height=400, sample_type="normal", seed=42)


def test_image_validation(sample_fundus):
    # Valid image
    is_valid, err = validate_image(sample_fundus)
    assert is_valid is True
    assert err is None
    
    # None image
    is_valid, err = validate_image(None)
    assert is_valid is False
    
    # Tiny image
    tiny = np.zeros((50, 50, 3), dtype=np.uint8)
    is_valid, err = validate_image(tiny)
    assert is_valid is False
    
    # Blank/zero variance image
    blank = np.full((200, 200, 3), 128, dtype=np.uint8)
    is_valid, err = validate_image(blank)
    assert is_valid is False


def test_preprocessing(sample_fundus):
    res = preprocess_fundus_image(sample_fundus, target_max_dim=400)
    
    assert "roi_mask" in res
    assert "green_channel" in res
    assert "enhanced_image" in res
    assert "denoised_image" in res
    
    roi = res["roi_mask"]
    assert roi.shape == sample_fundus.shape[:2]
    assert np.count_nonzero(roi) > 1000  # Non-trivial retinal field detected
    
    green = res["green_channel"]
    assert len(green.shape) == 2


def test_vessel_segmentation(sample_fundus):
    preprocessed = preprocess_fundus_image(sample_fundus, target_max_dim=400)
    vessel_mask = segment_vessels(preprocessed["denoised_image"], preprocessed["roi_mask"])
    
    assert vessel_mask.shape == sample_fundus.shape[:2]
    # Vessel mask is binary (0 or 255)
    unique_vals = set(np.unique(vessel_mask))
    assert unique_vals.issubset({0, 255})
    
    # Must detect vessels within ROI
    vessel_count = np.count_nonzero(vessel_mask)
    assert vessel_count > 100
    
    # Overlay test
    overlay = create_vessel_overlay(preprocessed["processed_image"], vessel_mask)
    assert overlay.shape == sample_fundus.shape


def test_skeletonization_and_geometry(sample_fundus):
    preprocessed = preprocess_fundus_image(sample_fundus, target_max_dim=400)
    roi_mask = preprocessed["roi_mask"]
    vessel_mask = segment_vessels(preprocessed["denoised_image"], roi_mask)
    
    skeleton = extract_vessel_skeleton(vessel_mask)
    assert skeleton.shape == vessel_mask.shape
    assert np.count_nonzero(skeleton) > 0
    assert np.count_nonzero(skeleton) <= np.count_nonzero(vessel_mask)
    
    geometry = analyze_vessel_geometry(vessel_mask, skeleton, roi_mask)
    
    assert "vessel_density" in geometry
    assert "vessel_length_pixels" in geometry
    assert "branch_points" in geometry
    assert "endpoints" in geometry
    
    assert geometry["vessel_density"] > 0.0
    assert geometry["vessel_density"] < 50.0  # Realistic physical bound
    assert geometry["branch_points"] >= 1
    assert geometry["endpoints"] >= 2
    assert geometry["vessel_length_pixels"] > 50


def test_full_pipeline(sample_fundus):
    res = analyze_retinal_fundus(sample_fundus, target_max_dim=400)
    
    assert "metrics" in res
    assert "quality" in res
    assert "summary" in res
    assert "images" in res
    
    # Check base64 images generated
    assert res["images"]["original"].startswith("data:image/png;base64,")
    assert res["images"]["enhanced"].startswith("data:image/png;base64,")
    assert res["images"]["vessel_mask"].startswith("data:image/png;base64,")
    assert res["images"]["vessel_overlay"].startswith("data:image/png;base64,")
    assert res["images"]["skeleton"].startswith("data:image/png;base64,")
    
    # Check non-diagnostic disclaimer
    assert "disclaimer" in res["summary"]
    assert "medical diagnosis" in res["summary"]["disclaimer"].lower()
