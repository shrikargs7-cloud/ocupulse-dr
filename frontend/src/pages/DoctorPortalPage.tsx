import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'react-hot-toast';
import { 
  FaUserMd, 
  FaPhoneAlt, 
  FaHospital, 
  FaCheckCircle, 
  FaClock, 
  FaExclamationTriangle, 
  FaEnvelope, 
  FaKey, 
  FaPaperPlane, 
  FaCalendarAlt, 
  FaFileMedical, 
  FaEye,
  FaShieldAlt,
  FaRedo,
  FaCog,
  FaBroadcastTower,
} from 'react-icons/fa';
import {
  getDoctorProfile,
  registerDoctor,
  getPendingVerifications,
  verifyAndScheduleAppointment,
  getSMSLogs,
  sendTestSMS,
  getTwilioConfig,
  updateTwilioConfig,
} from '../services/api';
import { DoctorProfile, SMSLogItem, Appointment } from '../types';

export const DoctorPortalPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'triage' | 'sms' | 'profile'>('triage');
  const [doctor, setDoctor] = useState<DoctorProfile | null>(null);
  const [isRegistered, setIsRegistered] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [verifications, setVerifications] = useState<Appointment[]>([]);
  const [smsLogs, setSmsLogs] = useState<SMSLogItem[]>([]);
  
  // Twilio Gateway State
  const [twilioStatus, setTwilioStatus] = useState<{
    configured: boolean;
    mode: string;
    account_sid_masked: string | null;
    from_number: string | null;
  } | null>(null);
  const [showTwilioModal, setShowTwilioModal] = useState<boolean>(false);
  const [twilioForm, setTwilioForm] = useState({
    account_sid: '',
    auth_token: '',
    from_number: '',
  });
  const [savingTwilio, setSavingTwilio] = useState<boolean>(false);
  
  // Registration / Edit Doctor Modal & Form State
  const [showRegModal, setShowRegModal] = useState<boolean>(false);
  const [regForm, setRegForm] = useState({
    full_name: 'Dr. Shrikar G S, MD',
    phone_number: '+91 98765 43210',
    specialty: 'Vitreoretinal Specialist & Ophthalmologist',
    hospital_name: 'Apex Regional Eye Institute & Referral Center',
    clinic_room: 'Suite 402 - Emergency Retina Clinic',
    email: 'shrikar.retina@hospital.org',
    license_number: 'KMC-RET-2026-8941',
    pin_code: '1234',
  });

  // Verification & Scheduling Modal State
  const [selectedAppt, setSelectedAppt] = useState<Appointment | null>(null);
  const [verifyForm, setVerifyForm] = useState({
    scheduled_date: new Date(Date.now() + 86400000).toISOString().split('T')[0],
    scheduled_time: '10:30',
    dr_grade_verified: 3,
    clinic_room: 'Suite 402 - Emergency Retina Clinic',
    doctor_notes: 'Urgent optical coherence tomography (OCT) and panretinal photocoagulation laser indicated within 48 hours.',
    patient_phone: '+91 98765 43210',
  });
  const [submittingVerify, setSubmittingVerify] = useState<boolean>(false);

  // Test SMS State
  const [testSmsPhone, setTestSmsPhone] = useState<string>('+91 98765 43210');
  const [testSmsMessage, setTestSmsMessage] = useState<string>(
    '🚨 OcuPulse Emergency Alert: Patient screened with Level 3 Severe NPDR. Action required: Doctor verification & scheduling.'
  );
  const [sendingTestSms, setSendingTestSms] = useState<boolean>(false);

  const loadAllData = async () => {
    setLoading(true);
    try {
      // 1. Doctor Profile
      const profRes = await getDoctorProfile();
      if (profRes.registered && profRes.doctor) {
        setDoctor(profRes.doctor);
        setIsRegistered(true);
      } else {
        setIsRegistered(false);
      }

      // 2. Pending Verifications
      const verifRes = await getPendingVerifications();
      setVerifications(verifRes.pending_verifications || []);

      // 3. SMS Logs
      const smsRes = await getSMSLogs();
      setSmsLogs(smsRes.sms_logs || []);

      // 4. Twilio Status
      const twilioRes = await getTwilioConfig().catch(() => null);
      if (twilioRes) setTwilioStatus(twilioRes);
    } catch (err: any) {
      console.error('Error fetching doctor portal data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAllData();
    const interval = setInterval(() => {
      getPendingVerifications().then(res => setVerifications(res.pending_verifications || [])).catch(() => {});
      getSMSLogs().then(res => setSmsLogs(res.sms_logs || [])).catch(() => {});
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleUpdateTwilio = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingTwilio(true);
    try {
      const res = await updateTwilioConfig(twilioForm);
      toast.success(res.message || 'Twilio configuration saved successfully!');
      if (res.status) setTwilioStatus(res.status);
      setShowTwilioModal(false);
    } catch (err: any) {
      toast.error(err.message || 'Failed to update Twilio settings');
    } finally {
      setSavingTwilio(false);
    }
  };

  const handleRegisterDoctor = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await registerDoctor(regForm);
      setDoctor(res.doctor);
      setIsRegistered(true);
      setShowRegModal(false);
      toast.success(`Registered ${res.doctor.full_name} as active on-call doctor! SMS dispatched.`);
      loadAllData();
    } catch (err: any) {
      toast.error(err.message || 'Failed to register doctor');
    }
  };

  const handleOpenVerifyModal = (appt: Appointment) => {
    setSelectedAppt(appt);
    setVerifyForm({
      scheduled_date: new Date(Date.now() + 86400000).toISOString().split('T')[0],
      scheduled_time: '10:30',
      dr_grade_verified: appt.dr_grade ?? 3,
      clinic_room: appt.clinic_room || (doctor?.clinic_room ?? 'Suite 402 - Emergency Retina Clinic'),
      doctor_notes: `Clinically verified by ${doctor?.full_name || 'Ophthalmologist'}. Dilated fundus examination and OCT scheduled.`,
      patient_phone: appt.contact_phone || (doctor?.phone_number ?? '+91 98765 43210'),
    });
  };

  const handleConfirmVerification = async () => {
    if (!selectedAppt) return;
    setSubmittingVerify(true);
    try {
      const combinedDateTime = `${verifyForm.scheduled_date}T${verifyForm.scheduled_time}:00`;
      await verifyAndScheduleAppointment({
        appointment_id: selectedAppt.appointment_id || (selectedAppt as any).analysis_id,
        scheduled_time: combinedDateTime,
        doctor_notes: verifyForm.doctor_notes,
        dr_grade_verified: verifyForm.dr_grade_verified,
        clinic_room: verifyForm.clinic_room,
        patient_phone: verifyForm.patient_phone,
      });

      toast.success('Appointment clinically verified and scheduled! Confirmation SMS dispatched.');
      setSelectedAppt(null);
      loadAllData();
    } catch (err: any) {
      toast.error(err.message || 'Failed to verify and schedule appointment');
    } finally {
      setSubmittingVerify(false);
    }
  };

  const handleSendTestSms = async (e: React.FormEvent) => {
    e.preventDefault();
    setSendingTestSms(true);
    try {
      await sendTestSMS(testSmsPhone, testSmsMessage, doctor?.full_name || 'Doctor');
      toast.success(`SMS dispatched to ${testSmsPhone}! Check Outbox.`);
      const smsRes = await getSMSLogs();
      setSmsLogs(smsRes.sms_logs || []);
    } catch (err: any) {
      toast.error(err.message || 'Failed to dispatch test SMS');
    } finally {
      setSendingTestSms(false);
    }
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto py-2">
      {/* Top Banner & Doctor On-Call Profile */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-3xl border border-sky-500/30 bg-gradient-to-r from-slate-900 via-[#0b1528] to-slate-900 p-6 sm:p-8 shadow-2xl relative overflow-hidden"
      >
        <div className="absolute top-0 right-0 w-80 h-80 bg-sky-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 relative z-10">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sky-950/70 border border-sky-500/40 text-xs font-mono text-sky-400">
              <FaShieldAlt className="text-sky-400" />
              <span>Ophthalmologist Clinical Decision & Triage Console</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center gap-3">
              <span>Doctor Verification & SMS Triage</span>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                ACTIVE ON-CALL
              </span>
            </h1>
            <p className="text-xs sm:text-sm text-slate-300 max-w-2xl leading-relaxed">
              When patient screenings indicate vision-threatening diabetic retinopathy, automated SMS alerts are dispatched to the on-call doctor. The specialist reviews findings, verifies the diagnosis, and schedules the appointment.
            </p>
          </div>

          {/* Active Doctor Card */}
          <div className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-lg min-w-[280px] w-full md:w-auto">
            {isRegistered && doctor ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <div className="flex items-center space-x-2">
                    <div className="w-8 h-8 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold">
                      <FaUserMd />
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-white">{doctor.full_name}</h4>
                      <p className="text-[10px] text-emerald-400 font-mono">Licensed Ophthalmologist</p>
                    </div>
                  </div>
                  <button
                    onClick={() => {
                      setRegForm({
                        full_name: doctor.full_name,
                        phone_number: doctor.phone_number,
                        specialty: doctor.specialty,
                        hospital_name: doctor.hospital_name,
                        clinic_room: doctor.clinic_room,
                        email: doctor.email || '',
                        license_number: doctor.license_number || '',
                        pin_code: '1234',
                      });
                      setShowRegModal(true);
                    }}
                    className="text-[11px] text-sky-400 hover:text-sky-300 font-mono underline"
                  >
                    Edit
                  </button>
                </div>

                <div className="space-y-1.5 text-xs text-slate-300 font-mono">
                  <div className="flex items-center space-x-2 text-[11px]">
                    <FaPhoneAlt className="text-sky-400 text-xs" />
                    <span className="text-white font-bold">{doctor.phone_number}</span>
                    <span className="text-[9px] bg-sky-950 text-sky-300 px-1.5 py-0.5 rounded border border-sky-800">
                      SMS Recipient
                    </span>
                  </div>
                  <div className="flex items-center space-x-2 text-[11px]">
                    <FaHospital className="text-slate-400 text-xs" />
                    <span className="truncate max-w-[200px]">{doctor.hospital_name}</span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center space-y-2 py-1">
                <p className="text-xs text-slate-400">No Doctor Registered Yet</p>
                <button
                  onClick={() => setShowRegModal(true)}
                  className="w-full py-2 px-3 rounded-xl bg-gradient-to-r from-sky-600 to-teal-500 hover:from-sky-500 hover:to-teal-400 text-white font-bold text-xs shadow-md transition"
                >
                  Register As On-Call Doctor
                </button>
              </div>
            )}
          </div>
        </div>
      </motion.div>

      {/* Navigation Tabs */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div className="flex items-center bg-slate-900 border border-slate-800 p-1 rounded-2xl gap-1">
          <button
            onClick={() => setActiveTab('triage')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition ${
              activeTab === 'triage'
                ? 'bg-sky-500 text-slate-950 font-bold shadow-md shadow-sky-500/20'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <FaFileMedical className="text-sm" />
            <span>Pending Triage Queue</span>
            {verifications.length > 0 && (
              <span className="px-1.5 py-0.2 rounded-full text-[10px] font-mono font-bold bg-rose-600 text-white animate-pulse">
                {verifications.length}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab('sms')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition ${
              activeTab === 'sms'
                ? 'bg-sky-500 text-slate-950 font-bold shadow-md shadow-sky-500/20'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <FaEnvelope className="text-sm" />
            <span>Live SMS Outbox ({smsLogs.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('profile')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition ${
              activeTab === 'profile'
                ? 'bg-sky-500 text-slate-950 font-bold shadow-md shadow-sky-500/20'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <FaUserMd className="text-sm" />
            <span>Doctor Profile</span>
          </button>
        </div>

        <button
          onClick={loadAllData}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-xs text-slate-300 font-mono transition"
        >
          <FaRedo className={`text-xs ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* TAB 1: PENDING TRIAGE QUEUE */}
      {activeTab === 'triage' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <FaExclamationTriangle className="text-amber-400" />
                <span>Patients Awaiting Clinical Sign-Off</span>
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Automated screening flagged these patients with referable disease. Sign off on findings and lock appointment slots.
              </p>
            </div>
          </div>

          {verifications.length === 0 ? (
            <div className="p-12 rounded-3xl bg-slate-900/40 border border-slate-800 text-center space-y-3">
              <FaCheckCircle className="w-10 h-10 text-emerald-400 mx-auto opacity-70" />
              <h4 className="text-base font-bold text-white">All Screenings Cleared</h4>
              <p className="text-xs text-slate-400 max-w-md mx-auto">
                No patients currently require emergency verification. Run an image upload on the Patient Screening portal to test emergency triage dispatch.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {verifications.map((appt) => {
                const isPdr = (appt.dr_grade ?? 0) >= 4;
                const isUrgent = (appt.dr_grade ?? 0) >= 3;
                return (
                  <motion.div
                    key={appt.appointment_id || appt.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-sky-500/40 transition-all space-y-4 shadow-lg"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-bold ${
                            isPdr 
                              ? 'bg-rose-950 text-rose-300 border border-rose-500/40' 
                              : isUrgent 
                              ? 'bg-amber-950 text-amber-300 border border-amber-500/40' 
                              : 'bg-sky-950 text-sky-300 border border-sky-500/40'
                          }`}>
                            {appt.priority || 'STAT / Urgent'}
                          </span>
                          <span className="text-[11px] font-mono text-slate-400">
                            #{appt.appointment_id || 'APT-ID'}
                          </span>
                        </div>
                        <h3 className="text-base font-bold text-white mt-1.5">{appt.patient_name}</h3>
                        <p className="text-xs text-emerald-400 font-mono">
                          {appt.severity_level || `ICDR Grade ${appt.dr_grade}`}
                        </p>
                      </div>

                      <button
                        onClick={() => handleOpenVerifyModal(appt)}
                        className="px-3.5 py-2 rounded-xl bg-gradient-to-r from-sky-600 to-teal-500 hover:from-sky-500 hover:to-teal-400 text-white font-bold text-xs shadow-md transition flex items-center space-x-1.5"
                      >
                        <FaCheckCircle className="text-xs" />
                        <span>Verify & Schedule</span>
                      </button>
                    </div>

                    <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800/80 text-xs text-slate-300 space-y-1 leading-relaxed">
                      <p className="text-slate-400 text-[11px] font-mono">Clinical Rationale:</p>
                      <p className="line-clamp-2">{appt.clinical_reason}</p>
                    </div>

                    <div className="flex items-center justify-between text-[11px] text-slate-400 border-t border-slate-800/80 pt-3">
                      <div className="flex items-center space-x-1.5">
                        <FaClock className="text-slate-500" />
                        <span>Detected: {appt.created_at ? new Date(appt.created_at).toLocaleString() : 'Recent'}</span>
                      </div>
                      <span className="font-mono text-amber-400">Status: Pending Verification</span>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: LIVE SMS OUTBOX LOG */}
      {activeTab === 'sms' && (
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <FaEnvelope className="text-sky-400" />
                <span>Automated SMS Dispatch Outbox</span>
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Every emergency clinical alert and patient appointment confirmation sent by the system is logged here in real-time.
              </p>
            </div>
          </div>

          {/* Twilio Gateway Status & Configuration Card */}
          <div className="p-4 sm:p-5 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900 to-slate-950 border border-slate-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="flex items-center space-x-3.5">
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-lg ${
                twilioStatus?.configured 
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' 
                  : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
              }`}>
                <FaBroadcastTower />
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <h3 className="text-sm font-bold text-white">Twilio SMS Gateway</h3>
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-bold ${
                    twilioStatus?.configured
                      ? 'bg-emerald-950 text-emerald-300 border border-emerald-500/40'
                      : 'bg-amber-950 text-amber-300 border border-amber-500/40'
                  }`}>
                    {twilioStatus?.configured ? '● Live Twilio REST API' : '● Simulation Outbox Fallback'}
                  </span>
                </div>
                <p className="text-xs text-slate-400 font-mono mt-0.5">
                  {twilioStatus?.configured
                    ? `Account: ${twilioStatus.account_sid_masked || 'Active'} | From: ${twilioStatus.from_number}`
                    : 'Dispatching to internal live outbox. Add your Twilio credentials to transmit real SMS to phones.'}
                </p>
              </div>
            </div>
            <button
              onClick={() => setShowTwilioModal(true)}
              className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-sky-300 border border-slate-700 text-xs font-mono transition flex items-center space-x-2"
            >
              <FaCog className="text-xs" />
              <span>{twilioStatus?.configured ? 'Edit Twilio Keys' : 'Configure Twilio API'}</span>
            </button>
          </div>

          {/* Test SMS Quick Sender */}
          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
            <h3 className="text-xs font-mono uppercase text-sky-400 font-bold tracking-wider flex items-center gap-2">
              <FaPaperPlane className="text-xs" />
              <span>Interactive SMS Demo Dispatcher (Try with any mobile number)</span>
            </h3>
            <form onSubmit={handleSendTestSms} className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <input
                type="text"
                value={testSmsPhone}
                onChange={(e) => setTestSmsPhone(e.target.value)}
                placeholder="Phone e.g. +91 98765 43210"
                className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-sky-500 font-mono"
                required
              />
              <input
                type="text"
                value={testSmsMessage}
                onChange={(e) => setTestSmsMessage(e.target.value)}
                placeholder="Message text"
                className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-sky-500 font-mono sm:col-span-1"
                required
              />
              <button
                type="submit"
                disabled={sendingTestSms}
                className="py-2 px-4 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-bold text-xs transition disabled:opacity-50 flex items-center justify-center space-x-2 shadow-md shadow-sky-600/20"
              >
                <FaPaperPlane className="text-xs" />
                <span>{sendingTestSms ? 'Transmitting...' : 'Dispatch Live SMS'}</span>
              </button>
            </form>
          </div>

          {/* SMS History Cards */}
          {smsLogs.length === 0 ? (
            <div className="p-12 rounded-3xl bg-slate-900/40 border border-slate-800 text-center space-y-2">
              <FaEnvelope className="w-8 h-8 text-slate-600 mx-auto" />
              <p className="text-xs text-slate-400">No SMS messages logged yet. Use the test sender above or run a patient screening.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {smsLogs.map((log) => (
                <div
                  key={log.id}
                  className="p-4 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-2 hover:border-slate-700 transition"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/60 pb-2 text-[11px] font-mono">
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-0.5 rounded-full font-bold text-[9px] ${
                        log.recipient_role === 'DOCTOR' 
                          ? 'bg-rose-950 text-rose-300 border border-rose-500/30' 
                          : 'bg-emerald-950 text-emerald-300 border border-emerald-500/30'
                      }`}>
                        {log.recipient_role}
                      </span>
                      <span className="text-white font-semibold">{log.recipient_phone}</span>
                      {log.recipient_name && (
                        <span className="text-slate-400">({log.recipient_name})</span>
                      )}
                    </div>
                    <div className="flex items-center space-x-3 text-slate-400">
                      <span className="text-[10px] text-sky-400">{log.gateway}</span>
                      <span className="text-slate-500">•</span>
                      <span>{log.sent_at ? new Date(log.sent_at).toLocaleTimeString() : 'Recent'}</span>
                    </div>
                  </div>

                  <p className="text-xs text-slate-200 font-mono leading-relaxed pt-1">
                    "{log.message_text}"
                  </p>

                  <div className="flex items-center justify-between text-[10px] font-mono text-slate-500 pt-1">
                    <span>Trigger: {log.trigger_event}</span>
                    <span className="text-emerald-400 font-semibold">✓ {log.status}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 3: DOCTOR PROFILE & REGISTRATION */}
      {activeTab === 'profile' && (
        <div className="max-w-2xl mx-auto space-y-6">
          <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 space-y-6">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-xl bg-sky-500/20 text-sky-400 flex items-center justify-center text-lg">
                  <FaUserMd />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">Registered Ophthalmologist Profile</h3>
                  <p className="text-xs text-slate-400 font-mono">Designated primary recipient for emergency screening dispatches</p>
                </div>
              </div>
              <button
                onClick={() => setShowRegModal(true)}
                className="px-3 py-1.5 rounded-xl bg-sky-500/20 hover:bg-sky-500/30 text-sky-300 border border-sky-500/40 text-xs font-mono transition"
              >
                Update Profile
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono">
              <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
                <span className="text-slate-500 block text-[10px]">Doctor Full Name:</span>
                <span className="text-white font-bold text-sm mt-0.5 block">{doctor?.full_name || 'Not Registered'}</span>
              </div>
              <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
                <span className="text-slate-500 block text-[10px]">Mobile Phone for SMS:</span>
                <span className="text-sky-400 font-bold text-sm mt-0.5 block">{doctor?.phone_number || 'Not Registered'}</span>
              </div>
              <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
                <span className="text-slate-500 block text-[10px]">Specialty:</span>
                <span className="text-slate-200 mt-0.5 block">{doctor?.specialty || 'Vitreoretinal Ophthalmology'}</span>
              </div>
              <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
                <span className="text-slate-500 block text-[10px]">Hospital / Eye Center:</span>
                <span className="text-slate-200 mt-0.5 block">{doctor?.hospital_name || 'Apex Regional Eye Institute'}</span>
              </div>
              <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
                <span className="text-slate-500 block text-[10px]">Clinic Room / Suite:</span>
                <span className="text-slate-200 mt-0.5 block">{doctor?.clinic_room || 'Room 402 - Emergency Retina'}</span>
              </div>
              <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
                <span className="text-slate-500 block text-[10px]">Medical License No:</span>
                <span className="text-emerald-400 mt-0.5 block">{doctor?.license_number || 'KMC-RET-2026-8941'}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: DOCTOR REGISTRATION & PROFILE EDIT */}
      <AnimatePresence>
        {showRegModal && (
          <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-slate-900 border border-sky-500/30 rounded-3xl p-6 sm:p-8 max-w-lg w-full space-y-6 shadow-2xl relative"
            >
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center space-x-2.5">
                  <div className="w-8 h-8 rounded-lg bg-sky-500/20 text-sky-400 flex items-center justify-center">
                    <FaUserMd />
                  </div>
                  <h3 className="text-base font-bold text-white">Register On-Call Doctor</h3>
                </div>
                <button
                  onClick={() => setShowRegModal(false)}
                  className="text-slate-400 hover:text-white font-mono text-sm"
                >
                  ✕
                </button>
              </div>

              <form onSubmit={handleRegisterDoctor} className="space-y-4 text-xs font-mono">
                <div>
                  <label className="text-slate-300 block mb-1">Doctor Full Name (Title + Name):</label>
                  <input
                    type="text"
                    value={regForm.full_name}
                    onChange={(e) => setRegForm({ ...regForm, full_name: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-sky-500"
                    placeholder="e.g. Dr. Shrikar G S, MD"
                    required
                  />
                </div>

                <div>
                  <label className="text-slate-300 block mb-1">
                    Mobile Phone Number for SMS Alerts (with country code):
                  </label>
                  <input
                    type="text"
                    value={regForm.phone_number}
                    onChange={(e) => setRegForm({ ...regForm, phone_number: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sky-400 font-bold focus:outline-none focus:border-sky-500"
                    placeholder="e.g. +91 98765 43210"
                    required
                  />
                  <span className="text-[10px] text-slate-500 block mt-1">
                    Emergency SMS alerts will be dispatched directly to this phone number.
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="text-slate-300 block mb-1">Specialty:</label>
                    <input
                      type="text"
                      value={regForm.specialty}
                      onChange={(e) => setRegForm({ ...regForm, specialty: e.target.value })}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-sky-500"
                      required
                    />
                  </div>
                  <div>
                    <label className="text-slate-300 block mb-1">Clinic Room / Suite:</label>
                    <input
                      type="text"
                      value={regForm.clinic_room}
                      onChange={(e) => setRegForm({ ...regForm, clinic_room: e.target.value })}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-sky-500"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="text-slate-300 block mb-1">Hospital / Eye Center:</label>
                  <input
                    type="text"
                    value={regForm.hospital_name}
                    onChange={(e) => setRegForm({ ...regForm, hospital_name: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-sky-500"
                    required
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="text-slate-300 block mb-1">License / Reg Number:</label>
                    <input
                      type="text"
                      value={regForm.license_number}
                      onChange={(e) => setRegForm({ ...regForm, license_number: e.target.value })}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-sky-500"
                    />
                  </div>
                  <div>
                    <label className="text-slate-300 block mb-1">Quick PIN (for Doctor Login):</label>
                    <input
                      type="password"
                      value={regForm.pin_code}
                      onChange={(e) => setRegForm({ ...regForm, pin_code: e.target.value })}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-sky-500"
                      placeholder="1234"
                    />
                  </div>
                </div>

                <div className="pt-3 border-t border-slate-800 flex justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => setShowRegModal(false)}
                    className="px-4 py-2 rounded-xl text-xs text-slate-400 hover:text-white"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-5 py-2 rounded-xl bg-gradient-to-r from-sky-600 to-teal-500 hover:from-sky-500 hover:to-teal-400 text-white font-bold text-xs shadow-md transition"
                  >
                    Save & Set Active Doctor
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* MODAL: TWILIO CREDENTIALS CONFIGURATION */}
      <AnimatePresence>
        {showTwilioModal && (
          <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-slate-900 border border-sky-500/30 rounded-3xl p-6 sm:p-8 max-w-lg w-full space-y-5 shadow-2xl relative"
            >
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center space-x-2.5">
                  <div className="w-8 h-8 rounded-lg bg-sky-500/20 text-sky-400 flex items-center justify-center">
                    <FaBroadcastTower />
                  </div>
                  <h3 className="text-base font-bold text-white">Twilio SMS API Configuration</h3>
                </div>
                <button
                  onClick={() => setShowTwilioModal(false)}
                  className="text-slate-400 hover:text-white font-mono text-sm"
                >
                  ✕
                </button>
              </div>

              <div className="p-3 rounded-xl bg-sky-950/40 border border-sky-500/30 text-xs font-mono text-sky-200">
                Enter your Twilio Console credentials below. Once configured, OcuPulse will instantly dispatch actual SMS text messages to the doctor's and patient's mobile phones.
              </div>

              <form onSubmit={handleUpdateTwilio} className="space-y-4 text-xs font-mono">
                <div>
                  <label className="text-slate-300 block mb-1">Twilio Account SID (e.g. AC...):</label>
                  <input
                    type="text"
                    value={twilioForm.account_sid}
                    onChange={(e) => setTwilioForm({ ...twilioForm, account_sid: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white font-mono focus:outline-none focus:border-sky-500"
                    placeholder="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                    required
                  />
                </div>

                <div>
                  <label className="text-slate-300 block mb-1">Twilio Auth Token:</label>
                  <input
                    type="password"
                    value={twilioForm.auth_token}
                    onChange={(e) => setTwilioForm({ ...twilioForm, auth_token: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white font-mono focus:outline-none focus:border-sky-500"
                    placeholder="••••••••••••••••••••••••••••••••"
                    required
                  />
                </div>

                <div>
                  <label className="text-slate-300 block mb-1">Twilio Sender Phone Number (E.164 format):</label>
                  <input
                    type="text"
                    value={twilioForm.from_number}
                    onChange={(e) => setTwilioForm({ ...twilioForm, from_number: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-emerald-400 font-bold font-mono focus:outline-none focus:border-sky-500"
                    placeholder="+1234567890"
                    required
                  />
                </div>

                <div className="pt-2 flex items-center justify-end space-x-3">
                  <button
                    type="button"
                    onClick={() => setShowTwilioModal(false)}
                    className="px-4 py-2 rounded-xl text-xs text-slate-400 hover:text-white"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={savingTwilio}
                    className="px-5 py-2 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-bold text-xs shadow-md shadow-sky-600/20 transition disabled:opacity-50"
                  >
                    {savingTwilio ? 'Saving & Testing...' : 'Save Twilio Configuration'}
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* MODAL: CLINICAL VERIFICATION & APPOINTMENT SCHEDULING */}
      <AnimatePresence>
        {selectedAppt && (
          <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-slate-900 border border-sky-500/30 rounded-3xl p-6 sm:p-8 max-w-xl w-full space-y-6 shadow-2xl relative my-8"
            >
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center space-x-2.5">
                  <div className="w-8 h-8 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center">
                    <FaFileMedical />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-white">Clinical Verification & Scheduling</h3>
                    <p className="text-[10px] text-slate-400 font-mono">Patient: {selectedAppt.patient_name}</p>
                  </div>
                </div>
                <button
                  onClick={() => setSelectedAppt(null)}
                  className="text-slate-400 hover:text-white font-mono text-sm"
                >
                  ✕
                </button>
              </div>

              {/* Scan summary banner */}
              <div className="p-3.5 rounded-2xl bg-slate-950 border border-slate-800/80 space-y-1 text-xs font-mono">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">AI Initial Screening:</span>
                  <span className="text-rose-400 font-bold">
                    {selectedAppt.severity_level || `Grade ${selectedAppt.dr_grade}`}
                  </span>
                </div>
                <p className="text-[11px] text-slate-300 pt-1 line-clamp-2">
                  {selectedAppt.clinical_reason}
                </p>
              </div>

              <div className="space-y-4 text-xs font-mono">
                {/* Doctor Grade Confirmation */}
                <div>
                  <label className="text-slate-300 block mb-1">Doctor-Verified DR Severity Grade:</label>
                  <select
                    value={verifyForm.dr_grade_verified}
                    onChange={(e) => setVerifyForm({ ...verifyForm, dr_grade_verified: parseInt(e.target.value, 10) })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-sky-500 font-mono"
                  >
                    <option value={0}>Level 0: No DR (Overrule AI finding)</option>
                    <option value={1}>Level 1: Mild NPDR (Microaneurysms only)</option>
                    <option value={2}>Level 2: Moderate NPDR (Referable)</option>
                    <option value={3}>Level 3: Severe NPDR (High risk 4-2-1)</option>
                    <option value={4}>Level 4: Proliferative DR (PDR Neovascularization)</option>
                  </select>
                </div>

                {/* Appointment Date & Time */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="text-slate-300 block mb-1">Appointment Date:</label>
                    <input
                      type="date"
                      value={verifyForm.scheduled_date}
                      onChange={(e) => setVerifyForm({ ...verifyForm, scheduled_date: e.target.value })}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-sky-500 font-mono"
                      required
                    />
                  </div>
                  <div>
                    <label className="text-slate-300 block mb-1">Consultation Time:</label>
                    <input
                      type="time"
                      value={verifyForm.scheduled_time}
                      onChange={(e) => setVerifyForm({ ...verifyForm, scheduled_time: e.target.value })}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-sky-500 font-mono"
                      required
                    />
                  </div>
                </div>

                {/* Patient Mobile for SMS */}
                <div>
                  <label className="text-slate-300 block mb-1">Patient Mobile Phone (for SMS Confirmation):</label>
                  <input
                    type="text"
                    value={verifyForm.patient_phone}
                    onChange={(e) => setVerifyForm({ ...verifyForm, patient_phone: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-sky-500 font-mono"
                    placeholder="+91 98765 43210"
                  />
                </div>

                {/* Doctor clinical notes */}
                <div>
                  <label className="text-slate-300 block mb-1">Doctor Clinical Notes & Recommendations:</label>
                  <textarea
                    rows={3}
                    value={verifyForm.doctor_notes}
                    onChange={(e) => setVerifyForm({ ...verifyForm, doctor_notes: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-white focus:outline-none focus:border-sky-500 font-mono text-[11px]"
                    placeholder="e.g. Schedule OCT macular examination. Initiate panretinal laser."
                  />
                </div>

                <div className="pt-3 border-t border-slate-800 flex items-center justify-between">
                  <span className="text-[10px] text-slate-500">
                    Signing as: {doctor?.full_name || 'Licensed Specialist'}
                  </span>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => setSelectedAppt(null)}
                      className="px-4 py-2 rounded-xl text-xs text-slate-400 hover:text-white"
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      onClick={handleConfirmVerification}
                      disabled={submittingVerify}
                      className="px-5 py-2 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-slate-950 font-bold text-xs shadow-md transition disabled:opacity-50 flex items-center space-x-1.5"
                    >
                      <FaCheckCircle className="text-xs" />
                      <span>{submittingVerify ? 'Verifying...' : 'Sign Off & Send SMS'}</span>
                    </button>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default DoctorPortalPage;
