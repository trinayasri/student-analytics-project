"""
analytics.py - Academic Analytics API Endpoints

Provides endpoints for institutional summary statistics, department-wise breakdowns,
grade distribution histograms, subject averages, and identification of at-risk students.
"""

from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app import crud
from app.schemas import (
    AnalyticsSummary,
    DepartmentAnalytics,
    GradeDistributionItem,
    SubjectAverageItem,
    StudentResponse
)

router = APIRouter()


@router.get(
    "/summary",
    response_model=AnalyticsSummary,
    summary="Get overall institutional performance summary"
)
def get_analytics_summary(db: Session = Depends(get_db)):
    """
    Returns high-level academic KPIs:
    - Total student count
    - College-wide average marks
    - Highest & lowest student average
    - Overall pass percentage
    - Total count of students requiring academic support
    - Top performing student
    """
    return crud.get_overall_summary(db)


@router.get(
    "/departments",
    response_model=List[DepartmentAnalytics],
    summary="Get department-wise performance breakdown"
)
def get_department_analytics(db: Session = Depends(get_db)):
    """
    Returns department-level metrics:
    - Student count per department
    - Department average marks
    - Department highest and lowest scores
    """
    return crud.get_department_analytics(db)


@router.get(
    "/grade-distribution",
    response_model=List[GradeDistributionItem],
    summary="Get grade distribution across all students"
)
def get_grade_distribution(db: Session = Depends(get_db)):
    """
    Returns counts and percentages for each grade tier:
    A+ (>=90%), A (80-89%), B (70-79%), C (60-69%), D (50-59%), F (<50%).
    """
    return crud.get_grade_distribution(db)


@router.get(
    "/subject-averages",
    response_model=List[SubjectAverageItem],
    summary="Get subject-level performance comparison"
)
def get_subject_averages(db: Session = Depends(get_db)):
    """
    Returns college-wide average, highest, and lowest scores
    for each of the 5 curriculum subjects.
    """
    return crud.get_subject_averages(db)


@router.get(
    "/at-risk",
    response_model=List[StudentResponse],
    summary="List students requiring academic intervention"
)
def get_at_risk_students(
    limit: int = Query(50, ge=1, le=200, description="Max records to return"),
    db: Session = Depends(get_db)
):
    """
    Identifies students who need academic support.
    Criteria: Overall average < 50.0% OR score in any subject < 40.0%.
    """
    return crud.get_at_risk_students(db, limit=limit)
