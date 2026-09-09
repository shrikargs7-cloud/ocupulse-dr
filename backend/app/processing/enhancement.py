import cv2
import numpy as np
from skimage import exposure, filters
from skimage.restoration import denoise_bilateral
from typing import Tuple

class ImageEnhancer:
    """Enhance fundus images for better analysis"""
    
    def __init__(self):
        self.clahe_clip = 2.0
        self.clahe_grid = 8
        self.denoise_strength = 0.1
        
    def enhance(self, image_path: str) -> np.ndarray:
        """Main enhancement pipeline"""
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError("Cannot read image")
        
        # Step 1: Convert to RGB
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Step 2: Illumination normalization
        img_norm = self._normalize_illumination(img_rgb)
        
        # Step 3: Contrast enhancement (CLAHE)
        img_clahe = self._apply_clahe(img_norm)
        
        # Step 4: Denoising
        img_denoised = self._denoise(img_clahe)
        
        # Step 5: Sharpening
        img_sharp = self._sharpen(img_denoised)
        
        return img_sharp
    
    def _normalize_illumination(self, img: np.ndarray) -> np.ndarray:
        """Normalize uneven illumination"""
        lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE to L channel only
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l_norm = clahe.apply(l)
        
        # Merge and convert back
        lab_norm = cv2.merge([l_norm, a, b])
        img_norm = cv2.cvtColor(lab_norm, cv2.COLOR_LAB2RGB)
        
        return img_norm
    
    def _apply_clahe(self, img: np.ndarray) -> np.ndarray:
        """Apply CLAHE for contrast enhancement"""
        # Convert to LAB
        lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE
        clahe = cv2.createCLAHE(
            clipLimit=self.clahe_clip,
            tileGridSize=(self.clahe_grid, self.clahe_grid)
        )
        l_clahe = clahe.apply(l)
        
        # Merge and convert back
        lab_clahe = cv2.merge([l_clahe, a, b])
        img_clahe = cv2.cvtColor(lab_clahe, cv2.COLOR_LAB2RGB)
        
        return img_clahe
    
    def _denoise(self, img: np.ndarray) -> np.ndarray:
        """Apply bilateral denoising"""
        # Convert to float for skimage
        img_float = img.astype(np.float32) / 255.0
        
        # Apply bilateral filter. `channel_axis=-1` replaced the removed
        # `multichannel` keyword in scikit-image >= 0.23.
        img_denoised = denoise_bilateral(
            img_float, 
            sigma_color=self.denoise_strength,
            sigma_spatial=2,
            channel_axis=-1
        )
        
        # Convert back to uint8
        img_denoised = (img_denoised * 255).astype(np.uint8)
        
        return img_denoised
    
    def _sharpen(self, img: np.ndarray) -> np.ndarray:
        """Apply sharpening filter"""
        kernel = np.array([
            [-1, -1, -1],
            [-1, 9, -1],
            [-1, -1, -1]
        ])
        img_sharp = cv2.filter2D(img, -1, kernel)
        
        return img_sharp
    
    def enhance_for_vessel(self, img: np.ndarray) -> np.ndarray:
        """Specialized enhancement for vessel segmentation"""
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        
        # Apply CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Normalize
        enhanced = cv2.normalize(enhanced, None, 0, 255, cv2.NORM_MINMAX)
        
        return enhanced
    
    def enhance_for_lesions(self, img: np.ndarray) -> np.ndarray:
        """Specialized enhancement for lesion detection"""
        # Convert to RGB
        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        
        # Enhance red channel (microaneurysms appear red)
        r, g, b = cv2.split(img)
        r_enhanced = self._apply_clahe_single(r)
        
        # Enhance green channel (exudates appear yellow/bright)
        g_enhanced = self._apply_clahe_single(g)
        
        # Combine
        enhanced = cv2.merge([r_enhanced, g_enhanced, b])
        
        return enhanced
    
    def _apply_clahe_single(self, channel: np.ndarray) -> np.ndarray:
        """Apply CLAHE to a single channel"""
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        return clahe.apply(channel)