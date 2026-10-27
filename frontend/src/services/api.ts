/**
 * Centralized API Service Layer for ShikshaSignal
 */

import {
  HealthResponse,
  OverviewResponse,
  StudentSummary,
  StudentProfileResponse,
  TeacherActionCard,
  InterventionItem,
  InterventionCreateRequest,
  ReassessmentLinkRequest,
  ReassessmentLinkResponse,
  ImportSummaryResponse,
  ValidationLogsResponse,
} from '../types/api';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${BASE_URL}${endpoint}`;
  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        'Accept': 'application/json',
        ...(options.headers || {}),
      },
    });

    if (!res.ok) {
      let errMsg = `Request failed with status ${res.status}`;
      try {
        const errJson = await res.json();
        if (errJson && errJson.detail) {
          errMsg = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
        }
      } catch {
        // Fallback to text
        const text = await res.text();
        if (text) errMsg = text;
      }
      throw new ApiError(errMsg, res.status);
    }

    return (await res.json()) as T;
  } catch (err: unknown) {
    if (err instanceof ApiError) {
      throw err;
    }
    const message = err instanceof Error ? err.message : 'Unknown network error';
    throw new ApiError(`Network error connecting to ShikshaSignal server (${message}). Ensure backend is running on port 8000.`, 0);
  }
}

export const api = {
  getHealth: () => request<HealthResponse>('/health'),

  getOverview: () => request<OverviewResponse>('/overview'),

  getStudents: (grade?: number, search?: string, statusFilter?: string) => {
    const params = new URLSearchParams();
    if (grade) params.append('grade', grade.toString());
    if (search && search.trim()) params.append('search', search.trim());
    if (statusFilter && statusFilter.trim()) params.append('status_filter', statusFilter.trim());
    const query = params.toString() ? `?${params.toString()}` : '';
    return request<StudentSummary[]>(`/students${query}`);
  },

  getStudentProfile: (studentId: string) =>
    request<StudentProfileResponse>(`/students/${encodeURIComponent(studentId)}`),

  getStudentActions: (studentId: string) =>
    request<TeacherActionCard[]>(`/students/${encodeURIComponent(studentId)}/actions`),

  getInterventions: (studentId?: string) => {
    const query = studentId ? `?student_id=${encodeURIComponent(studentId)}` : '';
    return request<InterventionItem[]>(`/interventions${query}`);
  },

  createIntervention: (payload: InterventionCreateRequest) =>
    request<Record<string, unknown>>('/interventions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),

  linkReassessment: (payload: ReassessmentLinkRequest) =>
    request<ReassessmentLinkResponse>('/reassessment', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),

  getValidationLogs: (limit = 100, status?: string) => {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (status) params.append('status', status);
    return request<ValidationLogsResponse>(`/validation-logs?${params.toString()}`);
  },

  importCsv: async (file: File, fileType?: string): Promise<ImportSummaryResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    if (fileType && fileType !== 'auto') {
      formData.append('file_type', fileType);
    }

    const res = await fetch(`${BASE_URL}/import`, {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) {
      let errMsg = `Upload failed (${res.status})`;
      try {
        const errJson = await res.json();
        if (errJson && errJson.detail) errMsg = errJson.detail;
      } catch {
        // fallback
      }
      throw new ApiError(errMsg, res.status);
    }

    return (await res.json()) as ImportSummaryResponse;
  },
};
