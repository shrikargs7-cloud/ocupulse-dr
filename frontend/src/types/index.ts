/**
 * OcuPulse TypeScript Type Definitions
 */

export interface QuantitativeMetrics {
  vessel_density: number;
  vessel_area: number;
  vessel_length_pixels: number;
  branch_points: number;
  endpoints: number;
  skeleton_density: number;
  vessel_to_roi_ratio: number;
  average_vessel_width_px: number;
  branching_index: number;
  fractal_dimension: number;
  tortuosity_index: number;
  mean_branching_angle_deg: number;
  roi_pixels: number;
}

export interface QualityDetails {
  sharpness_laplacian: number;
  rms_contrast: number;
  illumination_uniformity: number;
  roi_coverage_percent: number;
  mean_intensity: number;
}

export interface ImageQuality {
  score: number;
  label: 'Good' | 'Moderate' | 'Poor';
  description: string;
  metrics: QualityDetails;
}

export interface ScreeningSummary {
  headline: string;
  observations: string[];
  full_text: string;
  screening_status: string;
  recommendation: string;
  disclaimer: string;
}

export interface AnalysisImages {
  original: string;
  enhanced: string;
  roi_mask: string;
  vessel_mask: string;
  vessel_overlay: string;
  skeleton: string;
  skeleton_mask?: string;
  gradcam?: string;
}

export interface Appointment {
  id: number;
  appointment_id: string;
  analysis_id?: string;
  patient_id?: string;
  patient_name: string;
  doctor_name: string;
  doctor_specialty: string;
  hospital_name: string;
  clinic_room: string;
  contact_phone: string;
  scheduled_time: string;
  priority: string;
  status: 'CONFIRMED' | 'ATTENDED' | 'CANCELLED' | 'RESCHEDULED' | string;
  dr_grade?: number;
  severity_level?: string;
  clinical_reason?: string;
  action_required?: string;
  doctor_id?: string;
  verification_status?: 'PENDING_DOCTOR_REVIEW' | 'VERIFIED_SCHEDULED' | string;
  doctor_notes?: string;
  verified_at?: string;
  created_at: string;
}

export interface DoctorProfile {
  id?: number;
  doctor_id: string;
  full_name: string;
  phone_number: string;
  email?: string;
  specialty: string;
  hospital_name: string;
  clinic_room: string;
  license_number?: string;
  is_active_on_call: boolean;
  created_at?: string;
}

export interface SMSLogItem {
  id: number;
  recipient_phone: string;
  recipient_name: string;
  recipient_role: string;
  message_text: string;
  trigger_event: string;
  status: string;
  gateway: string;
  sent_at: string;
}

export interface AnalysisResponse {
  success: boolean;
  analysis_id: string;
  timestamp: string;
  filename: string;
  metrics: QuantitativeMetrics;
  quality: ImageQuality;
  summary: ScreeningSummary;
  images: AnalysisImages;
  dimensions: {
    width: number;
    height: number;
  };
  timing: {
    preprocessing_sec?: number;
    segmentation_sec?: number;
    overlay_sec?: number;
    skeletonization_sec?: number;
    geometry_sec?: number;
    quality_sec?: number;
    total_execution_sec: number;
  };
  dr_grade?: number;
  dr_confidence?: number;
  referable_dr?: boolean;
  vision_threatening?: boolean;
  is_critical?: boolean;
  lesions?: {
    microaneurysms?: number;
    exudates?: number;
    hemorrhages?: number;
    neovascularization?: number;
  };
  appointment?: Appointment;
}

export interface HistoryItem {
  analysis_id: string;
  timestamp: string;
  filename: string;
  quality_score: number;
  quality_label: string;
  vessel_density: number;
  vessel_area: number;
  vessel_length_pixels: number;
  branch_points: number;
  endpoints: number;
  skeleton_density: number;
  average_vessel_width_px: number;
  fractal_dimension: number;
  summary_headline: string;
  thumbnail_base64?: string;
}

export interface DemoSampleItem {
  id: string;
  name: string;
  description: string;
  sample_type: string;
  preview_url: string;
}

export type NavigationTab = 
  | 'landing' 
  | 'analyze' 
  | 'results' 
  | 'history' 
  | 'how-it-works' 
  | 'about'
  | 'simulink'
  | 'models'
  | 'appointments'
  | 'doctor';