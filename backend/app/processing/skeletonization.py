"""
OcuPulse Retinal Vessel Skeletonization Module

Provides algorithms for:
- One-pixel-wide vessel centerline extraction using skimage skeletonize
- Skeleton visualizer generation with color-coded topology markers
"""

import cv2
import numpy as np
from skimage.morphology import skeletonize
from typing import Tuple, Optional


def extract_vessel_skeleton(vessel_mask: np.ndarray) -> np.ndarray:
    """
    Extract one-pixel-wide centerline skeleton of segmented retinal vessels
    using morphological thinning (Zhang-Suen / Lee algorithm via scikit-image).
    
    Args:
        vessel_mask: Binary uint8 mask (0 = background, 255 = vessel)
        
    Returns:
        Binary uint8 skeleton mask (0 = background, 255 = skeleton centerline)
    """
    if np.count_nonzero(vessel_mask) == 0:
        return np.zeros_like(vessel_mask, dtype=np.uint8)
    
    # Normalize to boolean mask for skimage
    bool_mask = vessel_mask > 0
    
    # Run morphological skeletonization
    skel_bool = skeletonize(bool_mask)
    
    # Convert back to uint8 (0 or 255)
    skeleton = (skel_bool.astype(np.uint8)) * 255
    
    return skeleton


def generate_skeleton_visualizer(
    skeleton: np.ndarray,
    branch_coords: Optional[np.ndarray] = None,
    endpoint_coords: Optional[np.ndarray] = None,
    background_dim: Tuple[int, int] = None,
    base_image: Optional[np.ndarray] = None
) -> np.ndarray:
    """
    Generate an enhanced colorized visualizer of the vessel skeleton
    with marked branch points and endpoints.
    
    Args:
        skeleton: Binary uint8 skeleton mask (255 for centerline)
        branch_coords: (N, 2) array of (y, x) branch point coordinates
        endpoint_coords: (M, 2) array of (y, x) endpoint coordinates
        background_dim: Tuple of (height, width) if base_image is None
        base_image: Optional dark or original image backdrop
        
    Returns:
        BGR color image with highlighted skeleton, branch points, and endpoints
    """
    h, w = skeleton.shape[:2]
    
    if base_image is not None:
        # Darkened backdrop of original image for context
        vis = cv2.addWeighted(base_image, 0.25, np.zeros_like(base_image), 0.75, 0)
    else:
        # Dark scientific slate background
        vis = np.full((h, w, 3), 18, dtype=np.uint8)
        
    # Draw skeleton centerlines in high-visibility cyan [255, 230, 0] in BGR -> [0, 240, 255]
    vis[skeleton > 0] = [0, 230, 255]
    
    # Draw endpoints in golden yellow [0, 215, 255] with small circles
    if endpoint_coords is not None and len(endpoint_coords) > 0:
        for pt in endpoint_coords:
            y, x = int(pt[0]), int(pt[1])
            cv2.circle(vis, (x, y), 3, (0, 215, 255), thickness=-1)
            
    # Draw branch points in vibrant ruby/magenta [255, 0, 180] with slightly larger circles
    if branch_coords is not None and len(branch_coords) > 0:
        for pt in branch_coords:
            y, x = int(pt[0]), int(pt[1])
            cv2.circle(vis, (x, y), 4, (255, 60, 60), thickness=-1)
            
    return vis
