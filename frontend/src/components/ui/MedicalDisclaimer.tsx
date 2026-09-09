import React from 'react';
import { AlertCircle, ShieldCheck } from 'lucide-react';

interface Props {
  compact?: boolean;
}

export const MedicalDisclaimer: React.FC<Props> = ({ compact = false }) => {
  if (compact) {
    return (
      <div className="flex items-center gap-2 px-3 py-2 text-xs font-medium text-amber-300 bg-amber-950/40 border border-amber-500/20 rounded-lg">
        <AlertCircle className="w-4 h-4 flex-shrink-0 text-amber-400" />
        <span>
          <strong>Medical Disclaimer:</strong> AI-assisted screening tool only. Does not replace professional clinical ophthalmologist diagnosis.
        </span>
      </div>
    );
  }

  return (
    <div className="relative overflow-hidden p-4 sm:p-5 rounded-xl bg-gradient-to-r from-amber-950/30 via-slate-900/60 to-slate-900/40 border border-amber-500/30 shadow-lg">
      <div className="flex items-start gap-3.5">
        <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20 mt-0.5">
          <ShieldCheck className="w-5 h-5" />
        </div>
        <div className="space-y-1">
          <h4 className="text-sm font-semibold text-amber-300 tracking-wide uppercase flex items-center gap-2">
            Important Medical Disclaimer
            <span className="text-[10px] normal-case px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30">
              Non-Diagnostic Tool
            </span>
          </h4>
          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
            <strong>OcuPulse</strong> is an AI-assisted retinal image analysis and screening tool. It is <strong>not intended to provide a definitive medical diagnosis</strong>. Vascular measurements, skeleton lengths, and branching indices represent objective geometric computer-vision observations. All results must be reviewed by a qualified ophthalmologist or healthcare professional alongside comprehensive clinical patient examinations.
          </p>
        </div>
      </div>
    </div>
  );
};

export default MedicalDisclaimer;