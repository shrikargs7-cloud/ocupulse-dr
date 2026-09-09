import React from 'react';
import { FaGithub, FaTwitter, FaLinkedin, FaHeart } from 'react-icons/fa';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-[#0b1120] border-t border-slate-800/80 text-slate-400 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* About */}
          <div className="space-y-2">
            <h3 className="text-xs font-mono font-bold text-emerald-400 tracking-wider uppercase">
              OcuPlus AIDRSS
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              AI-Driven Diabetic Retinopathy Screening System with Explainable AI & Deterministic Computer Vision.
            </p>
            <div className="inline-block text-[11px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
              SIH Research Prototype
            </div>
          </div>

          {/* Links */}
          <div>
            <h3 className="text-xs font-mono font-bold text-slate-200 tracking-wider uppercase mb-3">
              Navigation
            </h3>
            <ul className="space-y-2 text-xs">
              <li>
                <a href="/analyze" className="text-slate-400 hover:text-emerald-400 transition-colors">
                  Analyze Image
                </a>
              </li>
              <li>
                <a href="/history" className="text-slate-400 hover:text-emerald-400 transition-colors">
                  Session History
                </a>
              </li>
              <li>
                <a href="/how-it-works" className="text-slate-400 hover:text-emerald-400 transition-colors">
                  How It Works
                </a>
              </li>
              <li>
                <a href="/simulink" className="text-slate-400 hover:text-emerald-400 transition-colors">
                  Simulink Optimization
                </a>
              </li>
            </ul>
          </div>

          {/* Resources */}
          <div>
            <h3 className="text-xs font-mono font-bold text-slate-200 tracking-wider uppercase mb-3">
              Platform
            </h3>
            <ul className="space-y-2 text-xs">
              <li>
                <a href="/docs" target="_blank" rel="noreferrer" className="text-slate-400 hover:text-emerald-400 transition-colors">
                  FastAPI OpenAPI Docs (/docs)
                </a>
              </li>
              <li>
                <a href="/about" className="text-slate-400 hover:text-emerald-400 transition-colors">
                  Clinical Positioning & Ethics
                </a>
              </li>
              <li>
                <span className="text-slate-500">
                  Supabase & SQLite Persistent Store
                </span>
              </li>
            </ul>
          </div>

          {/* Connect */}
          <div>
            <h3 className="text-xs font-mono font-bold text-slate-200 tracking-wider uppercase mb-3">
              Connect
            </h3>
            <div className="flex space-x-3 mb-3">
              <a href="#" className="p-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-emerald-400 border border-slate-800 transition">
                <FaGithub size={16} />
              </a>
              <a href="#" className="p-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-emerald-400 border border-slate-800 transition">
                <FaTwitter size={16} />
              </a>
              <a href="#" className="p-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-emerald-400 border border-slate-800 transition">
                <FaLinkedin size={16} />
              </a>
            </div>
            <p className="text-[11px] text-slate-500 flex items-center">
              Made with <FaHeart className="text-rose-500 mx-1" /> for Retinal Healthcare
            </p>
          </div>
        </div>

        <div className="mt-8 pt-4 border-t border-slate-800/80 flex flex-col sm:flex-row items-center justify-between gap-2 text-[11px] text-slate-500">
          <p>© 2026 OcuPlus AIDRSS. All rights reserved.</p>
          <p className="text-slate-500 text-center sm:text-right">
            Clinical research prototype. Not for clinical use without human ophthalmologist validation.
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;