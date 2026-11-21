"""
report_service.py - PDF Report Card & CSV Export Generation Service

Generates:
1. Individual Student PDF Report Cards (Demographics, Marks Table, Grade, Attendance, AI Recommendations).
2. Institutional At-Risk Early Warning PDF Reports.
3. Class Cohort CSV Export.
4. Subject Performance Analytics CSV Export.
5. AI Diagnostics Historical CSV Export.
"""

import io
import csv
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable
)

from app.models import Student, AIRecommendation
from app.services.risk_service import evaluate_student_risk
from app.services.ai_service import _deterministic_pedagogical_analysis


def generate_student_pdf_report(student: Student, db: Optional[Session] = None) -> bytes:
    """
    Generates a PDF academic report card for a single student.
    Includes demographics, course marks, grade standing, attendance gauge,
    and personalized AI improvement guidance.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom typography styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0f172a"),
        alignment=1  # Centered
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748b"),
        alignment=1
    )

    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155")
    )

    badge_risk = colors.HexColor("#ef4444") if student.risk_level == "At Risk" else (
        colors.HexColor("#f59e0b") if student.risk_level == "Needs Attention" else colors.HexColor("#10b981")
    )

    elements = []

    # 1. Header Banner
    elements.append(Paragraph("INSTITUTE OF ADVANCED TECHNOLOGY & SCIENCES", title_style))
    elements.append(Paragraph("OFFICIAL ACADEMIC PERFORMANCE & AI DIAGNOSTIC REPORT CARD", subtitle_style))
    elements.append(Spacer(1, 8))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563eb"), spaceAfter=14))

    # 2. Student Demographics & Academic KPI Card
    demo_data = [
        [
            Paragraph(f"<b>Student Name:</b> {student.name}", body_style),
            Paragraph(f"<b>Roll / Student ID:</b> {student.student_id}", body_style)
        ],
        [
            Paragraph(f"<b>Department:</b> {student.department}", body_style),
            Paragraph(f"<b>Semester:</b> {student.semester} | <b>Session:</b> {student.academic_year}", body_style)
        ],
        [
            Paragraph(f"<b>Institutional Email:</b> {student.email}", body_style),
            Paragraph(f"<b>Attendance Rate:</b> {student.attendance_percentage}%", body_style)
        ],
        [
            Paragraph(f"<b>Cumulative Average:</b> <b>{student.average_marks}%</b>", body_style),
            Paragraph(f"<b>Letter Grade:</b> <b>{student.grade}</b> | <b>Status:</b> <font color='{badge_risk.hexval()}'><b>{student.risk_level}</b></font>", body_style)
        ]
    ]

    demo_table = Table(demo_data, colWidths=[270, 270])
    demo_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#e2e8f0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    elements.append(demo_table)
    elements.append(Spacer(1, 16))

    # 3. Course Marks Breakdown Table
    elements.append(Paragraph("Course Marks Breakdown (Curriculum Subjects)", section_heading))

    course_rows = [
        [
            Paragraph("<b>Subject Course Title</b>", body_style),
            Paragraph("<b>Max Marks</b>", body_style),
            Paragraph("<b>Marks Scored</b>", body_style),
            Paragraph("<b>Passing Cutoff</b>", body_style),
            Paragraph("<b>Status</b>", body_style)
        ]
    ]

    courses = [
        ("Mathematics", float(student.math_marks)),
        ("Programming / Python", float(student.programming_marks)),
        ("Data Structures & Algorithms", float(student.data_structures_marks)),
        ("Database Management Systems", float(student.database_marks)),
        ("Machine Learning", float(student.machine_learning_marks)),
    ]

    for title, score in courses:
        passed = score >= 40.0
        status_text = "<font color='#10b981'><b>PASS</b></font>" if passed else "<font color='#ef4444'><b>FAIL</b></font>"
        course_rows.append([
            Paragraph(title, body_style),
            Paragraph("100.0", body_style),
            Paragraph(f"<b>{score:.1f}</b>", body_style),
            Paragraph("40.0", body_style),
            Paragraph(status_text, body_style)
        ])

    # Total row
    course_rows.append([
        Paragraph("<b>Total Score / Aggregate</b>", body_style),
        Paragraph("<b>500.0</b>", body_style),
        Paragraph(f"<b>{student.total_marks:.1f} ({student.average_marks}%)</b>", body_style),
        Paragraph("250.0 (50%)", body_style),
        Paragraph("<font color='#10b981'><b>QUALIFIED</b></font>" if student.average_marks >= 50.0 else "<font color='#ef4444'><b>NOT QUALIFIED</b></font>", body_style)
    ])

    course_table = Table(course_rows, colWidths=[200, 75, 95, 90, 80])
    course_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f1f5f9")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(course_table)
    elements.append(Spacer(1, 16))

    # 4. AI-Powered Academic Diagnostics & Study Roadmap
    elements.append(Paragraph("AI-Powered Performance Diagnostics & Recommendations", section_heading))

    # Retrieve latest persisted AI recommendation or compute pedagogical diagnosis
    ai_summary = ""
    ai_advice = ""
    weak_str = ""

    if db:
        latest_rec = (
            db.query(AIRecommendation)
            .filter(AIRecommendation.student_id == student.student_id)
            .order_by(AIRecommendation.generated_at.desc())
            .first()
        )
        if latest_rec:
            ai_summary = latest_rec.overall_summary
            ai_advice = latest_rec.actionable_plan
            weak_str = latest_rec.weak_subjects

    if not ai_summary:
        fallback_analysis, _ = _deterministic_pedagogical_analysis(student)
        ai_summary = fallback_analysis.overall_summary
        ai_advice = fallback_analysis.personalized_advice
        weak_str = ", ".join([f"{w.subject} ({w.score})" for w in fallback_analysis.weak_subjects])

    ai_data = [
        [Paragraph(f"<b>Academic Diagnosis:</b> {ai_summary}", body_style)],
        [Paragraph(f"<b>Identified Focus / Remedial Areas:</b> {weak_str if weak_str else 'All subjects satisfying good standing.'}", body_style)],
        [Paragraph(f"<b>Recommended Action Plan:</b> {ai_advice}", body_style)]
    ]

    ai_table = Table(ai_data, colWidths=[540])
    ai_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#eff6ff")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#3b82f6")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#bfdbfe")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    elements.append(ai_table)
    elements.append(Spacer(1, 18))

    # 5. Footer & Verification
    timestamp_str = datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC")
    footer_text = f"Report generated securely by AI-Powered Student Performance Analytics Platform on {timestamp_str}. Document ID: {student.student_id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M')}"
    elements.append(Paragraph(footer_text, subtitle_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


def generate_at_risk_pdf_report(students: List[Student]) -> bytes:
    """
    Generates an institutional executive PDF report of all students flagged for academic intervention.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "RiskTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#991b1b"),
        alignment=1
    )
    subtitle_style = ParagraphStyle(
        "RiskSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#64748b"),
        alignment=1
    )
    body_style = ParagraphStyle(
        "RiskBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#1e293b")
    )

    elements = []
    elements.append(Paragraph("INSTITUTIONAL EARLY INTERVENTION & AT-RISK MONITOR", title_style))
    elements.append(Paragraph(f"Confidential Faculty Advisory Dossier | Total Identified: {len(students)} Students", subtitle_style))
    elements.append(Spacer(1, 8))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#dc2626"), spaceAfter=12))

    rows = [
        [
            Paragraph("<b>ID</b>", body_style),
            Paragraph("<b>Student Name</b>", body_style),
            Paragraph("<b>Dept / Sem</b>", body_style),
            Paragraph("<b>Average %</b>", body_style),
            Paragraph("<b>Attendance</b>", body_style),
            Paragraph("<b>Tier</b>", body_style),
            Paragraph("<b>Primary Risk Drivers</b>", body_style)
        ]
    ]

    for s in students:
        eval_result = evaluate_student_risk(s)
        primary_factor = eval_result["factors"][0] if eval_result["factors"] else "Academic review needed"
        tier_color = "#ef4444" if eval_result["category"] == "At Risk" else "#f59e0b"

        rows.append([
            Paragraph(s.student_id, body_style),
            Paragraph(s.name, body_style),
            Paragraph(f"{s.department[:18]}.. / S{s.semester}", body_style),
            Paragraph(f"{s.average_marks}%", body_style),
            Paragraph(f"{s.attendance_percentage}%", body_style),
            Paragraph(f"<font color='{tier_color}'><b>{eval_result['category']}</b></font>", body_style),
            Paragraph(primary_factor, body_style)
        ])

    table = Table(rows, colWidths=[55, 95, 95, 55, 55, 75, 110])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 14))

    # Recommendations footer
    rec_text = (
        "<b>Immediate Recommended Protocol:</b><br/>"
        "1. Schedule mandatory faculty-mentor advisement sessions for all 'At Risk' students within 5 business days.<br/>"
        "2. Provide attendance warnings for students with < 75% attendance to prevent examination debarment.<br/>"
        "3. Assign student remedial coursework and track progress using the weekly study plan checklist."
    )
    elements.append(Paragraph(rec_text, body_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


def generate_class_csv_export(students: List[Student]) -> str:
    """
    Exports a cohort of students as CSV with demographic and computed metrics.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    headers = [
        "student_id", "name", "department", "semester", "academic_year", "email",
        "math_marks", "programming_marks", "data_structures_marks", "database_marks", "machine_learning_marks",
        "attendance_percentage", "total_marks", "average_marks", "percentage", "grade",
        "risk_level", "needs_support", "created_at"
    ]
    writer.writerow(headers)

    for s in students:
        writer.writerow([
            s.student_id,
            s.name,
            s.department,
            s.semester,
            s.academic_year,
            s.email,
            s.math_marks,
            s.programming_marks,
            s.data_structures_marks,
            s.database_marks,
            s.machine_learning_marks,
            s.attendance_percentage,
            s.total_marks,
            s.average_marks,
            s.percentage,
            s.grade,
            s.risk_level,
            s.needs_support,
            s.created_at.isoformat() if s.created_at else ""
        ])

    return output.getvalue()


def generate_subject_analytics_csv(subjects_data: List[Dict[str, Any]]) -> str:
    """Exports subject performance aggregates as CSV."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["subject", "average_score", "highest_score", "lowest_score"])
    for row in subjects_data:
        writer.writerow([row["subject"], row["average_score"], row["highest_score"], row["lowest_score"]])
    return output.getvalue()


def generate_ai_recommendations_csv(db: Session) -> str:
    """Exports all stored AI recommendations as CSV."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "student_id", "overall_summary", "strong_subjects", "weak_subjects", "actionable_plan", "generated_at"])

    recs = db.query(AIRecommendation).order_by(AIRecommendation.generated_at.desc()).all()
    for r in recs:
        writer.writerow([
            r.id,
            r.student_id,
            r.overall_summary,
            r.strong_subjects,
            r.weak_subjects,
            r.actionable_plan,
            r.generated_at.isoformat() if r.generated_at else ""
        ])
    return output.getvalue()
