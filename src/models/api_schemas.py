"""
Pydantic Schemas for FastAPI Request & Response Payloads
"""

from datetime import date
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field

from src.models.schemas import (
    Student,
    ValidationIssue,
    AssessmentSignal,
    AssessmentEvidence,
    TeacherActionCard,
)


class HealthResponse(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"]
    database: Literal["connected", "disconnected"]
    version: str
    counts: Dict[str, int]


class ImportSummaryResponse(BaseModel):
    file_name: str
    file_type: str
    total_rows: int
    inserted_rows: int
    duplicate_rows: int
    rejected_rows: int
    issues: List[ValidationIssue]


class OverviewResponse(BaseModel):
    total_students: int
    total_assessments: int
    review_flags_count: int
    priority_flags_count: int
    insufficient_data_count: int
    on_track_count: int
    data_quality_warnings_count: int
    reassessments_completed_count: int
    reassessments_pending_count: int


class StudentSummary(BaseModel):
    student_id: str
    school_id: str
    grade: int
    overall_status: Literal["priority_for_teacher_review", "needs_teacher_review", "on_track", "insufficient_data"]
    flagged_skills_count: int
    last_assessment_date: Optional[str] = None


class StudentProfileResponse(BaseModel):
    student: Student
    skills: List[AssessmentSignal]
    attendance_context: str
    interventions: List[Dict[str, Any]]


class InterventionCreateRequest(BaseModel):
    student_id: str = Field(..., description="Pseudonymous student ID (e.g., STU-0001)")
    skill_code: str = Field(..., description="Skill code matching catalog")
    intervention_date: date = Field(..., description="Date delivered (YYYY-MM-DD)")
    intervention_type: str = Field(..., description="Pedagogical activity type")
    teacher_note_non_identifying: str = Field(..., description="Non-identifying teacher notes")
    followup_assessment_id: Optional[str] = Field(None, description="Optional followup assessment event ID")


class ReassessmentLinkRequest(BaseModel):
    intervention_id: str = Field(..., description="Target intervention ID to update")
    followup_assessment_id: str = Field(..., description="Assessment event ID of the follow-up assessment")


class ReassessmentLinkResponse(BaseModel):
    success: bool
    intervention_id: str
    followup_assessment_id: str
    comparable: bool
    baseline_score_ratio: Optional[float] = None
    followup_score_ratio: Optional[float] = None
    progress_delta_ratio: Optional[float] = None
    message: str


class ValidationLogsResponse(BaseModel):
    total_count: int
    logs: List[Dict[str, Any]]
