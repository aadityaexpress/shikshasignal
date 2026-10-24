"""
Script to generate the official Round 1 Concept Proposal Document (.docx)
for Techfest 2026-27 | The India @ 71/100 Challenge (IIT Bombay)

Constraints & Specifications (from Official Guidelines):
- Page setup: A4 size
- Margins: Exactly 1 inch (72pt) on all sides
- Font: Arial (minimum 11pt for body text)
- Structured headers, tables, callout blocks, and evidence matrices.
"""

from pathlib import Path
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"
DOCS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = DOCS_DIR / "ROUND_1_SUBMISSION.docx"


def set_cell_background(cell, fill_hex):
    """Sets background shading of a table cell."""
    tcPr = cell._element.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)


def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Sets inner margins for a table cell in dxa (1 pt = 20 dxa)."""
    tcPr = cell._element.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)


def create_proposal():
    doc = docx.Document()

    # 1. Page Setup: A4 with 1-inch margins
    sections = doc.sections
    for section in sections:
        section.page_width = Inches(8.27)   # A4 Width
        section.page_height = Inches(11.69) # A4 Height
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # 2. Base Styles Configuration
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Arial'
    normal_style.font.size = Pt(11)
    normal_style.font.color.rgb = RGBColor(0x1E, 0x29, 0x3B) # Slate 800
    normal_style.paragraph_format.line_spacing = 1.15
    normal_style.paragraph_format.space_after = Pt(6)

    # Colors
    PRIMARY = RGBColor(0x0F, 0x4C, 0x81)   # Deep Navy
    SECONDARY = RGBColor(0x0D, 0x94, 0x88) # Teal 600
    DARK_TEXT = RGBColor(0x1E, 0x29, 0x3B) # Slate 800
    MUTED = RGBColor(0x64, 0x74, 0x8B)     # Slate 500

    # Header / Title Block
    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_after = Pt(2)
    title_p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_comp = title_p.add_run("TECHFEST 2026–27 | IIT BOMBAY\nTHE INDIA @ 71/100 CHALLENGE\n")
    r_comp.font.name = 'Arial'
    r_comp.font.size = Pt(11)
    r_comp.font.bold = True
    r_comp.font.color.rgb = PRIMARY

    r_title = title_p.add_run("Round 1: Concept Proposal Submission\n")
    r_title.font.name = 'Arial'
    r_title.font.size = Pt(15)
    r_title.font.bold = True
    r_title.font.color.rgb = PRIMARY

    sub_p = doc.add_paragraph()
    sub_p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_p.paragraph_format.space_after = Pt(14)
    r_sub = sub_p.add_run("Theme 2: Foundational Learning Outcomes\n")
    r_sub.font.bold = True
    r_sub.font.size = Pt(12)
    r_sub.font.color.rgb = SECONDARY

    r_name = sub_p.add_run("Project ShikshaSignal: Learning-Gap Early-Warning & Teacher Decision-Support Layer")
    r_name.font.size = Pt(12)
    r_name.font.bold = True
    r_name.font.color.rgb = DARK_TEXT

    # Section 1: Team & Project Identification
    h1 = doc.add_heading(level=1)
    r_h1 = h1.add_run("1. Team Information")
    r_h1.font.name = 'Arial'
    r_h1.font.size = Pt(13)
    r_h1.font.bold = True
    r_h1.font.color.rgb = PRIMARY
    h1.paragraph_format.space_before = Pt(8)
    h1.paragraph_format.space_after = Pt(4)

    team_table = doc.add_table(rows=5, cols=2)
    team_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    team_table.autofit = False

    col_widths = [Inches(2.2), Inches(4.07)]
    team_data = [
        ("Team Name & ID", "[Team Name]  |  Team ID: [Team ID]"),
        ("Institution / University", "[Institution / University Name]"),
        ("Theme Selected", "Theme 2: Foundational Learning Outcomes (NEP 2020 / NIPUN Bharat)"),
        ("Team Members & Roles", "1. [Lead Name] (System Architecture & Data Engineering)\n2. [Member 2] (Pedagogical Decision Modeling)\n3. [Member 3] (Frontend & Teacher Usability)\n4. [Member 4] (Policy Alignment & Impact Evaluation)"),
        ("Contact & Repository", "Email: [Contact Email]  |  Phone: [Contact Phone]\nPrototype: https://github.com/aadityaexpress/shikshasignal"),
    ]

    for row_idx, (k, v) in enumerate(team_data):
        row = team_table.rows[row_idx]
        row.cells[0].width = col_widths[0]
        row.cells[1].width = col_widths[1]
        set_cell_background(row.cells[0], "F1F5F9")
        set_cell_margins(row.cells[0], top=80, bottom=80, left=120, right=120)
        set_cell_margins(row.cells[1], top=80, bottom=80, left=120, right=120)

        p0 = row.cells[0].paragraphs[0]
        r0 = p0.add_run(k)
        r0.font.bold = True
        r0.font.size = Pt(10)
        p0.paragraph_format.space_after = Pt(2)

        p1 = row.cells[1].paragraphs[0]
        r1 = p1.add_run(v)
        r1.font.size = Pt(10)
        p1.paragraph_format.space_after = Pt(2)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # Section 2: Problem Identification
    h2 = doc.add_heading(level=1)
    r_h2 = h2.add_run("2. Problem Identification & Underserved Community")
    r_h2.font.name = 'Arial'
    r_h2.font.size = Pt(13)
    r_h2.font.bold = True
    r_h2.font.color.rgb = PRIMARY
    h2.paragraph_format.space_before = Pt(8)
    h2.paragraph_format.space_after = Pt(4)

    p_prob = doc.add_paragraph()
    p_prob.add_run(
        "India's elementary education system has achieved historic milestones in access, with Gross Enrollment Ratios (GER) "
        "exceeding 98% at the primary level (UDISE+ 2023–24). However, national aggregate scorecards mask a profound learning crisis "
        "at the grassroots: children are physically attending school, yet fail to acquire Foundational Literacy and Numeracy (FLN) skills."
    )

    p_gap = doc.add_paragraph()
    r_gap_bold = p_gap.add_run("The Measurable Implementation Gap: ")
    r_gap_bold.font.bold = True
    p_gap.add_run(
        "The problem is not an absence of assessment data, but how that data is governed and deployed. "
        "Periodic assessments are routinely administered and recorded for administrative compliance, but they sit dormant in offline paper registers "
        "or siloed state dashboards. Frontline primary teachers receive zero immediate, low-bandwidth, and explainable decision-support at point of use. "
        "By the time term-end examinations flag learning deficits, the academic year has passed, and foundational deficits compound into irreversible dropouts."
    )

    p_comm = doc.add_paragraph()
    r_comm_bold = p_comm.add_run("Underserved Community Affected: ")
    r_comm_bold.font.bold = True
    p_comm.add_run(
        "The primary beneficiaries are Grade 1–3 learners (ages 6–9) in rural government schools, particularly from socially and economically disadvantaged "
        "backgrounds (first-generation school-goers). The secondary beneficiaries are over 2.5 million primary teachers who face multi-grade classrooms, "
        "burdensome compliance documentation, and lack targeted micro-remediation tools."
    )

    # Section 3: Evidence & Ground-Level Context
    h3 = doc.add_heading(level=1)
    r_h3 = h3.add_run("3. Evidence & Ground-Level Context")
    r_h3.font.name = 'Arial'
    r_h3.font.size = Pt(13)
    r_h3.font.bold = True
    r_h3.font.color.rgb = PRIMARY
    h3.paragraph_format.space_before = Pt(8)
    h3.paragraph_format.space_after = Pt(4)

    p_ev = doc.add_paragraph()
    p_ev.add_run("The urgency of closing this implementation gap is established by India's primary diagnostic survey benchmarks:")

    ev_bullets = [
        ("ASER 2024 (Pratham): ", "Nationwide household survey evidence demonstrates that only 23.4% of Grade 3 children in rural government schools can read a simple Grade 2 text, and only 28.6% can perform basic subtraction with borrowing. Over 70% enter upper primary with compounded learning deficits."),
        ("PARAKH Rashtriya Sarvekshan 2024 / Foundational Learning Study (NCERT): ", "National competency evaluations confirm heavy clusters of primary learners performing in 'Below Basic' bands. Deficits concentrate early in letter-sound recognition, word decoding, single-digit decomposition, and base-10 place value."),
        ("NIPUN Bharat Guidelines (Ministry of Education, 2021): ", "Universal foundational reading with comprehension and basic mathematics by Grade 3 is an explicit national mission. NEP 2020 designates foundational literacy as an indispensable prerequisite to all future education."),
    ]
    for b_title, b_desc in ev_bullets:
        bp = doc.add_paragraph(style='List Bullet')
        r_bt = bp.add_run(b_title)
        r_bt.font.bold = True
        bp.add_run(b_desc)

    # Section 4: Existing Ecosystem Analysis
    h4 = doc.add_heading(level=1)
    r_h4 = h4.add_run("4. Existing Ecosystem Analysis & Persistence of Gap")
    r_h4.font.name = 'Arial'
    r_h4.font.size = Pt(13)
    r_h4.font.bold = True
    r_h4.font.color.rgb = PRIMARY
    h4.paragraph_format.space_before = Pt(8)
    h4.paragraph_format.space_after = Pt(4)

    eco_table = doc.add_table(rows=5, cols=3)
    eco_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    eco_table.autofit = False

    eco_widths = [Inches(1.8), Inches(2.2), Inches(2.27)]
    eco_headers = ["Existing Platform", "Mandate & Capabilities", "Bottleneck: Why Gap Persists"]
    for i, h in enumerate(eco_headers):
        cell = eco_table.rows[0].cells[i]
        cell.width = eco_widths[i]
        set_cell_background(cell, "0F4C81")
        set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
        p = cell.paragraphs[0]
        r = p.add_run(h)
        r.font.bold = True
        r.font.size = Pt(10)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    eco_rows = [
        ("UDISE+ (MoE)", "Annual national school census tracking infrastructure, teacher counts, and enrollment.", "Aggregated retrospectively at school/block level once a year; provides zero formative student-level diagnostic feedback."),
        ("DIKSHA FLN", "Digital repository of national teaching-learning materials and teacher training courses.", "Acts as an unlinked static content library; does not diagnose specific child deficits or generate automated classroom micro-action cards."),
        ("State Assessment Apps (Nipun Lakshya / SAT)", "Periodic digital evaluation of students against competency benchmarks.", "Employed primarily for upward compliance monitoring and district ranking; results do not loop back into immediate classroom micro-remediation."),
        ("ASER / PARAKH Diagnostics", "Periodic national/state sample-based diagnostic surveys.", "Cross-sectional sample datasets designed for macro policymaking; not designed or authorized for continuous individual classroom tracking."),
    ]

    for row_idx, data in enumerate(eco_rows, start=1):
        row = eco_table.rows[row_idx]
        bg = "F8FAFC" if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, text in enumerate(data):
            cell = row.cells[col_idx]
            cell.width = eco_widths[col_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=60, bottom=60, left=100, right=100)
            p = cell.paragraphs[0]
            r = p.add_run(text)
            r.font.size = Pt(9.5)
            if col_idx == 0:
                r.font.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # Section 5: Proposed Solution - ShikshaSignal
    h5 = doc.add_heading(level=1)
    r_h5 = h5.add_run("5. Proposed Solution: ShikshaSignal")
    r_h5.font.name = 'Arial'
    r_h5.font.size = Pt(13)
    r_h5.font.bold = True
    r_h5.font.color.rgb = PRIMARY
    h5.paragraph_format.space_before = Pt(8)
    h5.paragraph_format.space_after = Pt(4)

    p_sol = doc.add_paragraph()
    p_sol.add_run(
        "ShikshaSignal is a lightweight, low-bandwidth, and explainable learning-gap early-warning and teacher decision-support layer "
        "designed specifically for Grades 1–3 foundational literacy and numeracy. It operates on existing classroom assessment checks "
        "without replacing statutory systems like UDISE+ or DIKSHA. Rather than inventing government APIs or unverified diagnostic AI, "
        "it implements deterministic, policy-aligned decision rules paired with structured Teacher Action Cards."
    )

    # Innovation Pillars Table
    p_arch = doc.add_paragraph()
    r_arch_bold = p_arch.add_run("Architectural Pillars & Ground-Level Technical Features:")
    r_arch_bold.font.bold = True

    features_table = doc.add_table(rows=5, cols=2)
    features_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    features_table.autofit = False

    f_widths = [Inches(1.8), Inches(4.47)]
    features_data = [
        ("Deterministic Decision Engine", "100% transparent and explainable rules. Ratio = score / max_score. A score strictly below 60% triggers 'Needs Teacher Review'. A score of exactly 3/5 (60%) passes benchmark. Two consecutive low scores escalate to 'Priority for Teacher Review'. No hallucinating black-box ML."),
        ("Teacher Action Cards at Point of Use", "Flagged skills generate concrete, teacher-editable micro-activities mapped to the 8 FLN skills (sand tray tracing, CVC sliders, bundling sticks, number lines). Includes pedagogical rationale, follow-up prompt, and non-diagnostic disclaimer."),
        ("Closed-Loop Reassessment Tracking", "Teachers log delivered interventions. Follow-up checks automatically link to original events, verify version comparability, calculate score delta (Δ), and document progress without causal overclaims."),
        ("Privacy & DPDP Act 2023 Compliance", "Strict pseudonymisation (STU-XXXX). Zero personal identifying data (no child names, Aadhaar, biometric, or contact data). Attendance is strictly contextual metadata and never influences learning-gap status."),
    ]

    for row_idx, (k, v) in enumerate(features_data):
        row = features_table.rows[row_idx]
        row.cells[0].width = f_widths[0]
        row.cells[1].width = f_widths[1]
        set_cell_background(row.cells[0], "F1F5F9")
        set_cell_margins(row.cells[0], top=60, bottom=60, left=100, right=100)
        set_cell_margins(row.cells[1], top=60, bottom=60, left=100, right=100)

        p0 = row.cells[0].paragraphs[0]
        r0 = p0.add_run(k)
        r0.font.bold = True
        r0.font.size = Pt(10)

        p1 = row.cells[1].paragraphs[0]
        r1 = p1.add_run(v)
        r1.font.size = Pt(9.5)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # Section 6: Feasibility, Verification & Implementation Roadmap
    h6 = doc.add_heading(level=1)
    r_h6 = h6.add_run("6. Technical Feasibility & Implementation Roadmap")
    r_h6.font.name = 'Arial'
    r_h6.font.size = Pt(13)
    r_h6.font.bold = True
    r_h6.font.color.rgb = PRIMARY
    h6.paragraph_format.space_before = Pt(8)
    h6.paragraph_format.space_after = Pt(4)

    p_feas = doc.add_paragraph()
    p_feas.add_run(
        "ShikshaSignal is not a conceptual mockup; the prototype is fully built, container-ready, and verified through an automated test suite. "
        "The stack comprises a FastAPI backend with SQLite persistence and a React + Vite + TypeScript teacher dashboard, verified with 30 passing automated tests."
    )

    roadmap_table = doc.add_table(rows=4, cols=3)
    roadmap_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    roadmap_table.autofit = False

    r_widths = [Inches(1.2), Inches(2.2), Inches(2.87)]
    r_headers = ["Phase", "Milestone / Scope", "Key Deliverables & Validation"]
    for i, h in enumerate(r_headers):
        cell = roadmap_table.rows[0].cells[i]
        cell.width = r_widths[i]
        set_cell_background(cell, "0D9488")
        set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
        p = cell.paragraphs[0]
        r = p.add_run(h)
        r.font.bold = True
        r.font.size = Pt(10)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    r_rows = [
        ("Phase 1\n(Months 1–3)", "Cluster Pilot in 25 Primary Schools", "Deploy offline CSV ingest in 1 block (50 teachers). Evaluate teacher action adoption rate, time-to-action (<48h), and usability feedback."),
        ("Phase 2\n(Months 4–8)", "Block & District Scaling (100 Schools)", "Integrate state periodic assessment CSV adapters. Establish School Management Committee (SMC) progress reporting feedback loops."),
        ("Phase 3\n(Months 9–18)", "State-Level DPI Integration", "Standards-compliant data connector for State LMS / DIKSHA portal. Automated batch generation of micro-remediation worksheets."),
    ]

    for row_idx, data in enumerate(r_rows, start=1):
        row = roadmap_table.rows[row_idx]
        bg = "F8FAFC" if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, text in enumerate(data):
            cell = row.cells[col_idx]
            cell.width = r_widths[col_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=60, bottom=60, left=100, right=100)
            p = cell.paragraphs[0]
            r = p.add_run(text)
            r.font.size = Pt(9.5)
            if col_idx == 0:
                r.font.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # Section 7: Expected Social Impact & Measurable Metrics
    h7 = doc.add_heading(level=1)
    r_h7 = h7.add_run("7. Expected Social Impact & Measurable Metrics")
    r_h7.font.name = 'Arial'
    r_h7.font.size = Pt(13)
    r_h7.font.bold = True
    r_h7.font.color.rgb = PRIMARY
    h7.paragraph_format.space_before = Pt(8)
    h7.paragraph_format.space_after = Pt(4)

    impact_table = doc.add_table(rows=6, cols=3)
    impact_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    impact_table.autofit = False

    imp_widths = [Inches(2.0), Inches(1.8), Inches(2.47)]
    imp_headers = ["Evaluation Metric", "Target Benchmark", "Measurement Protocol"]
    for i, h in enumerate(imp_headers):
        cell = impact_table.rows[0].cells[i]
        cell.width = imp_widths[i]
        set_cell_background(cell, "0F4C81")
        set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
        p = cell.paragraphs[0]
        r = p.add_run(h)
        r.font.bold = True
        r.font.size = Pt(10)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    imp_rows = [
        ("Time to Classroom Action", "< 48 hours (vs 90 days)", "Elapsed time from assessment upload to teacher opening and executing an Action Card."),
        ("Teacher Action Adoption Rate", "> 75% adoption", "Proportion of generated action cards accepted, customized, or logged as completed in classroom."),
        ("Reassessment Loop Completion", "> 70% within 14 days", "Proportion of remediation interventions with a linked follow-up assessment event."),
        ("Data Quality & Governance", "100% DPDP Compliance", "Zero PII stored; 100% pseudonymous record linking with auditable validation rejection logs."),
        ("Foundational Learning Delta (Δ)", "Positive Δ on comparable forms", "Longitudinal pre/post score difference over a 60-day remediation cycle using form-comparable checks."),
    ]

    for row_idx, data in enumerate(imp_rows, start=1):
        row = impact_table.rows[row_idx]
        bg = "F8FAFC" if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, text in enumerate(data):
            cell = row.cells[col_idx]
            cell.width = imp_widths[col_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=60, bottom=60, left=100, right=100)
            p = cell.paragraphs[0]
            r = p.add_run(text)
            r.font.size = Pt(9.5)
            if col_idx == 0:
                r.font.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # Section 8: References
    h8 = doc.add_heading(level=1)
    r_h8 = h8.add_run("8. Key References & Ground-Level Sources")
    r_h8.font.name = 'Arial'
    r_h8.font.size = Pt(13)
    r_h8.font.bold = True
    r_h8.font.color.rgb = PRIMARY
    h8.paragraph_format.space_before = Pt(8)
    h8.paragraph_format.space_after = Pt(4)

    refs = [
        "ASER Centre / Pratham (2024). Annual Status of Education Report (Rural) 2024. New Delhi.",
        "PARAKH, NCERT (2024). Rashtriya Sarvekshan / Foundational Learning Study (FLS) National Report. Ministry of Education, New Delhi.",
        "Ministry of Education, Government of India (2021). NIPUN Bharat Mission Guidelines for Foundational Literacy and Numeracy.",
        "Ministry of Education, Government of India (2020). National Education Policy (NEP) 2020.",
        "Ministry of Law and Justice, Government of India (2023). Digital Personal Data Protection Act, 2023.",
        "UDISE+ (2024). Unified District Information System for Education Plus 2023–24. Department of School Education and Literacy.",
    ]
    for ref in refs:
        p_ref = doc.add_paragraph(style='List Bullet')
        r_ref = p_ref.add_run(ref)
        r_ref.font.size = Pt(9.5)
        p_ref.paragraph_format.space_after = Pt(2)

    doc.save(str(OUTPUT_FILE))
    print(f"Generated Word document successfully at: {OUTPUT_FILE}")


if __name__ == "__main__":
    create_proposal()
