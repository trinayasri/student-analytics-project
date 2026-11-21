"""
risk_service.py - Multi-Factor 3-Tier At-Risk Early Warning Engine

Evaluates student academic and engagement metrics across 4 dimensions:
1. Overall aggregate average percentage.
2. Subject-level pass/fail status (< 40.0 cutoff).
3. Attendance rate (< 65% critical, < 75% warning).
4. Temporal performance trajectories when historical assessments exist.

Outputs categorical risk status ('Good', 'Needs Attention', 'At Risk') with
a normalized 0-100 risk score, itemized risk drivers, and targeted intervention actions.
"""

from typing import Dict, Any, List, Optional
from app.models import Student, AssessmentMark


def evaluate_student_risk(student: Student) -> Dict[str, Any]:
    """
    Evaluates risk for an individual student.
    Returns:
    {
        "student_id": "STU1016",
        "name": "Siddharth Roy",
        "category": "At Risk",
        "risk_score": 75.0,
        "factors": ["Failed Mathematics (35.0)", ...],
        "recommendations": ["Assign faculty mentor", ...]
    }
    """
    risk_score = 0.0
    factors: List[str] = []
    recommendations: List[str] = []

    # 1. Overall Average Analysis
    avg = float(student.average_marks)
    if avg < 50.0:
        risk_score += 40.0
        factors.append(f"Failing aggregate percentage: {avg}% (< 50.0% cutoff)")
        recommendations.append("Mandatory remedial tutoring sessions for core academic concepts.")
    elif avg < 60.0:
        risk_score += 20.0
        factors.append(f"Borderline average percentage: {avg}% (Below 60% first-class standard)")
        recommendations.append("Bi-weekly academic progress reviews with department counselor.")
    elif avg < 70.0:
        risk_score += 5.0

    # 2. Subject-Level Failures (< 40.0 passing cutoff)
    subject_map = {
        "Mathematics": float(student.math_marks),
        "Programming": float(student.programming_marks),
        "Data Structures": float(student.data_structures_marks),
        "Database Systems": float(student.database_marks),
        "Machine Learning": float(student.machine_learning_marks)
    }

    failed_subjects = []
    for sub_name, score in subject_map.items():
        if score < 40.0:
            failed_subjects.append(f"{sub_name} ({score} / 100)")
            risk_score += 20.0
        elif score < 50.0:
            factors.append(f"Weak performance in {sub_name}: {score} / 100")
            risk_score += 8.0

    if failed_subjects:
        factors.insert(0, f"Failed subject(s): {', '.join(failed_subjects)}")
        recommendations.append(f"Focused revision and practice worksheets for failed courses: {', '.join([s.split(' (')[0] for s in failed_subjects])}.")

    # 3. Attendance Percentage Analysis
    att = float(student.attendance_percentage) if student.attendance_percentage is not None else 85.0
    if att < 65.0:
        risk_score += 35.0
        factors.append(f"Critical attendance deficit: {att}% (< 65% mandatory threshold)")
        recommendations.append("Immediate attendance alert notification to student and academic advisor.")
    elif att < 75.0:
        risk_score += 15.0
        factors.append(f"Sub-optimal attendance: {att}% (< 75% institutional requirement)")
        recommendations.append("Attendance counseling to prevent semester examination debarment.")

    # 4. Assessment Progression Trajectory (Historical assessments if recorded)
    if student.assessment_marks:
        # Sort marks by creation/semester
        sorted_marks = sorted(student.assessment_marks, key=lambda m: (m.semester, m.created_at))
        if len(sorted_marks) >= 2:
            first_score = sorted_marks[0].marks_obtained
            last_score = sorted_marks[-1].marks_obtained
            diff = last_score - first_score
            if diff < -10.0:
                risk_score += 15.0
                factors.append(f"Declining performance trend: -{abs(diff):.1f}% drop between assessments")
                recommendations.append("Investigate potential study impediments causing recent downward performance drift.")

    # Normalize risk score to [0, 100]
    risk_score = round(min(100.0, max(0.0, risk_score)), 1)

    # Categorization
    if risk_score >= 45.0 or avg < 50.0 or len(failed_subjects) >= 2 or att < 65.0:
        category = "At Risk"
    elif risk_score >= 20.0 or len(failed_subjects) == 1 or (65.0 <= att < 75.0):
        category = "Needs Attention"
    else:
        category = "Good"

    # Default recommendation for Good standing
    if category == "Good" and not recommendations:
        recommendations.append("Encourage participation in advanced problem-solving, open-source projects, or peer mentoring.")

    return {
        "student_id": student.student_id,
        "name": student.name,
        "department": student.department,
        "semester": student.semester,
        "academic_year": getattr(student, "academic_year", "2024-2025"),
        "average_marks": avg,
        "attendance_percentage": att,
        "category": category,
        "risk_score": risk_score,
        "factors": factors if factors else ["All course marks and attendance levels satisfy good standing requirements."],
        "recommendations": recommendations
    }


def evaluate_cohort_risk(students: List[Student], category_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Evaluates risk across a list of students, optionally filtering by category:
    'At Risk', 'Needs Attention', or 'Good'.
    """
    results = [evaluate_student_risk(s) for s in students]
    if category_filter:
        clean_cat = category_filter.strip().lower()
        results = [r for r in results if r["category"].lower() == clean_cat]
    # Sort by risk score descending (highest risk first)
    return sorted(results, key=lambda x: x["risk_score"], reverse=True)
