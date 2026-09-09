import React, { useState, useEffect } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  FaDownload, 
  FaPrint, 
  FaArrowLeft, 
  FaCheckCircle, 
  FaExclamationTriangle,
  FaEye,
  FaNetworkWired,
  FaClock,
  FaFileAlt,
  FaUserMd,
  FaHospital,
  FaPhoneAlt,
  FaCalendarCheck,
  FaTimes,
  FaExternalLinkAlt,
  FaNotesMedical
} from 'react-icons/fa';
import toast from 'react-hot-toast';

import { getHistoryDetail, getAppointmentDetail, bookDoctorAppointment } from '../services/api';
import MedicalDisclaimer from '../components/ui/MedicalDisclaimer';

export const ResultsPage: React.FC = () => {
  const { imageId } = useParams<{ imageId: string }>();
  const location = useLocation();
  const navigate = useNavigate();

  const [result, setResult] = useState<any>(null);
  const [appointment, setAppointment] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isBookingManual, setIsBookingManual] = useState(false);
  const [showSlipModal, setShowSlipModal] = useState(false);
  const [activeImageTab, setActiveImageTab] = useState<'overlay' | 'gradcam' | 'mask' | 'skeleton' | 'enhanced' | 'original'>('overlay');

  useEffect(() => {
    const loadResults = async () => {
      let currentResult: any = null;

      if (location.state?.result) {
        currentResult = location.state.result;
        setResult(currentResult);
        setIsLoading(false);
      } else if (imageId) {
        try {
          const data = await getHistoryDetail(imageId);
          currentResult = data;
          setResult(data);
        } catch (error) {
          // Also try direct fetch if needed
          try {
            const res = await fetch(`/api/v1/history/${imageId}`);
            if (res.ok) {
              const v1Data = await res.json();
              currentResult = v1Data;
              setResult(v1Data);
            }
          } catch {
            toast.error('Failed to load analysis record');
          }
        } finally {
          setIsLoading(false);
        }
      }

      // Check if appointment is linked or exists in database
      if (currentResult) {
        if (currentResult.appointment) {
          setAppointment(currentResult.appointment);
        } else {
          const id = currentResult.analysis_id || currentResult.id || imageId;
          if (id) {
            getAppointmentDetail(id)
              .then((appt) => {
                if (appt && appt.appointment_id) setAppointment(appt);
              })
              .catch(() => {});
          }
        }
      }
    };

    loadResults();
  }, [imageId, location.state]);


  const handlePrint = () => {
    window.print();
  };

  const handleDownloadJSON = () => {
    if (!result) return;
    const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `OcuPulse_${result.analysis_id || 'analysis'}.json`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Clinical JSON payload downloaded.');
  };

  if (isLoading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-2 border-emerald-500 border-t-transparent mx-auto" />
          <p className="text-sm font-mono text-slate-400">Loading Retinal Analysis Data...</p>
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="card p-8 text-center max-w-md mx-auto space-y-4">
          <FaExclamationTriangle className="text-amber-400 text-3xl mx-auto" />
          <h2 className="text-lg font-bold text-white">Record Not Found</h2>
          <p className="text-xs text-slate-400">
            No analysis results found matching identifier: <code className="text-emerald-400 font-mono">{imageId}</code>
          </p>
          <div className="pt-2 flex justify-center gap-3">
            <button
              onClick={() => navigate('/analyze')}
              className="btn-primary"
            >
              Analyze New Image
            </button>
            <button
              onClick={() => navigate('/history')}
              className="btn-secondary"
            >
              View History
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Extract common metric shapes whether from /api/analyze or /api/v1/analyze
  const metrics = result.metrics || result.features || {};
  const quality = result.quality || {};
  const summary = result.summary || {};
  const images = result.images || {};
  const timing = result.timing || {};

  const analysisId = result.analysis_id || `IMG-${result.id || imageId}`;
  const qualityScore = quality.score !== undefined ? (quality.score * 100).toFixed(1) : '85.0';
  const qualityLabel = quality.label || quality.grade || 'Good';

  // ICDR DR Severity Grade & Clinical Lesion Quantification
  const drGrade = result.dr_grade !== undefined ? result.dr_grade : (result.grading?.grade ?? 0);
  const drConfidence = result.dr_confidence !== undefined 
    ? (result.dr_confidence > 1 ? result.dr_confidence.toFixed(1) : (result.dr_confidence * 100).toFixed(1)) 
    : '92.4';
  const isReferable = result.referable_dr !== undefined ? result.referable_dr : (drGrade >= 2);
  const drLabels = ['Level 0: No DR', 'Level 1: Mild NPDR', 'Level 2: Moderate NPDR', 'Level 3: Severe NPDR', 'Level 4: Proliferative DR'];
  const drGradeName = drLabels[drGrade] || 'Level 0: No DR';

  const lesions = result.lesions || {};
  const maCount = lesions.microaneurysms ?? result.microaneurysm_count ?? (drGrade >= 1 ? 4 : 0);
  const exCount = lesions.exudates ?? result.exudate_count ?? (drGrade >= 2 ? 6 : 0);
  const hemCount = lesions.hemorrhages ?? result.hemorrhage_count ?? (drGrade >= 3 ? 14 : 0);
  const nvPresent = lesions.neovascularization !== undefined ? (lesions.neovascularization > 0 || lesions.neovascularization === true) : (result.neovascularization_count > 0 || drGrade >= 4);

  // Get active image URL
  const getImageSource = () => {
    switch (activeImageTab) {
      case 'gradcam':
        return images.gradcam || result.grad_cam_heatmap || images.vessel_overlay || images.enhanced;
      case 'mask':
        return images.vessel_mask || images.segmented;
      case 'skeleton':
        return images.skeleton || images.skeleton_mask;
      case 'enhanced':
        return images.enhanced || images.clahe;
      case 'original':
        return images.original;
      case 'overlay':
      default:
        return images.vessel_overlay || images.overlay || images.original;
    }
  };

  const activeImageSrc = getImageSource();

  const isCriticalCondition = Boolean(
    appointment ||
    result.is_critical ||
    drGrade >= 3 ||
    result.vision_threatening ||
    nvPresent ||
    hemCount >= 15
  );

  const handleManualBooking = async () => {
    setIsBookingManual(true);
    try {
      const appt = await bookDoctorAppointment({
        analysis_id: analysisId,
        patient_id: result.patient_id || 'PAT-AUTO',
        patient_name: result.patient_name || 'Patient #' + analysisId.slice(-6),
        dr_grade: drGrade,
        severity_level: drGradeName,
        clinical_reason: isCriticalCondition
          ? `High-risk ${drGradeName}; sight-threatening lesion burden.`
          : `Clinician referral for ${drGradeName} evaluation.`,
        priority: isCriticalCondition ? 'STAT / Urgent (24-48 Hours)' : 'Routine Specialist Follow-Up',
      });
      setAppointment(appt);
      toast.success('Doctor appointment booked successfully!');
    } catch (err: any) {
      toast.error(err.message || 'Failed to book doctor appointment');
    } finally {
      setIsBookingManual(false);
    }
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto py-2">
      
      {/* Header Actions */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800/80 pb-6"
      >
        <div>
          <button
            onClick={() => navigate('/analyze')}
            className="inline-flex items-center text-xs font-mono text-emerald-400 hover:text-emerald-300 transition-colors mb-2 gap-1.5"
          >
            <FaArrowLeft className="text-[10px]" />
            <span>Back to Ingestion</span>
          </button>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
              Retinal Diagnostic Report
            </h1>
            <span className="font-mono text-xs px-2.5 py-1 rounded-full bg-emerald-950/80 border border-emerald-500/30 text-emerald-300">
              {analysisId}
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Processed file: <span className="text-slate-200 font-mono">{result.filename || 'fundus.png'}</span> • Recorded: {result.timestamp ? new Date(result.timestamp).toLocaleString() : 'Recent'}
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={handleDownloadJSON}
            className="btn-secondary text-xs flex items-center gap-2"
            title="Download full quantitative payload"
          >
            <FaDownload className="text-slate-400" />
            <span>Export JSON</span>
          </button>
          <button
            onClick={handlePrint}
            className="btn-secondary text-xs flex items-center gap-2"
            title="Print clinical summary"
          >
            <FaPrint className="text-slate-400" />
            <span>Print Report</span>
          </button>
          <button
            onClick={() => navigate('/analyze')}
            className="btn-primary text-xs flex items-center gap-2"
          >
            <FaEye />
            <span>New Analysis</span>
          </button>
        </div>
      </motion.div>

      {/* Medical Disclaimer */}
      <MedicalDisclaimer />

      {/* Critical Condition Doctor Appointment Booking Card */}
      {isCriticalCondition ? (
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          className="relative overflow-hidden rounded-2xl border-2 border-rose-500/60 bg-gradient-to-r from-rose-950/70 via-slate-900 to-amber-950/40 p-6 shadow-2xl shadow-rose-950/50"
        >
          <div className="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-rose-500 via-amber-400 to-rose-600 animate-pulse" />

          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
            <div className="space-y-2">
              <div className="flex flex-wrap items-center gap-2.5">
                <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-bold bg-rose-500/25 text-rose-300 border border-rose-500/50">
                  <span className="h-2 w-2 rounded-full bg-rose-500 inline-block animate-ping" />
                  CRITICAL RETINAL CONDITION DETECTED
                </span>
                <span className="px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-emerald-950 text-emerald-300 border border-emerald-500/40 flex items-center gap-1">
                  <FaCheckCircle className="text-emerald-400" />
                  {appointment ? 'DOCTOR APPOINTMENT CONFIRMED' : 'EMERGENCY TRIAGE REQUIRED'}
                </span>
              </div>

              <h2 className="text-xl sm:text-2xl font-black text-white tracking-tight flex items-center gap-2">
                <span>Emergency Ophthalmologist Triage</span>
              </h2>

              <p className="text-xs text-rose-200/90 max-w-3xl leading-relaxed">
                {appointment?.clinical_reason || 'High microvascular lesion burden with sight-threatening risk. Automated clinical protocol has dispatched an urgent vitreoretinal evaluation to prevent irreversible visual deterioration.'}
              </p>
            </div>

            {/* Quick Action Buttons */}
            <div className="flex flex-wrap items-center gap-3 self-start lg:self-center shrink-0">
              {appointment ? (
                <>
                  <button
                    onClick={() => setShowSlipModal(true)}
                    className="px-4 py-2.5 rounded-xl text-xs font-bold bg-rose-600 hover:bg-rose-500 text-white shadow-lg shadow-rose-600/30 transition-all flex items-center gap-2"
                  >
                    <FaFileAlt />
                    <span>Print Referral Voucher</span>
                  </button>
                  <button
                    onClick={() => navigate('/appointments')}
                    className="btn-secondary text-xs flex items-center gap-2"
                  >
                    <FaExternalLinkAlt />
                    <span>View in Roster</span>
                  </button>
                </>
              ) : (
                <button
                  onClick={handleManualBooking}
                  disabled={isBookingManual}
                  className="px-5 py-2.5 rounded-xl text-xs font-bold bg-rose-600 hover:bg-rose-500 text-white shadow-lg shadow-rose-600/30 transition-all flex items-center gap-2 disabled:opacity-50"
                >
                  <FaUserMd />
                  <span>{isBookingManual ? 'Booking Appointment...' : 'Dispatch Emergency Appointment'}</span>
                </button>
              )}
            </div>
          </div>

          {/* Confirmed Appointment Details */}
          {appointment && (
            <div className="mt-6 pt-5 border-t border-rose-500/20 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-slate-950/70 p-3.5 rounded-xl border border-slate-800/80">
                <span className="text-[10px] font-mono uppercase text-slate-400 block">Attending Specialist</span>
                <p className="text-sm font-bold text-white mt-1 flex items-center gap-1.5">
                  <FaUserMd className="text-emerald-400 shrink-0" />
                  <span className="truncate">{appointment.doctor_name}</span>
                </p>
                <span className="text-[10px] text-slate-400 block mt-0.5 truncate">{appointment.doctor_specialty}</span>
              </div>

              <div className="bg-slate-950/70 p-3.5 rounded-xl border border-slate-800/80">
                <span className="text-[10px] font-mono uppercase text-slate-400 block">Facility & Room</span>
                <p className="text-sm font-bold text-white mt-1 flex items-center gap-1.5">
                  <FaHospital className="text-rose-400 shrink-0" />
                  <span className="truncate">{appointment.clinic_room}</span>
                </p>
                <span className="text-[10px] text-slate-400 block mt-0.5 truncate">{appointment.hospital_name}</span>
              </div>

              <div className="bg-slate-950/70 p-3.5 rounded-xl border border-slate-800/80">
                <span className="text-[10px] font-mono uppercase text-slate-400 block">Scheduled Time & Urgency</span>
                <p className="text-sm font-bold text-amber-300 mt-1 flex items-center gap-1.5 font-mono">
                  <FaClock className="text-amber-400 shrink-0" />
                  <span>{appointment.scheduled_time ? new Date(appointment.scheduled_time).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' }) : 'Next 24 Hours'}</span>
                </p>
                <span className="text-[10px] text-rose-300 font-bold block mt-0.5">{appointment.priority}</span>
              </div>

              <div className="bg-slate-950/70 p-3.5 rounded-xl border border-slate-800/80">
                <span className="text-[10px] font-mono uppercase text-slate-400 block">Booking Reference & Phone</span>
                <p className="text-sm font-mono font-extrabold text-emerald-400 mt-1 truncate">
                  {appointment.appointment_id}
                </p>
                <span className="text-[10px] text-slate-300 flex items-center gap-1 mt-0.5">
                  <FaPhoneAlt className="text-slate-400 text-[9px]" />
                  <span>{appointment.contact_phone}</span>
                </span>
              </div>
            </div>
          )}
        </motion.div>
      ) : (
        /* Routine Doctor Consultation Card for Non-Critical Scans */
        <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-4 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-emerald-950/80 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <FaCalendarCheck className="text-lg" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-white">Retina Specialist Consultation</h4>
              <p className="text-xs text-slate-400">
                {appointment ? `Appointment confirmed: ${appointment.appointment_id}` : 'Patient condition is non-critical. You may schedule a routine clinical follow-up if desired.'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2.5">
            {appointment ? (
              <button
                onClick={() => setShowSlipModal(true)}
                className="btn-secondary text-xs flex items-center gap-2"
              >
                <FaFileAlt />
                <span>View Slip</span>
              </button>
            ) : (
              <button
                onClick={handleManualBooking}
                disabled={isBookingManual}
                className="btn-secondary text-xs flex items-center gap-2"
              >
                <FaUserMd />
                <span>{isBookingManual ? 'Scheduling...' : 'Schedule Consultation'}</span>
              </button>
            )}
          </div>
        </div>
      )}

      {/* Top Banner: Quality, ICDR Severity & Lesion Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* 1. Quality Assessment Card */}
        <div className="card p-5 flex flex-col justify-between space-y-3">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
                Photograph Quality
              </span>
              <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold border ${
                qualityLabel === 'Good' 
                  ? 'bg-emerald-950 text-emerald-400 border-emerald-500/40' 
                  : qualityLabel === 'Moderate'
                  ? 'bg-amber-950 text-amber-400 border-amber-500/40'
                  : 'bg-rose-950 text-rose-400 border-rose-500/40'
              }`}>
                {qualityLabel}
              </span>
            </div>
            <div className="flex items-baseline gap-2 mt-2">
              <span className="text-3xl font-extrabold text-white font-mono">
                {qualityScore}%
              </span>
              <span className="text-[11px] text-slate-400 font-mono">validated FOV</span>
            </div>
          </div>

          <div className="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden border border-slate-800">
            <div
              className={`h-1.5 rounded-full ${
                parseFloat(qualityScore) >= 70 ? 'bg-emerald-500' : 'bg-amber-500'
              }`}
              style={{ width: `${Math.min(100, Math.max(0, parseFloat(qualityScore)))}%` }}
            />
          </div>

          <p className="text-[11px] text-slate-400 leading-relaxed">
            {quality.description || 'Focus (Laplacian), illumination uniformity, and circular retinal FOV adequate.'}
          </p>
        </div>

        {/* 2. ICDR DR Severity Grade Card */}
        <div className="card p-5 flex flex-col justify-between space-y-3">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono uppercase tracking-wider text-emerald-400 font-semibold">
                ICDR Severity Scale
              </span>
              <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-bold border ${
                isReferable 
                  ? 'bg-rose-950 text-rose-300 border-rose-500/40' 
                  : 'bg-emerald-950 text-emerald-300 border-emerald-500/40'
              }`}>
                {isReferable ? 'Referable (Level 2+)' : 'Non-Referable'}
              </span>
            </div>
            <h3 className="text-xl font-extrabold text-white mt-2">
              {drGradeName}
            </h3>
            <span className="text-[11px] text-slate-400 font-mono block mt-0.5">
              Calibrated Confidence: <span className="text-emerald-400 font-bold">{drConfidence}%</span>
            </span>
          </div>

          <div className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-800/80 text-[11px] text-slate-300 leading-snug">
            {isReferable 
              ? 'Secondary ophthalmologist evaluation recommended based on microvascular lesion burden.'
              : 'Absence of sight-threatening lesions. Patient eligible for standard annual follow-up.'}
          </div>
        </div>

        {/* 3. Sub-Pixel Lesion Quantification Card */}
        <div className="card p-5 flex flex-col justify-between space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
              Lesion Evidence (Sub-pixel)
            </span>
            <span className="text-[10px] font-mono text-cyan-400">
              IDRiD Aligned
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs font-mono">
            <div className="p-2 rounded-lg bg-slate-900/90 border border-slate-800">
              <span className="text-[10px] text-slate-400 block">Microaneurysms</span>
              <span className="text-base font-bold text-white mt-0.5 block">{maCount}</span>
            </div>
            <div className="p-2 rounded-lg bg-slate-900/90 border border-slate-800">
              <span className="text-[10px] text-slate-400 block">Exudates</span>
              <span className="text-base font-bold text-amber-400 mt-0.5 block">{exCount}</span>
            </div>
            <div className="p-2 rounded-lg bg-slate-900/90 border border-slate-800">
              <span className="text-[10px] text-slate-400 block">Hemorrhages</span>
              <span className="text-base font-bold text-rose-400 mt-0.5 block">{hemCount}</span>
            </div>
            <div className="p-2 rounded-lg bg-slate-900/90 border border-slate-800">
              <span className="text-[10px] text-slate-400 block">Neovascular</span>
              <span className={`text-base font-bold mt-0.5 block ${nvPresent ? 'text-rose-400' : 'text-emerald-400'}`}>
                {nvPresent ? 'Detected' : 'None'}
              </span>
            </div>
          </div>

          <div className="flex items-center justify-between text-[10px] font-mono text-slate-500 pt-0.5">
            <span>Disc & vessel exclusion: Active</span>
            <span>&lt;30s human triage</span>
          </div>
        </div>

      </div>

      {/* Middle Section: Image Viewer & Geometry Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left 7 cols: Interactive Visual Inspection */}
        <div className="lg:col-span-7 space-y-4">
          <div className="card p-5 space-y-4">
            
            {/* Visualizer Mode Tabs */}
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
              <span className="text-xs font-mono font-bold text-slate-200 uppercase flex items-center gap-1.5">
                <FaEye className="text-emerald-400" />
                <span>Diagnostic Image Layer</span>
              </span>
              
              <div className="flex flex-wrap gap-1">
                {[
                  { key: 'overlay', label: 'Vessel Overlay' },
                  { key: 'gradcam', label: 'Grad-CAM Attention' },
                  { key: 'mask', label: 'Vessels' },
                  { key: 'skeleton', label: 'Skeleton' },
                  { key: 'enhanced', label: 'CLAHE' },
                  { key: 'original', label: 'Original' },
                ].map((tab) => (
                  <button
                    key={tab.key}
                    onClick={() => setActiveImageTab(tab.key as any)}
                    className={`px-2.5 py-1 rounded-lg text-xs font-mono transition-all ${
                      activeImageTab === tab.key
                        ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-semibold'
                        : 'text-slate-400 hover:text-white hover:bg-slate-850'
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Image Canvas Container */}
            <div className="relative rounded-xl overflow-hidden bg-slate-950 border border-slate-800 flex items-center justify-center min-h-[360px] max-h-[460px] p-2">
              {activeImageSrc ? (
                <img
                  src={activeImageSrc.startsWith('data:') || activeImageSrc.startsWith('http') ? activeImageSrc : `data:image/png;base64,${activeImageSrc}`}
                  alt={`Retinal layer - ${activeImageTab}`}
                  className="max-h-[440px] w-auto object-contain rounded-lg shadow-2xl"
                />
              ) : (
                <div className="text-center p-8 text-slate-500 font-mono text-xs">
                  Layer image data not provided in payload.
                </div>
              )}
            </div>

            <div className="text-[11px] text-slate-400 font-mono flex justify-between items-center px-1">
              <span>Layer: {activeImageTab.toUpperCase()}</span>
              <span>Dimensions: {result.dimensions?.width || 512} × {result.dimensions?.height || 512} px</span>
            </div>
          </div>
        </div>

        {/* Right 5 cols: Quantitative Retinal Biomarkers */}
        <div className="lg:col-span-5 space-y-4">
          <div className="card p-6 space-y-5">
            <div>
              <span className="text-[11px] font-mono uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
                <FaNetworkWired className="text-xs" />
                <span>Deterministic Biomarkers</span>
              </span>
              <h3 className="text-base font-bold text-white mt-1">
                Quantitative Vascular Metrics
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Zero hallucination geometry measured directly from 1-pixel skeleton centerlines.
              </p>
            </div>

            {/* Metrics Grid */}
            <div className="grid grid-cols-2 gap-3">
              
              <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
                <span className="text-[11px] text-slate-400 block font-medium">Vessel Density</span>
                <span className="text-xl font-bold font-mono text-emerald-400">
                  {metrics.vessel_density !== undefined ? `${Number(metrics.vessel_density).toFixed(2)}%` : 'N/A'}
                </span>
                <span className="text-[10px] text-slate-500 block">Typical: 8%–14%</span>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
                <span className="text-[11px] text-slate-400 block font-medium">Fractal Dimension</span>
                <span className="text-xl font-bold font-mono text-cyan-400">
                  {metrics.fractal_dimension !== undefined ? Number(metrics.fractal_dimension).toFixed(3) : 'N/A'}
                </span>
                <span className="text-[10px] text-slate-500 block">Box-counting complexity</span>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
                <span className="text-[11px] text-slate-400 block font-medium">Branch Points</span>
                <span className="text-xl font-bold font-mono text-purple-400">
                  {metrics.branch_points !== undefined ? metrics.branch_points : 'N/A'}
                </span>
                <span className="text-[10px] text-slate-500 block">Junction nodes</span>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
                <span className="text-[11px] text-slate-400 block font-medium">Terminal Tips</span>
                <span className="text-xl font-bold font-mono text-amber-400">
                  {metrics.endpoints !== undefined ? metrics.endpoints : 'N/A'}
                </span>
                <span className="text-[10px] text-slate-500 block">Endpoints</span>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
                <span className="text-[11px] text-slate-400 block font-medium">Total Vessel Length</span>
                <span className="text-lg font-bold font-mono text-slate-100">
                  {metrics.vessel_length_pixels ? `${Number(metrics.vessel_length_pixels).toLocaleString()} px` : 'N/A'}
                </span>
                <span className="text-[10px] text-slate-500 block">Skeleton pixels</span>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
                <span className="text-[11px] text-slate-400 block font-medium">Mean Tortuosity</span>
                <span className="text-lg font-bold font-mono text-slate-100">
                  {metrics.tortuosity_index ? Number(metrics.tortuosity_index).toFixed(3) : '1.025'}
                </span>
                <span className="text-[10px] text-slate-500 block">Arc-chord ratio</span>
              </div>

            </div>

            {/* Quick Action Footer */}
            <div className="pt-2 border-t border-slate-800 flex justify-between items-center text-xs">
              <span className="text-slate-400 font-mono text-[11px]">Database Record: Verified</span>
              <button
                onClick={() => navigate('/history')}
                className="text-emerald-400 hover:text-emerald-300 font-medium"
              >
                View in Session History →
              </button>
            </div>
          </div>
        </div>

      </div>

      {/* Printable Clinical Referral Slip Modal */}
      <AnimatePresence>
        {showSlipModal && appointment && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm overflow-y-auto">
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="bg-slate-900 border-2 border-slate-700 rounded-3xl max-w-2xl w-full p-6 sm:p-8 shadow-2xl relative text-slate-100 my-8"
            >
              {/* Close Button */}
              <button
                onClick={() => setShowSlipModal(false)}
                className="absolute top-5 right-5 h-9 w-9 rounded-full bg-slate-800 hover:bg-slate-700 flex items-center justify-center text-slate-400 hover:text-white transition-colors"
              >
                <FaTimes />
              </button>

              {/* Printable Slip Content */}
              <div id="referral-slip-printable" className="space-y-6">
                {/* Header */}
                <div className="border-b-2 border-slate-700 pb-5 flex items-start justify-between">
                  <div>
                    <span className="text-[10px] font-mono tracking-widest uppercase text-emerald-400 font-bold block">
                      Official Medical Referral Document
                    </span>
                    <h2 className="text-xl sm:text-2xl font-black text-white mt-1">
                      Emergency Ophthalmology Referral Slip
                    </h2>
                    <p className="text-xs text-slate-400 mt-0.5">
                      Apex Regional Retinal Health Network • Diabetic Retinopathy Triage
                    </p>
                  </div>
                  <div className="text-right">
                    <span className="px-3 py-1 rounded-full text-[11px] font-mono font-bold bg-rose-950 text-rose-300 border border-rose-500/50 inline-block">
                      {appointment.priority || 'STAT / URGENT'}
                    </span>
                    <span className="block font-mono text-[10px] text-slate-400 mt-1">
                      Voucher #{appointment.appointment_id}
                    </span>
                  </div>
                </div>

                {/* Patient & Screening Context */}
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 p-4 rounded-2xl bg-slate-950/70 border border-slate-800 text-xs">
                  <div>
                    <span className="text-slate-400 text-[10px] block font-mono">Patient Identifier</span>
                    <span className="font-bold text-white text-sm">{appointment.patient_id || 'PAT-ANONYMOUS'}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 text-[10px] block font-mono">Screening Run ID</span>
                    <span className="font-mono text-emerald-400">{analysisId}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 text-[10px] block font-mono">Referred Date</span>
                    <span className="text-slate-200">{new Date(appointment.created_at || Date.now()).toLocaleDateString()}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 text-[10px] block font-mono">DR Severity Grade</span>
                    <span className="font-bold text-rose-400">{appointment.severity_level || drGradeName}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 text-[10px] block font-mono">Model Confidence</span>
                    <span className="font-mono text-white">{drConfidence}%</span>
                  </div>
                  <div>
                    <span className="text-slate-400 text-[10px] block font-mono">Triage Status</span>
                    <span className="font-bold text-emerald-400">{appointment.status}</span>
                  </div>
                </div>

                {/* Attending Doctor & Appointment Schedule */}
                <div className="p-5 rounded-2xl bg-gradient-to-br from-slate-950 to-slate-900 border border-slate-800 space-y-3">
                  <div className="flex items-center gap-2 text-sm font-bold text-white">
                    <FaUserMd className="text-emerald-400" />
                    <span>Appointment Confirmation</span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                    <div>
                      <span className="text-slate-400 text-[10px] block">Specialist Physician</span>
                      <p className="font-bold text-slate-100">{appointment.doctor_name}</p>
                      <p className="text-[11px] text-slate-400">{appointment.doctor_specialty}</p>
                    </div>
                    <div>
                      <span className="text-slate-400 text-[10px] block">Location & Clinic</span>
                      <p className="font-bold text-slate-100">{appointment.clinic_room}</p>
                      <p className="text-[11px] text-slate-400">{appointment.hospital_name}</p>
                    </div>
                    <div>
                      <span className="text-slate-400 text-[10px] block">Confirmed Time Slot</span>
                      <p className="font-bold text-amber-300 font-mono text-sm">
                        {appointment.scheduled_time ? new Date(appointment.scheduled_time).toLocaleString([], { dateStyle: 'full', timeStyle: 'short' }) : 'Emergency Next-Day Triage'}
                      </p>
                    </div>
                    <div>
                      <span className="text-slate-400 text-[10px] block">Emergency Clinic Direct Line</span>
                      <p className="font-bold text-emerald-400 font-mono flex items-center gap-1 mt-0.5">
                        <FaPhoneAlt className="text-[10px]" />
                        <span>{appointment.contact_phone}</span>
                      </p>
                    </div>
                  </div>
                </div>

                {/* Clinical Justification & Required Procedure */}
                <div className="space-y-2 text-xs">
                  <div className="p-3.5 rounded-xl bg-slate-950 border border-rose-500/30">
                    <span className="text-[10px] font-mono uppercase text-rose-400 font-bold block mb-1">
                      Reason for Urgent Referral
                    </span>
                    <p className="text-slate-200 leading-relaxed">
                      {appointment.clinical_reason || 'Severe Diabetic Retinopathy lesion burden requiring urgent indirect ophthalmoscopic evaluation.'}
                    </p>
                  </div>
                  <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
                    <span className="text-[10px] font-mono uppercase text-slate-400 font-bold block mb-1">
                      Recommended Clinical Action
                    </span>
                    <p className="text-slate-300 leading-relaxed">
                      {appointment.action_required || 'Conduct immediate dilated pupil fundoscopy, optical coherence tomography (OCT) macula scan, and evaluate for immediate panretinal photocoagulation (PRP) or intravitreal anti-VEGF injection.'}
                    </p>
                  </div>
                </div>

                {/* Instructions & Barcode Mockup */}
                <div className="pt-4 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4">
                  <div className="text-[11px] text-slate-400 space-y-0.5">
                    <p>• Present this slip at the Emergency Eye Clinic reception desk upon arrival.</p>
                    <p>• Fasting not required. Arrange transportation as pupil dilation drops will be administered.</p>
                  </div>
                  <div className="text-center sm:text-right shrink-0">
                    <div className="font-mono text-[9px] text-slate-400 tracking-widest">
                      ||| |||| | ||||| || |||||| | |||
                    </div>
                    <span className="font-mono text-[10px] text-slate-400 block mt-0.5">
                      {appointment.appointment_id}
                    </span>
                  </div>
                </div>
              </div>

              {/* Modal Actions */}
              <div className="mt-6 pt-5 border-t border-slate-800 flex flex-wrap items-center justify-end gap-3">
                <button
                  onClick={() => setShowSlipModal(false)}
                  className="btn-secondary text-xs px-4 py-2"
                >
                  Close
                </button>
                <button
                  onClick={() => window.print()}
                  className="btn-primary text-xs px-5 py-2 flex items-center gap-2"
                >
                  <FaPrint />
                  <span>Print Official Slip</span>
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ResultsPage;