import React from 'react';
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Line,
  ComposedChart
} from 'recharts';

interface FractalPlotProps {
  data: Array<{
    logScale: number;
    logCount: number;
    fitted?: number;
  }>;
  fractalDimension: number;
  className?: string;
}

const FractalPlot: React.FC<FractalPlotProps> = ({
  data,
  fractalDimension,
  className = ''
}) => {
  return (
    <div className={`${className}`}>
      <div className="bg-gray-50 p-4 rounded-lg mb-4">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="text-sm font-medium text-gray-700">Fractal Dimension</h4>
            <p className="text-2xl font-bold text-primary-600">{fractalDimension.toFixed(3)}</p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-500">Box-Counting Method</p>
            <p className="text-xs text-gray-400">D = lim(ε→0) log(N(ε)) / log(1/ε)</p>
          </div>
        </div>
      </div>

      <div className="w-full h-64">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="logScale"
              label={{ value: 'log(1/ε)', position: 'insideBottom', offset: -5 }}
            />
            <YAxis
              dataKey="logCount"
              label={{ value: 'log(N(ε))', angle: -90, position: 'insideLeft' }}
            />
            <Tooltip
              formatter={(value: number) => value.toFixed(3)}
              contentStyle={{
                backgroundColor: 'white',
                border: '1px solid #e5e7eb',
                borderRadius: '8px'
              }}
            />
            <Legend />
            <Scatter
              name="Observed"
              data={data}
              fill="#0ea5e9"
              shape="circle"
            />
            <Line
              type="monotone"
              dataKey="fitted"
              stroke="#22c55e"
              strokeWidth={2}
              name="Fitted Line"
              dot={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default FractalPlot;