"""
test_reports.py - Test Suite for Downloadable PDF & CSV Reporting Services

Tests:
- Individual student PDF report card generation
- Institutional at-risk early intervention PDF dossier generation
- Class cohort CSV export
- Curriculum subject analytics CSV export
- AI recommendations archive CSV export
- Student RBAC isolation on PDF report cards
"""

import pytest
from fastapi import status
from app.core.security import create_access_token


@pytest.fixture
def populated_report_student(client):
    """Creates a sample student with demographic and marks data."""
    res = client.post("/api/students/", json={
        "student_id": "STU_REP_001",
        "name": "Report Card Student",
        "department": "Information Technology",
        "semester": 5,
        "academic_year": "2024-2025",
        "email": "report.student@test.edu",
        "math_marks": 78.0,
        "programming_marks": 85.0,
        "data_structures_marks": 72.0,
        "database_marks": 80.0,
        "machine_learning_marks": 82.0,
        "attendance_percentage": 88.5
    })
    return res.json()


def test_download_student_pdf_report(client, populated_report_student):
    """Verifies downloading an official individual student PDF report card."""
    stu_id = populated_report_student["student_id"]
    res = client.get(f"/api/reports/student/{stu_id}/pdf")

    assert res.status_code == status.HTTP_200_OK
    assert res.headers["content-type"] == "application/pdf"
    assert "attachment; filename=STU_REP_001_report_card.pdf" in res.headers["content-disposition"]
    # PDF binary signature verification
    assert res.content.startswith(b"%PDF")
    assert len(res.content) > 1000


def test_download_at_risk_pdf_report(client):
    """Verifies generating and downloading the institutional at-risk PDF dossier."""
    # Seed an at-risk student
    client.post("/api/students/", json={
        "student_id": "STU_RISK_REP",
        "name": "At Risk Student Rep",
        "department": "Computer Science",
        "semester": 2,
        "academic_year": "2024-2025",
        "email": "riskrep@test.edu",
        "math_marks": 35.0,
        "programming_marks": 40.0,
        "data_structures_marks": 38.0,
        "database_marks": 42.0,
        "machine_learning_marks": 40.0,
        "attendance_percentage": 60.0
    })

    res = client.get("/api/reports/at-risk/pdf")
    assert res.status_code == status.HTTP_200_OK
    assert res.headers["content-type"] == "application/pdf"
    assert "institutional_at_risk_report.pdf" in res.headers["content-disposition"]
    assert res.content.startswith(b"%PDF")


def test_download_class_csv_export(client, populated_report_student):
    """Verifies downloading full cohort records as CSV."""
    res = client.get("/api/reports/class/csv")
    assert res.status_code == status.HTTP_200_OK
    assert "text/csv" in res.headers["content-type"]
    assert "students_cohort_export.csv" in res.headers["content-disposition"]

    csv_text = res.text
    assert "student_id,name,department,semester" in csv_text
    assert "STU_REP_001" in csv_text
    assert "Report Card Student" in csv_text


def test_download_subject_analytics_csv(client, populated_report_student):
    """Verifies downloading subject-level analytics as CSV."""
    res = client.get("/api/reports/subject-analytics/csv")
    assert res.status_code == status.HTTP_200_OK
    assert "text/csv" in res.headers["content-type"]
    assert "subject,average_score,highest_score,lowest_score" in res.text
    assert "Mathematics" in res.text


def test_download_ai_recommendations_csv(client, populated_report_student):
    """Verifies downloading historical AI recommendations archive as CSV."""
    stu_id = populated_report_student["student_id"]
    # Trigger AI analysis so a recommendation exists
    client.post(f"/api/ai/analyze/{stu_id}")

    res = client.get("/api/reports/ai-recommendations/csv")
    assert res.status_code == status.HTTP_200_OK
    assert "text/csv" in res.headers["content-type"]
    assert "student_id,overall_summary,strong_subjects" in res.text
    assert stu_id in res.text


def test_student_rbac_pdf_isolation(client, populated_report_student):
    """Verifies that a student cannot download another student's PDF report card."""
    other_token = create_access_token(
        data={"sub": "STU_UNAUTHORIZED", "role": "student", "user_id": 777, "student_id": "STU_UNAUTHORIZED"}
    )
    headers = {"Authorization": f"Bearer {other_token}"}

    stu_id = populated_report_student["student_id"]
    res = client.get(f"/api/reports/student/{stu_id}/pdf", headers=headers)
    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert "Students are restricted to accessing their own records" in res.json()["detail"]
