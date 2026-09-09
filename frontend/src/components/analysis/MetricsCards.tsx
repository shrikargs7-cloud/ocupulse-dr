import React from 'react';
import { Percent, GitFork, Compass, Ruler, Grid, Maximize2, Network, Activity } from 'lucide-react';
import { QuantitativeMetrics } from '../../types';

interface Props {
  metrics: QuantitativeMetrics;
}

export const MetricsCards: React.FC<Props> = ({ metrics }) => {
  const cards = [
    {
      title: 'Vessel Density',
      value: `${metrics.vessel_density}%`,
      subtitle: 'Percentage of retinal ROI occupied by vessels',
      icon: Percent,
      color: 'from-emerald-500/20 to-teal-500/10',
      border: 'border-emerald-500/30',
      textColor: 'text-emerald-400',
      badge: 'Primary Metric',
      badgeColor: 'bg-emerald-950 text-emerald-300 border-emerald-500/30',
    },
    {
      title: 'Total Vessel Length',
      value: `${metrics.vessel_length_pixels.toLocaleString()} px`,
      subtitle: 'Skeleton-based centerline length',
      icon: Ruler,
      color: 'from-cyan-500/20 to-blue-500/10',
      border: 'border-cyan-500/30',
      textColor: 'text-cyan-400',
      badge: 'Centerline',
      badgeColor: 'bg-cyan-950 text-cyan-300 border-cyan-500/30',
    },
    {
      title: 'Branch Points',
      value: `${metrics.branch_points}`,
      subtitle: 'Vascular bifurcations and junctions',
      icon: GitFork,
      color: 'from-purple-500/20 to-pink-500/10',
      border: 'border-purple-500/30',
      textColor: 'text-purple-400',
      badge: 'Topology',
      badgeColor: 'bg-purple-950 text-purple-300 border-purple-500/30',
    },
    {
      title: 'Vessel Endpoints',
      value: `${metrics.endpoints}`,
      subtitle: 'Terminal vessel tips detected',
      icon: Compass,
      color: 'from-amber-500/20 to-orange-500/10',
      border: 'border-amber-500/30',
      textColor: 'text-amber-400',
      badge: 'Terminals',
      badgeColor: 'bg-amber-950 text-amber-300 border-amber-500/30',
    },
    {
      title: 'Vessel Area',
      value: `${metrics.vessel_area.toLocaleString()} px`,
      subtitle: `ROI Area: ${metrics.roi_pixels.toLocaleString()} px`,
      icon: Grid,
      color: 'from-teal-500/20 to-emerald-500/10',
      border: 'border-teal-500/30',
      textColor: 'text-teal-400',
      badge: 'Vascular Pixels',
      badgeColor: 'bg-teal-950 text-teal-300 border-teal-500/30',
    },
    {
      title: 'Skeleton Density',
      value: `${metrics.skeleton_density}%`,
      subtitle: 'Centerline density across retinal field',
      icon: Maximize2,
      color: 'from-blue-500/20 to-indigo-500/10',
      border: 'border-blue-500/30',
      textColor: 'text-blue-400',
      badge: 'Linear Density',
      badgeColor: 'bg-blue-950 text-blue-300 border-blue-500/30',
    },
    {
      title: 'Mean Caliber Index',
      value: `${metrics.average_vessel_width_px} px`,
      subtitle: 'Estimated average vascular width',
      icon: Activity,
      color: 'from-rose-500/20 to-pink-500/10',
      border: 'border-rose-500/30',
      textColor: 'text-rose-400',
      badge: 'Caliber',
      badgeColor: 'bg-rose-950 text-rose-300 border-rose-500/30',
    },
    {
      title: 'Fractal Complexity',
      value: `${metrics.fractal_dimension}`,
      subtitle: 'Box-counting network complexity',
      icon: Network,
      color: 'from-indigo-500/20 to-sky-500/10',
      border: 'border-indigo-500/30',
      textColor: 'text-indigo-400',
      badge: 'Box-Counting',
      badgeColor: 'bg-indigo-950 text-indigo-300 border-indigo-500/30',
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
          <Activity className="w-4 h-4 text-emerald-400" />
          Quantitative Vascular Biomarkers
        </h3>
        <span className="text-xs text-slate-400 font-mono">
          Strict Computer-Vision Calculation
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {cards.map((card, idx) => {
          const Icon = card.icon;
          return (
            <div
              key={idx}
              className={`p-4 rounded-xl glass-panel ${card.border} glass-card-hover relative overflow-hidden flex flex-col justify-between`}
            >
              {/* Subtle gradient glow */}
              <div className={`absolute top-0 right-0 w-24 h-24 bg-gradient-to-br ${card.color} blur-2xl -z-10 opacity-70`} />

              {/* Header row */}
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-medium text-slate-300 truncate">
                  {card.title}
                </span>
                <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${card.badgeColor}`}>
                  {card.badge}
                </span>
              </div>

              {/* Value */}
              <div className="my-1 flex items-baseline gap-2">
                <span className={`text-2xl sm:text-3xl font-extrabold tracking-tight font-mono ${card.textColor}`}>
                  {card.value}
                </span>
              </div>

              {/* Subtitle / Explanation */}
              <div className="mt-3 pt-2.5 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
                <span className="truncate">{card.subtitle}</span>
                <Icon className={`w-3.5 h-3.5 flex-shrink-0 ml-1.5 ${card.textColor}`} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default MetricsCards;