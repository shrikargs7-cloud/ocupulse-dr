import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { FaUpload, FaFileImage, FaTimes } from 'react-icons/fa';
import { motion, AnimatePresence } from 'framer-motion';
import toast from 'react-hot-toast';

interface ImageUploaderProps {
  onUpload: (file: File) => void;
  isUploading?: boolean;
  maxSize?: number;
  acceptedTypes?: string[];
}

const ImageUploader: React.FC<ImageUploaderProps> = ({
  onUpload,
  isUploading = false,
  maxSize = 50 * 1024 * 1024, // 50MB
  acceptedTypes = ['image/jpeg', 'image/png', 'image/tiff', 'image/bmp']
}) => {
  const [preview, setPreview] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    // Validate file size
    if (file.size > maxSize) {
      toast.error(`File too large. Max size: ${maxSize / (1024 * 1024)}MB`);
      return;
    }

    setFile(file);
    
    // Create preview
    const reader = new FileReader();
    reader.onload = () => {
      setPreview(reader.result as string);
    };
    reader.readAsDataURL(file);
    
    onUpload(file);
    toast.success('Image uploaded successfully!');
  }, [maxSize, onUpload]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: acceptedTypes.reduce((acc, type) => ({ ...acc, [type]: [] }), {}),
    maxFiles: 1,
    disabled: isUploading,
  });

  const clearImage = () => {
    setPreview(null);
    setFile(null);
  };

  return (
    <div className="w-full">
      <AnimatePresence mode="wait">
        {!preview ? (
          <motion.div
            key="dropzone"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all duration-200
                ${isDragActive 
                  ? 'border-emerald-400 bg-emerald-500/10' 
                  : 'border-slate-700 hover:border-emerald-500/50 hover:bg-slate-900/60 bg-slate-950/40'
                }
                ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}
              `}
            >
              <input {...getInputProps()} />
              <div className="flex flex-col items-center space-y-4">
                <div className="p-4 bg-emerald-500/20 border border-emerald-500/30 rounded-2xl text-emerald-400 shadow-lg shadow-emerald-500/10">
                  <FaUpload className="text-3xl" />
                </div>
                <div>
                  <p className="text-base font-semibold text-white">
                    {isDragActive ? 'Drop fundus image here' : 'Upload Retinal Fundus Photograph'}
                  </p>
                  <p className="text-xs text-slate-400 mt-1">
                    Drag & drop or click anywhere to select from your device
                  </p>
                </div>
                <div className="text-[11px] font-mono text-slate-500 flex gap-3">
                  <span>JPG, PNG, TIFF, BMP</span>
                  <span>•</span>
                  <span>Max {maxSize / (1024 * 1024)}MB</span>
                </div>
              </div>
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="preview"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="relative"
          >
            <div className="relative rounded-2xl overflow-hidden border border-slate-800 bg-slate-950/80 p-2">
              <img 
                src={preview} 
                alt="Fundus preview" 
                className="w-full max-h-96 object-contain rounded-xl bg-black"
              />
              <button
                onClick={clearImage}
                className="absolute top-4 right-4 p-2.5 bg-rose-600 hover:bg-rose-500 text-white rounded-xl shadow-lg transition-colors duration-200"
                disabled={isUploading}
                title="Remove image"
              >
                <FaTimes />
              </button>
              {file && (
                <div className="absolute bottom-4 left-4 bg-slate-900/90 border border-slate-700 text-slate-200 px-3 py-1.5 rounded-lg text-xs font-mono">
                  {file.name} ({(file.size / 1024).toFixed(0)} KB)
                </div>
              )}
              {isUploading && (
                <div className="absolute inset-0 bg-slate-950/70 backdrop-blur-sm flex items-center justify-center">
                  <div className="bg-slate-900 border border-slate-700 rounded-2xl p-5 flex items-center space-x-3 shadow-2xl">
                    <div className="animate-spin rounded-full h-6 w-6 border-2 border-emerald-500 border-t-transparent"></div>
                    <span className="text-slate-200 font-medium text-sm">Processing Retinal Geometry...</span>
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ImageUploader;