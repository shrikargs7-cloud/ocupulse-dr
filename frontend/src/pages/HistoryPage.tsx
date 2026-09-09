import React, { useEffect, useState } from 'react';
import {
  History,
  Eye,
  Trash2,
  Calendar,
  ShieldCheck,
  Percent,
  Ruler,
  GitFork,
  ArrowUpRight,
  Search,
  RefreshCw,
  Sparkles,
} from 'lucide-react';
import { HistoryItem, AnalysisResponse, NavigationTab } from '../types';
import { getHistory, getHistoryDetail, deleteHistoryItem } from '../services/api';
import { MedicalDisclaimer } from '../components/ui/MedicalDisclaimer';

interface Props {
  onSelectAnalysis: (result: AnalysisResponse) => void;
  setActiveTab: (tab: NavigationTab) => void;
}

export const HistoryPage: React.FC<Props> = ({ onSelectAnalysis, setActiveTab }) => {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const data = await getHistory();
      setHistory(data);
    } catch (err) {
      console.error('Failed to load history:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleOpenAnalysis = async (analysisId: string) => {
    try {
      const detail = await getHistoryDetail(analysisId);
      onSelectAnalysis(detail);
    } catch (err) {
      console.error('Failed to open analysis:', err);
    }
  };

  const handleDelete = async (e: React.MouseEvent, analysisId: string) => {
    e.stopPropagation();
    if (!window.confirm(`Delete analysis record ${analysisId}?`)) return;

    setDeletingId(analysisId);
    try {
      await deleteHistoryItem(analysisId);
      setHistory((prev) => prev.filter((item) => item.analysis_id !== analysisId));
    } catch (err) {
      console.error('Delete failed:', err);
    } finally {
      setDeletingId(null);
    }
  };

  const filteredHistory = history.filter(
    (item) =>
      item.analysis_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.quality_label.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-950/60 border border-emerald-500/30 text-xs font-mono text-emerald-400 mb-1.5">
            <History className="w-3.5 h-3.5" />
            <span>Session Persistence</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            Analysis Session History
          </h1>
          <p className="text-xs sm:text-sm text-slate-400">
            Stored quantitative retinal analysis records (Supabase PostgreSQL / SQLite database).
          </p>
        </div>

        <button
          onClick={fetchHistory}
          className="self-start sm:self-auto flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs font-medium text-slate-300 transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Search Bar */}
      <div className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
        <input
          type="text"
          placeholder="Search by analysis ID, image filename, or quality status..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full pl-11 pr-4 py-3 rounded-2xl glass-panel border border-slate-800 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500/50"
        />
      </div>

      {/* Table / List */}
      {loading ? (
        <div className="py-20 text-center text-slate-400 font-mono text-xs">
          Loading past analysis sessions...
        </div>
      ) : filteredHistory.length === 0 ? (
        <div className="p-12 rounded-3xl glass-panel border border-slate-800 text-center space-y-4">
          <div className="w-12 h-12 rounded-2xl bg-slate-800/80 border border-slate-700 flex items-center justify-center text-slate-400 mx-auto">
            <History className="w-6 h-6" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-semibold text-slate-200">
              No Analysis Sessions Found
            </h3>
            <p className="text-xs text-slate-400 max-w-sm mx-auto">
              Run your first retinal fundus scan or launch demo mode to populate history records.
            </p>
          </div>
          <button
            onClick={() => setActiveTab('analyze')}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-500 text-slate-950 font-bold text-xs hover:bg-emerald-400 transition shadow-lg"
          >
            <Eye className="w-4 h-4" />
            <span>Analyze Retina Now</span>
          </button>
        </div>
      ) : (
        <div className="rounded-2xl glass-panel border border-slate-800 overflow-hidden shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900/80 border-b border-slate-800 text-slate-400 uppercase tracking-wider font-semibold">
                <tr>
                  <th className="px-5 py-3.5">Analysis ID</th>
                  <th className="px-5 py-3.5">Date & Time</th>
                  <th className="px-5 py-3.5">Quality</th>
                  <th className="px-5 py-3.5">Vessel Density</th>
                  <th className="px-5 py-3.5 hidden md:table-cell">Length</th>
                  <th className="px-5 py-3.5 hidden md:table-cell">Branches</th>
                  <th className="px-5 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredHistory.map((item) => (
                  <tr
                    key={item.analysis_id}
                    onClick={() => handleOpenAnalysis(item.analysis_id)}
                    className="hover:bg-emerald-500/5 cursor-pointer transition-colors group"
                  >
                    <td className="px-5 py-3.5 font-mono font-semibold text-slate-200 group-hover:text-emerald-300">
                      {item.analysis_id}
                    </td>
                    <td className="px-5 py-3.5 text-slate-400 whitespace-nowrap">
                      {new Date(item.timestamp).toLocaleDateString()}{' '}
                      <span className="text-[10px] text-slate-500">
                        {new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </td>
                    <td className="px-5 py-3.5">
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono bg-emerald-950 text-emerald-300 border border-emerald-500/30">
                        {item.quality_label}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 font-mono font-bold text-emerald-400">
                      {item.vessel_density}%
                    </td>
                    <td className="px-5 py-3.5 font-mono text-cyan-400 hidden md:table-cell">
                      {item.vessel_length_pixels.toLocaleString()} px
                    </td>
                    <td className="px-5 py-3.5 font-mono text-purple-400 hidden md:table-cell">
                      {item.branch_points}
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleOpenAnalysis(item.analysis_id)}
                          className="p-1.5 rounded-lg bg-emerald-500/20 text-emerald-300 hover:bg-emerald-500/30 transition"
                          title="Open full results"
                        >
                          <ArrowUpRight className="w-4 h-4" />
                        </button>
                        <button
                          onClick={(e) => handleDelete(e, item.analysis_id)}
                          disabled={deletingId === item.analysis_id}
                          className="p-1.5 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-slate-800 transition"
                          title="Delete session"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Medical Disclaimer */}
      <MedicalDisclaimer />

    </div>
  );
};

export default HistoryPage;
