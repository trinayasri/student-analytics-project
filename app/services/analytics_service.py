"""
analytics_service.py - Advanced Academic Analytics & Statistical Modeling

Provides:
- Side-by-side student comparison.
- Student vs. class/cohort benchmarking.
- Semester-wise progression trend analysis.
- Attendance vs. academic performance correlation and tier analysis.
- Highest and lowest performers ranking.
"""

import math
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Student


def compare_students(db: Session, student_ids: List[str]) -> Dict[str, Any]:
    """
    Retrieves and formats comparison metrics for two or more students side-by-side.
    """
    clean_ids = [s.strip() for s in student_ids if s.strip()]
    students = (
        db.query(Student)
        .filter(Student.student_id.in_(clean_ids))
        .all()
    )

    if not students:
        return {"students": [], "comparison_table": [], "benchmarks": {}}

    metrics_list = [
        ("Mathematics", "math_marks"),
        ("Programming / Python", "programming_marks"),
        ("Data Structures", "data_structures_marks"),
        ("Database Systems", "database_marks"),
        ("Machine Learning", "machine_learning_marks"),
        ("Total Marks (out of 500)", "total_marks"),
        ("Average Percentage", "average_marks"),
        ("Attendance Rate (%)", "attendance_percentage")
    ]

    table_rows = []
    for label, attr in metrics_list:
        row: Dict[str, Any] = {"metric": label}
        for s in students:
            val = getattr(s, attr, 0.0)
            row[s.student_id] = round(float(val), 2) if val is not None else 0.0
        table_rows.append(row)

    # Calculate institution benchmarks for context
    benchmarks = {
        "institution_average": round(float(db.query(func.avg(Student.average_marks)).scalar() or 0.0), 2),
        "institution_attendance": round(float(db.query(func.avg(Student.attendance_percentage)).scalar() or 0.0), 2)
    }

    return {
        "students": students,
        "comparison_table": table_rows,
        "benchmarks": benchmarks
    }


def compare_student_with_class(db: Session, student_id: str) -> Dict[str, Any]:
    """
    Benchmarks a single student against their department class average and the institution average.
    """
    student = db.query(Student).filter(Student.student_id == student_id.strip()).first()
    if not student:
        return {}

    dept = student.department

    # Department averages
    dept_stats = db.query(
        func.avg(Student.math_marks).label("math"),
        func.avg(Student.programming_marks).label("prog"),
        func.avg(Student.data_structures_marks).label("ds"),
        func.avg(Student.database_marks).label("db"),
        func.avg(Student.machine_learning_marks).label("ml"),
        func.avg(Student.average_marks).label("avg"),
        func.avg(Student.attendance_percentage).label("att")
    ).filter(Student.department == dept).first()

    # College-wide averages
    college_stats = db.query(
        func.avg(Student.average_marks).label("avg"),
        func.avg(Student.attendance_percentage).label("att")
    ).first()

    subjects = [
        ("Mathematics", student.math_marks, dept_stats.math or 0.0),
        ("Programming", student.programming_marks, dept_stats.prog or 0.0),
        ("Data Structures", student.data_structures_marks, dept_stats.ds or 0.0),
        ("Database Systems", student.database_marks, dept_stats.db or 0.0),
        ("Machine Learning", student.machine_learning_marks, dept_stats.ml or 0.0),
        ("Overall Average", student.average_marks, dept_stats.avg or 0.0),
        ("Attendance Rate", student.attendance_percentage, dept_stats.att or 0.0),
    ]

    breakdown = []
    for sub, stu_val, dept_avg in subjects:
        diff = round(float(stu_val) - float(dept_avg), 2)
        breakdown.append({
            "subject": sub,
            "student_score": round(float(stu_val), 2),
            "department_average": round(float(dept_avg), 2),
            "variance": diff,
            "status": "Above Average" if diff > 0 else ("Equal" if diff == 0 else "Below Average")
        })

    return {
        "student": student,
        "department": dept,
        "college_average": round(float(college_stats.avg or 0.0), 2),
        "college_attendance": round(float(college_stats.att or 0.0), 2),
        "breakdown": breakdown
    }


def get_semester_trends(db: Session, department: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Computes semester-by-semester performance progression across semesters 1 to 8.
    """
    query = db.query(
        Student.semester,
        func.count(Student.id).label("student_count"),
        func.avg(Student.average_marks).label("average_marks"),
        func.max(Student.average_marks).label("max_marks"),
        func.min(Student.average_marks).label("min_marks"),
        func.avg(Student.attendance_percentage).label("avg_attendance")
    )
    if department:
        query = query.filter(Student.department == department.strip())

    results = query.group_by(Student.semester).order_by(Student.semester.asc()).all()

    trends = []
    for r in results:
        # Calculate passing percentage for this semester
        total = r.student_count
        pass_q = db.query(func.count(Student.id)).filter(Student.semester == r.semester, Student.average_marks >= 50.0)
        if department:
            pass_q = pass_q.filter(Student.department == department.strip())
        pass_count = pass_q.scalar() or 0
        pass_rate = round((pass_count / total * 100.0), 2) if total > 0 else 0.0

        trends.append({
            "semester": r.semester,
            "semester_label": f"Semester {r.semester}",
            "student_count": r.student_count,
            "average_marks": round(float(r.average_marks), 2),
            "max_marks": round(float(r.max_marks), 2),
            "min_marks": round(float(r.min_marks), 2),
            "avg_attendance": round(float(r.avg_attendance or 85.0), 2),
            "pass_percentage": pass_rate
        })
    return trends


def get_attendance_performance_insights(db: Session, department: Optional[str] = None) -> Dict[str, Any]:
    """
    Computes statistical correlation and tier-based insights between attendance and marks.
    """
    query = db.query(Student.attendance_percentage, Student.average_marks)
    if department:
        query = query.filter(Student.department == department.strip())

    records = query.all()
    if not records or len(records) < 2:
        return {
            "correlation_coefficient": 0.0,
            "correlation_strength": "Insufficient data",
            "tiers": [],
            "summary": "At least 2 student records are required to calculate attendance-performance correlation."
        }

    x = [float(r[0] or 0.0) for r in records]  # Attendance
    y = [float(r[1] or 0.0) for r in records]  # Marks
    n = len(x)

    mean_x = sum(x) / n
    mean_y = sum(y) / n

    numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    denominator_x = sum((x[i] - mean_x) ** 2 for i in range(n))
    denominator_y = sum((y[i] - mean_y) ** 2 for i in range(n))

    if denominator_x > 0 and denominator_y > 0:
        r = numerator / math.sqrt(denominator_x * denominator_y)
        r = round(max(-1.0, min(1.0, r)), 3)
    else:
        r = 0.0

    if abs(r) >= 0.7:
        strength = "Strong Positive Correlation" if r > 0 else "Strong Negative Correlation"
    elif abs(r) >= 0.4:
        strength = "Moderate Positive Correlation" if r > 0 else "Moderate Negative Correlation"
    elif abs(r) >= 0.1:
        strength = "Weak Positive Correlation" if r > 0 else "Weak Negative Correlation"
    else:
        strength = "Negligible Correlation"

    # Attendance Tiers:
    # 1. High (>= 85%)
    # 2. Moderate (75% - 84.9%)
    # 3. Critical / Low (< 75%)
    high_att = [r for r in records if (r[0] or 0.0) >= 85.0]
    mod_att = [r for r in records if 75.0 <= (r[0] or 0.0) < 85.0]
    low_att = [r for r in records if (r[0] or 0.0) < 75.0]

    def _tier_stats(tier_list, label):
        if not tier_list:
            return {"tier": label, "student_count": 0, "average_marks": 0.0, "pass_percentage": 0.0}
        cnt = len(tier_list)
        avg = round(sum(r[1] for r in tier_list) / cnt, 2)
        passed = sum(1 for r in tier_list if r[1] >= 50.0)
        return {
            "tier": label,
            "student_count": cnt,
            "average_marks": avg,
            "pass_percentage": round(passed / cnt * 100.0, 2)
        }

    tiers = [
        _tier_stats(high_att, "High Attendance (>= 85%)"),
        _tier_stats(mod_att, "Moderate Attendance (75% - 84%)"),
        _tier_stats(low_att, "Low Attendance (< 75%)")
    ]

    summary = (
        f"Pearson correlation coefficient r = {r} indicates a {strength.lower()} between attendance and marks. "
        f"Students with >=85% attendance achieved an average score of "
        f"{tiers[0]['average_marks']}% vs {tiers[2]['average_marks']}% for students with <75% attendance."
    )

    return {
        "correlation_coefficient": r,
        "correlation_strength": strength,
        "tiers": tiers,
        "summary": summary
    }


def get_rankings(db: Session, limit: int = 5, department: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieves highest and lowest performers based on aggregate average marks.
    """
    q_top = db.query(Student)
    q_low = db.query(Student)

    if department:
        q_top = q_top.filter(Student.department == department.strip())
        q_low = q_low.filter(Student.department == department.strip())

    highest = q_top.order_by(Student.average_marks.desc()).limit(limit).all()
    lowest = q_low.order_by(Student.average_marks.asc()).limit(limit).all()

    return {
        "highest_performers": highest,
        "lowest_performers": lowest
    }
