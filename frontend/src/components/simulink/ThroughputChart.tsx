import React from 'react';
import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  ComposedChart,
  Line,
  Bar
} from 'recharts';

interface ThroughputChartProps {
  data: Array<{
    hour: number;
    throughput: number;
    capacity: number;
    backlog?: number;
  }>;
  className?: string;
  summaryTitle?: string;
}

export const ThroughputChart: React.FC<ThroughputChartProps> = ({ 
  data, 
  className = '',
  summaryTitle = '24-Hour Telemedicine Network Load Profile'
}) => {
  // Calculate summary stats safely
  const maxThroughput = data.length > 0 ? Math.max(...data.map(d => d.throughput)) : 0;
  const avgThroughput = data.length > 0 ? Math.round(data.reduce((sum, d) => sum + d.throughput, 0) / data.length) : 0;
  const totalThroughput = data.length > 0 ? data.reduce((sum, d) => sum + d.throughput, 0) : 0;
  const totalCapacity = data.length > 0 ? data.reduce((sum, d) => sum + d.capacity, 0) : 0;
  const utilization = totalCapacity > 0 ? (totalThroughput / totalCapacity) * 100 : 0;
  const totalBacklog = data.length > 0 ? data.reduce((sum, d) => sum + (d.backlog || 0), 0) : 0;

  return (
    <div className={`card p-6 ${className}`}>
      <div className="flex flex-wrap justify-between items-center mb-4 border-b border-slate-800 pb-3 gap-2">
        <div>
          <h3 className="text-base font-bold text-white">{summaryTitle}</h3>
          <p className="text-xs text-slate-400">Hourly throughput vs. system capacity threshold</p>
        </div>
        <div className="flex items-center space-x-4 text-xs font-mono">
          <div className="flex items-center space-x-1.5">
            <div className="w-2.5 h-2.5 bg-cyan-400 rounded-full" />
            <span className="text-slate-300">Throughput</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <div className="w-2.5 h-2.5 bg-emerald-400 rounded-full" />
            <span className="text-slate-300">Capacity</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <div className="w-2.5 h-2.5 bg-rose-400 rounded-full" />
            <span className="text-slate-300">Queued Backlog</span>
          </div>
        </div>
      </div>

      <div className="w-full h-72">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 10, right: 10, left: -15, bottom: 0 }}>
            <defs>
              <linearGradient id="throughputGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis 
              dataKey="hour" 
              stroke="#64748b"
              tick={{ fill: '#94a3b8', fontSize: 11 }}
              tickFormatter={(hour) => `${hour}:00`}
            />
            <YAxis 
              yAxisId="left"
              stroke="#64748b"
              tick={{ fill: '#94a3b8', fontSize: 11 }}
            />
            <YAxis 
              yAxisId="right"
              orientation="right"
              stroke="#64748b"
              tick={{ fill: '#94a3b8', fontSize: 11 }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#0b1120',
                borderColor: '#334155',
                borderRadius: '0.75rem',
                color: '#f8fafc',
                boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.5)'
              }}
              labelFormatter={(hour) => `Hour ${hour}:00`}
              formatter={(value: number, name: string) => [value.toLocaleString(), name]}
            />
            <Legend 
              wrapperStyle={{ paddingTop: '10px', fontSize: '11px' }}
            />
            <Area
              yAxisId="left"
              type="monotone"
              dataKey="throughput"
              fill="url(#throughputGrad)"
              stroke="#06b6d4"
              strokeWidth={2}
              name="Processed Images / Hr"
            />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="capacity"
              stroke="#10b981"
              strokeWidth={2}
              strokeDasharray="4 4"
              dot={false}
              name="System Capacity / Hr"
            />
            <Bar
              yAxisId="right"
              dataKey="backlog"
              fill="#f43f5e"
              opacity={0.7}
              radius={[4, 4, 0, 0]}
              name="Transmission Backlog"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4 pt-4 border-t border-slate-800">
        <div>
          <p className="text-xs text-slate-400 font-mono">Peak Hourly Load</p>
          <p className="text-lg font-bold text-white font-mono mt-0.5">
            {maxThroughput.toLocaleString()}/hr
          </p>
        </div>
        <div>
          <p className="text-xs text-slate-400 font-mono">Average Hourly Rate</p>
          <p className="text-lg font-bold text-white font-mono mt-0.5">
            {avgThroughput.toLocaleString()}/hr
          </p>
        </div>
        <div>
          <p className="text-xs text-slate-400 font-mono">System Utilization</p>
          <p className="text-lg font-bold text-cyan-400 font-mono mt-0.5">
            {utilization.toFixed(1)}%
          </p>
        </div>
        <div>
          <p className="text-xs text-slate-400 font-mono">Queued Backlog Peak</p>
          <p className={`text-lg font-bold font-mono mt-0.5 ${
            totalBacklog > 0 ? 'text-rose-400' : 'text-emerald-400'
          }`}>
            {totalBacklog > 0 ? totalBacklog.toLocaleString() : 'Optimal (0)'}
          </p>
        </div>
      </div>
    </div>
  );
};

export default ThroughputChart;