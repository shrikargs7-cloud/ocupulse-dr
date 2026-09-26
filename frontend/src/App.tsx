import React from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AnimatePresence } from 'framer-motion';

import Navbar from './components/ui/Navbar';
import Footer from './components/ui/Footer';
import LandingPage from './pages/LandingPage';
import AnalyzePage from './pages/AnalyzePage';
import ResultsPage from './pages/ResultsPage';
import HistoryPage from './pages/HistoryPage';
import HowItWorksPage from './pages/HowItWorksPage';
import AboutPage from './pages/AboutPage';
import AppointmentsPage from './pages/AppointmentsPage';
import DoctorPortalPage from './pages/DoctorPortalPage';
import { AnalysisResponse, NavigationTab } from './types';

const AdminRedirect: React.FC<{ section: string }> = ({ section }) => {
  return (
    <div className="max-w-2xl mx-auto my-16 p-8 bg-slate-900/90 rounded-2xl border border-sky-500/30 text-center shadow-xl">
      <div className="w-14 h-14 mx-auto mb-4 rounded-2xl bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400 text-2xl">
        🛡️
      </div>
      <h2 className="text-2xl font-bold text-white mb-2">{section} Has Moved</h2>
      <p className="text-slate-300 text-sm mb-6 leading-relaxed">
        Engineering benchmarks, Simulink queue simulators, and dataset explorers are reserved for system administrators and have been moved to the standalone <strong>OcuPulse Admin & Systems Console (Port 5174)</strong>.
      </p>
      <a
        href="http://localhost:5174"
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center space-x-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-sky-600 to-teal-500 hover:from-sky-500 hover:to-teal-400 text-white font-semibold text-sm transition-all shadow-lg shadow-sky-500/20"
      >
        <span>Launch Admin Console (Port 5174)</span>
        <span>→</span>
      </a>
    </div>
  );
};

const HistoryRoute: React.FC = () => {
  const navigate = useNavigate();
  return (
    <HistoryPage
      onSelectAnalysis={(result: AnalysisResponse) => {
        const id = result.analysis_id || (result as any).id;
        navigate(`/results/${encodeURIComponent(id)}`, { state: { result } });
      }}
      setActiveTab={(tab: NavigationTab) => {
        if (tab === 'analyze') navigate('/analyze');
        else if (tab === 'history') navigate('/history');
        else if (tab === 'appointments') navigate('/appointments');
        else navigate('/');
      }}
    />
  );
};

function App() {
  return (
    <Router>
      <div className="min-h-screen flex flex-col bg-[#080d1a] text-slate-100 selection:bg-emerald-500/30 selection:text-emerald-200">
        <Navbar />
        <main className="flex-grow py-6 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full">
          <AnimatePresence mode="wait">
            <Routes>
              <Route path="/" element={<LandingPage />} />
              <Route path="/analyze" element={<AnalyzePage />} />
              <Route path="/results/:imageId" element={<ResultsPage />} />
              <Route path="/history" element={<HistoryRoute />} />
              <Route path="/appointments" element={<AppointmentsPage />} />
              <Route path="/doctor" element={<DoctorPortalPage />} />
              <Route path="/how-it-works" element={<HowItWorksPage />} />
              <Route path="/about" element={<AboutPage />} />
              <Route path="/simulink" element={<AdminRedirect section="Simulink Telemedicine Simulator" />} />
              <Route path="/models" element={<AdminRedirect section="AI Models & Benchmark Datasets" />} />
            </Routes>
          </AnimatePresence>
        </main>
        <Footer />
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#0f172a',
              color: '#f8fafc',
              border: '1px solid #334155',
            },
          }}
        />
      </div>
    </Router>
  );
}

export default App;