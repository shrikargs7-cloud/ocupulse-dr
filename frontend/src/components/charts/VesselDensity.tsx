import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';

interface VesselDensityProps {
  data: Array<{
    label: string;
    density: number;
    normal?: number;
  }>;
  className?: string;
}

const VesselDensity: React.FC<VesselDensityProps> = ({ data, className = '' }) => {
  return (
    <div className={`w-full h-64 ${className}`}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="label" />
          <YAxis domain={[0, 30]} label={{ value: 'Density (%)', angle: -90, position: 'insideLeft' }} />
          <Tooltip
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid #e5e7eb',
              borderRadius: '8px'
            }}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="density"
            stroke="#0ea5e9"
            strokeWidth={3}
            name="Vessel Density"
            dot={{ r: 4 }}
          />
          <Line
            type="monotone"
            dataKey="normal"
            stroke="#22c55e"
            strokeWidth={2}
            name="Normal Range"
            dot={false}
            strokeDasharray="5 5"
          />
          <ReferenceLine
            y={15}
            label="High Risk"
            stroke="#ef4444"
            strokeDasharray="3 3"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default VesselDensity;