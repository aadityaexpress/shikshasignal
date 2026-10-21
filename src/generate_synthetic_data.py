"""
Synthetic Data Generator for ShikshaSignal Prototype

Generates:
1. students.csv (~100 fictional students in SCH-001 across Grades 1-3)
2. assessments.csv (Assessment events with multiple skill records, baseline + follow-up)
3. attendance.csv (Contextual attendance dates)
4. interventions.csv (Teacher support activities linked to flagged skills)
5. invalid_assessments.csv (Separate test fixture with deliberate errors)
"""

import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "synthetic"
FIXTURES_DIR = Path(__file__).resolve().parent.parent / "data" / "fixtures"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

# Grade to applicable skills mapping
GRADE_SKILLS = {
    1: [
        ("letter_recognition", "Letter Recognition", "literacy"),
        ("word_reading", "Word Reading", "literacy"),
        ("number_recognition", "Number Recognition", "numeracy"),
        ("addition", "Addition", "numeracy"),
    ],
    2: [
        ("word_reading", "Word Reading", "literacy"),
        ("sentence_reading", "Sentence Reading", "literacy"),
        ("number_recognition", "Number Recognition", "numeracy"),
        ("place_value", "Place Value", "numeracy"),
        ("addition", "Addition", "numeracy"),
        ("subtraction", "Subtraction", "numeracy"),
    ],
    3: [
        ("sentence_reading", "Sentence Reading", "literacy"),
        ("reading_comprehension", "Reading Comprehension", "literacy"),
        ("place_value", "Place Value", "numeracy"),
        ("addition", "Addition", "numeracy"),
        ("subtraction", "Subtraction", "numeracy"),
    ]
}


def generate_all():
    students = []
    # 1. Generate 100 students
    for i in range(1, 101):
        stu_id = f"STU-{i:04d}"
        if i <= 34:
            grade = 1
        elif i <= 67:
            grade = 2
        else:
            grade = 3
        students.append({"student_id": stu_id, "school_id": "SCH-001", "grade": grade})

    with open(OUTPUT_DIR / "students.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["student_id", "school_id", "grade"])
        writer.writeheader()
        writer.writerows(students)
    print(f"Generated {len(students)} students in students.csv")

    # 2. Generate Assessments
    # Baseline: 2026-09-05 (Event ASMT-0001 to ASMT-0100)
    # Follow-up: 2026-09-25 for some students (Event ASMT-0200+)
    assessment_records = []
    record_counter = 1
    asmt_event_counter = 1

    interventions = []
    intervention_counter = 1

    student_flagged_skills = {}

    for stu in students:
        s_id = stu["student_id"]
        grade = stu["grade"]
        skills = GRADE_SKILLS[grade]

        baseline_event_id = f"ASMT-{asmt_event_counter:04d}"
        asmt_event_counter += 1
        baseline_date = "2026-09-05"

        flagged_for_stu = []

        for skill_code, skill_name, domain in skills:
            # Score distribution:
            # ~60% score well (4 or 5 / 5)
            # ~20% score borderline 3 / 5 (meets threshold 60%, does NOT trigger flag)
            # ~20% score low (1 or 2 / 5, triggers flag)
            roll = random.random()
            if roll < 0.20:
                score = random.choice([1, 2])
                flagged_for_stu.append((skill_code, skill_name, domain))
            elif roll < 0.40:
                score = 3  # exactly 60%
            else:
                score = random.choice([4, 5])

            rec_id = f"REC-{record_counter:05d}"
            record_counter += 1

            prof = "proficient" if score >= 4 else ("emerging" if score == 3 else "needs_review")

            assessment_records.append({
                "record_id": rec_id,
                "assessment_id": baseline_event_id,
                "student_id": s_id,
                "assessment_date": baseline_date,
                "assessment_source": "classroom_check",
                "assessment_version": "FLN-MVP-v1",
                "domain": domain,
                "skill_code": skill_code,
                "skill_name": skill_name,
                "score": score,
                "max_score": 5,
                "proficiency_level": prof,
                "data_source": "synthetic_demo"
            })

        student_flagged_skills[s_id] = flagged_for_stu

    # Generate interventions and follow-up assessments for a subset of flagged students
    reassessed_students = []
    for s_id, flagged_skills in student_flagged_skills.items():
        if flagged_skills and random.random() < 0.50:
            # Create an intervention for the first flagged skill
            skill_code, skill_name, domain = flagged_skills[0]
            int_id = f"INT-{intervention_counter:04d}"
            intervention_counter += 1
            int_date = "2026-09-15"

            # 70% chance follow-up assessment occurred
            has_followup = random.random() < 0.70
            followup_asmt_id = f"ASMT-{asmt_event_counter:04d}" if has_followup else ""

            if has_followup:
                asmt_event_counter += 1
                reassessed_students.append((s_id, followup_asmt_id, skill_code, skill_name, domain))

            interventions.append({
                "intervention_id": int_id,
                "student_id": s_id,
                "intervention_date": int_date,
                "skill_code": skill_code,
                "intervention_type": f"targeted_{skill_code}_practice",
                "teacher_note_non_identifying": f"Conducted targeted 15-minute small-group remediation on {skill_name}.",
                "followup_assessment_id": followup_asmt_id
            })

    # Add follow-up assessment records
    for s_id, followup_asmt_id, skill_code, skill_name, domain in reassessed_students:
        rec_id = f"REC-{record_counter:05d}"
        record_counter += 1
        # Progress: mostly improved to 3, 4, or 5
        improved_score = random.choice([3, 4, 4, 5])
        prof = "proficient" if improved_score >= 4 else "emerging"

        assessment_records.append({
            "record_id": rec_id,
            "assessment_id": followup_asmt_id,
            "student_id": s_id,
            "assessment_date": "2026-09-25",
            "assessment_source": "classroom_check",
            "assessment_version": "FLN-MVP-v1",
            "domain": domain,
            "skill_code": skill_code,
            "skill_name": skill_name,
            "score": improved_score,
            "max_score": 5,
            "proficiency_level": prof,
            "data_source": "synthetic_demo"
        })

    with open(OUTPUT_DIR / "assessments.csv", "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "record_id", "assessment_id", "student_id", "assessment_date",
            "assessment_source", "assessment_version", "domain", "skill_code",
            "skill_name", "score", "max_score", "proficiency_level", "data_source"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(assessment_records)
    print(f"Generated {len(assessment_records)} assessment records in assessments.csv")

    with open(OUTPUT_DIR / "interventions.csv", "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "intervention_id", "student_id", "intervention_date", "skill_code",
            "intervention_type", "teacher_note_non_identifying", "followup_assessment_id"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(interventions)
    print(f"Generated {len(interventions)} interventions in interventions.csv")

    # 3. Attendance CSV (5 dates across September)
    attendance_dates = ["2026-09-01", "2026-09-02", "2026-09-03", "2026-09-04", "2026-09-05"]
    attendance_records = []
    for stu in students:
        s_id = stu["student_id"]
        for dt in attendance_dates:
            status = "present" if random.random() < 0.90 else "absent"
            attendance_records.append({
                "student_id": s_id,
                "attendance_date": dt,
                "attendance_status": status,
                "data_source": "synthetic_demo"
            })

    with open(OUTPUT_DIR / "attendance.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["student_id", "attendance_date", "attendance_status", "data_source"])
        writer.writeheader()
        writer.writerows(attendance_records)
    print(f"Generated {len(attendance_records)} attendance records in attendance.csv")

    # 4. Generate Deliberately Invalid Records Test Fixture
    invalid_rows = [
        # 1. Negative score
        {
            "record_id": "REC-ERR-001", "assessment_id": "ASMT-ERR-01", "student_id": "STU-0001",
            "assessment_date": "2026-09-05", "assessment_source": "classroom_check",
            "assessment_version": "FLN-MVP-v1", "domain": "literacy", "skill_code": "word_reading",
            "skill_name": "Word Reading", "score": -1, "max_score": 5, "proficiency_level": "emerging",
            "data_source": "synthetic_demo", "expected_issue": "ERR_NEGATIVE_SCORE"
        },
        # 2. Score exceeds max_score
        {
            "record_id": "REC-ERR-002", "assessment_id": "ASMT-ERR-01", "student_id": "STU-0002",
            "assessment_date": "2026-09-05", "assessment_source": "classroom_check",
            "assessment_version": "FLN-MVP-v1", "domain": "literacy", "skill_code": "word_reading",
            "skill_name": "Word Reading", "score": 7, "max_score": 5, "proficiency_level": "proficient",
            "data_source": "synthetic_demo", "expected_issue": "ERR_SCORE_EXCEEDS_MAX"
        },
        # 3. Missing student_id
        {
            "record_id": "REC-ERR-003", "assessment_id": "ASMT-ERR-02", "student_id": "",
            "assessment_date": "2026-09-05", "assessment_source": "classroom_check",
            "assessment_version": "FLN-MVP-v1", "domain": "numeracy", "skill_code": "addition",
            "skill_name": "Addition", "score": 3, "max_score": 5, "proficiency_level": "emerging",
            "data_source": "synthetic_demo", "expected_issue": "ERR_MISSING_STUDENT_ID"
        },
        # 4. Invalid date format
        {
            "record_id": "REC-ERR-004", "assessment_id": "ASMT-ERR-03", "student_id": "STU-0003",
            "assessment_date": "2026-15-40", "assessment_source": "classroom_check",
            "assessment_version": "FLN-MVP-v1", "domain": "numeracy", "skill_code": "addition",
            "skill_name": "Addition", "score": 3, "max_score": 5, "proficiency_level": "emerging",
            "data_source": "synthetic_demo", "expected_issue": "ERR_INVALID_DATE"
        },
        # 5. Unknown skill code not in catalog
        {
            "record_id": "REC-ERR-005", "assessment_id": "ASMT-ERR-04", "student_id": "STU-0004",
            "assessment_date": "2026-09-05", "assessment_source": "classroom_check",
            "assessment_version": "FLN-MVP-v1", "domain": "literacy", "skill_code": "quantum_physics",
            "skill_name": "Quantum Physics", "score": 4, "max_score": 5, "proficiency_level": "proficient",
            "data_source": "synthetic_demo", "expected_issue": "ERR_UNKNOWN_SKILL_CODE"
        },
        # 6. Zero max_score (division by zero risk)
        {
            "record_id": "REC-ERR-006", "assessment_id": "ASMT-ERR-05", "student_id": "STU-0005",
            "assessment_date": "2026-09-05", "assessment_source": "classroom_check",
            "assessment_version": "FLN-MVP-v1", "domain": "numeracy", "skill_code": "place_value",
            "skill_name": "Place Value", "score": 0, "max_score": 0, "proficiency_level": "emerging",
            "data_source": "synthetic_demo", "expected_issue": "ERR_ZERO_MAX_SCORE"
        },
        # 7. Non-pseudonymous student ID violating privacy protocol
        {
            "record_id": "REC-ERR-007", "assessment_id": "ASMT-ERR-06", "student_id": "Aaditya_Sharma",
            "assessment_date": "2026-09-05", "assessment_source": "classroom_check",
            "assessment_version": "FLN-MVP-v1", "domain": "literacy", "skill_code": "sentence_reading",
            "skill_name": "Sentence Reading", "score": 4, "max_score": 5, "proficiency_level": "proficient",
            "data_source": "synthetic_demo", "expected_issue": "ERR_NON_PSEUDONYMOUS_ID"
        }
    ]

    with open(FIXTURES_DIR / "invalid_assessments.csv", "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "record_id", "assessment_id", "student_id", "assessment_date",
            "assessment_source", "assessment_version", "domain", "skill_code",
            "skill_name", "score", "max_score", "proficiency_level", "data_source",
            "expected_issue"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(invalid_rows)
    print(f"Generated {len(invalid_rows)} deliberate error cases in fixtures/invalid_assessments.csv")


if __name__ == "__main__":
    generate_all()
