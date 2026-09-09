// src/pages/AnalyzePage.tsx
import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { 
  FaMicroscope, 
  FaPlay, 
  FaHistory, 
  FaCheckCircle, 
  FaInfoCircle, 
  FaEye, 
  FaArrowRight 
} from 'react-icons/fa';

import ImageUploader from '../components/analysis/ImageUploader';
import ProgressIndicator from '../components/analysis/ProgressIndicator';
import MedicalDisclaimer from '../components/ui/MedicalDisclaimer';
import useAnalysis from '../hooks/useAnalysis';
import { analyzeImage as analyzeWithApi } from '../services/api';

interface DemoSample {
  id: string;
  name: string;
  tag: string;
  desc: string;
  badgeColor: string;
}

const DEMO_SAMPLES: DemoSample[] = [
  {
    id: 'demo_normal',
    name: 'Standard Screening',
    tag: 'Normal Control',
    desc: 'Balanced retinal vasculature typical of a healthy screening photograph.',
    badgeColor: 'bg-emerald-950/80 border-emerald-500/40 text-emerald-300',
  },
  {
    id: 'demo_dense',
    name: 'Dense Retinal Arborization',
    tag: 'Complex Vascular Tree',
    desc: 'High vessel density with extensive branching and tortuosity.',
    badgeColor: 'bg-cyan-950/80 border-cyan-500/40 text-cyan-300',
  },
  {
    id: 'demo_subtle',
    name: 'Subtle Micro-Vasculature',
    tag: 'Capillary Challenge',
    desc: 'Fine capillary network testing algorithm sensitivity on delicate vessels.',
    badgeColor: 'bg-purple-950/80 border-purple-500/40 text-purple-300',
  },
];

export const AnalyzePage: React.FC = () => {
  const navigate = useNavigate();
  const { uploadImage, isUploading, progress } = useAnalysis();

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedDemoId, setSelectedDemoId] = useState<string | null>(null);
  const [patientId, setPatientId] = useState<string>('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  const steps = [
    { id: 'upload', label: 'Input Ingestion', status: 'pending' as const },
    { id: 'quality', label: 'Quality Assessment', status: 'pending' as const },
    { id: 'analysis', label: 'Geometry & ML Grading', status: 'pending' as const },
    { id: 'report', label: 'Complete Analysis', status: 'pending' as const },
  ];

  const handleFileDrop = (file: File) => {
    setSelectedFile(file);
    setSelectedDemoId(null);
    setAnalysisError(null);
  };

  const handleSelectDemo = (demoId: string) => {
    setSelectedDemoId(demoId);
    setSelectedFile(null);
    setAnalysisError(null);
  };

  const handleStartAnalysis = async () => {
    if (!selectedFile && !selectedDemoId) {
      toast.error('Please upload an image or choose a demo sample first.');
      return;
    }

    setIsAnalyzing(true);
    setAnalysisError(null);
    setCurrentStep(1);

    try {
      if (selectedDemoId) {
        // Run demo sample through unified backend analysis
        setCurrentStep(2);
        const result = await analyzeWithApi(null, selectedDemoId);
        setCurrentStep(3);
        toast.success('Retinal analysis completed successfully!');
        const id = result.analysis_id || 'DEMO';
        navigate(`/results/${encodeURIComponent(id)}`, { state: { result } });
      } else if (selectedFile) {
        // Run uploaded file
        setCurrentStep(1);
        const uploadRes = await uploadImage(selectedFile, patientId || undefined);
        setCurrentStep(2);
        const result = await analyzeWithApi(selectedFile);
        setCurrentStep(3);
        toast.success('Retinal analysis completed successfully!');
        const id = result.analysis_id || uploadRes.id;
        navigate(`/results/${encodeURIComponent(id)}`, { state: { result } });
      }
    } catch (err: any) {
      console.error('Analysis failed:', err);
      const msg = err.message || err.response?.data?.detail || 'Analysis pipeline failed';
      setAnalysisError(msg);
      toast.error(msg);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto py-2">
      {/* Page Header */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6"
      >
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-950/60 border border-emerald-500/30 text-xs font-mono text-emerald-400 mb-2">
            <FaMicroscope className="w-3.5 h-3.5" />
            <span>AI Diagnostic Ingestion</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            Retinal Fundus Analysis
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Upload retinal fundus photography or test with verified screening samples for zero-hallucination vascular analysis.
          </p>
        </div>

        <button
          onClick={() => navigate('/history')}
          className="self-start md:self-auto btn-secondary text-xs flex items-center gap-2"
        >
          <FaHistory />
          <span>Past Sessions</span>
        </button>
      </motion.div>

      {/* Medical Disclaimer */}
      <MedicalDisclaimer />

      {/* Main Analysis Workflow */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left 2 Columns: Uploader & Demo Samples */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Uploader Card */}
          <div className="card p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-semibold text-white flex items-center gap-2">
                <FaEye className="text-emerald-400" />
                <span>Upload Photograph</span>
              </h2>
              {selectedFile && (
                <button
                  onClick={() => setSelectedFile(null)}
                  className="text-xs text-rose-400 hover:underline"
                >
                  Clear File
                </button>
              )}
            </div>

            <ImageUploader
              onUpload={handleFileDrop}
              isUploading={isUploading || isAnalyzing}
            />

            {progress && (
              <div className="mt-4 space-y-1.5">
                <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                  <div
                    className="bg-emerald-500 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${progress.percentage}%` }}
                  />
                </div>
                <p className="text-xs text-slate-400 font-mono text-right">
                  Uploading Image: {progress.percentage.toFixed(0)}%
                </p>
              </div>
            )}
          </div>

          {/* Quick Demo Samples Selection */}
          <div className="card p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                  <FaCheckCircle className="text-emerald-400 text-xs" />
                  <span>Or Quick-Test with Validated Demo Samples</span>
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Pre-calibrated clinical fundus datasets for rapid demonstration.
                </p>
              </div>
              {selectedDemoId && (
                <button
                  onClick={() => setSelectedDemoId(null)}
                  className="text-xs text-slate-400 hover:text-white"
                >
                  Deselect
                </button>
              )}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {DEMO_SAMPLES.map((sample) => {
                const isSelected = selectedDemoId === sample.id;
                return (
                  <button
                    key={sample.id}
                    type="button"
                    onClick={() => handleSelectDemo(sample.id)}
                    className={`p-4 rounded-xl text-left transition-all border ${
                      isSelected
                        ? 'bg-emerald-500/15 border-emerald-400 ring-2 ring-emerald-500/30'
                        : 'bg-slate-900/60 border-slate-800 hover:border-slate-700 hover:bg-slate-900'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${sample.badgeColor}`}>
                        {sample.tag}
                      </span>
                      {isSelected && (
                        <FaCheckCircle className="text-emerald-400 text-xs" />
                      )}
                    </div>
                    <div className="text-xs font-semibold text-slate-100">
                      {sample.name}
                    </div>
                    <p className="text-[11px] text-slate-400 mt-1 leading-relaxed line-clamp-2">
                      {sample.desc}
                    </p>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right 1 Column: Metadata & Action CTA */}
        <div className="space-y-6">
          
          {/* Patient Details & Action */}
          <div className="card p-6 space-y-5">
            <h3 className="text-sm font-semibold text-white tracking-wide uppercase font-mono flex items-center gap-2">
              <FaInfoCircle className="text-emerald-400" />
              <span>Session Metadata</span>
            </h3>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Patient Identifier (Optional)
              </label>
              <input
                type="text"
                value={patientId}
                onChange={(e) => setPatientId(e.target.value)}
                placeholder="e.g., P-2026-0908-001"
                className="input-field"
                disabled={isAnalyzing}
              />
              <p className="text-[11px] text-slate-500 mt-1 font-mono">
                Opaque ID for clinical confidentiality
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1.5 text-xs text-slate-300">
              <div className="flex justify-between text-slate-400">
                <span>Selected Target:</span>
                <span className="font-mono text-emerald-400 font-semibold">
                  {selectedFile ? selectedFile.name : selectedDemoId ? selectedDemoId : 'None'}
                </span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Analysis Engine:</span>
                <span className="font-mono text-slate-200">OpenCV + NumPy</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Database Sync:</span>
                <span className="font-mono text-slate-200">Active</span>
              </div>
            </div>

            {/* Run Analysis CTA Button */}
            <button
              onClick={handleStartAnalysis}
              disabled={isAnalyzing || (!selectedFile && !selectedDemoId)}
              className="btn-primary w-full py-3 text-sm flex items-center justify-center gap-2 text-slate-950 font-bold"
            >
              {isAnalyzing ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-slate-950 border-t-transparent" />
                  <span>Processing Retinal Pixels...</span>
                </>
              ) : (
                <>
                  <FaPlay className="text-xs" />
                  <span>Run Retinal Analysis</span>
                  <FaArrowRight className="text-xs ml-1" />
                </>
              )}
            </button>

            {analysisError && (
              <div className="p-3 rounded-xl bg-rose-950/60 border border-rose-500/40 text-rose-300 text-xs">
                {analysisError}
              </div>
            )}
          </div>

          {/* Progress Tracker Card */}
          {isAnalyzing && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="card p-6 space-y-4"
            >
              <h3 className="text-xs font-mono font-bold uppercase text-slate-200">
                Execution Steps
              </h3>
              <ProgressIndicator
                steps={steps.map((step, index) => ({
                  ...step,
                  status: index < currentStep ? 'completed' : 
                          index === currentStep ? 'active' : 'pending'
                }))}
                currentStep={currentStep}
              />
            </motion.div>
          )}

        </div>
      </div>
    </div>
  );
};

export default AnalyzePage;