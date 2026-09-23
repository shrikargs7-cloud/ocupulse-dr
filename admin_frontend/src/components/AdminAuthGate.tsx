import React, { useState } from 'react';
import { ShieldCheck, Lock, ArrowRight, Eye, KeyRound } from 'lucide-react';

interface AdminAuthGateProps {
  children: React.ReactNode;
}

export const AdminAuthGate: React.FC<AdminAuthGateProps> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => {
    return sessionStorage.getItem('ocupluse_admin_authenticated') === 'true';
  });
  const [passcode, setPasscode] = useState('');
  const [error, setError] = useState('');

  const handleLogin = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (passcode === 'admin' || passcode === 'admin2026' || passcode === '1234') {
      sessionStorage.setItem('ocupluse_admin_authenticated', 'true');
      setIsAuthenticated(true);
      setError('');
    } else {
      setError('Invalid Administrator Passcode. (Hint: admin2026)');
    }
  };

  const handleQuickBypass = () => {
    sessionStorage.setItem('ocupluse_admin_authenticated', 'true');
    setIsAuthenticated(true);
  };

  if (isAuthenticated) {
    return <>{children}</>;
  }

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4">
      <div className="max-w-md w-full admin-card p-8 border border-sky-500/30 shadow-2xl relative overflow-hidden">
        {/* Background glow */}
        <div className="absolute -top-24 -right-24 w-48 h-48 bg-sky-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -left-24 w-48 h-48 bg-teal-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="text-center mb-8 relative">
          <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-tr from-sky-600 to-teal-500 flex items-center justify-center shadow-lg shadow-sky-500/25">
            <ShieldCheck className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-2xl font-bold text-white tracking-tight">OcuPulse Systems Console</h2>
          <p className="text-xs text-sky-400 font-mono font-medium mt-1">PORT 5174 • RESTRICTED ACCESS</p>
          <p className="text-slate-400 text-sm mt-2">
            Engineering telemetry, Simulink healthcare models, and benchmark dataset telemetry are restricted to authorized administrators.
          </p>
        </div>

        <form onSubmit={handleLogin} className="space-y-4 relative">
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
              Admin Access Passcode
            </label>
            <div className="relative">
              <KeyRound className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 w-4 h-4" />
              <input
                type="password"
                value={passcode}
                onChange={(e) => {
                  setPasscode(e.target.value);
                  setError('');
                }}
                placeholder="Enter admin passcode..."
                className="w-full pl-10 pr-4 py-2.5 bg-slate-950/80 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 transition-all placeholder:text-slate-600"
                autoFocus
              />
            </div>
            {error && (
              <p className="text-rose-400 text-xs mt-1.5 font-medium flex items-center gap-1">
                <span>⚠️</span> {error}
              </p>
            )}
          </div>

          <button
            type="submit"
            className="w-full btn-admin py-2.5 font-semibold text-sm flex items-center justify-center gap-2"
          >
            <span>Authenticate Session</span>
            <ArrowRight className="w-4 h-4" />
          </button>

          <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-xs">
            <button
              type="button"
              onClick={handleQuickBypass}
              className="text-sky-400 hover:text-sky-300 font-medium hover:underline flex items-center gap-1"
            >
              <span>⚡ One-Click Demo Access</span>
            </button>
            <a
              href="http://localhost:5173"
              className="text-slate-400 hover:text-slate-200 transition-colors"
            >
              ← Back to User App
            </a>
          </div>
        </form>
      </div>
    </div>
  );
};
