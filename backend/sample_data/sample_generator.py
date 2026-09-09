"""
OcuPulse Sample Retinal Image Generator

Generates realistic retinal fundus benchmark images for:
- 1-Click SIH demonstration mode
- Automated unit and integration testing
- Offline development and validation
"""

import os
import cv2
import numpy as np
import math


def generate_synthetic_fundus(
    width: int = 600,
    height: int = 600,
    sample_type: str = "normal",
    seed: int = 42
) -> np.ndarray:
    """
    Generate a high-fidelity synthetic retinal fundus photograph with circular field of view,
    choroidal background gradients, optic disc, macula, and realistic branching vascular tree.
    
    Args:
        width: Image width
        height: Image height
        sample_type: 'normal', 'dense', or 'subtle'
        seed: Random seed for reproducible branching
        
    Returns:
        BGR uint8 image
    """
    np.random.seed(seed)
    
    # 1. Circular Retinal Field of View (FOV)
    center_x, center_y = width // 2, height // 2
    radius = int(min(width, height) * 0.45)
    
    # Canvas with dark background
    img = np.zeros((height, width, 3), dtype=np.float32)
    
    # Grid coordinates
    y_coords, x_coords = np.ogrid[:height, :width]
    dist_from_center = np.sqrt((x_coords - center_x) ** 2 + (y_coords - center_y) ** 2)
    inside_roi = dist_from_center <= radius
    
    # 2. Retinal background (Warm Orange-Red / Choroid Gradient)
    # Vignetting towards edge of retina
    norm_dist = np.clip(dist_from_center / radius, 0.0, 1.0)
    vignette = 1.0 - 0.35 * (norm_dist ** 2)
    
    # Base fundus color in BGR: Red dominates (~180-220), Green moderate (~70-110), Blue low (~15-35)
    base_b = (20.0 + 10.0 * np.sin(x_coords * 0.02)) * vignette
    base_g = (85.0 + 20.0 * (1.0 - norm_dist)) * vignette
    base_r = (195.0 + 25.0 * (1.0 - norm_dist)) * vignette
    
    img[:, :, 0] = base_b
    img[:, :, 1] = base_g
    img[:, :, 2] = base_r
    
    # 3. Optic Disc (Nasal/medial region, bright yellowish-pink circle)
    od_x = int(center_x - radius * 0.42)
    od_y = int(center_y)
    od_radius = int(radius * 0.16)
    
    dist_od = np.sqrt((x_coords - od_x) ** 2 + (y_coords - od_y) ** 2)
    od_mask = np.clip(1.0 - (dist_od / od_radius), 0.0, 1.0)
    
    # Blend Optic Disc
    img[:, :, 0] += od_mask * 40.0   # B
    img[:, :, 1] += od_mask * 110.0  # G
    img[:, :, 2] += od_mask * 50.0   # R
    
    # 4. Macula / Fovea (Temporal region, darker reddish-brown)
    macula_x = int(center_x + radius * 0.30)
    macula_y = int(center_y)
    macula_radius = int(radius * 0.22)
    
    dist_macula = np.sqrt((x_coords - macula_x) ** 2 + (y_coords - macula_y) ** 2)
    macula_mask = np.clip(1.0 - (dist_macula / macula_radius), 0.0, 1.0) ** 2
    
    img[:, :, 0] -= macula_mask * 10.0
    img[:, :, 1] -= macula_mask * 35.0
    img[:, :, 2] -= macula_mask * 45.0
    
    # Convert to uint8 for drawing vessel branches with anti-aliasing
    img_uint8 = np.clip(img, 0, 255).astype(np.uint8)
    
    # 5. Vessel Tree Generation (Emerging from Optic Disc)
    # Vessels appear darker, especially in the Green channel
    vessel_layer = np.zeros((height, width), dtype=np.uint8)
    
    def grow_branch(x, y, angle, length, thickness, depth, branch_prob=0.85):
        if depth <= 0 or thickness < 1:
            return
        
        # Segment steps
        steps = int(max(4, length // 6))
        cx, cy = float(x), float(y)
        cur_angle = angle
        
        for _ in range(steps):
            cur_angle += np.random.uniform(-0.15, 0.15)
            nx = cx + math.cos(cur_angle) * (length / steps)
            ny = cy + math.sin(cur_angle) * (length / steps)
            
            # Check if within ROI
            if (nx - center_x) ** 2 + (ny - center_y) ** 2 < (radius * 0.95) ** 2:
                cv2.line(
                    vessel_layer,
                    (int(round(cx)), int(round(cy))),
                    (int(round(nx)), int(round(ny))),
                    color=255,
                    thickness=max(1, int(round(thickness))),
                    lineType=cv2.LINE_AA
                )
            cx, cy = nx, ny
            
        # Recursive bifurcation
        if np.random.rand() < branch_prob:
            angle_delta = np.random.uniform(0.35, 0.65)
            grow_branch(cx, cy, cur_angle + angle_delta, length * 0.78, thickness * 0.72, depth - 1, branch_prob)
            grow_branch(cx, cy, cur_angle - angle_delta, length * 0.78, thickness * 0.72, depth - 1, branch_prob)
        else:
            grow_branch(cx, cy, cur_angle + np.random.uniform(-0.2, 0.2), length * 0.82, thickness * 0.85, depth - 1, branch_prob)

    # Main vascular arcades
    # Superior temporal, Inferior temporal, Superior nasal, Inferior nasal
    arcades = [
        # (angle, length, initial_thickness, depth)
        (-0.7, radius * 0.45, 5.0, 5),  # Superior temporal
        (0.7, radius * 0.45, 5.0, 5),   # Inferior temporal
        (-2.4, radius * 0.35, 4.0, 4),  # Superior nasal
        (2.4, radius * 0.35, 4.0, 4),   # Inferior nasal
        (-1.55, radius * 0.40, 3.5, 4), # Superior radial
        (1.55, radius * 0.40, 3.5, 4),  # Inferior radial
        (0.0, radius * 0.30, 2.5, 3),   # Nasal horizontal
        (3.14, radius * 0.25, 2.0, 3),  # Temporal horizontal
    ]
    
    if sample_type == "dense":
        arcades.extend([
            (-1.1, radius * 0.38, 4.0, 5),
            (1.1, radius * 0.38, 4.0, 5),
            (-0.35, radius * 0.30, 3.0, 4),
            (0.35, radius * 0.30, 3.0, 4),
        ])
    elif sample_type == "subtle":
        # Narrower initial vessels
        arcades = [(ang, l * 0.9, th * 0.7, d) for (ang, l, th, d) in arcades]
        
    for ang, l, th, d in arcades:
        grow_branch(od_x, od_y, ang, l, th, d)
        
    # Smooth vessel layer slightly
    vessel_smooth = cv2.GaussianBlur(vessel_layer, (3, 3), 0.6)
    vessel_norm = vessel_smooth.astype(np.float32) / 255.0
    
    # Subtract vessels from fundus image (vessels absorb green and blue heavily)
    result = img_uint8.astype(np.float32)
    result[:, :, 0] -= vessel_norm * 35.0  # Blue drop
    result[:, :, 1] -= vessel_norm * 90.0  # Green drop (strongest contrast)
    result[:, :, 2] -= vessel_norm * 55.0  # Red drop
    
    # 6. Subtle sensor noise and choroid texture
    noise = np.random.normal(0, 3.5, (height, width, 3))
    result += noise
    
    # 7. Apply circular field of view mask (black out anything outside retinal circle)
    result = np.clip(result, 0, 255).astype(np.uint8)
    circular_mask = np.zeros((height, width), dtype=np.uint8)
    cv2.circle(circular_mask, (center_x, center_y), radius, 255, -1)
    
    # Anti-alias mask border
    mask_blurred = cv2.GaussianBlur(circular_mask, (7, 7), 2.0).astype(np.float32) / 255.0
    for c in range(3):
        result[:, :, c] = (result[:, :, c] * mask_blurred).astype(np.uint8)
        
    return result


def ensure_sample_images(sample_dir: str) -> None:
    """Generate and save benchmark fundus samples if not already present."""
    os.makedirs(sample_dir, exist_ok=True)
    
    samples = [
        ("demo_normal.png", "normal", 42, "Standard Screening Fundus (Balanced Vasculature)"),
        ("demo_dense.png", "dense", 101, "Dense Retinal Arborization (High Vessel Density)"),
        ("demo_subtle.png", "subtle", 202, "Subtle Micro-Vasculature (Fine Capillaries)")
    ]
    
    for filename, stype, seed, _ in samples:
        filepath = os.path.join(sample_dir, filename)
        if not os.path.exists(filepath):
            img = generate_synthetic_fundus(width=650, height=650, sample_type=stype, seed=seed)
            cv2.imwrite(filepath, img)
            print(f"[Sample Generator] Created {filename}")


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    ensure_sample_images(current_dir)
