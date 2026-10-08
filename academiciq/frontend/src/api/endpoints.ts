/**
 * Typed API endpoint functions for all AcademicIQ modules.
 */
import { apiClient } from './client'
import type {
  AIInsight, AttentionScore, EvidenceNode, LongitudinalProfile,
  LoginRequest, ResultUpload, Student, StudentListResponse,
  TokenResponse, WhatIfRequest, WhatIfResult,
} from '@/types'

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------
export const authApi = {
  login: (data: LoginRequest) =>
    apiClient.post<TokenResponse>('/auth/login', data),
  refresh: (refreshToken: string) =>
    apiClient.post<{ access_token: string; token_type: string; expires_in: number }>(
      '/auth/refresh', { refresh_token: refreshToken }
    ),
  logout: () => apiClient.post('/auth/logout'),
}

// ---------------------------------------------------------------------------
// Students
// ---------------------------------------------------------------------------
export const studentsApi = {
  list: (params?: Record<string, unknown>) =>
    apiClient.get<StudentListResponse>('/students', { params }),
  get: (id: string) => apiClient.get<Student>(`/students/${id}`),
  create: (data: Partial<Student>) => apiClient.post<Student>('/students', data),
  update: (id: string, data: Partial<Student>) =>
    apiClient.put<Student>(`/students/${id}`, data),
}

// ---------------------------------------------------------------------------
// Profile / Longitudinal Academic Profile
// ---------------------------------------------------------------------------
export const profileApi = {
  get: (studentId: string) =>
    apiClient.get<LongitudinalProfile>(`/profile/student/${studentId}`),
}

// ---------------------------------------------------------------------------
// Results
// ---------------------------------------------------------------------------
export const resultsApi = {
  upload: (formData: FormData) =>
    apiClient.post<ResultUpload>('/results/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  listUploads: () => apiClient.get<ResultUpload[]>('/results/uploads'),
  getUpload: (id: string) => apiClient.get<ResultUpload>(`/results/uploads/${id}`),
  getValidation: (id: string) =>
    apiClient.get(`/results/uploads/${id}/validation`),
  updateRecord: (uploadId: string, recordId: string, data: Record<string, unknown>) =>
    apiClient.put(`/results/uploads/${uploadId}/records/${recordId}`, data),
  commit: (id: string) =>
    apiClient.post(`/results/uploads/${id}/commit`),
  reject: (id: string, reason?: string) =>
    apiClient.post(`/results/uploads/${id}/reject`, { reason }),
}

// ---------------------------------------------------------------------------
// Analytics
// ---------------------------------------------------------------------------
export const analyticsApi = {
  student: (id: string, examinationId: string) =>
    apiClient.get(`/analytics/student/${id}`, { params: { examination_id: examinationId } }),
  subject: (id: string, examinationId: string) =>
    apiClient.get(`/analytics/subject/${id}`, { params: { examination_id: examinationId } }),
  class: (sectionId: string, examinationId: string) =>
    apiClient.get(`/analytics/class/${sectionId}`, { params: { examination_id: examinationId } }),
  semesterCompare: (studentId: string, fromExamId: string, toExamId: string) =>
    apiClient.get('/analytics/semester/compare', {
      params: { student_id: studentId, from_examination_id: fromExamId, to_examination_id: toExamId },
    }),
}

// ---------------------------------------------------------------------------
// Intelligence
// ---------------------------------------------------------------------------
export const intelligenceApi = {
  attention: (examinationId: string, band?: string) =>
    apiClient.get<AttentionScore[]>('/intelligence/attention', {
      params: { examination_id: examinationId, band },
    }),
  computeAttention: (studentId: string, examinationId: string, sectionId?: string) =>
    apiClient.post<AttentionScore>(`/intelligence/attention/compute/${studentId}`, undefined, {
      params: { examination_id: examinationId, section_id: sectionId },
    }),
}

// ---------------------------------------------------------------------------
// Evidence
// ---------------------------------------------------------------------------
export const evidenceApi = {
  getNode: (nodeId: string) =>
    apiClient.get<EvidenceNode>(`/evidence/${nodeId}`),
  getInsightChain: (insightId: string) =>
    apiClient.get(`/evidence/insight/${insightId}`),
}

// ---------------------------------------------------------------------------
// Interventions
// ---------------------------------------------------------------------------
export const interventionsApi = {
  list: (params?: Record<string, unknown>) =>
    apiClient.get('/interventions', { params }),
  create: (data: Record<string, unknown>) =>
    apiClient.post('/interventions', data),
  review: (id: string, action: string, data?: Record<string, unknown>) =>
    apiClient.patch(`/interventions/${id}`, { action, ...data }),
}

// ---------------------------------------------------------------------------
// Simulation
// ---------------------------------------------------------------------------
export const simulationApi = {
  whatIf: (data: WhatIfRequest) =>
    apiClient.post<WhatIfResult>('/simulation/what-if', data),
  getScenario: (id: string) =>
    apiClient.get<WhatIfResult>(`/simulation/${id}`),
}

// ---------------------------------------------------------------------------
// AI Insights
// ---------------------------------------------------------------------------
export const aiApi = {
  list: (entityType: string, entityId: string) =>
    apiClient.get<AIInsight[]>('/ai/insights', { params: { entity_type: entityType, entity_id: entityId } }),
  generate: (entityType: string, entityId: string, examinationId?: string) =>
    apiClient.post<AIInsight>('/ai/insights/generate', {
      entity_type: entityType,
      entity_id: entityId,
      examination_id: examinationId,
    }),
}

// ---------------------------------------------------------------------------
// Reports
// ---------------------------------------------------------------------------
export const reportsApi = {
  studentReport: (id: string, format: 'pdf' | 'xlsx' | 'csv' = 'pdf') =>
    apiClient.get(`/reports/student/${id}`, {
      params: { format },
      responseType: 'blob',
    }),
  classReport: (sectionId: string, examinationId: string, format: 'pdf' | 'xlsx' = 'pdf') =>
    apiClient.get(`/reports/class/${sectionId}`, {
      params: { examination_id: examinationId, format },
      responseType: 'blob',
    }),
}
