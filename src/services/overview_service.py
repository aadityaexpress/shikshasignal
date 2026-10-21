"""
Overview Service for ShikshaSignal

Aggregates school/cluster-level metrics, flag counts, and data-quality indicators.
"""

from typing import Dict, Any, List
from src.models.database import DatabaseManager
from src.engine.validator import DataValidator
from src.engine.rules import evaluate_skill_signal
from src.models.api_schemas import OverviewResponse


class OverviewService:
    def __init__(self, db: DatabaseManager, validator: DataValidator):
        self.db = db
        self.validator = validator

    def get_overview(self) -> OverviewResponse:
        counts = self.db.get_counts()
        students = self.db.get_students()
        all_assessments = self.db.get_all_assessments()
        catalog = self.validator.skill_catalog

        # Group assessments by student
        asmts_by_student: Dict[str, List] = {}
        for a in all_assessments:
            asmts_by_student.setdefault(a.student_id, []).append(a)

        review_count = 0
        priority_count = 0
        insufficient_count = 0
        ontrack_count = 0

        for stu in students:
            stu_asmts = asmts_by_student.get(stu.student_id, [])
            grade_str = str(stu.grade)

            # Applicable skills for student
            applicable = [
                code for code, item in catalog.items()
                if grade_str in item.grade_applicability.split(",")
            ]

            for sc in applicable:
                item = catalog.get(sc)
                name = item.skill_name if item else sc
                domain = item.domain if item else "literacy"
                threshold = item.benchmark_threshold_ratio if item else 0.60
                sig = evaluate_skill_signal(stu.student_id, sc, name, domain, stu_asmts, threshold)
                
                if sig.status == "priority_for_teacher_review":
                    priority_count += 1
                elif sig.status == "needs_teacher_review":
                    review_count += 1
                elif sig.status == "on_track":
                    ontrack_count += 1
                else:
                    insufficient_count += 1

        # Interventions summary
        interventions = self.db.get_interventions_with_followup()
        completed = sum(1 for i in interventions if i["has_reassessment"])
        pending = len(interventions) - completed

        # Data quality warnings count
        warnings = self.db.get_validation_logs(limit=10000, status="warning")
        warning_count = len(warnings)

        return OverviewResponse(
            total_students=counts["students"],
            total_assessments=counts["assessments"],
            review_flags_count=review_count,
            priority_flags_count=priority_count,
            insufficient_data_count=insufficient_count,
            on_track_count=ontrack_count,
            data_quality_warnings_count=warning_count,
            reassessments_completed_count=completed,
            reassessments_pending_count=pending
        )
