"""
Unit & Integration Tests for Phase 2: Rule Engine and Persistence Layer

Tests:
1. Insufficient data: zero assessment or invalid assessment case
2. Threshold boundary: scores exactly at (3/5), above (4/5), below (2/5)
3. Single below-threshold assessment flag (needs_teacher_review)
4. Two consecutive comparable below-threshold assessments (priority_for_teacher_review)
5. Recovery after a subsequent score meets the threshold (on_track)
6. Mismatched assessment versions and score scales (comparability guardrail)
7. Attendance independence (attendance does not alter flag status)
8. Action-card coverage for all 8 FLN skills
9. Duplicate CSV import handling (skip with audit log)
10. Database persistence across connection close and restart
11. Intervention-to-reassessment linkage and score progress delta
"""

import sys
import unittest
import tempfile
import shutil
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.models.schemas import (
    AssessmentResult,
    AttendanceRecord,
    Student,
    InterventionRecord,
    ValidationIssue,
)
from src.models.database import DatabaseManager
from src.engine.rules import (
    evaluate_skill_signal,
    generate_action_card,
    are_assessments_comparable,
    SKILL_ACTION_CATALOG,
    RULE_INSUFFICIENT_DATA,
    RULE_ON_TRACK,
    RULE_SINGLE_GAP,
    RULE_REPEAT_GAP,
    RULE_RECOVERY_ON_TRACK,
)
from src.engine.validator import DataValidator
from src.config import SYNTHETIC_DIR, DEFAULT_BENCHMARK_THRESHOLD_RATIO


class TestRuleEngineAndPersistence(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for isolated database testing
        self.test_dir = tempfile.mkdtemp()
        self.test_db_path = Path(self.test_dir) / "test_shikshasignal.db"
        self.db = DatabaseManager(self.test_db_path)
        self.validator = DataValidator(SYNTHETIC_DIR / "skill_catalog.csv")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _make_asmt(
        self,
        record_id="REC-001",
        assessment_id="ASMT-001",
        student_id="STU-0001",
        asmt_date="2026-09-01",
        skill_code="word_reading",
        score=2.0,
        max_score=5.0,
        version="FLN-MVP-v1"
    ) -> AssessmentResult:
        return AssessmentResult(
            record_id=record_id,
            assessment_id=assessment_id,
            student_id=student_id,
            assessment_date=date.fromisoformat(asmt_date),
            assessment_source="classroom_check",
            assessment_version=version,
            domain="literacy",
            skill_code=skill_code,
            skill_name="Word Reading",
            score=score,
            max_score=max_score,
            data_source="synthetic_demo"
        )

    # 1. No assessment case -> insufficient_data
    def test_01_no_assessment_insufficient_data(self):
        signal = evaluate_skill_signal(
            student_id="STU-0001",
            skill_code="word_reading",
            skill_name="Word Reading",
            domain="literacy",
            assessments=[]
        )
        self.assertEqual(signal.status, "insufficient_data")
        self.assertEqual(signal.triggering_rule, RULE_INSUFFICIENT_DATA)
        self.assertEqual(len(signal.evidence_history), 0)
        # Action card must not be generated
        card = generate_action_card(signal)
        self.assertIsNone(card)

    # 2. Threshold boundary: 3/5 vs 4/5 vs 2/5
    def test_02_threshold_boundary_evaluation(self):
        # Exactly 3/5 = 0.60 (meets 60% benchmark) -> on_track
        asmt_3 = self._make_asmt(record_id="R-3", score=3.0, max_score=5.0)
        signal_3 = evaluate_skill_signal("STU-0001", "word_reading", "Word Reading", "literacy", [asmt_3])
        self.assertEqual(signal_3.status, "on_track")
        self.assertEqual(signal_3.triggering_rule, RULE_ON_TRACK)

        # Above threshold: 4/5 = 0.80 -> on_track
        asmt_4 = self._make_asmt(record_id="R-4", score=4.0, max_score=5.0)
        signal_4 = evaluate_skill_signal("STU-0001", "word_reading", "Word Reading", "literacy", [asmt_4])
        self.assertEqual(signal_4.status, "on_track")

        # Below threshold: 2/5 = 0.40 -> needs_teacher_review
        asmt_2 = self._make_asmt(record_id="R-2", score=2.0, max_score=5.0)
        signal_2 = evaluate_skill_signal("STU-0001", "word_reading", "Word Reading", "literacy", [asmt_2])
        self.assertEqual(signal_2.status, "needs_teacher_review")
        self.assertEqual(signal_2.triggering_rule, RULE_SINGLE_GAP)

    # 3. Single below-threshold assessment flag
    def test_03_single_below_threshold_flag(self):
        asmt = self._make_asmt(record_id="R-1", score=1.0, max_score=5.0)
        signal = evaluate_skill_signal("STU-0001", "word_reading", "Word Reading", "literacy", [asmt])
        self.assertEqual(signal.status, "needs_teacher_review")
        self.assertEqual(signal.triggering_rule, RULE_SINGLE_GAP)
        self.assertIn("1.0/5.0", signal.explanation)

        card = generate_action_card(signal)
        self.assertIsNotNone(card)
        self.assertEqual(card.student_id, "STU-0001")
        self.assertEqual(card.skill_code, "word_reading")
        self.assertIn("Phonics Blending", card.suggested_activity_title)
        self.assertIn("not a diagnostic determination", card.teacher_guidance_disclaimer)

    # 4. Two consecutive comparable below-threshold assessments -> priority_for_teacher_review
    def test_04_repeated_gap_priority(self):
        a1 = self._make_asmt(record_id="R-1", assessment_id="A-1", asmt_date="2026-09-01", score=2.0)
        a2 = self._make_asmt(record_id="R-2", assessment_id="A-2", asmt_date="2026-09-15", score=1.0)
        signal = evaluate_skill_signal("STU-0001", "word_reading", "Word Reading", "literacy", [a1, a2])
        
        self.assertEqual(signal.status, "priority_for_teacher_review")
        self.assertEqual(signal.triggering_rule, RULE_REPEAT_GAP)
        self.assertEqual(len(signal.evidence_history), 2)
        self.assertIn("Two consecutive comparable assessments", signal.explanation)

        card = generate_action_card(signal)
        self.assertIsNotNone(card)
        self.assertEqual(card.status, "priority_for_teacher_review")

    # 5. Recovery after a subsequent score meets the threshold -> on_track
    def test_05_recovery_progress_on_track(self):
        a1 = self._make_asmt(record_id="R-1", assessment_id="A-1", asmt_date="2026-09-01", score=2.0) # gap
        a2 = self._make_asmt(record_id="R-2", assessment_id="A-2", asmt_date="2026-09-20", score=4.0) # improved
        signal = evaluate_skill_signal("STU-0001", "word_reading", "Word Reading", "literacy", [a1, a2])

        self.assertEqual(signal.status, "on_track")
        self.assertEqual(signal.triggering_rule, RULE_RECOVERY_ON_TRACK)
        self.assertIn("demonstrating progress", signal.explanation)
        self.assertIsNone(generate_action_card(signal))

    # 6. Mismatched assessment versions and incompatible score scales
    def test_06_incomparable_assessments_guardrail(self):
        # Differing versions
        a1 = self._make_asmt(record_id="R-1", asmt_date="2026-09-01", score=2.0, version="FLN-MVP-v1")
        a2 = self._make_asmt(record_id="R-2", asmt_date="2026-09-15", score=2.0, version="FLN-STATE-PILOT-v2")
        
        comp, reason = are_assessments_comparable(a1, a2)
        self.assertFalse(comp)
        self.assertIn("Incompatible assessment versions", reason)

        # Signal evaluation should not claim repeated gap priority across mismatched versions
        signal = evaluate_skill_signal("STU-0001", "word_reading", "Word Reading", "literacy", [a1, a2])
        self.assertEqual(signal.status, "needs_teacher_review") # evaluates only latest single check
        self.assertNotEqual(signal.status, "priority_for_teacher_review")
        self.assertIsNotNone(signal.comparability_notes)
        self.assertIn("Comparability Notice", signal.comparability_notes)

        # Differing max_score scales
        a3 = self._make_asmt(record_id="R-3", asmt_date="2026-09-20", score=2.0, max_score=10.0, version="FLN-MVP-v1")
        comp_scale, reason_scale = are_assessments_comparable(a1, a3)
        self.assertFalse(comp_scale)
        self.assertIn("Incompatible score scales", reason_scale)

    # 7. Attendance independence: varying attendance does NOT alter flag
    def test_07_attendance_independence(self):
        asmt_low = self._make_asmt(record_id="R-1", score=2.0, max_score=5.0)

        # Perfect attendance (100%)
        att_perfect = [
            AttendanceRecord(student_id="STU-0001", attendance_date=date(2026, 9, 1), attendance_status="present"),
            AttendanceRecord(student_id="STU-0001", attendance_date=date(2026, 9, 2), attendance_status="present"),
        ]
        sig_perfect = evaluate_skill_signal(
            "STU-0001", "word_reading", "Word Reading", "literacy",
            [asmt_low], attendance_records=att_perfect
        )

        # Zero attendance (0%)
        att_zero = [
            AttendanceRecord(student_id="STU-0001", attendance_date=date(2026, 9, 1), attendance_status="absent"),
            AttendanceRecord(student_id="STU-0001", attendance_date=date(2026, 9, 2), attendance_status="absent"),
        ]
        sig_zero = evaluate_skill_signal(
            "STU-0001", "word_reading", "Word Reading", "literacy",
            [asmt_low], attendance_records=att_zero
        )

        # No attendance records
        sig_none = evaluate_skill_signal(
            "STU-0001", "word_reading", "Word Reading", "literacy",
            [asmt_low], attendance_records=None
        )

        # All three must have identical status and triggering_rule
        self.assertEqual(sig_perfect.status, "needs_teacher_review")
        self.assertEqual(sig_zero.status, "needs_teacher_review")
        self.assertEqual(sig_none.status, "needs_teacher_review")
        self.assertEqual(sig_perfect.triggering_rule, sig_zero.triggering_rule)
        self.assertIn("does not influence learning-gap determination", sig_perfect.attendance_context)

    # 8. Action-card coverage for all eight skills
    def test_08_action_card_coverage_all_eight_skills(self):
        catalog = self.validator.skill_catalog
        self.assertEqual(len(catalog), 8)

        for skill_code, item in catalog.items():
            self.assertIn(skill_code, SKILL_ACTION_CATALOG, f"Missing pedagogical activity for {skill_code}")
            activity = SKILL_ACTION_CATALOG[skill_code]
            self.assertTrue(len(activity["title"]) > 0)
            self.assertTrue(len(activity["steps"]) > 0)
            self.assertTrue(len(activity["rationale"]) > 0)
            self.assertTrue(len(activity["followup_prompt"]) > 0)

            # Generate signal and card
            asmt = self._make_asmt(record_id=f"REC-{skill_code}", skill_code=skill_code, score=1.0)
            signal = evaluate_skill_signal("STU-0001", skill_code, item.skill_name, item.domain, [asmt])
            card = generate_action_card(signal)
            self.assertIsNotNone(card)
            self.assertEqual(card.skill_code, skill_code)
            self.assertEqual(card.suggested_activity_title, activity["title"])
            self.assertIn("not a diagnostic determination", card.teacher_guidance_disclaimer)

    # 9. Duplicate CSV import handling (skip with audit log)
    def test_09_duplicate_csv_import_handling(self):
        students_path = SYNTHETIC_DIR / "students.csv"
        valid_students, _ = self.validator.validate_students(students_path)

        # First import
        ins1, dup1 = self.db.insert_students(valid_students, file_name="students.csv")
        self.assertEqual(ins1, 100)
        self.assertEqual(dup1, 0)

        # Re-import identical students
        ins2, dup2 = self.db.insert_students(valid_students, file_name="students.csv")
        self.assertEqual(ins2, 0)
        self.assertEqual(dup2, 100)

        # Verify database still has exactly 100 students (no duplicates inserted)
        counts = self.db.get_counts()
        self.assertEqual(counts["students"], 100)
        # Validation logs recorded duplicate warnings
        self.assertGreaterEqual(counts["validation_logs"], 100)

    # 10. Database persistence across connection close and restart
    def test_10_database_persistence_across_restart(self):
        # Insert student and assessment
        student = Student(student_id="STU-9999", school_id="SCH-001", grade=2)
        asmt = self._make_asmt(record_id="REC-9999", student_id="STU-9999", score=2.0)

        self.db.insert_students([student])
        self.db.insert_assessments([asmt])

        counts_before = self.db.get_counts()
        self.assertEqual(counts_before["students"], 1)
        self.assertEqual(counts_before["assessments"], 1)

        # Close database by deleting manager instance and instantiate a new DatabaseManager
        del self.db
        reopened_db = DatabaseManager(self.test_db_path)

        counts_after = reopened_db.get_counts()
        self.assertEqual(counts_after["students"], 1)
        self.assertEqual(counts_after["assessments"], 1)

        persisted_asmts = reopened_db.get_assessments_for_student("STU-9999")
        self.assertEqual(len(persisted_asmts), 1)
        self.assertEqual(persisted_asmts[0].record_id, "REC-9999")

    # 11. Intervention-to-reassessment linkage and score progress delta
    def test_11_intervention_to_reassessment_linkage(self):
        student = Student(student_id="STU-0042", school_id="SCH-001", grade=1)
        self.db.insert_students([student])

        # Baseline assessment (low score)
        a1 = self._make_asmt(
            record_id="REC-B1", assessment_id="ASMT-BASE", student_id="STU-0042",
            asmt_date="2026-09-01", score=1.0, max_score=5.0
        )
        # Follow-up assessment event ASMT-POST
        a2 = self._make_asmt(
            record_id="REC-F1", assessment_id="ASMT-POST", student_id="STU-0042",
            asmt_date="2026-09-20", score=4.0, max_score=5.0
        )
        self.db.insert_assessments([a1, a2])

        # Intervention linking to follow-up event ASMT-POST
        intv = InterventionRecord(
            intervention_id="INT-0042",
            student_id="STU-0042",
            intervention_date=date(2026, 9, 10),
            skill_code="word_reading",
            intervention_type="guided_word_practice",
            teacher_note_non_identifying="15 minutes daily phonics flashcard review.",
            followup_assessment_id="ASMT-POST"
        )
        self.db.insert_interventions([intv])

        # Retrieve interventions with followup
        results = self.db.get_interventions_with_followup("STU-0042")
        self.assertEqual(len(results), 1)
        item = results[0]
        self.assertTrue(item["has_reassessment"])
        self.assertEqual(item["followup_assessment_id"], "ASMT-POST")
        self.assertIsNotNone(item["followup_details"])
        self.assertEqual(item["followup_details"]["score"], 4.0)
        self.assertAlmostEqual(item["followup_details"]["score_ratio"], 0.80)


if __name__ == "__main__":
    unittest.main()
