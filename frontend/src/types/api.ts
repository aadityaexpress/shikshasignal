/**
 * TypeScript Interfaces for ShikshaSignal REST API
 * Strictly mirrors FastAPI / Pydantic schemas without inventing fields.
 */

export type Domain = 'literacy' | 'numeracy';

export type DecisionStatus =
  | 'insufficient_data'
  | 'on_track'
  | 'needs_teacher_review'
  | 'priority_for_teacher_review';

export interface HealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  database: 'connected' | 'disconnected';
  version: string;
  counts: Record<string, number>;
}

export interface OverviewResponse {
  total_students: number;
  total_assessments: number;
  review_flags_count: number;
  priority_flags_count: number;
  insufficient_data_count: number;
  on_track_count: number;
  data_quality_warnings_count: number;
  reassessments_completed_count: number;
  reassessments_pending_count: number;
}

export interface StudentSummary {
  student_id: string;
  school_id: string;
  grade: number;
  overall_status: DecisionStatus;
  flagged_skills_count: number;
  last_assessment_date?: string | null;
}

export interface Student {
  student_id: string;
  school_id: string;
  grade: number;
}

export interface AssessmentEvidence {
  record_id: string;
  assessment_id: string;
  assessment_date: string;
  assessment_version: string;
  score: number;
  max_score: number;
  score_ratio: number;
}

export interface AssessmentSignal {
  student_id: string;
  skill_code: string;
  skill_name: string;
  domain: Domain;
  status: DecisionStatus;
  triggering_rule: string;
  explanation: string;
  benchmark_threshold_ratio: number;
  evidence_history: AssessmentEvidence[];
  comparability_notes?: string | null;
  attendance_context?: string | null;
}

export interface TeacherActionCard {
  card_id: string;
  student_id: string;
  skill_code: string;
  skill_name: string;
  status: 'needs_teacher_review' | 'priority_for_teacher_review';
  triggering_rule: string;
  evidence: AssessmentEvidence[];
  suggested_activity_title: string;
  suggested_activity_steps: string;
  activity_rationale: string;
  followup_prompt: string;
  teacher_guidance_disclaimer: string;
}

export interface FollowupDetails {
  record_id: string;
  date: string;
  score: number;
  max_score: number;
  version: string;
  score_ratio: number;
}

export interface InterventionItem {
  intervention_id: string;
  student_id: string;
  intervention_date: string;
  skill_code: string;
  intervention_type: string;
  teacher_note: string;
  followup_assessment_id?: string | null;
  has_reassessment: boolean;
  followup_details?: FollowupDetails | null;
}

export interface StudentProfileResponse {
  student: Student;
  skills: AssessmentSignal[];
  attendance_context: string;
  interventions: InterventionItem[];
}

export interface InterventionCreateRequest {
  student_id: string;
  skill_code: string;
  intervention_date: string;
  intervention_type: string;
  teacher_note_non_identifying: string;
  followup_assessment_id?: string | null;
}

export interface ReassessmentLinkRequest {
  intervention_id: string;
  followup_assessment_id: string;
}

export interface ReassessmentLinkResponse {
  success: boolean;
  intervention_id: string;
  followup_assessment_id: string;
  comparable: boolean;
  baseline_score_ratio?: number | null;
  followup_score_ratio?: number | null;
  progress_delta_ratio?: number | null;
  message: string;
}

export interface ValidationIssue {
  row_id: number;
  file_name: string;
  validation_status: 'valid' | 'warning' | 'rejected';
  issue_code: string;
  issue_description: string;
}

export interface ImportSummaryResponse {
  file_name: string;
  file_type: string;
  total_rows: number;
  inserted_rows: number;
  duplicate_rows: number;
  rejected_rows: number;
  issues: ValidationIssue[];
}

export interface ValidationLogItem {
  id: number;
  import_id?: number | null;
  row_id: number;
  file_name: string;
  validation_status: string;
  issue_code: string;
  issue_description: string;
  created_at: string;
}

export interface ValidationLogsResponse {
  total_count: number;
  logs: ValidationLogItem[];
}
