import numpy as np
import cv2
from skimage import morphology, measure, feature
from scipy import ndimage
from typing import Dict, Any, List, Tuple

class LesionDetector:
    """Detect and classify retinal lesions using deterministic methods"""
    
    def __init__(self):
        # Lesion thresholds
        self.ma_threshold = 0.3
        self.exudate_threshold = 0.5
        self.hemorrhage_threshold = 0.4
        self.neovascularization_threshold = 0.35
        
    def detect_all(self, image: np.ndarray) -> Dict[str, Any]:
        """Detect all types of lesions"""
        # Convert to LAB for better color analysis
        if len(image.shape) == 3:
            lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
            L, A, B = cv2.split(lab)
        else:
            L = image
            A = np.zeros_like(image)
            B = np.zeros_like(image)
        
        # Detect different lesion types
        microaneurysms = self.detect_microaneurysms(A, B, L)
        exudates = self.detect_exudates(L)
        hemorrhages = self.detect_hemorrhages(A, B)
        neovascularization = self.detect_neovascularization(A, B)
        
        # Combine all lesions
        all_lesions = {
            "microaneurysms": microaneurysms,
            "exudates": exudates,
            "hemorrhages": hemorrhages,
            "neovascularization": neovascularization
        }
        
        # Generate detected lesions list for schema
        detected_lesions = []
        for lesion_type, data in all_lesions.items():
            if data["count"] > 0:
                detected_lesions.append({
                    "type": lesion_type,
                    "count": data["count"],
                    "area": data["area"],
                    "density": data["density"],
                    "locations": data["locations"][:10]  # Limit locations
                })
        
        return {
            "detected_lesions": detected_lesions,
            "total_count": sum(l["count"] for l in detected_lesions),
            "summary": self._generate_summary(all_lesions)
        }
    
    def detect_microaneurysms(self, A: np.ndarray, B: np.ndarray, L: np.ndarray) -> Dict[str, Any]:
        """
        Detect microaneurysms (small red spots)
        Microaneurysms appear as:
        - Dark in A channel (red-green)
        - Bright in B channel (blue-yellow)
        - Small circular objects
        """
        # Normalize
        A_norm = cv2.normalize(A, None, 0, 255, cv2.NORM_MINMAX)
        B_norm = cv2.normalize(B, None, 0, 255, cv2.NORM_MINMAX)
        
        # Create microaneurysm probability map
        ma_score = ((A_norm < 50) & (B_norm > 180)).astype(np.float32)
        
        # Apply morphological operations
        kernel = np.ones((3, 3), np.uint8)
        ma_score = cv2.morphologyEx(ma_score, cv2.MORPH_OPEN, kernel)
        ma_score = cv2.morphologyEx(ma_score, cv2.MORPH_CLOSE, kernel)
        
        # Threshold
        ma_mask = ma_score > self.ma_threshold
        
        # Remove large objects (microaneurysms are small)
        ma_mask = morphology.remove_small_objects(ma_mask, min_size=5)
        ma_mask = morphology.remove_small_objects(ma_mask, max_size=200)
        
        # Label and extract features
        labeled, num_features = ndimage.label(ma_mask)
        
        if num_features == 0:
            return {"count": 0, "area": 0, "density": 0, "locations": []}
        
        # Extract locations
        locations = []
        for i in range(1, num_features + 1):
            y_coords, x_coords = np.where(labeled == i)
            if len(x_coords) > 0:
                centroid = (int(np.mean(x_coords)), int(np.mean(y_coords)))
                locations.append(centroid)
        
        area = np.sum(ma_mask)
        density = area / ma_mask.size * 100
        
        return {
            "count": num_features,
            "area": float(area),
            "density": float(density),
            "locations": locations
        }
    
    def detect_exudates(self, L: np.ndarray) -> Dict[str, Any]:
        """
        Detect hard exudates (bright yellow lesions)
        Exudates appear as:
        - Bright in L channel (lightness)
        - Often multiple and clustered
        """
        # Normalize L channel
        L_norm = cv2.normalize(L, None, 0, 255, cv2.NORM_MINMAX)
        
        # Create exudate probability map
        exudate_score = (L_norm > 180).astype(np.float32)
        
        # Morphological operations
        kernel = np.ones((5, 5), np.uint8)
        exudate_score = cv2.morphologyEx(exudate_score, cv2.MORPH_OPEN, kernel)
        exudate_score = cv2.morphologyEx(exudate_score, cv2.MORPH_CLOSE, kernel)
        
        # Threshold
        exudate_mask = exudate_score > self.exudate_threshold
        
        # Remove small objects
        exudate_mask = morphology.remove_small_objects(exudate_mask, min_size=20)
        
        # Label
        labeled, num_features = ndimage.label(exudate_mask)
        
        if num_features == 0:
            return {"count": 0, "area": 0, "density": 0, "locations": []}
        
        # Extract locations
        locations = []
        for i in range(1, num_features + 1):
            y_coords, x_coords = np.where(labeled == i)
            if len(x_coords) > 0:
                centroid = (int(np.mean(x_coords)), int(np.mean(y_coords)))
                locations.append(centroid)
        
        area = np.sum(exudate_mask)
        density = area / exudate_mask.size * 100
        
        return {
            "count": num_features,
            "area": float(area),
            "density": float(density),
            "locations": locations
        }
    
    def detect_hemorrhages(self, A: np.ndarray, B: np.ndarray) -> Dict[str, Any]:
        """
        Detect hemorrhages (dark red lesions)
        Hemorrhages appear as:
        - Dark in both A and B channels
        - Larger than microaneurysms
        - Irregular shape
        """
        # Normalize
        A_norm = cv2.normalize(A, None, 0, 255, cv2.NORM_MINMAX)
        B_norm = cv2.normalize(B, None, 0, 255, cv2.NORM_MINMAX)
        
        # Create hemorrhage probability map
        hemo_score = ((A_norm < 40) & (B_norm < 120)).astype(np.float32)
        
        # Morphological operations
        kernel = np.ones((5, 5), np.uint8)
        hemo_score = cv2.morphologyEx(hemo_score, cv2.MORPH_OPEN, kernel)
        hemo_score = cv2.morphologyEx(hemo_score, cv2.MORPH_CLOSE, kernel)
        
        # Threshold
        hemo_mask = hemo_score > self.hemorrhage_threshold
        
        # Remove small objects
        hemo_mask = morphology.remove_small_objects(hemo_mask, min_size=30)
        
        # Label
        labeled, num_features = ndimage.label(hemo_mask)
        
        if num_features == 0:
            return {"count": 0, "area": 0, "density": 0, "locations": []}
        
        # Extract locations
        locations = []
        for i in range(1, num_features + 1):
            y_coords, x_coords = np.where(labeled == i)
            if len(x_coords) > 0:
                centroid = (int(np.mean(x_coords)), int(np.mean(y_coords)))
                locations.append(centroid)
        
        area = np.sum(hemo_mask)
        density = area / hemo_mask.size * 100
        
        return {
            "count": num_features,
            "area": float(area),
            "density": float(density),
            "locations": locations
        }
    
    def detect_neovascularization(self, A: np.ndarray, B: np.ndarray) -> Dict[str, Any]:
        """
        Detect neovascularization (abnormal new vessels)
        Appears as:
        - Abnormal vessel patterns near optic disc
        - Irregular branching
        """
        # This is a simplified version - real detection requires more complex analysis
        # For now, we use a combination of features
        
        # Normalize
        A_norm = cv2.normalize(A, None, 0, 255, cv2.NORM_MINMAX)
        B_norm = cv2.normalize(B, None, 0, 255, cv2.NORM_MINMAX)
        
        # Look for abnormal vessel patterns
        nv_score = ((A_norm < 60) & (B_norm > 150)).astype(np.float32)
        
        # Morphological operations
        kernel = np.ones((3, 3), np.uint8)
        nv_score = cv2.morphologyEx(nv_score, cv2.MORPH_OPEN, kernel)
        
        # Threshold
        nv_mask = nv_score > self.neovascularization_threshold
        
        # Remove small objects
        nv_mask = morphology.remove_small_objects(nv_mask, min_size=10)
        
        labeled, num_features = ndimage.label(nv_mask)
        
        if num_features == 0:
            return {"count": 0, "area": 0, "density": 0, "locations": []}
        
        locations = []
        for i in range(1, num_features + 1):
            y_coords, x_coords = np.where(labeled == i)
            if len(x_coords) > 0:
                centroid = (int(np.mean(x_coords)), int(np.mean(y_coords)))
                locations.append(centroid)
        
        area = np.sum(nv_mask)
        density = area / nv_mask.size * 100
        
        return {
            "count": num_features,
            "area": float(area),
            "density": float(density),
            "locations": locations
        }
    
    def _generate_summary(self, all_lesions: Dict) -> str:
        """Generate a text summary of lesions"""
        summary = []
        for lesion_type, data in all_lesions.items():
            if data["count"] > 0:
                summary.append(f"{lesion_type}: {data['count']} detected")
        
        if not summary:
            return "No lesions detected"
        return ", ".join(summary)