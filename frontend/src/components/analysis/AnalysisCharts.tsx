import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';
import { BarChart3, PieChart as PieIcon } from 'lucide-react';
import type { QuantitativeMetrics } from '../../types';

interface Props {
  metrics: QuantitativeMetrics;
}

export const AnalysisCharts: React.FC<Props> = ({ metrics }) => {
  // Area Distribution Data
  const nonVesselPixels = Math.max(0, metrics.roi_pixels - metrics.vessel_area);
  const areaData = [
    { name: 'Vascular Network', value: metrics.vessel_area, color: '#10b981' },
    { name: 'Retinal Background', value: nonVesselPixels, color: '#1e293b' },
  ];

  // Structural Topology Data
  const structuralData = [
    { name: 'Branch Points', count: metrics.branch_points, fill: '#a855f7' },
    { name: 'Endpoints', count: metrics.endpoints, fill: '#f59e0b' },
    { name: 'Branch Index (x10)', count: Math.round(metrics.branching_index * 10), fill: '#06b6d4' },
  ];

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="p-3 bg-slate-900/95 border border-slate-700 rounded-xl shadow-xl text-xs font-mono">
          <p className="font-semibold text-slate-200">{label || payload[0].name}</p>
          <p className="text-emerald-400">
            Value: {payload[0].value.toLocaleString()}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-emerald-400" />
          Vascular Distribution & Topology Analytics
        </h3>
        <span className="text-xs text-slate-400 font-mono">
          Objective Parametric Visualizations
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        
        {/* Chart 1: Retinal Field ROI Coverage Distribution */}
        <div className="p-5 rounded-2xl bg-slate-800/50 border border-slate-700 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-xs font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-2">
              <PieIcon className="w-3.5 h-3.5 text-emerald-400" />
              Retinal Area Occupation
            </h4>
            <span className="text-xs font-mono text-emerald-400 font-bold">
              {metrics.vessel_density.toFixed(1)}%
            </span>
          </div>

          <div className="h-52 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={areaData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={75}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {areaData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} stroke="#0f172a" strokeWidth={2} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
                <Legend
                  verticalAlign="bottom"
                  height={36}
                  formatter={(value) => <span className="text-xs text-slate-300">{value}</span>}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <p className="text-[11px] text-slate-400 text-center mt-1">
            Vessels occupy {metrics.vessel_area.toLocaleString()} of {metrics.roi_pixels.toLocaleString()} retinal ROI pixels
          </p>
        </div>

        {/* Chart 2: Structural Junction & Terminal Distribution */}
        <div className="p-5 rounded-2xl bg-slate-800/50 border border-slate-700 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-xs font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-2">
              <BarChart3 className="w-3.5 h-3.5 text-purple-400" />
              Vascular Branching Topology
            </h4>
            <span className="text-xs font-mono text-purple-400 font-bold">
              {metrics.branch_points} Nodes
            </span>
          </div>

          <div className="h-52 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={structuralData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <XAxis dataKey="name" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                  {structuralData.map((entry, index) => (
                    <Cell key={`cell-bar-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <p className="text-[11px] text-slate-400 text-center mt-1">
            Bifurcation ratio: {metrics.branching_index.toFixed(2)} junctions / 1,000 px centerline
          </p>
        </div>

      </div>
    </div>
  );
};

export default AnalysisCharts;