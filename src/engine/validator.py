"""
Data Validator Engine for ShikshaSignal

Parses, validates, and logs quality checks for incoming CSV records.
Emits clean Pydantic model objects and writes/returns an auditable validation log.
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Set

from src.models.schemas import (
    SkillCatalogItem,
    Student,
    AssessmentResult,
    AttendanceRecord,
    InterventionRecord,
    ValidationIssue
)


class DataValidator:
    def __init__(self, skill_catalog_path: Optional[Path] = None):
        self.skill_catalog: Dict[str, SkillCatalogItem] = {}
        if skill_catalog_path and skill_catalog_path.exists():
            self.load_skill_catalog(skill_catalog_path)

    def load_skill_catalog(self, path: Path) -> List[ValidationIssue]:
        issues = []
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader, start=2):
                try:
                    item = SkillCatalogItem(
                        skill_code=row["skill_code"].strip(),
                        domain=row["domain"].strip(),
                        skill_name=row["skill_name"].strip(),
                        grade_applicability=row["grade_applicability"].strip(),
                        description=row["description"].strip(),
                        mapping_reference=row["mapping_reference"].strip(),
                        benchmark_threshold_ratio=float(row.get("benchmark_threshold_ratio", 0.60))
                    )
                    self.skill_catalog[item.skill_code] = item
                except Exception as e:
                    issues.append(ValidationIssue(
                        row_id=idx,
                        file_name=path.name,
                        validation_status="rejected",
                        issue_code="ERR_CATALOG_PARSE",
                        issue_description=str(e)
                    ))
        return issues

    def validate_students(self, path: Path) -> Tuple[List[Student], List[ValidationIssue]]:
        valid_students: List[Student] = []
        issues: List[ValidationIssue] = []
        seen_ids: Set[str] = set()

        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader, start=2):
                s_id = row.get("student_id", "").strip()
                if not s_id:
                    issues.append(ValidationIssue(
                        row_id=idx, file_name=path.name, validation_status="rejected",
                        issue_code="ERR_MISSING_STUDENT_ID", issue_description="student_id is required"
                    ))
                    continue
                if s_id in seen_ids:
                    issues.append(ValidationIssue(
                        row_id=idx, file_name=path.name, validation_status="rejected",
                        issue_code="ERR_DUPLICATE_STUDENT_ID", issue_description=f"Duplicate student_id: {s_id}"
                    ))
                    continue
                try:
                    student = Student(
                        student_id=s_id,
                        school_id=row.get("school_id", "").strip(),
                        grade=int(row.get("grade", 0))
                    )
                    valid_students.append(student)
                    seen_ids.add(s_id)
                except Exception as e:
                    issues.append(ValidationIssue(
                        row_id=idx, file_name=path.name, validation_status="rejected",
                        issue_code="ERR_STUDENT_VALIDATION", issue_description=str(e)
                    ))

        return valid_students, issues

    def validate_assessments(
        self,
        path: Path,
        known_student_ids: Optional[Set[str]] = None
    ) -> Tuple[List[AssessmentResult], List[ValidationIssue]]:
        valid_results: List[AssessmentResult] = []
        issues: List[ValidationIssue] = []
        seen_record_ids: Set[str] = set()

        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader, start=2):
                rec_id = row.get("record_id", "").strip()
                s_id = row.get("student_id", "").strip()
                asmt_id = row.get("assessment_id", "").strip()
                skill_code = row.get("skill_code", "").strip()

                if not rec_id:
                    issues.append(ValidationIssue(
                        row_id=idx, file_name=path.name, validation_status="rejected",
                        issue_code="ERR_MISSING_RECORD_ID", issue_description="record_id is required"
                    ))
                    continue

                if rec_id in seen_record_ids:
                    issues.append(ValidationIssue(
                        row_id=idx, file_name=path.name, validation_status="rejected",
                        issue_code="ERR_DUPLICATE_RECORD_ID", issue_description=f"Duplicate record_id: {rec_id}"
                    ))
                    continue

                if not s_id:
                    issues.append(ValidationIssue(
                        row_id=idx, file_name=path.name, validation_status="rejected",
                        issue_code="ERR_MISSING_STUDENT_ID", issue_description="student_id is missing"
                    ))
                    continue

                if not s_id.startswith("STU-"):
                    issues.append(ValidationIssue(
                        row_id=idx, file_name=path.name, validation_status="rejected",
                        issue_code="ERR_NON_PSEUDONYMOUS_ID",
                        issue_description=f"student_id '{s_id}' violates pseudonymous privacy requirement; must start with STU-"
                    ))
                    continue

                if known_student_ids and s_id not in known_student_ids:
                    issues.append(ValidationIssue(
                        row_id=idx, file_name=path.name, validation_status="warning",
                        issue_code="WARN_UNREGISTERED_STUDENT",
                        issue_description=f"student_id {s_id} is not in registered student roster"
                    ))

                if self.skill_catalog and skill_code not in self.skill_catalog:
                    issues.append(ValidationIssue(
                        row_id=idx, file_name=path.name, validation_status="rejected",
                        issue_code="ERR_UNKNOWN_SKILL_CODE",
                        issue_description=f"skill_code '{skill_code}' is not recognized in skill catalog"
                    ))
                    continue

                # Parse date
                raw_date = row.get("assessment_date", "").strip()
                try:
                    parsed_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
                except ValueError:
                    issues.append(ValidationIssue(
                        row_id=idx, file_name=path.name, validation_status="rejected",
                        issue_code="ERR_INVALID_DATE",
                        issue_description=f"Date '{raw_date}' does not match YYYY-MM-DD format"
                    ))
                    continue

                # Score checks
                try:
                    score = float(row.get("score", 0))
                    max_score = float(row.get("max_score", 0))
                except ValueError:
                    issues.append(ValidationIssue(
                        row_id=idx, file_name=path.name, validation_status="rejected",
                        issue_code="ERR_NUMERIC_SCORE",
                        issue_description="score and max_score must be numeric values"
                    ))
                    continue

                if max_score <= 0:
                    issues.append(ValidationIssue(
                        row_id=idx, file_name=path.name, validation_status="rejected",
                        issue_code="ERR_ZERO_MAX_SCORE",
                        issue_description=f"max_score must be greater than zero, got {max_score}"
                    ))
                    continue

                if score < 0:
                    issues.append(ValidationIssue(
                        row_id=idx, file_name=path.name, validation_status="rejected",
                        issue_code="ERR_NEGATIVE_SCORE",
                        issue_description=f"score cannot be negative, got {score}"
                    ))
                    continue

                if score > max_score:
                    issues.append(ValidationIssue(
                        row_id=idx, file_name=path.name, validation_status="rejected",
                        issue_code="ERR_SCORE_EXCEEDS_MAX",
                        issue_description=f"score {score} exceeds max_score {max_score}"
                    ))
                    continue

                try:
                    asmt_result = AssessmentResult(
                        record_id=rec_id,
                        assessment_id=asmt_id,
                        student_id=s_id,
                        assessment_date=parsed_date,
                        assessment_source=row.get("assessment_source", "classroom_check").strip(),
                        assessment_version=row.get("assessment_version", "FLN-MVP-v1").strip(),
                        domain=row.get("domain", "").strip(),
                        skill_code=skill_code,
                        skill_name=row.get("skill_name", "").strip(),
                        score=score,
                        max_score=max_score,
                        proficiency_level=row.get("proficiency_level", "").strip() or None,
                        data_source=row.get("data_source", "synthetic_demo").strip()
                    )
                    valid_results.append(asmt_result)
                    seen_record_ids.add(rec_id)
                except Exception as e:
                    issues.append(ValidationIssue(
                        row_id=idx, file_name=path.name, validation_status="rejected",
                        issue_code="ERR_ASSESSMENT_VALIDATION",
                        issue_description=str(e)
                    ))

        return valid_results, issues

    def validate_attendance(
        self,
        path: Path,
        known_student_ids: Optional[Set[str]] = None
    ) -> Tuple[List[AttendanceRecord], List[ValidationIssue]]:
        valid_records: List[AttendanceRecord] = []
        issues: List[ValidationIssue] = []
        seen_keys: Set[Tuple[str, str]] = set()

        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader, start=2):
                s_id = row.get("student_id", "").strip()
                raw_date = row.get("attendance_date", "").strip()
                status = row.get("attendance_status", "").strip().lower()

                if not s_id:
                    issues.append(ValidationIssue(
                        row_id=idx, file_name=path.name, validation_status="rejected",
                        issue_code="ERR_MISSING_STUDENT_ID", issue_description="student_id is required"
                    ))
                    continue

                if not s_id.startswith("STU-"):
                    issues.append(ValidationIssue(
                        row_id=idx, file_name=path.name, validation_status="rejected",
                        issue_code="ERR_NON_PSEUDONYMOUS_ID",
                        issue_description=f"student_id '{s_id}' must start with STU-"
                    ))
                    continue

                if known_student_ids and s_id not in known_student_ids:
                    issues.append(ValidationIssue(
                        row_id=idx, file_name=path.name, validation_status="warning",
                        issue_code="WARN_UNREGISTERED_STUDENT",
                        issue_description=f"student_id {s_id} is not in registered student roster"
                    ))

                try:
                    parsed_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
                except ValueError:
                    issues.append(ValidationIssue(
                        row_id=idx, file_name=path.name, validation_status="rejected",
                        issue_code="ERR_INVALID_DATE",
                        issue_description=f"Date '{raw_date}' does not match YYYY-MM-DD"
                    ))
                    continue

                if status not in ("present", "absent", "unknown"):
                    issues.append(ValidationIssue(
                        row_id=idx, file_name=path.name, validation_status="rejected",
                        issue_code="ERR_INVALID_ATTENDANCE_STATUS",
                        issue_description=f"Invalid attendance_status: '{status}'. Must be present, absent, or unknown."
                    ))
                    continue

                key = (s_id, raw_date)
                if key in seen_keys:
                    issues.append(ValidationIssue(
                        row_id=idx, file_name=path.name, validation_status="warning",
                        issue_code="WARN_DUPLICATE_ATTENDANCE",
                        issue_description=f"Duplicate attendance entry for student {s_id} on {raw_date}."
                    ))
                    continue

                try:
                    rec = AttendanceRecord(
                        student_id=s_id,
                        attendance_date=parsed_date,
                        attendance_status=status,
                        data_source=row.get("data_source", "synthetic_demo").strip()
                    )
                    valid_records.append(rec)
                    seen_keys.add(key)
                except Exception as e:
                    issues.append(ValidationIssue(
                        row_id=idx, file_name=path.name, validation_status="rejected",
                        issue_code="ERR_ATTENDANCE_VALIDATION",
                        issue_description=str(e)
                    ))

        return valid_records, issues

    def validate_interventions(
        self,
        path: Path,
        known_student_ids: Optional[Set[str]] = None
    ) -> Tuple[List[InterventionRecord], List[ValidationIssue]]:
        valid_records: List[InterventionRecord] = []
        issues: List[ValidationIssue] = []
        seen_ids: Set[str] = set()

        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader, start=2):
                intv_id = row.get("intervention_id", "").strip()
                s_id = row.get("student_id", "").strip()
                raw_date = row.get("intervention_date", "").strip()
                skill_code = row.get("skill_code", "").strip()

                if not intv_id:
                    issues.append(ValidationIssue(
                        row_id=idx, file_name=path.name, validation_status="rejected",
                        issue_code="ERR_MISSING_INTERVENTION_ID",
                        issue_description="intervention_id is required"
                    ))
                    continue

                if intv_id in seen_ids:
                    issues.append(ValidationIssue(
                        row_id=idx, file_name=path.name, validation_status="rejected",
                        issue_code="ERR_DUPLICATE_INTERVENTION_ID",
                        issue_description=f"Duplicate intervention_id: {intv_id}"
                    ))
                    continue

                if not s_id:
                    issues.append(ValidationIssue(
                        row_id=idx, file_name=path.name, validation_status="rejected",
                        issue_code="ERR_MISSING_STUDENT_ID",
                        issue_description="student_id is required"
                    ))
                    continue

                if not s_id.startswith("STU-"):
                    issues.append(ValidationIssue(
                        row_id=idx, file_name=path.name, validation_status="rejected",
                        issue_code="ERR_NON_PSEUDONYMOUS_ID",
                        issue_description=f"student_id '{s_id}' must start with STU-"
                    ))
                    continue

                if known_student_ids and s_id not in known_student_ids:
                    issues.append(ValidationIssue(
                        row_id=idx, file_name=path.name, validation_status="warning",
                        issue_code="WARN_UNREGISTERED_STUDENT",
                        issue_description=f"student_id {s_id} is not in registered student roster"
                    ))

                if self.skill_catalog and skill_code not in self.skill_catalog:
                    issues.append(ValidationIssue(
                        row_id=idx, file_name=path.name, validation_status="rejected",
                        issue_code="ERR_UNKNOWN_SKILL_CODE",
                        issue_description=f"skill_code '{skill_code}' is not recognized in skill catalog"
                    ))
                    continue

                try:
                    parsed_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
                except ValueError:
                    issues.append(ValidationIssue(
                        row_id=idx, file_name=path.name, validation_status="rejected",
                        issue_code="ERR_INVALID_DATE",
                        issue_description=f"Date '{raw_date}' does not match YYYY-MM-DD"
                    ))
                    continue

                try:
                    rec = InterventionRecord(
                        intervention_id=intv_id,
                        student_id=s_id,
                        intervention_date=parsed_date,
                        skill_code=skill_code,
                        intervention_type=row.get("intervention_type", "").strip(),
                        teacher_note_non_identifying=row.get("teacher_note_non_identifying", "").strip(),
                        followup_assessment_id=row.get("followup_assessment_id", "").strip() or None
                    )
                    valid_records.append(rec)
                    seen_ids.add(intv_id)
                except Exception as e:
                    issues.append(ValidationIssue(
                        row_id=idx, file_name=path.name, validation_status="rejected",
                        issue_code="ERR_INTERVENTION_VALIDATION",
                        issue_description=str(e)
                    ))

        return valid_records, issues

    def write_validation_log(self, issues: List[ValidationIssue], output_path: Path):
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            fieldnames = ["row_id", "file_name", "validation_status", "issue_code", "issue_description"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for issue in issues:
                writer.writerow(issue.model_dump())
