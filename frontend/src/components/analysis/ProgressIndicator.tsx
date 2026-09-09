import React from 'react';
import { motion } from 'framer-motion';
import { FaCheck, FaSpinner } from 'react-icons/fa';

interface ProgressStep {
  id: string;
  label: string;
  status: 'pending' | 'active' | 'completed' | 'error';
}

interface ProgressIndicatorProps {
  steps: ProgressStep[];
  currentStep: number;
  className?: string;
}

const ProgressIndicator: React.FC<ProgressIndicatorProps> = ({
  steps,
  currentStep,
  className = ''
}) => {
  return (
    <div className={`w-full ${className}`}>
      <div className="relative">
        {/* Progress Bar */}
        <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-gray-200 -translate-y-1/2">
          <motion.div
            className="h-full bg-primary-500"
            initial={{ width: '0%' }}
            animate={{ width: `${(currentStep / (steps.length - 1)) * 100}%` }}
            transition={{ duration: 0.5 }}
          />
        </div>

        {/* Steps */}
        <div className="relative flex justify-between">
          {steps.map((step, index) => {
            const isCompleted = step.status === 'completed' || index < currentStep;
            const isActive = step.status === 'active' || index === currentStep;
            const isError = step.status === 'error';

            return (
              <div key={step.id} className="flex flex-col items-center">
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-medium transition-all duration-200
                    ${isCompleted ? 'bg-primary-500 text-white' :
                      isActive ? 'bg-primary-100 text-primary-700 border-2 border-primary-500' :
                      isError ? 'bg-red-100 text-red-700 border-2 border-red-500' :
                      'bg-gray-100 text-gray-400 border-2 border-gray-200'}
                  `}
                >
                  {isCompleted ? (
                    <FaCheck />
                  ) : isActive ? (
                    <FaSpinner className="animate-spin" />
                  ) : isError ? (
                    '!'
                  ) : (
                    index + 1
                  )}
                </div>
                <span className={`text-xs mt-2 text-center ${
                  isCompleted ? 'text-primary-600 font-medium' :
                  isActive ? 'text-primary-600 font-medium' :
                  isError ? 'text-red-600' :
                  'text-gray-400'
                }`}>
                  {step.label}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default ProgressIndicator;