import React, { useState, useEffect } from 'react';
import { 
  Server, 
  Database, 
  Cpu, 
  HardDrive, 
  Activity, 
  RefreshCw, 
  CheckCircle2, 
  AlertTriangle, 
  Clock, 
  ShieldCheck,
  FileCode,
  FileText
} from 'lucide-react';

interface SystemInfo {
  status: string;
  app_name: string;
  version: string;
  uptime_seconds: number;
  uptime_human: string;
  timestamp: string;
  database: {
    dialect: string;
    is_supabase: boolean;
    using_fallback_sqlite: boolean;
    active_storage_path: string;
    table_records: {
      patients: number;
      images: number;
      appointments: number;
      reports: number;
    };
    status: string;
  };
  ml_subsystem: {
    model_name: string;
    weights_file: string;
    weights_found: boolean;
    weights_size_mb: number;
    icdr_classes: number;
    reconciliation_engine: string;
    explainability: string;
  };
  matlab_simulink: {
    matlab_bridge_available: boolean;
    simulink_models_loaded: string[];
    matlab_scripts: string[];
  };
  storage: {
    uploads_directory: string;
    cached_images_count: number;
    total_storage_mb: number;
  };
}

export const SystemInfoPage: React.FC = () => {
  const [data, setData] = useState<SystemInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchSystemInfo = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/admin/system-info');
      if (res.ok) {
        const json = await res.json();
        setData(json);
        setError('');
      } else {
        setError(`Failed to fetch telemetry (HTTP ${res.status})`);
      }
    } catch (err: any) {
      setError(err.message || 'Error connecting to FastAPI backend');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSystemInfo();
    const interval = setInterval(fetchSystemInfo, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-2xl font-bold text-white tracking-tight">System Telemetry & Health Console</h1>
            <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-sky-500/20 text-sky-400 border border-sky-500/30">
              Admin Exclusive
            </span>
          </div>
          <p className="text-slate-400 text-sm mt-1">
            Real-time diagnostics covering database connections, PyTorch model integrity, MATLAB co-simulation, and server load.
          </p>
        </div>

        <button
          onClick={fetchSystemInfo}
          disabled={loading}
          className="inline-flex items-center space-x-2 px-3.5 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-all self-start md:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-sky-400' : ''}`} />
          <span>Refresh Metrics</span>
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-500/30 text-rose-300 text-sm flex items-center space-x-3">
          <AlertTriangle className="w-5 h-5 text-rose-400 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Top 4 KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Backend Server Status */}
        <div className="admin-card p-4 border border-slate-800">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium">FastAPI Backend</span>
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center text-emerald-400">
              <Server className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline space-x-2">
            <span className="text-xl font-bold text-white">Online :8000</span>
            <span className="text-xs text-emerald-400 font-semibold flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" /> Active
            </span>
          </div>
          <div className="mt-1 text-[11px] text-slate-400 font-mono">
            Uptime: {data?.uptime_human || 'Connecting...'}
          </div>
        </div>

        {/* Database Engine */}
        <div className="admin-card p-4 border border-slate-800">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium">Active Database</span>
            <div className="w-8 h-8 rounded-lg bg-sky-500/10 flex items-center justify-center text-sky-400">
              <Database className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline space-x-2">
            <span className="text-xl font-bold text-white uppercase">
              {data?.database.dialect || 'SQLite'}
            </span>
            <span className={`text-[10px] font-mono px-1.5 py-0.2 rounded border ${
              data?.database.is_supabase 
                ? 'bg-emerald-950/60 border-emerald-500/30 text-emerald-300' 
                : 'bg-amber-950/60 border-amber-500/30 text-amber-300'
            }`}>
              {data?.database.is_supabase ? 'Supabase Pooler' : 'Offline Local Fallback'}
            </span>
          </div>
          <div className="mt-1 text-[11px] text-slate-400 truncate">
            {data?.database.table_records.images || 0} analyses recorded
          </div>
        </div>

        {/* PyTorch Classifier */}
        <div className="admin-card p-4 border border-slate-800">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium">Diagnostic AI Model</span>
            <div className="w-8 h-8 rounded-lg bg-purple-500/10 flex items-center justify-center text-purple-400">
              <Cpu className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline space-x-2">
            <span className="text-xl font-bold text-white">EfficientNet-B3</span>
            <span className="text-xs text-purple-300 font-mono">5-Class</span>
          </div>
          <div className="mt-1 text-[11px] text-slate-400">
            {data?.ml_subsystem.weights_size_mb || 41.3} MB checkpoint loaded
          </div>
        </div>

        {/* Storage Volume */}
        <div className="admin-card p-4 border border-slate-800">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium">Scratch & Reports Storage</span>
            <div className="w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center text-amber-400">
              <HardDrive className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline space-x-2">
            <span className="text-xl font-bold text-white">{data?.storage.total_storage_mb || 0} MB</span>
            <span className="text-xs text-slate-400">total cached</span>
          </div>
          <div className="mt-1 text-[11px] text-slate-400 font-mono">
            {data?.storage.cached_images_count || 0} scans in uploads buffer
          </div>
        </div>
      </div>

      {/* Database Detailed Table */}
      <div className="admin-card p-6 border border-slate-800">
        <h2 className="text-lg font-bold text-white flex items-center gap-2 mb-4">
          <Database className="w-5 h-5 text-sky-400" />
          <span>Relational Database Architecture & Records Summary</span>
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800">
            <div className="text-xs text-slate-400">Total Patients</div>
            <div className="text-2xl font-bold text-white mt-1">{data?.database.table_records.patients || 0}</div>
            <div className="text-[11px] text-slate-500 mt-1">Unique screening cases</div>
          </div>
          <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800">
            <div className="text-xs text-slate-400">Retinal Scans Processed</div>
            <div className="text-2xl font-bold text-sky-400 mt-1">{data?.database.table_records.images || 0}</div>
            <div className="text-[11px] text-slate-500 mt-1">Full biomarker vectors</div>
          </div>
          <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800">
            <div className="text-xs text-slate-400">Emergency Appointments</div>
            <div className="text-2xl font-bold text-rose-400 mt-1">{data?.database.table_records.appointments || 0}</div>
            <div className="text-[11px] text-slate-500 mt-1">Auto-booked Grade 2+ cases</div>
          </div>
          <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800">
            <div className="text-xs text-slate-400">PDF Reports Generated</div>
            <div className="text-2xl font-bold text-emerald-400 mt-1">{data?.database.table_records.reports || 0}</div>
            <div className="text-[11px] text-slate-500 mt-1">Clinical screening summaries</div>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 text-xs font-mono text-slate-300 space-y-1.5">
          <div className="flex justify-between border-b border-slate-800/60 pb-1.5">
            <span className="text-slate-500">Database Engine:</span>
            <span className="text-sky-300 font-semibold">{data?.database.dialect?.toUpperCase()}</span>
          </div>
          <div className="flex justify-between border-b border-slate-800/60 pb-1.5">
            <span className="text-slate-500">Supabase Cloud Status:</span>
            <span className={data?.database.is_supabase ? 'text-emerald-400' : 'text-amber-400'}>
              {data?.database.is_supabase ? 'Active (Session Pooler Port 5432)' : 'Paused / Offline (Auto-switched to SQLite)'}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">Active Storage Target:</span>
            <span className="text-slate-300 truncate max-w-md">{data?.database.active_storage_path}</span>
          </div>
        </div>
      </div>

      {/* Model & MATLAB Architecture Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* ML Specifications */}
        <div className="admin-card p-6 border border-slate-800">
          <h2 className="text-lg font-bold text-white flex items-center gap-2 mb-4">
            <Cpu className="w-5 h-5 text-purple-400" />
            <span>Deep Learning Subsystem Specifications</span>
          </h2>
          <div className="space-y-3 text-xs">
            <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex justify-between items-center">
              <span className="text-slate-400">Backbone Architecture</span>
              <span className="text-white font-semibold">EfficientNet-B3 (Transfer Learning)</span>
            </div>
            <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex justify-between items-center">
              <span className="text-slate-400">Weights Checkpoint File</span>
              <span className="text-sky-400 font-mono">dr_classifier_efficientnet_b3.pt</span>
            </div>
            <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex justify-between items-center">
              <span className="text-slate-400">Clinical Prior Reconciler</span>
              <span className="text-emerald-400 font-semibold">Lesion-Gated Gating (Zero False Positive Normal Eyes)</span>
            </div>
            <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex justify-between items-center">
              <span className="text-slate-400">Explainable AI (XAI)</span>
              <span className="text-amber-400 font-semibold">Grad-CAM Convolutional Attention Maps</span>
            </div>
          </div>
        </div>

        {/* MATLAB & Simulink Integration */}
        <div className="admin-card p-6 border border-slate-800">
          <h2 className="text-lg font-bold text-white flex items-center gap-2 mb-4">
            <FileCode className="w-5 h-5 text-orange-400" />
            <span>MATLAB & Simulink Co-Simulation Modules</span>
          </h2>
          <div className="space-y-3 text-xs">
            <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800">
              <div className="text-slate-400 font-medium mb-1.5">Simulink Healthcare Models (.slx)</div>
              <div className="flex flex-wrap gap-1.5">
                {data?.matlab_simulink.simulink_models_loaded.map((slx) => (
                  <span key={slx} className="px-2 py-1 rounded bg-sky-950/60 border border-sky-500/30 text-sky-300 font-mono text-[11px]">
                    {slx}
                  </span>
                ))}
              </div>
            </div>
            <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800">
              <div className="text-slate-400 font-medium mb-1.5">Core MATLAB Mathematical Algorithms (.m)</div>
              <div className="flex flex-wrap gap-1.5">
                {data?.matlab_simulink.matlab_scripts.map((m) => (
                  <span key={m} className="px-2 py-1 rounded bg-slate-800 border border-slate-700 text-slate-300 font-mono text-[11px]">
                    {m}
                  </span>
                ))}
              </div>
            </div>
            <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-slate-400 text-[11px]">
              Hybrid Deployment: Pure MATLAB scripts available in repository; mirrored by production SciPy/OpenCV pipeline for standalone zero-license deployment.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
