import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Network, 
  History, 
  Sparkles, 
  Activity, 
  Server, 
  RefreshCw,
  Clock,
  DollarSign,
  TrendingUp,
  Sliders
} from 'lucide-react';
import PipelineSimulator from '../components/simulink/PipelinesSimulator';
import ResourceOptimiser, { OptimizationResult, ResourceConfig } from '../components/simulink/ResourceOptimiser';
import ThroughputChart from '../components/simulink/ThroughputChart';

interface SavedSimulation {
  id: number;
  simulation_name: string;
  created_at: string;
  patient_volume: number;
  bandwidth_mbps: number;
  processing_throughput: number;
  review_capacity: number;
  operating_hours: number;
  total_cost: number;
  cost_per_patient: number;
  throughput_per_day: number;
  backlog_after_year: number;
  optimized_params: any;
  recommendations: string[];
  source: string;
}

// Helper to generate realistic 24h diurnal curve based on configuration
const generateHourlyProfile = (
  patientVolume: number = 100000,
  operatingHours: number = 8,
  throughputDaily: number = 34332,
  annualBacklog: number = 0
) => {
  const dailyPatients = Math.round(patientVolume / 260);
  const hourlyCapacity = Math.round(throughputDaily / Math.max(1, operatingHours));

  return Array.from({ length: 24 }, (_, hour) => {
    // Diurnal factor: peak between 9am and 4pm
    let diurnalFactor = 0.05; // Night baseline
    if (hour >= 8 && hour <= 17) {
      // Bell-shaped curve during clinic hours
      const mid = 12.5;
      const dist = Math.abs(hour - mid);
      diurnalFactor = Math.max(0.2, 1.0 - (dist / 6) * 0.7);
    } else if (hour === 7 || hour === 18 || hour === 19) {
      diurnalFactor = 0.25;
    }

    const hourlyScreeningDemand = Math.round((dailyPatients / operatingHours) * diurnalFactor);
    const capacityThisHour = (hour >= 8 && hour < 8 + operatingHours) ? hourlyCapacity : Math.round(hourlyCapacity * 0.1);
    const hourlyBacklog = Math.max(0, hourlyScreeningDemand - capacityThisHour);

    return {
      hour,
      throughput: Math.min(hourlyScreeningDemand, capacityThisHour),
      capacity: capacityThisHour,
      backlog: annualBacklog > 0 ? hourlyBacklog : 0
    };
  });
};

const SimulinkPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'studio' | 'history'>('studio');
  const [throughputData, setThroughputData] = useState(() => generateHourlyProfile());
  const [savedSimulations, setSavedSimulations] = useState<SavedSimulation[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [latestResult, setLatestResult] = useState<OptimizationResult | null>(null);

  const fetchSimulationHistory = async () => {
    setLoadingHistory(true);
    try {
      const res = await fetch('/api/v1/simulink/simulations');
      if (res.ok) {
        const data = await res.json();
        setSavedSimulations(data);
      }
    } catch (err) {
      console.error('Failed to fetch simulations:', err);
    } finally {
      setLoadingHistory(false);
    }
  };

  useEffect(() => {
    fetchSimulationHistory();
  }, []);

  const handleOptimizationComplete = (result: OptimizationResult, config: ResourceConfig) => {
    setLatestResult(result);
    // Regenerate 24-hour profile based on result
    const newProfile = generateHourlyProfile(
      config.patientVolume,
      config.operatingHours,
      result.throughputPerDay,
      result.backlogAfterYear
    );
    setThroughputData(newProfile);
    // Refresh history
    fetchSimulationHistory();
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto py-2">
      
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-6"
      >
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-950/60 border border-emerald-500/30 text-xs font-mono text-emerald-400 mb-2">
            <Network className="w-3.5 h-3.5" />
            <span>Simulink Telemedicine Queuing Architecture</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            Telemedicine Workflow Simulator
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Mathematical modeling of district-scale diabetic retinopathy screening infrastructure, bandwidth latency, and clinical reviewer allocations.
          </p>
        </div>

        {/* View Switcher Tabs */}
        <div className="flex items-center bg-slate-900 border border-slate-800 p-1 rounded-2xl self-start sm:self-auto">
          <button
            onClick={() => setActiveTab('studio')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-medium transition ${
              activeTab === 'studio'
                ? 'bg-emerald-500 text-slate-950 font-bold shadow-md shadow-emerald-500/20'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            <span>Simulation Studio</span>
          </button>

          <button
            onClick={() => {
              setActiveTab('history');
              fetchSimulationHistory();
            }}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-medium transition ${
              activeTab === 'history'
                ? 'bg-emerald-500 text-slate-950 font-bold shadow-md shadow-emerald-500/20'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <History className="w-3.5 h-3.5" />
            <span>Saved Runs ({savedSimulations.length})</span>
          </button>
        </div>
      </motion.div>

      {/* Main Content Area */}
      {activeTab === 'studio' ? (
        <div className="space-y-8">
          
          {/* 1. Live Interactive Pipeline Simulator */}
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <PipelineSimulator />
          </motion.div>

          {/* 2. 24-Hour Diurnal Throughput Chart */}
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <ThroughputChart 
              data={throughputData} 
              summaryTitle={latestResult ? `Simulated Demand Profile (Run #${latestResult.simulationId || 'Active'})` : undefined}
            />
          </motion.div>

          {/* 3. Resource Optimizer Form & Results */}
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <ResourceOptimiser onOptimizationComplete={handleOptimizationComplete} />
          </motion.div>

          {/* 4. Engineering Context & Methodology Cards */}
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="card p-6 border-slate-800 space-y-4"
          >
            <div className="flex items-center gap-2 text-emerald-400">
              <Sparkles className="w-4 h-4" />
              <h3 className="text-xs font-bold uppercase font-mono tracking-wider">
                Mathematical Modeling & Queuing Theory Foundations
              </h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-xs text-slate-300">
              <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1.5">
                <strong className="text-white block font-sans text-sm">1. M/M/c Queuing Formulation</strong>
                <p className="text-slate-400 leading-relaxed">
                  Models multi-server ophthalmology reviewer nodes as Poisson arrivals with exponential review service distributions to compute queue wait times.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1.5">
                <strong className="text-white block font-sans text-sm">2. Telemedicine Link Sizing</strong>
                <p className="text-slate-400 leading-relaxed">
                  Calibrates raw DICOM / fundus transmission bandwidth to ensure network bottlenecks do not choke GPU inference clusters during peak intake.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1.5">
                <strong className="text-white block font-sans text-sm">3. District Cost Optimization</strong>
                <p className="text-slate-400 leading-relaxed">
                  Balances automated initial screening (\$5/scan) with tiered human secondary grading (\$2/review) to maximize screening reach per budget dollar.
                </p>
              </div>
            </div>
          </motion.div>

        </div>
      ) : (
        /* History of Past Simulations */
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="space-y-6"
        >
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Server className="w-4 h-4 text-emerald-400" />
              <span>Recorded Optimization Runs ({savedSimulations.length})</span>
            </h2>
            <button
              onClick={fetchSimulationHistory}
              className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-xs text-slate-300 transition"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loadingHistory ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>
          </div>

          {loadingHistory ? (
            <div className="py-20 text-center text-slate-400 font-mono text-xs">
              Loading simulation audit records...
            </div>
          ) : savedSimulations.length === 0 ? (
            <div className="p-12 rounded-2xl glass-panel border border-slate-800 text-center space-y-3">
              <History className="w-8 h-8 text-slate-600 mx-auto" />
              <h4 className="text-sm font-bold text-slate-300">No Simulations Recorded Yet</h4>
              <p className="text-xs text-slate-500 max-w-sm mx-auto">
                Run an optimization in the Simulation Studio to save reproducible configuration runs to the database.
              </p>
            </div>
          ) : (
            <div className="rounded-2xl glass-panel border border-slate-800 overflow-hidden shadow-xl">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-900/80 border-b border-slate-800 text-slate-400 uppercase tracking-wider font-semibold font-mono">
                    <tr>
                      <th className="px-5 py-3.5">ID / Name</th>
                      <th className="px-5 py-3.5">Timestamp</th>
                      <th className="px-5 py-3.5">Population</th>
                      <th className="px-5 py-3.5">Bandwidth</th>
                      <th className="px-5 py-3.5">Total Cost</th>
                      <th className="px-5 py-3.5">Cost / Patient</th>
                      <th className="px-5 py-3.5">Backlog</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono">
                    {savedSimulations.map((sim) => (
                      <tr key={sim.id} className="hover:bg-slate-900/50 transition-colors">
                        <td className="px-5 py-3.5 text-slate-200 font-bold">
                          #{sim.id} <span className="font-normal text-slate-400 text-[11px]">{sim.simulation_name}</span>
                        </td>
                        <td className="px-5 py-3.5 text-slate-400 whitespace-nowrap text-[11px]">
                          {sim.created_at ? new Date(sim.created_at).toLocaleString() : 'N/A'}
                        </td>
                        <td className="px-5 py-3.5 text-emerald-400">
                          {sim.patient_volume?.toLocaleString()}
                        </td>
                        <td className="px-5 py-3.5 text-cyan-400">
                          {sim.bandwidth_mbps} Mbps
                        </td>
                        <td className="px-5 py-3.5 text-slate-200">
                          ${sim.total_cost ? (sim.total_cost / 1000).toFixed(1) + 'K' : '0'}
                        </td>
                        <td className="px-5 py-3.5 text-emerald-400 font-bold">
                          ${sim.cost_per_patient?.toFixed(2)}
                        </td>
                        <td className="px-5 py-3.5">
                          <span className={`px-2 py-0.5 rounded-full text-[10px] ${
                            (sim.backlog_after_year || 0) > 0 
                              ? 'bg-rose-950 text-rose-300 border border-rose-500/30' 
                              : 'bg-emerald-950 text-emerald-300 border border-emerald-500/30'
                          }`}>
                            {sim.backlog_after_year > 0 ? `${sim.backlog_after_year.toLocaleString()} backlog` : 'Zero backlog'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </motion.div>
      )}

    </div>
  );
};

export default SimulinkPage;