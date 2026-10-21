"""
Pydantic Schemas for ShikshaSignal Data Model

Governs validation for students, skills, assessment results, attendance,
and interventions in accordance with the ShikshaSignal Data Dictionary.
"""

from datetime import date
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator, model_validator


class SkillCatalogItem(BaseModel):
    skill_code: str = Field(..., description="Unique stable skill identifier")
    domain: Literal["literacy", "numeracy"] = Field(..., description="Learning domain")
    skill_name: str = Field(..., description="Human-readable skill label")
    grade_applicability: str = Field(..., description="Comma-separated applicable grades (e.g., '1,2,3')")
    description: str = Field(..., description="Pedagogical description of the skill")
    mapping_reference: str = Field(..., description="Reference to framework learning goal")
    benchmark_threshold_ratio: float = Field(
        default=0.60,
        ge=0.0,
        le=1.0,
        description="Configurable synthetic benchmark ratio (e.g. 0.60). Below this triggers review."
    )


class Student(BaseModel):
    student_id: str = Field(..., description="Pseudonymous unique identifier (e.g., STU-0001)")
    school_id: str = Field(..., description="School identifier (e.g., SCH-001)")
    grade: int = Field(..., ge=1, le=3, description="Grade level (1, 2, or 3)")

    @field_validator("student_id")
    @classmethod
    def validate_pseudonymous_id(cls, v: str) -> str:
        v = v.strip()
        if not v.startswith("STU-"):
            raise ValueError(f"Student ID '{v}' must follow pseudonymous format 'STU-XXXX'")
        return v


class AssessmentResult(BaseModel):
    """
    Represents an individual skill evaluation within an assessment event.
    Multiple skill results can share the same assessment_id (the event)
    without primary key collision.
    """
    record_id: str = Field(..., description="Unique record identifier for this skill result (e.g., REC-0001)")
    assessment_id: str = Field(..., description="Assessment event identifier (e.g., ASMT-0001)")
    student_id: str = Field(..., description="Pseudonymous student ID")
    assessment_date: date = Field(..., description="Date administered (YYYY-MM-DD)")
    assessment_source: str = Field(..., description="Source e.g. classroom_check")
    assessment_version: str = Field(..., description="Version e.g. FLN-MVP-v1 to enforce comparability")
    domain: Literal["literacy", "numeracy"] = Field(..., description="Domain")
    skill_code: str = Field(..., description="Target skill code")
    skill_name: str = Field(..., description="Human-readable skill label")
    score: float = Field(..., ge=0.0, description="Earned score (must be non-negative)")
    max_score: float = Field(..., gt=0.0, description="Maximum possible score (must be > 0)")
    proficiency_level: Optional[str] = Field(None, description="Descriptive level e.g. emerging/proficient")
    data_source: str = Field(default="synthetic_demo", description="Origin of record")

    @field_validator("student_id")
    @classmethod
    def validate_pseudonymous_id(cls, v: str) -> str:
        v = v.strip()
        if not v.startswith("STU-"):
            raise ValueError(f"Student ID '{v}' must follow pseudonymous format 'STU-XXXX'")
        return v

    @model_validator(mode="after")
    def validate_score_within_bounds(self):
        if self.score > self.max_score:
            raise ValueError(f"Score {self.score} cannot exceed max_score {self.max_score}")
        return self

    @property
    def score_ratio(self) -> float:
        return self.score / self.max_score

    def triggers_review(self, threshold_ratio: float = 0.60) -> bool:
        """
        Unambiguous boundary check:
        Strictly ratio < threshold_ratio triggers a review.
        A score of exactly 3/5 (0.60) does NOT trigger a review.
        """
        return self.score_ratio < threshold_ratio


class AttendanceRecord(BaseModel):
    student_id: str = Field(..., description="Pseudonymous student ID")
    attendance_date: date = Field(..., description="Date of attendance (YYYY-MM-DD)")
    attendance_status: Literal["present", "absent", "unknown"] = Field(..., description="Attendance status")
    data_source: str = Field(default="synthetic_demo", description="Data origin")


class InterventionRecord(BaseModel):
    intervention_id: str = Field(..., description="Unique intervention identifier (e.g., INT-0001)")
    student_id: str = Field(..., description="Pseudonymous student ID")
    intervention_date: date = Field(..., description="Date intervention delivered (YYYY-MM-DD)")
    skill_code: str = Field(..., description="Target skill code")
    intervention_type: str = Field(..., description="Activity category (e.g., guided_word_practice)")
    teacher_note_non_identifying: str = Field(..., description="Non-identifying pedagogical note")
    followup_assessment_id: Optional[str] = Field(None, description="Linked followup assessment event ID, if reassessed")


class ValidationIssue(BaseModel):
    row_id: int
    file_name: str
    validation_status: Literal["valid", "warning", "rejected"]
    issue_code: str
    issue_description: str


class AssessmentEvidence(BaseModel):
    record_id: str
    assessment_id: str
    assessment_date: date
    assessment_version: str
    score: float
    max_score: float
    score_ratio: float


class AssessmentSignal(BaseModel):
    student_id: str
    skill_code: str
    skill_name: str
    domain: str
    status: Literal[
        "insufficient_data",
        "on_track",
        "needs_teacher_review",
        "priority_for_teacher_review"
    ]
    triggering_rule: str
    explanation: str
    benchmark_threshold_ratio: float
    evidence_history: list[AssessmentEvidence] = Field(default_factory=list)
    comparability_notes: Optional[str] = None
    attendance_context: Optional[str] = None


class TeacherActionCard(BaseModel):
    card_id: str
    student_id: str
    skill_code: str
    skill_name: str
    status: Literal["needs_teacher_review", "priority_for_teacher_review"]
    triggering_rule: str
    evidence: list[AssessmentEvidence]
    suggested_activity_title: str
    suggested_activity_steps: str
    activity_rationale: str
    followup_prompt: str
    teacher_guidance_disclaimer: str = (
        "This recommendation is a decision-support aid for teacher review, "
        "not a diagnostic determination or psychological assessment."
    )

