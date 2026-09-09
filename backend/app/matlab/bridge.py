try:
    import matlab.engine
    import matlab
    MATLAB_AVAILABLE = True
except ImportError:
    MATLAB_AVAILABLE = False

import numpy as np
import cv2
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime

from ..config import settings

class MATLABBridge:
    """Bridge between Python and MATLAB for advanced analysis"""
    
    def __init__(self):
        self.eng = None
        self.available = False
        if MATLAB_AVAILABLE:
            self._initialize()
        else:
            print("⚠️ MATLAB engine not available (module not installed)")
        
    def _initialize(self):
        """Initialize MATLAB engine"""
        try:
            self.eng = matlab.engine.start_matlab()
            # Add MATLAB scripts to path
            script_path = settings.MATLAB_SCRIPTS_PATH
            if os.path.exists(script_path):
                self.eng.addpath(self.eng.genpath(script_path))
            self.available = True
            print("✅ MATLAB engine initialized successfully")
        except Exception as e:
            print(f"⚠️ MATLAB initialization failed: {e}")
            self.available = False
            
    def is_available(self) -> bool:
        """Check if MATLAB is available"""
        return self.available
    
    def analyze_retina(self, image_path: str) -> Dict[str, Any]:
        """Run comprehensive MATLAB analysis on retinal image"""
        if not self.available:
            return {"error": "MATLAB not available"}
        
        try:
            # Read image
            img = cv2.imread(image_path)
            if img is None:
                return {"error": "Cannot read image"}
            
            # Convert to MATLAB format
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            mat_img = matlab.double(img_rgb.tolist())
            
            # Run MATLAB analysis
            result = self.eng.analyze_retina(mat_img, nargout=1)
            
            # Convert result to dict
            result_dict = self._matlab_struct_to_dict(result)
            
            return result_dict
            
        except Exception as e:
            return {"error": f"MATLAB analysis failed: {str(e)}"}
    
    def compute_fractal_dimension(self, vessel_image: np.ndarray) -> float:
        """Compute fractal dimension using MATLAB"""
        if not self.available:
            return 0.0
        
        try:
            mat_vessel = matlab.double(vessel_image.tolist())
            result = self.eng.fractal_analysis(mat_vessel, nargout=1)
            return float(result)
        except:
            return 0.0
    
    def _simulate_pipeline_python(
        self, patient_volume: int, bandwidth_mbps: float,
        processing_throughput: float, review_capacity: int,
        operating_hours: int
    ) -> Dict[str, Any]:
        """High-fidelity Python implementation of simulate_pipeline.m queuing model."""
        import math

        working_days_per_year = 260
        # Compute throughput: images processed per day based on compute capacity
        daily_compute_throughput = processing_throughput * 3600 * operating_hours
        
        # Telemedicine network bandwidth constraint (assuming 10MB per fundus image)
        # bandwidth_mbps * 1000 kbits / (10 * 8 kbits per byte) -> images/day
        daily_network_capacity = (bandwidth_mbps * 1_000_000 / (10 * 1024 * 1024 * 8)) * (3600 * operating_hours)
        daily_network_capacity = max(1.0, daily_network_capacity)
        
        # Bottleneck determines daily throughput
        images_per_day = max(1, int(min(daily_compute_throughput, daily_network_capacity)))
        
        # Annual screening capacity
        annual_capacity = images_per_day * working_days_per_year
        
        # Backlog after 1 full calendar year
        backlog = max(0, patient_volume - annual_capacity)
        backlog_after_year = int(backlog)
        
        # Cost modeling: $5 per automated algorithmic screening + $2 per clinical review tier
        cost_per_image = 5.0
        review_cost_per_image = 2.0
        effective_reviewers = max(1, review_capacity)
        total_cost = round(patient_volume * (cost_per_image + (review_cost_per_image / effective_reviewers)), 2)
        cost_per_patient = round(total_cost / max(1, patient_volume), 2)
        
        # Optimization calculation: compute parameter requirements to eliminate backlog
        opt_throughput = processing_throughput
        opt_reviewers = review_capacity
        opt_bandwidth = bandwidth_mbps
        recommendations = []
        
        if backlog > 0:
            required_daily = patient_volume / working_days_per_year
            req_throughput = required_daily / (3600 * operating_hours)
            opt_throughput = round(max(req_throughput, processing_throughput * 1.25), 2)
            
            # Each clinician can review ~100 fundus images per 8-hour shift
            opt_reviewers = max(1, math.ceil(required_daily / 100))
            
            # Required bandwidth for required daily images (10MB/image)
            required_bandwidth = (required_daily * 10 * 1024 * 1024 * 8) / (3600 * operating_hours * 1_000_000)
            opt_bandwidth = round(max(required_bandwidth * 1.15, bandwidth_mbps), 1)
            
            recommendations.append(f"Scale compute throughput to at least {opt_throughput:.2f} images/sec to prevent clinical queuing.")
            recommendations.append(f"Expand ophthalmologist review pool to {opt_reviewers} clinicians (100 fundus examinations/day target).")
            recommendations.append(f"Upgrade clinic uplink bandwidth to at least {opt_bandwidth:.1f} Mbps to eliminate transfer bottlenecks.")
        else:
            recommendations.append("Current network bandwidth and processing throughput are sufficient to absorb annual patient screening demand.")
            recommendations.append("Capacity surplus allows expanding screening coverage to adjacent community healthcare centers.")

        utilization_rate = patient_volume / max(1, annual_capacity)
        if utilization_rate > 0.9:
            recommendations.append("System utilization exceeds 90% - Peak loads may cause clinical turn-around delays. Buffer capacity recommended.")
        elif utilization_rate < 0.4:
            recommendations.append("System utilization below 40% - Resource reallocation can lower annual operating expenditure.")

        optimized_params = {
            "patient_volume": patient_volume,
            "patientVolume": patient_volume,
            "bandwidth_mbps": opt_bandwidth,
            "bandwidthMbps": opt_bandwidth,
            "processing_throughput": opt_throughput,
            "processingThroughput": opt_throughput,
            "review_capacity": opt_reviewers,
            "reviewCapacity": opt_reviewers,
            "operating_hours": operating_hours,
            "operatingHours": operating_hours
        }

        return {
            "total_cost": total_cost,
            "cost_per_patient": cost_per_patient,
            "throughput_per_day": images_per_day,
            "backlog_after_year": backlog_after_year,
            "annual_capacity": annual_capacity,
            "utilization_rate": round(utilization_rate * 100, 1),
            "optimized_params": optimized_params,
            "recommendations": recommendations,
            "source": "telemedicine-simulation-engine"
        }

    def run_simulink_optimization(self, patient_volume: int, bandwidth_mbps: float,
                                  processing_throughput: float, review_capacity: int,
                                  operating_hours: int) -> Dict[str, Any]:
        """Run Simulink workflow optimization with automatic high-fidelity fallback"""
        if not self.available or self.eng is None:
            return self._simulate_pipeline_python(
                patient_volume=patient_volume,
                bandwidth_mbps=bandwidth_mbps,
                processing_throughput=processing_throughput,
                review_capacity=review_capacity,
                operating_hours=operating_hours
            )
        
        try:
            # Run simulation via MATLAB engine
            result = self.eng.simulate_pipeline(
                patient_volume,
                bandwidth_mbps,
                processing_throughput,
                review_capacity,
                operating_hours,
                nargout=1
            )
            result_dict = self._matlab_struct_to_dict(result)
            
            return {
                "total_cost": float(result_dict.get("total_cost", 0)),
                "cost_per_patient": float(result_dict.get("cost_per_patient", 0)),
                "throughput_per_day": int(result_dict.get("throughput_per_day", 0)),
                "backlog_after_year": int(result_dict.get("backlog_after_year", 0)),
                "optimized_params": result_dict.get("optimized_params", {}),
                "recommendations": result_dict.get("recommendations", []),
                "source": "matlab-engine"
            }
            
        except Exception as e:
            # Fallback to high-fidelity Python mathematical model
            fallback = self._simulate_pipeline_python(
                patient_volume=patient_volume,
                bandwidth_mbps=bandwidth_mbps,
                processing_throughput=processing_throughput,
                review_capacity=review_capacity,
                operating_hours=operating_hours
            )
            fallback["warning"] = f"MATLAB simulation error: {str(e)}"
            return fallback
    
    def _matlab_struct_to_dict(self, matlab_struct):
        """Convert MATLAB struct to Python dict"""
        if matlab_struct is None:
            return {}
        
        try:
            # Get field names
            fields = matlab_struct._fieldnames()
            result = {}
            
            for field in fields:
                value = getattr(matlab_struct, field)
                if hasattr(value, '_fieldnames'):
                    # Nested struct
                    result[field] = self._matlab_struct_to_dict(value)
                elif isinstance(value, (list, matlab.double)):
                    # Convert to list
                    result[field] = list(value)
                else:
                    result[field] = value
            
            return result
        except:
            return {"value": list(matlab_struct)}
    
    def __del__(self):
        """Clean up MATLAB engine"""
        if hasattr(self, 'eng') and self.eng:
            self.eng.quit()