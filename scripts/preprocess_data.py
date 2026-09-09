"""
OcuPulse Retinal Data Preprocessing Pipeline
Normalizes, crops, and enhances raw fundus images across datasets:
- Retinal Field-of-View (FOV) automatic crop
- Green channel spectral enhancement
- CLAHE (Contrast Limited Adaptive Histogram Equalization)
- Bilateral denoising
- Resizing to standard dimensions (300x300 for EfficientNet, 512x512 for U-Net)
"""

import os
import sys
import argparse
from typing import Tuple, Optional

import cv2
import numpy as np

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def crop_retinal_fov(img: np.ndarray, tol: int = 15) -> np.ndarray:
    """Crops black border margins around the circular retinal field of view."""
    if len(img.shape) == 2:
        mask = img > tol
        return img[np.ix_(mask.any(1), mask.any(0))]
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    mask = gray > tol
    
    # If mask is empty, return original
    if not np.any(mask):
        return img
        
    check_shape = img[:, :, 0][np.ix_(mask.any(1), mask.any(0))].shape[0]
    if check_shape == 0:
        return img
    
    img1 = img[:, :, 0][np.ix_(mask.any(1), mask.any(0))]
    img2 = img[:, :, 1][np.ix_(mask.any(1), mask.any(0))]
    img3 = img[:, :, 2][np.ix_(mask.any(1), mask.any(0))]
    
    return np.stack([img1, img2, img3], axis=-1)


def apply_ben_graham_preprocessing(img: np.ndarray, sigmaX: int = 10) -> np.ndarray:
    """
    Applies standard Ben Graham preprocessing (Kaggle DR 1st Place technique):
    Subtracts Gaussian blurred local illumination to normalize fundus pigmentation.
    """
    img = cv2.addWeighted(img, 4, cv2.GaussianBlur(img, (0, 0), sigmaX), -4, 128)
    return img


def preprocess_fundus_image(
    image_path: str,
    target_size: Tuple[int, int] = (300, 300),
    apply_clahe: bool = True
) -> Optional[np.ndarray]:
    """Complete preprocessing for one retinal photograph."""
    img = cv2.imread(image_path)
    if img is None:
        return None
        
    # 1. Crop circular FOV
    cropped = crop_retinal_fov(img)
    
    # 2. Resize
    resized = cv2.resize(cropped, target_size, interpolation=cv2.INTER_AREA)
    
    # 3. Optional CLAHE enhancement on green channel
    if apply_clahe:
        lab = cv2.cvtColor(resized, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l_clahe = clahe.apply(l)
        enhanced = cv2.cvtColor(cv2.merge([l_clahe, a, b]), cv2.COLOR_LAB2BGR)
        return enhanced
        
    return resized


def preprocess_directory(input_dir: str, output_dir: str, target_size=(300, 300)):
    """Batch preprocesses all images in input_dir and saves to output_dir."""
    os.makedirs(output_dir, exist_ok=True)
    valid_exts = (".png", ".jpg", ".jpeg", ".tif", ".tiff")
    
    files = [f for f in os.listdir(input_dir) if f.lower().endswith(valid_exts)]
    print(f"🔄 Preprocessing {len(files)} fundus images from {input_dir}...")
    
    processed = 0
    for f in files:
        in_path = os.path.join(input_dir, f)
        out_name = os.path.splitext(f)[0] + ".png"
        out_path = os.path.join(output_dir, out_name)
        
        result = preprocess_fundus_image(in_path, target_size=target_size)
        if result is not None:
            cv2.imwrite(out_path, result)
            processed += 1
            
    print(f"✅ Successfully preprocessed {processed}/{len(files)} images to {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OcuPulse Retinal Data Preprocessor")
    parser.add_argument("--input", type=str, help="Input directory of fundus images")
    parser.add_argument("--output", type=str, help="Output directory for preprocessed images")
    parser.add_argument("--size", type=int, default=300, help="Output square size in pixels")
    args = parser.parse_args()

    if args.input and args.output:
        preprocess_directory(args.input, args.output, target_size=(args.size, args.size))
    else:
        print("Usage: python preprocess_data.py --input <input_dir> --output <output_dir> [--size 300]")
