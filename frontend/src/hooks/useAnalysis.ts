import { useState, useCallback } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';

interface AnalysisResult {
  image_id: number;
  quality: {
    grade: 'Good' | 'Borderline' | 'Reject';
    score: number;
    illumination_score: number;
    focus_score: number;
    fov_score: number;
    recommendations?: string;
  };
  grading: {
    grade: number;
    grade_label: string;
    confidence: number;
    is_referable: boolean;
    is_vision_threatening: boolean;
    clinical_criteria: string[];
  };
  lesions: Array<{
    type: string;
    count: number;
    area: number;
    density: number;
    locations: Array<{ x: number; y: number }>;
  }>;
  features: {
    fractal_dimension: number;
    vessel_density: number;
    tortuosity_index: number;
    branching_angle: number;
    vessel_geometry: any;
  };
  grad_cam_heatmap: string;
  processing_time: number;
  matlab_analysis: any;
  model_version: string;
}

interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

export const useAnalysis = () => {
  const [isUploading, setIsUploading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [progress, setProgress] = useState<UploadProgress | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const uploadImage = useCallback(async (file: File, patientId?: string) => {
    setIsUploading(true);
    setError(null);
    setProgress(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      if (patientId) {
        formData.append('patient_id', patientId);
      }

      const response = await axios.post('/api/v1/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            setProgress({
              loaded: progressEvent.loaded,
              total: progressEvent.total,
              percentage: (progressEvent.loaded / progressEvent.total) * 100
            });
          }
        }
      });

      toast.success('Image uploaded successfully!');
      return response.data;
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Upload failed';
      setError(errorMsg);
      toast.error(errorMsg);
      throw err;
    } finally {
      setIsUploading(false);
      setProgress(null);
    }
  }, []);

  const analyzeImage = useCallback(async (imageId: number) => {
    setIsAnalyzing(true);
    setError(null);
    setResult(null);

    try {
      const response = await axios.post(`/api/v1/analyze/${imageId}`, {
        use_matlab: true
      });

      setResult(response.data);
      toast.success('Analysis completed!');
      return response.data;
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Analysis failed';
      setError(errorMsg);
      toast.error(errorMsg);
      throw err;
    } finally {
      setIsAnalyzing(false);
    }
  }, []);

  const batchAnalyze = useCallback(async (imageIds: number[]) => {
    setIsAnalyzing(true);
    setError(null);

    try {
      const response = await axios.post('/api/v1/batch-analyze', {
        image_ids: imageIds
      });

      toast.success(`Batch analysis completed! ${response.data.summary.processed} images processed`);
      return response.data;
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Batch analysis failed';
      setError(errorMsg);
      toast.error(errorMsg);
      throw err;
    } finally {
      setIsAnalyzing(false);
    }
  }, []);

  const getHistory = useCallback(async (filters?: any) => {
    try {
      const response = await axios.get('/api/v1/history', { params: filters });
      return response.data;
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to fetch history';
      toast.error(errorMsg);
      throw err;
    }
  }, []);

  const getResults = useCallback(async (imageId: number) => {
    try {
      const response = await axios.get(`/api/v1/analysis/${imageId}`);
      setResult(response.data);
      return response.data;
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to fetch results';
      toast.error(errorMsg);
      throw err;
    }
  }, []);

  const clearResults = useCallback(() => {
    setResult(null);
    setError(null);
  }, []);

  return {
    isUploading,
    isAnalyzing,
    progress,
    result,
    error,
    uploadImage,
    analyzeImage,
    batchAnalyze,
    getHistory,
    getResults,
    clearResults
  };
};

export default useAnalysis;