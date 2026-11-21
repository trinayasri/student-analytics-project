"""
reports.py - PDF & CSV Reporting REST API Endpoints

Provides downloadable reports:
- Individual student PDF grade cards with AI recommendations.
- Institutional at-risk early warning PDF dossiers.
- Cohort class performance CSV exports with customizable filters.
- Subject-wise performance analytics CSV exports.
- AI diagnostic recommendation archives CSV exports.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Student
from app import crud
from app.core.deps import get_current_user_optional
from app.routes.students import _resolve_student
from app.services.report_service import (
    generate_student_pdf_report,
    generate_at_risk_pdf_report,
    generate_class_csv_export,
    generate_subject_analytics_csv,
    generate_ai_recommendations_csv
)

router = APIRouter()


@router.get(
    "/student/{identifier}/pdf",
    summary="Download individual student PDF academic report card"
)
def download_student_pdf_report(
    identifier: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Generates and returns an individual student official PDF report card.
    Enforces student isolation: students can only download their own report card.
    """
    student = _resolve_student(identifier, db, current_user=current_user)
    pdf_bytes = generate_student_pdf_report(student, db=db)

    filename = f"{student.student_id}_report_card.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get(
    "/at-risk/pdf",
    summary="Download institutional executive PDF report of at-risk students"
)
def download_at_risk_pdf_report(
    department: Optional[str] = Query(None, description="Filter by department"),
    db: Session = Depends(get_db)
):
    """
    Generates an executive PDF report summarizing all students requiring academic counseling.
    """
    query = db.query(Student).filter(Student.needs_support == True)
    if department:
        query = query.filter(Student.department == department.strip())

    at_risk_students = query.order_by(Student.average_marks.asc()).all()
    pdf_bytes = generate_at_risk_pdf_report(at_risk_students)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=institutional_at_risk_report.pdf"}
    )


@router.get(
    "/class/csv",
    summary="Download class cohort records as CSV"
)
def download_class_csv(
    department: Optional[str] = Query(None, description="Filter by department"),
    semester: Optional[int] = Query(None, ge=1, le=8, description="Filter by semester"),
    academic_year: Optional[str] = Query(None, description="Filter by academic year"),
    db: Session = Depends(get_db)
):
    """
    Streams a full CSV spreadsheet of students matching given filters.
    Includes demographics, marks, attendance, and computed risk tiers.
    """
    students, _ = crud.get_students(
        db=db,
        skip=0,
        limit=10000,
        department=department,
        semester=semester,
        academic_year=academic_year
    )
    csv_content = generate_class_csv_export(students)

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=students_cohort_export.csv"}
    )


@router.get(
    "/subject-analytics/csv",
    summary="Download curriculum subject-wise analytics as CSV"
)
def download_subject_analytics_csv(db: Session = Depends(get_db)):
    """
    Exports summary statistics (average, max, min) for each curriculum course as CSV.
    """
    subject_stats = crud.get_subject_averages(db)
    csv_content = generate_subject_analytics_csv(subject_stats)

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=subject_analytics.csv"}
    )


@router.get(
    "/ai-recommendations/csv",
    summary="Download historical AI recommendations as CSV"
)
def download_ai_recommendations_csv(db: Session = Depends(get_db)):
    """
    Exports all persisted AI recommendations as CSV for institutional records.
    """
    csv_content = generate_ai_recommendations_csv(db)

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=ai_recommendations_archive.csv"}
    )
