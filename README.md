# ShikshaSignal

> **Theme 2: Foundational Learning Outcomes | Techfest IIT Bombay Challenge 2026–27**  
> Learning-gap early-warning and teacher decision-support layer for foundational literacy and numeracy (Grades 1–3).

---

## 1. Project Overview & Current State

ShikshaSignal translates classroom assessment evidence into transparent, explainable decision support for primary teachers. It does **not** replace statutory government systems (such as UDISE+, DIKSHA, PARAKH, or state LMS platforms); rather, it acts as an explainable, teacher-centered decision-support layer.

**Current State:** **Phase 1, Phase 2, Phase 3 & Phase 4 Complete**  
* **Phase 1:** Data models, schemas, starter 8-skill catalog, 100-student synthetic dataset, and ingestion validator.
* **Phase 2:** Transparent Decision Engine (gap detection, repeated-gap priority, comparability guardrails, attendance independence, and pedagogical action cards) and SQLite Persistence Layer (duplicate-skip policy, audit trails, and intervention-to-reassessment tracking).
* **Phase 3:** Application Services (`ImportService`, `StudentService`, `OverviewService`, `InterventionService`) and FastAPI REST API with OpenAPI documentation.
* **Phase 4:** Teacher-Centred React + Vite + TypeScript + Tailwind CSS Frontend Dashboard.

---

## 2. Claims & Assumptions Register

In strict adherence to project governance:

| Category | Description | Status / Boundary |
|---|---|---|
| **Verified Public Facts** | • ASER 2024 is a sample-based rural household survey providing national/state context; not an individual student tracking database.<br>• PARAKH & Foundational Learning Study establish national benchmark frameworks, but public reports do not provide student-level records or live APIs.<br>• NIPUN Bharat defines national FLN target goals. | Verified from public sources; no live government API or data-access permissions are claimed. |
| **Proposed Design Decisions** | • Documented CSV batch import with strict validation and auditable error logs.<br>• Explainable, deterministic rule engine (no opaque black-box ML).<br>• Closed-loop teacher action cards linked to subsequent reassessments.<br>• Neutral UI labels ("Needs Teacher Review", "Insufficient Data") preventing student stigmatization.<br>• Layered REST API architecture separating routes, services, database, and rule engine.<br>• Calm, accessible education-technology UI system prioritizing teacher usability and evidence transparency. | Technical prototype design. |
| **Synthetic Demo Assumptions** | • Fictional cohort of 100 students (`STU-0001` to `STU-0100`) in school `SCH-001`.<br>• Scoring scale: Integer score out of `max_score` (5 items per skill).<br>• **Threshold Ratio**: Default benchmark ratio is **0.60 (60%)**. Strictly configurable. Not an official NIPUN Bharat or NCERT benchmark. | Labeled as synthetic demonstration assumptions. |

---

## 3. Frontend Dashboard Architecture & Screens

Built with React 18, Vite, TypeScript, and Tailwind CSS in `frontend/`:

* **Screen A: Overview Dashboard ([OverviewScreen.tsx](file:///C:/Users/hp/.gemini/antigravity/scratch/shikshasignal/frontend/src/screens/OverviewScreen.tsx))**
  * Live school metrics from `/api/overview`: Total students, total assessments, review flags, priority flags, skills on track, and pending/completed reassessments.
  * Direct drill-down navigation into flagged student lists.
* **Screen B: Classroom Matrix View ([StudentsScreen.tsx](file:///C:/Users/hp/.gemini/antigravity/scratch/shikshasignal/frontend/src/screens/StudentsScreen.tsx))**
  * Searchable student list using pseudonymous IDs (`STU-XXXX`).
  * Grade filter (Grades 1, 2, 3) and decision status filter (`priority_for_teacher_review`, `needs_teacher_review`, `on_track`, `insufficient_data`).
  * Non-stigmatizing status badges and skill-level review counts.
* **Screen C: Student Skill Profile ([StudentProfileScreen.tsx](file:///C:/Users/hp/.gemini/antigravity/scratch/shikshasignal/frontend/src/screens/StudentProfileScreen.tsx))**
  * Longitudinal assessment history per skill with rule explanations.
  * Attendance shown strictly as contextual metadata with explicit non-causal disclaimer.
  * Version/scale comparability warnings.
* **Screen D: Teacher Decision Support Cards ([StudentProfileScreen.tsx](file:///C:/Users/hp/.gemini/antigravity/scratch/shikshasignal/frontend/src/screens/StudentProfileScreen.tsx))**
  * Pedagogical micro-activities mapped to the 8 FLN skills (sand tracing, CVC word sliders, bundling sticks, floor number lines).
  * Evidence history, follow-up prompt, and mandatory non-diagnostic disclaimer.
* **Screen E: Intervention Tracking & Reassessment Loop ([InterventionsScreen.tsx](file:///C:/Users/hp/.gemini/antigravity/scratch/shikshasignal/frontend/src/screens/InterventionsScreen.tsx))**
  * Form to record delivered remediation (skill, activity type, non-identifying teacher note).
  * Follow-up reassessment linker verifying version comparability and computing score progression delta ($\Delta$).
* **Screen F: Data Import & Audit Governance ([GovernanceScreen.tsx](file:///C:/Users/hp/.gemini/antigravity/scratch/shikshasignal/frontend/src/screens/GovernanceScreen.tsx))**
  * Direct CSV file upload to `/api/import` with real-time validation summaries (inserted, duplicate, rejected).
  * Live audit log viewer from `/api/validation-logs`.
  * Prominent notice that all demo data is synthetic.

---

## 4. How to Run the Application

### Option 1: Unified Full-Stack Server (Recommended)
Since the production React bundle is built into `frontend/dist/`, starting the FastAPI backend serves both the REST API and the React web dashboard simultaneously on port 8000:

```bash
# From project root: C:\Users\hp\.gemini\antigravity\scratch\shikshasignal
uvicorn src.web.app:app --host 127.0.0.1 --port 8000 --reload
```
* **Teacher Web Dashboard:** Open `http://127.0.0.1:8000/` in your browser.
* **Interactive API Docs (Swagger):** `http://127.0.0.1:8000/docs`
* **Health Endpoint:** `http://127.0.0.1:8000/api/health`

### Option 2: Frontend Development Mode with Hot Reload
To run the Vite dev server with proxy to backend:

```bash
# Terminal 1: Start Backend (Port 8000)
uvicorn src.web.app:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2: Start Frontend Dev Server (Port 5173)
cd frontend
npm run dev
```
Open `http://127.0.0.1:5173/` in your browser.

---

## 5. Verification & Test Suite Execution

### Backend Automated Tests (30 Tests across Phases 1, 2, and 3)
```bash
python -m unittest discover -s tests -p "test_*.py"
```

**Result:**
```
..............................
----------------------------------------------------------------------
Ran 30 tests in 4.176s

OK
```

### Frontend Production Build
```bash
cd frontend
npm run build
```

**Result:**
```
✓ 38 modules transformed.
dist/index.html                   0.76 kB │ gzip:  0.44 kB
dist/assets/index-By4XQseE.css   20.54 kB │ gzip:  4.57 kB
dist/assets/index-BiPoSJw8.js   202.07 kB │ gzip: 58.57 kB
✓ built in 5.12s
```
Zero build errors, zero type errors.

---

## 6. Directory Layout

```
shikshasignal/
├── README.md                          # Project documentation and governance register
├── requirements.txt                  # Python dependencies (FastAPI, Pydantic, httpx, etc.)
├── data/
│   ├── raw/                          # Preserved raw uploaded CSV files
│   ├── templates/                    # Blank CSV import templates
│   ├── synthetic/                    # Generated 100-student demo dataset (8 skills)
│   ├── fixtures/                     # Deliberate validation test anomalies
│   └── shikshasignal.db              # Default SQLite database
├── src/
│   ├── config.py                     # Configurable thresholds and paths
│   ├── generate_synthetic_data.py    # Synthetic data generator script
│   ├── models/                       # Schemas, API models & SQLite database manager
│   ├── engine/                       # Validator & transparent decision engine
│   ├── services/                     # Application business services
│   └── web/                          # FastAPI app factory and route controllers
├── frontend/                         # React + Vite + TypeScript Dashboard
│   ├── package.json
│   ├── vite.config.ts                # Vite config with /api proxy
│   ├── tailwind.config.js            # Calm, accessible styling palette
│   ├── src/
│   │   ├── types/api.ts              # Typed interfaces strictly mirroring backend
│   │   ├── services/api.ts           # Centralized API service layer
│   │   ├── components/               # Navbar, StatusBadge, StatCard, icons, loading/error
│   │   ├── screens/                  # 6 functional dashboard views
│   │   ├── App.tsx                   # Main routing & state
│   │   └── main.tsx
│   └── dist/                         # Compiled production bundle
└── tests/                            # 30 automated backend tests across all phases
```
