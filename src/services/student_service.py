"""
Student Service for ShikshaSignal

Handles querying students, computing aggregated class-view statuses,
and compiling individual student skill profiles and action cards.
"""

from typing import List, Optional, Dict, Any
from src.models.database import DatabaseManager
from src.engine.rules import (
    evaluate_skill_signal,
    generate_action_card,
    SKILL_ACTION_CATALOG
)
from src.engine.validator import DataValidator
from src.models.schemas import (
    Student,
    AssessmentSignal,
    TeacherActionCard,
    AssessmentEvidence,
)
from src.models.api_schemas import (
    StudentSummary,
    StudentProfileResponse,
)


class StudentService:
    def __init__(self, db: DatabaseManager, validator: DataValidator):
        self.db = db
        self.validator = validator

    def list_students(
        self,
        grade: Optional[int] = None,
        search: Optional[str] = None,
        status_filter: Optional[str] = None
    ) -> List[StudentSummary]:
        """
        Lists students matching search and grade filters, calculating
        overall classroom alert status for each student.
        """
        students = self.db.get_students(grade=grade, search=search)
        all_assessments = self.db.get_all_assessments()

        # Group assessments by student_id
        asmt_by_student: Dict[str, List] = {}
        for a in all_assessments:
            asmt_by_student.setdefault(a.student_id, []).append(a)

        catalog = self.validator.skill_catalog
        summaries: List[StudentSummary] = []

        for stu in students:
            stu_asmts = asmt_by_student.get(stu.student_id, [])
            last_date = max((a.assessment_date.isoformat() for a in stu_asmts), default=None)

            # Evaluate signals for skills assessed for this student
            assessed_skills = {a.skill_code for a in stu_asmts}
            if not assessed_skills and catalog:
                # If unassessed, consider applicable skills for grade
                grade_str = str(stu.grade)
                assessed_skills = {
                    code for code, item in catalog.items()
                    if grade_str in item.grade_applicability.split(",")
                }

            signals = []
            for sc in assessed_skills:
                item = catalog.get(sc)
                name = item.skill_name if item else sc
                domain = item.domain if item else "literacy"
                sig = evaluate_skill_signal(stu.student_id, sc, name, domain, stu_asmts)
                signals.append(sig)

            # Determine overall status priority:
            # 1. priority_for_teacher_review
            # 2. needs_teacher_review
            # 3. on_track
            # 4. insufficient_data
            flagged_count = sum(1 for s in signals if s.status in ("needs_teacher_review", "priority_for_teacher_review"))
            has_priority = any(s.status == "priority_for_teacher_review" for s in signals)
            has_review = any(s.status == "needs_teacher_review" for s in signals)
            has_ontrack = any(s.status == "on_track" for s in signals)

            if has_priority:
                overall = "priority_for_teacher_review"
            elif has_review:
                overall = "needs_teacher_review"
            elif has_ontrack:
                overall = "on_track"
            else:
                overall = "insufficient_data"

            if status_filter and overall != status_filter:
                continue

            summaries.append(StudentSummary(
                student_id=stu.student_id,
                school_id=stu.school_id,
                grade=stu.grade,
                overall_status=overall,
                flagged_skills_count=flagged_count,
                last_assessment_date=last_date
            ))

        return summaries

    def get_student_profile(self, student_id: str) -> Optional[StudentProfileResponse]:
        """
        Compiles detailed skill evaluation, attendance context,
        and intervention history for a single student.
        """
        student = self.db.get_student(student_id)
        if not student:
            return None

        asmts = self.db.get_assessments_for_student(student_id)
        attendance = self.db.get_attendance_for_student(student_id)
        interventions = self.db.get_interventions_with_followup(student_id)
        catalog = self.validator.skill_catalog

        # Identify all skills applicable to student grade or assessed
        grade_str = str(student.grade)
        relevant_skills = set()
        for code, item in catalog.items():
            if grade_str in item.grade_applicability.split(","):
                relevant_skills.add(code)
        for a in asmts:
            relevant_skills.add(a.skill_code)

        signals: List[AssessmentSignal] = []
        for sc in sorted(relevant_skills):
            item = catalog.get(sc)
            name = item.skill_name if item else sc
            domain = item.domain if item else "literacy"
            threshold = item.benchmark_threshold_ratio if item else 0.60
            sig = evaluate_skill_signal(
                student_id=student_id,
                skill_code=sc,
                skill_name=name,
                domain=domain,
                assessments=asmts,
                benchmark_threshold_ratio=threshold,
                attendance_records=attendance
            )
            signals.append(sig)

        # Contextual attendance string
        if attendance:
            present = sum(1 for r in attendance if r.attendance_status == "present")
            total = len(attendance)
            pct = (present / total) * 100 if total > 0 else 0
            att_context = f"{present}/{total} sessions present ({pct:.0f}%). Notice: Attendance is contextual only."
        else:
            att_context = "No attendance records available. (Contextual only)"

        return StudentProfileResponse(
            student=student,
            skills=signals,
            attendance_context=att_context,
            interventions=interventions
        )

    def get_student_actions(self, student_id: str) -> Optional[List[TeacherActionCard]]:
        """
        Generates Action Cards for all flagged skills for a student.
        Returns None if student does not exist, empty list if no skills flagged.
        """
        student = self.db.get_student(student_id)
        if not student:
            return None

        asmts = self.db.get_assessments_for_student(student_id)
        catalog = self.validator.skill_catalog

        grade_str = str(student.grade)
        skills_to_check = set()
        for code, item in catalog.items():
            if grade_str in item.grade_applicability.split(","):
                skills_to_check.add(code)
        for a in asmts:
            skills_to_check.add(a.skill_code)

        cards: List[TeacherActionCard] = []
        for sc in sorted(skills_to_check):
            item = catalog.get(sc)
            name = item.skill_name if item else sc
            domain = item.domain if item else "literacy"
            threshold = item.benchmark_threshold_ratio if item else 0.60
            sig = evaluate_skill_signal(student_id, sc, name, domain, asmts, threshold)
            card = generate_action_card(sig)
            if card:
                cards.append(card)

        return cards
