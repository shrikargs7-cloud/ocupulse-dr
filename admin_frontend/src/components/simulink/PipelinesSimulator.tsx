import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { FaPlay, FaStop, FaRedo, FaMicrochip, FaNetworkWired, FaCheckCircle, FaBolt } from 'react-icons/fa';

export interface PipelineStep {
  id: string;
  label: string;
  sublabel?: string;
  status: 'idle' | 'active' | 'completed' | 'error';
  throughput: number;
  utilization: number;
  latencyMs?: number;
}

interface PipelineSimulatorProps {
  steps?: PipelineStep[];
  onStart?: () => void;
  onStop?: () => void;
  className?: string;
}

const DEFAULT_STEPS: PipelineStep[] = [
  { id: '1', label: 'Ingestion', sublabel: 'Clinic DICOM/JPEG', status: 'idle', throughput: 50, utilization: 65, latencyMs: 24 },
  { id: '2', label: 'Quality Gate', sublabel: 'Laplacian Blur / FOV', status: 'idle', throughput: 45, utilization: 72, latencyMs: 45 },
  { id: '3', label: 'CLAHE & Green', sublabel: 'Illumination Equalize', status: 'idle', throughput: 40, utilization: 68, latencyMs: 60 },
  { id: '4', label: 'Segmentation', sublabel: 'Multi-scale Top-Hat', status: 'idle', throughput: 35, utilization: 74, latencyMs: 120 },
  { id: '5', label: 'Skeletonization', sublabel: 'Zhang-Suen Thinning', status: 'idle', throughput: 30, utilization: 80, latencyMs: 85 },
  { id: '6', label: 'Biomarkers', sublabel: 'Topology & Fractal Dim', status: 'idle', throughput: 28, utilization: 76, latencyMs: 50 },
  { id: '7', label: 'Report Dispatch', sublabel: 'PDF / Cloud Sync', status: 'idle', throughput: 25, utilization: 70, latencyMs: 30 }
];

export const PipelineSimulator: React.FC<PipelineSimulatorProps> = ({
  steps = DEFAULT_STEPS,
  onStart,
  onStop,
  className = ''
}) => {
  const [activeSteps, setActiveSteps] = useState<PipelineStep[]>(steps);
  const [isRunning, setIsRunning] = useState(false);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [imagesProcessed, setImagesProcessed] = useState(1420);
  const [speedMultiplier, setSpeedMultiplier] = useState(1);

  // Sync if external steps prop updates
  useEffect(() => {
    if (steps && steps.length > 0) {
      setActiveSteps(steps);
    }
  }, [steps]);

  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;
    if (isRunning) {
      const stepInterval = Math.max(300, Math.floor(1200 / speedMultiplier));
      interval = setInterval(() => {
        setCurrentStepIndex((prev) => {
          const next = (prev + 1) % activeSteps.length;
          if (next === 0) {
            setImagesProcessed((c) => c + Math.floor(Math.random() * 5 + 3));
          }
          return next;
        });
      }, stepInterval);
    }
    return () => clearInterval(interval);
  }, [isRunning, activeSteps.length, speedMultiplier]);

  const handleStart = () => {
    setIsRunning(true);
    onStart?.();
  };

  const handleStop = () => {
    setIsRunning(false);
    onStop?.();
  };

  const handleReset = () => {
    setIsRunning(false);
    setCurrentStepIndex(0);
    setImagesProcessed(1420);
  };

  return (
    <div className={`card p-6 ${className}`}>
      <div className="flex flex-wrap justify-between items-center mb-6 gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full bg-emerald-950/60 border border-emerald-500/30 text-[10px] font-mono text-emerald-400 mb-1">
            <FaMicrochip className="w-3 h-3" />
            <span>Distributed Inference Model</span>
          </div>
          <h3 className="text-base font-bold text-white">Telemedicine Screening Pipeline Execution</h3>
          <p className="text-xs text-slate-400">
            Real-time simulation of multi-threaded retinal image processing and clinical grading.
          </p>
        </div>

        {/* Controls */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Speed selector */}
          <div className="flex items-center bg-slate-900 border border-slate-800 rounded-xl p-1 text-[11px] font-mono text-slate-300">
            <span className="px-2 text-slate-500">Speed:</span>
            {[1, 2, 4].map((s) => (
              <button
                key={s}
                onClick={() => setSpeedMultiplier(s)}
                className={`px-2 py-0.5 rounded-lg transition ${
                  speedMultiplier === s 
                    ? 'bg-emerald-500 text-slate-950 font-bold' 
                    : 'hover:text-white'
                }`}
              >
                {s}x
              </button>
            ))}
          </div>

          <button
            onClick={handleStart}
            disabled={isRunning}
            className="btn-primary text-xs flex items-center space-x-1.5 shadow-md shadow-emerald-500/20"
          >
            <FaPlay className="w-2.5 h-2.5" />
            <span>Run Sim</span>
          </button>

          <button
            onClick={handleStop}
            disabled={!isRunning}
            className="btn-secondary text-xs flex items-center space-x-1.5"
          >
            <FaStop className="w-2.5 h-2.5" />
            <span>Pause</span>
          </button>

          <button
            onClick={handleReset}
            className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition"
            title="Reset simulation counter"
          >
            <FaRedo className="w-3 h-3" />
          </button>
        </div>
      </div>

      {/* Pipeline visualization */}
      <div className="relative py-8 my-2 overflow-x-auto">
        {/* Continuous Data Flow Track */}
        <div className="relative min-w-[700px]">
          {/* Connection line track */}
          <div className="absolute top-6 left-8 right-8 h-1 bg-slate-800 rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-gradient-to-r from-emerald-500 via-teal-400 to-cyan-400"
              initial={{ width: '0%' }}
              animate={{ width: isRunning ? '100%' : '0%' }}
              transition={{ duration: 1.5, repeat: isRunning ? Infinity : 0, ease: 'linear' }}
            />
          </div>

          {/* Step Nodes */}
          <div className="relative flex justify-between">
            {activeSteps.map((step, index) => {
              const isCurrent = index === currentStepIndex && isRunning;
              const isPast = (index < currentStepIndex || !isRunning) && isRunning;

              return (
                <div key={step.id} className="flex flex-col items-center group w-24">
                  <motion.div
                    animate={{
                      scale: isCurrent ? 1.15 : 1,
                    }}
                    transition={{ type: 'spring', stiffness: 300, damping: 20 }}
                    className={`w-12 h-12 rounded-2xl flex items-center justify-center font-bold text-sm transition-all duration-300 border relative ${
                      isCurrent
                        ? 'bg-emerald-500 text-slate-950 border-emerald-300 shadow-xl shadow-emerald-500/40 z-10 ring-4 ring-emerald-500/20'
                        : isPast
                        ? 'bg-emerald-950/90 text-emerald-300 border-emerald-500/60'
                        : 'bg-slate-900 text-slate-400 border-slate-800'
                    }`}
                  >
                    {isCurrent ? (
                      <FaBolt className="w-5 h-5 animate-pulse text-slate-950" />
                    ) : isPast ? (
                      <FaCheckCircle className="w-4 h-4 text-emerald-400" />
                    ) : (
                      <span className="font-mono">{index + 1}</span>
                    )}

                    {/* Ping animation indicator */}
                    {isCurrent && (
                      <span className="absolute -top-1 -right-1 flex h-3 w-3">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
                      </span>
                    )}
                  </motion.div>

                  <span className={`text-xs font-bold mt-3 text-center transition-colors ${
                    isCurrent ? 'text-emerald-300' : 'text-slate-200'
                  }`}>
                    {step.label}
                  </span>

                  <span className="text-[10px] text-slate-400 text-center font-mono line-clamp-1">
                    {step.sublabel || `${step.throughput} img/s`}
                  </span>

                  <span className="text-[10px] font-mono text-cyan-400 mt-0.5">
                    {step.latencyMs ? `~${step.latencyMs}ms` : `${step.throughput}/s`}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Live Pipeline Statistics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 pt-6 border-t border-slate-800">
        <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800/80">
          <p className="text-xs text-slate-400 font-mono">Processed Fundus Images</p>
          <p className="text-xl font-bold text-white font-mono mt-1">
            {imagesProcessed.toLocaleString()}
          </p>
          <span className="text-[10px] text-emerald-400 font-mono">
            {isRunning ? `+${(speedMultiplier * 4.2).toFixed(1)}/sec active` : 'Idle'}
          </span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800/80">
          <p className="text-xs text-slate-400 font-mono">Pipeline Compute Rate</p>
          <p className="text-xl font-bold text-emerald-400 font-mono mt-1">
            {activeSteps.reduce((sum, s) => sum + s.throughput, 0)} <span className="text-xs text-slate-400 font-normal">img/s</span>
          </p>
          <span className="text-[10px] text-slate-500 font-mono">Max instantaneous bandwidth</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800/80">
          <p className="text-xs text-slate-400 font-mono">Mean End-to-End Latency</p>
          <p className="text-xl font-bold text-cyan-400 font-mono mt-1">
            {activeSteps.reduce((sum, s) => sum + (s.latencyMs || 50), 0)} <span className="text-xs text-slate-400 font-normal">ms</span>
          </p>
          <span className="text-[10px] text-slate-500 font-mono">7-stage image traversal</span>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800/80 flex flex-col justify-between">
          <p className="text-xs text-slate-400 font-mono">Simulation Node Engine</p>
          <div className="mt-1">
            <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-mono font-medium border ${
              isRunning 
                ? 'bg-emerald-950 text-emerald-300 border-emerald-500/40' 
                : 'bg-slate-900 text-slate-400 border-slate-700'
            }`}>
              <span className={`w-1.5 h-1.5 rounded-full mr-1.5 ${isRunning ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'}`} />
              {isRunning ? `Streaming (${speedMultiplier}x)` : 'Paused'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PipelineSimulator;