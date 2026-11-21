"""
test_risk_and_analytics.py - Test Suite for 3-Tier Risk Engine & Advanced Analytics

Tests:
- 3-tier risk evaluation categorization (Good, Needs Attention, At Risk) with factors and recommendations
- Side-by-side student comparison
- Student benchmarking against class / department average
- Semester-wise performance trends
- Attendance vs. marks correlation analysis
- Top and lowest performers rankings
"""

import pytest
from fastapi import status


@pytest.fixture
def populated_students(client):
    """Populates 4 test students across diverse performance and attendance levels."""
    # S1: High Performer in Good standing
    client.post("/api/students/", json={
        "student_id": "STU_HIGH",
        "name": "High Performer",
        "department": "AI & ML",
        "semester": 6,
        "academic_year": "2024-2025",
        "email": "high@test.edu",
        "math_marks": 95.0,
        "programming_marks": 96.0,
        "data_structures_marks": 92.0,
        "database_marks": 90.0,
        "machine_learning_marks": 94.0,
        "attendance_percentage": 95.0
    })

    # S2: Mid Performer (Needs Attention due to 70% attendance)
    client.post("/api/students/", json={
        "student_id": "STU_MID",
        "name": "Mid Performer",
        "department": "AI & ML",
        "semester": 6,
        "academic_year": "2024-2025",
        "email": "mid@test.edu",
        "math_marks": 58.0,
        "programming_marks": 60.0,
        "data_structures_marks": 55.0,
        "database_marks": 57.0,
        "machine_learning_marks": 59.0,
        "attendance_percentage": 70.0
    })

    # S3: At Risk (Failed Math: 32, Critical Attendance: 60%)
    client.post("/api/students/", json={
        "student_id": "STU_RISK",
        "name": "Risk Performer",
        "department": "Computer Science",
        "semester": 4,
        "academic_year": "2024-2025",
        "email": "risk@test.edu",
        "math_marks": 32.0,  # Failed Math
        "programming_marks": 45.0,
        "data_structures_marks": 38.0,  # Failed DSA
        "database_marks": 42.0,
        "machine_learning_marks": 40.0,
        "attendance_percentage": 60.0
    })

    # S4: CSE Good Student
    client.post("/api/students/", json={
        "student_id": "STU_CSE",
        "name": "CSE Student",
        "department": "Computer Science",
        "semester": 4,
        "academic_year": "2024-2025",
        "email": "cse@test.edu",
        "math_marks": 80.0,
        "programming_marks": 82.0,
        "data_structures_marks": 78.0,
        "database_marks": 85.0,
        "machine_learning_marks": 80.0,
        "attendance_percentage": 88.0
    })


def test_detailed_risk_evaluations(client, populated_students):
    """Verifies 3-tier risk engine categories, factors, and recommendations."""
    res = client.get("/api/analytics/risk-evaluations")
    assert res.status_code == status.HTTP_200_OK
    evaluations = res.json()
    assert len(evaluations) == 4

    # Locate STU_RISK
    risk_item = next(e for e in evaluations if e["student_id"] == "STU_RISK")
    assert risk_item["category"] == "At Risk"
    assert risk_item["risk_score"] >= 50.0
    assert any("Failed subject" in f for f in risk_item["factors"])
    assert any("attendance" in f.lower() for f in risk_item["factors"])
    assert len(risk_item["recommendations"]) > 0

    # Locate STU_HIGH
    good_item = next(e for e in evaluations if e["student_id"] == "STU_HIGH")
    assert good_item["category"] == "Good"
    assert good_item["risk_score"] < 25.0

    # Filter by category
    filter_res = client.get("/api/analytics/risk-evaluations?category=At%20Risk")
    assert filter_res.status_code == status.HTTP_200_OK
    assert all(e["category"] == "At Risk" for e in filter_res.json())


def test_student_side_by_side_comparison(client, populated_students):
    """Verifies comparing multiple students returns aligned metrics table."""
    payload = {"student_ids": ["STU_HIGH", "STU_RISK"]}
    res = client.post("/api/analytics/compare", json=payload)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert len(data["students"]) == 2
    assert len(data["comparison_table"]) > 5
    assert "benchmarks" in data
    assert "institution_average" in data["benchmarks"]


def test_student_class_benchmarking(client, populated_students):
    """Verifies benchmarking a student against their department class average."""
    res = client.get("/api/analytics/compare/STU_HIGH")
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["department"] == "AI & ML"
    assert len(data["breakdown"]) >= 5

    math_entry = next(b for b in data["breakdown"] if b["subject"] == "Mathematics")
    assert math_entry["student_score"] == 95.0
    assert math_entry["status"] == "Above Average"
    assert math_entry["variance"] > 0


def test_semester_trends(client, populated_students):
    """Verifies semester-by-semester progression trends."""
    res = client.get("/api/analytics/trends")
    assert res.status_code == status.HTTP_200_OK
    trends = res.json()
    assert len(trends) >= 2  # Semesters 4 and 6
    for t in trends:
        assert "average_marks" in t
        assert "pass_percentage" in t
        assert "avg_attendance" in t


def test_attendance_performance_insights(client, populated_students):
    """Verifies attendance correlation and tier statistics."""
    res = client.get("/api/analytics/attendance-insights")
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert "correlation_coefficient" in data
    assert "correlation_strength" in data
    assert len(data["tiers"]) == 3
    assert "summary" in data


def test_performers_rankings(client, populated_students):
    """Verifies top and lowest performers rankings."""
    res = client.get("/api/analytics/rankings?limit=2")
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert len(data["highest_performers"]) == 2
    assert len(data["lowest_performers"]) == 2
    assert data["highest_performers"][0]["student_id"] == "STU_HIGH"
    assert data["lowest_performers"][0]["student_id"] == "STU_RISK"
