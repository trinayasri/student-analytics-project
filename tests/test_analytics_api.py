"""
test_analytics_api.py - Integration Tests for Academic Analytics REST Endpoints
"""

import pytest


def _create_student_helper(client, stu_id, name, dept, sem, email, math, prog, ds, db, ml):
    return client.post(
        "/api/students/",
        json={
            "student_id": stu_id,
            "name": name,
            "department": dept,
            "semester": sem,
            "email": email,
            "math_marks": math,
            "programming_marks": prog,
            "data_structures_marks": ds,
            "database_marks": db,
            "machine_learning_marks": ml
        }
    )


def test_analytics_empty_database(client):
    """Test analytics endpoints return graceful zeroed structures when database is empty."""
    res_summary = client.get("/api/analytics/summary")
    assert res_summary.status_code == 200
    summary = res_summary.json()
    assert summary["total_students"] == 0
    assert summary["overall_average"] == 0.0

    res_grades = client.get("/api/analytics/grade-distribution")
    assert res_grades.status_code == 200
    assert len(res_grades.json()) == 6

    res_depts = client.get("/api/analytics/departments")
    assert res_depts.status_code == 200
    assert res_depts.json() == []

    res_at_risk = client.get("/api/analytics/at-risk")
    assert res_at_risk.status_code == 200
    assert res_at_risk.json() == []


def test_analytics_calculations_with_data(client):
    """Test analytics calculation accuracy with populated students."""
    # Student 1: High performer (Avg = 90)
    _create_student_helper(client, "S1", "High Performer", "AI & ML", 6, "s1@test.com", 90, 90, 90, 90, 90)
    # Student 2: Average performer (Avg = 70)
    _create_student_helper(client, "S2", "Mid Performer", "AI & ML", 6, "s2@test.com", 70, 70, 70, 70, 70)
    # Student 3: CSE Performer (Avg = 80)
    _create_student_helper(client, "S3", "CSE Student", "CSE", 4, "s3@test.com", 80, 80, 80, 80, 80)
    # Student 4: At-Risk (Avg = 40, failed math = 30)
    _create_student_helper(client, "S4", "Low Performer", "CSE", 4, "s4@test.com", 30, 40, 45, 45, 40)

    # 1. Summary Check
    res_summary = client.get("/api/analytics/summary")
    assert res_summary.status_code == 200
    summary = res_summary.json()
    assert summary["total_students"] == 4
    # (90 + 70 + 80 + 40) / 4 = 70.0
    assert summary["overall_average"] == 70.0
    assert summary["highest_average"] == 90.0
    assert summary["lowest_average"] == 40.0
    assert summary["at_risk_count"] == 1
    assert summary["pass_percentage"] == 75.0
    assert summary["top_performer"]["student_id"] == "S1"

    # 2. Departments Check
    res_depts = client.get("/api/analytics/departments")
    assert res_depts.status_code == 200
    depts = res_depts.json()
    assert len(depts) == 2
    # AI & ML: avg = 80.0
    # CSE: avg = 60.0
    aiml = next(d for d in depts if d["department"] == "AI & ML")
    assert aiml["student_count"] == 2
    assert aiml["average_marks"] == 80.0

    # 3. Grade Distribution Check
    res_grades = client.get("/api/analytics/grade-distribution")
    assert res_grades.status_code == 200
    grades = {item["grade"]: item["count"] for item in res_grades.json()}
    assert grades["A+"] == 1  # S1 (90)
    assert grades["A"] == 1   # S3 (80)
    assert grades["B"] == 1   # S2 (70)
    assert grades["F"] == 1   # S4 (40)

    # 4. At-Risk Check
    res_risk = client.get("/api/analytics/at-risk")
    assert res_risk.status_code == 200
    risk_list = res_risk.json()
    assert len(risk_list) == 1
    assert risk_list[0]["student_id"] == "S4"

    # 5. Subject Averages Check
    res_sub = client.get("/api/analytics/subject-averages")
    assert res_sub.status_code == 200
    subs = res_sub.json()
    assert len(subs) == 5
    math_sub = next(s for s in subs if s["subject"] == "Mathematics")
    # Math scores: 90, 70, 80, 30 -> sum=270 / 4 = 67.5
    assert math_sub["average_score"] == 67.5
    assert math_sub["highest_score"] == 90.0
    assert math_sub["lowest_score"] == 30.0
