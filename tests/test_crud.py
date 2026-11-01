"""
test_crud.py - Unit Tests for CRUD and Analytics Database Logic
"""

import pytest
from app import crud
from app.schemas import StudentCreate, StudentUpdate


def test_create_and_get_student(db_session):
    """Test creating a student record and retrieving it by primary key and student_id."""
    student_data = StudentCreate(
        student_id="STU2001",
        name="Test User",
        department="Computer Science",
        semester=4,
        email="test.user@example.edu",
        math_marks=90.0,
        programming_marks=95.0,
        data_structures_marks=85.0,
        database_marks=90.0,
        machine_learning_marks=90.0
    )

    created = crud.create_student(db_session, student_data)
    assert created.id is not None
    assert created.student_id == "STU2001"
    assert created.total_marks == 450.0
    assert created.average_marks == 90.0
    assert created.grade == "A+"
    assert created.needs_support is False

    # Retrieve by ID
    by_id = crud.get_student_by_id(db_session, created.id)
    assert by_id is not None
    assert by_id.name == "Test User"

    # Retrieve by student_id
    by_stu_id = crud.get_student_by_student_id(db_session, "STU2001")
    assert by_stu_id is not None
    assert by_stu_id.email == "test.user@example.edu"


def test_update_student_recalculates_metrics(db_session):
    """Test updating student marks and verifying metrics are updated."""
    student_data = StudentCreate(
        student_id="STU2002",
        name="Update Target",
        department="Information Technology",
        semester=3,
        email="update.target@example.edu",
        math_marks=50.0,
        programming_marks=50.0,
        data_structures_marks=50.0,
        database_marks=50.0,
        machine_learning_marks=50.0
    )
    student = crud.create_student(db_session, student_data)
    assert student.average_marks == 50.0
    assert student.grade == "D"

    # Update scores to higher values
    update_data = StudentUpdate(
        math_marks=90.0,
        programming_marks=90.0,
        data_structures_marks=90.0,
        database_marks=90.0,
        machine_learning_marks=90.0
    )
    updated = crud.update_student(db_session, student, update_data)
    assert updated.average_marks == 90.0
    assert updated.grade == "A+"
    assert updated.needs_support is False


def test_at_risk_threshold_detection(db_session):
    """Verify that a student with any subject < 40 is marked as needing support."""
    # Student with average > 50, but failed math (< 40)
    student_data = StudentCreate(
        student_id="STU2003",
        name="Borderline Student",
        department="AI & ML",
        semester=5,
        email="borderline@example.edu",
        math_marks=35.0,  # Failed!
        programming_marks=80.0,
        data_structures_marks=75.0,
        database_marks=70.0,
        machine_learning_marks=65.0
    )
    student = crud.create_student(db_session, student_data)
    assert student.average_marks == 65.0
    assert student.grade == "C"
    assert student.needs_support is True  # Flagged because of math_marks < 40


def test_delete_student(db_session):
    """Test deleting a student."""
    student_data = StudentCreate(
        student_id="STU2004",
        name="Delete Me",
        department="ECE",
        semester=2,
        email="delete.me@example.edu",
        math_marks=60.0,
        programming_marks=60.0,
        data_structures_marks=60.0,
        database_marks=60.0,
        machine_learning_marks=60.0
    )
    student = crud.create_student(db_session, student_data)
    stu_id = student.id

    assert crud.delete_student(db_session, student) is True
    assert crud.get_student_by_id(db_session, stu_id) is None


def test_search_and_pagination(db_session):
    """Test substring searching, filtering, and pagination limits."""
    for i in range(1, 16):
        crud.create_student(
            db_session,
            StudentCreate(
                student_id=f"STU{3000 + i}",
                name=f"Student {i:02d}",
                department="AI & ML" if i % 2 == 0 else "CSE",
                semester=4,
                email=f"stu{i}@example.edu",
                math_marks=70.0,
                programming_marks=70.0,
                data_structures_marks=70.0,
                database_marks=70.0,
                machine_learning_marks=70.0
            )
        )

    # Page 1 (limit 10)
    p1_items, total = crud.get_students(db_session, skip=0, limit=10)
    assert len(p1_items) == 10
    assert total == 15

    # Page 2 (limit 10)
    p2_items, _ = crud.get_students(db_session, skip=10, limit=10)
    assert len(p2_items) == 5

    # Filter by department
    aiml_items, aiml_count = crud.get_students(db_session, department="AI & ML")
    assert aiml_count == 7

    # Substring search
    search_items, search_count = crud.get_students(db_session, search="05")
    assert search_count == 1
    assert search_items[0].name == "Student 05"
