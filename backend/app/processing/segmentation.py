"""
OcuPulse Retinal Blood Vessel Segmentation Module

Provides algorithms for:
- Multi-scale vessel enhancement (Top-Hat morphology + local contrast filter)
- Adaptive local thresholding within retinal ROI
- Connected-component morphological noise suppression
- Colorized vessel overlay generation on original fundus photograph
- Clear extensible interface for plug-and-play ML models (U-Net)
"""

import cv2
import numpy as np
from typing import Tuple, Optional


def enhance_vessel_ridges(
    denoised_green: np.ndarray,
    kernel_radius: int = 9
) -> np.ndarray:
    """
    Enhance tubular vessel structures using morphological top-hat transforms
    and background luminance normalization on inverted green channel.
    
    Args:
        denoised_green: 2D uint8 green channel image
        kernel_radius: Radius of structuring element for vessel scale
        
    Returns:
        Enhanced vessel ridge map (uint8, bright vessels on dark background)
    """
    # Invert green channel so vessels (darker in raw fundus) become bright ridges
    inv_green = cv2.bitwise_not(denoised_green)
    
    # 1. Morphological Top-Hat with circular structuring elements at multiple scales
    k1 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_radius, kernel_radius))
    k2 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_radius * 2 + 1, kernel_radius * 2 + 1))
    
    tophat1 = cv2.morphologyEx(inv_green, cv2.MORPH_TOPHAT, k1)
    tophat2 = cv2.morphologyEx(inv_green, cv2.MORPH_TOPHAT, k2)
    
    # Multi-scale fusion: weights fine and major vascular branches
    multiscale_tophat = cv2.addWeighted(tophat1, 0.6, tophat2, 0.4, 0)
    
    # 2. Local background illumination estimation & subtraction
    bg_estimate = cv2.medianBlur(inv_green, 31)
    subtracted = cv2.subtract(inv_green, bg_estimate)
    
    # Combined ridge representation
    enhanced = cv2.addWeighted(multiscale_tophat, 0.7, subtracted, 0.3, 0)
    
    # Normalize to full 0-255 range
    enhanced = cv2.normalize(enhanced, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)
    
    return enhanced


def segment_vessels(
    denoised_green: np.ndarray,
    roi_mask: np.ndarray,
    min_vessel_size: int = 20,
    adaptive_block_size: int = 31,
    adaptive_c: float = -3.0
) -> np.ndarray:
    """
    Segment retinal blood vessels and produce a clean binary mask.
    
    Pixel interpretation:
        0   = Background / Non-vessel
        255 = Detected Retinal Blood Vessel
        
    Args:
        denoised_green: 2D uint8 green channel image
        roi_mask: 2D binary uint8 mask of the retinal field of view
        min_vessel_size: Minimum connected component pixel count to eliminate noise
        adaptive_block_size: Neighborhood size for adaptive thresholding
        adaptive_c: Constant subtracted from weighted mean
        
    Returns:
        Binary vessel mask (uint8, 0 or 255)
    """
    # 1. Enhance vessel tubular features
    vessel_enhanced = enhance_vessel_ridges(denoised_green)
    
    # 2. Adaptive Gaussian thresholding for local contrast adaptation
    # Ensure block size is odd and >= 3
    if adaptive_block_size % 2 == 0:
        adaptive_block_size += 1
    adaptive_block_size = max(3, adaptive_block_size)
    
    # Local adaptive thresholding on enhanced ridges
    thresh_adaptive = cv2.adaptiveThreshold(
        vessel_enhanced,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        adaptive_block_size,
        adaptive_c
    )
    
    # 3. Global Otsu threshold on enhanced vessels within ROI
    roi_pixels = vessel_enhanced[roi_mask > 0]
    if len(roi_pixels) > 0:
        otsu_val, _ = cv2.threshold(roi_pixels, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        # Relaxed Otsu threshold for sensitivity to micro-vessels
        _, thresh_otsu = cv2.threshold(vessel_enhanced, max(20, int(otsu_val * 0.85)), 255, cv2.THRESH_BINARY)
    else:
        thresh_otsu = np.zeros_like(vessel_enhanced)
        
    # Combine adaptive and Otsu for balanced sensitivity & specificity
    combined = cv2.bitwise_or(thresh_adaptive, thresh_otsu)
    
    # Strict confinement within retinal ROI
    vessel_candidate = cv2.bitwise_and(combined, roi_mask)
    
    # 4. Morphological opening to detach spurious single-pixel bridges
    clean_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    cleaned = cv2.morphologyEx(vessel_candidate, cv2.MORPH_OPEN, clean_kernel)
    
    # 5. Connected Component Analysis to remove small isolated speckle noise
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(cleaned, connectivity=8)
    
    final_mask = np.zeros_like(cleaned, dtype=np.uint8)
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        if area >= min_vessel_size:
            final_mask[labels == i] = 255
            
    # Final boundary protection: ensure no boundary bleed outside ROI
    final_mask = cv2.bitwise_and(final_mask, roi_mask)
    
    return final_mask


def create_vessel_overlay(
    original_image: np.ndarray,
    vessel_mask: np.ndarray,
    overlay_color: Tuple[int, int, int] = (0, 255, 230),  # Bright Cyan/Teal (BGR)
    alpha: float = 0.65
) -> np.ndarray:
    """
    Create a high-contrast visualizer overlay combining the original fundus image
    with the detected retinal vessel segmentation mask.
    
    Args:
        original_image: Original BGR color fundus photograph
        vessel_mask: Binary uint8 vessel segmentation mask (0 or 255)
        overlay_color: BGR color tuple for vessel highlighting
        alpha: Blending weight for vessel color (0.0 to 1.0)
        
    Returns:
        Color BGR image with highlighted vessel overlay
    """
    overlay = original_image.copy()
    
    # Create colored vessel layer
    colored_vessels = np.zeros_like(original_image)
    colored_vessels[vessel_mask > 0] = overlay_color
    
    # Blend overlay with original where vessel_mask is positive
    mask_indices = vessel_mask > 0
    overlay[mask_indices] = cv2.addWeighted(
        original_image[mask_indices],
        1.0 - alpha,
        colored_vessels[mask_indices],
        alpha,
        0
    )
    
    return overlay
