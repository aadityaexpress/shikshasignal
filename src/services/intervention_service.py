"""
Intervention Service for ShikshaSignal

Coordinates recording pedagogical micro-activities and linking follow-up
reassessment events with comparability and progress delta calculation.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from src.models.database import DatabaseManager
from src.engine.validator import DataValidator
from src.engine.rules import are_assessments_comparable
from src.models.schemas import InterventionRecord, AssessmentResult
from src.models.api_schemas import (
    InterventionCreateRequest,
    ReassessmentLinkRequest,
    ReassessmentLinkResponse,
)


class InterventionService:
    def __init__(self, db: DatabaseManager, validator: DataValidator):
        self.db = db
        self.validator = validator

    def list_interventions(self, student_id: Optional[str] = None) -> List[Dict[str, Any]]:
        return self.db.get_interventions_with_followup(student_id)

    def create_intervention(self, req: InterventionCreateRequest) -> Dict[str, Any]:
        # Validate student exists
        student = self.db.get_student(req.student_id)
        if not student:
            raise ValueError(f"Student '{req.student_id}' does not exist.")

        # Validate skill code exists in catalog
        if req.skill_code not in self.validator.skill_catalog:
            raise ValueError(f"Skill code '{req.skill_code}' is not recognized in the skill catalog.")

        # Generate unique intervention ID
        intv_id = f"INT-{req.student_id}-{int(datetime.now().timestamp() * 1000)}"

        record = InterventionRecord(
            intervention_id=intv_id,
            student_id=req.student_id,
            intervention_date=req.intervention_date,
            skill_code=req.skill_code,
            intervention_type=req.intervention_type,
            teacher_note_non_identifying=req.teacher_note_non_identifying,
            followup_assessment_id=req.followup_assessment_id
        )

        inserted, _ = self.db.insert_interventions([record])
        if inserted == 0:
            raise RuntimeError("Failed to insert intervention record.")

        return {
            "intervention_id": intv_id,
            "student_id": req.student_id,
            "skill_code": req.skill_code,
            "intervention_date": req.intervention_date.isoformat(),
            "intervention_type": req.intervention_type,
            "teacher_note": req.teacher_note_non_identifying,
            "followup_assessment_id": req.followup_assessment_id
        }

    def link_reassessment(self, req: ReassessmentLinkRequest) -> ReassessmentLinkResponse:
        # 1. Retrieve intervention
        intv = self.db.get_intervention_by_id(req.intervention_id)
        if not intv:
            return ReassessmentLinkResponse(
                success=False,
                intervention_id=req.intervention_id,
                followup_assessment_id=req.followup_assessment_id,
                comparable=False,
                message=f"Intervention '{req.intervention_id}' not found."
            )

        student_id = intv["student_id"]
        skill_code = intv["skill_code"]

        # 2. Retrieve follow-up assessment result for this student and skill
        followup = self.db.get_assessment_by_id_and_skill(req.followup_assessment_id, skill_code)
        if not followup or followup.student_id != student_id:
            return ReassessmentLinkResponse(
                success=False,
                intervention_id=req.intervention_id,
                followup_assessment_id=req.followup_assessment_id,
                comparable=False,
                message=(
                    f"Follow-up assessment event '{req.followup_assessment_id}' does not contain "
                    f"a valid record for student '{student_id}' on skill '{skill_code}'."
                )
            )

        # 3. Retrieve student's prior assessments for this skill to find baseline
        history = self.db.get_assessments_for_student(student_id, skill_code)
        # Find preceding assessment before follow-up date
        prior_asmts = [a for a in history if a.assessment_date < followup.assessment_date]
        baseline: Optional[AssessmentResult] = prior_asmts[-1] if prior_asmts else None

        comparable = False
        baseline_ratio: Optional[float] = None
        followup_ratio = followup.score_ratio
        progress_delta: Optional[float] = None
        msg: str = ""

        if baseline:
            baseline_ratio = baseline.score_ratio
            is_comp, reason = are_assessments_comparable(baseline, followup)
            if is_comp:
                comparable = True
                progress_delta = followup_ratio - baseline_ratio
                msg = (
                    f"Reassessment linked successfully. Score progressed from {baseline_ratio:.0%} "
                    f"({baseline.assessment_date}) to {followup_ratio:.0%} ({followup.assessment_date}) "
                    f"[Delta: {progress_delta:+.0%}]. Notice: Educational variation applies; not a clinical claim."
                )
            else:
                comparable = False
                msg = (
                    f"Reassessment linked, but assessments cannot be directly compared. "
                    f"Reason: {reason}. Trajectory delta is not computed."
                )
        else:
            msg = "Reassessment linked. No prior baseline assessment found for comparison."

        # Update intervention record in DB
        self.db.link_reassessment(req.intervention_id, req.followup_assessment_id)

        return ReassessmentLinkResponse(
            success=True,
            intervention_id=req.intervention_id,
            followup_assessment_id=req.followup_assessment_id,
            comparable=comparable,
            baseline_score_ratio=baseline_ratio,
            followup_score_ratio=followup_ratio,
            progress_delta_ratio=progress_delta,
            message=msg
        )
