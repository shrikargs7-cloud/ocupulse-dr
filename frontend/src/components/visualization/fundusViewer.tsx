import React, { useState } from 'react';
import { FaSearchPlus, FaSearchMinus, FaUndo, FaExpand } from 'react-icons/fa';

interface FundusViewerProps {
  image: string;
  className?: string;
  height?: string;
}

export const FundusViewer: React.FC<FundusViewerProps> = ({
  image,
  className = '',
  height = 'h-96'
}) => {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [scale, setScale] = useState(1);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  const handleZoomIn = () => {
    setScale(prev => Math.min(prev + 0.25, 3));
  };

  const handleZoomOut = () => {
    setScale(prev => Math.max(prev - 0.25, 0.5));
  };

  const handleReset = () => {
    setScale(1);
    setPosition({ x: 0, y: 0 });
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - position.x, y: e.clientY - position.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      setPosition({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  return (
    <div className={`relative ${height} ${className}`}>
      <div 
        className="w-full h-full bg-gray-900 rounded-xl overflow-hidden cursor-grab active:cursor-grabbing relative"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        <img
          src={image}
          alt="Fundus image"
          className="w-full h-full object-contain transition-transform duration-200 select-none"
          style={{
            transform: `scale(${scale}) translate(${position.x / scale}px, ${position.y / scale}px)`,
            transformOrigin: 'center'
          }}
          draggable={false}
        />
        
        {/* Scale indicator */}
        <div className="absolute top-4 right-4 bg-black/50 text-white px-2 py-1 rounded text-xs">
          {Math.round(scale * 100)}%
        </div>
      </div>

      {/* Controls */}
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-2 bg-black/70 backdrop-blur-sm p-2 rounded-lg">
        <button
          onClick={handleZoomIn}
          className="p-2 text-white hover:bg-white/10 rounded-lg transition-colors"
          title="Zoom In"
          aria-label="Zoom In"
        >
          <FaSearchPlus />
        </button>
        <button
          onClick={handleZoomOut}
          className="p-2 text-white hover:bg-white/10 rounded-lg transition-colors"
          title="Zoom Out"
          aria-label="Zoom Out"
        >
          <FaSearchMinus />
        </button>
        <button
          onClick={handleReset}
          className="p-2 text-white hover:bg-white/10 rounded-lg transition-colors"
          title="Reset Zoom"
          aria-label="Reset Zoom"
        >
          <FaUndo />
        </button>
        <button
          onClick={() => setIsFullscreen(!isFullscreen)}
          className="p-2 text-white hover:bg-white/10 rounded-lg transition-colors"
          title="Fullscreen"
          aria-label="Fullscreen"
        >
          <FaExpand />
        </button>
      </div>

      {/* Fullscreen Modal */}
      {isFullscreen && (
        <div
          className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-4"
          onClick={() => setIsFullscreen(false)}
        >
          <div
            className="relative max-w-6xl max-h-[90vh] w-full"
            onClick={(e) => e.stopPropagation()}
          >
            <img
              src={image}
              alt="Fundus fullscreen"
              className="w-full h-full object-contain"
            />
            <button
              onClick={() => setIsFullscreen(false)}
              className="absolute top-4 right-4 p-2 bg-white/10 text-white rounded-full hover:bg-white/20 transition-colors text-2xl"
              aria-label="Close fullscreen"
            >
              ✕
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default FundusViewer;