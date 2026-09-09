"""
OcuPulse Retinal Image Preprocessing Module

Provides functions for:
- Input image validation
- Retinal Field of View (ROI) detection
- Green channel extraction (optimal vessel contrast)
- CLAHE (Contrast Limited Adaptive Histogram Equalization)
- Edge-preserving noise reduction
"""

import cv2
import numpy as np
from typing import Tuple, Dict, Any, Optional


def validate_image(image: np.ndarray) -> Tuple[bool, Optional[str]]:
    """
    Validate that an input image is a valid, readable retinal photograph.
    
    Args:
        image: Input image as numpy array (BGR or RGB)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if image is None or not isinstance(image, np.ndarray):
        return False, "Invalid image payload: unable to decode image data."
    
    if image.size == 0:
        return False, "Uploaded image is empty (0 bytes)."
    
    if len(image.shape) not in (2, 3):
        return False, f"Unsupported image dimensions: {image.shape}"
    
    h, w = image.shape[:2]
    if h < 100 or w < 100:
        return False, f"Image resolution too small ({w}x{h} px). Minimum required is 100x100 px."
    
    if h > 6000 or w > 6000:
        return False, f"Image resolution too large ({w}x{h} px). Maximum supported is 6000x6000 px."
    
    # Check for near-constant or blank images
    std_dev = np.std(image)
    if std_dev < 3.0:
        return False, "Image contains almost zero contrast/variance (appears blank or solid color)."
    
    return True, None


def detect_retinal_roi(
    image: np.ndarray, 
    threshold_val: int = 15, 
    erosion_margin: int = 6
) -> np.ndarray:
    """
    Detect the circular/elliptical retinal field of view (ROI) and produce a binary mask.
    Excludes black camera borders, padding, and out-of-field artifacts.
    
    Args:
        image: Color or grayscale image (uint8)
        threshold_val: Luminance cutoff for background separation
        erosion_margin: Pixels to erode around boundary to prevent border artifacts
        
    Returns:
        Binary mask (uint8) where 255 = inside retinal ROI, 0 = background
    """
    if len(image.shape) == 3:
        # Fundus images have highest illumination in Red/Green channels
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.shape[2] == 3 else image
    else:
        gray = image.copy()
    
    h, w = gray.shape
    
    # Threshold background
    _, binary = cv2.threshold(gray, threshold_val, 255, cv2.THRESH_BINARY)
    
    # Morphological closing to fill holes inside retina
    kernel_size = max(5, int(min(h, w) * 0.02))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    
    # Find contours and extract the largest component (retinal circle)
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    roi_mask = np.zeros((h, w), dtype=np.uint8)
    
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest_contour)
        
        # Verify the contour covers a significant portion (at least 15% of image area)
        if area > (h * w * 0.15):
            cv2.drawContours(roi_mask, [largest_contour], -1, 255, thickness=cv2.FILLED)
            # Smooth mask using convex hull if slightly irregular
            hull = cv2.convexHull(largest_contour)
            cv2.drawContours(roi_mask, [hull], -1, 255, thickness=cv2.FILLED)
        else:
            # Fallback to circular mask in center
            center = (w // 2, h // 2)
            radius = int(min(w, h) * 0.46)
            cv2.circle(roi_mask, center, radius, 255, thickness=-1)
    else:
        # Fallback circular mask
        center = (w // 2, h // 2)
        radius = int(min(w, h) * 0.46)
        cv2.circle(roi_mask, center, radius, 255, thickness=-1)
    
    # Optional erosion margin to avoid sharp boundary gradient artifacts during segmentation
    if erosion_margin > 0:
        erode_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (erosion_margin * 2 + 1, erosion_margin * 2 + 1))
        roi_mask = cv2.erode(roi_mask, erode_kernel, iterations=1)
        
    return roi_mask


def extract_green_channel(image: np.ndarray) -> np.ndarray:
    """
    Extract the green channel from a fundus photograph.
    Retinal blood vessels have maximum absorption in the green spectrum (~540-570nm),
    providing the highest contrast against the retinal pigment epithelium.
    
    Args:
        image: Color image in BGR or RGB format
        
    Returns:
        Grayscale 2D array of the green channel
    """
    if len(image.shape) == 2:
        return image.copy()
    
    # For standard BGR format from OpenCV
    # Channel index 1 is green in both BGR and RGB
    return image[:, :, 1].copy()


def enhance_contrast(
    green_channel: np.ndarray,
    clip_limit: float = 2.5,
    tile_grid_size: Tuple[int, int] = (8, 8)
) -> np.ndarray:
    """
    Apply Contrast Limited Adaptive Histogram Equalization (CLAHE)
    to normalize local lighting variations and enhance fine retinal blood vessels.
    
    Args:
        green_channel: 2D uint8 green channel
        clip_limit: CLAHE contrast clip limit (default: 2.5)
        tile_grid_size: Grid size for local histogram equalization (default: 8x8)
        
    Returns:
        Enhanced uint8 grayscale image
    """
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    enhanced = clahe.apply(green_channel)
    return enhanced


def reduce_noise(
    image: np.ndarray,
    method: str = "bilateral"
) -> np.ndarray:
    """
    Apply edge-preserving noise reduction to smooth camera sensor noise
    without blurring narrow micro-vessel boundaries.
    
    Args:
        image: 2D uint8 enhanced grayscale image
        method: Denoising algorithm ('bilateral', 'median', or 'gaussian')
        
    Returns:
        Denoised 2D uint8 image
    """
    if method == "bilateral":
        # Bilateral filter preserves sharp vessel edges while smoothing flat areas
        return cv2.bilateralFilter(image, d=5, sigmaColor=40, sigmaSpace=40)
    elif method == "median":
        return cv2.medianBlur(image, 3)
    elif method == "gaussian":
        return cv2.GaussianBlur(image, (3, 3), 0.8)
    else:
        return cv2.bilateralFilter(image, d=5, sigmaColor=40, sigmaSpace=40)


def preprocess_fundus_image(
    image: np.ndarray,
    target_max_dim: int = 1024
) -> Dict[str, Any]:
    """
    Execute full preprocessing pipeline on input fundus image.
    
    Args:
        image: BGR color image
        target_max_dim: Maximum dimension for standardized processing (scales if larger)
        
    Returns:
        Dictionary containing preprocessed representations and metadata
    """
    is_valid, err = validate_image(image)
    if not is_valid:
        raise ValueError(err)
        
    h, w = image.shape[:2]
    scale_factor = 1.0
    
    # Standardize image size for consistent vessel geometry computation
    if max(h, w) > target_max_dim:
        scale_factor = target_max_dim / float(max(h, w))
        new_w, new_h = int(w * scale_factor), int(h * scale_factor)
        image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
    elif min(h, w) < 400:
        # Scale up tiny images for better segmentation stability
        scale_factor = 600.0 / float(min(h, w))
        new_w, new_h = int(w * scale_factor), int(h * scale_factor)
        image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
        
    # 1. Detect retinal Field of View (ROI)
    roi_mask = detect_retinal_roi(image)
    
    # 2. Extract Green Channel
    green = extract_green_channel(image)
    
    # 3. Enhance Contrast via CLAHE
    enhanced = enhance_contrast(green, clip_limit=3.0, tile_grid_size=(8, 8))
    
    # 4. Noise Reduction
    denoised = reduce_noise(enhanced, method="bilateral")
    
    return {
        "processed_image": image,
        "roi_mask": roi_mask,
        "green_channel": green,
        "enhanced_image": enhanced,
        "denoised_image": denoised,
        "dimensions": {"width": image.shape[1], "height": image.shape[0]},
        "scale_factor": scale_factor,
        "roi_pixel_count": int(np.count_nonzero(roi_mask))
    }
