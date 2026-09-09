import React, { useState } from 'react';
import { motion } from 'framer-motion';

interface VesselOverlayProps {
  fundusImage: string;
  vesselMask: string;
  skeletonImage?: string;
  className?: string;
}

const VesselOverlay: React.FC<VesselOverlayProps> = ({
  fundusImage,
  vesselMask,
  skeletonImage,
  className = ''
}) => {
  const [opacity, setOpacity] = useState(50);
  const [showSkeleton, setShowSkeleton] = useState(false);

  return (
    <div className={`${className}`}>
      <div className="relative rounded-xl overflow-hidden bg-gray-900">
        <img
          src={fundusImage}
          alt="Fundus image"
          className="w-full max-h-96 object-contain"
        />
        
        {/* Vessel overlay */}
        <img
          src={showSkeleton && skeletonImage ? skeletonImage : vesselMask}
          alt="Vessel overlay"
          className="absolute inset-0 w-full h-full object-contain"
          style={{ opacity: opacity / 100 }}
        />

        {/* Controls */}
        <div className="absolute bottom-4 left-4 right-4 bg-black/70 backdrop-blur-sm p-4 rounded-lg">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center space-x-2">
              <span className="text-white text-sm">Opacity:</span>
              <input
                type="range"
                min="0"
                max="100"
                value={opacity}
                onChange={(e) => setOpacity(parseInt(e.target.value))}
                className="w-32 accent-primary-500"
              />
              <span className="text-white text-sm">{opacity}%</span>
            </div>
            
            <button
              onClick={() => setShowSkeleton(!showSkeleton)}
              className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors
                ${showSkeleton 
                  ? 'bg-primary-500 text-white' 
                  : 'bg-white/20 text-white hover:bg-white/30'
                }
              `}
            >
              {showSkeleton ? 'Skeleton' : 'Mask'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VesselOverlay;