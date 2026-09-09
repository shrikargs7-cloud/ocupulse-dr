import React from 'react';
import {
  HelpCircle,
  Eye,
  Sliders,
  Layers,
  Sparkles,
  GitFork,
  Ruler,
  ShieldCheck,
  Zap,
} from 'lucide-react';
import { MedicalDisclaimer } from '../components/ui/MedicalDisclaimer';

export const HowItWorksPage: React.FC = () => {
  const steps = [
    {
      num: '01',
      title: 'Input Ingestion & Format Validation',
      desc: 'Validates uploaded image matrix integrity, color space (BGR/RGB), minimum resolution (100x100 px), and variance to reject blank or corrupted files.',
      badge: 'Input Verification',
    },
    {
      num: '02',
      title: 'Retinal Field of View (ROI) Detection',
      desc: 'Isolates the anatomical circular/elliptical retina from black borders and out-of-field artifacts using luminance thresholding, morphological closing, and contour convex hull estimation.',
      badge: 'Boundary Isolation',
    },
    {
      num: '03',
      title: 'Green Channel Spectral Extraction',
      desc: 'Retinal blood vessels have peak light absorption in the green spectrum (~540–570 nm), producing the highest vessel-to-choroid contrast against the retinal pigment epithelium.',
      badge: 'Spectral Isolation',
    },
    {
      num: '04',
      title: 'CLAHE Local Contrast Enhancement',
      desc: 'Applies Contrast Limited Adaptive Histogram Equalization with tuned clip limits and grid tiles to balance uneven fundus illumination and boost micro-capillary visibility.',
      badge: 'Contrast Normalization',
    },
    {
      num: '05',
      title: 'Multi-Scale Morphological Vessel Segmentation',
      desc: 'Fuses multi-scale Top-Hat ridge filters with local adaptive Gaussian thresholding, constrained strictly within the retinal ROI to generate clean binary vessel masks (255 = vessel, 0 = background).',
      badge: 'Segmentation Engine',
    },
    {
      num: '06',
      title: 'Centerline Thinning & Skeletonization',
      desc: 'Employs Zhang-Suen morphological thinning to reduce thick vessels to exact 1-pixel-wide centerlines, preserving vascular topology for geometric calculation.',
      badge: 'Topology Engine',
    },
    {
      num: '07',
      title: 'Parametric Biomarkers & Report Generation',
      desc: 'Calculates vessel density percentage, skeleton length, 8-connectivity junction nodes (branch points), terminal tips (endpoints), fractal dimension, and image quality.',
      badge: 'Quantitative Analytics',
    },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-12">
      
      {/* Header */}
      <div className="text-center space-y-3">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-950/60 border border-emerald-500/30 text-xs font-mono text-emerald-400">
          <HelpCircle className="w-3.5 h-3.5" />
          <span>Pipeline Documentation</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
          How OcuPulse Analyzes Retinal Images
        </h1>
        <p className="text-sm text-slate-400 max-w-xl mx-auto">
          A step-by-step walkthrough of the computer vision and mathematical algorithms powering our automated retinal vessel analysis.
        </p>
      </div>

      {/* Steps List */}
      <div className="space-y-6">
        {steps.map((stg) => (
          <div
            key={stg.num}
            className="p-6 rounded-2xl glass-panel border border-slate-800 flex flex-col sm:flex-row sm:items-start gap-5 hover:border-emerald-500/30 transition-all"
          >
            <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center font-mono font-bold text-lg flex-shrink-0">
              {stg.num}
            </div>

            <div className="space-y-2 flex-1">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h3 className="text-base font-bold text-slate-100">
                  {stg.title}
                </h3>
                <span className="text-[10px] font-mono px-2.5 py-0.5 rounded-full bg-slate-900 text-emerald-400 border border-emerald-500/30">
                  {stg.badge}
                </span>
              </div>
              <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
                {stg.desc}
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* Formula & Mathematics Callout */}
      <div className="p-6 sm:p-8 rounded-3xl glass-panel-glow border border-emerald-500/30 space-y-4">
        <h3 className="text-sm font-bold uppercase tracking-wider text-emerald-400 font-mono flex items-center gap-2">
          <Zap className="w-4 h-4" />
          Key Mathematical Formulas
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono">
          <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-1">
            <span className="text-slate-400 font-sans font-semibold block">Vessel Density (%)</span>
            <div className="text-emerald-300 text-sm">
              (Total Vessel Pixels / Retinal ROI Pixels) × 100
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-1">
            <span className="text-slate-400 font-sans font-semibold block">Junction / Branch Points</span>
            <div className="text-purple-300 text-sm">
              Cluster(Skeleton Pixels with ∑ N_8 Neighbors ≥ 3)
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-1">
            <span className="text-slate-400 font-sans font-semibold block">Terminal Endpoints</span>
            <div className="text-amber-300 text-sm">
              Count(Skeleton Pixels with ∑ N_8 Neighbors == 1)
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-1">
            <span className="text-slate-400 font-sans font-semibold block">Average Caliber Index</span>
            <div className="text-cyan-300 text-sm">
              Total Vessel Area / Centerline Length (px)
            </div>
          </div>
        </div>
      </div>

      {/* Medical Disclaimer */}
      <MedicalDisclaimer />

    </div>
  );
};

export default HowItWorksPage;