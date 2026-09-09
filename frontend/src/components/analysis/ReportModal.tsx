import React from 'react';
import { X, Printer, Download, Eye, ShieldAlert, CheckCircle2, FileText } from 'lucide-react';
import { AnalysisResponse } from '../../types';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  analysis: AnalysisResponse;
}

export const ReportModal: React.FC<Props> = ({ isOpen, onClose, analysis }) => {
  if (!isOpen) return null;

  const { metrics, quality, summary, images, analysis_id, timestamp, filename } = analysis;

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-md p-4 sm:p-6 overflow-y-auto animate-in fade-in duration-200">
      
      <div className="relative w-full max-w-4xl max-h-[90vh] rounded-2xl bg-[#0b1120] text-slate-100 border border-slate-700 shadow-2xl flex flex-col overflow-hidden">
        
        {/* Modal Top Control Bar (Hidden on Print) */}
        <div className="no-print flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/90">
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-emerald-400" />
            <h3 className="text-sm sm:text-base font-bold text-slate-100">
              Retinal Vascular Screening Report
            </h3>
          </div>

          <div className="flex items-center gap-2.5">
            <button
              onClick={handlePrint}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-emerald-500 text-slate-950 font-semibold text-xs hover:bg-emerald-400 transition shadow-lg shadow-emerald-950/50"
            >
              <Printer className="w-4 h-4" />
              <span>Print / Save PDF</span>
            </button>
            <button
              onClick={onClose}
              className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Printable Report Document Body */}
        <div className="flex-1 overflow-y-auto p-6 sm:p-10 space-y-8 bg-[#0b1120] text-slate-100 print:bg-white print:text-black">
          
          {/* Report Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-6 gap-4 print:border-slate-300">
            <div>
              <div className="flex items-center gap-2.5 mb-1">
                <div className="w-8 h-8 rounded-lg bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center print:border-slate-400">
                  <Eye className="w-4 h-4 text-emerald-400 print:text-slate-800" />
                </div>
                <h1 className="text-xl sm:text-2xl font-black tracking-tight text-white print:text-slate-900">
                  OcuPulse
                </h1>
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-emerald-950/60 text-emerald-300 border border-emerald-500/30 print:border-slate-300 print:text-slate-700">
                  Screening Report
                </span>
              </div>
              <p className="text-xs text-slate-400 print:text-slate-600">
                AI-Assisted Quantitative Retinal Blood Vessel Analysis
              </p>
            </div>

            <div className="text-left sm:text-right font-mono text-xs text-slate-300 print:text-slate-700 space-y-1">
              <div><span className="text-slate-500">Analysis ID:</span> <strong>{analysis_id}</strong></div>
              <div><span className="text-slate-500">Date:</span> {new Date(timestamp).toLocaleString()}</div>
              <div><span className="text-slate-500">File:</span> {filename}</div>
              <div>
                <span className="text-slate-500">Quality:</span>{' '}
                <span className="text-emerald-400 font-bold print:text-slate-900">{quality.label} ({Math.round(quality.score * 100)}%)</span>
              </div>
            </div>
          </div>

          {/* Visual Evidence Strip (4 core images) */}
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 print:text-slate-800 mb-3">
              1. Visual Evidence & Computer Vision Stages
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { title: 'Original Fundus', src: images.original },
                { title: 'Enhanced Green', src: images.enhanced },
                { title: 'Vessel Mask', src: images.vessel_mask },
                { title: 'Centerline Skeleton', src: images.skeleton },
              ].map((img, idx) => (
                <div key={idx} className="p-2 rounded-xl bg-slate-900/80 border border-slate-800 print:border-slate-300 print:bg-slate-50 text-center">
                  <img
                    src={img.src}
                    alt={img.title}
                    className="w-full aspect-square object-contain rounded-lg bg-black mb-1.5"
                  />
                  <span className="text-[10px] font-semibold text-slate-300 print:text-slate-700">
                    {img.title}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Quantitative Biomarkers Table */}
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 print:text-slate-800 mb-3">
              2. Quantitative Vascular Geometry Measurements
            </h3>
            <div className="overflow-hidden rounded-xl border border-slate-800 print:border-slate-300">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-900/80 print:bg-slate-100 text-slate-300 print:text-slate-700 font-semibold uppercase tracking-wider border-b border-slate-800 print:border-slate-300">
                  <tr>
                    <th className="px-4 py-2.5">Parameter</th>
                    <th className="px-4 py-2.5">Calculated Value</th>
                    <th className="px-4 py-2.5 hidden sm:table-cell">Physical / Pixel Definition</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 print:divide-slate-200">
                  <tr>
                    <td className="px-4 py-2 font-medium text-slate-200 print:text-slate-900">Vessel Density</td>
                    <td className="px-4 py-2 font-mono font-bold text-emerald-400 print:text-slate-900">{metrics.vessel_density}%</td>
                    <td className="px-4 py-2 text-slate-400 print:text-slate-600 hidden sm:table-cell">Vessel area divided by Retinal ROI area × 100</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-2 font-medium text-slate-200 print:text-slate-900">Total Centerline Length</td>
                    <td className="px-4 py-2 font-mono font-bold text-cyan-400 print:text-slate-900">{metrics.vessel_length_pixels.toLocaleString()} px</td>
                    <td className="px-4 py-2 text-slate-400 print:text-slate-600 hidden sm:table-cell">Zhang-Suen skeleton centerline length</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-2 font-medium text-slate-200 print:text-slate-900">Branch Points (Bifurcations)</td>
                    <td className="px-4 py-2 font-mono font-bold text-purple-400 print:text-slate-900">{metrics.branch_points}</td>
                    <td className="px-4 py-2 text-slate-400 print:text-slate-600 hidden sm:table-cell">Clustered skeleton junction nodes (N_8 ≥ 3)</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-2 font-medium text-slate-200 print:text-slate-900">Vessel Endpoints</td>
                    <td className="px-4 py-2 font-mono font-bold text-amber-400 print:text-slate-900">{metrics.endpoints}</td>
                    <td className="px-4 py-2 text-slate-400 print:text-slate-600 hidden sm:table-cell">Terminal skeleton end pixels (N_8 = 1)</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-2 font-medium text-slate-200 print:text-slate-900">Mean Caliber Index</td>
                    <td className="px-4 py-2 font-mono font-bold text-rose-400 print:text-slate-900">{metrics.average_vessel_width_px} px</td>
                    <td className="px-4 py-2 text-slate-400 print:text-slate-600 hidden sm:table-cell">Vessel area / Centerline length</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-2 font-medium text-slate-200 print:text-slate-900">Fractal Dimension</td>
                    <td className="px-4 py-2 font-mono font-bold text-indigo-400 print:text-slate-900">{metrics.fractal_dimension}</td>
                    <td className="px-4 py-2 text-slate-400 print:text-slate-600 hidden sm:table-cell">Box-counting vascular branching complexity</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Analysis Summary & Observations */}
          <div className="space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 print:text-slate-800">
              3. Objective Screening Observations
            </h3>
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 print:border-slate-300 print:bg-slate-50 space-y-2 text-xs sm:text-sm">
              <p className="font-semibold text-emerald-300 print:text-slate-900">
                {summary.headline}
              </p>
              <ul className="space-y-1 text-slate-300 print:text-slate-700 list-disc list-inside">
                {summary.observations.map((obs: string, i: number) => (
                  <li key={i}>{obs}</li>
                ))}
              </ul>
              <div className="pt-2 border-t border-slate-800 print:border-slate-200 text-xs text-slate-400 print:text-slate-600">
                <strong>Recommendation:</strong> {summary.recommendation}
              </div>
            </div>
          </div>

          {/* Strict Medical Disclaimer Notice */}
          <div className="p-4 rounded-xl bg-amber-950/30 border border-amber-500/30 print:border-slate-400 print:bg-slate-100 text-xs text-slate-300 print:text-slate-800 space-y-1">
            <div className="flex items-center gap-1.5 font-bold text-amber-400 print:text-slate-900 uppercase tracking-wide">
              <ShieldAlert className="w-4 h-4" />
              <span>Mandatory Medical Screening Notice</span>
            </div>
            <p className="leading-relaxed text-[11px]">
              {summary.disclaimer}
            </p>
          </div>

          {/* Signoff / Timestamp */}
          <div className="pt-4 border-t border-slate-800 print:border-slate-300 flex items-center justify-between text-[10px] text-slate-500 font-mono">
            <span>Report Generated via OcuPulse v1.0.0</span>
            <span>SIH Retinal Analysis Architecture</span>
          </div>

        </div>

      </div>

    </div>
  );
};

export default ReportModal;