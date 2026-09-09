import React from 'react';
import { motion } from 'framer-motion';

interface Lesion {
  type: 'microaneurysm' | 'exudate' | 'hemorrhage' | 'neovascularization';
  x: number;
  y: number;
  size?: number;
  confidence?: number;
}

interface LesionMarkersProps {
  image: string;
  lesions: Lesion[];
  className?: string;
}

const LesionMarkers: React.FC<LesionMarkersProps> = ({
  image,
  lesions,
  className = ''
}) => {
  const getColor = (type: Lesion['type']) => {
    switch (type) {
      case 'microaneurysm':
        return '#ef4444';
      case 'exudate':
        return '#eab308';
      case 'hemorrhage':
        return '#8b5cf6';
      case 'neovascularization':
        return '#3b82f6';
      default:
        return '#6b7280';
    }
  };

  const getLabel = (type: Lesion['type']) => {
    switch (type) {
      case 'microaneurysm':
        return 'MA';
      case 'exudate':
        return 'Ex';
      case 'hemorrhage':
        return 'Hem';
      case 'neovascularization':
        return 'NV';
      default:
        return '';
    }
  };

  return (
    <div className={`relative rounded-xl overflow-hidden ${className}`}>
      <img
        src={image}
        alt="Fundus with lesion markers"
        className="w-full max-h-96 object-contain bg-gray-900"
      />
      
      {/* Lesion markers */}
      {lesions.map((lesion, index) => (
        <motion.div
          key={index}
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: index * 0.05 }}
          className="absolute cursor-pointer group"
          style={{
            left: `${lesion.x}%`,
            top: `${lesion.y}%`,
            transform: 'translate(-50%, -50%)'
          }}
        >
          <div
            className="w-4 h-4 rounded-full border-2 border-white shadow-lg transition-transform duration-200 group-hover:scale-150"
            style={{
              backgroundColor: getColor(lesion.type),
              borderColor: getColor(lesion.type),
              boxShadow: `0 0 10px ${getColor(lesion.type)}`
            }}
          />
          
          {/* Tooltip */}
          <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none">
            <div className="bg-gray-900 text-white text-xs rounded-lg px-2 py-1 whitespace-nowrap">
              {getLabel(lesion.type)}
              {lesion.confidence && ` (${(lesion.confidence * 100).toFixed(0)}%)`}
            </div>
          </div>
        </motion.div>
      ))}

      {/* Legend */}
      <div className="absolute bottom-4 right-4 bg-black/70 backdrop-blur-sm text-white p-2 rounded-lg text-xs">
        <div className="space-y-1">
          {['microaneurysm', 'exudate', 'hemorrhage', 'neovascularization'].map((type) => (
            <div key={type} className="flex items-center space-x-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: getColor(type as Lesion['type']) }}
              />
              <span className="capitalize">{type.replace('_', ' ')}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default LesionMarkers;