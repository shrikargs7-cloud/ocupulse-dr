import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  FaHome, 
  FaMicroscope, 
  FaHistory, 
  FaInfoCircle, 
  FaBars,
  FaTimes,
  FaEye,
  FaDatabase,
  FaCalendarCheck,
  FaShieldAlt,
  FaUserMd
} from 'react-icons/fa';

export const Navbar: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [urgentApptsCount, setUrgentApptsCount] = useState<number>(0);
  const [dbStatus, setDbStatus] = useState<{ connected: boolean; label: string }>({
    connected: false,
    label: 'Checking DB...'
  });
  const location = useLocation();

  useEffect(() => {
    const fetchDbStatus = async () => {
      try {
        const res = await fetch('/api/health');
        if (res.ok) {
          const data = await res.json();
          const db = data.database;
          if (db?.status === 'connected') {
            const isSupabase = db.is_supabase || db.dialect === 'postgresql';
            setDbStatus({
              connected: true,
              label: isSupabase ? 'Supabase' : 'SQLite'
            });
          } else {
            setDbStatus({ connected: false, label: 'DB Offline' });
          }
        } else {
          setDbStatus({ connected: false, label: 'DB Offline' });
        }
      } catch {
        setDbStatus({ connected: false, label: 'DB Offline' });
      }
    };

    const fetchUrgentCount = async () => {
      try {
        const res = await fetch('/api/appointments?priority=URGENT&status=CONFIRMED');
        if (res.ok) {
          const appts = await res.json();
          setUrgentApptsCount(Array.isArray(appts) ? appts.length : 0);
        }
      } catch {
        // silent
      }
    };

    fetchDbStatus();
    fetchUrgentCount();
    const interval = setInterval(() => {
      fetchDbStatus();
      fetchUrgentCount();
    }, 15000);
    return () => clearInterval(interval);
  }, []);

  const navItems = [
    { path: '/', label: 'Home', icon: FaHome },
    { path: '/analyze', label: 'Analyze', icon: FaMicroscope },
    { path: '/history', label: 'History', icon: FaHistory },
    { path: '/appointments', label: 'Appointments', icon: FaCalendarCheck, badge: urgentApptsCount },
    { path: '/doctor', label: 'Doctor Portal', icon: FaUserMd, badge: urgentApptsCount },
    { path: '/how-it-works', label: 'How It Works', icon: FaInfoCircle },
    { path: '/about', label: 'About', icon: FaInfoCircle },
  ];


  const isActive = (path: string) => location.pathname === path;

  return (
    <nav className="bg-[#0b1120]/95 backdrop-blur-md border-b border-slate-800/80 sticky top-0 z-50 text-slate-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          {/* Logo */}
          <div className="flex items-center space-x-3">
            <Link to="/" className="flex items-center space-x-2.5 group">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center shadow-lg shadow-emerald-500/20 group-hover:scale-105 transition-transform">
                <FaEye className="text-slate-950 text-xl" />
              </div>
              <div className="flex flex-col">
                <div className="flex items-center space-x-1.5">
                  <span className="text-xl font-bold tracking-tight text-white group-hover:text-emerald-300 transition-colors">OcuPlus</span>
                  <span className="text-[10px] font-mono font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-1.5 py-0.5 rounded">
                    AIDRSS
                  </span>
                </div>
                <span className="text-[10px] text-slate-400 -mt-1 hidden sm:block">Retinal Analysis System</span>
              </div>
            </Link>

            {/* Live DB indicator badge */}
            <div className={`hidden lg:inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-mono border ${
              dbStatus.connected 
                ? 'bg-emerald-950/60 border-emerald-500/30 text-emerald-400' 
                : dbStatus.label.includes('Checking')
                ? 'bg-amber-950/40 border-amber-500/30 text-amber-300'
                : 'bg-rose-950/60 border-rose-500/30 text-rose-400'
            }`}>
              <span className={`w-2 h-2 rounded-full ${
                dbStatus.connected 
                  ? 'bg-emerald-400 animate-pulse' 
                  : dbStatus.label.includes('Checking')
                  ? 'bg-amber-400 animate-pulse'
                  : 'bg-rose-500'
              }`} />
              <FaDatabase className="text-[10px] opacity-70" />
              <span>{dbStatus.label}</span>
            </div>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-1.5">
            {navItems.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.path);
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`px-3 py-2 rounded-xl text-xs sm:text-sm font-medium transition-all duration-200 flex items-center space-x-1.5 ${
                    active
                      ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 shadow-sm'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/60 border border-transparent'
                  }`}
                >
                  <Icon className={`text-sm ${active ? 'text-emerald-400' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                  {Boolean(item.badge && item.badge > 0) && (
                    <span className="px-1.5 py-0.2 rounded-full text-[10px] font-mono font-bold bg-rose-600 text-white animate-pulse">
                      {item.badge}
                    </span>
                  )}
                </Link>
              );
            })}

            {/* Link to Standalone Admin Website (Port 5174) */}
            <div className="pl-2 border-l border-slate-800 ml-1">
              <a
                href="http://localhost:5174"
                target="_blank"
                rel="noopener noreferrer"
                className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-900/80 hover:bg-sky-950/60 text-sky-400 hover:text-sky-300 border border-sky-500/30 hover:border-sky-500/60 transition-all flex items-center space-x-1.5 shadow-sm group"
                title="Open Admin & Systems Console (Simulink, Datasets, System Telemetry)"
              >
                <FaShieldAlt className="text-xs text-sky-400 group-hover:scale-110 transition-transform" />
                <span>Admin Console</span>
                <span className="text-[10px] font-mono bg-sky-500/20 text-sky-300 px-1.5 py-0.2 rounded border border-sky-500/40">5174</span>
              </a>
            </div>
          </div>

          {/* Mobile menu button */}
          <div className="flex items-center md:hidden space-x-2">
            <div className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-mono border ${
              dbStatus.connected 
                ? 'bg-emerald-950/60 border-emerald-500/30 text-emerald-400' 
                : dbStatus.label.includes('Checking')
                ? 'bg-amber-950/40 border-amber-500/30 text-amber-300'
                : 'bg-rose-950/60 border-rose-500/30 text-rose-400'
            }`}>
              <span className={`w-1.5 h-1.5 rounded-full ${
                dbStatus.connected 
                  ? 'bg-emerald-400' 
                  : dbStatus.label.includes('Checking')
                  ? 'bg-amber-400 animate-pulse'
                  : 'bg-rose-500'
              }`} />
              <span>{dbStatus.label}</span>
            </div>

            <button
              onClick={() => setIsOpen(!isOpen)}
              className="p-2 rounded-xl text-slate-300 hover:text-white hover:bg-slate-800 focus:outline-none border border-slate-700"
            >
              {isOpen ? <FaTimes size={20} /> : <FaBars size={20} />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Navigation */}
      <motion.div
        initial={false}
        animate={isOpen ? { height: 'auto', opacity: 1 } : { height: 0, opacity: 0 }}
        transition={{ duration: 0.2 }}
        className="md:hidden overflow-hidden bg-[#0b1120] border-t border-slate-800"
      >
        <div className="px-4 pt-2 pb-4 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.path);
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setIsOpen(false)}
                className={`flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium ${
                  active
                    ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
                    : 'text-slate-300 hover:bg-slate-800/80 hover:text-white'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <Icon className={active ? 'text-emerald-400' : 'text-slate-400'} />
                  <span>{item.label}</span>
                </div>
                {Boolean(item.badge && item.badge > 0) && (
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-rose-600 text-white animate-pulse">
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}

          <div className="pt-2 border-t border-slate-800/80">
            <a
              href="http://localhost:5174"
              target="_blank"
              rel="noopener noreferrer"
              onClick={() => setIsOpen(false)}
              className="flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-semibold bg-sky-950/40 text-sky-300 border border-sky-500/30 hover:bg-sky-900/50"
            >
              <div className="flex items-center space-x-3">
                <FaShieldAlt className="text-sky-400" />
                <span>Admin & Systems Console</span>
              </div>
              <span className="text-[10px] font-mono bg-sky-500/20 text-sky-200 px-1.5 py-0.5 rounded border border-sky-500/40">Port 5174</span>
            </a>
          </div>
        </div>
      </motion.div>
    </nav>
  );
};

export default Navbar;