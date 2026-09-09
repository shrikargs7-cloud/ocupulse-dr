import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell
} from 'recharts';

interface SeverityChartProps {
  data: Array<{
    grade: string;
    probability: number;
    isReferable?: boolean;
  }>;
  className?: string;
}

const SeverityChart: React.FC<SeverityChartProps> = ({ data, className = '' }) => {
  const colors = {
    'No DR': '#22c55e',
    'Mild NPDR': '#eab308',
    'Moderate NPDR': '#f97316',
    'Severe NPDR': '#ef4444',
    'PDR': '#dc2626'
  };

  return (
    <div className={`w-full h-64 ${className}`}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical">
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis type="number" domain={[0, 1]} tickFormatter={(value) => `${(value * 100).toFixed(0)}%`} />
          <YAxis type="category" dataKey="grade" />
          <Tooltip
            formatter={(value: number) => `${(value * 100).toFixed(1)}%`}
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid #e5e7eb',
              borderRadius: '8px'
            }}
          />
          <Legend />
          <Bar dataKey="probability" fill="#0ea5e9" radius={[0, 4, 4, 0]}>
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={colors[entry.grade as keyof typeof colors] || '#0ea5e9'}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default SeverityChart;