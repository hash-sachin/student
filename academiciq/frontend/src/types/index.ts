/**
 * AcademicIQ TypeScript types.
 * All metric values carry a MetricLabel per the platform specification.
 */

// ---------------------------------------------------------------------------
// Metric labels (spec Section 3, Principle 2)
// ---------------------------------------------------------------------------
export type MetricLabel = 'OFFICIAL' | 'CALCULATED' | 'ESTIMATED' | 'HYPOTHETICAL'

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------
export interface LoginRequest {
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  refresh_token?: string
  token_type: string
  expires_in: number
}

export interface User {
  id: string
  email: string
  full_name: string
  role: string
  is_active: boolean
}

// ---------------------------------------------------------------------------
// Student
// ---------------------------------------------------------------------------
export type StudentStatus = 'ACTIVE' | 'DISCONTINUED' | 'GRADUATED' | 'ON_LEAVE'

export interface Student {
  id: string
  register_number: string
  university_register_number: string | null
  name: string
  department_id: string
  program_id: string
  batch_id: string
  admission_year: number
  status: StudentStatus
  created_at: string
  updated_at: string
}

export interface StudentListResponse {
  items: Student[]
  total: number
  page: number
  page_size: number
}

// ---------------------------------------------------------------------------
// Academic Attention
// ---------------------------------------------------------------------------
export type AttentionBand = 'NORMAL' | 'MONITOR' | 'ATTENTION' | 'HIGH_ATTENTION'

export interface AttentionFactor {
  id: string
  name: string
  raw_value: string
  points: number
  max_points: number
  evidence: string
  skipped: boolean
  skip_reason: string | null
}

export interface AttentionScore {
  student_id: string
  examination_id: string
  raw_score: number
  band: AttentionBand
  is_partial_score: boolean
  missing_factors: string[]
  factors: AttentionFactor[]
  algorithm_version: string
  metric_label: 'ESTIMATED'
  input_snapshot_hash: string
}

// ---------------------------------------------------------------------------
// Longitudinal Profile
// ---------------------------------------------------------------------------
export interface SemesterMetrics {
  average: number | null
  subjects_passed: number
  subjects_failed: number
  subjects_appeared: number
  metric_label: MetricLabel
}

export interface SubjectResult {
  subject_id: string
  total_marks: number | null
  internal_marks: number | null
  external_marks: number | null
  grade: string | null
  grade_point: number | null
  result_status: string
  is_absent: boolean
  attempt_number: number
  metric_label: 'OFFICIAL'
}

export interface TimelineEntry {
  examination_id: string
  examination_type: string
  academic_year: string
  subject_results: SubjectResult[]
  semester_metrics: SemesterMetrics
  attention: AttentionScore | null
}

export interface LongitudinalProfile {
  student: Student
  profile_note: string
  timeline: TimelineEntry[]
  aggregate_metrics: {
    semesters_with_data: number
    total_arrears: number
    overall_average: number | null
    metric_label: MetricLabel
  }
  detected_patterns: {
    declines: Array<{ from_exam: string; to_exam: string; magnitude: number }>
    improvements: Array<{ from_exam: string; to_exam: string; magnitude: number }>
  }
}

// ---------------------------------------------------------------------------
// What-If Simulation
// ---------------------------------------------------------------------------
export interface SubjectChange {
  subject_id: string
  hypothetical_total_marks: number
}

export interface WhatIfRequest {
  student_id: string
  examination_id: string
  changes: SubjectChange[]
  scenario_label?: string
}

export interface WhatIfSubjectDetail {
  subject_id: string
  subject_code: string
  total_marks: number | null
  grade: string | null
  result_status: string
  metric_label: MetricLabel
  changed?: boolean
}

export interface WhatIfResult {
  scenario_id: string
  student_id: string
  examination_id: string
  current: {
    average: number | null
    subjects_passed: number
    subjects_failed: number
    subject_details: WhatIfSubjectDetail[]
    metric_label: 'OFFICIAL'
  }
  hypothetical: {
    average: number | null
    subjects_passed: number
    subjects_failed: number
    subject_details: WhatIfSubjectDetail[]
    metric_label: 'HYPOTHETICAL'
  }
  delta: {
    average: number | null
    failed_change: number
    metric_label: 'HYPOTHETICAL'
  }
  is_hypothetical: true
  hypothetical_banner: string
  algorithm_version: string
}

// ---------------------------------------------------------------------------
// Upload
// ---------------------------------------------------------------------------
export type UploadStatus =
  | 'QUEUED'
  | 'PROCESSING'
  | 'VALIDATION'
  | 'READY_FOR_REVIEW'
  | 'COMMITTED'
  | 'REJECTED'
  | 'FAILED'

export interface ResultUpload {
  id: string
  file_name: string
  file_hash: string
  file_size_bytes: number
  processing_status: UploadStatus
  validation_status: string | null
  record_count: number | null
  valid_count: number | null
  warning_count: number | null
  error_count: number | null
  unmatched_count: number | null
  parser_name: string | null
  parser_version: string | null
  parser_confidence: number | null
  uploaded_by: string
  created_at: string
}

// ---------------------------------------------------------------------------
// AI Insight
// ---------------------------------------------------------------------------
export interface AIInsight {
  id: string
  entity_type: string
  entity_id: string
  rendered_text: string
  evidence_ids: string[]
  guardrail_passed: boolean
  is_fallback_template: boolean
  model_version: string
  metric_label: 'ESTIMATED'
  created_at: string
}

// ---------------------------------------------------------------------------
// Evidence node
// ---------------------------------------------------------------------------
export interface EvidenceNode {
  id: string
  node_type: string
  entity_id: string | null
  label: string
  depth: number
}
