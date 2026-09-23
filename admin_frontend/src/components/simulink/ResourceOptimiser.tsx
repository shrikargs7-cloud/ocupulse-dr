import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  FaCogs,
  FaDatabase,
  FaNetworkWired,
  FaUsers,
  FaClock,
  FaChartLine,
  FaCheckCircle,
  FaExclamationTriangle,
  FaArrowRight
} from 'react-icons/fa';
import toast from 'react-hot-toast';

export interface ResourceConfig {
  patientVolume: number;
  bandwidthMbps: number;
  processingThroughput: number;
  reviewCapacity: number;
  operatingHours: number;
}

export interface OptimizationResult {
  simulationId?: number;
  totalCost: number;
  costPerPatient: number;
  throughputPerDay: number;
  backlogAfterYear: number;
  annualCapacity?: number;
  utilizationRate?: number;
  optimizedParams: ResourceConfig;
  recommendations: string[];
  source?: string;
}

interface ResourceOptimiserProps {
  onOptimizationComplete?: (result: OptimizationResult, currentConfig: ResourceConfig) => void;
}

const PRESETS = [
  {
    id: 'rural_phc',
    name: 'Rural PHC Clinic',
    desc: 'Low-bandwidth remote clinic (25K screening)',
    config: {
      patientVolume: 25000,
      bandwidthMbps: 15,
      processingThroughput: 5,
      reviewCapacity: 10,
      operatingHours: 6
    }
  },
  {
    id: 'district_hub',
    name: 'District Hospital Grid',
    desc: 'Standard district hub (100K screening)',
    config: {
      patientVolume: 100000,
      bandwidthMbps: 100,
      processingThroughput: 30,
      reviewCapacity: 50,
      operatingHours: 8
    }
  },
  {
    id: 'state_grid',
    name: 'State-Wide Network',
    desc: 'High-volume central cluster (500K screening)',
    config: {
      patientVolume: 500000,
      bandwidthMbps: 500,
      processingThroughput: 120,
      reviewCapacity: 180,
      operatingHours: 12
    }
  }
];

export const ResourceOptimiser: React.FC<ResourceOptimiserProps> = ({ onOptimizationComplete }) => {
  const [config, setConfig] = useState<ResourceConfig>({
    patientVolume: 100000,
    bandwidthMbps: 100,
    processingThroughput: 30,
    reviewCapacity: 50,
    operatingHours: 8
  });

  const [isOptimizing, setIsOptimizing] = useState(false);
  const [result, setResult] = useState<OptimizationResult | null>(null);

  const handleApplyPreset = (presetConfig: ResourceConfig) => {
    setConfig(presetConfig);
    toast.success('Preset profile applied');
  };

  const handleOptimize = async () => {
    setIsOptimizing(true);
    try {
      // Backend expects snake_case SimulinkParams
      const payload = {
        patient_volume: Number(config.patientVolume),
        bandwidth_mbps: Number(config.bandwidthMbps),
        processing_throughput: Number(config.processingThroughput),
        review_capacity: Number(config.reviewCapacity),
        operating_hours: Number(config.operatingHours)
      };

      const response = await fetch('/api/v1/simulink/optimize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || 'Optimization failed');
      }
      
      const data = await response.json();
      
      // Map response safely regardless of casing
      const optP = data.optimized_params || {};
      const mappedResult: OptimizationResult = {
        simulationId: data.simulation_id,
        totalCost: Number(data.total_cost ?? data.totalCost ?? 0),
        costPerPatient: Number(data.cost_per_patient ?? data.costPerPatient ?? 0),
        throughputPerDay: Number(data.throughput_per_day ?? data.throughputPerDay ?? 0),
        backlogAfterYear: Number(data.backlog_after_year ?? data.backlogAfterYear ?? 0),
        annualCapacity: Number(data.annual_capacity ?? 0),
        utilizationRate: Number(data.utilization_rate ?? 0),
        optimizedParams: {
          patientVolume: Number(optP.patient_volume ?? optP.patientVolume ?? config.patientVolume),
          bandwidthMbps: Number(optP.bandwidth_mbps ?? optP.bandwidthMbps ?? config.bandwidthMbps),
          processingThroughput: Number(optP.processing_throughput ?? optP.processingThroughput ?? config.processingThroughput),
          reviewCapacity: Number(optP.review_capacity ?? optP.reviewCapacity ?? config.reviewCapacity),
          operatingHours: Number(optP.operating_hours ?? optP.operatingHours ?? config.operatingHours)
        },
        recommendations: Array.isArray(data.recommendations) ? data.recommendations : [],
        source: data.source || 'telemedicine-simulation-engine'
      };

      setResult(mappedResult);
      if (onOptimizationComplete) {
        onOptimizationComplete(mappedResult, config);
      }
      toast.success('Simulation & resource optimization completed!');
    } catch (error: any) {
      toast.error(error.message || 'Failed to optimize resources');
      console.error('Optimization error:', error);
    } finally {
      setIsOptimizing(false);
    }
  };

  const handleApplyOptimized = () => {
    if (!result) return;
    setConfig(result.optimizedParams);
    toast.success('Optimal parameters applied to configuration inputs!');
  };

  const handleInputChange = (field: keyof ResourceConfig, value: number) => {
    if (!isNaN(value) && value >= 0) {
      setConfig(prev => ({ ...prev, [field]: value }));
    }
  };

  return (
    <div className="card p-6">
      <div className="flex flex-wrap items-center justify-between mb-6 gap-4 border-b border-slate-800 pb-4">
        <div>
          <h3 className="text-base font-bold text-white flex items-center space-x-2">
            <FaCogs className="text-emerald-400" />
            <span>Telemedicine Resource Optimizer</span>
          </h3>
          <p className="text-xs text-slate-400">
            Simulate network bandwidth, clinical review capacity, and district screening backlogs.
          </p>
        </div>
        <button
          onClick={handleOptimize}
          disabled={isOptimizing}
          className="btn-primary text-xs flex items-center space-x-2 shadow-lg shadow-emerald-500/20"
        >
          <FaChartLine className={isOptimizing ? 'animate-spin' : ''} />
          <span>{isOptimizing ? 'Running Simulation...' : 'Run Optimization'}</span>
        </button>
      </div>

      {/* District Deployment Presets */}
      <div className="mb-6">
        <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block mb-2">
          Deployment Archetype Presets:
        </span>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {PRESETS.map((preset) => (
            <button
              key={preset.id}
              onClick={() => handleApplyPreset(preset.config)}
              className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 hover:border-emerald-500/50 hover:bg-slate-800/80 transition text-left group"
            >
              <span className="text-xs font-bold text-slate-200 group-hover:text-emerald-300 block">
                {preset.name}
              </span>
              <span className="text-[10px] text-slate-400 block mt-0.5">
                {preset.desc}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Configuration Inputs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1.5 font-mono">
            <FaUsers className="inline mr-1 text-emerald-400" /> Patient Volume (Annual)
          </label>
          <input
            type="number"
            value={config.patientVolume}
            onChange={(e) => handleInputChange('patientVolume', parseInt(e.target.value, 10))}
            className="input-field"
            min="1000"
            max="2000000"
            step="5000"
          />
          <span className="text-[10px] text-slate-500 mt-1 block">Annual screening population</span>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1.5 font-mono">
            <FaNetworkWired className="inline mr-1 text-cyan-400" /> Bandwidth (Mbps)
          </label>
          <input
            type="number"
            value={config.bandwidthMbps}
            onChange={(e) => handleInputChange('bandwidthMbps', parseFloat(e.target.value))}
            className="input-field"
            min="1"
            max="10000"
            step="5"
          />
          <span className="text-[10px] text-slate-500 mt-1 block">Available uplink per clinic site</span>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1.5 font-mono">
            <FaDatabase className="inline mr-1 text-purple-400" /> Processing Rate (img/s)
          </label>
          <input
            type="number"
            value={config.processingThroughput}
            onChange={(e) => handleInputChange('processingThroughput', parseFloat(e.target.value))}
            className="input-field"
            min="0.5"
            max="1000"
            step="1"
          />
          <span className="text-[10px] text-slate-500 mt-1 block">Automated AI compute throughput</span>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1.5 font-mono">
            <FaUsers className="inline mr-1 text-amber-400" /> Review Capacity (Doctors)
          </label>
          <input
            type="number"
            value={config.reviewCapacity}
            onChange={(e) => handleInputChange('reviewCapacity', parseInt(e.target.value, 10))}
            className="input-field"
            min="1"
            max="500"
            step="1"
          />
          <span className="text-[10px] text-slate-500 mt-1 block">Clinician reviews per 8-hr shift</span>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1.5 font-mono">
            <FaClock className="inline mr-1 text-teal-400" /> Operating Hours (per day)
          </label>
          <input
            type="number"
            value={config.operatingHours}
            onChange={(e) => handleInputChange('operatingHours', parseFloat(e.target.value))}
            className="input-field"
            min="1"
            max="24"
            step="1"
          />
          <span className="text-[10px] text-slate-500 mt-1 block">Daily clinic operating window</span>
        </div>
      </div>

      {/* Results */}
      {result && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="border-t border-slate-800 pt-6 mt-6 space-y-6"
        >
          <div className="flex items-center justify-between">
            <h4 className="font-semibold text-white text-sm font-mono uppercase tracking-wider flex items-center gap-2">
              <FaCheckCircle className="text-emerald-400" />
              <span>Simulation & Optimization Results</span>
            </h4>
            <span className="text-[10px] font-mono px-2.5 py-1 rounded-full bg-slate-900 border border-slate-700 text-slate-300">
              Run #{result.simulationId || 'Live'}
            </span>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl">
              <p className="text-xs font-mono text-slate-400">Total Program Cost</p>
              <p className="text-xl font-bold font-mono text-white mt-1">
                ${(result.totalCost / 1000).toFixed(1)}K
              </p>
              <span className="text-[10px] text-slate-500 font-mono">Annual Capex + Opex</span>
            </div>
            <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl">
              <p className="text-xs font-mono text-slate-400">Cost per Patient</p>
              <p className="text-xl font-bold font-mono text-emerald-400 mt-1">
                ${result.costPerPatient.toFixed(2)}
              </p>
              <span className="text-[10px] text-slate-500 font-mono">Comprehensive screening</span>
            </div>
            <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl">
              <p className="text-xs font-mono text-slate-400">Throughput / Day</p>
              <p className="text-xl font-bold font-mono text-cyan-400 mt-1">
                {result.throughputPerDay.toLocaleString()}
              </p>
              <span className="text-[10px] text-slate-500 font-mono">Max fundus scans/day</span>
            </div>
            <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl">
              <p className="text-xs font-mono text-slate-400">Yearly Backlog</p>
              <p className={`text-xl font-bold font-mono mt-1 ${result.backlogAfterYear > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                {result.backlogAfterYear.toLocaleString()}
              </p>
              <span className="text-[10px] text-slate-500 font-mono">
                {result.backlogAfterYear > 0 ? 'Patients unserved' : 'Zero backlog!'}
              </span>
            </div>
          </div>

          {/* Optimal Operating Parameters */}
          <div className="bg-emerald-950/30 border border-emerald-500/30 rounded-2xl p-5 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h5 className="font-semibold text-emerald-300 text-xs uppercase font-mono">
                Optimal Operating Configuration Recommendation
              </h5>
              <button
                onClick={handleApplyOptimized}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 text-xs font-mono hover:bg-emerald-500/30 transition"
              >
                <span>Apply Optimal Settings</span>
                <FaArrowRight className="w-2.5 h-2.5" />
              </button>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
              <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-800">
                <span className="text-slate-400 block font-mono text-[11px]">Recommended Bandwidth:</span>
                <span className="font-bold text-emerald-400 font-mono text-base">
                  {result.optimizedParams.bandwidthMbps.toFixed(1)} Mbps
                </span>
              </div>
              <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-800">
                <span className="text-slate-400 block font-mono text-[11px]">Recommended Compute:</span>
                <span className="font-bold text-emerald-400 font-mono text-base">
                  {result.optimizedParams.processingThroughput.toFixed(1)} img/s
                </span>
              </div>
              <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-800">
                <span className="text-slate-400 block font-mono text-[11px]">Recommended Reviewers:</span>
                <span className="font-bold text-emerald-400 font-mono text-base">
                  {result.optimizedParams.reviewCapacity} Doctors
                </span>
              </div>
              <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-800">
                <span className="text-slate-400 block font-mono text-[11px]">Operating Window:</span>
                <span className="font-bold text-emerald-400 font-mono text-base">
                  {result.optimizedParams.operatingHours} hrs/day
                </span>
              </div>
            </div>
          </div>

          {/* Strategic Recommendations */}
          {result.recommendations && result.recommendations.length > 0 && (
            <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 space-y-3">
              <h5 className="font-semibold text-white text-xs uppercase font-mono flex items-center gap-2">
                <FaExclamationTriangle className="text-amber-400" />
                <span>Simulink Engineering Recommendations</span>
              </h5>
              <ul className="space-y-2 text-xs text-slate-300">
                {result.recommendations.map((rec: string, idx: number) => (
                  <li key={idx} className="flex items-start gap-2 leading-relaxed">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5 flex-shrink-0" />
                    <span>{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </motion.div>
      )}
    </div>
  );
};

export default ResourceOptimiser;