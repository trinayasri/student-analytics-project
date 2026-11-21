"""
analytics.py - Academic Analytics & Performance Intelligence API Endpoints

Provides:
- High-level executive summary KPIs and department breakdowns.
- Grade distribution histograms and curriculum subject averages.
- Multi-factor 3-tier at-risk student evaluations (Good, Needs Attention, At Risk).
- Side-by-side student comparison and cohort benchmarking.
- Semester-wise progression trend analysis.
- Attendance vs. marks correlation and tier statistics.
- Top and lowest performers rankings.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import crud
from app.models import Student
from app.schemas import (
    AnalyticsSummary,
    DepartmentAnalytics,
    GradeDistributionItem,
    SubjectAverageItem,
    StudentResponse,
    RiskAssessmentResponse,
    StudentComparisonRequest,
    StudentComparisonResult,
    StudentClassBenchmarkResponse,
    SemesterTrendItem,
    AttendanceInsightResult,
    PerformersRankingResponse
)
from app.services.risk_service import evaluate_cohort_risk, evaluate_student_risk
from app.services.analytics_service import (
    compare_students,
    compare_student_with_class,
    get_semester_trends,
    get_attendance_performance_insights,
    get_rankings
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
    - Counts for Good, Needs Attention, and At-Risk tiers
    - Top performing student profile
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
    summary="List students requiring academic intervention (Legacy compatibility)"
)
def get_at_risk_students(
    limit: int = Query(50, ge=1, le=200, description="Max records to return"),
    db: Session = Depends(get_db)
):
    """
    Identifies students who need academic support.
    Criteria: Overall average < 50.0% OR score in any subject < 40.0% OR attendance < 75%.
    """
    return crud.get_at_risk_students(db, limit=limit)


@router.get(
    "/risk-evaluations",
    response_model=List[RiskAssessmentResponse],
    summary="Detailed 3-tier risk analysis with factors and recommendations"
)
def get_detailed_risk_evaluations(
    category: Optional[str] = Query(None, description="Filter by category: 'Good', 'Needs Attention', 'At Risk'"),
    department: Optional[str] = Query(None, description="Filter by department"),
    db: Session = Depends(get_db)
):
    """
    Multi-Factor 3-Tier Risk Engine:
    Evaluates students across Aggregate %, Subject Failures, Attendance %, and Historical Trend.
    Provides itemized risk factors and targeted intervention action items.
    """
    query = db.query(Student)
    if department:
        query = query.filter(Student.department == department.strip())
    students = query.all()
    return evaluate_cohort_risk(students, category_filter=category)


@router.post(
    "/compare",
    response_model=StudentComparisonResult,
    summary="Side-by-side student performance comparison"
)
def compare_selected_students(
    req: StudentComparisonRequest,
    db: Session = Depends(get_db)
):
    """
    Compares 2 to 10 students side-by-side across all subjects, totals, and attendance.
    Includes benchmark reference values.
    """
    return compare_students(db, req.student_ids)


@router.get(
    "/compare/{student_id}",
    response_model=StudentClassBenchmarkResponse,
    summary="Benchmark student against department class average"
)
def compare_student_with_class_average(
    student_id: str,
    db: Session = Depends(get_db)
):
    """
    Benchmarks an individual student against their department peers and the institution average.
    """
    result = compare_student_with_class(db, student_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID '{student_id}' not found."
        )
    return result


@router.get(
    "/trends",
    response_model=List[SemesterTrendItem],
    summary="Get semester-wise performance trends"
)
def get_trends(
    department: Optional[str] = Query(None, description="Filter by department"),
    db: Session = Depends(get_db)
):
    """
    Calculates academic progression across Semesters 1 to 8:
    - Average score progression
    - Student enrollment per semester
    - Passing rate trends
    - Average attendance progression
    """
    return get_semester_trends(db, department=department)


@router.get(
    "/attendance-insights",
    response_model=AttendanceInsightResult,
    summary="Get attendance vs. academic performance correlation and tier insights"
)
def get_attendance_insights(
    department: Optional[str] = Query(None, description="Filter by department"),
    db: Session = Depends(get_db)
):
    """
    Computes Pearson correlation coefficient (r) between attendance and academic scores.
    Categorizes students into High (>=85%), Moderate (75-84%), and Low (<75%) attendance tiers.
    """
    return get_attendance_performance_insights(db, department=department)


@router.get(
    "/rankings",
    response_model=PerformersRankingResponse,
    summary="Get top and lowest performers rankings"
)
def get_performers_ranking(
    limit: int = Query(5, ge=1, le=20, description="Number of students per list"),
    department: Optional[str] = Query(None, description="Filter by department"),
    db: Session = Depends(get_db)
):
    """
    Returns the top highest and lowest performing students for honors and targeted intervention.
    """
    return get_rankings(db, limit=limit, department=department)
