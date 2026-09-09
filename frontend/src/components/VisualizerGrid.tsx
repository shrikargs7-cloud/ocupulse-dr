import React, { useState } from 'react';
import { Maximize2, Download, Layers, Eye, Sparkles } from 'lucide-react';
import { AnalysisImages } from '../types';
import { ZoomModal } from './ZoomModal';

interface Props {
  images: AnalysisImages;
}

interface ImageCardData {
  id: string;
  title: string;
  badge: string;
  badgeColor: string;
  src: string;
  description: string;
}

export const VisualizerGrid: React.FC<Props> = ({ images }) => {
  const [activeZoomImage, setActiveZoomImage] = useState<ImageCardData | null>(null);

  const imageCards: ImageCardData[] = [
    {
      id: 'original',
      title: '1. Original Fundus Photograph',
      badge: 'Input Scan',
      badgeColor: 'bg-slate-800 text-slate-300 border-slate-700',
      src: images.original,
      description: 'Raw clinical retinal fundus image before digital preprocessing.',
    },
    {
      id: 'enhanced',
      title: '2. Enhanced Green Channel (CLAHE)',
      badge: 'Preprocessed',
      badgeColor: 'bg-emerald-950 text-emerald-300 border-emerald-500/40',
      src: images.enhanced,
      description: 'Green channel with Contrast Limited Adaptive Histogram Equalization.',
    },
    {
      id: 'roi_mask',
      title: '3. Retinal Field of View (ROI)',
      badge: 'Field Mask',
      badgeColor: 'bg-blue-950 text-blue-300 border-blue-500/40',
      src: images.roi_mask,
      description: 'Circular retinal boundary isolating retina from black camera borders.',
    },
    {
      id: 'vessel_mask',
      title: '4. Binary Vessel Segmentation',
      badge: 'Binary Mask',
      badgeColor: 'bg-teal-950 text-teal-300 border-teal-500/40',
      src: images.vessel_mask,
      description: 'Multi-scale filtered binary mask (255 = vessel, 0 = background).',
    },
    {
      id: 'vessel_overlay',
      title: '5. Vessel Detection Overlay',
      badge: 'Detection Overlay',
      badgeColor: 'bg-cyan-950 text-cyan-300 border-cyan-500/40',
      src: images.vessel_overlay,
      description: 'High-contrast alpha blend of segmented vessels over fundus anatomy.',
    },
    {
      id: 'skeleton',
      title: '6. Vessel Centerline Skeleton',
      badge: 'Topology & Skeletons',
      badgeColor: 'bg-purple-950 text-purple-300 border-purple-500/40',
      src: images.skeleton,
      description: '1-pixel wide centerline skeleton with marked branch and endpoints.',
    },
  ];

  const handleDownload = (e: React.MouseEvent, card: ImageCardData) => {
    e.stopPropagation();
    const link = document.createElement('a');
    link.href = card.src;
    link.download = `ocupulse_${card.id}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-emerald-400" />
          <h3 className="text-base font-semibold text-slate-100">
            Multi-Stage Visualizer Matrix
          </h3>
        </div>
        <span className="text-xs text-slate-400">
          Click any stage to open high-resolution zoom inspector
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {imageCards.map((card) => (
          <div
            key={card.id}
            onClick={() => setActiveZoomImage(card)}
            className="group rounded-2xl glass-panel border border-slate-800 hover:border-emerald-500/40 transition-all duration-300 overflow-hidden cursor-pointer flex flex-col justify-between shadow-lg hover:shadow-emerald-950/30"
          >
            {/* Header info */}
            <div className="p-3.5 border-b border-slate-800/80 bg-slate-900/60 flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-200 truncate group-hover:text-emerald-300 transition-colors">
                {card.title}
              </span>
              <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${card.badgeColor}`}>
                {card.badge}
              </span>
            </div>

            {/* Image Preview Box */}
            <div className="relative aspect-square w-full bg-[#050811] flex items-center justify-center overflow-hidden p-2">
              <img
                src={card.src}
                alt={card.title}
                className="max-h-full max-w-full object-contain rounded-lg group-hover:scale-105 transition-transform duration-300 shadow-md"
              />

              {/* Hover overlay icons */}
              <div className="absolute inset-0 bg-slate-950/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-3 backdrop-blur-[2px]">
                <button
                  onClick={() => setActiveZoomImage(card)}
                  className="p-2.5 rounded-xl bg-emerald-500 text-slate-950 font-bold hover:scale-110 active:scale-95 transition shadow-lg flex items-center gap-1.5 text-xs"
                >
                  <Maximize2 className="w-4 h-4" />
                  <span>Inspect</span>
                </button>
                <button
                  onClick={(e) => handleDownload(e, card)}
                  className="p-2.5 rounded-xl bg-slate-800 text-slate-200 hover:bg-slate-700 hover:scale-110 active:scale-95 transition shadow-lg"
                  title="Download PNG"
                >
                  <Download className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Footer description */}
            <div className="p-3 bg-slate-900/40 border-t border-slate-800/60 flex items-center justify-between text-xs text-slate-400">
              <p className="line-clamp-2 leading-relaxed text-[11px]">
                {card.description}
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* Fullscreen Zoom Inspector Modal */}
      {activeZoomImage && (
        <ZoomModal
          isOpen={!!activeZoomImage}
          onClose={() => setActiveZoomImage(null)}
          imageSrc={activeZoomImage.src}
          title={activeZoomImage.title}
          description={activeZoomImage.description}
        />
      )}
    </div>
  );
};

export default VisualizerGrid;
