import React, { useState } from 'react';
import { AdminAuthGate } from './components/AdminAuthGate';
import { AdminNavbar } from './components/AdminNavbar';
import { SystemInfoPage } from './pages/SystemInfoPage';
import SimulinkAdminPage from './pages/SimulinkAdminPage';
import { ModelsPage as ModelsDatasetsAdminPage } from './pages/ModelsDatasetsAdminPage';

export function App() {
  const [activeTab, setActiveTab] = useState<'system' | 'simulink' | 'models'>('system');

  const handleLogout = () => {
    sessionStorage.removeItem('ocupluse_admin_authenticated');
    window.location.reload();
  };

  return (
    <AdminAuthGate>
      <div className="min-h-screen flex flex-col bg-[#070b14] text-slate-100 selection:bg-sky-500/30 selection:text-sky-200">
        <AdminNavbar 
          activeTab={activeTab} 
          setActiveTab={setActiveTab} 
          onLogout={handleLogout} 
        />
        
        <main className="flex-grow py-6 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full">
          {activeTab === 'system' && <SystemInfoPage />}
          {activeTab === 'simulink' && <SimulinkAdminPage />}
          {activeTab === 'models' && <ModelsDatasetsAdminPage />}
        </main>

        <footer className="border-t border-slate-800/80 bg-[#090e1c] py-6 px-4 sm:px-6 text-center text-xs text-slate-500">
          <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-sky-400" />
              <span className="font-semibold text-slate-400">OcuPulse AIDRSS Systems & Admin Console</span>
              <span className="font-mono text-[10px] bg-slate-800 text-sky-400 px-1.5 py-0.5 rounded">PORT 5174</span>
            </div>
            <div>
              Restricted Clinical & Systems Engineering Access • Integrated with MATLAB & Simulink
            </div>
            <a
              href="http://localhost:5173"
              className="text-sky-400 hover:text-sky-300 font-medium hover:underline"
            >
              Switch to User Screening App (:5173) →
            </a>
          </div>
        </footer>
      </div>
    </AdminAuthGate>
  );
}

export default App;
