import React, { useState, useRef, useCallback, useEffect } from 'react';
import { Sliders, Eye } from 'lucide-react';

interface Props {
  beforeImage: string;
  afterImage: string;
  beforeLabel?: string;
  afterLabel?: string;
}

export const ImageSlider: React.FC<Props> = ({
  beforeImage,
  afterImage,
  beforeLabel = 'Original Fundus',
  afterLabel = 'Vessel Detection Overlay',
}) => {
  const [sliderPosition, setSliderPosition] = useState(50);
  const [isDragging, setIsDragging] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const handleMove = useCallback((clientX: number) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = Math.max(0, Math.min(clientX - rect.left, rect.width));
    const percent = Math.max(0, Math.min(100, (x / rect.width) * 100));
    setSliderPosition(percent);
  }, []);

  const handleTouchMove = useCallback((e: TouchEvent) => {
    if (!isDragging) return;
    handleMove(e.touches[0].clientX);
  }, [isDragging, handleMove]);

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isDragging) return;
    handleMove(e.clientX);
  }, [isDragging, handleMove]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  useEffect(() => {
    if (isDragging) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
      window.addEventListener('touchmove', handleTouchMove);
      window.addEventListener('touchend', handleMouseUp);
    }
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
      window.removeEventListener('touchmove', handleTouchMove);
      window.removeEventListener('touchend', handleMouseUp);
    };
  }, [isDragging, handleMouseMove, handleMouseUp, handleTouchMove]);

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm font-semibold text-slate-200">
          <Sliders className="w-4 h-4 text-emerald-400" />
          <span>Interactive Split Comparison</span>
        </div>
        <span className="text-xs text-slate-400">
          Drag slider to compare detection accuracy
        </span>
      </div>

      <div
        ref={containerRef}
        onMouseDown={() => setIsDragging(true)}
        onTouchStart={() => setIsDragging(true)}
        className="relative w-full aspect-square sm:aspect-[4/3] max-h-[500px] rounded-2xl overflow-hidden glass-panel border border-slate-700/80 cursor-ew-resize select-none shadow-2xl"
      >
        {/* Background Image (After - Vessel Overlay) */}
        <img
          src={afterImage}
          alt={afterLabel}
          className="absolute inset-0 w-full h-full object-contain bg-black"
        />

        {/* Foreground Image (Before - Original Fundus) clipped */}
        <div
          className="absolute inset-0 overflow-hidden"
          style={{ width: `${sliderPosition}%` }}
        >
          <img
            src={beforeImage}
            alt={beforeLabel}
            className="absolute inset-0 w-full h-full object-contain bg-black max-w-none"
            style={{ width: containerRef.current ? `${containerRef.current.clientWidth}px` : '100%' }}
          />
        </div>

        {/* Divider Bar & Handle */}
        <div
          className="absolute top-0 bottom-0 w-0.5 bg-emerald-400 shadow-[0_0_12px_rgba(16,185,129,0.8)] flex items-center justify-center pointer-events-none"
          style={{ left: `${sliderPosition}%` }}
        >
          <div className="w-8 h-8 rounded-full bg-slate-900 border-2 border-emerald-400 shadow-xl flex items-center justify-center text-emerald-400">
            <Sliders className="w-4 h-4" />
          </div>
        </div>

        {/* Labels on top */}
        <div className="absolute top-3 left-3 px-3 py-1 rounded-lg bg-slate-950/80 backdrop-blur-md border border-slate-800 text-xs font-semibold text-slate-200 pointer-events-none flex items-center gap-1.5">
          <Eye className="w-3 h-3 text-slate-400" />
          {beforeLabel}
        </div>
        <div className="absolute top-3 right-3 px-3 py-1 rounded-lg bg-emerald-950/80 backdrop-blur-md border border-emerald-500/40 text-xs font-semibold text-emerald-300 pointer-events-none flex items-center gap-1.5">
          <Eye className="w-3 h-3 text-emerald-400" />
          {afterLabel}
        </div>
      </div>
    </div>
  );
};

export default ImageSlider;
