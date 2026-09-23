import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, 
  Activity, 
  Cpu, 
  Database, 
  LogOut, 
  ExternalLink,
  Layers,
  Server
} from 'lucide-react';

interface AdminNavbarProps {
  activeTab: 'system' | 'simulink' | 'models';
  setActiveTab: (tab: 'system' | 'simulink' | 'models') => void;
  onLogout: () => void;
}

export const AdminNavbar: React.FC<AdminNavbarProps> = ({ activeTab, setActiveTab, onLogout }) => {
  const [dbStatus, setDbStatus] = useState<{ connected: boolean; label: string }>({
    connected: false,
    label: 'Checking...'
  });

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const res = await fetch('/api/health');
        if (res.ok) {
          const data = await res.json();
          const db = data.database;
          const isSupabase = db?.is_supabase || db?.dialect === 'postgresql';
          setDbStatus({
            connected: db?.status === 'connected',
            label: isSupabase ? 'Supabase Cloud' : 'SQLite Local'
          });
        } else {
          setDbStatus({ connected: false, label: 'Offline' });
        }
      } catch {
        setDbStatus({ connected: false, label: 'Offline' });
      }
    };

    fetchHealth();
    const interval = setInterval(fetchHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  const navItems = [
    { id: 'system' as const, label: 'System Telemetry', icon: Server },
    { id: 'simulink' as const, label: 'Simulink Simulator', icon: Activity },
    { id: 'models' as const, label: 'Models & Datasets', icon: Cpu },
  ];

  return (
    <nav className="bg-[#0b1329]/95 backdrop-blur-md border-b border-sky-900/40 sticky top-0 z-50 text-slate-100 shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          {/* Brand */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-600 to-teal-500 flex items-center justify-center shadow-lg shadow-sky-500/20">
              <ShieldCheck className="w-5 h-5 text-white" />
            </div>
            <div className="flex flex-col">
              <div className="flex items-center space-x-2">
                <span className="text-lg font-bold tracking-tight text-white">OcuPulse</span>
                <span className="text-[10px] font-mono font-bold bg-sky-500/20 text-sky-400 border border-sky-500/40 px-2 py-0.5 rounded-full uppercase">
                  Admin Console
                </span>
                <span className="text-[10px] font-mono bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded border border-slate-700">
                  :5174
                </span>
              </div>
              <span className="text-[10px] text-slate-400 -mt-0.5">Systems Engineering & Medical AI Dossier</span>
            </div>
          </div>

          {/* Navigation Links */}
          <div className="flex items-center space-x-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const active = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`px-3.5 py-2 rounded-xl text-xs sm:text-sm font-medium transition-all flex items-center space-x-2 ${
                    active
                      ? 'bg-sky-500/20 text-sky-300 border border-sky-500/40 shadow-sm'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/60 border border-transparent'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${active ? 'text-sky-400' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </div>

          {/* Right Actions: DB Pill, Back to User App, Logout */}
          <div className="flex items-center space-x-3">
            {/* Database Telemetry Indicator */}
            <div className={`hidden md:inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-mono border ${
              dbStatus.connected 
                ? 'bg-emerald-950/60 border-emerald-500/30 text-emerald-400' 
                : 'bg-rose-950/60 border-rose-500/30 text-rose-400'
            }`}>
              <span className={`w-2 h-2 rounded-full ${dbStatus.connected ? 'bg-emerald-400' : 'bg-rose-500'}`} />
              <Database className="w-3 h-3 opacity-70" />
              <span>{dbStatus.label}</span>
            </div>

            {/* Link to User Screening Portal */}
            <a
              href="http://localhost:5173"
              target="_blank"
              rel="noopener noreferrer"
              className="hidden sm:inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-medium bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-700 transition-colors shadow-sm"
              title="Open Public Clinical Screening Website on Port 5173"
            >
              <span>User App (:5173)</span>
              <ExternalLink className="w-3 h-3 text-slate-400" />
            </a>

            {/* Logout */}
            <button
              onClick={onLogout}
              className="p-2 text-slate-400 hover:text-rose-400 hover:bg-rose-950/40 border border-slate-800 rounded-xl transition-all"
              title="Lock Admin Console"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};
