# TECHFEST 2026–27 | IIT BOMBAY
## THE INDIA @ 71/100 CHALLENGE
### Round 1: Concept Proposal Submission

---

**Theme 2:** Foundational Learning Outcomes  
**Project Title:** **ShikshaSignal** — Learning-Gap Early-Warning & Teacher Decision-Support Layer  
**Document Code:** India71_100_[Team_ID]  

---

## 1. Team & Submission Information

* **Team Name:** [Team Name]
* **Team ID:** [Team ID]
* **Institution:** [Institution / University Name]
* **Team Members:**
  1. Member 1 (Lead): [Name] — [Role: System Architecture & Data Engineering] — [Email / Phone]
  2. Member 2: [Name] — [Role: Pedagogical Rule Modeling & Backend] — [Email / Phone]
  3. Member 3: [Name] — [Role: Frontend & Teacher Usability] — [Email / Phone]
  4. Member 4: [Name] — [Role: Policy Alignment & Impact Evaluation] — [Email / Phone]
* **Contact Email:** [Primary Contact Email]
* **Contact Phone:** [Primary Contact Phone]
* **Codebase & Prototype:** [https://github.com/aadityaexpress/shikshasignal](https://github.com/aadityaexpress/shikshasignal)

---

## 2. Problem Identification

### The Core Implementation Gap
India’s **SDG 4 (Quality Education)** scorecard reflects near-universal elementary school gross enrollment (>98% at primary levels per UDISE+ 2023–24). However, national aggregate indicators conceal a profound learning crisis at the classroom level: **children are physically in school but are not acquiring foundational literacy and numeracy (FLN) skills.** 

The National Education Policy (NEP) 2020 explicitly identifies foundational learning as an urgent national priority, establishing the **NIPUN Bharat Mission** with the goal that every child achieves foundational reading, writing, and mathematical comprehension by Grade 3.

Despite regular administrative data reporting, the lived reality in primary classrooms reveals a critical systemic failure:
> **The Implementation Gap:** Classroom assessment data is routinely collected for compliance, aggregate surveys, and administrative reporting, but it sits dormant in offline registers and siloed dashboards. It is rarely converted into immediate, transparent, and actionable classroom pedagogical decisions for the teacher before learning deficits compound into irreversible dropouts.

### The Underserved Community Affected
* **Primary Beneficiaries:** Children in **Grades 1 to 3** (ages 6 to 9) enrolled in government and government-aided primary schools, especially in rural, tribal, and low-income peri-urban habitations.
* **Secondary Frontline Beneficiaries:** Over **2.5 million primary school teachers** who shoulder multi-grade teaching responsibilities, heavy administrative data-entry burdens, and lack low-bandwidth, diagnostic decision-support tools tailored to specific learner gaps.

---

## 3. Evidence & Ground-Level Context

The severity of the foundational learning gap is corroborated by India's primary diagnostic benchmarks:

1. **ASER 2024 (Annual Status of Education Report, Pratham):**
   * Only **23.4%** of Grade 3 children in rural government schools can read a simple Grade 2 level text.
   * Only **28.6%** of Grade 3 children can solve a basic 2-digit subtraction problem with borrowing.
   * Over **70%** of children enter upper primary schools without grade-appropriate foundational fluency, permanently hampering downstream academic attainment and vocational productivity.

2. **PARAKH Rashtriya Sarvekshan 2024 / Foundational Learning Study (FLS, NCERT):**
   * National benchmarks confirm that a substantial proportion of primary learners perform at the "Below Basic" and "Basic" proficiency tiers.
   * Learning outcome disparities are heavily concentrated in early foundational milestones (phoneme recognition, letter-sound blending, single-digit decomposition, and place value).

3. **UDISE+ (Unified District Information System for Education Plus) & Administrative Registers:**
   * Attendance and terminal marks are diligently recorded, but they fail to provide granular formative skill-level feedback.
   * School-level assessments are retrospective—conducted at the end of the term when it is too late to remediate gaps for that academic cycle.

---

## 4. Existing Ecosystem Analysis & Why the Gap Persists

| Platform / Initiative | Primary Mandate | Systemic Bottleneck / Why Gap Persists |
|---|---|---|
| **UDISE+** | National administrative and infrastructure school census. | Collects high-level school-aggregate data once a year; provides zero formative classroom-level student diagnostic feedback. |
| **DIKSHA FLN** | Repository of digital teaching-learning materials and teacher training courses. | Serves as a static resource repository; lacks an automated diagnostic layer that links a specific child’s formative assessment gap to a recommended micro-activity. |
| **State Assessment Portals (e.g., Nipun Lakshya, SAT)** | Periodic periodic assessment of student outcomes against state competency benchmarks. | Operates primarily as an upward accountability mechanism (ranking blocks/districts) rather than a bottom-up pedagogical decision aid for teachers. Results take weeks to process. |
| **ASER / PARAKH Surveys** | National and state-level sample diagnostics. | Sample-based cross-sectional surveys designed for macro-policy monitoring, not continuous classroom remediation for individual children. |

### Why the Gap Persists
1. **Upward Accountability vs. Point-of-Use Decision Support:** Existing systems prioritize feeding dashboards for district and state administrators rather than empowering the frontline teacher during the instructional hour.
2. **Data Silos & Version Incomparability:** Assessment formats, scoring scales, and form versions vary between state assessments and classroom periodic checks, making longitudinal comparison statistically invalid without standardized normalization.
3. **Absence of Explainable Pedagogical Feedback Loops:** Even when a child is marked "emerging" or "low-scoring", existing tools do not tell the teacher *why* the child struggled or *what specific micro-remediation activity* to execute next.

---

## 5. Proposed Solution: ShikshaSignal

**ShikshaSignal** is an open, privacy-preserving, explainable **early-warning and teacher decision-support layer** designed specifically for Grades 1–3 Foundational Literacy and Numeracy. It bridges the gap between assessment collection and point-of-use classroom action without replacing existing statutory databases.

```
┌────────────────────────────────────────────────────────┐
│                   Data Input Layer                     │
│  - Standardized CSV Ingestion (Offline/Low-Bandwidth)   │
│  - Strict Schema & Boundary Validation Engine          │
│  - Raw Upload Preservation & Auditable Validation Logs │
└──────────────────────────┬─────────────────────────────┘
                           │ Cleaned & Normalized Evidence
┌──────────────────────────▼─────────────────────────────┐
│             Transparent Deterministic Rule Engine      │
│  - Rule 1: Insufficient Data & Missing Evidence Guard  │
│  - Rule 2: Single Below-Threshold Flag (Score < 60%)   │
│  - Rule 3: Repeated Gap Priority (2 Consecutive Checks)│
│  - Rule 4: Comparability Enforcement (Version & Scale) │
│  - Rule 5: Attendance Independence (Non-Causal Context)│
└──────────────────────────┬─────────────────────────────┘
                           │ Explainable Alerts & Decisions
┌──────────────────────────▼─────────────────────────────┐
│          Teacher Decision Support & Tracking UI        │
│  - Classroom Matrix with Pseudonymous IDs (STU-XXXX)   │
│  - Teacher Action Cards with Micro-Activities          │
│  - Closed-Loop Remediation Log & Reassessment Tracker  │
│  - Governance & Data-Quality Auditing Portal           │
└────────────────────────────────────────────────────────┘
```

### Core Technical Innovations & Architectural Pillars

#### 1. Deterministic & Explainable Rules Engine (No Opaque AI)
Rather than relying on black-box predictive algorithms or hallucinations, ShikshaSignal executes 100% deterministic, policy-aligned rules:
* **The 60% Benchmark Ratio Rule:** Ratio = $\frac{\text{score}}{\text{max\_score}}$. A score ratio strictly $< 0.60$ triggers `"Needs Teacher Review"`. A score of exactly $3/5$ ($60\%$) meets the benchmark and does not trigger review.
* **Repeated Evidence Escalation:** If two consecutive *comparable* assessments fall below the benchmark, the status elevates to `"Priority for Teacher Review"`.
* **Comparability Guardrail:** Assessments can only be compared across time if `skill_code`, `assessment_version` (e.g., `FLN-MVP-v1`), and `max_score` scale are identical. Mismatched forms trigger an `"incomparable version"` alert, preventing erroneous trend calculations.
* **Attendance Independence Guardrail:** Attendance data is strictly isolated as contextual metadata. Under no circumstances can low attendance independently trigger, elevate, or suppress a student's learning-gap status.

#### 2. Actionable Point-of-Use Teacher Action Cards
When a learning deficit is flagged, ShikshaSignal immediately generates a structured, printable or mobile-friendly **Teacher Action Card** mapped across the 8 core FLN skills:

| Domain | Competency Skill | Suggested Teacher Micro-Activity | Pedagogical Rationale | Reassessment Window |
|---|---|---|---|---|
| **Literacy** | `letter_recognition` | Tactile Sand Tray & Phonics Flashcard Tracing | Multisensory phoneme-grapheme mapping | 7–10 days |
| **Literacy** | `word_reading` | CVC Phonics Blending Sliders & Decodable Cards | Syllabic elongation and consonant-vowel blending | 7–10 days |
| **Literacy** | `sentence_reading` | Paired Guided Reading with Pointer Wands | Builds oral cadence and left-to-right eye tracking | 10–14 days |
| **Literacy** | `reading_comprehension`| Picture-Supported Who/What/Where Prompting | Scaffolds literal recall using visual anchors | 10–14 days |
| **Numeracy** | `number_recognition` | Concrete Counter Quantity Matching (1–20) | Connects physical set cardinality to numeral symbols | 7–10 days |
| **Numeracy** | `place_value` | Bundling Sticks (Tens and Ones) & Ten-Frames | Grounding base-10 structure before symbolic math | 10–14 days |
| **Numeracy** | `addition` | Floor Number Line Hopscotch & Counter Steps | Spatial kinesthetic visualization of forward addition | 7–10 days |
| **Numeracy** | `subtraction` | Take-Away Counter Baskets & Backward Steps | Physical reduction prevents additive confusion | 7–10 days |

*Every card features an explicit non-diagnostic disclaimer:*  
> *"This recommendation is a decision-support aid for teacher review, not a diagnostic determination or psychological assessment."*

#### 3. Closed-Loop Reassessment Tracking
Teachers log the date and nature of the intervention. When follow-up assessments occur, ShikshaSignal automatically links the post-intervention score to the original event, calculates the score progression delta ($\Delta = \text{ratio}_{\text{post}} - \text{ratio}_{\text{pre}}$), and documents recovery on-track without making unverified causal claims.

#### 4. Privacy by Design & DPDP Act 2023 Compliance
* **Strict Pseudonymisation:** Real child names, Aadhaar numbers, parents' contact numbers, and biometric records are completely excluded. Students are identified strictly through synthetic pseudonymous tokens (`STU-0001`).
* **Non-Stigmatizing Terminology:** Avoids deficit labeling; utilizes neutral statuses (`Needs Review`, `On Track`, `Insufficient Data`).
* **Offline-First & Local Storage:** Operates on lightweight SQLite with zero cloud-database dependencies, ensuring full functionality in rural schools with intermittent electricity and zero internet connectivity.

---

## 6. Technical Implementation & Verified Feasibility

The ShikshaSignal prototype is fully developed, persistent, container-ready, and verified through an automated test suite.

### Tech Stack
* **Backend:** Python 3.10, FastAPI 0.116, Pydantic v2 (Strict Schema Validation), SQLite3 (ACID-compliant storage).
* **Frontend:** React 18, Vite 6, TypeScript 5.6, Tailwind CSS (Calm, accessible UI).
* **Automated Testing:** Python `unittest` discovering 30 test cases across 3 dedicated suites.

### Verified Test Suite (30/30 Tests Passing)
* **Phase 1: Schemas & Ingestion Validation (`test_schema_and_validation.py` - 7 tests):** Verified 8 FLN skills, 100 students roster, 519 assessment rows, boundary math ($3/5$ passing), multi-skill events, and rejection of 7 deliberate anomaly fixtures (negative scores, score > max, invalid dates, zero max score).
* **Phase 2: Decision Engine & Persistence (`test_rule_engine_and_persistence.py` - 11 tests):** Verified single-gap flags, two-point repeated-gap priority, progress recovery on-track, version mismatch blocking, attendance independence, full action-card coverage, duplicate-skip policy, and database persistence across restarts.
* **Phase 3: FastAPI REST API (`test_api_endpoints.py` - 12 tests):** Verified health checks, multipart CSV uploads, overview metrics, search/grade filters, 404 missing handling, intervention creation, and reassessment linkage.

---

## 7. Feasibility, Roadmap & Scaling Strategy

```
Phase 1: School Cluster Validation (Months 1–3)
  • Pilot in 10–25 rural/tribal primary schools in 1 aspirational district.
  • Deploy low-bandwidth offline CSV ingest; train 50 primary teachers.
  • Evaluate teacher usability, time-to-action, and action adoption rate.

Phase 2: Block & District Integration (Months 4–8)
  • Expand to 100 schools across 2 blocks.
  • Interoperability adapter for state periodic assessment CSV exports.
  • Establish School Management Committee (SMC) aggregate reporting loops.

Phase 3: State-Level Integration (Months 9–18)
  • API integration with State LMS / DIKSHA portal via open standards.
  • Automated batch generation of micro-remediation printables for teachers.
```

### Operational Constraints & Mitigation
1. **Low Connectivity in Rural Schools:** Operates locally on school laptops, tablets, or block-coordinator PCs via SQLite without needing continuous cloud internet.
2. **Teacher Time Poverty:** Action Cards are pre-formulated, requiring less than 2 minutes of teacher review per flagged student.
3. **Data Quality & Inconsistencies:** The automated Ingestion Validator automatically detects duplicates, impossible scores, and syntax errors, isolating corrupted rows into an auditable log without halting the system.

---

## 8. Expected Social Impact & Measurable Metrics

| Evaluation Metric | Baseline / Target | Measurement Methodology |
|---|---|---|
| **Early Gap Detection Time** | Reduced from **90 days** (term exams) to **< 48 hours** | Interval between classroom check entry and teacher action card review. |
| **Action Adoption Rate** | **> 75%** of generated action cards executed | Logged interventions with non-identifying teacher notes. |
| **Reassessment Loop Closure** | **> 70%** of interventions reassessed within 14 days | Proportion of interventions with linked follow-up assessment event. |
| **Data Integrity & Governance** | **100%** compliance with DPDP Act 2023 | Zero PII ingestion; 100% pseudonymous record linking. |
| **Foundational Competency Progress** | Demonstrated positive score delta ($\Delta$) across comparable FLN forms | Form-comparable pre/post score tracking over a 60-day remediation cycle. |

### Alignment with National Priorities
* **NIPUN Bharat Mission:** Direct operationalization of universal foundational literacy and numeracy targets by Grade 3.
* **National Education Policy (NEP) 2020:** Formative, competency-based classroom assessment replacing high-stakes rote examinations.
* **Digital Public Infrastructure (DPI):** An open, non-proprietary layer that strengthens existing investments in UDISE+ and DIKSHA.

---

## 9. References & Data Sources

1. **ASER Centre / Pratham (2024):** *Annual Status of Education Report (Rural) 2024*. [https://asercentre.org/aser-2024/](https://asercentre.org/aser-2024/)
2. **PARAKH, NCERT (2024):** *Rashtriya Sarvekshan / Foundational Learning Study (FLS) National Report*. [https://parakh.ncert.gov.in/foundation-learning-study](https://parakh.ncert.gov.in/foundation-learning-study)
3. **Ministry of Education, Government of India (2021):** *National Initiative for Proficiency in Reading with Understanding and Numeracy (NIPUN Bharat) Guidelines*. [https://nipunbharat.education.gov.in/](https://nipunbharat.education.gov.in/)
4. **Ministry of Education, Government of India (2020):** *National Education Policy (NEP) 2020*.
5. **Ministry of Law and Justice, Government of India (2023):** *Digital Personal Data Protection (DPDP) Act, 2023*.
6. **Unified District Information System for Education Plus (UDISE+):** *Flash Statistics 2023–24, Ministry of Education*.
