"""
test_ai_and_study_plans.py - Test Suite for Gemini AI Diagnostics & Weekly Study Plans

Tests:
- AI performance analysis generation (structured JSON validation, weak subjects, recommendations)
- Fallback handling when offline or without API key
- Study plan retrieval and persistent storage in DB
- Interactive task completion toggling and progress percentage updates
- Student authorization isolation on study plan tasks
- Historical recommendation logs
"""

import pytest
from fastapi import status
from app.core.security import create_access_token


@pytest.fixture
def sample_ai_student(client):
    """Creates a student with a clear weak subject in Mathematics and Database."""
    res = client.post("/api/students/", json={
        "student_id": "STU_AI_TEST",
        "name": "Dev AI Student",
        "department": "Computer Science",
        "semester": 4,
        "academic_year": "2024-2025",
        "email": "dev.ai@university.edu",
        "math_marks": 36.0,  # Weak / Failed
        "programming_marks": 88.0,  # Strong
        "data_structures_marks": 78.0,
        "database_marks": 45.0,  # Weak
        "machine_learning_marks": 85.0,  # Strong
        "attendance_percentage": 78.0
    })
    return res.json()


def test_generate_ai_analysis_structure_and_fallback(client, sample_ai_student):
    """Verifies that AI analysis produces validated structured JSON diagnosing actual weak courses."""
    stu_id = sample_ai_student["student_id"]
    res = client.post(f"/api/ai/analyze/{stu_id}")
    assert res.status_code == status.HTTP_200_OK
    data = res.json()

    assert data["student_id"] == stu_id
    assert data["name"] == "Dev AI Student"
    assert "analysis" in data
    assert data["source"] in ["gemini_api", "resilient_fallback"]

    analysis = data["analysis"]
    assert len(analysis["overall_summary"]) > 20
    assert "Programming / Python" in analysis["strong_subjects"] or "Machine Learning" in analysis["strong_subjects"]
    
    # Mathematics (36.0) and Database (45.0) must be identified as weak
    weak_names = [w["subject"] for w in analysis["weak_subjects"]]
    assert "Mathematics" in weak_names
    assert len(analysis["weak_subjects"][0]["priority_topics"]) > 0
    assert analysis["recommended_weekly_hours"] > 0
    assert len(analysis["personalized_advice"]) > 10

    # Verify study plan created
    assert data["study_plan_id"] is not None
    assert data["study_plan_items_count"] >= 5


def test_ai_history_persistence(client, sample_ai_student):
    """Verifies that generated recommendations are persisted in database and queryable."""
    stu_id = sample_ai_student["student_id"]
    # Trigger analysis
    client.post(f"/api/ai/analyze/{stu_id}")

    # Query history
    res_hist = client.get(f"/api/ai/history/{stu_id}")
    assert res_hist.status_code == status.HTTP_200_OK
    history = res_hist.json()
    assert len(history) >= 1
    assert history[0]["student_id"] == stu_id
    assert "Mathematics" in history[0]["weak_subjects"]


def test_get_and_toggle_study_plan_items(client, sample_ai_student):
    """Verifies study plan retrieval, task toggling, and progress tracking."""
    stu_id = sample_ai_student["student_id"]

    # 1. Fetch study plan
    res_plan = client.get(f"/api/study-plans/{stu_id}")
    assert res_plan.status_code == status.HTTP_200_OK
    plan = res_plan.json()
    assert plan["student_id"] == stu_id
    assert len(plan["items"]) >= 5

    first_item = plan["items"][0]
    item_id = first_item["id"]
    assert first_item["is_completed"] is False

    # 2. Toggle item to completed
    res_toggle1 = client.patch(f"/api/study-plans/items/{item_id}/toggle")
    assert res_toggle1.status_code == status.HTTP_200_OK
    toggle_data1 = res_toggle1.json()
    assert toggle_data1["is_completed"] is True
    assert toggle_data1["completed_at"] is not None
    assert toggle_data1["completed_items_count"] == 1
    assert toggle_data1["completion_percentage"] > 0.0

    # 3. Toggle back to incomplete
    res_toggle2 = client.patch(f"/api/study-plans/items/{item_id}/toggle")
    assert res_toggle2.status_code == status.HTTP_200_OK
    toggle_data2 = res_toggle2.json()
    assert toggle_data2["is_completed"] is False
    assert toggle_data2["completed_items_count"] == 0
    assert toggle_data2["completion_percentage"] == 0.0


def test_student_isolation_on_study_plan_toggle(client, sample_ai_student):
    """Verifies that students cannot modify another student's study plan tasks."""
    stu_id = sample_ai_student["student_id"]
    res_plan = client.get(f"/api/study-plans/{stu_id}")
    item_id = res_plan.json()["items"][0]["id"]

    # Authenticate as a different student
    other_token = create_access_token(
        data={"sub": "DIFFERENT_STU", "role": "student", "user_id": 888, "student_id": "DIFFERENT_STU"}
    )
    headers = {"Authorization": f"Bearer {other_token}"}

    # Attempt toggle on STU_AI_TEST's item
    res_toggle = client.patch(f"/api/study-plans/items/{item_id}/toggle", headers=headers)
    assert res_toggle.status_code == status.HTTP_403_FORBIDDEN
    assert "Students can only modify their own study plan tasks" in res_toggle.json()["detail"]


def test_regenerate_study_plan(client, sample_ai_student):
    """Verifies explicit regeneration of a study plan."""
    stu_id = sample_ai_student["student_id"]
    res = client.post(f"/api/study-plans/generate/{stu_id}")
    assert res.status_code == status.HTTP_200_OK
    plan = res.json()
    assert plan["status"] == "active"
    assert len(plan["items"]) >= 5
