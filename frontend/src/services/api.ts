/**
 * OcuPulse API Client Service
 */

import { AnalysisResponse, HistoryItem, DemoSampleItem } from '../types';

const API_BASE_URL = '/api';

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE_URL}/health`);
    if (!res.ok) return false;
    const data = await res.json();
    return data.status === 'ok';
  } catch (err) {
    console.error('Health check failed:', err);
    return false;
  }
}

export async function getDemoSamples(): Promise<DemoSampleItem[]> {
  const res = await fetch(`${API_BASE_URL}/demo-samples`);
  if (!res.ok) {
    throw new Error('Failed to load demo retinal fundus samples');
  }
  return res.json();
}

export async function analyzeImage(
  file?: File | null,
  demoId?: string | null
): Promise<AnalysisResponse> {
  const formData = new FormData();
  
  if (demoId) {
    formData.append('demo_id', demoId);
  } else if (file) {
    formData.append('file', file);
  } else {
    throw new Error('Please select an image file or demo sample to analyze.');
  }

  const res = await fetch(`${API_BASE_URL}/analyze`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    let errorDetail = 'Analysis request failed';
    try {
      const errJson = await res.json();
      errorDetail = errJson.detail || errJson.message || errorDetail;
    } catch {
      errorDetail = `Server responded with status ${res.status}`;
    }
    throw new Error(errorDetail);
  }

  return res.json();
}

export async function getHistory(): Promise<HistoryItem[]> {
  const res = await fetch(`${API_BASE_URL}/history`);
  if (!res.ok) {
    throw new Error('Failed to retrieve analysis history');
  }
  return res.json();
}

export async function getHistoryDetail(analysisId: string): Promise<AnalysisResponse> {
  const res = await fetch(`${API_BASE_URL}/history/${encodeURIComponent(analysisId)}`);
  if (!res.ok) {
    throw new Error(`Failed to load analysis record ${analysisId}`);
  }
  return res.json();
}

export async function deleteHistoryItem(analysisId: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/history/${encodeURIComponent(analysisId)}`, {
    method: 'DELETE',
  });
  if (!res.ok) {
    throw new Error(`Failed to delete record ${analysisId}`);
  }
}

// ---------------------------------------------------------------------------
// Doctor Appointments & Critical Referrals
// ---------------------------------------------------------------------------

export async function getAppointments(status?: string, priority?: string): Promise<any[]> {
  const params = new URLSearchParams();
  if (status && status !== 'ALL') params.append('status', status);
  if (priority && priority !== 'ALL') params.append('priority', priority);
  const queryStr = params.toString() ? `?${params.toString()}` : '';
  const res = await fetch(`${API_BASE_URL}/appointments${queryStr}`);
  if (!res.ok) {
    throw new Error('Failed to retrieve booked appointments');
  }
  return res.json();
}

export async function getAppointmentDetail(identifier: string): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/appointments/${encodeURIComponent(identifier)}`);
  if (!res.ok) {
    throw new Error(`Appointment not found for ${identifier}`);
  }
  return res.json();
}

export async function bookDoctorAppointment(payload: {
  analysis_id?: string;
  patient_id?: string;
  patient_name?: string;
  dr_grade?: number;
  severity_level?: string;
  clinical_reason?: string;
  action_required?: string;
  priority?: string;
  doctor_name?: string;
  scheduled_time?: string;
}): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/appointments/book`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to book doctor appointment');
  }
  return res.json();
}

export async function updateAppointmentStatus(appointmentId: string, status: string): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/appointments/${encodeURIComponent(appointmentId)}/status`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status }),
  });
  if (!res.ok) {
    throw new Error('Failed to update appointment status');
  }
  return res.json();
}

export async function deleteAppointment(appointmentId: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/appointments/${encodeURIComponent(appointmentId)}`, {
    method: 'DELETE',
  });
  if (!res.ok) {
    throw new Error('Failed to delete appointment');
  }
}


