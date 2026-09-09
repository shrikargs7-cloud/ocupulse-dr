import React from 'react';
import { motion } from 'framer-motion';
import { FaCheckCircle, FaExclamationCircle, FaTimesCircle } from 'react-icons/fa';

interface QualityIndicatorProps {
  grade: 'Good' | 'Borderline' | 'Reject' | null;
  score?: number;
  className?: string;
}

const QualityIndicator: React.FC<QualityIndicatorProps> = ({ 
  grade, 
  score, 
  className = '' 
}) => {
  if (!grade) return null;

  const configs = {
    Good: {
      icon: FaCheckCircle,
      color: 'text-green-600',
      bg: 'bg-green-50',
      border: 'border-green-200',
      label: 'Good Quality',
      description: 'Image quality is sufficient for accurate analysis'
    },
    Borderline: {
      icon: FaExclamationCircle,
      color: 'text-yellow-600',
      bg: 'bg-yellow-50',
      border: 'border-yellow-200',
      label: 'Borderline Quality',
      description: 'Image quality is marginal. Results may be affected.'
    },
    Reject: {
      icon: FaTimesCircle,
      color: 'text-red-600',
      bg: 'bg-red-50',
      border: 'border-red-200',
      label: 'Reject',
      description: 'Image quality is insufficient. Please recapture.'
    }
  };

  const config = configs[grade];
  const Icon = config.icon;

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      className={`p-4 rounded-lg border ${config.bg} ${config.border} ${className}`}
    >
      <div className="flex items-center space-x-3">
        <Icon className={`${config.color} text-2xl`} />
        <div>
          <h4 className={`font-semibold ${config.color}`}>{config.label}</h4>
          <p className="text-sm text-gray-600">{config.description}</p>
          {score !== undefined && (
            <p className="text-xs text-gray-500 mt-1">Quality Score: {(score * 100).toFixed(0)}%</p>
          )}
        </div>
      </div>
    </motion.div>
  );
};

export default QualityIndicator;