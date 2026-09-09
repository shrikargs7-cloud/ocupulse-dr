import React, { useEffect, useState } from 'react';
import { CheckCircle2, Loader2, Sparkles } from 'lucide-react';

interface Props {
  isAnalyzing: boolean;
}

const STAGES = [
  { id: 1, label: 'Image payload validated & dimensions verified' },
  { id: 2, label: 'Circular retinal field of view (ROI) isolated' },
  { id: 3, label: 'Green channel extracted & CLAHE contrast enhanced' },
  { id: 4, label: 'Retinal blood vessels segmented (Multi-scale filter)' },
  { id: 5, label: 'Vessel centerline skeleton extracted (Zhang-Suen)' },
  { id: 6, label: 'Vascular geometry, branch & endpoints calculated' },
  { id: 7, label: 'Image quality assessed & screening summary generated' },
];

export const ProgressIndicator: React.FC<Props> = ({ isAnalyzing }) => {
  const [currentStage, setCurrentStage] = useState(1);

  useEffect(() => {
    if (!isAnalyzing) {
      setCurrentStage(1);
      return;
    }

    // Progress through visual steps during the asynchronous backend call
    const interval = setInterval(() => {
      setCurrentStage((prev) => (prev < STAGES.length ? prev + 1 : prev));
    }, 450);

    return () => clearInterval(interval);
  }, [isAnalyzing]);

  return (
    <div className="w-full max-w-xl mx-auto p-6 rounded-2xl glass-panel-glow text-left space-y-5 animate-in fade-in zoom-in-95 duration-300">
      
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center">
            <Loader2 className="w-5 h-5 text-emerald-400 animate-spin" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-slate-100">
              Processing Retinal Fundus Photograph
            </h4>
            <p className="text-xs text-emerald-400 font-mono">
              Running computer vision analysis pipeline...
            </p>
          </div>
        </div>
        <span className="text-xs font-mono px-2.5 py-1 rounded-full bg-emerald-950/80 text-emerald-300 border border-emerald-500/30">
          Step {Math.min(currentStage, STAGES.length)} / {STAGES.length}
        </span>
      </div>

      {/* Step by step checklist */}
      <div className="space-y-3">
        {STAGES.map((stage) => {
          const isDone = stage.id < currentStage;
          const isCurrent = stage.id === currentStage;
          const isPending = stage.id > currentStage;

          return (
            <div
              key={stage.id}
              className={`flex items-center gap-3 text-xs sm:text-sm p-2 rounded-lg transition-all ${
                isCurrent
                  ? 'bg-emerald-500/10 text-emerald-200 border border-emerald-500/20 font-medium'
                  : isDone
                  ? 'text-slate-300'
                  : 'text-slate-500 opacity-60'
              }`}
            >
              <div className="flex-shrink-0">
                {isDone ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : isCurrent ? (
                  <Loader2 className="w-4 h-4 text-emerald-400 animate-spin" />
                ) : (
                  <div className="w-4 h-4 rounded-full border border-slate-700 flex items-center justify-center text-[9px] font-mono text-slate-600">
                    {stage.id}
                  </div>
                )}
              </div>
              <span className="truncate">{stage.label}</span>
            </div>
          );
        })}
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
        <div
          className="bg-gradient-to-r from-emerald-500 via-teal-400 to-emerald-300 h-full rounded-full transition-all duration-300"
          style={{ width: `${(currentStage / STAGES.length) * 100}%` }}
        />
      </div>

    </div>
  );
};

export default ProgressIndicator;