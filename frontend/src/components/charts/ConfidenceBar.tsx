import React from 'react';
import { motion } from 'framer-motion';

interface ConfidenceBarProps {
  confidence: number;
  label?: string;
  className?: string;
}

const ConfidenceBar: React.FC<ConfidenceBarProps> = ({
  confidence,
  label = 'Confidence',
  className = ''
}) => {
  const percentage = confidence * 100;
  const color = percentage >= 80 ? 'green' : percentage >= 60 ? 'yellow' : 'red';

  const getColorClasses = (color: string) => {
    switch (color) {
      case 'green':
        return 'bg-green-500';
      case 'yellow':
        return 'bg-yellow-500';
      case 'red':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  return (
    <div className={`${className}`}>
      <div className="flex justify-between items-center mb-1">
        <span className="text-sm font-medium text-gray-700">{label}</span>
        <span className="text-sm font-semibold text-gray-900">{percentage.toFixed(1)}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2.5 overflow-hidden">
        <motion.div
          className={`h-2.5 rounded-full ${getColorClasses(color)}`}
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 1, ease: 'easeOut' }}
        />
      </div>
      <div className="flex justify-between mt-1 text-xs text-gray-500">
        <span>Low</span>
        <span>Medium</span>
        <span>High</span>
      </div>
    </div>
  );
};

export default ConfidenceBar;