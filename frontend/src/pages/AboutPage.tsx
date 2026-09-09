import React from 'react';
import {
  Info,
  ShieldCheck,
  Award,
  Layers,
  Cpu,
  Database,
  ArrowUpRight,
  GitBranch,
} from 'lucide-react';
import { MedicalDisclaimer } from '../components/ui/MedicalDisclaimer';

export const AboutPage: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto space-y-12 text-left">
      
      {/* Header */}
      <div className="text-center space-y-3">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-950/60 border border-emerald-500/30 text-xs font-mono text-emerald-400">
          <Info className="w-3.5 h-3.5" />
          <span>Project Overview & Research</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
          About OcuPulse
        </h1>
        <p className="text-sm text-slate-400 max-w-xl mx-auto">
          AI-assisted quantitative retinal vessel analysis and screening platform built for Smart India Hackathon.
        </p>
      </div>

      {/* Mission Section */}
      <div className="p-6 sm:p-8 rounded-3xl glass-panel border border-slate-800 space-y-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <Award className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-100">Project Mission & SIH Focus</h2>
            <p className="text-xs text-slate-400 font-mono">Automating Micro-Vascular Geometry Extraction</p>
          </div>
        </div>

        <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
          Manual delineation of retinal vessels requires significant clinical ophthalmology expertise and is tedious and subjective. <strong>OcuPulse</strong> provides a fast, reproducible, and objective computer-vision pipeline that extracts quantitative structural biomarkers directly from standard retinal fundus photographs.
        </p>
      </div>

      {/* Architecture & Ethical Safeguards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Ethical Standards */}
        <div className="p-6 rounded-2xl glass-panel border border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-emerald-400 font-semibold text-sm">
            <ShieldCheck className="w-4 h-4" />
            <span>Ethical AI & Clinical Positioning</span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            OcuPulse strictly avoids unsupported medical claims. Rather than claiming to diagnose conditions without clinical ground truth, it functions as an <strong>assistive screening instrument</strong> that surfaces observable quantitative features (density, branching, caliber) for human ophthalmologist evaluation.
          </p>
        </div>

        {/* Modular Extensibility */}
        <div className="p-6 rounded-2xl glass-panel border border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-cyan-400 font-semibold text-sm">
            <GitBranch className="w-4 h-4" />
            <span>Future Deep Learning Extension</span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            The processing architecture has a pluggable segmentation interface (<code>segment_vessels</code>). Future versions can effortlessly swap the multi-scale morphological filter with trained U-Net or Attention U-Net deep learning models benchmarked on standard datasets like DRIVE and STARE.
          </p>
        </div>

      </div>

      {/* Dataset & Benchmarking Roadmap */}
      <div className="p-6 sm:p-8 rounded-3xl glass-panel border border-slate-800 space-y-4">
        <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200 font-mono flex items-center gap-2">
          <Database className="w-4 h-4 text-emerald-400" />
          Standard Dataset Validation Roadmap
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
            <span className="font-bold text-slate-200 block">DRIVE Dataset</span>
            <p className="text-slate-400 text-[11px]">Digital Retinal Images for Vessel Extraction (40 calibrated scans with manual ground truth).</p>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
            <span className="font-bold text-slate-200 block">STARE Dataset</span>
            <p className="text-slate-400 text-[11px]">Structured Analysis of the Retina (20 clinical images with expert vascular annotations).</p>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
            <span className="font-bold text-slate-200 block">HRF Dataset</span>
            <p className="text-slate-400 text-[11px]">High-Resolution Fundus dataset for micro-vessel segmentation precision.</p>
          </div>
        </div>
      </div>

      {/* Medical Disclaimer */}
      <MedicalDisclaimer />

    </div>
  );
};

export default AboutPage;