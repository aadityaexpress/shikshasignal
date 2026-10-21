"""
FastAPI REST API Tests for Phase 3

Tests all endpoints using an isolated temporary SQLite database and TestClient:
- Health & DB status
- CSV import (success, invalid format, duplicate handling)
- Overview aggregation metrics
- Students list, filtering, and 404 handling
- Student skill profiles and action cards
- Intervention creation and follow-up reassessment linkage
- Validation log retrieval
- Persistence across app restart
"""

import sys
import unittest
import tempfile
import shutil
from pathlib import Path
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.web.app import create_app
from src.models.database import DatabaseManager
from src.config import SYNTHETIC_DIR, FIXTURES_DIR


class TestFastAPIEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create a temporary directory and isolated test database
        cls.test_dir = tempfile.mkdtemp()
        cls.test_db_path = Path(cls.test_dir) / "test_api.db"
        cls.db = DatabaseManager(cls.test_db_path)
        cls.app = create_app(db=cls.db)
        cls.client = TestClient(cls.app)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.test_dir, ignore_errors=True)

    # 1. Health and database connectivity
    def test_01_health_check(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["database"], "connected")
        self.assertIn("counts", data)

    # 2. Successful CSV imports (Students, Assessments, Attendance, Interventions)
    def test_02_import_synthetic_datasets(self):
        # Import students.csv
        students_file = SYNTHETIC_DIR / "students.csv"
        with open(students_file, "rb") as f:
            resp = self.client.post(
                "/api/import",
                files={"file": ("students.csv", f, "text/csv")},
                data={"file_type": "students"}
            )
        self.assertEqual(resp.status_code, 200)
        summary = resp.json()
        self.assertEqual(summary["inserted_rows"], 100)
        self.assertEqual(summary["duplicate_rows"], 0)
        self.assertEqual(summary["rejected_rows"], 0)

        # Import assessments.csv
        assessments_file = SYNTHETIC_DIR / "assessments.csv"
        with open(assessments_file, "rb") as f:
            resp = self.client.post(
                "/api/import",
                files={"file": ("assessments.csv", f, "text/csv")},
                data={"file_type": "assessments"}
            )
        self.assertEqual(resp.status_code, 200)
        self.assertGreaterEqual(resp.json()["inserted_rows"], 400)

        # Import attendance.csv
        attendance_file = SYNTHETIC_DIR / "attendance.csv"
        with open(attendance_file, "rb") as f:
            resp = self.client.post(
                "/api/import",
                files={"file": ("attendance.csv", f, "text/csv")},
                data={"file_type": "attendance"}
            )
        self.assertEqual(resp.status_code, 200)
        self.assertGreaterEqual(resp.json()["inserted_rows"], 400)

        # Import interventions.csv
        interventions_file = SYNTHETIC_DIR / "interventions.csv"
        with open(interventions_file, "rb") as f:
            resp = self.client.post(
                "/api/import",
                files={"file": ("interventions.csv", f, "text/csv")},
                data={"file_type": "interventions"}
            )
        self.assertEqual(resp.status_code, 200)
        self.assertGreaterEqual(resp.json()["inserted_rows"], 20)

    # 3. Invalid and malformed CSV imports
    def test_03_invalid_import_handling(self):
        # Non-csv extension rejected
        resp = self.client.post(
            "/api/import",
            files={"file": ("test.pdf", b"fake binary data", "application/pdf")}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Only .csv files are supported", resp.json()["detail"])

        # Deliberately invalid assessments fixture
        invalid_file = FIXTURES_DIR / "invalid_assessments.csv"
        with open(invalid_file, "rb") as f:
            resp = self.client.post(
                "/api/import",
                files={"file": ("invalid_assessments.csv", f, "text/csv")},
                data={"file_type": "assessments"}
            )
        self.assertEqual(resp.status_code, 200)
        summary = resp.json()
        self.assertEqual(summary["rejected_rows"], 7)
        self.assertEqual(summary["inserted_rows"], 0)

    # 4. Duplicate imports handled via duplicate-skip policy
    def test_04_duplicate_import_policy(self):
        students_file = SYNTHETIC_DIR / "students.csv"
        with open(students_file, "rb") as f:
            resp = self.client.post(
                "/api/import",
                files={"file": ("students.csv", f, "text/csv")},
                data={"file_type": "students"}
            )
        self.assertEqual(resp.status_code, 200)
        summary = resp.json()
        # All 100 students were already inserted in test_02, so all 100 are duplicates
        self.assertEqual(summary["inserted_rows"], 0)
        self.assertEqual(summary["duplicate_rows"], 100)

    # 5. Overview aggregates endpoint
    def test_05_overview_endpoint(self):
        resp = self.client.get("/api/overview")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["total_students"], 100)
        self.assertGreater(data["total_assessments"], 400)
        self.assertGreater(data["review_flags_count"] + data["on_track_count"], 0)
        self.assertGreater(data["data_quality_warnings_count"], 0)

    # 6. Student listing and search/grade filtering
    def test_06_students_listing_and_filters(self):
        # All students
        resp = self.client.get("/api/students")
        self.assertEqual(resp.status_code, 200)
        students = resp.json()
        self.assertEqual(len(students), 100)

        # Filter by grade 1
        resp_g1 = self.client.get("/api/students?grade=1")
        self.assertEqual(resp_g1.status_code, 200)
        for s in resp_g1.json():
            self.assertEqual(s["grade"], 1)

        # Search by student_id
        resp_search = self.client.get("/api/students?search=STU-0010")
        self.assertEqual(resp_search.status_code, 200)
        self.assertEqual(len(resp_search.json()), 1)
        self.assertEqual(resp_search.json()[0]["student_id"], "STU-0010")

    # 7. Student individual profile and missing student 404
    def test_07_student_profile(self):
        resp = self.client.get("/api/students/STU-0001")
        self.assertEqual(resp.status_code, 200)
        profile = resp.json()
        self.assertEqual(profile["student"]["student_id"], "STU-0001")
        self.assertIn("skills", profile)
        self.assertIn("attendance_context", profile)
        self.assertIn("interventions", profile)

        # Missing student returns 404
        resp_missing = self.client.get("/api/students/STU-9999")
        self.assertEqual(resp_missing.status_code, 404)
        self.assertIn("not found", resp_missing.json()["detail"])

    # 8. Teacher action cards endpoint
    def test_08_student_actions(self):
        # Find a student who has flagged actions
        resp_list = self.client.get("/api/students")
        flagged_student = None
        for s in resp_list.json():
            if s["flagged_skills_count"] > 0:
                flagged_student = s["student_id"]
                break

        self.assertIsNotNone(flagged_student, "Expected at least one student with flagged skills")
        resp_actions = self.client.get(f"/api/students/{flagged_student}/actions")
        self.assertEqual(resp_actions.status_code, 200)
        actions = resp_actions.json()
        self.assertGreater(len(actions), 0)
        first_action = actions[0]
        self.assertIn("suggested_activity_title", first_action)
        self.assertIn("suggested_activity_steps", first_action)
        self.assertIn("activity_rationale", first_action)
        self.assertIn("not a diagnostic determination", first_action["teacher_guidance_disclaimer"])

        # 404 on missing student
        resp_404 = self.client.get("/api/students/STU-9999/actions")
        self.assertEqual(resp_404.status_code, 404)

    # 9. Interventions listing and creation
    def test_09_interventions_crud(self):
        # List interventions
        resp_list = self.client.get("/api/interventions")
        self.assertEqual(resp_list.status_code, 200)
        self.assertGreater(len(resp_list.json()), 0)

        # Filter by student
        resp_stu = self.client.get("/api/interventions?student_id=STU-0001")
        self.assertEqual(resp_stu.status_code, 200)

        # Create new intervention
        payload = {
            "student_id": "STU-0001",
            "skill_code": "word_reading",
            "intervention_date": "2026-10-01",
            "intervention_type": "guided_word_practice",
            "teacher_note_non_identifying": "Practiced CVC flashcards with sound blending.",
            "followup_assessment_id": None
        }
        resp_create = self.client.post("/api/interventions", json=payload)
        self.assertEqual(resp_create.status_code, 201)
        created = resp_create.json()
        self.assertIn("intervention_id", created)
        self.assertEqual(created["student_id"], "STU-0001")

        # Invalid student_id rejected with 400
        payload_bad_student = payload.copy()
        payload_bad_student["student_id"] = "STU-9999"
        resp_bad = self.client.post("/api/interventions", json=payload_bad_student)
        self.assertEqual(resp_bad.status_code, 400)

        # Invalid skill_code rejected with 400
        payload_bad_skill = payload.copy()
        payload_bad_skill["skill_code"] = "nonexistent_skill"
        resp_bad_skill = self.client.post("/api/interventions", json=payload_bad_skill)
        self.assertEqual(resp_bad_skill.status_code, 400)

    # 10. Reassessment linkage & progress delta
    def test_10_reassessment_linkage(self):
        # Find an intervention that already has a followup_assessment_id from the demo data
        resp_list = self.client.get("/api/interventions")
        target_intv = None
        for item in resp_list.json():
            if item["followup_assessment_id"]:
                target_intv = item
                break

        self.assertIsNotNone(target_intv, "Expected an intervention with follow-up assessment in demo data")

        # Relink / update reassessment event
        payload = {
            "intervention_id": target_intv["intervention_id"],
            "followup_assessment_id": target_intv["followup_assessment_id"]
        }
        resp_link = self.client.post("/api/reassessment", json=payload)
        self.assertEqual(resp_link.status_code, 200)
        link_data = resp_link.json()
        self.assertTrue(link_data["success"])
        self.assertIn("progress_delta_ratio", link_data)

    # 11. Validation-log retrieval
    def test_11_validation_logs_endpoint(self):
        resp = self.client.get("/api/validation-logs?limit=50")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("total_count", data)
        self.assertGreater(data["total_count"], 0)
        self.assertIn("logs", data)

    # 12. Persistence across application restart
    def test_12_persistence_across_restart(self):
        # Count records before restart
        before_resp = self.client.get("/api/health")
        before_counts = before_resp.json()["counts"]

        # Create a completely fresh app and TestClient pointing to the SAME test db
        restarted_app = create_app(db_path=self.test_db_path)
        restarted_client = TestClient(restarted_app)

        after_resp = restarted_client.get("/api/health")
        self.assertEqual(after_resp.status_code, 200)
        after_counts = after_resp.json()["counts"]

        self.assertEqual(before_counts["students"], after_counts["students"])
        self.assertEqual(before_counts["assessments"], after_counts["assessments"])
        self.assertEqual(before_counts["interventions"], after_counts["interventions"])


if __name__ == "__main__":
    unittest.main()
