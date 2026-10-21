"""
Transparent Decision Engine for ShikshaSignal

Implements deterministic, explainable rules for:
1. Insufficient Data Detection
2. Single Assessment Below-Threshold Flagging
3. Repeated Gap Priority Escalation
4. Assessment Comparability Enforcement (Version & Scale)
5. Attendance Independence
6. Teacher Action Card Generation with Pedagogical Micro-Activities

DISCLAIMER:
All thresholds and activities are synthetic demonstration assumptions for prototyping.
They are NOT official NIPUN Bharat, NCERT, or state assessment cut-offs.
"""

from typing import List, Optional, Tuple, Dict
from datetime import date

from src.models.schemas import (
    AssessmentResult,
    AssessmentEvidence,
    AssessmentSignal,
    TeacherActionCard,
    AttendanceRecord,
)
from src.config import DEFAULT_BENCHMARK_THRESHOLD_RATIO

# Rule Identifiers
RULE_INSUFFICIENT_DATA = "RULE_01_INSUFFICIENT_DATA"
RULE_ON_TRACK = "RULE_02_ON_TRACK"
RULE_SINGLE_GAP = "RULE_03_SINGLE_ASSESSMENT_GAP"
RULE_REPEAT_GAP = "RULE_04_REPEATED_GAP_PRIORITY"
RULE_RECOVERY_ON_TRACK = "RULE_05_PROGRESS_RECOVERY"

# Pedagogical Micro-Activities Catalog for the 8 Starter Skills
SKILL_ACTION_CATALOG: Dict[str, Dict[str, str]] = {
    "letter_recognition": {
        "title": "Tactile Sand & Phonics Flashcard Tracing",
        "steps": (
            "1. Present 3-5 focus letter flashcards with clear visual shapes.\n"
            "2. Have student trace letter shape in sand tray while verbalizing the distinct phoneme sound.\n"
            "3. Conduct rapid flashcard identification probe across 3 rounds."
        ),
        "rationale": "Multisensory kinesthetic tracing reinforces orthographic-to-phonological mapping for early letter-sound correspondence.",
        "followup_prompt": "Reassess in 7–10 school days using standard 5-letter recognition probe (Form FLN-MVP-v1)."
    },
    "word_reading": {
        "title": "Phonics Blending Sliders & CVC Word Cards",
        "steps": (
            "1. Use a physical letter slider to blend consonant-vowel-consonant (CVC) sounds.\n"
            "2. Guide the child to elongate vowel sounds before joining final consonants.\n"
            "3. Provide 5 decodable practice word cards for independent oral reading."
        ),
        "rationale": "Explicit blending practice bridges discrete letter-sound knowledge into continuous word decoding fluency.",
        "followup_prompt": "Reassess in 7–10 school days using 5-word reading check (Form FLN-MVP-v1)."
    },
    "sentence_reading": {
        "title": "Paired Guided Reading with Pointer Wand",
        "steps": (
            "1. Teacher and student read a short 2-line decodable sentence in unison.\n"
            "2. Student uses a finger or pointer to track word-by-word pacing.\n"
            "3. Student reads sentence independently; teacher gently prompts on stalled words."
        ),
        "rationale": "Choral and guided paired reading models sentence cadence, reduces anxiety, and builds automatic phrase tracking.",
        "followup_prompt": "Reassess in 10–14 school days with a 2-sentence classroom oral reading check."
    },
    "reading_comprehension": {
        "title": "Picture-Assisted 'Who / What / Where' Story Prompting",
        "steps": (
            "1. Read a 3-sentence illustrated narrative together.\n"
            "2. Ask direct questions: 'Who is in the story? What did they do? Where did they go?'\n"
            "3. Have student point to the illustration and sentence confirming their response."
        ),
        "rationale": "Grounding textual questions in concrete visual references scaffolds literal recall and comprehension monitoring.",
        "followup_prompt": "Reassess in 10–14 school days with a short 3-question passage check."
    },
    "number_recognition": {
        "title": "Concrete Quantity Matching & Number Cards",
        "steps": (
            "1. Place counting pebbles/counters in groups of 1 to 20.\n"
            "2. Have student match the group to the corresponding written numeral card.\n"
            "3. Practice flashcard naming of random numerals within the target range."
        ),
        "rationale": "Linking cardinal quantity directly to symbolic numeral representation solidifies early number sense.",
        "followup_prompt": "Reassess in 7–10 school days using 5-numeral identification check."
    },
    "place_value": {
        "title": "Bundling Sticks (Tens and Ones) & Ten-Frames",
        "steps": (
            "1. Use matchsticks/straws and rubber bands to bundle groups of 10.\n"
            "2. Demonstrate numbers as 'Bundles of Ten' and 'Loose Ones' (e.g., 23 = 2 bundles + 3 loose).\n"
            "3. Have student construct 3 given numbers using bundles and ten-frame mats."
        ),
        "rationale": "Concrete manipulatives make the abstract base-10 positional system tangible before pencil-and-paper arithmetic.",
        "followup_prompt": "Reassess in 10–14 school days using tens/ones visual representation probe."
    },
    "addition": {
        "title": "Floor Number Line Hopscotch & Counter Steps",
        "steps": (
            "1. Draw or lay out a 1-20 number line on the classroom floor.\n"
            "2. State addition problem (e.g., 4 + 3); student stands on 4 and hops forward 3 spaces.\n"
            "3. Student records the equation and outcome on slate or worksheet."
        ),
        "rationale": "Kinesthetic movement along a physical number line builds an intuitive mental model of addition as forward counting.",
        "followup_prompt": "Reassess in 7–10 school days using 5 single/double-digit addition problems."
    },
    "subtraction": {
        "title": "'Take-Away' Counter Sets & Backward Number Line",
        "steps": (
            "1. Count out a starting set of beads/counters (e.g., 7).\n"
            "2. Physically remove the subtrahend count (e.g., remove 3) and place into a basket.\n"
            "3. Count remaining counters; confirm with backward steps on a desk number line."
        ),
        "rationale": "Direct physical reduction of objects prevents confusion between addition and subtraction concepts.",
        "followup_prompt": "Reassess in 7–10 school days using 5 subtraction problems."
    }
}


def are_assessments_comparable(a1: AssessmentResult, a2: AssessmentResult) -> Tuple[bool, Optional[str]]:
    """
    Comparability Guardrail:
    Two assessments can only be compared for longitudinal trajectories if:
    1. Same skill code
    2. Same assessment form/version
    3. Same maximum score scale
    """
    if a1.skill_code != a2.skill_code:
        return False, f"Incompatible skills: '{a1.skill_code}' vs '{a2.skill_code}'"
    if a1.assessment_version != a2.assessment_version:
        return False, f"Incompatible assessment versions: '{a1.assessment_version}' vs '{a2.assessment_version}'"
    if a1.max_score != a2.max_score:
        return False, f"Incompatible score scales: max_score {a1.max_score} vs {a2.max_score}"
    return True, None


def evaluate_skill_signal(
    student_id: str,
    skill_code: str,
    skill_name: str,
    domain: str,
    assessments: List[AssessmentResult],
    benchmark_threshold_ratio: float = DEFAULT_BENCHMARK_THRESHOLD_RATIO,
    attendance_records: Optional[List[AttendanceRecord]] = None
) -> AssessmentSignal:
    """
    Evaluates learning-gap status with 100% transparent, explainable logic.
    Attendance records, if provided, are purely attached as contextual metadata
    and NEVER affect or alter flag determinations.
    """
    # Filter assessments for this specific student and skill
    relevant = [a for a in assessments if a.student_id == student_id and a.skill_code == skill_code]
    # Sort chronologically by assessment_date
    relevant.sort(key=lambda a: a.assessment_date)

    # Format attendance context string if provided (Contextual Only)
    att_context_str: Optional[str] = None
    if attendance_records is not None:
        stu_att = [r for r in attendance_records if r.student_id == student_id]
        if stu_att:
            present_count = sum(1 for r in stu_att if r.attendance_status == "present")
            total_count = len(stu_att)
            rate = (present_count / total_count) if total_count > 0 else 0.0
            att_context_str = (
                f"Contextual attendance: {present_count}/{total_count} ({rate:.0%}) sessions recorded present. "
                "Notice: Attendance is contextual only and does not influence learning-gap determination."
            )
        else:
            att_context_str = "No attendance records available for this student. (Contextual only)"

    # Rule 1: Insufficient Data check
    if not relevant:
        return AssessmentSignal(
            student_id=student_id,
            skill_code=skill_code,
            skill_name=skill_name,
            domain=domain,
            status="insufficient_data",
            triggering_rule=RULE_INSUFFICIENT_DATA,
            explanation="Insufficient evidence: No valid assessment records exist for this skill.",
            benchmark_threshold_ratio=benchmark_threshold_ratio,
            evidence_history=[],
            attendance_context=att_context_str
        )

    # Build evidence list
    evidence_list = [
        AssessmentEvidence(
            record_id=a.record_id,
            assessment_id=a.assessment_id,
            assessment_date=a.assessment_date,
            assessment_version=a.assessment_version,
            score=a.score,
            max_score=a.max_score,
            score_ratio=a.score_ratio
        )
        for a in relevant
    ]

    latest = relevant[-1]
    latest_ratio = latest.score_ratio
    # Unambiguous boundary check: strictly < threshold triggers review
    latest_below_threshold = latest_ratio < benchmark_threshold_ratio

    # If only one assessment is available
    if len(relevant) == 1:
        if latest_below_threshold:
            return AssessmentSignal(
                student_id=student_id,
                skill_code=skill_code,
                skill_name=skill_name,
                domain=domain,
                status="needs_teacher_review",
                triggering_rule=RULE_SINGLE_GAP,
                explanation=(
                    f"Assessment on {latest.assessment_date} scored {latest.score:.1f}/{latest.max_score:.1f} "
                    f"({latest_ratio:.0%}), which is below the synthetic benchmark threshold of {benchmark_threshold_ratio:.0%}."
                ),
                benchmark_threshold_ratio=benchmark_threshold_ratio,
                evidence_history=evidence_list,
                attendance_context=att_context_str
            )
        else:
            return AssessmentSignal(
                student_id=student_id,
                skill_code=skill_code,
                skill_name=skill_name,
                domain=domain,
                status="on_track",
                triggering_rule=RULE_ON_TRACK,
                explanation=(
                    f"Assessment on {latest.assessment_date} scored {latest.score:.1f}/{latest.max_score:.1f} "
                    f"({latest_ratio:.0%}), meeting the benchmark threshold of {benchmark_threshold_ratio:.0%}."
                ),
                benchmark_threshold_ratio=benchmark_threshold_ratio,
                evidence_history=evidence_list,
                attendance_context=att_context_str
            )

    # Two or more assessments: Check comparability between the two most recent
    previous = relevant[-2]
    comparable, reason = are_assessments_comparable(previous, latest)

    if not comparable:
        # Incomparable assessments cannot be used for repeated-gap trajectory
        comp_note = (
            f"Comparability Notice: Latest assessment ({latest.assessment_version}, max_score {latest.max_score}) "
            f"cannot be directly compared with prior assessment on {previous.assessment_date} "
            f"({previous.assessment_version}, max_score {previous.max_score}). Reason: {reason}."
        )
        if latest_below_threshold:
            return AssessmentSignal(
                student_id=student_id,
                skill_code=skill_code,
                skill_name=skill_name,
                domain=domain,
                status="needs_teacher_review",
                triggering_rule=RULE_SINGLE_GAP,
                explanation=(
                    f"Latest assessment on {latest.assessment_date} scored {latest.score:.1f}/{latest.max_score:.1f} "
                    f"({latest_ratio:.0%}), which is below the benchmark ({benchmark_threshold_ratio:.0%}). "
                    "Multi-assessment trend cannot be computed due to version/scale incompatibility."
                ),
                benchmark_threshold_ratio=benchmark_threshold_ratio,
                evidence_history=evidence_list,
                comparability_notes=comp_note,
                attendance_context=att_context_str
            )
        else:
            return AssessmentSignal(
                student_id=student_id,
                skill_code=skill_code,
                skill_name=skill_name,
                domain=domain,
                status="on_track",
                triggering_rule=RULE_ON_TRACK,
                explanation=(
                    f"Latest assessment on {latest.assessment_date} scored {latest.score:.1f}/{latest.max_score:.1f} "
                    f"({latest_ratio:.0%}), meeting benchmark threshold ({benchmark_threshold_ratio:.0%})."
                ),
                benchmark_threshold_ratio=benchmark_threshold_ratio,
                evidence_history=evidence_list,
                comparability_notes=comp_note,
                attendance_context=att_context_str
            )

    # Assessments are comparable:
    previous_ratio = previous.score_ratio
    previous_below_threshold = previous_ratio < benchmark_threshold_ratio

    # Rule 3: Repeated Gap Priority
    if latest_below_threshold and previous_below_threshold:
        return AssessmentSignal(
            student_id=student_id,
            skill_code=skill_code,
            skill_name=skill_name,
            domain=domain,
            status="priority_for_teacher_review",
            triggering_rule=RULE_REPEAT_GAP,
            explanation=(
                f"Two consecutive comparable assessments show scores below threshold ({benchmark_threshold_ratio:.0%}): "
                f"Prior check on {previous.assessment_date} ({previous.score:.1f}/{previous.max_score:.1f}, {previous_ratio:.0%}) and "
                f"Latest check on {latest.assessment_date} ({latest.score:.1f}/{latest.max_score:.1f}, {latest_ratio:.0%}). "
                "Elevated to priority for teacher review."
            ),
            benchmark_threshold_ratio=benchmark_threshold_ratio,
            evidence_history=evidence_list,
            attendance_context=att_context_str
        )

    # Rule 5: Recovery / Progress on-track
    if not latest_below_threshold and previous_below_threshold:
        return AssessmentSignal(
            student_id=student_id,
            skill_code=skill_code,
            skill_name=skill_name,
            domain=domain,
            status="on_track",
            triggering_rule=RULE_RECOVERY_ON_TRACK,
            explanation=(
                f"Latest assessment on {latest.assessment_date} ({latest.score:.1f}/{latest.max_score:.1f}, {latest_ratio:.0%}) "
                f"meets the benchmark ({benchmark_threshold_ratio:.0%}), demonstrating progress from prior below-threshold "
                f"assessment on {previous.assessment_date} ({previous.score:.1f}/{previous.max_score:.1f}, {previous_ratio:.0%})."
            ),
            benchmark_threshold_ratio=benchmark_threshold_ratio,
            evidence_history=evidence_list,
            attendance_context=att_context_str
        )

    if latest_below_threshold and not previous_below_threshold:
        return AssessmentSignal(
            student_id=student_id,
            skill_code=skill_code,
            skill_name=skill_name,
            domain=domain,
            status="needs_teacher_review",
            triggering_rule=RULE_SINGLE_GAP,
            explanation=(
                f"Latest assessment on {latest.assessment_date} scored {latest.score:.1f}/{latest.max_score:.1f} "
                f"({latest_ratio:.0%}), which is below the benchmark ({benchmark_threshold_ratio:.0%})."
            ),
            benchmark_threshold_ratio=benchmark_threshold_ratio,
            evidence_history=evidence_list,
            attendance_context=att_context_str
        )

    # Both met/exceeded threshold
    return AssessmentSignal(
        student_id=student_id,
        skill_code=skill_code,
        skill_name=skill_name,
        domain=domain,
        status="on_track",
        triggering_rule=RULE_ON_TRACK,
        explanation=(
            f"Consistent proficiency: Assessment on {latest.assessment_date} scored "
            f"{latest.score:.1f}/{latest.max_score:.1f} ({latest_ratio:.0%}), meeting benchmark ({benchmark_threshold_ratio:.0%})."
        ),
        benchmark_threshold_ratio=benchmark_threshold_ratio,
        evidence_history=evidence_list,
        attendance_context=att_context_str
    )


def generate_action_card(signal: AssessmentSignal, card_id: Optional[str] = None) -> Optional[TeacherActionCard]:
    """
    Generates an explainable Teacher Action Card for signals that require teacher review.
    Returns None if the student skill is on_track or insufficient_data.
    """
    if signal.status not in ("needs_teacher_review", "priority_for_teacher_review"):
        return None

    activity_info = SKILL_ACTION_CATALOG.get(signal.skill_code)
    if not activity_info:
        # Fallback activity if unmapped
        activity_info = {
            "title": f"Targeted Small-Group Practice for {signal.skill_name}",
            "steps": "1. Review fundamental concepts using concrete visual aids.\n2. Practice 5 guided exercises with immediate feedback.",
            "rationale": "Direct guided practice scaffolds foundational mastery.",
            "followup_prompt": "Reassess in 7–10 school days."
        }

    c_id = card_id or f"CARD-{signal.student_id}-{signal.skill_code}"

    return TeacherActionCard(
        card_id=c_id,
        student_id=signal.student_id,
        skill_code=signal.skill_code,
        skill_name=signal.skill_name,
        status=signal.status,
        triggering_rule=signal.triggering_rule,
        evidence=signal.evidence_history,
        suggested_activity_title=activity_info["title"],
        suggested_activity_steps=activity_info["steps"],
        activity_rationale=activity_info["rationale"],
        followup_prompt=activity_info["followup_prompt"]
    )
