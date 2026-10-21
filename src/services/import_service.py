"""
Import Service for ShikshaSignal

Coordinates CSV upload parsing, raw storage auditing, validation,
and persistence through the DatabaseManager.
"""

import csv
import io
import shutil
from pathlib import Path
from typing import Tuple, List, Optional
from datetime import datetime

from src.models.database import DatabaseManager
from src.engine.validator import DataValidator
from src.models.schemas import ValidationIssue
from src.models.api_schemas import ImportSummaryResponse
from src.config import RAW_DIR


class ImportService:
    def __init__(self, db: DatabaseManager, validator: DataValidator):
        self.db = db
        self.validator = validator

    def import_csv_content(
        self,
        file_name: str,
        content_bytes: bytes,
        file_type: Optional[str] = None
    ) -> ImportSummaryResponse:
        """
        Processes an uploaded CSV file.
        1. Saves a raw auditable copy into data/raw/
        2. Detects or verifies file_type
        3. Validates using DataValidator
        4. Inserts into database with duplicate-skip policy
        5. Logs issues and updates raw_imports audit log
        """
        # 1. Save raw copy
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = Path(file_name).name
        raw_filename = f"{timestamp}_{safe_name}"
        raw_path = RAW_DIR / raw_filename
        with open(raw_path, "wb") as f:
            f.write(content_bytes)

        # Decode content
        try:
            text_content = content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text_content = content_bytes.decode("latin-1")

        lines = [line for line in text_content.splitlines() if line.strip()]
        if not lines:
            issue = ValidationIssue(
                row_id=1, file_name=safe_name, validation_status="rejected",
                issue_code="ERR_EMPTY_FILE", issue_description="Uploaded file is empty."
            )
            self.db.log_validation_issues([issue])
            return ImportSummaryResponse(
                file_name=safe_name, file_type=file_type or "unknown",
                total_rows=0, inserted_rows=0, duplicate_rows=0, rejected_rows=0,
                issues=[issue]
            )

        # Auto-detect file_type if not provided
        header = lines[0].lower()
        if not file_type or file_type == "auto":
            if "score" in header and "skill_code" in header:
                file_type = "assessments"
            elif "attendance_status" in header:
                file_type = "attendance"
            elif "intervention_type" in header:
                file_type = "interventions"
            elif "student_id" in header and "grade" in header:
                file_type = "students"
            else:
                file_type = "unknown"

        # Temporary path for validator file processing
        temp_path = raw_path

        inserted = 0
        duplicates = 0
        rejected = 0
        issues: List[ValidationIssue] = []

        # Get known student IDs for referential integrity warning checks
        existing_students = self.db.get_students()
        known_student_ids = {s.student_id for s in existing_students}

        if file_type == "students":
            valid_items, issues = self.validator.validate_students(temp_path)
            rejected = sum(1 for i in issues if i.validation_status == "rejected")
            inserted, duplicates = self.db.insert_students(valid_items, file_name=safe_name)

        elif file_type == "assessments":
            valid_items, issues = self.validator.validate_assessments(temp_path, known_student_ids)
            rejected = sum(1 for i in issues if i.validation_status == "rejected")
            inserted, duplicates = self.db.insert_assessments(valid_items, file_name=safe_name)

        elif file_type == "attendance":
            valid_items, issues = self.validator.validate_attendance(temp_path, known_student_ids)
            rejected = sum(1 for i in issues if i.validation_status == "rejected")
            inserted, duplicates = self.db.insert_attendance(valid_items, file_name=safe_name)

        elif file_type == "interventions":
            valid_items, issues = self.validator.validate_interventions(temp_path, known_student_ids)
            rejected = sum(1 for i in issues if i.validation_status == "rejected")
            inserted, duplicates = self.db.insert_interventions(valid_items, file_name=safe_name)

        else:
            issue = ValidationIssue(
                row_id=1, file_name=safe_name, validation_status="rejected",
                issue_code="ERR_UNRECOGNIZED_SCHEMA",
                issue_description=f"File schema unrecognized. Could not map headers to a valid entity: {lines[0]}"
            )
            issues.append(issue)
            rejected = 1

        total_rows = len(lines) - 1

        # Record in raw_imports table
        import_id = self.db.create_raw_import(
            file_name=safe_name,
            raw_path=raw_path,
            total_rows=total_rows,
            inserted_rows=inserted,
            duplicate_rows=duplicates,
            rejected_rows=rejected
        )

        # Log any validation issues
        if issues:
            self.db.log_validation_issues(issues, import_id=import_id)

        return ImportSummaryResponse(
            file_name=safe_name,
            file_type=file_type,
            total_rows=total_rows,
            inserted_rows=inserted,
            duplicate_rows=duplicates,
            rejected_rows=rejected,
            issues=issues
        )
