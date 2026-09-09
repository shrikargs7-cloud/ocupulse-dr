import torch
import torch.nn.functional as F
import numpy as np
import cv2
from typing import Dict, Any, Tuple, Optional

class GradCAM:
    """Gradient-weighted Class Activation Mapping"""
    
    def __init__(self, model, target_layer: Optional[str] = None):
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None
        self.hooks = []
        
        self._register_hooks()
    
    def _register_hooks(self):
        """Register forward and backward hooks"""
        def forward_hook(module, input, output):
            self.activations = output
        
        def backward_hook(module, grad_input, grad_output):
            self.gradients = grad_output[0]
        
        # Find target layer
        if self.target_layer is None:
            # Use last convolutional layer
            self.target_layer = self._find_last_conv_layer()
        
        # Register hooks
        layer = self._get_layer(self.model, self.target_layer)
        self.hooks.append(layer.register_forward_hook(forward_hook))
        self.hooks.append(layer.register_full_backward_hook(backward_hook))
    
    def _find_last_conv_layer(self) -> str:
        """Find the last convolutional layer"""
        for name, module in self.model.named_modules():
            if isinstance(module, torch.nn.Conv2d):
                last_conv = name
        return last_conv
    
    def _get_layer(self, model, layer_name: str):
        """Get layer by name"""
        layers = layer_name.split('.')
        current = model
        for layer in layers:
            current = getattr(current, layer)
        return current
    
    def generate_heatmap(self, input_tensor: torch.Tensor, class_idx: Optional[int] = None) -> np.ndarray:
        """Generate Grad-CAM heatmap"""
        # Forward pass
        output = self.model(input_tensor)
        
        if class_idx is None:
            class_idx = torch.argmax(output, dim=1).item()
        
        # Zero gradients
        self.model.zero_grad()
        
        # Backward pass
        output[0][class_idx].backward()
        
        # Get gradients and activations
        gradients = self.gradients
        activations = self.activations
        
        # Compute weights (global average pooling of gradients)
        weights = torch.mean(gradients, dim=[2, 3], keepdim=True)
        
        # Compute weighted combination of activations
        grad_cam = torch.sum(weights * activations, dim=1, keepdim=True)
        grad_cam = F.relu(grad_cam)
        
        # Normalize
        grad_cam = grad_cam.squeeze().cpu().detach().numpy()
        grad_cam = (grad_cam - grad_cam.min()) / (grad_cam.max() - grad_cam.min() + 1e-8)
        
        return grad_cam
    
    def overlay_heatmap(self, image: np.ndarray, heatmap: np.ndarray, alpha: float = 0.5) -> np.ndarray:
        """Overlay heatmap on original image"""
        # Resize heatmap to image size
        heatmap_resized = cv2.resize(heatmap, (image.shape[1], image.shape[0]))
        
        # Convert to color
        heatmap_colored = cv2.applyColorMap(
            (heatmap_resized * 255).astype(np.uint8),
            cv2.COLORMAP_JET
        )
        
        # Overlay
        if len(image.shape) == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        elif image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        overlay = cv2.addWeighted(image, 1 - alpha, heatmap_colored, alpha, 0)
        
        return overlay
    
    def __del__(self):
        """Remove hooks"""
        for hook in self.hooks:
            hook.remove()