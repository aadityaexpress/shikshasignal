"""
SQLite Persistence Layer for ShikshaSignal

Provides reliable local storage, transaction safety, duplicate handling,
and linkage between interventions and reassessment events.
"""

import sqlite3
import shutil
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from src.config import DATABASE_PATH, RAW_DIR
from src.models.schemas import (
    Student,
    AssessmentResult,
    AttendanceRecord,
    InterventionRecord,
    ValidationIssue,
)


class DatabaseManager:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DATABASE_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def init_db(self):
        """Initializes database tables if they do not exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Raw imports audit table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS raw_imports (
                    import_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_name TEXT NOT NULL,
                    raw_path TEXT NOT NULL,
                    imported_at TEXT NOT NULL,
                    total_rows INTEGER NOT NULL,
                    inserted_rows INTEGER NOT NULL,
                    duplicate_rows INTEGER NOT NULL,
                    rejected_rows INTEGER NOT NULL
                );
            """)

            # Validation logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS validation_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    import_id INTEGER,
                    row_id INTEGER NOT NULL,
                    file_name TEXT NOT NULL,
                    validation_status TEXT NOT NULL,
                    issue_code TEXT NOT NULL,
                    issue_description TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (import_id) REFERENCES raw_imports (import_id)
                );
            """)

            # Students table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    student_id TEXT PRIMARY KEY,
                    school_id TEXT NOT NULL,
                    grade INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );
            """)

            # Assessment Results table (unique record_id, grouped by assessment_id)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS assessment_results (
                    record_id TEXT PRIMARY KEY,
                    assessment_id TEXT NOT NULL,
                    student_id TEXT NOT NULL,
                    assessment_date TEXT NOT NULL,
                    assessment_source TEXT NOT NULL,
                    assessment_version TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    skill_code TEXT NOT NULL,
                    skill_name TEXT NOT NULL,
                    score REAL NOT NULL,
                    max_score REAL NOT NULL,
                    proficiency_level TEXT,
                    data_source TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (student_id) REFERENCES students (student_id)
                );
            """)

            # Attendance table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT NOT NULL,
                    attendance_date TEXT NOT NULL,
                    attendance_status TEXT NOT NULL,
                    data_source TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE (student_id, attendance_date),
                    FOREIGN KEY (student_id) REFERENCES students (student_id)
                );
            """)

            # Interventions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS interventions (
                    intervention_id TEXT PRIMARY KEY,
                    student_id TEXT NOT NULL,
                    intervention_date TEXT NOT NULL,
                    skill_code TEXT NOT NULL,
                    intervention_type TEXT NOT NULL,
                    teacher_note_non_identifying TEXT NOT NULL,
                    followup_assessment_id TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (student_id) REFERENCES students (student_id)
                );
            """)

            # Indexes for performant queries
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_asmt_stu_skill ON assessment_results (student_id, skill_code);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_asmt_date ON assessment_results (assessment_date);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_intervention_stu ON interventions (student_id, skill_code);")
            conn.commit()

    def store_raw_file(self, source_path: Path) -> Path:
        """Stores a preserved copy of the raw uploaded CSV for auditing."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest_filename = f"{timestamp}_{source_path.name}"
        dest_path = RAW_DIR / dest_filename
        shutil.copy2(source_path, dest_path)
        return dest_path

    def insert_students(
        self,
        students: List[Student],
        import_id: Optional[int] = None,
        file_name: str = "students.csv"
    ) -> Tuple[int, int]:
        """
        Inserts students using duplicate-skip policy.
        Returns (inserted_count, duplicate_count).
        """
        now = datetime.now().isoformat()
        inserted = 0
        duplicates = 0

        with self.get_connection() as conn:
            cursor = conn.cursor()
            for s in students:
                cursor.execute("SELECT 1 FROM students WHERE student_id = ?", (s.student_id,))
                if cursor.fetchone():
                    duplicates += 1
                    cursor.execute("""
                        INSERT INTO validation_logs 
                        (import_id, row_id, file_name, validation_status, issue_code, issue_description, created_at)
                        VALUES (?, ?, ?, 'warning', 'WARN_DUPLICATE_SKIPPED', ?, ?)
                    """, (import_id, 0, file_name, f"Student {s.student_id} already exists; skipped duplicate.", now))
                else:
                    cursor.execute("""
                        INSERT INTO students (student_id, school_id, grade, created_at)
                        VALUES (?, ?, ?, ?)
                    """, (s.student_id, s.school_id, s.grade, now))
                    inserted += 1
            conn.commit()
        return inserted, duplicates

    def insert_assessments(
        self,
        assessments: List[AssessmentResult],
        import_id: Optional[int] = None,
        file_name: str = "assessments.csv"
    ) -> Tuple[int, int]:
        """
        Inserts assessment results using duplicate-skip policy based on record_id.
        Returns (inserted_count, duplicate_count).
        """
        now = datetime.now().isoformat()
        inserted = 0
        duplicates = 0

        with self.get_connection() as conn:
            cursor = conn.cursor()
            for a in assessments:
                cursor.execute("SELECT 1 FROM assessment_results WHERE record_id = ?", (a.record_id,))
                if cursor.fetchone():
                    duplicates += 1
                    cursor.execute("""
                        INSERT INTO validation_logs 
                        (import_id, row_id, file_name, validation_status, issue_code, issue_description, created_at)
                        VALUES (?, ?, ?, 'warning', 'WARN_DUPLICATE_SKIPPED', ?, ?)
                    """, (import_id, 0, file_name, f"Assessment record {a.record_id} already exists; skipped duplicate.", now))
                else:
                    cursor.execute("""
                        INSERT INTO assessment_results (
                            record_id, assessment_id, student_id, assessment_date,
                            assessment_source, assessment_version, domain, skill_code,
                            skill_name, score, max_score, proficiency_level, data_source, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        a.record_id, a.assessment_id, a.student_id, a.assessment_date.isoformat(),
                        a.assessment_source, a.assessment_version, a.domain, a.skill_code,
                        a.skill_name, a.score, a.max_score, a.proficiency_level, a.data_source, now
                    ))
                    inserted += 1
            conn.commit()
        return inserted, duplicates

    def insert_interventions(
        self,
        interventions: List[InterventionRecord],
        import_id: Optional[int] = None,
        file_name: str = "interventions.csv"
    ) -> Tuple[int, int]:
        """
        Inserts interventions with duplicate-skip policy based on intervention_id.
        Returns (inserted_count, duplicate_count).
        """
        now = datetime.now().isoformat()
        inserted = 0
        duplicates = 0

        with self.get_connection() as conn:
            cursor = conn.cursor()
            for intv in interventions:
                cursor.execute("SELECT 1 FROM interventions WHERE intervention_id = ?", (intv.intervention_id,))
                if cursor.fetchone():
                    duplicates += 1
                    cursor.execute("""
                        INSERT INTO validation_logs 
                        (import_id, row_id, file_name, validation_status, issue_code, issue_description, created_at)
                        VALUES (?, ?, ?, 'warning', 'WARN_DUPLICATE_SKIPPED', ?, ?)
                    """, (import_id, 0, file_name, f"Intervention {intv.intervention_id} already exists; skipped duplicate.", now))
                else:
                    cursor.execute("""
                        INSERT INTO interventions (
                            intervention_id, student_id, intervention_date, skill_code,
                            intervention_type, teacher_note_non_identifying, followup_assessment_id, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        intv.intervention_id, intv.student_id, intv.intervention_date.isoformat(),
                        intv.skill_code, intv.intervention_type, intv.teacher_note_non_identifying,
                        intv.followup_assessment_id, now
                    ))
                    inserted += 1
            conn.commit()
        return inserted, duplicates

    def insert_attendance(
        self,
        records: List[AttendanceRecord],
        import_id: Optional[int] = None,
        file_name: str = "attendance.csv"
    ) -> Tuple[int, int]:
        """
        Inserts attendance records with duplicate-skip policy on (student_id, attendance_date).
        Returns (inserted_count, duplicate_count).
        """
        now = datetime.now().isoformat()
        inserted = 0
        duplicates = 0

        with self.get_connection() as conn:
            cursor = conn.cursor()
            for r in records:
                cursor.execute(
                    "SELECT 1 FROM attendance WHERE student_id = ? AND attendance_date = ?",
                    (r.student_id, r.attendance_date.isoformat())
                )
                if cursor.fetchone():
                    duplicates += 1
                else:
                    cursor.execute("""
                        INSERT INTO attendance (student_id, attendance_date, attendance_status, data_source, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (r.student_id, r.attendance_date.isoformat(), r.attendance_status, r.data_source, now))
                    inserted += 1
            conn.commit()
        return inserted, duplicates

    def log_validation_issues(self, issues: List[ValidationIssue], import_id: Optional[int] = None):
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for issue in issues:
                cursor.execute("""
                    INSERT INTO validation_logs 
                    (import_id, row_id, file_name, validation_status, issue_code, issue_description, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    import_id, issue.row_id, issue.file_name,
                    issue.validation_status, issue.issue_code,
                    issue.issue_description, now
                ))
            conn.commit()

    def get_assessments_for_student(self, student_id: str, skill_code: Optional[str] = None) -> List[AssessmentResult]:
        """Retrieves assessment results for a student, optionally filtered by skill."""
        query = "SELECT * FROM assessment_results WHERE student_id = ?"
        params = [student_id]
        if skill_code:
            query += " AND skill_code = ?"
            params.append(skill_code)
        query += " ORDER BY assessment_date ASC"

        results = []
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            for row in cursor.fetchall():
                results.append(AssessmentResult(
                    record_id=row["record_id"],
                    assessment_id=row["assessment_id"],
                    student_id=row["student_id"],
                    assessment_date=date.fromisoformat(row["assessment_date"]),
                    assessment_source=row["assessment_source"],
                    assessment_version=row["assessment_version"],
                    domain=row["domain"],
                    skill_code=row["skill_code"],
                    skill_name=row["skill_name"],
                    score=row["score"],
                    max_score=row["max_score"],
                    proficiency_level=row["proficiency_level"],
                    data_source=row["data_source"]
                ))
        return results

    def get_interventions_with_followup(self, student_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieves interventions (optionally filtered by student_id), linking to the follow-up assessment
        event and calculating score progress delta where available.
        """
        query = """
            SELECT 
                i.intervention_id,
                i.student_id,
                i.intervention_date,
                i.skill_code,
                i.intervention_type,
                i.teacher_note_non_identifying,
                i.followup_assessment_id,
                f.record_id AS followup_record_id,
                f.assessment_date AS followup_date,
                f.score AS followup_score,
                f.max_score AS followup_max_score,
                f.assessment_version AS followup_version
            FROM interventions i
            LEFT JOIN assessment_results f 
                ON i.followup_assessment_id = f.assessment_id 
                AND i.skill_code = f.skill_code
        """
        params = []
        if student_id:
            query += " WHERE i.student_id = ?"
            params.append(student_id)
        query += " ORDER BY i.intervention_date ASC"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            output = []
            for row in cursor.fetchall():
                item = {
                    "intervention_id": row["intervention_id"],
                    "student_id": row["student_id"],
                    "intervention_date": row["intervention_date"],
                    "skill_code": row["skill_code"],
                    "intervention_type": row["intervention_type"],
                    "teacher_note": row["teacher_note_non_identifying"],
                    "followup_assessment_id": row["followup_assessment_id"],
                    "has_reassessment": row["followup_record_id"] is not None,
                }
                if row["followup_record_id"]:
                    item["followup_details"] = {
                        "record_id": row["followup_record_id"],
                        "date": row["followup_date"],
                        "score": row["followup_score"],
                        "max_score": row["followup_max_score"],
                        "version": row["followup_version"],
                        "score_ratio": row["followup_score"] / row["followup_max_score"]
                    }
                else:
                    item["followup_details"] = None
                output.append(item)
            return output

    def get_student(self, student_id: str) -> Optional[Student]:
        """Retrieves a single student by pseudonymous ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT student_id, school_id, grade FROM students WHERE student_id = ?", (student_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return Student(student_id=row["student_id"], school_id=row["school_id"], grade=row["grade"])

    def get_students(self, grade: Optional[int] = None, search: Optional[str] = None) -> List[Student]:
        """Retrieves students with optional grade filtering and search term."""
        query = "SELECT student_id, school_id, grade FROM students WHERE 1=1"
        params = []
        if grade is not None:
            query += " AND grade = ?"
            params.append(grade)
        if search:
            query += " AND (student_id LIKE ? OR school_id LIKE ?)"
            term = f"%{search.strip()}%"
            params.extend([term, term])
        query += " ORDER BY student_id ASC"

        students = []
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            for row in cursor.fetchall():
                students.append(Student(
                    student_id=row["student_id"],
                    school_id=row["school_id"],
                    grade=row["grade"]
                ))
        return students

    def get_attendance_for_student(self, student_id: str) -> List[AttendanceRecord]:
        """Retrieves attendance records for a student ordered by date."""
        records = []
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT student_id, attendance_date, attendance_status, data_source "
                "FROM attendance WHERE student_id = ? ORDER BY attendance_date ASC",
                (student_id,)
            )
            for row in cursor.fetchall():
                records.append(AttendanceRecord(
                    student_id=row["student_id"],
                    attendance_date=date.fromisoformat(row["attendance_date"]),
                    attendance_status=row["attendance_status"],
                    data_source=row["data_source"]
                ))
        return records

    def get_all_assessments(self) -> List[AssessmentResult]:
        """Retrieves all assessment records."""
        results = []
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM assessment_results ORDER BY assessment_date ASC")
            for row in cursor.fetchall():
                results.append(AssessmentResult(
                    record_id=row["record_id"],
                    assessment_id=row["assessment_id"],
                    student_id=row["student_id"],
                    assessment_date=date.fromisoformat(row["assessment_date"]),
                    assessment_source=row["assessment_source"],
                    assessment_version=row["assessment_version"],
                    domain=row["domain"],
                    skill_code=row["skill_code"],
                    skill_name=row["skill_name"],
                    score=row["score"],
                    max_score=row["max_score"],
                    proficiency_level=row["proficiency_level"],
                    data_source=row["data_source"]
                ))
        return results

    def get_all_attendance(self) -> List[AttendanceRecord]:
        """Retrieves all attendance records."""
        records = []
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM attendance ORDER BY attendance_date ASC")
            for row in cursor.fetchall():
                records.append(AttendanceRecord(
                    student_id=row["student_id"],
                    attendance_date=date.fromisoformat(row["attendance_date"]),
                    attendance_status=row["attendance_status"],
                    data_source=row["data_source"]
                ))
        return records

    def get_intervention_by_id(self, intervention_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single intervention by its ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM interventions WHERE intervention_id = ?", (intervention_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "intervention_id": row["intervention_id"],
                "student_id": row["student_id"],
                "intervention_date": row["intervention_date"],
                "skill_code": row["skill_code"],
                "intervention_type": row["intervention_type"],
                "teacher_note": row["teacher_note_non_identifying"],
                "followup_assessment_id": row["followup_assessment_id"]
            }

    def get_assessment_by_id_and_skill(self, assessment_id: str, skill_code: str) -> Optional[AssessmentResult]:
        """Finds an assessment result matching event assessment_id and skill_code."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM assessment_results WHERE assessment_id = ? AND skill_code = ?",
                (assessment_id, skill_code)
            )
            row = cursor.fetchone()
            if not row:
                return None
            return AssessmentResult(
                record_id=row["record_id"],
                assessment_id=row["assessment_id"],
                student_id=row["student_id"],
                assessment_date=date.fromisoformat(row["assessment_date"]),
                assessment_source=row["assessment_source"],
                assessment_version=row["assessment_version"],
                domain=row["domain"],
                skill_code=row["skill_code"],
                skill_name=row["skill_name"],
                score=row["score"],
                max_score=row["max_score"],
                proficiency_level=row["proficiency_level"],
                data_source=row["data_source"]
            )

    def link_reassessment(self, intervention_id: str, followup_assessment_id: str) -> bool:
        """Links a follow-up assessment ID to an existing intervention."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE interventions SET followup_assessment_id = ? WHERE intervention_id = ?",
                (followup_assessment_id, intervention_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def create_raw_import(
        self,
        file_name: str,
        raw_path: Path,
        total_rows: int,
        inserted_rows: int,
        duplicate_rows: int,
        rejected_rows: int
    ) -> int:
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO raw_imports 
                (file_name, raw_path, imported_at, total_rows, inserted_rows, duplicate_rows, rejected_rows)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (file_name, str(raw_path.name), now, total_rows, inserted_rows, duplicate_rows, rejected_rows))
            conn.commit()
            return cursor.lastrowid

    def get_validation_logs(self, limit: int = 100, status: Optional[str] = None) -> List[Dict[str, Any]]:
        query = "SELECT id, import_id, row_id, file_name, validation_status, issue_code, issue_description, created_at FROM validation_logs WHERE 1=1"
        params = []
        if status:
            query += " AND validation_status = ?"
            params.append(status)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        logs = []
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            for row in cursor.fetchall():
                logs.append({
                    "id": row["id"],
                    "import_id": row["import_id"],
                    "row_id": row["row_id"],
                    "file_name": row["file_name"],
                    "validation_status": row["validation_status"],
                    "issue_code": row["issue_code"],
                    "issue_description": row["issue_description"],
                    "created_at": row["created_at"]
                })
        return logs

    def get_counts(self) -> Dict[str, int]:
        """Returns row counts across all persistent tables."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            students_count = cursor.execute("SELECT COUNT(*) FROM students").fetchone()[0]
            asmt_count = cursor.execute("SELECT COUNT(*) FROM assessment_results").fetchone()[0]
            intv_count = cursor.execute("SELECT COUNT(*) FROM interventions").fetchone()[0]
            att_count = cursor.execute("SELECT COUNT(*) FROM attendance").fetchone()[0]
            val_count = cursor.execute("SELECT COUNT(*) FROM validation_logs").fetchone()[0]
            return {
                "students": students_count,
                "assessments": asmt_count,
                "interventions": intv_count,
                "attendance": att_count,
                "validation_logs": val_count
            }
