"""
Unit and Schema Validation Tests for ShikshaSignal (Phase 1)
"""

import sys
import unittest
from pathlib import Path

# Ensure src can be imported
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import (
    SYNTHETIC_DIR,
    FIXTURES_DIR,
    DEFAULT_BENCHMARK_THRESHOLD_RATIO,
)
from src.models.schemas import (
    AssessmentResult,
    Student,
    SkillCatalogItem,
)
from src.engine.validator import DataValidator


class TestSchemaAndValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator = DataValidator(SYNTHETIC_DIR / "skill_catalog.csv")

    def test_01_skill_catalog_loading(self):
        """Verify the 8 FLN skills are loaded correctly with expected domains."""
        catalog = self.validator.skill_catalog
        self.assertEqual(len(catalog), 8, "Expected exactly 8 skills in the starter taxonomy")
        
        expected_skills = {
            "letter_recognition": "literacy",
            "word_reading": "literacy",
            "sentence_reading": "literacy",
            "reading_comprehension": "literacy",
            "number_recognition": "numeracy",
            "place_value": "numeracy",
            "addition": "numeracy",
            "subtraction": "numeracy",
        }
        for code, domain in expected_skills.items():
            self.assertIn(code, catalog)
            self.assertEqual(catalog[code].domain, domain)
            self.assertAlmostEqual(catalog[code].benchmark_threshold_ratio, 0.60)

    def test_02_students_validation(self):
        """Verify the synthetic student roster: 100 students, grades 1-3, 0 errors."""
        students_path = SYNTHETIC_DIR / "students.csv"
        valid_students, issues = self.validator.validate_students(students_path)
        
        self.assertEqual(len(issues), 0, f"Expected 0 issues in students.csv, got {issues}")
        self.assertEqual(len(valid_students), 100, "Expected exactly 100 students")
        
        grades = {s.grade for s in valid_students}
        self.assertEqual(grades, {1, 2, 3})
        
        # Verify pseudonymous format
        for s in valid_students:
            self.assertTrue(s.student_id.startswith("STU-"))
            self.assertEqual(s.school_id, "SCH-001")

    def test_03_assessments_validation(self):
        """Verify synthetic assessments validate with 0 rejections against student roster."""
        students_path = SYNTHETIC_DIR / "students.csv"
        valid_students, _ = self.validator.validate_students(students_path)
        known_ids = {s.student_id for s in valid_students}

        assessments_path = SYNTHETIC_DIR / "assessments.csv"
        valid_results, issues = self.validator.validate_assessments(assessments_path, known_ids)

        rejections = [i for i in issues if i.validation_status == "rejected"]
        self.assertEqual(len(rejections), 0, f"Expected 0 rejections in assessments.csv, got {rejections}")
        self.assertGreaterEqual(len(valid_results), 400, "Expected at least 400 skill results")

    def test_04_threshold_boundary_logic(self):
        """
        Explicitly verify the score-ratio threshold boundary:
        Ratio = score / max_score
        Trigger condition: ratio < benchmark_threshold_ratio (0.60)
        - 3/5 = 0.60: Does NOT trigger review (meets benchmark)
        - 2/5 = 0.40: DOES trigger review (< 0.60)
        - 4/5 = 0.80: Does NOT trigger review (> 0.60)
        """
        base_kwargs = {
            "record_id": "REC-TEST-1",
            "assessment_id": "ASMT-TEST-1",
            "student_id": "STU-0001",
            "assessment_date": "2026-09-05",
            "assessment_source": "classroom_check",
            "assessment_version": "FLN-MVP-v1",
            "domain": "literacy",
            "skill_code": "word_reading",
            "skill_name": "Word Reading",
            "max_score": 5.0,
            "data_source": "synthetic_demo"
        }

        # Case 1: Exactly 3/5 (60%) -> Should NOT trigger review
        asmt_3_of_5 = AssessmentResult(score=3.0, **base_kwargs)
        self.assertAlmostEqual(asmt_3_of_5.score_ratio, 0.60)
        self.assertFalse(
            asmt_3_of_5.triggers_review(DEFAULT_BENCHMARK_THRESHOLD_RATIO),
            "A score of exactly 3/5 (60%) must NOT trigger a review flag."
        )

        # Case 2: 2/5 (40%) -> Must trigger review
        asmt_2_of_5 = AssessmentResult(score=2.0, **base_kwargs)
        self.assertAlmostEqual(asmt_2_of_5.score_ratio, 0.40)
        self.assertTrue(
            asmt_2_of_5.triggers_review(DEFAULT_BENCHMARK_THRESHOLD_RATIO),
            "A score of 2/5 (40%) must trigger a review flag."
        )

        # Case 3: 4/5 (80%) -> Should NOT trigger review
        asmt_4_of_5 = AssessmentResult(score=4.0, **base_kwargs)
        self.assertAlmostEqual(asmt_4_of_5.score_ratio, 0.80)
        self.assertFalse(asmt_4_of_5.triggers_review(DEFAULT_BENCHMARK_THRESHOLD_RATIO))

        # Case 4: Configurable threshold behavior (e.g. raised to 70%)
        self.assertTrue(
            asmt_3_of_5.triggers_review(threshold_ratio=0.70),
            "Under a configured 70% benchmark, 3/5 (60%) must trigger review."
        )

    def test_05_assessment_event_multi_skill_records(self):
        """
        Verify that multiple skill assessment results can share the same
        assessment_id without collision, each having distinct record_id.
        """
        assessments_path = SYNTHETIC_DIR / "assessments.csv"
        valid_results, _ = self.validator.validate_assessments(assessments_path)
        
        # Group by assessment_id
        event_groups = {}
        for r in valid_results:
            event_groups.setdefault(r.assessment_id, []).append(r)
            
        multi_skill_events = [ev for ev, recs in event_groups.items() if len(recs) > 1]
        self.assertGreater(
            len(multi_skill_events), 0,
            "Expected assessment events containing multiple skill records"
        )
        
        # Verify distinct record_ids within the same event
        first_multi_event = event_groups[multi_skill_events[0]]
        rec_ids = [r.record_id for r in first_multi_event]
        self.assertEqual(len(rec_ids), len(set(rec_ids)), "Record IDs within an event must be unique")

    def test_06_deliberate_invalid_records_fixture(self):
        """
        Validate that the fixture of deliberate errors is properly rejected
        with the expected error codes.
        """
        fixtures_path = FIXTURES_DIR / "invalid_assessments.csv"
        _, issues = self.validator.validate_assessments(fixtures_path)

        rejected_issues = [i for i in issues if i.validation_status == "rejected"]
        self.assertEqual(len(rejected_issues), 7, f"Expected exactly 7 rejected rows, got {len(rejected_issues)}")

        issue_codes = {i.issue_code for i in rejected_issues}
        expected_codes = {
            "ERR_NEGATIVE_SCORE",
            "ERR_SCORE_EXCEEDS_MAX",
            "ERR_MISSING_STUDENT_ID",
            "ERR_INVALID_DATE",
            "ERR_UNKNOWN_SKILL_CODE",
            "ERR_ZERO_MAX_SCORE",
            "ERR_NON_PSEUDONYMOUS_ID",
        }
        self.assertEqual(issue_codes, expected_codes)

    def test_07_validation_log_output(self):
        """Verify that write_validation_log creates an auditable CSV."""
        fixtures_path = FIXTURES_DIR / "invalid_assessments.csv"
        _, issues = self.validator.validate_assessments(fixtures_path)

        log_path = FIXTURES_DIR / "test_validation_log.csv"
        self.validator.write_validation_log(issues, log_path)

        self.assertTrue(log_path.exists())
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            self.assertGreaterEqual(len(lines), 8)  # header + 7 rows
        # Clean up test output
        log_path.unlink()


if __name__ == "__main__":
    unittest.main()
