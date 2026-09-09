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
import SimulinkPage from './pages/SimulinkPage';
import ModelsPage from './pages/ModelsPage';
import AppointmentsPage from './pages/AppointmentsPage';
import { AnalysisResponse, NavigationTab } from './types';

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
        else if (tab === 'simulink') navigate('/simulink');
        else if (tab === 'models') navigate('/models');
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
              <Route path="/how-it-works" element={<HowItWorksPage />} />
              <Route path="/about" element={<AboutPage />} />
              <Route path="/simulink" element={<SimulinkPage />} />
              <Route path="/models" element={<ModelsPage />} />
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