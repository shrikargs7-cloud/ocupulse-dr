import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { FaEye, FaEyeSlash } from 'react-icons/fa';

interface HeatmapViewerProps {
  originalImage: string;
  heatmap: string;
  overlayImage?: string;
  className?: string;
}

const HeatmapViewer: React.FC<HeatmapViewerProps> = ({
  originalImage,
  heatmap,
  overlayImage,
  className = ''
}) => {
  const [viewMode, setViewMode] = useState<'original' | 'heatmap' | 'overlay'>('overlay');

  const getImage = () => {
    switch (viewMode) {
      case 'original':
        return originalImage;
      case 'heatmap':
        return heatmap;
      case 'overlay':
        return overlayImage || originalImage;
      default:
        return originalImage;
    }
  };

  return (
    <div className={`${className}`}>
      <div className="relative rounded-xl overflow-hidden bg-gray-900">
        <img
          src={getImage()}
          alt="Fundus with heatmap"
          className="w-full max-h-96 object-contain"
        />
        
        {/* Controls */}
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-2 bg-black/70 backdrop-blur-sm p-1 rounded-lg">
          {['original', 'heatmap', 'overlay'].map((mode) => (
            <button
              key={mode}
              onClick={() => setViewMode(mode as any)}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors duration-200
                ${viewMode === mode 
                  ? 'bg-primary-500 text-white' 
                  : 'text-gray-300 hover:bg-white/10'
                }
              `}
            >
              {mode.charAt(0).toUpperCase() + mode.slice(1)}
            </button>
          ))}
        </div>

        <div className="absolute top-4 right-4 bg-black/50 text-white px-3 py-1 rounded-lg text-xs">
          Grad-CAM Attribution
        </div>
      </div>
    </div>
  );
};

export default HeatmapViewer;