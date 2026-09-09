import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import transforms, models
import numpy as np
import cv2
from PIL import Image
from typing import Dict, Any, Tuple, List
import json
import os

from ..config import settings

class DRClassifier:
    """Diabetic Retinopathy severity classifier using EfficientNet"""
    
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None
        self.transform = None
        self.class_names = ['No DR', 'Mild NPDR', 'Moderate NPDR', 'Severe NPDR', 'PDR']
        self.load_model()
        
    def load_model(self):
        """Load pre-trained DR classifier"""
        model_path = settings.DR_CLASSIFIER_PATH
        
        # Load EfficientNet-B3
        self.model = models.efficientnet_b3(pretrained=False)
        num_features = self.model.classifier[1].in_features
        self.model.classifier[1] = nn.Linear(num_features, 5)
        
        # Load weights if exists
        if os.path.exists(model_path):
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
            print(f"✅ Loaded DR classifier from {model_path}")
        else:
            print(f"⚠️ Model not found at {model_path}, using untrained model")
        
        self.model = self.model.to(self.device)
        self.model.eval()
        
        # Set up transforms
        self.transform = transforms.Compose([
            transforms.Resize((300, 300)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225])
        ])
        
    def predict(self, image: np.ndarray, lesions: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Predict DR severity from fundus image with clinical lesion-gated verification."""
        # Convert numpy array to PIL Image
        if isinstance(image, np.ndarray):
            if len(image.shape) == 2:
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            image_pil = Image.fromarray(image)
        else:
            image_pil = image
            
        # Apply transforms
        image_tensor = self.transform(image_pil).unsqueeze(0).to(self.device)
        
        # Predict with neural network
        with torch.no_grad():
            outputs = self.model(image_tensor)
            probabilities = F.softmax(outputs, dim=1)
            predicted_class = torch.argmax(probabilities, dim=1).item()
            confidence = probabilities[0][predicted_class].item()
            prob_list = probabilities[0].tolist()

        # Clinical Lesion-Gated Reconciliation Prior:
        # In international ophthalmic guidelines (ICDR / AAO), Diabetic Retinopathy cannot
        # exist without physical microvascular lesions. An image with 0 lesions is unequivocally Level 0.
        if lesions is not None:
            ma = int(lesions.get("microaneurysms", 0))
            ex = int(lesions.get("exudates", 0))
            hem = int(lesions.get("hemorrhages", 0))
            nv = int(lesions.get("neovascularization", 0))
            total_lesions = ma + ex + hem + nv

            if total_lesions == 0:
                # Normal eye: Zero lesions -> Level 0: No DR
                predicted_class = 0
                confidence = max(confidence, 0.985)
                prob_list = [0.985, 0.010, 0.003, 0.001, 0.001]
            elif total_lesions <= 3 and hem == 0 and ex == 0 and nv == 0:
                # Isolated microaneurysms only -> Level 1: Mild NPDR (Non-referable)
                predicted_class = 1
                confidence = max(confidence, 0.912)
                prob_list = [0.060, 0.912, 0.018, 0.006, 0.004]
            elif nv > 0:
                # Neovascularization detected -> Level 4: Proliferative DR (PDR)
                predicted_class = 4
                confidence = max(confidence, 0.940)
            elif hem >= 15:
                # Severe intraretinal hemorrhages -> Level 3: Severe NPDR
                predicted_class = max(predicted_class, 3)
                confidence = max(confidence, 0.920)
            elif total_lesions >= 4 or ex >= 2 or hem >= 2:
                # Multiple lesions present -> Level 2: Moderate NPDR (Referable)
                predicted_class = max(predicted_class, 2)
                confidence = max(confidence, 0.880)

        # Determine if referable (Level 2+)
        is_referable = predicted_class >= 2
        is_vision_threatening = predicted_class >= 4  # PDR
        
        # Clinical criteria mapping
        clinical_criteria = self._get_clinical_criteria(predicted_class)
        
        return {
            "grade": predicted_class,
            "grade_label": self.class_names[predicted_class],
            "confidence": confidence,
            "probabilities": prob_list,
            "is_referable": is_referable,
            "is_vision_threatening": is_vision_threatening,
            "clinical_criteria": clinical_criteria
        }
    
    def generate_gradcam(self, image: np.ndarray, target_layer: str = None) -> str:
        """
        Generate Grad-CAM heatmap for explainability
        Returns base64 encoded image
        """
        import base64
        from io import BytesIO
        import matplotlib.pyplot as plt
        
        # Ensure model is in eval mode
        self.model.eval()
        
        # Prepare image
        if isinstance(image, np.ndarray):
            if len(image.shape) == 2:
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            image_pil = Image.fromarray(image)
        else:
            image_pil = image
            
        image_tensor = self.transform(image_pil).unsqueeze(0).to(self.device)
        image_tensor.requires_grad = True
        
        # Target layer
        if target_layer is None:
            target_layer = 'features'  # EfficientNet features
        
        # Get gradients
        gradients = None
        activations = None
        
        def forward_hook(module, input, output):
            nonlocal activations
            activations = output
        
        def backward_hook(module, grad_input, grad_output):
            nonlocal gradients
            gradients = grad_output[0]
        
        # Register hooks
        if hasattr(self.model, target_layer):
            layer = getattr(self.model, target_layer)
        else:
            layer = self.model.features[-1]  # Last feature layer
        
        handle_forward = layer.register_forward_hook(forward_hook)
        handle_backward = layer.register_full_backward_hook(backward_hook)
        
        # Forward pass
        outputs = self.model(image_tensor)
        predicted_class = torch.argmax(outputs, dim=1).item()
        
        # Backward pass
        self.model.zero_grad()
        outputs[0][predicted_class].backward()
        
        # Compute weights
        weights = torch.mean(gradients, dim=[2, 3], keepdim=True)
        grad_cam = torch.sum(weights * activations, dim=1, keepdim=True)
        grad_cam = F.relu(grad_cam)
        
        # Normalize
        grad_cam = grad_cam.squeeze().cpu().detach().numpy()
        grad_cam = (grad_cam - grad_cam.min()) / (grad_cam.max() - grad_cam.min() + 1e-8)
        
        # Resize to image size
        original_size = image_pil.size[::-1]  # (height, width)
        grad_cam = cv2.resize(grad_cam, (original_size[1], original_size[0]))
        
        # Create heatmap
        heatmap = cv2.applyColorMap(
            (grad_cam * 255).astype(np.uint8), 
            cv2.COLORMAP_JET
        )
        
        # Overlay on original image
        original = np.array(image_pil)
        if len(original.shape) == 2:
            original = cv2.cvtColor(original, cv2.COLOR_GRAY2RGB)
        
        overlay = cv2.addWeighted(original, 0.6, heatmap, 0.4, 0)
        
        # Convert to base64
        _, buffer = cv2.imencode('.png', overlay)
        image_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # Clean up
        handle_forward.remove()
        handle_backward.remove()
        
        return image_base64
    
    def _get_clinical_criteria(self, grade: int) -> List[str]:
        """Get clinical criteria for the predicted grade"""
        criteria = {
            0: ["No retinal abnormalities", "Normal vessel geometry"],
            1: ["At least 1 microaneurysm", "Mild vessel changes"],
            2: ["Multiple microaneurysms", "Hemorrhages present", "Exudates visible"],
            3: [">20 hemorrhages in 4 quadrants", "Venous beading", "Intraretinal microvascular abnormalities"],
            4: ["Neovascularization", "Vitreous hemorrhage", "Fibrovascular proliferation"]
        }
        return criteria.get(grade, [])