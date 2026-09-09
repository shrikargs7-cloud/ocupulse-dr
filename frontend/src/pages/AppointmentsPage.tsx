import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FaUserMd,
  FaCalendarCheck,
  FaClock,
  FaHospital,
  FaPhoneAlt,
  FaPrint,
  FaEye,
  FaCheckCircle,
  FaTimes,
  FaSearch,
  FaFilter,
  FaExclamationTriangle,
  FaNotesMedical,
  FaExternalLinkAlt,
  FaSync,
  FaTrash
} from 'react-icons/fa';
import toast from 'react-hot-toast';

import { getAppointments, updateAppointmentStatus, deleteAppointment } from '../services/api';
import { Appointment } from '../types';

export const AppointmentsPage: React.FC = () => {
  const navigate = useNavigate();
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [priorityFilter, setPriorityFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedAppointment, setSelectedAppointment] = useState<Appointment | null>(null);

  const fetchAppointmentsList = async () => {
    setIsLoading(true);
    try {
      const data = await getAppointments(statusFilter, priorityFilter);
      setAppointments(data);
    } catch (err: any) {
      toast.error(err.message || 'Failed to load appointments from database');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAppointmentsList();
  }, [statusFilter, priorityFilter]);

  const handleStatusChange = async (appointmentId: string, newStatus: string) => {
    try {
      const updated = await updateAppointmentStatus(appointmentId, newStatus);
      setAppointments(prev => prev.map(a => a.appointment_id === appointmentId ? updated : a));
      toast.success(`Appointment marked as ${newStatus}`);
    } catch (err: any) {
      toast.error(err.message || 'Failed to update appointment status');
    }
  };

  const handleDeleteAppointment = async (appointmentId: string) => {
    if (!window.confirm(`Delete appointment record ${appointmentId}?`)) return;
    try {
      await deleteAppointment(appointmentId);
      setAppointments(prev => prev.filter(a => a.appointment_id !== appointmentId));
      toast.success(`Appointment ${appointmentId} removed from roster`);
    } catch (err: any) {
      toast.error(err.message || 'Failed to delete appointment');
    }
  };

  // Filtered by search query
  const filteredAppointments = appointments.filter(a => {
    const q = searchQuery.toLowerCase();
    return (
      (a.appointment_id && a.appointment_id.toLowerCase().includes(q)) ||
      (a.patient_id && a.patient_id.toLowerCase().includes(q)) ||
      (a.patient_name && a.patient_name.toLowerCase().includes(q)) ||
      (a.doctor_name && a.doctor_name.toLowerCase().includes(q)) ||
      (a.severity_level && a.severity_level.toLowerCase().includes(q)) ||
      (a.analysis_id && a.analysis_id.toLowerCase().includes(q))
    );
  });

  const totalCount = appointments.length;
  const urgentCount = appointments.filter(a => a.priority && a.priority.toUpperCase().includes('URGENT')).length;
  const confirmedCount = appointments.filter(a => a.status === 'CONFIRMED').length;
  const attendedCount = appointments.filter(a => a.status === 'ATTENDED').length;

  return (
    <div className="space-y-8 max-w-6xl mx-auto py-2">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="p-2 rounded-xl bg-rose-950/80 border border-rose-500/30 text-rose-400">
              <FaCalendarCheck className="text-xl" />
            </span>
            <div>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
                Emergency Doctor Appointments & Triage
              </h1>
              <p className="text-xs text-slate-400 mt-0.5">
                Automated ophthalmologist referrals for patients flagged with critical retinal disease
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchAppointmentsList}
            className="btn-secondary text-xs flex items-center gap-2"
            title="Refresh database records"
          >
            <FaSync className={isLoading ? 'animate-spin' : ''} />
            <span>Refresh Roster</span>
          </button>
          <button
            onClick={() => navigate('/analyze')}
            className="btn-primary text-xs flex items-center gap-2"
          >
            <FaEye />
            <span>New Screening Scan</span>
          </button>
        </div>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card p-4 flex items-center gap-4">
          <div className="h-12 w-12 rounded-2xl bg-slate-800/80 border border-slate-700 flex items-center justify-center text-slate-200">
            <FaCalendarCheck className="text-xl" />
          </div>
          <div>
            <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block">
              Total Referrals
            </span>
            <span className="text-2xl font-black text-white font-mono">{totalCount}</span>
          </div>
        </div>

        <div className="card p-4 flex items-center gap-4 border-rose-500/30 bg-rose-950/20">
          <div className="h-12 w-12 rounded-2xl bg-rose-500/20 border border-rose-500/40 flex items-center justify-center text-rose-400">
            <FaExclamationTriangle className="text-xl animate-pulse" />
          </div>
          <div>
            <span className="text-[11px] font-mono text-rose-300 uppercase tracking-wider block">
              STAT / Urgent
            </span>
            <span className="text-2xl font-black text-rose-200 font-mono">{urgentCount}</span>
          </div>
        </div>

        <div className="card p-4 flex items-center gap-4">
          <div className="h-12 w-12 rounded-2xl bg-emerald-950/80 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <FaCheckCircle className="text-xl" />
          </div>
          <div>
            <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block">
              Confirmed
            </span>
            <span className="text-2xl font-black text-emerald-400 font-mono">{confirmedCount}</span>
          </div>
        </div>

        <div className="card p-4 flex items-center gap-4">
          <div className="h-12 w-12 rounded-2xl bg-blue-950/80 border border-blue-500/30 flex items-center justify-center text-blue-400">
            <FaUserMd className="text-xl" />
          </div>
          <div>
            <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block">
              Attended
            </span>
            <span className="text-2xl font-black text-blue-300 font-mono">{attendedCount}</span>
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="card p-4 flex flex-wrap items-center justify-between gap-4">
        {/* Search */}
        <div className="relative flex-1 min-w-[240px]">
          <FaSearch className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 text-xs" />
          <input
            type="text"
            placeholder="Search by patient ID, voucher #, doctor, or analysis ID..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-4 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-colors"
          />
        </div>

        {/* Priority Filter */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 font-mono">Priority:</span>
          <select
            value={priorityFilter}
            onChange={e => setPriorityFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-white focus:outline-none focus:border-emerald-500 font-mono"
          >
            <option value="ALL">All Priorities</option>
            <option value="URGENT">STAT / Urgent (24-48h)</option>
            <option value="ROUTINE">Routine Follow-Up</option>
          </select>
        </div>

        {/* Status Filter */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 font-mono">Status:</span>
          <select
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-white focus:outline-none focus:border-emerald-500 font-mono"
          >
            <option value="ALL">All Statuses</option>
            <option value="CONFIRMED">CONFIRMED</option>
            <option value="ATTENDED">ATTENDED</option>
            <option value="CANCELLED">CANCELLED</option>
          </select>
        </div>
      </div>

      {/* Appointments List */}
      {isLoading ? (
        <div className="min-h-[30vh] flex items-center justify-center">
          <div className="text-center space-y-3">
            <div className="animate-spin rounded-full h-10 w-10 border-2 border-emerald-500 border-t-transparent mx-auto" />
            <p className="text-xs font-mono text-slate-400">Querying Supabase Appointments...</p>
          </div>
        </div>
      ) : filteredAppointments.length === 0 ? (
        <div className="card p-12 text-center max-w-md mx-auto space-y-3">
          <FaCalendarCheck className="text-3xl text-slate-500 mx-auto" />
          <h3 className="text-base font-bold text-white">No Appointments Found</h3>
          <p className="text-xs text-slate-400">
            {searchQuery || statusFilter !== 'ALL' || priorityFilter !== 'ALL'
              ? 'No records match the active search or filters.'
              : 'No appointments have been booked yet. Critical retinal conditions will automatically be triaged and displayed here.'}
          </p>
          <button onClick={() => navigate('/analyze')} className="btn-primary text-xs mx-auto mt-2">
            Run Retinal Screening
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredAppointments.map(appt => {
            const isUrgent = appt.priority && appt.priority.toUpperCase().includes('URGENT');
            const isConfirmed = appt.status === 'CONFIRMED';
            const isAttended = appt.status === 'ATTENDED';

            return (
              <motion.div
                key={appt.appointment_id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className={`card p-5 border transition-all ${
                  isUrgent
                    ? 'border-rose-500/40 bg-gradient-to-r from-rose-950/30 via-slate-900 to-slate-900 shadow-lg shadow-rose-950/20'
                    : 'border-slate-800 bg-slate-900/60'
                }`}
              >
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                  {/* Left Column: Identifiers & Badges */}
                  <div className="space-y-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-mono text-xs font-bold text-emerald-400 px-2.5 py-0.5 rounded-full bg-emerald-950 border border-emerald-500/30">
                        {appt.appointment_id}
                      </span>
                      <span
                        className={`px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold border ${
                          isUrgent
                            ? 'bg-rose-950 text-rose-300 border-rose-500/50 animate-pulse'
                            : 'bg-slate-800 text-slate-300 border-slate-700'
                        }`}
                      >
                        {appt.priority}
                      </span>
                      <span
                        className={`px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold border ${
                          isConfirmed
                            ? 'bg-emerald-950 text-emerald-300 border-emerald-500/40'
                            : isAttended
                            ? 'bg-blue-950 text-blue-300 border-blue-500/40'
                            : 'bg-slate-800 text-slate-400 border-slate-700'
                        }`}
                      >
                        {appt.status}
                      </span>
                      {appt.severity_level && (
                        <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-rose-950/80 text-rose-300 border border-rose-500/30">
                          {appt.severity_level}
                        </span>
                      )}
                    </div>

                    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-400">
                      <span>Patient: <strong className="text-white">{appt.patient_name || appt.patient_id || 'Anonymous'}</strong></span>
                      {appt.analysis_id && (
                        <span>Linked Scan: <code className="text-emerald-400 font-mono">{appt.analysis_id}</code></span>
                      )}
                      <span>Booked: {new Date(appt.created_at).toLocaleDateString()}</span>
                    </div>

                    {/* Retinal Screening Clinical Report Findings Box */}
                    <div className="mt-3 p-3 rounded-xl bg-slate-950/80 border border-slate-800/90 grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                      <div>
                        <span className="text-[10px] font-mono uppercase tracking-wider text-emerald-400 font-bold block mb-1 flex items-center gap-1.5">
                          <FaNotesMedical className="text-xs" />
                          ICDR Severity & Clinical Findings
                        </span>
                        <p className="text-slate-200 font-semibold text-xs">
                          {appt.severity_level || (appt.dr_grade !== undefined ? `Level ${appt.dr_grade}: Referable DR` : 'Diabetic Retinopathy Assessment')}
                        </p>
                        <p className="text-slate-400 text-[11px] mt-0.5 leading-relaxed">
                          {appt.clinical_reason || 'Diabetic retinopathy screening identified microvascular abnormalities requiring specialist ophthalmology evaluation.'}
                        </p>
                      </div>
                      <div>
                        <span className="text-[10px] font-mono uppercase tracking-wider text-amber-400 font-bold block mb-1">
                          Recommended Action Plan
                        </span>
                        <p className="text-slate-300 text-[11px] leading-relaxed">
                          {appt.action_required || 'Comprehensive dilated stereoscopic fundus examination and optical coherence tomography (OCT) to assess macular status.'}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Right Column: Appointment Details & Actions */}
                  <div className="flex flex-col sm:flex-row lg:flex-col items-start sm:items-center lg:items-end gap-3 shrink-0">
                    <div className="text-left sm:text-right">
                      <span className="text-xs font-bold text-amber-300 font-mono block">
                        {appt.scheduled_time ? new Date(appt.scheduled_time).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' }) : 'Next 24h Triage'}
                      </span>
                      <span className="text-[11px] text-slate-400 block mt-0.5">
                        {appt.doctor_name} • {appt.clinic_room}
                      </span>
                    </div>

                    <div className="flex flex-wrap items-center gap-2">
                      {appt.analysis_id && (
                        <button
                          onClick={() => navigate(`/results/${encodeURIComponent(appt.analysis_id!)}`)}
                          className="btn-primary text-xs px-3.5 py-1.5 flex items-center gap-1.5 font-bold shadow-md shadow-emerald-950/40"
                          title="Open complete interactive screening report and visualizers"
                        >
                          <FaNotesMedical />
                          <span>View Screening Report</span>
                        </button>
                      )}

                      <button
                        onClick={() => setSelectedAppointment(appt)}
                        className="btn-secondary text-xs px-3 py-1.5 flex items-center gap-1.5"
                        title="View printable official referral voucher"
                      >
                        <FaPrint />
                        <span>Referral Slip</span>
                      </button>

                      {isConfirmed && (
                        <button
                          onClick={() => handleStatusChange(appt.appointment_id, 'ATTENDED')}
                          className="px-3 py-1.5 rounded-xl text-xs font-bold bg-blue-600 hover:bg-blue-500 text-white transition-colors flex items-center gap-1"
                        >
                          <FaCheckCircle />
                          <span>Mark Attended</span>
                        </button>
                      )}

                      <button
                        onClick={() => handleDeleteAppointment(appt.appointment_id)}
                        className="p-2 rounded-xl text-xs text-rose-400/80 hover:text-rose-300 hover:bg-rose-950/40 border border-transparent hover:border-rose-500/30 transition-colors"
                        title="Delete / remove appointment record"
                      >
                        <FaTrash />
                      </button>
                    </div>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      )}

      {/* Referral Slip Modal */}
      <AnimatePresence>
        {selectedAppointment && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm overflow-y-auto">
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="bg-slate-900 border-2 border-slate-700 rounded-3xl max-w-2xl w-full p-6 sm:p-8 shadow-2xl relative text-slate-100 my-8"
            >
              <button
                onClick={() => setSelectedAppointment(null)}
                className="absolute top-5 right-5 h-9 w-9 rounded-full bg-slate-800 hover:bg-slate-700 flex items-center justify-center text-slate-400 hover:text-white transition-colors"
              >
                <FaTimes />
              </button>

              <div id="referral-slip-printable" className="space-y-6">
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
                      {selectedAppointment.priority}
                    </span>
                    <span className="block font-mono text-[10px] text-slate-400 mt-1">
                      Voucher #{selectedAppointment.appointment_id}
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 p-4 rounded-2xl bg-slate-950/70 border border-slate-800 text-xs">
                  <div>
                    <span className="text-slate-400 text-[10px] block font-mono">Patient</span>
                    <span className="font-bold text-white text-sm">{selectedAppointment.patient_name || selectedAppointment.patient_id || 'Anonymous'}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 text-[10px] block font-mono">Linked Scan ID</span>
                    <span className="font-mono text-emerald-400">{selectedAppointment.analysis_id || 'N/A'}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 text-[10px] block font-mono">Referred Date</span>
                    <span className="text-slate-200">{new Date(selectedAppointment.created_at).toLocaleDateString()}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 text-[10px] block font-mono">DR Severity</span>
                    <span className="font-bold text-rose-400">{selectedAppointment.severity_level || 'Critical'}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 text-[10px] block font-mono">Priority</span>
                    <span className="font-mono text-amber-300">{selectedAppointment.priority}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 text-[10px] block font-mono">Status</span>
                    <span className="font-bold text-emerald-400">{selectedAppointment.status}</span>
                  </div>
                </div>

                <div className="p-5 rounded-2xl bg-gradient-to-br from-slate-950 to-slate-900 border border-slate-800 space-y-3">
                  <div className="flex items-center gap-2 text-sm font-bold text-white">
                    <FaUserMd className="text-emerald-400" />
                    <span>Appointment Confirmation</span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                    <div>
                      <span className="text-slate-400 text-[10px] block">Specialist Physician</span>
                      <p className="font-bold text-slate-100">{selectedAppointment.doctor_name}</p>
                      <p className="text-[11px] text-slate-400">{selectedAppointment.doctor_specialty}</p>
                    </div>
                    <div>
                      <span className="text-slate-400 text-[10px] block">Location & Clinic</span>
                      <p className="font-bold text-slate-100">{selectedAppointment.clinic_room}</p>
                      <p className="text-[11px] text-slate-400">{selectedAppointment.hospital_name}</p>
                    </div>
                    <div>
                      <span className="text-slate-400 text-[10px] block">Confirmed Time Slot</span>
                      <p className="font-bold text-amber-300 font-mono text-sm">
                        {selectedAppointment.scheduled_time ? new Date(selectedAppointment.scheduled_time).toLocaleString([], { dateStyle: 'full', timeStyle: 'short' }) : 'Emergency Next-Day Triage'}
                      </p>
                    </div>
                    <div>
                      <span className="text-slate-400 text-[10px] block">Clinic Direct Line</span>
                      <p className="font-bold text-emerald-400 font-mono flex items-center gap-1 mt-0.5">
                        <FaPhoneAlt className="text-[10px]" />
                        <span>{selectedAppointment.contact_phone}</span>
                      </p>
                    </div>
                  </div>
                </div>

                <div className="space-y-2 text-xs">
                  <div className="p-3.5 rounded-xl bg-slate-950 border border-rose-500/30">
                    <span className="text-[10px] font-mono uppercase text-rose-400 font-bold block mb-1">
                      Clinical Reason for Referral
                    </span>
                    <p className="text-slate-200 leading-relaxed">
                      {selectedAppointment.clinical_reason}
                    </p>
                  </div>
                  <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
                    <span className="text-[10px] font-mono uppercase text-slate-400 font-bold block mb-1">
                      Recommended Clinical Action
                    </span>
                    <p className="text-slate-300 leading-relaxed">
                      {selectedAppointment.action_required || 'Conduct immediate dilated pupil fundoscopy, optical coherence tomography (OCT) macula scan, and evaluate for immediate panretinal photocoagulation (PRP) or intravitreal anti-VEGF injection.'}
                    </p>
                  </div>
                </div>

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
                      {selectedAppointment.appointment_id}
                    </span>
                  </div>
                </div>
              </div>

              <div className="mt-6 pt-5 border-t border-slate-800 flex flex-wrap items-center justify-between gap-3">
                <div>
                  {selectedAppointment.analysis_id && (
                    <button
                      onClick={() => {
                        const aid = selectedAppointment.analysis_id;
                        setSelectedAppointment(null);
                        navigate(`/results/${encodeURIComponent(aid!)}`);
                      }}
                      className="btn-secondary text-xs px-4 py-2 flex items-center gap-2 text-emerald-400 hover:text-emerald-300"
                    >
                      <FaNotesMedical />
                      <span>Open Full Screening Report</span>
                    </button>
                  )}
                </div>
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => setSelectedAppointment(null)}
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
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default AppointmentsPage;
